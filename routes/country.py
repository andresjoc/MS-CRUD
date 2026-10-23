from dependencies.auth_guard import TokenUser, get_current_user_from_token
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from utils.query_builder import apply_get_query_params

router = APIRouter(
    prefix="/countries",
    tags=["Countries"]
)


@router.post("/", response_model=schemas.CountryResponse, status_code=201)
def create_country(country: schemas.CountryCreate, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):
    db_country = models.Country(
        name=country.name
    )

    db.add(db_country)
    db.commit()
    db.refresh(db_country)

    return db_country


@router.get("/", response_model=List[schemas.CountryResponse])
def get_countries(
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
    db_query = db.query(models.Country)

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.Country,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.get("/{country_id}", response_model=schemas.CountryResponse)
def get_country(country_id: int, db: Session = Depends(get_db)):
    country = db.query(models.Country).filter(
        models.Country.id_country == country_id
    ).first()

    if country is None:
        raise HTTPException(status_code=404, detail="País no encontrado")

    return country


@router.put("/{country_id}", response_model=schemas.CountryResponse)
def update_country(country_id: int, data: schemas.CountryCreate, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):

    country = db.query(models.Country).filter(
        models.Country.id_country == country_id
    ).first()

    if country is None:
        raise HTTPException(status_code=404, detail="País no encontrado")

    country.name = data.name

    db.commit()
    db.refresh(country)

    return country


@router.delete("/{country_id}", status_code=204)
def delete_country(country_id: int, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):
    country = db.query(models.Country).filter(
        models.Country.id_country == country_id
    ).first()

    if country is None:
        raise HTTPException(status_code=404, detail="País no encontrado")

    db.delete(country)
    db.commit()
    