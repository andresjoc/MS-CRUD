from datetime import datetime
from decimal import Decimal
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from dependencies.auth_guard import TokenUser, get_current_user_from_token

router = APIRouter(
    prefix="/clinical_validation",
    tags=["ClinicalValidation"]
)


def _parse_list(val) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str) and val.strip():
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    return []


def _parse_dict(val) -> Optional[dict]:
    if val is None:
        return None
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val.strip():
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return None


def _parse_datetime(val) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str) and val.strip():
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            pass
    return None


@router.post("/batch_upload", response_model=schemas.ClinicalBatchSyncResponse)
def batch_upload_clinical_records(
    payload: schemas.ClinicalBatchSyncRequest,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    """
    Sincronización masiva y transaccional de mediciones clínicas del estudio.
    Asocia todas las mediciones al evaluator_user_id obtenido del JWT.
    """
    if not payload.records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La lista de registros no puede estar vacía"
        )

    synced_ids = []

    try:
        for r in payload.records:
            rec_id = str(r.get("id"))
            patient_code = str(r.get("patient_code") or r.get("patientCode") or "HS-000")
            cohort = str(r.get("cohort") or "AF")
            capture_index = int(r.get("capture_index") or r.get("captureIndex") or 1)
            age = int(r.get("age") or 0)
            biological_sex = str(r.get("biological_sex") or r.get("biologicalSex") or "Masculino")

            weight_kg = Decimal(str(r.get("weight_kg") or r.get("weightKg") or 70.0))
            height_cm = Decimal(str(r.get("height_cm") or r.get("heightCm") or 170.0))
            h_m = height_cm / Decimal("100.0")
            bmi = round(weight_kg / (h_m * h_m), 1) if h_m > 0 else Decimal("0.0")

            skin_temperature = Decimal(str(r.get("skin_temperature") or r.get("skinTemperature") or 33.0))
            fitzpatrick_scale = int(r.get("fitzpatrick_scale") or r.get("fitzpatrickScale") or 3)
            wrist = str(r.get("wrist") or "Izquierda")

            has_af_history = bool(r.get("has_af_history") if "has_af_history" in r else r.get("hasAfHistory", False))
            af_subtype = r.get("af_subtype") or r.get("afSubtype")
            time_since_diagnosis = r.get("time_since_diagnosis") or r.get("timeSinceDiagnosis")

            comorbidities = _parse_list(r.get("comorbidities"))
            cardio_drugs_12h = _parse_list(r.get("cardio_drugs_12h") or r.get("cardioDrugs12h"))
            device_history = _parse_list(r.get("device_history") or r.get("deviceHistory"))

            ecg_rhythm = str(r.get("ecg_rhythm_diagnosis") or r.get("ecgRhythmDiagnosis") or "No evaluado")
            ecg_modality = str(r.get("ecg_modality") or r.get("ecgModality") or "No especificado")
            evaluating_physician = r.get("evaluating_physician") or r.get("evaluatingPhysician")
            ecg_time = _parse_datetime(r.get("ecg_taken_at") or r.get("ecgTakenAt"))
            observations = r.get("observations")

            ai_af_detected = bool(r.get("ai_af_detected") if "ai_af_detected" in r else r.get("aiAfDetected", False))
            ai_confidence = Decimal(str(r.get("ai_confidence") or r.get("aiConfidence") or 0.0))
            heart_rate_bpm = Decimal(str(r.get("heart_rate_bpm") or r.get("heartRateBpm") or 0.0))
            hrv_rmssd = Decimal(str(r.get("hrv_rmssd") or r.get("hrvRmssd") or 0.0))
            hrv_sdnn = Decimal(str(r.get("hrv_sdnn") or r.get("hrvSdnn") or 0.0))
            is_tachycardic = bool(r.get("is_tachycardic") if "is_tachycardic" in r else r.get("isTachycardic", False))
            recorded_beats = int(r.get("recorded_beats_count") or r.get("recordedBeatsCount") or 0)
            duration_sec = int(r.get("recording_duration_seconds") or r.get("recordingDurationSeconds") or 60)

            validation_outcome = r.get("validation_outcome") or r.get("validationOutcome")
            if not validation_outcome:
                ecg_is_af = "fibrila" in ecg_rhythm.lower() or "af" in ecg_rhythm.lower()
                if ecg_is_af and ai_af_detected:
                    validation_outcome = "VP"
                elif not ecg_is_af and not ai_af_detected:
                    validation_outcome = "VN"
                elif not ecg_is_af and ai_af_detected:
                    validation_outcome = "FP"
                else:
                    validation_outcome = "FN"

            raw_ppg = _parse_dict(r.get("raw_ppg_data") or r.get("rawPpgData"))
            created_at = _parse_datetime(r.get("created_at") or r.get("createdAt")) or datetime.utcnow()

            record_dict = {
                "id": rec_id,
                "evaluator_user_id": current_user.user_id,
                "patient_code": patient_code,
                "capture_index": capture_index,
                "cohort": cohort,
                "age": age,
                "biological_sex": biological_sex,
                "weight_kg": weight_kg,
                "height_cm": height_cm,
                "bmi": bmi,
                "skin_temperature": skin_temperature,
                "fitzpatrick_scale": fitzpatrick_scale,
                "wrist": wrist,
                "has_af_history": has_af_history,
                "af_subtype": af_subtype,
                "time_since_diagnosis": time_since_diagnosis,
                "comorbidities": comorbidities,
                "cardio_drugs_12h": cardio_drugs_12h,
                "device_history": device_history,
                "ecg_rhythm_diagnosis": ecg_rhythm,
                "ecg_modality": ecg_modality,
                "evaluating_physician": evaluating_physician,
                "ecg_taken_at": ecg_time,
                "observations": observations,
                "ai_af_detected": ai_af_detected,
                "ai_confidence": ai_confidence,
                "heart_rate_bpm": heart_rate_bpm,
                "hrv_rmssd": hrv_rmssd,
                "hrv_sdnn": hrv_sdnn,
                "is_tachycardic": is_tachycardic,
                "recorded_beats_count": recorded_beats,
                "recording_duration_seconds": duration_sec,
                "validation_outcome": validation_outcome,
                "raw_ppg_data": raw_ppg,
                "sync_status": "SYNCED",
                "created_at": created_at,
                "synced_at": datetime.utcnow(),
            }

            # Upsert atómico por ID de registro
            stmt = insert(models.ClinicalValidationRecord).values(record_dict)
            stmt = stmt.on_conflict_do_update(
                index_elements=[models.ClinicalValidationRecord.id],
                set_={
                    "evaluator_user_id": record_dict["evaluator_user_id"],
                    "ecg_rhythm_diagnosis": record_dict["ecg_rhythm_diagnosis"],
                    "ecg_modality": record_dict["ecg_modality"],
                    "evaluating_physician": record_dict["evaluating_physician"],
                    "observations": record_dict["observations"],
                    "validation_outcome": record_dict["validation_outcome"],
                    "sync_status": "SYNCED",
                    "synced_at": record_dict["synced_at"],
                }
            )
            db.execute(stmt)
            synced_ids.append(rec_id)

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transaccional al guardar lote: {str(e)}"
        )

    return schemas.ClinicalBatchSyncResponse(
        status="success",
        synced_count=len(synced_ids),
        synced_ids=synced_ids,
        evaluator_user_id=current_user.user_id,
    )


@router.get("/records")
def list_clinical_records(
    cohort: Optional[str] = Query(None, description="Filtrar por 'AF' o 'CONTROL'"),
    patient_code: Optional[str] = Query(None, description="Filtrar por código de paciente"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    """
    Lista las mediciones clínicas sincronizadas para el evaluador autenticado.
    """
    query = db.query(models.ClinicalValidationRecord).filter(
        models.ClinicalValidationRecord.evaluator_user_id == current_user.user_id
    )

    if cohort:
        query = query.filter(models.ClinicalValidationRecord.cohort == cohort)
    if patient_code:
        query = query.filter(models.ClinicalValidationRecord.patient_code == patient_code)

    total = query.count()
    records = query.order_by(models.ClinicalValidationRecord.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": [
            {
                "id": r.id,
                "patient_code": r.patient_code,
                "capture_index": r.capture_index,
                "cohort": r.cohort,
                "age": r.age,
                "biological_sex": r.biological_sex,
                "ai_af_detected": r.ai_af_detected,
                "ai_confidence": float(r.ai_confidence),
                "heart_rate_bpm": float(r.heart_rate_bpm),
                "hrv_rmssd": float(r.hrv_rmssd),
                "validation_outcome": r.validation_outcome,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
    }
