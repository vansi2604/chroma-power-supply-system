import pyvisa
from fastapi import HTTPException

# Địa chỉ VISA cố định của máy nguồn Chroma 62050P
VISA_ADDRESS = "USB0::0x1698::0x0837::008000000304::INSTR"

def get_instrument():
    """Mở kết nối phiên làm việc với thiết bị qua PyVISA."""
    try:
        rm = pyvisa.ResourceManager()
        instr = rm.open_resource(VISA_ADDRESS)
        instr.timeout = 2000  # Timeout 2 giây
        return instr
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Không thể kết nối phần cứng Chroma 62050P: {str(e)}"
        )

def query_idn():
    """Kiểm tra xác thực thiết bị (*IDN?)"""
    instr = get_instrument()
    try:
        idn_response = instr.query("*IDN?")
        return idn_response.strip()
    finally:
        instr.close()

def set_voltage(voltage: float):
    """Cài đặt điện áp đầu ra (Volt)"""
    instr = get_instrument()
    try:
        instr.write(f"SOURce:VOLTage {voltage}")
        return True
    finally:
        instr.close()

def set_current(current: float):
    """Cài đặt giới hạn dòng điện (Ampere)"""
    instr = get_instrument()
    try:
        instr.write(f"SOURce:CURRent {current}")
        return True
    finally:
        instr.close()

def control_output(state: str):
    """Điều khiển trạng thái ngõ ra: 'ON' hoặc 'OFF'"""
    instr = get_instrument()
    try:
        state_upper = state.upper()
        if state_upper in ["ON", "OFF"]:
            instr.write(f"OUTPut {state_upper}")
            return state_upper
        else:
            raise ValueError("Trạng thái ngõ ra chỉ nhận 'ON' hoặc 'OFF'")
    finally:
        instr.close()