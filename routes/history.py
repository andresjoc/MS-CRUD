from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from dependencies.auth_guard import TokenUser, get_current_user_from_token

router = APIRouter(
    prefix="/history",
    tags=["History"],
)


@router.get("/", response_model=list[schemas.HistorySessionResponse])
def get_history(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    sessions = (
        db.query(models.MonitoringSession)
        .options(
            joinedload(models.MonitoringSession.compute_status),
            joinedload(models.MonitoringSession.measurements).joinedload(
                models.Measurement.metric_type
            ),
            joinedload(models.MonitoringSession.ppg_samples),
            joinedload(models.MonitoringSession.alerts).joinedload(
                models.Alert.severity_level
            ),
            joinedload(models.MonitoringSession.wearable).joinedload(
                models.Wearable.wearable_model
            ),
        )
        .filter(models.MonitoringSession.id_user == current_user.user_id)
        .order_by(models.MonitoringSession.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [_build_history_session(session) for session in sessions]


def _build_history_session(
    session: models.MonitoringSession,
) -> schemas.HistorySessionResponse:
    return schemas.HistorySessionResponse(
        id_session=session.id_session,
        id_wearable=session.id_wearable,
        date_time=session.date_time,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_delta_encoded=session.is_delta_encoded,
        compute_status=session.compute_status.name if session.compute_status else None,
        measurements=[
            schemas.HistoryMeasurementResponse(
                id_measurement=measurement.id_measurement,
                id_metric_type=measurement.id_metric_type,
                metric_name=measurement.metric_type.name
                if measurement.metric_type
                else str(measurement.id_metric_type),
                unit=measurement.metric_type.unit if measurement.metric_type else "",
                value=measurement.value,
                error_message=measurement.error_message,
                recorded_at=measurement.recorded_at,
            )
            for measurement in sorted(
                session.measurements,
                key=lambda item: item.recorded_at,
            )
        ],
        samples=[
            schemas.HistoryPpgSampleResponse(
                ts=sample.ts,
                green=sample.green,
                red=sample.red,
                ir=sample.ir,
            )
            for sample in sorted(session.ppg_samples, key=lambda item: item.ts)
        ],
        alerts=[
            schemas.HistoryAlertResponse(
                id_alert=alert.id_alert,
                severity_name=alert.severity_level.name
                if alert.severity_level
                else None,
                description=alert.description,
                created_at=alert.created_at,
            )
            for alert in sorted(session.alerts, key=lambda item: item.created_at)
        ],
        wearable=_build_history_wearable(session.wearable),
    )


def _build_history_wearable(
    wearable: models.Wearable | None,
) -> schemas.HistoryWearableResponse | None:
    if wearable is None:
        return None
    model = wearable.wearable_model
    return schemas.HistoryWearableResponse(
        id_wearable=wearable.id_wearable,
        id_wearable_model=wearable.id_wearable_model,
        model=schemas.HistoryWearableModelResponse(
            id_wearable_model=model.id_wearable_model,
            brand=model.brand,
            model=model.model,
        ) if model else None,
    )
