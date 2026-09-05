from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models, schemas, translate
from ..database import get_db

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[schemas.ServiceCategoryOut])
def list_categories(lang: str = "en", db: Session = Depends(get_db)):
    categories = db.query(models.ServiceCategory).all()
    return [
        schemas.ServiceCategoryOut(
            id=c.id,
            name=translate.translate_text(c.name, lang),
            base_price=c.base_price,
        )
        for c in categories
    ]


@router.post(
    "/categories",
    response_model=schemas.ServiceCategoryOut,
    dependencies=[Depends(auth.require_role("admin"))],
)
def create_category(
    payload: schemas.ServiceCategoryCreate, db: Session = Depends(get_db)
):
    existing = (
        db.query(models.ServiceCategory)
        .filter(models.ServiceCategory.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    category = models.ServiceCategory(name=payload.name, base_price=payload.base_price)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/federations", response_model=list[schemas.FederationOut])
def list_federations(db: Session = Depends(get_db)):
    return db.query(models.Federation).all()


@router.post(
    "/federations",
    response_model=schemas.FederationOut,
    dependencies=[Depends(auth.require_role("admin"))],
)
def create_federation(
    payload: schemas.FederationCreate, db: Session = Depends(get_db)
):
    federation = models.Federation(name=payload.name, region=payload.region)
    db.add(federation)
    db.commit()
    db.refresh(federation)
    return federation
