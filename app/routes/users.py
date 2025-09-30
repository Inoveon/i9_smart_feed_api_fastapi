from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserDetailResponse,
    UserPasswordReset,
    UserStatistics
)
from app.schemas.pagination import PaginationParams, PaginatedResponse
from app.services.user_service import UserService


router = APIRouter(prefix="/users")


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Verifica se o usuário atual é um administrador."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return current_user


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="Listar usuários",
    description="Lista todos os usuários com filtros e paginação (requer role admin)"
)
async def list_users(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(50, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Buscar em username, email e nome"),
    role: Optional[str] = Query(None, pattern="^(admin|editor|viewer)$", description="Filtrar por role"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status ativo/inativo"),
    sort_by: str = Query("created_at", pattern="^(username|email|created_at|updated_at)$", description="Campo para ordenação"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Direção da ordenação"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Lista usuários com filtros e paginação."""
    skip = (page - 1) * limit
    
    users, total = UserService.get_users(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        role=role,
        is_active=is_active,
        sort_by=sort_by,
        order=order
    )
    
    # Atualizar último login do usuário atual se necessário
    if current_user.last_login is None:
        UserService.update_last_login(db, current_user.id)
    
    return PaginatedResponse.create(
        items=users,
        page=page,
        page_size=limit,
        total=total
    )


@router.get(
    "/statistics",
    response_model=UserStatistics,
    summary="Estatísticas de usuários",
    description="Retorna estatísticas gerais sobre os usuários do sistema (requer role admin)"
)
async def get_user_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Obtém estatísticas de usuários."""
    return UserService.get_user_statistics(db)


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Obter usuário específico",
    description="Retorna detalhes de um usuário específico (requer role admin)"
)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Obtém detalhes de um usuário específico."""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Adicionar estatísticas do usuário
    from app.models.campaign import Campaign
    campaigns_created = db.query(Campaign).filter(Campaign.created_by == user_id).count()
    
    user_dict = UserDetailResponse.model_validate(user)
    user_dict.statistics = {
        "campaigns_created": campaigns_created,
        "last_activity": user.updated_at or user.created_at
    }
    
    return user_dict


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo usuário",
    description="Cria um novo usuário no sistema (requer role admin)"
)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Cria um novo usuário."""
    new_user = UserService.create_user(
        db=db,
        user_data=user_data,
        created_by=current_user.id
    )
    return new_user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Atualizar usuário",
    description="Atualiza dados de um usuário existente (requer role admin)"
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Atualiza dados de um usuário."""
    updated_user = UserService.update_user(
        db=db,
        user_id=user_id,
        user_data=user_data,
        current_user_id=current_user.id
    )
    return updated_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar usuário",
    description="Desativa um usuário (soft delete) (requer role admin)"
)
async def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Desativa um usuário (soft delete)."""
    UserService.delete_user(
        db=db,
        user_id=user_id,
        current_user_id=current_user.id
    )
    return None


@router.put(
    "/{user_id}/password",
    summary="Resetar senha de usuário",
    description="Reseta a senha de um usuário específico (requer role admin)"
)
async def reset_user_password(
    user_id: UUID,
    password_data: UserPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Reseta a senha de um usuário."""
    result = UserService.reset_user_password(
        db=db,
        user_id=user_id,
        password_data=password_data
    )
    return result