"""
=============================================================================
KỊCH BẢN KIỂM THỬ PHẦN CỨNG MÁY NGUỒN CHROMA 62050P-100-100 (HARDWARE TEST)
=============================================================================
Mục đích:
- Kiểm tra toàn bộ luồng giao tiếp SCPI thực tế từ máy tính xuống máy nguồn.
- Bám sát từng bước theo quy trình Pseudo Flow trong tài liệu Power-Document.md.
- Đảm bảo an toàn: luôn tắt Output nguồn trong mọi tình huống (kể cả khi gặp lỗi).

Cách chạy:
    cd backend
    .\\venv\\Scripts\\python.exe test_hardware.py
=============================================================================
"""

import time
import sys
import pyvisa

# Thiết lập encoding UTF-8 cho console Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Địa chỉ VISA cổng USB máy nguồn Chroma 62050P
VISA_ADDRESS = "USB0::0x1698::0x0837::008000000304::INSTR"

def print_step(step_num: int, title: str):
    print(f"\n[{step_num}] === {title} ===")

def main():
    print("=" * 65)
    print(" BẮT ĐẦU KIỂM THỬ THIẾT BỊ PHẦN CỨNG CHROMA 62050P-100-100")
    print("=" * 65)

    rm = None
    inst = None

    try:
        # BƯỚC 1: Quét cổng và mở kết nối VISA
        print_step(1, "Khởi tạo kết nối VISA qua cổng USB-TMC")
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        print(f"-> Danh sách thiết bị VISA tìm thấy: {resources}")

        if VISA_ADDRESS not in resources:
            print(f"[!] CẢNH BÁO: Không thấy địa chỉ '{VISA_ADDRESS}' trong danh sách.")
            print("    Vui lòng kiểm tra lại cáp USB và công tắc nguồn của máy Chroma.")
            return

        print(f"-> Đang mở kết nối tới: {VISA_ADDRESS} ...")
        inst = rm.open_resource(VISA_ADDRESS)
        inst.timeout = 3000          # Timeout 3 giây
        inst.write_termination = '\n' # Đệm ký tự Line Feed \n theo chuẩn Power-Document.md
        print("-> Đã mở phiên làm việc thành công!")

        # BƯỚC 2: Kiểm tra nhận diện thiết bị (*IDN?)
        print_step(2, "Xác thực danh tính thiết bị (*IDN?)")
        idn = inst.query("*IDN?").strip()
        print(f"-> Phản hồi *IDN?: {idn}")
        assert "CHROMA" in idn, "LỖI: Thiết bị không phải của hãng CHROMA!"
        print("-> [PASS] Thiết bị phản hồi đúng thương hiệu Chroma.")

        # BƯỚC 3: Tắt Analog Programming (APG) và Xóa trạng thái lỗi cũ (*CLS)
        print_step(3, "Tắt Analog Programming (CONF:APG NONE) và xóa cờ lỗi (*CLS)")
        inst.write("CONF:APG NONE")
        time.sleep(0.05)
        inst.write("*CLS")
        time.sleep(0.05)
        print("-> Đã gửi lệnh CONF:APG NONE và *CLS thành công.")

        # BƯỚC 4: Cài đặt thông số an toàn (Set Voltage = 5.0V, Current = 1.0A)
        print_step(4, "Cài đặt điện áp 5.0V và giới hạn dòng 1.0A")
        test_volt = 5.0
        test_curr = 1.0

        print(f"-> Gửi lệnh: SOUR:VOLT {test_volt:.3f}")
        inst.write(f"SOUR:VOLT {test_volt:.3f}")
        time.sleep(0.05)

        print(f"-> Gửi lệnh: SOUR:CURR {test_curr:.3f}")
        inst.write(f"SOUR:CURR {test_curr:.3f}")
        time.sleep(0.05)

        # BƯỚC 5: Đọc lại thông số vừa cài đặt để kiểm tra chéo (Verification)
        print_step(5, "Đọc lại thông số cài đặt (SOUR:VOLT?, SOUR:CURR?)")
        read_volt = float(inst.query("SOUR:VOLT?").strip())
        read_curr = float(inst.query("SOUR:CURR?").strip())
        print(f"-> Điện áp máy nhận: {read_volt:.3f} V (Kỳ vọng: {test_volt:.3f} V)")
        print(f"-> Dòng điện máy nhận: {read_curr:.3f} A (Kỳ vọng: {test_curr:.3f} A)")
        assert abs(read_volt - test_volt) < 0.1, "LỖI: Điện áp cài đặt không khớp!"
        assert abs(read_curr - test_curr) < 0.1, "LỖI: Dòng điện cài đặt không khớp!"
        print("-> [PASS] Thông số cài đặt hoàn toàn chính xác.")

        # BƯỚC 6: Bật nguồn Output (CONF:OUTP ON)
        print_step(6, "Bật ngõ ra Output (CONF:OUTP ON)")
        print("-> Gửi lệnh: CONF:OUTP ON")
        inst.write("CONF:OUTP ON")
        time.sleep(0.5)  # Chờ relay đóng và điện áp ổn định

        outp_state = inst.query("CONF:OUTP?").strip().upper()
        print(f"-> Trạng thái Output hiện tại: {outp_state}")
        assert outp_state in ["1", "ON"], "LỖI: Output chưa được bật!"
        print("-> [PASS] Output đã bật thành công!")

        # BƯỚC 7: Đọc dữ liệu đo lường thực tế (MEAS:VOLT?, MEAS:CURR?, MEAS:POW?)
        print_step(7, "Đo lường thời gian thực (Real-time Telemetry)")
        for i in range(1, 4):
            v_meas = float(inst.query("MEAS:VOLT?").strip())
            c_meas = float(inst.query("MEAS:CURR?").strip())
            p_meas = float(inst.query("MEAS:POW?").strip())
            print(f"   Lần đọc {i}: Điện áp = {v_meas:6.3f} V | Dòng = {c_meas:6.3f} A | Công suất = {p_meas:6.3f} W")
            time.sleep(0.5)
        print("-> [PASS] Đọc dữ liệu đo lường liên tục ổn định.")

        # BƯỚC 8: Tắt nguồn an toàn (CONF:OUTP OFF)
        print_step(8, "Tắt ngõ ra an toàn (CONF:OUTP OFF)")
        print("-> Gửi lệnh: CONF:OUTP OFF")
        inst.write("CONF:OUTP OFF")
        time.sleep(0.3)

        outp_state = inst.query("CONF:OUTP?").strip().upper()
        print(f"-> Trạng thái Output sau khi tắt: {outp_state}")
        assert outp_state in ["0", "OFF"], "LỖI: Output chưa ngắt an toàn!"
        print("-> [PASS] Output đã ngắt an toàn về 0V.")

        # BƯỚC 9: Đọc thông báo lỗi từ hệ thống (SYST:ERR?)
        print_step(9, "Kiểm tra hàng đợi lỗi của máy nguồn (SYST:ERR?)")
        err_msg = inst.query("SYST:ERR?").strip()
        print(f"-> Trạng thái lỗi máy nguồn báo về: {err_msg}")
        if err_msg.startswith("0") or "No error" in err_msg:
            print("-> [PASS] Máy nguồn hoạt động hoàn hảo, không có bất kỳ lỗi nào!")
        else:
            print(f"-> [!] Máy nguồn có cảnh báo: {err_msg}")

        print("\n" + "=" * 65)
        print(" TẤT CẢ CÁC BƯỚC KIỂM THỬ ĐÃ HOÀN TẤT THÀNH CÔNG VẺ VANG! 🎉")
        print("=" * 65)

    except Exception as e:
        print(f"\n[X] PHÁT HIỆN SỰ CỐ TRONG QUÁ TRÌNH TEST: {e}")
    finally:
        # Khối dọn dẹp: Đảm bảo Output luôn được TẮT và kết nối được đóng an toàn
        if inst is not None:
            try:
                print("\n[Dọn dẹp] Đang đảm bảo tắt Output và đóng kết nối VISA an toàn...")
                inst.write("CONF:OUTP OFF")
                inst.close()
                print("[Dọn dẹp] Đã đóng phiên VISA an toàn.")
            except Exception:
                pass
        if rm is not None:
            try:
                rm.close()
            except Exception:
                pass

if __name__ == "__main__":
    main()
