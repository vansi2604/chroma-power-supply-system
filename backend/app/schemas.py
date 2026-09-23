from pydantic import BaseModel, Field

class VoltageRequest(BaseModel):
    voltage: float = Field(..., description="Giá trị điện áp đầu ra (Volt)")

class CurrentRequest(BaseModel):
    current: float = Field(..., description="Giới hạn dòng điện (Ampere)")

class OutputRequest(BaseModel):
    state: str = Field(..., description="Trạng thái ngõ ra: 'ON' hoặc 'OFF'")