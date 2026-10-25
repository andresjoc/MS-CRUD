from pydantic import BaseModel, EmailStr
from decimal import Decimal
from datetime import date, datetime
from typing import Optional


class CountryCreate(BaseModel):
    name: str


class CountryResponse(BaseModel):
    id_country: int
    name: str

    class Config:
        from_attributes = True


class RegionCreate(BaseModel):
    name: str
    id_country: int


class RegionResponse(BaseModel):
    id_region: int
    name: str
    id_country: int

    class Config:
        from_attributes = True


class CityCreate(BaseModel):
    name: str
    id_region: int


class CityResponse(BaseModel):
    id_city: int
    name: str
    id_region: int

    class Config:
        from_attributes = True


class AppUserCreate(BaseModel):
    id_city: int
    email: EmailStr
    first_name: str
    last_name: str
    birth_date: date


class AppUserResponse(BaseModel):
    id_user: int
    id_city: Optional[int] = None
    email: EmailStr
    first_name: str
    last_name: str
    birth_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthRecordCreate(BaseModel):
    weight_kg: float
    height_cm: float


class HealthRecordResponse(BaseModel):
    id_health_record: int
    id_user: int
    weight_kg: float
    height_cm: float
    recorded_at: datetime

    class Config:
        from_attributes = True


class WearableModelCreate(BaseModel):
    brand: str
    model: str


class WearableModelResponse(BaseModel):
    id_wearable_model: int
    brand: str
    model: str

    class Config:
        from_attributes = True


class WearableCreate(BaseModel):
    id_wearable_model: int


class WearableResponse(BaseModel):
    id_wearable: int
    id_user: int
    id_wearable_model: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MonitoringSessionCreate(BaseModel):
    id_compute_status: int
    id_wearable: Optional[int] = None
    date_time: datetime
    is_delta_encoded: bool = False


class MonitoringSessionResponse(BaseModel):
    id_session: int
    id_user: int
    id_wearable: Optional[int] = None
    id_compute_status: int
    date_time: datetime
    created_at: datetime
    updated_at: datetime
    is_delta_encoded: bool

    class Config:
        from_attributes = True


class MetricTypeCreate(BaseModel):
    unit: str
    min_value: Decimal
    max_value: Decimal
    is_derived: bool = False
    name: str


class MetricTypeResponse(BaseModel):
    id_metric_type: int
    unit: str
    min_value: Decimal
    max_value: Decimal
    is_derived: bool
    name: str

    class Config:
        from_attributes = True


class MeasurementCreate(BaseModel):
    id_metric_type: int
    id_session: int
    value: Decimal
    error_message: str | None = None


class MeasurementResponse(BaseModel):
    id_measurement: int
    id_metric_type: int
    id_session: int
    value: Optional[Decimal] = None
    error_message: str | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class SeverityLevelCreate(BaseModel):
    name: str
    description: str


class SeverityLevelResponse(BaseModel):
    id_severity_level: int
    name: str
    description: str

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    id_session: int
    id_severity_level: int
    description: str


class AlertResponse(BaseModel):
    id_alert: int
    id_session: int
    id_severity_level: int
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComputeStatusCreate(BaseModel):
    name: str
    description: str


class ComputeStatusResponse(BaseModel):
    id_compute_status: int
    name: str
    description: str

    class Config:
        from_attributes = True


class PpgSampleCreate(BaseModel):
    id_session: int
    ts: int
    green: int
    red: Optional[int] = None
    ir: Optional[int] = None


class PpgSampleResponse(BaseModel):
    id_ppg_sample: int
    id_session: int
    ts: int
    green: int
    red: Optional[int] = None
    ir: Optional[int] = None

    class Config:
        from_attributes = True


class HistoryMeasurementResponse(BaseModel):
    id_measurement: int
    id_metric_type: int
    metric_name: str
    unit: str
    value: Optional[Decimal] = None
    error_message: str | None = None
    recorded_at: datetime


class HistoryPpgSampleResponse(BaseModel):
    ts: int
    green: int
    red: Optional[int] = None
    ir: Optional[int] = None


class HistoryAlertResponse(BaseModel):
    id_alert: int
    severity_name: str | None = None
    description: str
    created_at: datetime


class HistoryWearableModelResponse(BaseModel):
    id_wearable_model: int
    brand: str
    model: str


class HistoryWearableResponse(BaseModel):
    id_wearable: int
    id_wearable_model: int
    model: HistoryWearableModelResponse | None = None


class HistorySessionResponse(BaseModel):
    id_session: int
    id_wearable: Optional[int] = None
    date_time: datetime
    created_at: datetime
    updated_at: datetime
    is_delta_encoded: bool
    compute_status: str | None = None
    measurements: list[HistoryMeasurementResponse]
    samples: list[HistoryPpgSampleResponse] = []
    alerts: list[HistoryAlertResponse]
    wearable: HistoryWearableResponse | None = None


class BatchMeasurementItem(BaseModel):
    id_metric_type: int
    value: Decimal
    error_message: Optional[str] = None


class BatchSampleItem(BaseModel):
    ts: int
    green: int
    red: Optional[int] = None
    ir: Optional[int] = None


class BatchAlertItem(BaseModel):
    id_severity_level: int
    description: str


class MonitoringSessionBatchCreate(BaseModel):
    id_compute_status: int
    id_wearable: Optional[int] = None
    date_time: datetime
    is_delta_encoded: bool = False
    samples: list[BatchSampleItem] = []
    measurements: list[BatchMeasurementItem] = []
    alert: Optional[BatchAlertItem] = None


class MonitoringSessionBatchResponse(BaseModel):
    id_session: int
    id_user: int
    samples_inserted: int
    measurement_ids: list[int]
    alert_id: Optional[int] = None

    class Config:
        from_attributes = True


class ClinicalRecordSyncItem(BaseModel):
    id: str
    patient_code: str
    capture_index: int = 1
    cohort: str
    age: int
    biological_sex: str
    weight_kg: Decimal
    height_cm: Decimal
    skin_temperature: Decimal
    fitzpatrick_scale: int
    wrist: str
    has_af_history: bool = False
    af_subtype: Optional[str] = None
    time_since_diagnosis: Optional[str] = None
    comorbidities: list[str] = []
    cardio_drugs_12h: list[str] = []
    device_history: list[str] = []
    observations: Optional[str] = None
    ecg_rhythm_diagnosis: str
    ecg_modality: str
    evaluating_physician: Optional[str] = None
    ecg_taken_at: Optional[datetime] = None
    ai_af_detected: bool
    ai_confidence: Decimal
    heart_rate_bpm: Decimal
    hrv_rmssd: Decimal
    hrv_sdnn: Optional[Decimal] = Decimal("0.0")
    is_tachycardic: bool = False
    recorded_beats_count: int = 0
    recording_duration_seconds: int = 60
    validation_outcome: Optional[str] = None
    raw_ppg_data: Optional[dict] = None
    sync_status: Optional[str] = "SYNCED"
    created_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        extra = "allow"


class ClinicalBatchSyncRequest(BaseModel):
    records: list[dict]


class ClinicalBatchSyncResponse(BaseModel):
    status: str
    synced_count: int
    synced_ids: list[str]
    evaluator_user_id: Optional[int] = None
