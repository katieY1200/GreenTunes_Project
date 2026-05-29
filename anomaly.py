import joblib
import numpy as np
import os

MODEL_PATH = "model.pkl"
_model = None

# TODO: 센서/농장별로 다르게 설정할 수 있어야 함 — 현재는 전체 동일 기준
FREQ_MIN = 20.0
FREQ_MAX = 100.0
AMP_THRESHOLD = 0.75
NOISE_MAX = 0.30
DURATION_MIN = 2.0
CONSECUTIVE_DANGER = 3


def load_model():
    global _model
    if os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
        print("model loaded")
    else:
        print("model not found — rule-based fallback")


def check_signal_quality(frequency_khz, amplitude, noise_level, duration_ms):
    if not (FREQ_MIN <= frequency_khz <= FREQ_MAX):
        return False, "out_of_band"

    if duration_ms < DURATION_MIN:
        return False, "transient_noise"

    if noise_level > NOISE_MAX:
        return False, "high_noise"

    return True, "valid"


def _compute_risk(amplitude, noise_level, consecutive_count):
    if consecutive_count >= CONSECUTIVE_DANGER:
        return "위험"
    if amplitude >= 0.88 and noise_level <= 0.12:
        return "위험"
    return "주의"


def detect_anomaly(frequency_khz, amplitude, noise_level, duration_ms, recent_readings=None):
    """
    반환: (is_anomaly, risk_level, signal_quality)
    recent_readings: 같은 sensor_id의 최근 기록 (최신순). 연속성 판단에 사용.
    """
    is_valid, quality = check_signal_quality(frequency_khz, amplitude, noise_level, duration_ms)
    if not is_valid:
        return False, "정상", quality

    features = np.array([[frequency_khz, amplitude, noise_level, duration_ms]])
    if _model is not None:
        is_anomaly = bool(_model.predict(features)[0])
    else:
        is_anomaly = amplitude >= AMP_THRESHOLD

    if not is_anomaly:
        return False, "정상", quality

    consecutive_count = 1
    if recent_readings:
        for r in recent_readings:
            if r.is_anomaly:
                consecutive_count += 1
            else:
                break

    return True, _compute_risk(amplitude, noise_level, consecutive_count), quality
