import os
import threading
import logging
from typing import Dict, Any, Optional
import pyvisa
from fastapi import HTTPException

logger = logging.getLogger("chroma_driver")
logging.basicConfig(level=logging.INFO)

# Địa chỉ VISA cấu hình cho Chroma 62050P
DEFAULT_VISA_ADDRESS = os.getenv("VISA_ADDRESS", "USB0::0x1698::0x0837::008000000304::INSTR")
SIMULATION_MODE = os.getenv("CHROMA_SIMULATION", "0") == "1"


class ChromaManager:
    """
    Quản lý phiên kết nối VISA duy nhất (Singleton) tới máy nguồn Chroma 62050P-100-100.
    Tuân thủ đúng cú pháp SCPI chuẩn từ tài liệu Power-Document.md:
    - Bật/Tắt Output: CONF:OUTP ON / CONF:OUTP OFF
    - Ký tự kết thúc lệnh: \n (LF) ở cuối chuỗi gửi đi
    - Đọc trạng thái Output: CONF:OUTP? (trả về 1/ON hoặc 0/OFF)
    - Cài đặt Setpoint: SOUR:VOLT <v>, SOUR:CURR <i>
    - Đọc Setpoint: SOUR:VOLT?, SOUR:CURR?
    - Đo lường thực tế: MEAS:VOLT?, MEAS:CURR?, MEAS:POW?
    - Xóa & Đọc lỗi: *CLS, SYST:ERR?
    LƯU Ý KỸ THUẬT:
    - KHÔNG gọi viClear() (inst.clear()) trên USB-TMC vì firmware Chroma không hỗ trợ IEEE 488.1 Clear gây lỗi VI_ERROR_SYSTEM_ERROR.
    - KHÔNG gán read_termination trên USB-TMC để NI-VISA tự động bắt cờ EOI phần cứng.
    """
    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super(ChromaManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, visa_address: str = DEFAULT_VISA_ADDRESS):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.visa_address = visa_address
        self.rm: Optional[pyvisa.ResourceManager] = None
        self.instr = None
        self.is_connected = False
        self.sim_mode = SIMULATION_MODE
        self.operation_lock = threading.Lock()

        # Trạng thái giả lập phục vụ development khi không cắm phần cứng
        self._sim_state = {
            "output": "OFF",
            "voltage_set": 12.0,
            "current_set": 2.0,
            "voltage_measured": 0.0,
            "current_measured": 0.0,
            "power_measured": 0.0,
        }

        self._initialized = True

    def connect(self) -> bool:
        """
        Khởi tạo kết nối VISA bền vững (Persistent Session) tới Chroma 62050P.
        """
        if self.sim_mode:
            logger.info("ChromaManager: Đang chạy ở chế độ SIMULATION (Giả lập).")
            self.is_connected = True
            return True

        with self.operation_lock:
            # Nếu đang có kết nối cũ không hợp lệ, đóng an toàn trước
            if self.instr is not None:
                try:
                    self.instr.close()
                except Exception:
                    pass
                self.instr = None

            try:
                if self.rm is None:
                    self.rm = pyvisa.ResourceManager()

                logger.info(f"ChromaManager: Mở kết nối VISA tới {self.visa_address}")
                self.instr = self.rm.open_resource(self.visa_address)
                
                # Cấu hình chuẩn cho USB-TMC
                self.instr.timeout = 3000  # 3 giây timeout
                self.instr.write_termination = '\n'
                # Để read_termination mặc định (None) để NI-VISA bắt hardware EOI

                # Kiểm tra phản hồi *IDN?
                idn = self.instr.query("*IDN?").strip()
                logger.info(f"ChromaManager: Kết nối thành công tới thiết bị: {idn}")

                # Tự động tắt Analog Programming (APG) và xóa cờ lỗi để sẵn sàng nhận lệnh điều khiển số SCPI
                try:
                    self.instr.write("CONF:APG NONE")
                    import time
                    time.sleep(0.02)
                    self.instr.write("*CLS")
                except Exception as ex:
                    logger.warning(f"Cảnh báo cấu hình khởi tạo APG/CLS: {ex}")

                self.is_connected = True
                self._last_error = ""
                return True

            except Exception as e:
                self.is_connected = False
                self._last_error = str(e)
                if self.instr is not None:
                    try:
                        self.instr.close()
                    except Exception:
                        pass
                    self.instr = None
                logger.error(f"ChromaManager: Không thể kết nối phần cứng Chroma: {e}")
                return False

    def disconnect(self):
        """Đóng an toàn phiên làm việc VISA."""
        with self.operation_lock:
            try:
                if self.instr:
                    self.instr.close()
                    self.instr = None
                if self.rm:
                    self.rm.close()
                    self.rm = None
            except Exception as e:
                logger.warning(f"Lỗi khi đóng kết nối VISA: {e}")
            finally:
                self.is_connected = False
                logger.info("ChromaManager: Đã ngắt kết nối VISA.")

    def ensure_connected(self):
        """Đảm bảo kết nối sẵn sàng trước khi thực thi lệnh."""
        if not self.is_connected or (not self.sim_mode and self.instr is None):
            connected = self.connect()
            if not connected:
                err_detail = getattr(self, "_last_error", "")
                suffix = f": {err_detail}" if err_detail else ". Vui lòng kiểm tra cáp USB và nguồn máy."
                raise HTTPException(
                    status_code=503,
                    detail=f"Không thể kết nối với máy nguồn Chroma tại {self.visa_address}{suffix}"
                )

    def _query(self, scpi_cmd: str) -> str:
        """Gửi lệnh truy vấn SCPI và đọc phản hồi (thread-safe, chuẩn LF)."""
        if self.sim_mode:
            return ""

        self.ensure_connected()
        with self.operation_lock:
            try:
                # Đảm bảo lệnh sạch và tuân thủ terminator \n
                clean_cmd = scpi_cmd.strip()
                resp = self.instr.query(clean_cmd).strip()
                return resp
            except Exception as e:
                self.is_connected = False
                logger.error(f"Lỗi SCPI Query '{scpi_cmd}': {e}")
                raise HTTPException(status_code=500, detail=f"Lỗi truy vấn thiết bị ({scpi_cmd}): {str(e)}")

    def _write(self, scpi_cmd: str) -> bool:
        """Gửi lệnh cấu hình SCPI với pacing 20ms bảo vệ MCU Chroma."""
        if self.sim_mode:
            return True

        self.ensure_connected()
        with self.operation_lock:
            try:
                clean_cmd = scpi_cmd.strip()
                self.instr.write(clean_cmd)
                # Nghỉ ngắn 20ms theo chuẩn giao tiếp phần cứng để máy kịp cập nhật thanh ghi
                import time
                time.sleep(0.02)
                return True
            except Exception as e:
                self.is_connected = False
                logger.error(f"Lỗi SCPI Write '{scpi_cmd}': {e}")
                raise HTTPException(status_code=500, detail=f"Lỗi gửi lệnh tới thiết bị ({scpi_cmd}): {str(e)}")

    def query_idn(self) -> str:
        """Kiểm tra kết nối và định danh thiết bị (*IDN?)."""
        if self.sim_mode:
            return "CHROMA,62050P-100-100-SIMULATED,03.00,00304"
        return self._query("*IDN?")
    
    def get_system_error(self) -> str:
        """Đọc tin nhắn lỗi từ thiết bị: SYSTem:ERRor? theo Power-Document.md."""
        if self.sim_mode:
            return '0, "No error"'
        return self._query("SYST:ERR?")

    def clear_status(self) -> bool:
        """Xóa sạch cờ trạng thái và hàng đợi lỗi (*CLS)."""
        if self.sim_mode:
            return True
        return self._write("*CLS")

    def set_voltage(self, voltage: float) -> Dict[str, float]:
        """
        Cài đặt điện áp ngõ ra (Volt): SOUR:VOLT <value>
        Sau đó đọc lại xác nhận giá trị máy đã lưu (SOUR:VOLT?) và điện áp đo thực tế (MEAS:VOLT?).
        """
        if self.sim_mode:
            self._sim_state["voltage_set"] = voltage
            if self._sim_state["output"] == "ON":
                self._sim_state["voltage_measured"] = voltage
                self._sim_state["power_measured"] = round(self._sim_state["voltage_measured"] * self._sim_state["current_measured"], 2)
            return {
                "voltage_set": voltage,
                "voltage_measured": self._sim_state["voltage_measured"]
            }

        self._write(f"SOUR:VOLT {voltage:.3f}")
        v_set = float(self._query("SOUR:VOLT?"))
        try:
            v_meas = float(self._query("MEAS:VOLT?"))
        except Exception:
            v_meas = 0.0

        return {
            "voltage_set": round(v_set, 3),
            "voltage_measured": round(v_meas, 3)
        }

    def set_current(self, current: float) -> Dict[str, float]:
        """
        Cài đặt giới hạn dòng điện (Ampere): SOUR:CURR <value>
        Sau đó đọc lại xác nhận giá trị máy đã lưu (SOUR:CURR?) và dòng điện đo thực tế (MEAS:CURR?).
        """
        if self.sim_mode:
            self._sim_state["current_set"] = current
            return {
                "current_set": current,
                "current_measured": self._sim_state["current_measured"]
            }

        self._write(f"SOUR:CURR {current:.3f}")
        c_set = float(self._query("SOUR:CURR?"))
        try:
            c_meas = float(self._query("MEAS:CURR?"))
        except Exception:
            c_meas = 0.0

        return {
            "current_set": round(c_set, 3),
            "current_measured": round(c_meas, 3)
        }

    def control_output(self, state: str) -> Dict[str, Any]:
        """
        Điều khiển đóng/cắt ngõ ra: CONF:OUTP ON / CONF:OUTP OFF
        Sau đó đọc lại xác nhận trạng thái (CONF:OUTP?) và giá trị đo thực tế.
        """
        state_upper = state.upper()
        if state_upper not in ["ON", "OFF"]:
            raise HTTPException(status_code=400, detail="Trạng thái ngõ ra chỉ nhận 'ON' hoặc 'OFF'")

        if self.sim_mode:
            self._sim_state["output"] = state_upper
            if state_upper == "ON":
                self._sim_state["voltage_measured"] = self._sim_state["voltage_set"]
                self._sim_state["current_measured"] = min(0.5, self._sim_state["current_set"])
                self._sim_state["power_measured"] = round(self._sim_state["voltage_measured"] * self._sim_state["current_measured"], 2)
            else:
                self._sim_state["voltage_measured"] = 0.0
                self._sim_state["current_measured"] = 0.0
                self._sim_state["power_measured"] = 0.0
            return {
                "output_state": state_upper,
                "voltage_measured": self._sim_state["voltage_measured"],
                "current_measured": self._sim_state["current_measured"]
            }

        # Gửi cú pháp chuẩn: CONF:OUTP ON hoặc CONF:OUTP OFF
        self._write(f"CONF:OUTP {state_upper}")
        import time
        time.sleep(0.05)  # Chờ relay máy chuyển mạch
        
        outp_raw = self._query("CONF:OUTP?").upper()
        outp = "ON" if outp_raw in ["1", "ON"] else "OFF"
        try:
            v_meas = float(self._query("MEAS:VOLT?"))
            c_meas = float(self._query("MEAS:CURR?"))
        except Exception:
            v_meas = 0.0
            c_meas = 0.0

        return {
            "output_state": outp,
            "voltage_measured": round(v_meas, 3),
            "current_measured": round(c_meas, 3)
        }

    def emergency_stop(self) -> bool:
        """
        Dừng khẩn cấp: Ngắt ngõ ra lập tức (CONF:OUTP OFF) và gửi *CLS xóa lỗi.
        """
        if self.sim_mode:
            self.control_output("OFF")
            return True

        self.ensure_connected()
        with self.operation_lock:
            try:
                self.instr.write("CONF:OUTP OFF\n")
                import time
                time.sleep(0.02)
                self.instr.write("*CLS\n")
                return True
            except Exception as e:
                logger.error(f"Lỗi Emergency Stop: {e}")
                raise HTTPException(status_code=500, detail=f"Lỗi dừng khẩn cấp: {str(e)}")

    def get_telemetry(self) -> Dict[str, Any]:
        """
        Đọc dữ liệu tức thời từ máy nguồn Chroma theo đúng chuẩn Power-Document.md:
        - MEAS:VOLT? (Điện áp thực tế, hoặc FETC:VOLT?)
        - MEAS:CURR? (Dòng điện thực tế, hoặc FETC:CURR?)
        - MEAS:POW?  (Công suất tức thời, hoặc FETC:POW?)
        - CONF:OUTP? (Trạng thái Output: 1/ON hoặc 0/OFF)
        - SOUR:VOLT? (Mức Volt đang cài đặt)
        - SOUR:CURR? (Mức Amp đang cài đặt)
        """
        if self.sim_mode:
            return {
                "voltage_measured": self._sim_state["voltage_measured"],
                "current_measured": self._sim_state["current_measured"],
                "power_measured": self._sim_state["power_measured"],
                "output_state": self._sim_state["output"],
                "voltage_set": self._sim_state["voltage_set"],
                "current_set": self._sim_state["current_set"],
            }

        self.ensure_connected()
        with self.operation_lock:
            try:
                # 1. Đọc trạng thái ngõ ra (CONF:OUTP? trả về 1/0 hoặc ON/OFF)
                outp_raw = self.instr.query("CONF:OUTP?").strip().upper()
                outp = "ON" if outp_raw in ["1", "ON"] else "OFF"

                # 2. Đọc giá trị cài đặt (Setpoint)
                v_set = float(self.instr.query("SOUR:VOLT?").strip())
                c_set = float(self.instr.query("SOUR:CURR?").strip())

                # 3. Đọc giá trị đo lường thực tế (MEAS:VOLT?, MEAS:CURR?, MEAS:POW?)
                v_meas = float(self.instr.query("MEAS:VOLT?").strip())
                c_meas = float(self.instr.query("MEAS:CURR?").strip())
                try:
                    p_meas = float(self.instr.query("MEAS:POW?").strip())
                except Exception:
                    p_meas = round(v_meas * c_meas, 3)

                return {
                    "voltage_measured": round(v_meas, 3),
                    "current_measured": round(c_meas, 3),
                    "power_measured": round(p_meas, 3),
                    "output_state": outp,
                    "voltage_set": round(v_set, 3),
                    "current_set": round(c_set, 3),
                }
            except Exception as e:
                self.is_connected = False
                logger.error(f"Lỗi đọc Telemetry: {e}")
                raise HTTPException(status_code=500, detail=f"Lỗi đọc telemetry thiết bị: {str(e)}")


# Khởi tạo instance singleton
chroma_manager = ChromaManager()

# Wrapper functions
def query_idn() -> str:
    return chroma_manager.query_idn()

def get_system_error() -> str:
    return chroma_manager.get_system_error()

def clear_status() -> bool:
    return chroma_manager.clear_status()

def set_voltage(voltage: float) -> Dict[str, float]:
    return chroma_manager.set_voltage(voltage)

def set_current(current: float) -> Dict[str, float]:
    return chroma_manager.set_current(current)

def control_output(state: str) -> Dict[str, Any]:
    return chroma_manager.control_output(state)

def emergency_stop() -> bool:
    return chroma_manager.emergency_stop()

def get_telemetry() -> Dict[str, Any]:
    return chroma_manager.get_telemetry()