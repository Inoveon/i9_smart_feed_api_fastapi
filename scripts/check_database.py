#!/usr/bin/env python3
"""
Script para verificar estado do banco de dados
Usado durante o deploy para determinar se é primeira instalação ou upgrade
"""

import sys
import os
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory


def check_database_exists(database_url: str) -> bool:
    """Verifica se consegue conectar no banco"""
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar no banco: {e}")
        return False


def check_alembic_initialized(database_url: str) -> bool:
    """Verifica se Alembic já foi inicializado (tabela alembic_version existe)"""
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                );
            """))
            return result.scalar()
    except Exception:
        return False


def get_current_revision(database_url: str) -> str:
    """Obtém a revisão atual do banco"""
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            return context.get_current_revision()
    except Exception:
        return None


def get_pending_migrations(alembic_cfg_path: str = "alembic.ini") -> list:
    """Obtém lista de migrações pendentes"""
    try:
        config = Config(alembic_cfg_path)
        script = ScriptDirectory.from_config(config)
        
        # Obter revisão atual do banco
        database_url = config.get_main_option("sqlalchemy.url")
        if not database_url:
            # Tentar obter de variável de ambiente
            database_url = os.getenv("DATABASE_URL")
        
        current_rev = get_current_revision(database_url)
        head_rev = script.get_current_head()
        
        if current_rev == head_rev:
            return []
        
        # Obter migrações pendentes
        revisions = []
        for revision in script.walk_revisions(current_rev, head_rev):
            if revision.revision != current_rev:
                revisions.append(revision.revision)
        
        return revisions
    except Exception as e:
        print(f"⚠️  Erro ao verificar migrações: {e}")
        return []


def main():
    """Função principal"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL não configurada")
        sys.exit(1)
    
    print("🔍 Verificando estado do banco de dados...")
    
    # 1. Verificar se banco existe
    if not check_database_exists(database_url):
        print("❌ BANCO_NAO_EXISTE")
        sys.exit(1)
    
    # 2. Verificar se Alembic foi inicializado
    if not check_alembic_initialized(database_url):
        print("🆕 PRIMEIRA_INSTALACAO")
        sys.exit(0)
    
    # 3. Verificar migrações pendentes
    current_rev = get_current_revision(database_url)
    pending = get_pending_migrations()
    
    if not pending:
        print("✅ BANCO_ATUALIZADO")
        print(f"📍 Revisão atual: {current_rev}")
    else:
        print("🔄 MIGRACOES_PENDENTES")
        print(f"📍 Revisão atual: {current_rev}")
        print(f"📋 Migrações pendentes: {len(pending)}")
        for rev in pending[:5]:  # Mostrar apenas as primeiras 5
            print(f"   - {rev}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()