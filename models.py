from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime, timezone
from database import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    farm_id = Column(String, index=True)
    timestamp = Column(DateTime)
    frequency_khz = Column(Float)
    amplitude = Column(Float)
    noise_level = Column(Float)
    duration_ms = Column(Float)
    is_anomaly = Column(Boolean, default=False)
    risk_level = Column(String, default="정상")
    signal_quality = Column(String, default="valid")  # valid | out_of_band | transient_noise | high_noise
    created_at = Column(DateTime, default=utcnow)


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    farm_id = Column(String)
    first_seen_at = Column(DateTime)
    last_seen_at = Column(DateTime)
    consecutive_count = Column(Integer, default=1)
    peak_amplitude = Column(Float)
    risk_level = Column(String)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
