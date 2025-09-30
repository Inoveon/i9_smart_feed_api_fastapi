#!/usr/bin/env python3
"""
Script para criar um usuário administrador de teste.
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.services.user_service import UserService
from app.config.settings import settings

# Criar engine e sessão
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_admin():
    """Cria um usuário administrador de teste."""
    db = SessionLocal()
    try:
        # Verificar se já existe um admin
        admin = db.query(User).filter(User.email == "admin@i9smart.com").first()
        
        if admin:
            print("❌ Usuário admin@i9smart.com já existe")
            if admin.role != "admin":
                admin.role = "admin"
                admin.is_active = True
                admin.is_verified = True
                db.commit()
                print("✅ Usuário atualizado para admin")
            return
        
        # Verificar se existe usuário com username admin
        existing_username = db.query(User).filter(User.username == "admin").first()
        if existing_username:
            # Atualizar o usuário existente
            existing_username.email = "admin@i9smart.com"
            existing_username.hashed_password = UserService.get_password_hash("Admin@123456")
            existing_username.full_name = "Administrador do Sistema"
            existing_username.role = "admin"
            existing_username.is_active = True
            existing_username.is_verified = True
            db.commit()
            print("✅ Usuário admin atualizado com sucesso!")
            print("📧 Email: admin@i9smart.com")
            print("🔑 Senha: Admin@123456")
            print("👤 Role: admin")
            return
        
        # Criar novo admin
        admin = User(
            email="admin@i9smart.com",
            username="adminuser",
            hashed_password=UserService.get_password_hash("Admin@123456"),
            full_name="Administrador do Sistema",
            role="admin",
            is_active=True,
            is_verified=True
        )
        
        db.add(admin)
        db.commit()
        print("✅ Usuário admin criado com sucesso!")
        print("📧 Email: admin@i9smart.com")
        print("🔑 Senha: Admin@123456")
        print("👤 Role: admin")
        
    except Exception as e:
        print(f"❌ Erro ao criar admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()