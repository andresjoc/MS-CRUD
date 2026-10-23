from dependencies.auth_guard import TokenUser, get_current_user_from_token
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from utils.query_builder import apply_get_query_params

router = APIRouter(
    prefix="/compute_statuses",
    tags=["ComputeStatuses"]
)


@router.post("/", response_model=schemas.ComputeStatusResponse)
def create_status(data: schemas.ComputeStatusCreate, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):
    status = models.ComputeStatus(**data.dict())

    db.add(status)
    db.commit()
    db.refresh(status)

    return status


@router.get("/", response_model=list[schemas.ComputeStatusResponse])
def get_statuses(
    query: Optional[str] = Query(
        default=None,
        description="Filter records <miembro>:<valor>"
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
    db: Session = Depends(get_db)
):
    db_query = db.query(models.ComputeStatus)

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.ComputeStatus,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.put("/{id_compute_status}", response_model=schemas.ComputeStatusResponse)
def update_status(
    id_compute_status: int,
    data: schemas.ComputeStatusCreate,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user_from_token)
):
    status = db.query(models.ComputeStatus).filter(
        models.ComputeStatus.id_compute_status == id_compute_status
    ).first()

    if not status:
        raise HTTPException(status_code=404, detail="Status not found")

    for key, value in data.dict().items():
        setattr(status, key, value)

    db.commit()
    db.refresh(status)

    return status


@router.delete("/{id_status}")
def delete_status(id_status: int, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):
    status = db.query(models.ComputeStatus).filter(
        models.ComputeStatus.id_compute_status == id_status
    ).first()

    if not status:
        raise HTTPException(status_code=404, detail="Status not found")

    db.delete(status)
    db.commit()

    return {"message": "Status deleted"}