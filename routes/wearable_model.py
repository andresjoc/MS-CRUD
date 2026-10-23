from dependencies.auth_guard import TokenUser, get_current_user_from_token
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from utils.query_builder import apply_get_query_params

router = APIRouter(
    prefix="/wearable-models",
    tags=["Wearable Models"]
)


@router.post("/", response_model=schemas.WearableModelResponse)
def create_model(data: schemas.WearableModelCreate, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):
    model = models.WearableModel(**data.dict())

    db.add(model)
    db.commit()
    db.refresh(model)

    return model


@router.get("/", response_model=list[schemas.WearableModelResponse])
def get_models(
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
    db_query = db.query(models.WearableModel)

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.WearableModel,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.get("/{model_id}", response_model=schemas.WearableModelResponse)
def get_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(models.WearableModel).filter(
        models.WearableModel.id_wearable_model == model_id
    ).first()

    if model is None:
        raise HTTPException(status_code=404, detail="Modelo de wearable no encontrado")

    return model


@router.put("/{model_id}", response_model=schemas.WearableModelResponse)
def update_model(model_id: int, data: schemas.WearableModelCreate, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):

    model = db.query(models.WearableModel).filter(
        models.WearableModel.id_wearable_model == model_id
    ).first()

    if model is None:
        raise HTTPException(status_code=404, detail="Modelo de wearable no encontrado")

    for key, value in data.dict().items():
        setattr(model, key, value)

    db.commit()
    db.refresh(model)

    return model


@router.delete("/{model_id}", status_code=204)
def delete_model(model_id: int, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):
    model = db.query(models.WearableModel).filter(
        models.WearableModel.id_wearable_model == model_id
    ).first()

    if model is None:
        raise HTTPException(status_code=404, detail="Modelo de wearable no encontrado")

    db.delete(model)
    db.commit()