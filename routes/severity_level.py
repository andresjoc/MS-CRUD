from dependencies.auth_guard import TokenUser, get_current_user_from_token
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from utils.query_builder import apply_get_query_params

router = APIRouter(
    prefix="/severity-levels",
    tags=["Severity Levels"]
)


@router.post("/", response_model=schemas.SeverityLevelResponse)
def create_severity(data: schemas.SeverityLevelCreate, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):
    existing = db.query(models.SeverityLevel).filter(
        models.SeverityLevel.name == data.name
    ).first()
 
    if existing:
        raise HTTPException(status_code=400, detail="Severity already exists")

    severity = models.SeverityLevel(**data.dict())

    db.add(severity)
    db.commit()
    db.refresh(severity)

    return severity


@router.get("/", response_model=list[schemas.SeverityLevelResponse])
def get_severities(
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
    db_query = db.query(models.SeverityLevel)

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.SeverityLevel,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.get("/{id_severity_level}", response_model=schemas.SeverityLevelResponse)
def get_severity(id_severity_level: int, db: Session = Depends(get_db)):
    severity = db.query(models.SeverityLevel).filter(
        models.SeverityLevel.id_severity_level == id_severity_level
    ).first()

    if not severity:
        raise HTTPException(status_code=404, detail="Severity not found")

    return severity


@router.put("/{id_severity_level}", response_model=schemas.SeverityLevelResponse)
def update_severity(
    id_severity_level: int,
    data: schemas.SeverityLevelCreate,
    db: Session = Depends(get_db, current_user: TokenUser = Depends(get_current_user_from_token))
):
    severity = db.query(models.SeverityLevel).filter(
        models.SeverityLevel.id_severity_level == id_severity_level
    ).first()

    if not severity:
        raise HTTPException(status_code=404, detail="Severity not found")

    severity.name = data.name
    severity.description = data.description

    db.commit()
    db.refresh(severity)

    return severity


@router.delete("/{id_severity_level}")
def delete_severity(id_severity_level: int, db: Session = Depends(get_db), current_user: TokenUser = Depends(get_current_user_from_token)):
    severity = db.query(models.SeverityLevel).filter(
        models.SeverityLevel.id_severity_level == id_severity_level
    ).first()

    if not severity:
        raise HTTPException(status_code=404, detail="Severity not found")

    db.delete(severity)
    db.commit()

    return {"detail": "Severity deleted successfully"}