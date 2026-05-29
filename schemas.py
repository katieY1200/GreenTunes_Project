from pydantic import BaseModel
from datetime import datetime

class SensorDataCreate(BaseModel):
    sensor_id: str
    farm_id: str
    timestamp: datetime
    frequency_khz: float
    amplitude: float
    noise_level: float
    duration_ms: float


class SensorDataResponse(SensorDataCreate):
    id: int
    is_anomaly: bool
    risk_level: str
    signal_quality: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnomalyEventResponse(BaseModel):
    id: int
    sensor_id: str
    farm_id: str
    first_seen_at: datetime
    last_seen_at: datetime
    consecutive_count: int
    peak_amplitude: float
    risk_level: str
    resolved: bool

    class Config:
        from_attributes = True
