#!/usr/bin/env python3
"""
Script para limpar todas as tabelas do banco de dados
Ordem de limpeza respeitando foreign keys
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.config.settings import settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_all_tables():
    """
    Limpa todas as tabelas na ordem correta
    """
    # Ordem de limpeza (respeita foreign keys)
    tables_to_clean = [
        "campaign_images",    # Imagens das campanhas
        "campaign_stations",  # Relação campaign x station
        "campaigns",          # Campanhas
        "stations",          # Estações/Bicos
        "branches",          # Filiais
    ]
    
    # Criar engine
    engine = create_engine(str(settings.DATABASE_URL))
    
    logger.info("🔄 Iniciando limpeza do banco de dados...")
    
    # Limpar cada tabela em conexões separadas
    for table in tables_to_clean:
        try:
            with engine.connect() as conn:
                # Tentar TRUNCATE primeiro
                try:
                    result = conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                    conn.commit()
                    logger.info(f"✅ Tabela '{table}' limpa (TRUNCATE)")
                except:
                    # Se falhar, usar DELETE
                    result = conn.execute(text(f"DELETE FROM {table}"))
                    count = result.rowcount
                    conn.execute(text(f"ALTER SEQUENCE IF EXISTS {table}_id_seq RESTART WITH 1"))
                    conn.commit()
                    logger.info(f"✅ Tabela '{table}' limpa - {count} registros removidos")
                    
        except Exception as e:
            logger.warning(f"⚠️  Tabela '{table}': {str(e)}")
    
    # Verificar contagem final
    logger.info("\n📊 Verificando contagem final:")
    with engine.connect() as conn:
        for table in tables_to_clean:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                count = result.scalar()
                logger.info(f"   {table}: {count} registros")
            except Exception as e:
                logger.warning(f"   {table}: erro ao verificar - {str(e)}")
    
    logger.info("\n✨ Limpeza concluída!")
    engine.dispose()


def main():
    """
    Função principal
    """
    print("=" * 60)
    print("🧹 LIMPEZA COMPLETA DO BANCO DE DADOS")
    print("=" * 60)
    print("\n⚠️  ATENÇÃO: Este script irá DELETAR TODOS os dados de:")
    print("   - Campanhas")
    print("   - Imagens de campanhas")
    print("   - Estações/Bicos")
    print("   - Filiais")
    print("\n" + "=" * 60)
    
    print("✅ Executando limpeza automaticamente...")
    print("\n🚀 Iniciando limpeza...\n")
    
    try:
        clean_all_tables()
        print("\n✅ Banco de dados limpo com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante limpeza: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Verificar se estamos no ambiente correto
    if "production" in settings.ENVIRONMENT.lower():
        print("❌ ERRO: Não é possível executar limpeza em produção!")
        sys.exit(1)
    
    # Executar
    main()