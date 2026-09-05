import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models
from .database import get_db

# In a real product this secret would come from an environment variable.
# For a prototype it's fine hardcoded, but never commit real secrets like this.
SECRET_KEY = "bluedot-prototype-secret-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours, generous for demo purposes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Tells FastAPI's auto-docs (/docs) where to send the "Authorize" login form.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: int) -> str:
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """Runs on every protected endpoint: decodes the JWT sent in the
    Authorization header and loads the matching User row, or rejects
    the request with 401 if anything is wrong."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def find_worker_profile(db: Session, user_id: int) -> models.WorkerProfile | None:
    """The one query every route needs to go from a logged-in worker to
    their WorkerProfile row. Callers decide what "not found" means for
    them (404, empty list, etc.)."""
    return (
        db.query(models.WorkerProfile)
        .filter(models.WorkerProfile.user_id == user_id)
        .first()
    )


def require_role(*allowed_roles: str):
    """Usage: Depends(require_role("admin")) on a route to restrict it."""

    def role_checker(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {allowed_roles}",
            )
        return user

    return role_checker
