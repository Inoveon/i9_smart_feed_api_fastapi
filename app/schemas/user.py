from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID
import re


class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    role: str = Field(..., pattern="^(admin|editor|viewer)$")
    is_active: bool = True
    is_verified: bool = False
    
    @validator('email')
    def email_lowercase(cls, v):
        """Converte email para lowercase."""
        return v.lower() if v else v
    
    @validator('username')
    def username_lowercase_and_valid(cls, v):
        """Valida e converte username para lowercase."""
        if not v:
            return v
        v = v.lower()
        if not re.match(r'^[a-z0-9_-]{3,50}$', v):
            raise ValueError('Username deve conter apenas letras minúsculas, números, underscore e hífen (3-50 caracteres)')
        return v
    
    @validator('full_name')
    def trim_full_name(cls, v):
        """Remove espaços extras do nome completo."""
        return v.strip() if v else v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password_strength(cls, v, values):
        """Valida força da senha."""
        if len(v) < 8:
            raise ValueError('Senha deve ter pelo menos 8 caracteres')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Senha deve conter pelo menos uma letra minúscula')
        
        if not re.search(r'[0-9]', v):
            raise ValueError('Senha deve conter pelo menos um número')
        
        if not re.search(r'[@$!%*?&#]', v):
            raise ValueError('Senha deve conter pelo menos um caractere especial (@$!%*?&#)')
        
        # Verifica se a senha não contém username ou email
        username = values.get('username', '')
        email = values.get('email', '')
        
        if username and username.lower() in v.lower():
            raise ValueError('Senha não pode conter o username')
        
        if email:
            email_local = email.split('@')[0]
            if email_local.lower() in v.lower():
                raise ValueError('Senha não pode conter parte do email')
        
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, max_length=255)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, pattern="^(admin|editor|viewer)$")
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    @validator('email')
    def email_lowercase(cls, v):
        """Converte email para lowercase."""
        return v.lower() if v else v
    
    @validator('username')
    def username_lowercase_and_valid(cls, v):
        """Valida e converte username para lowercase."""
        if not v:
            return v
        v = v.lower()
        if not re.match(r'^[a-z0-9_-]{3,50}$', v):
            raise ValueError('Username deve conter apenas letras minúsculas, números, underscore e hífen (3-50 caracteres)')
        return v
    
    @validator('full_name')
    def trim_full_name(cls, v):
        """Remove espaços extras do nome completo."""
        return v.strip() if v else v


class UserPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Valida força da senha."""
        if len(v) < 8:
            raise ValueError('Senha deve ter pelo menos 8 caracteres')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Senha deve conter pelo menos uma letra minúscula')
        
        if not re.search(r'[0-9]', v):
            raise ValueError('Senha deve conter pelo menos um número')
        
        if not re.search(r'[@$!%*?&#]', v):
            raise ValueError('Senha deve conter pelo menos um caractere especial (@$!%*?&#)')
        
        return v


class UserResponse(UserBase):
    id: UUID
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=lambda: {"theme": "light", "palette": "blue"})
    
    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Resposta com detalhes adicionais do usuário."""
    statistics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class UserStatistics(BaseModel):
    """Estatísticas gerais de usuários."""
    total_users: int = 0
    users_by_role: Dict[str, int] = Field(default_factory=dict)
    active_users: int = 0
    inactive_users: int = 0
    verified_users: int = 0
    users_created_last_30_days: int = 0
    users_logged_in_last_7_days: int = 0