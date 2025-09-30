from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserPasswordReset, UserStatistics


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Serviço para gerenciamento de usuários."""
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Gera hash de senha usando bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha corresponde ao hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        order: str = "desc"
    ) -> tuple[List[User], int]:
        """
        Lista usuários com filtros e paginação.
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros para pular
            limit: Número máximo de registros
            search: Texto para buscar em username, email e full_name
            role: Filtrar por role
            is_active: Filtrar por status ativo/inativo
            sort_by: Campo para ordenação
            order: Direção da ordenação (asc/desc)
            
        Returns:
            Tupla com lista de usuários e total de registros
        """
        query = db.query(User)
        
        # Aplicar filtros
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Contar total antes da paginação
        total = query.count()
        
        # Aplicar ordenação
        sort_mapping = {
            "username": User.username,
            "email": User.email,
            "created_at": User.created_at,
            "updated_at": User.updated_at
        }
        sort_field = sort_mapping.get(sort_by, User.created_at)
        
        if order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        # Aplicar paginação
        users = query.offset(skip).limit(limit).all()
        
        return users, total
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Busca usuário por ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Busca usuário por email."""
        return db.query(User).filter(User.email == email.lower()).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Busca usuário por username."""
        return db.query(User).filter(User.username == username.lower()).first()
    
    @staticmethod
    def create_user(
        db: Session,
        user_data: UserCreate,
        created_by: Optional[UUID] = None
    ) -> User:
        """
        Cria novo usuário.
        
        Args:
            db: Sessão do banco de dados
            user_data: Dados do novo usuário
            created_by: ID do usuário que está criando
            
        Returns:
            Usuário criado
            
        Raises:
            HTTPException: Se email ou username já existirem
        """
        # Verificar se email já existe
        if UserService.get_user_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email já cadastrado"
            )
        
        # Verificar se username já existe
        if UserService.get_user_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username já cadastrado"
            )
        
        # Criar usuário
        db_user = User(
            email=user_data.email.lower(),
            username=user_data.username.lower(),
            hashed_password=UserService.get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=user_data.is_active,
            is_verified=user_data.is_verified,
            created_by=created_by
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def update_user(
        db: Session,
        user_id: UUID,
        user_data: UserUpdate,
        current_user_id: UUID
    ) -> User:
        """
        Atualiza dados do usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário a ser atualizado
            user_data: Dados para atualização
            current_user_id: ID do usuário que está fazendo a atualização
            
        Returns:
            Usuário atualizado
            
        Raises:
            HTTPException: Se usuário não existir ou dados conflitarem
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Verificar se está tentando alterar próprio role
        if user_id == current_user_id and user_data.role is not None:
            if user_data.role != db_user.role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Não é permitido alterar o próprio role"
                )
        
        # Verificar se email já existe (se está sendo alterado)
        if user_data.email and user_data.email != db_user.email:
            existing_user = UserService.get_user_by_email(db, user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email já cadastrado"
                )
        
        # Verificar se username já existe (se está sendo alterado)
        if user_data.username and user_data.username != db_user.username:
            existing_user = UserService.get_user_by_username(db, user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username já cadastrado"
                )
        
        # Verificar se não está removendo o último admin
        if user_data.role and user_data.role != "admin" and db_user.role == "admin":
            UserService._check_last_admin(db, user_id)
        
        if user_data.is_active is False and db_user.role == "admin":
            UserService._check_last_admin(db, user_id)
        
        # Atualizar campos
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "email" and value:
                value = value.lower()
            elif field == "username" and value:
                value = value.lower()
            setattr(db_user, field, value)
        
        db_user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: UUID, current_user_id: UUID) -> bool:
        """
        Desativa usuário (soft delete).
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário a ser desativado
            current_user_id: ID do usuário que está fazendo a exclusão
            
        Returns:
            True se sucesso
            
        Raises:
            HTTPException: Se usuário não existir ou tentar deletar a si mesmo
        """
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Não é permitido deletar a própria conta"
            )
        
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Verificar se não está removendo o último admin
        if db_user.role == "admin":
            UserService._check_last_admin(db, user_id)
        
        # Soft delete
        db_user.is_active = False
        db_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return True
    
    @staticmethod
    def reset_user_password(
        db: Session,
        user_id: UUID,
        password_data: UserPasswordReset
    ) -> Dict[str, Any]:
        """
        Reseta senha do usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            password_data: Nova senha
            
        Returns:
            Dicionário com informações da operação
            
        Raises:
            HTTPException: Se usuário não existir
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Atualizar senha
        db_user.hashed_password = UserService.get_password_hash(password_data.new_password)
        db_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Senha alterada com sucesso",
            "user_id": str(user_id),
            "temporary_password": False
        }
    
    @staticmethod
    def get_user_statistics(db: Session) -> UserStatistics:
        """
        Obtém estatísticas gerais de usuários.
        
        Args:
            db: Sessão do banco de dados
            
        Returns:
            Estatísticas de usuários
        """
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        inactive_users = total_users - active_users
        verified_users = db.query(User).filter(User.is_verified == True).count()
        
        # Usuários por role
        users_by_role = {}
        for role in ["admin", "editor", "viewer"]:
            count = db.query(User).filter(User.role == role).count()
            users_by_role[role] = count
        
        # Usuários criados nos últimos 30 dias
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        users_created_last_30_days = db.query(User).filter(
            User.created_at >= thirty_days_ago
        ).count()
        
        # Usuários que fizeram login nos últimos 7 dias
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        users_logged_in_last_7_days = db.query(User).filter(
            User.last_login >= seven_days_ago
        ).count()
        
        return UserStatistics(
            total_users=total_users,
            users_by_role=users_by_role,
            active_users=active_users,
            inactive_users=inactive_users,
            verified_users=verified_users,
            users_created_last_30_days=users_created_last_30_days,
            users_logged_in_last_7_days=users_logged_in_last_7_days
        )
    
    @staticmethod
    def update_last_login(db: Session, user_id: UUID) -> None:
        """Atualiza último login do usuário."""
        db_user = UserService.get_user_by_id(db, user_id)
        if db_user:
            db_user.last_login = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def _check_last_admin(db: Session, user_id: UUID) -> None:
        """
        Verifica se não está removendo o último admin ativo.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário sendo modificado
            
        Raises:
            HTTPException: Se for o último admin
        """
        active_admins = db.query(User).filter(
            and_(
                User.role == "admin",
                User.is_active == True,
                User.id != user_id
            )
        ).count()
        
        if active_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Não é permitido remover o último administrador ativo"
            )