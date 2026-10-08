from dependencies.auth_guard import TokenUser, get_current_user_from_token
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from utils.query_builder import apply_get_query_params

router = APIRouter(
    prefix="/metric-types",
    tags=["Metric Types"]
)


@router.post("/", response_model=schemas.MetricTypeResponse)
def create_metric_type(data: schemas.MetricTypeCreate, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):
    existing_metric = db.query(models.MetricType).filter(
        models.MetricType.name == data.name
    ).first()

    if existing_metric:
        raise HTTPException(status_code=400, detail="Metric type already exists")

    metric_type = models.MetricType(**data.dict())

    db.add(metric_type)
    db.commit()
    db.refresh(metric_type)

    return metric_type


@router.get("/", response_model=list[schemas.MetricTypeResponse])
def get_metric_types(
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
    db: Session = Depends(get_db)
):
    db_query = db.query(models.MetricType)

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.MetricType,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.get("/{id_metric_type}", response_model=schemas.MetricTypeResponse)
def get_metric_type(id_metric_type: int, db: Session = Depends(get_db)):
    metric_type = db.query(models.MetricType).filter(
        models.MetricType.id_metric_type == id_metric_type
    ).first()

    if not metric_type:
        raise HTTPException(status_code=404, detail="Metric type not found")

    return metric_type


@router.put("/{id_metric_type}", response_model=schemas.MetricTypeResponse)
def update_metric_type(
    id_metric_type: int,
    data: schemas.MetricTypeCreate,
    db: Session = Depends(get_db, current_user: TokenUser = Depends(get_current_user_from_token))
):
    metric_type = db.query(models.MetricType).filter(
        models.MetricType.id_metric_type == id_metric_type
    ).first()

    if not metric_type:
        raise HTTPException(status_code=404, detail="Metric type not found")

    metric_type.unit = data.unit
    metric_type.min_value = data.min_value
    metric_type.max_value = data.max_value
    metric_type.is_derived = data.is_derived
    metric_type.name = data.name

    db.commit()
    db.refresh(metric_type)

    return metric_type


@router.delete("/{id_metric_type}")
def delete_metric_type(id_metric_type: int, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):
    metric_type = db.query(models.MetricType).filter(
        models.MetricType.id_metric_type == id_metric_type
    ).first()

    if not metric_type:
        raise HTTPException(status_code=404, detail="Metric type not found")

    db.delete(metric_type)
    db.commit()

    return {"message": "Metric type deleted"}