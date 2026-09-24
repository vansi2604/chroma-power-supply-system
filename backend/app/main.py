from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import hardware
from app.schemas import (
    VoltageRequest, 
    CurrentRequest, 
    OutputRequest, 
    TelemetryResponse,
    TelemetryData
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo kết nối VISA khi FastAPI khởi động
    hardware.chroma_manager.connect()
    yield
    # Giải phóng tài nguyên VISA an toàn khi tắt server
    hardware.chroma_manager.disconnect()

app = FastAPI(
    title="Chroma 62050P-100-100 Control & Telemetry System",
    description="Hệ thống điều khiển và giám sát thời gian thực máy nguồn Chroma 62050P-100-100",
    version="2.0.0",
    lifespan=lifespan
)

# Cấu hình CORS mở cho giao diện Web Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/idn")
def api_get_idn():
    """Kiểm tra kết nối và trả về định danh thiết bị (*IDN?)."""
    device_info = hardware.query_idn()
    return {
        "status": "success", 
        "connected": hardware.chroma_manager.is_connected,
        "device_id": device_info
    }

@app.get("/api/error")
def api_get_error():
    """Đọc thông báo lỗi từ phần cứng Chroma (SYSTem:ERRor?)."""
    error_info = hardware.get_system_error()
    return {
        "status": "success",
        "error": error_info
    }

@app.post("/api/clear")
def api_clear_status():
    """Xóa sạch cờ trạng thái và bộ nhớ lỗi (*CLS)."""
    hardware.clear_status()
    return {
        "status": "success",
        "message": "Đã gửi lệnh xóa lỗi *CLS thành công."
    }

@app.get("/api/telemetry", response_model=TelemetryResponse)
def api_get_telemetry():
    """
    Đọc dữ liệu tức thời (Real-time Telemetry):
    - Điện áp đo được (V)
    - Dòng điện đo được (A)
    - Công suất đo được (W)
    - Trạng thái ngõ ra (ON/OFF)
    - Mức điện áp đang cài đặt (V)
    - Mức giới hạn dòng điện đang cài đặt (A)
    """
    telemetry = hardware.get_telemetry()
    return TelemetryResponse(
        status="success",
        connected=hardware.chroma_manager.is_connected,
        data=TelemetryData(**telemetry)
    )

@app.post("/api/voltage")
def api_set_voltage(data: VoltageRequest):
    """Cài đặt điện áp ngõ ra (0V - 100V) và nhận về thông số xác nhận từ máy nguồn."""
    result = hardware.set_voltage(data.voltage)
    return {
        "status": "success",
        "voltage": result["voltage_set"],
        "voltage_requested": data.voltage,
        "voltage_set": result["voltage_set"],
        "voltage_measured": result["voltage_measured"]
    }

@app.post("/api/current")
def api_set_current(data: CurrentRequest):
    """Cài đặt giới hạn dòng điện (0A - 100A) và nhận về thông số xác nhận từ máy nguồn."""
    result = hardware.set_current(data.current)
    return {
        "status": "success",
        "current": result["current_set"],
        "current_requested": data.current,
        "current_set": result["current_set"],
        "current_measured": result["current_measured"]
    }

@app.post("/api/output")
def api_control_output(data: OutputRequest):
    """Bật/Tắt ngõ ra nguồn (ON/OFF) và nhận về thông số xác nhận từ máy nguồn."""
    result = hardware.control_output(data.state)
    return {
        "status": "success",
        "output": result["output_state"],
        "voltage_measured": result["voltage_measured"],
        "current_measured": result["current_measured"]
    }

@app.post("/api/emergency-stop")
def api_emergency_stop():
    """Dừng khẩn cấp: Ngắt ngõ ra ngay lập tức và xóa thanh ghi lỗi (*CLS)."""
    hardware.emergency_stop()
    return {"status": "success", "message": "Đã ngắt ngõ ra và gửi lệnh xóa lỗi khẩn cấp."}