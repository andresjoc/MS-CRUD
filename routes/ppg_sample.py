from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from dependencies.auth_guard import TokenUser, get_current_user_from_token
from utils.query_builder import apply_get_query_params

router = APIRouter(
    prefix="/ppg_samples",
    tags=["PpgSamples"]
)


def _get_owned_session(
    db: Session,
    id_session: int,
    current_user: TokenUser,
) -> models.MonitoringSession:
    session = db.query(models.MonitoringSession).filter(
        models.MonitoringSession.id_session == id_session
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.id_user != current_user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return session


def _ensure_sample_owner(sample: models.PpgSample, current_user: TokenUser):
    if sample.session.id_user != current_user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/", response_model=schemas.PpgSampleResponse)
def create_sample(
    data: schemas.PpgSampleCreate,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):

    _get_owned_session(db, data.id_session, current_user)

    sample = models.PpgSample(**data.dict())

    db.add(sample)
    db.commit()
    db.refresh(sample)

    return sample


@router.get("/", response_model=list[schemas.PpgSampleResponse])
def get_samples(
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
    db_query = db.query(models.PpgSample).join(models.PpgSample.session).filter(
        models.MonitoringSession.id_user == current_user.user_id
    )

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.PpgSample,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.get("/session/{id_session}", response_model=list[schemas.PpgSampleResponse])
def get_samples_by_session(
    id_session: int,
    query: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1),
    offset: Optional[int] = Query(default=None, ge=0),
    orderBy: Optional[str] = Query(default=None),
    sort: Optional[str] = Query(default="asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    _get_owned_session(db, id_session, current_user)

    db_query = db.query(models.PpgSample).filter(
        models.PpgSample.id_session == id_session
    )

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.PpgSample,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.delete("/{id_sample}")
def delete_sample(
    id_sample: int,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    sample = db.query(models.PpgSample).filter(
        models.PpgSample.id_ppg_sample == id_sample
    ).first()

    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    _ensure_sample_owner(sample, current_user)

    db.delete(sample)
    db.commit()

    return {"message": "PPG sample deleted"}


@router.post("/bulk")
def create_samples_bulk(
    data: list[schemas.PpgSampleCreate],
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):
    checked_sessions = set()
    for item in data:
        if item.id_session not in checked_sessions:
            _get_owned_session(db, item.id_session, current_user)
            checked_sessions.add(item.id_session)

    samples = [models.PpgSample(**item.dict()) for item in data]

    db.bulk_save_objects(samples)
    db.commit()

    return {"inserted": len(samples)}


@router.put("/{id_sample}", response_model=schemas.PpgSampleResponse)
def update_sample(
    id_sample: int,
    data: schemas.PpgSampleCreate,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token),
):

    sample = db.query(models.PpgSample).filter(
        models.PpgSample.id_ppg_sample == id_sample
    ).first()

    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    _ensure_sample_owner(sample, current_user)
    _get_owned_session(db, data.id_session, current_user)

    for key, value in data.dict().items():
        setattr(sample, key, value)

    db.commit()
    db.refresh(sample)

    return sample
