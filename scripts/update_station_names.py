#!/usr/bin/env python3
"""
Script para atualizar os nomes das estações de 'Bomba' para 'Caixa'
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config.settings import settings
from app.config.database import SessionLocal
from app.models.branch import Branch  # Importar Branch primeiro
from app.models.station import Station
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_station_names():
    """
    Atualiza todos os nomes de estações que contém 'Bomba' para 'Caixa'
    """
    db = SessionLocal()
    
    try:
        logger.info("=" * 60)
        logger.info("🔄 Iniciando atualização dos nomes das estações...")
        logger.info("=" * 60)
        
        # Buscar todas as estações com 'Bomba' no nome
        stations_to_update = db.query(Station).filter(
            Station.name.like('%Bomba%')
        ).all()
        
        if not stations_to_update:
            logger.info("✅ Nenhuma estação com 'Bomba' encontrada. Tudo já está atualizado!")
            return
        
        logger.info(f"📊 Encontradas {len(stations_to_update)} estações para atualizar")
        
        updated_count = 0
        for station in stations_to_update:
            old_name = station.name
            new_name = old_name.replace('Bomba', 'Caixa')
            station.name = new_name
            updated_count += 1
            logger.info(f"   ✏️  {old_name} → {new_name}")
        
        # Commit das alterações
        db.commit()
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ ATUALIZAÇÃO CONCLUÍDA!")
        logger.info(f"   Total de estações atualizadas: {updated_count}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar estações: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def verify_update():
    """
    Verifica se a atualização foi bem sucedida
    """
    db = SessionLocal()
    
    try:
        logger.info("\n🔍 Verificando atualização...")
        
        # Verificar se ainda existem estações com 'Bomba'
        bomba_count = db.query(Station).filter(
            Station.name.like('%Bomba%')
        ).count()
        
        # Verificar estações com 'Caixa'
        caixa_count = db.query(Station).filter(
            Station.name.like('%Caixa%')
        ).count()
        
        logger.info(f"   Estações com 'Bomba': {bomba_count}")
        logger.info(f"   Estações com 'Caixa': {caixa_count}")
        
        if bomba_count == 0:
            logger.info("✅ Todas as estações foram atualizadas com sucesso!")
        else:
            logger.warning(f"⚠️  Ainda existem {bomba_count} estações com 'Bomba' no nome")
        
        # Mostrar algumas estações como exemplo
        sample_stations = db.query(Station).limit(5).all()
        if sample_stations:
            logger.info("\n📋 Amostra das estações atualizadas:")
            for station in sample_stations:
                logger.info(f"   • {station.code}: {station.name}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    try:
        # Executar atualização
        update_station_names()
        
        # Verificar resultado
        verify_update()
        
    except Exception as e:
        logger.error(f"❌ Erro geral: {str(e)}")
        sys.exit(1)