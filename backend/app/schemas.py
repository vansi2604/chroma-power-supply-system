from typing import Literal
from pydantic import BaseModel, Field

class VoltageRequest(BaseModel):
    voltage: float = Field(
        ..., 
        ge=0.0, 
        le=100.0, 
        description="Giá trị điện áp cài đặt (0V đến 100V cho Chroma 62050P-100-100)"
    )

class CurrentRequest(BaseModel):
    current: float = Field(
        ..., 
        ge=0.0, 
        le=100.0, 
        description="Giới hạn dòng điện cài đặt (0A đến 100A cho Chroma 62050P-100-100)"
    )

class OutputRequest(BaseModel):
    state: Literal["ON", "OFF", "on", "off"] = Field(
        ..., 
        description="Trạng thái ngõ ra: 'ON' hoặc 'OFF'"
    )

class TelemetryData(BaseModel):
    voltage_measured: float = Field(..., description="Điện áp thực tế đo được (V)")
    current_measured: float = Field(..., description="Dòng điện thực tế đo được (A)")
    power_measured: float = Field(..., description="Công suất tức thời đo được (W)")
    output_state: str = Field(..., description="Trạng thái ngõ ra hiện tại ('ON' hoặc 'OFF')")
    voltage_set: float = Field(..., description="Mức điện áp đang cài đặt (V)")
    current_set: float = Field(..., description="Mức giới hạn dòng đang cài đặt (A)")

class TelemetryResponse(BaseModel):
    status: str
    connected: bool
    data: TelemetryData