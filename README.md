# GreenTunes 센서 모니터링 MVP

> 식물 초음파 센서 데이터 기반 이상 신호 분석 및 모니터링 시스템

---

## 프로젝트 실행 방법

**요구 환경:** Python 3.9 이상

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. ML 모델 학습 
python train_model.py

# 3. 임시 데이터 수집 (Random)
python seed_data.py

# 4. 서버 실행
uvicorn main:app --reload
```

- 대시보드: http://localhost:8000
- API 문서 (Swagger UI): http://localhost:8000/docs

---

## 기술 스택 및 선택 이유

- FastAPI: Python 기반 AI 모델과 연결이 쉽고 빠른 MVP 구현이 가능하며, /docs Swagger API 생성이 가능합니다.
- Jinja2 + Tailwind CDN + Chart.js: 복잡한 프론트엔드 설정 없이 빠르게 화면 구현이 가능하며, Chart.js를 통해 데이터 시각화를 적용할 수 있습니다.
- SQLite + SQLAlchemy ORM: 가볍고 초기 설정이 간단해 빠른 개발에 적합하며, 추후 MySQL과 같은 DB로 변경하기 쉽습니다.
- scikit-learn RandomForest: 표 형태의 센서 데이터 처리에 적합하며, 학습 속도가 빠르고 결과를 쉽게 해석할 수 있습니다.

### 설계 결정 사항

Q. rule-based와 ML 병행 이유

처음에는 실제 현장 데이터에 대한 정답(label) 데이터가 없어서, 먼저 rule-based 기준을 만들고 이를 기반으로 ML 모델을 학습시켰습니다. 기준 없이 바로 ML만 사용하는 것보다 결과를 검증하기 쉽다고 생각했습니다. 또한 실제 운영에서는 threshold 값만 조정해도 빠르게 대응할 수 있어 유지보수 측면에서도 유리하다고 판단했습니다. model.pkl 파일이 없을 경우 rule-based 방식으로 자동 전환되도록 구성한 것도 같은 이유입니다.

실제 서비스 환경에서는 raw 초음파 데이터를 스펙트로그램으로 변환한 뒤 CNN 같은 딥러닝 모델로 처리하는 방식이 더 적합할 수 있다고 생각했습니다. 하지만 이번 과제에서는 이미 주파수, 진폭 등의 특징값이 정리된 표 형태(tabular) 데이터가 제공되었기 때문에, 이에 맞는 RandomForest 모델을 선택했습니다. 비교적 빠르게 학습할 수 있고, 어떤 값이 판단에 영향을 주었는지 확인하기 쉽다는 점도 고려했습니다.

Q. 신호 품질 필터를 이상 판단 앞에 배치한 이유

노이즈가 심한 환경에서는 amplitude 값이 실제보다 크게 튈 수 있어서 false positive가 많이 발생할 수 있습니다. 또 측정 범위를 벗어난 주파수나 너무 짧게 들어오는 신호는 실제 이상 상황보다는 장비 오류나 순간 간섭일 가능성이 높다고 판단했습니다. 그래서 ML 모델에 넣기 전에 이런 데이터들을 먼저 걸러내도록 구성했습니다. 정확도 자체보다도 실제 운영에서 신뢰할 수 있는 결과를 만드는 게 더 중요하다고 생각했습니다.

Q. 단발·연속 이벤트 구분 이유

센서 환경에서는 threshold를 한 번 넘었다고 해서 바로 위험 상황이라고 보기 어려운 경우가 많다고 생각했습니다. 순간적인 간섭이나 센서 흔들림일 수도 있기 때문입니다. 그래서 연속적으로 이상 신호가 발생했을 때만 위험으로 판단하도록 해서 불필요한 알림을 줄이고, 실제 운영자가 신뢰할 수 있는 형태로 만들고 싶었습니다.

Q. raw 데이터와 분석 결과 분리 이유

원본 센서 데이터는 그대로 보관하고, 이상 탐지 결과만 별도 테이블로 관리하도록 구성했습니다. 나중에 threshold를 바꾸거나 탐지 로직을 수정했을 때 원본 데이터를 기반으로 다시 분석할 수 있게 하기 위해서입니다. 만약 원본 데이터에 결과를 바로 덮어쓰는 구조였다면 이전 기준으로 어떻게 탐지됐는지 추적하기 어렵다고 생각했습니다.

### Trade-offs

SQLite vs MySQL
SQLite는 파일 하나로 관리할 수 있어 초기 개발에 용이합니다. 이후 센서 수나 요청량이 증가할 경우 성능 문제가 발생할 수 있습니다. 그래서 SQLAlchemy ORM을 사용해 추후 MySQL 같은 서버형 DB로 쉽게 확장할 수 있도록 구성했습니다.

Jinja2(SSR) vs React(SPA)
현재 대시보드는 수동 갱신 방식이라 SSR이 구조상 더 단순합니다. 빌드 환경도 필요 없어서 MVP 속도에서 유리합니다. 실시간 알림이나 센서별 자동 갱신이 필요해지면 WebSocket + SPA 구조로 전환해야 합니다.

Rule-based 라벨로 ML 학습
실제 현장 레이블 데이터가 없어서 rule-based 기준으로 학습 데이터를 만들었습니다. 모델이 사실상 규칙을 학습하는 셈이라 정확도가 높게 나오지만, 실제 식물 반응 패턴과 다를 가능성이 있습니다. 현장 데이터가 쌓이면 라벨만 교체해 재학습할 수 있도록 파이프라인을 분리해뒀습니다.

단일 서버 동기 처리
현재는 센서가 HTTP POST로 직접 서버에 데이터를 보내는 방식입니다. 구조가 단순하고 디버깅이 쉬운 반면, 센서가 많아지면 burst traffic에 취약합니다. 추후에 개선 여지가 있습니다.

---

## API 명세

### `GET /health`
서버 상태 확인

**Response**
```json
{ "status": "ok", "timestamp": "2026-05-29T01:07:27.045126+00:00" }
```

---

### `POST /api/sensor-data`
센서 데이터 저장 및 이상 신호 자동 판정

수신 즉시 신호 품질 필터 → ML 판단 → 연속성 분석의 3단계로 처리됩니다.

**Request Body**
```json
{
  "sensor_id": "sensor-001",
  "farm_id": "farm-A",
  "timestamp": "2026-05-29T10:00:00",
  "frequency_khz": 42.1,
  "amplitude": 0.78,
  "noise_level": 0.12,
  "duration_ms": 3.4
}
```

**Response**
```json
{
  "id": 1,
  "sensor_id": "sensor-001",
  "farm_id": "farm-A",
  "timestamp": "2026-05-29T10:00:00",
  "frequency_khz": 42.1,
  "amplitude": 0.78,
  "noise_level": 0.12,
  "duration_ms": 3.4,
  "is_anomaly": true,
  "risk_level": "주의",
  "signal_quality": "valid",
  "created_at": "2026-05-29T01:07:27"
}
```

`signal_quality` 가능한 값: `valid` | `out_of_band` | `transient_noise` | `high_noise`

---

### `GET /api/sensor-data`
센서 데이터 목록 조회

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `farm_id` | string | 농장 ID 필터 |
| `sensor_id` | string | 센서 ID 필터 |
| `from` | datetime | 조회 시작 시각 (ISO 8601) |
| `to` | datetime | 조회 종료 시각 (ISO 8601) |
| `limit` | int | 최대 건수 (기본 100, 최대 1000) |

---

### `GET /api/anomalies`
이상 신호로 판정된 개별 센서 레코드 조회

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `farm_id` | string | 농장 ID 필터 |
| `sensor_id` | string | 센서 ID 필터 |

---

### `GET /api/anomaly-events`
연속 이상신호를 하나의 이벤트로 묶은 집계 결과 조회

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `resolved` | boolean | `false`: 진행 중인 이벤트만, `true`: 종료된 이벤트만 |

**Response 예시**
```json
{
  "id": 1,
  "sensor_id": "sensor-001",
  "farm_id": "farm-A",
  "first_seen_at": "2026-05-29T12:01:00",
  "last_seen_at": "2026-05-29T12:03:00",
  "consecutive_count": 3,
  "peak_amplitude": 0.913,
  "risk_level": "위험",
  "resolved": false
}
```

---

## 프론트엔드 화면 구성

- **요약 카드**: 전체 / 정상 / 주의 / 위험 건수 + 마지막 이상 탐지 시각
- **Amplitude 시계열 그래프**: 최근 60건, threshold 점선(0.75) 표시, 이상 포인트 크기·색상 강조
- **위험도 분포 도넛 차트**: 정상 / 주의 / 위험 비율 시각화
- **진행 중인 이상 이벤트**: 연속 횟수·최대 amplitude·시작 시각 표시
- **이상 신호 테이블**: 최신 20건, signal_quality로 신호 품질 확인 가능
- **농장 선택 드롭다운**: 농장별 필터링, 선택 즉시 갱신

---

## 이상 신호 판단 로직

1단계: 신호 품질 필터

이상 판단 이전에 신호 자체의 유효성을 먼저 검증합니다. 유효하지 않은 신호를 이상신호로 오인하면 false positive가 발생합니다.

- `frequency_khz` < 20 또는 > 100 → `out_of_band` (식물 생체신호 유효 대역 외부)
- `duration_ms` < 2.0 → `transient_noise` (지속 시간 짧음, 전기 간섭 등 순간 노이즈)
- `noise_level` > 0.30 → `high_noise` (노이즈 비율 높으면 amplitude 값 신뢰 불가)

2단계: 이상신호 판단 (ML / rule-based)

신호 품질이 `valid`인 경우에만 ML 모델 또는 rule-based 로직으로 이상 여부를 판단합니다.

- `frequency_khz`: 20 ~ 100 kHz
- `amplitude`: ≥ 0.75
- `noise_level`: ≤ 0.30
- `duration_ms`: ≥ 2.0 ms

3단계: 연속성 분석

단발 이벤트와 지속적인 이상 상태를 구분하여 위험도를 결정합니다.

- 연속 3회 이상 이상신호 → 위험
- amplitude ≥ 0.88 + noise_level ≤ 0.12 → 위험 (1회도 즉시 격상)
- 그 외 이상신호 → 주의
- 이상신호 아님 → 정상

ML 모델 (RandomForestClassifier)

rule-based 기준을 라벨로 활용하여 RandomForest를 학습했습니다. 

- 학습 샘플: 2,000건 (80% train / 20% test)
- 모델: RandomForestClassifier (n_estimators=100)
- Accuracy: 0.97 / Precision: 0.80 / Recall: 0.57 / F1: 0.67

> Recall 개선 계획: 현재 데이터에서는 이상 신호 비율이 적어 정상 데이터에 비해 학습이 불균형하게 이루어졌습니다. 이후 실제 데이터를 확보하면 데이터 균형을 맞추는 방식(class weight 조정 등)을 적용해 이상 신호를 더 잘 탐지할 수 있도록 개선할 예정입니다. 이상 탐지에서는 정상 데이터를 잘 맞추는 것보다 위험 상황을 놓치지 않는 것이 더 중요하다고 판단해 Recall을 주요 지표로 설정했습니다.

---

## DB 구조

### sensor_data — 원시 센서 스트림

```sql
CREATE TABLE sensor_data (
    id             INTEGER  PRIMARY KEY AUTOINCREMENT,
    sensor_id      TEXT     NOT NULL,
    farm_id        TEXT     NOT NULL,
    timestamp      DATETIME NOT NULL,
    frequency_khz  REAL     NOT NULL,
    amplitude      REAL     NOT NULL,
    noise_level    REAL     NOT NULL,
    duration_ms    REAL     NOT NULL,
    is_anomaly     BOOLEAN  NOT NULL DEFAULT 0,
    risk_level     TEXT     NOT NULL DEFAULT '정상',
    signal_quality TEXT     NOT NULL DEFAULT 'valid',
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### anomaly_events — 분석 결과 (연속 이벤트 집계)

```sql
CREATE TABLE anomaly_events (
    id                INTEGER  PRIMARY KEY AUTOINCREMENT,
    sensor_id         TEXT     NOT NULL,
    farm_id           TEXT     NOT NULL,
    first_seen_at     DATETIME NOT NULL,
    last_seen_at      DATETIME NOT NULL,
    consecutive_count INTEGER  DEFAULT 1,
    peak_amplitude    REAL     NOT NULL,
    risk_level        TEXT     NOT NULL,
    resolved          BOOLEAN  DEFAULT 0,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

두 테이블을 분리한 이유는 detection 로직 변경이나 threshold 튜닝 시 원본 스트림(sensor_data)을 보존한 채 anomaly_events만 재생성할 수 있기 때문입니다.

인덱스: `sensor_id`, `farm_id`

---

## 실제 서비스 확장 시 개선 방향

### 현재 구조의 한계와 확장 경로

현재는 단일 서버 기반 동기 처리 MVP입니다. 수백 개 센서가 동시에 데이터를 보내는 환경으로 확장할 때 다음과 같은 구조 변경이 필요합니다.

- **HTTP → MQTT / Kafka**: 현재는 센서가 HTTP 요청으로 직접 데이터를 보내는 구조입니다. 다수의 센서가 동시에 데이터를 전송하면 서버 부하가 커질 수 있어, 이후에는 메시지 큐 기반 구조로 변경해 수신과 처리를 분리하는 방향을 고려했습니다.
- **SQLite → MySQL**: 현재는 SQLite를 사용해 빠르게 개발했지만, 데이터 양이 많아질 경우 MySQL 같은 서버형 DB로 전환해 안정적으로 운영할 수 있도록 고려했습니다.
- **REST → WebSocket**: 현재 대시보드는 수동 새로고침 방식입니다. 이후 실시간 모니터링이 중요해질 경우 WebSocket 기반 실시간 갱신 구조로 확장할 수 있습니다.
- **Edge preprocessing**: 센서 단에서 노이즈 필터링 등 간단한 전처리를 먼저 수행하면 서버 부하와 네트워크 사용량을 줄일 수 있다고 생각했습니다.

### 데이터 신뢰성

- 센서 데이터가 일시적으로 끊기더라도 유실되지 않도록 로컬 버퍼 및 재전송 구조를 추가할 수 있습니다.
- 여러 센서를 동시에 분석할 경우 시간 오차가 중요하기 때문에 타임스탬프 동기화가 필요합니다.
- 순간적인 노이즈를 줄이기 위해 연속 데이터 평균 기반 필터를 추가 적용할 수 있습니다.

### ML 고도화

- 현재는 이상 여부만 판단하지만, 이후에는 원인까지 분류하는 방향으로 확장할 수 있습니다.
- 새로운 이상 패턴이 발생했을 때 지속적으로 학습할 수 있는 구조도 고려할 수 있습니다.
- Feature Importance 시각화를 통해 어떤 값이 판단에 영향을 주었는지 사용자에게 제공할 수 있습니다.
- 농장 환경이나 계절에 따라 threshold를 자동 조정하는 방식도 필요하다고 생각했습니다.

### 확장성 설계

- 시계열 조회 성능 개선을 위해 (farm_id, timestamp) 기반 인덱스를 추가할 수 있습니다.
- 여러 센서 데이터를 한 번에 저장할 수 있는 batch API 구조로 확장할 수 있습니다.
- 오래된 데이터는 별도 스토리지에 저장해 운영 비용을 줄이는 방향도 고려했습니다.

### 운영 환경에서 고려한 예외 상황

이번 MVP에서는 핵심 기능 구현에 집중했지만, 운영 환경에서는 다음과 같은 예외 상황 대응이 추가로 필요하다고 판단했습니다.

- 비정상 입력값 검증 : 음수 amplitude, 미래 timestamp, 비정상적으로 긴 sensor_id 등 물리적으로 의미 없는 입력값에 대한 검증이 필요합니다.

- 모델 파일 손상 대응 : model.pkl 파일이 손상되거나 로드에 실패할 경우 예측 기능이 중단될 수 있어 fallback 처리 및 예외 로깅이 필요합니다.

- 노이즈 데이터 처리 : NaN 값이나 순간적인 스파이크 노이즈가 들어올 경우 예측 결과가 왜곡될 수 있어 사전 필터링이 필요합니다.

- 센서 데이터 범위 검증 : 잘못된 날짜 범위 조회나 비정상 limit 요청 등에 대한 방어 로직이 필요합니다.

- DB 장애 대응 : 디스크 용량 부족이나 DB 연결 실패 상황에서 데이터 유실을 방지하기 위한 retry 및 buffering 구조를 고려할 수 있습니다.

현재는 MVP 단계이기 때문에 핵심 흐름 구현에 집중했고, 이후 운영 단계에서는 입력 검증과 장애 대응 로직을 우선적으로 보완할 계획입니다.
