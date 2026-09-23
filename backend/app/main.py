from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import hardware
from app.schemas import VoltageRequest, CurrentRequest, OutputRequest

app = FastAPI(title="Web-based Power Supply Control System", version="1.0.0")

# Cấu hình CORS để cho phép Frontend gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/idn")
def api_get_idn():
    """Kiểm tra kết nối và lấy thông tin thiết bị (*IDN?)"""
    device_info = hardware.query_idn()
    return {"status": "success", "device_id": device_info}

@app.post("/api/voltage")
def api_set_voltage(data: VoltageRequest):
    """Cài đặt điện áp đầu ra"""
    hardware.set_voltage(data.voltage)
    return {"status": "success", "voltage": data.voltage}

@app.post("/api/current")
def api_set_current(data: CurrentRequest):
    """Cài đặt giới hạn dòng điện"""
    hardware.set_current(data.current)
    return {"status": "success", "current": data.current}

@app.post("/api/output")
def api_control_output(data: OutputRequest):
    """Bật/Tắt ngõ ra nguồn (ON/OFF)"""
    state = hardware.control_output(data.state)
    return {"status": "success", "output": state}