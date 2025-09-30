#!/usr/bin/env python3
"""
Cria usuário de teste para autenticação
"""
import sys
sys.path.append('.')

from app.config.database import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash
from datetime import datetime

def create_test_user():
    """Cria usuário de teste admin@test.com"""
    db = SessionLocal()
    
    try:
        # Verificar se já existe
        existing = db.query(User).filter(User.email == "admin@test.com").first()
        
        if existing:
            print("✅ Usuário admin@test.com já existe")
            return
        
        # Criar novo usuário
        new_user = User(
            name="Admin Test",
            email="admin@test.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(new_user)
        db.commit()
        
        print("✅ Usuário admin@test.com criado com sucesso!")
        print("   Email: admin@test.com")
        print("   Senha: admin123")
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {str(e)}")
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()