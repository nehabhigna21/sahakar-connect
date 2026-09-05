from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.Token)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if payload.role not in ("customer", "worker", "admin"):
        raise HTTPException(status_code=400, detail="role must be customer, worker, or admin")

    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=auth.hash_password(payload.password),
        role=payload.role,
        language_pref=payload.language_pref,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # A worker gets an empty profile immediately so they can fill it in later.
    if user.role == "worker":
        profile = models.WorkerProfile(user_id=user.id)
        db.add(profile)
        db.commit()

    token = auth.create_access_token(user.id)
    return schemas.Token(access_token=token, user=schemas.UserOut.model_validate(user))


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm expects fields named "username" and "password"
    # (a FastAPI/OAuth2 convention) - we treat "username" as the email.
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = auth.create_access_token(user.id)
    return schemas.Token(access_token=token, user=schemas.UserOut.model_validate(user))


@router.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.patch("/me", response_model=schemas.UserOut)
def update_my_address(
    payload: schemas.UserAddressUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    current_user.address = payload.address
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/{user_id}/verify-household", response_model=schemas.UserOut)
def verify_household(
    user_id: int,
    _: models.User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db),
):
    """Federation-side household verification for the trust story on the
    consumer side - requires an address on file first."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.address.strip():
        raise HTTPException(status_code=400, detail="User has no address on file to verify")

    user.household_verified = True
    db.commit()
    db.refresh(user)
    return user
