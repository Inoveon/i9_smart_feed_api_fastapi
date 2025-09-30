from datetime import datetime, timedelta
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.config.database import get_db
from app.models.user import User
from pydantic import BaseModel


router = APIRouter()
logger = logging.getLogger("auth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    exp_minutes = minutes if minutes is not None else int(settings.__dict__.get("JWT_EXPIRATION_MINUTES", 60))
    expire = datetime.utcnow() + timedelta(minutes=exp_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username = form_data.username
    user = (
        db.query(User)
        .filter((User.username == username) | (User.email == username))
        .first()
    )
    if not user:
        logger.warning("Login falhou: usuário não encontrado: %s", username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")
    if not pwd_context.verify(form_data.password, user.hashed_password):
        logger.warning("Login falhou: senha inválida para usuário: %s", username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")

    role_value = getattr(user.role, "value", user.role)
    access_token = create_access_token({"sub": user.email, "role": role_value}, minutes=int(settings.__dict__.get("JWT_EXPIRATION_MINUTES", 60)))
    refresh_token = create_access_token({"sub": user.email, "role": role_value, "type": "refresh"}, minutes=60*24*7)
    logger.info("Login bem-sucedido para usuário: %s", username)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
def refresh(req: RefreshRequest):
    try:
        payload = jwt.decode(req.refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        access_token = create_access_token({"sub": payload.get("sub"), "role": payload.get("role")})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
