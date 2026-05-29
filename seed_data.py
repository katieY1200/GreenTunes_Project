import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

random.seed(7)

SENSORS = [
    ("sensor-001", "farm-A"),
    ("sensor-002", "farm-A"),
    ("sensor-003", "farm-A"),
    ("sensor-004", "farm-B"),
    ("sensor-005", "farm-B"),
]

def make_record(sensor_id, farm_id, ts, force_anomaly=False):
    if force_anomaly or random.random() < 0.35:
        freq = random.uniform(25, 95)
        amp  = random.uniform(0.75, 1.0)
        noise = random.uniform(0.0, 0.28)
        dur  = random.uniform(2.1, 7.5)
        is_anom = True
        risk = "위험" if amp >= 0.88 and noise <= 0.12 else "주의"
    else:
        freq  = random.choice([random.uniform(1, 18), random.uniform(102, 180)])
        amp   = random.uniform(0.05, 0.72)
        noise = random.uniform(0.32, 0.79)
        dur   = random.uniform(0.3, 1.8)
        is_anom = False
        risk = "정상"

    return models.SensorData(
        sensor_id=sensor_id,
        farm_id=farm_id,
        timestamp=ts,
        frequency_khz=round(freq, 2),
        amplitude=round(amp, 3),
        noise_level=round(noise, 3),
        duration_ms=round(dur, 2),
        is_anomaly=is_anom,
        risk_level=risk,
        signal_quality="valid",
    )

db = SessionLocal()

if db.query(models.SensorData).count() > 0:
    print("SKIP")
    db.close()
    sys.exit(0)

now = datetime.now()
records = []
for i in range(80):
    for sensor_id, farm_id in SENSORS:
        ts = now - timedelta(minutes=i * 5)
        records.append(make_record(sensor_id, farm_id, ts))

db.add_all(records)
db.commit()
db.close()
print(f"seeded {len(records)} records")
