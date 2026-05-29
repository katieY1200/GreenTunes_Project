import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone

import database, models, schemas, anomaly

models.Base.metadata.create_all(bind=database.engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    anomaly.load_model()
    yield

app = FastAPI(title="GreenTunes 센서 모니터링 API", version="1.0.0", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/api/sensor-data", response_model=schemas.SensorDataResponse, tags=["Sensor"])
def create_sensor_data(data: schemas.SensorDataCreate, db: Session = Depends(database.get_db)):
    recent = (
        db.query(models.SensorData)
        .filter(models.SensorData.sensor_id == data.sensor_id)
        .order_by(models.SensorData.created_at.desc())
        .limit(5)
        .all()
    )

    is_anom, risk, sig_quality = anomaly.detect_anomaly(
        data.frequency_khz, data.amplitude, data.noise_level, data.duration_ms,
        recent_readings=recent,
    )

    record = models.SensorData(
        **data.model_dump(),
        is_anomaly=is_anom,
        risk_level=risk,
        signal_quality=sig_quality,
    )
    db.add(record)
    db.commit()

    if is_anom:
        existing = (
            db.query(models.AnomalyEvent)
            .filter(
                models.AnomalyEvent.sensor_id == data.sensor_id,
                models.AnomalyEvent.resolved.is_(False),
            )
            .first()
        )
        if existing:
            existing.consecutive_count += 1
            existing.last_seen_at = data.timestamp
            existing.risk_level = risk
            if data.amplitude > existing.peak_amplitude:
                existing.peak_amplitude = data.amplitude
        else:
            db.add(models.AnomalyEvent(
                sensor_id=data.sensor_id,
                farm_id=data.farm_id,
                first_seen_at=data.timestamp,
                last_seen_at=data.timestamp,
                consecutive_count=1,
                peak_amplitude=data.amplitude,
                risk_level=risk,
            ))
    else:
        unresolved = (
            db.query(models.AnomalyEvent)
            .filter(
                models.AnomalyEvent.sensor_id == data.sensor_id,
                models.AnomalyEvent.resolved.is_(False),
            )
            .first()
        )
        if unresolved:
            unresolved.resolved = True

    db.commit()
    db.refresh(record)
    return record


@app.get("/api/sensor-data", response_model=List[schemas.SensorDataResponse], tags=["Sensor"])
def list_sensor_data(
    farm_id: Optional[str] = None,
    sensor_id: Optional[str] = None,
    from_: Optional[datetime] = Query(None, alias="from"),
    to: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(database.get_db),
):
    q = db.query(models.SensorData)
    if farm_id:
        q = q.filter(models.SensorData.farm_id == farm_id)
    if sensor_id:
        q = q.filter(models.SensorData.sensor_id == sensor_id)
    if from_:
        q = q.filter(models.SensorData.timestamp >= from_)
    if to:
        q = q.filter(models.SensorData.timestamp <= to)
    return q.order_by(models.SensorData.timestamp.desc()).limit(limit).all()


@app.get("/api/anomalies", response_model=List[schemas.SensorDataResponse], tags=["Sensor"])
def list_anomalies(
    farm_id: Optional[str] = None,
    sensor_id: Optional[str] = None,
    db: Session = Depends(database.get_db),
):
    q = db.query(models.SensorData).filter(models.SensorData.is_anomaly.is_(True))
    if farm_id:
        q = q.filter(models.SensorData.farm_id == farm_id)
    if sensor_id:
        q = q.filter(models.SensorData.sensor_id == sensor_id)
    return q.order_by(models.SensorData.timestamp.desc()).all()


@app.get("/api/anomaly-events", response_model=List[schemas.AnomalyEventResponse], tags=["Sensor"])
def list_anomaly_events(
    resolved: Optional[bool] = None,
    db: Session = Depends(database.get_db),
):
    q = db.query(models.AnomalyEvent)
    if resolved is not None:
        q = q.filter(models.AnomalyEvent.resolved == resolved)
    return q.order_by(models.AnomalyEvent.last_seen_at.desc()).limit(50).all()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard(
    request: Request,
    farm_id: Optional[str] = None,
    db: Session = Depends(database.get_db),
):
    base = db.query(models.SensorData)
    if farm_id:
        base = base.filter(models.SensorData.farm_id == farm_id)

    total = base.count()
    danger_count = base.filter(models.SensorData.risk_level == "위험").count()
    warning_count = base.filter(models.SensorData.risk_level == "주의").count()
    normal_count = base.filter(models.SensorData.risk_level == "정상").count()

    recent = (
        db.query(models.SensorData)
        .filter(models.SensorData.farm_id == farm_id if farm_id else True)
        .order_by(models.SensorData.timestamp.asc())
        .limit(60)
        .all()
    )

    anom_q = db.query(models.SensorData).filter(models.SensorData.is_anomaly.is_(True))
    if farm_id:
        anom_q = anom_q.filter(models.SensorData.farm_id == farm_id)
    anomalies = anom_q.order_by(models.SensorData.timestamp.desc()).limit(20).all()

    active_events = (
        db.query(models.AnomalyEvent)
        .filter(models.AnomalyEvent.resolved.is_(False))
        .order_by(models.AnomalyEvent.last_seen_at.desc())
        .limit(10)
        .all()
    )

    last_anom = (
        db.query(models.SensorData)
        .filter(models.SensorData.is_anomaly.is_(True))
        .order_by(models.SensorData.timestamp.desc())
        .first()
    )
    last_anomaly_time = str(last_anom.timestamp)[:16] if last_anom else "없음"

    farms = [f[0] for f in db.query(models.SensorData.farm_id).distinct().all()]
    sensors = [s[0] for s in db.query(models.SensorData.sensor_id).distinct().all()]

    n = len(recent)
    chart_labels = json.dumps([str(d.timestamp)[:16] for d in recent])
    chart_amplitudes = json.dumps([round(d.amplitude, 3) for d in recent])
    chart_threshold = json.dumps([0.75] * n)  # threshold line
    point_colors = json.dumps([
        "#ef4444" if d.risk_level == "위험" else
        "#f59e0b" if d.risk_level == "주의" else
        "#22c55e"
        for d in recent
    ])
    point_radii = json.dumps([
        7 if d.is_anomaly else 3
        for d in recent
    ])
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total": total,
        "danger_count": danger_count,
        "warning_count": warning_count,
        "normal_count": normal_count,
        "anomaly_count": danger_count + warning_count,
        "anomalies": anomalies,
        "active_events": active_events,
        "last_anomaly_time": last_anomaly_time,
        "farms": farms,
        "sensors": sensors,
        "selected_farm": farm_id or "",
        "chart_labels": chart_labels,
        "chart_amplitudes": chart_amplitudes,
        "chart_threshold": chart_threshold,
        "point_colors": point_colors,
        "point_radii": point_radii,
    })
