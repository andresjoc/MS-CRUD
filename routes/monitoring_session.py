from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from dependencies.auth_guard import TokenUser, get_current_user_from_token
from utils.query_builder import apply_get_query_params
 
router = APIRouter( 
    prefix="/monitoring_sessions",
    tags=["MonitoringSessions"]
)


def _ensure_session_owner(
    session: models.MonitoringSession,
    current_user: TokenUser,
):
    if session.id_user != current_user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/", response_model=schemas.MonitoringSessionResponse)
def create_monitoring_session(
    data: schemas.MonitoringSessionCreate,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    user = db.query(models.App_user).filter(
        models.App_user.id_user == current_user.user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    compute_status = db.query(models.ComputeStatus).filter(
        models.ComputeStatus.id_compute_status == data.id_compute_status
    ).first()

    if not compute_status:
        raise HTTPException(status_code=404, detail="Compute status not found")

    if data.id_wearable is not None:
        wearable = db.query(models.Wearable).filter(
            models.Wearable.id_wearable == data.id_wearable
        ).first()
        if not wearable:
            raise HTTPException(status_code=404, detail="Wearable not found")
        if wearable.id_user != current_user.user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

    session = models.MonitoringSession(
        id_user=current_user.user_id,
        id_wearable=data.id_wearable,
        id_compute_status=data.id_compute_status,
        date_time=data.date_time,
        is_delta_encoded=data.is_delta_encoded,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.get("/", response_model=list[schemas.MonitoringSessionResponse])
def get_monitoring_sessions(
    query: Optional[str] = Query(
        default=None,
        description="Filter records. Example: id_user:1 or date_time__gte:1710000000"
    ),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        description="Maximum number of records to return"
    ),
    offset: Optional[int] = Query(
        default=None,
        ge=0,
        description="Number of records to skip"
    ),
    orderBy: Optional[str] = Query(
        default=None,
        description="Field used to order the results"
    ),
    sort: Optional[str] = Query(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort direction: asc or desc"
    ),
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    db_query = db.query(models.MonitoringSession).filter(
        models.MonitoringSession.id_user == current_user.user_id
    )

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.MonitoringSession,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.get("/{id_session}", response_model=schemas.MonitoringSessionResponse)
def get_monitoring_session(
    id_session: int,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    session = db.query(models.MonitoringSession).filter(
        models.MonitoringSession.id_session == id_session
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Monitoring session not found")

    _ensure_session_owner(session, current_user)

    return session


@router.get("/user/{id_user}", response_model=list[schemas.MonitoringSessionResponse])
def get_monitoring_sessions_by_user(
    id_user: int,
    query: Optional[str] = Query(
        default=None,
        description="Filter records. <miembro>:<valor>"
    ),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        description="Maximum number of records to return"
    ),
    offset: Optional[int] = Query(
        default=None,
        ge=0,
        description="Number of records to skip"
    ),
    orderBy: Optional[str] = Query(
        default=None,
        description="Field used to order the results"
    ),
    sort: Optional[str] = Query(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort direction: asc or desc"
    ),
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    if id_user != current_user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    db_query = db.query(models.MonitoringSession).filter(
        models.MonitoringSession.id_user == current_user.user_id
    )

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.MonitoringSession,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.put("/{id_session}", response_model=schemas.MonitoringSessionResponse)
def update_monitoring_session(
    id_session: int,
    data: schemas.MonitoringSessionCreate,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    session = db.query(models.MonitoringSession).filter(
        models.MonitoringSession.id_session == id_session
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Monitoring session not found")

    _ensure_session_owner(session, current_user)

    compute_status = db.query(models.ComputeStatus).filter(
        models.ComputeStatus.id_compute_status == data.id_compute_status
    ).first()

    if not compute_status:
        raise HTTPException(status_code=404, detail="Compute status not found")

    if data.id_wearable is not None:
        wearable = db.query(models.Wearable).filter(
            models.Wearable.id_wearable == data.id_wearable
        ).first()
        if not wearable:
            raise HTTPException(status_code=404, detail="Wearable not found")
        if wearable.id_user != current_user.user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

    session.id_user = current_user.user_id
    session.id_wearable = data.id_wearable
    session.id_compute_status = data.id_compute_status
    session.date_time = data.date_time
    session.is_delta_encoded = data.is_delta_encoded

    db.commit()
    db.refresh(session)

    return session


@router.delete("/{id_session}")
def delete_monitoring_session(
    id_session: int,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    session = db.query(models.MonitoringSession).filter(
        models.MonitoringSession.id_session == id_session
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Monitoring session not found")

    _ensure_session_owner(session, current_user)

    db.delete(session)
    db.commit()

    return {"message": "Monitoring session deleted"}
