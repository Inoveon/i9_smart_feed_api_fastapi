"""
Endpoints relacionados ao perfil do usuário.
"""
from datetime import datetime
from typing import Dict, Any, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
import re

from app.config.database import get_db
from app.dependencies.auth import oauth2_scheme, decode_token, get_current_user
from app.models.user import User


router = APIRouter(tags=["profile"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserPreferences(BaseModel):
    """Modelo para preferências do usuário."""
    theme: Literal["light", "dark"] = "light"
    palette: Literal["blue", "emerald", "violet", "rose", "amber"] = "blue"


class UserProfile(BaseModel):
    """Modelo de resposta para perfil do usuário."""
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    preferences: UserPreferences
    created_at: datetime
    updated_at: datetime


class UpdateProfile(BaseModel):
    """Modelo para atualização de perfil."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    preferences: Optional[UserPreferences] = None


class ChangePassword(BaseModel):
    """Modelo para mudança de senha."""
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """
        Valida a força da senha:
        - Mínimo 8 caracteres
        - Pelo menos 1 maiúscula
        - Pelo menos 1 minúscula
        - Pelo menos 1 número
        - Pelo menos 1 caractere especial
        """
        if len(v) < 8:
            raise ValueError('A senha deve ter pelo menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('A senha deve conter pelo menos uma letra maiúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('A senha deve conter pelo menos uma letra minúscula')
        if not re.search(r'\d', v):
            raise ValueError('A senha deve conter pelo menos um número')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('A senha deve conter pelo menos um caractere especial')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('As senhas não coincidem')
        return v


@router.get("/me", response_model=UserProfile, summary="Obter perfil do usuário atual")
async def get_me(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    Retorna as informações do perfil do usuário autenticado.
    
    Inclui:
    - Dados básicos do usuário
    - Role e permissões
    - Status da conta
    - Informações do token
    """
    # Decodifica token para pegar informações adicionais
    payload = decode_token(token)
    exp = payload.get("exp")
    
    # Calcula tempo até expiração
    token_expires_in = None
    if exp:
        expires_at = datetime.fromtimestamp(exp)
        now = datetime.utcnow()
        if expires_at > now:
            token_expires_in = int((expires_at - now).total_seconds())
    
    # Determina o valor do role
    role_value = getattr(current_user.role, "value", current_user.role)
    
    # Garante que preferences sempre existe
    preferences = current_user.preferences or {"theme": "light", "palette": "blue"}
    
    response = {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": role_value,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "preferences": preferences,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "token_info": {
            "expires_in_seconds": token_expires_in,
            "expires_at": expires_at.isoformat() if exp else None
        }
    }
    
    return response


@router.put("/me", response_model=UserProfile, summary="Atualizar perfil")
async def update_me(
    profile_data: UpdateProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Atualiza as informações do perfil do usuário atual.
    
    Campos permitidos:
    - full_name: Nome completo
    - email: Novo email (deve ser único)
    - preferences: Preferências de tema e paleta
    """
    # Verifica se o email já está em uso
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = db.query(User).filter(
            User.email == profile_data.email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já está em uso"
            )
    
    # Atualiza os campos
    update_data = profile_data.dict(exclude_unset=True)
    
    # Trata preferences especialmente
    if 'preferences' in update_data and update_data['preferences']:
        current_user.preferences = update_data['preferences']
        del update_data['preferences']
    
    # Atualiza outros campos
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    # Retorna o perfil atualizado
    role_value = getattr(current_user.role, "value", current_user.role)
    preferences = current_user.preferences or {"theme": "light", "palette": "blue"}
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": role_value,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "preferences": preferences,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }


@router.put("/me/password", summary="Alterar senha")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Altera a senha do usuário atual.
    
    Requer:
    - current_password: Senha atual para validação
    - new_password: Nova senha (mín. 8 caracteres, maiúscula, minúscula, número, especial)
    - confirm_password: Confirmação da nova senha
    
    Validações aplicadas automaticamente pelo schema ChangePassword.
    """
    # Valida senha atual
    if not pwd_context.verify(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta. Por favor, verifique e tente novamente."
        )
    
    # Verifica se a nova senha é diferente da atual
    if pwd_context.verify(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha não pode ser igual à senha atual"
        )
    
    # Atualiza a senha
    current_user.hashed_password = pwd_context.hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Senha alterada com sucesso",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.delete("/me", summary="Desativar conta")
async def deactivate_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Desativa a conta do usuário atual.
    A conta não é deletada, apenas marcada como inativa.
    """
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Conta desativada com sucesso",
        "timestamp": datetime.utcnow().isoformat()
    }