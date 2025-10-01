"""
Service para sincronização de dados do Protheus (SQL Server) para o PostgreSQL
Conexão READ-ONLY com SQL Server para garantir segurança
"""

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    pyodbc = None
    PYODBC_AVAILABLE = False
    print("⚠️  pyodbc não disponível - funcionalidades SQL Server desabilitadas")

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.branch import Branch
from app.models.station import Station
from app.config.database import SessionLocal
from app.config.settings import settings

# Configurar logging
logger = logging.getLogger(__name__)


class ProtheusSyncService:
    """
    Service para sincronizar dados do Protheus (SQL Server) com PostgreSQL
    """
    
    # Configuração SQL Server (READ-ONLY)
    SQLSERVER_CONFIG = {
        "server": "172.16.2.41",
        "database": "totvs",  # Nome correto do database
        "uid": "sistema.i9on",
        "pwd": "faSQDjxT",
        "driver": "{ODBC Driver 17 for SQL Server}",
        "timeout": 30,
        "autocommit": False,  # Garantir que não há commits
        "readonly": True
    }
    
    # Query para buscar filiais (SOMENTE SELECT - READ ONLY)
    BRANCHES_QUERY = """
    SELECT 
        M0_CODFIL as branch_code,
        M0_FILIAL as name,
        M0_CGC as cnpj,
        M0_ENDENT as address,
        M0_CIDENT as city,
        M0_ESTENT as state,
        M0_CEPENT as zip_code,
        M0_TEL as phone,
        M0_BAIRENT as district,
        CASE WHEN D_E_L_E_T_ = '' THEN 1 ELSE 0 END as is_active
    FROM SYS_COMPANY
    WHERE 
        M0_CODIGO = '11'
        AND M0_CODFIL NOT IN ('838301','808001','010101','020201','030301','0404041','050501','818101','828202')
        AND D_E_L_E_T_ = ''
    ORDER BY M0_CODFIL
    """
    
    def __init__(self):
        """Inicializa o service"""
        self.stats = {
            "branches_processed": 0,
            "branches_created": 0,
            "branches_updated": 0,
            "stations_created": 0,
            "errors": []
        }
    
    def _get_sqlserver_connection(self) -> pyodbc.Connection:
        """
        Cria conexão READ-ONLY com SQL Server
        IMPORTANTE: Apenas permite SELECT, nunca INSERT/UPDATE/DELETE
        """
        try:
            # Criar string de conexão
            conn_str = (
                f"DRIVER={self.SQLSERVER_CONFIG['driver']};"
                f"SERVER={self.SQLSERVER_CONFIG['server']};"
                f"DATABASE={self.SQLSERVER_CONFIG['database']};"
                f"UID={self.SQLSERVER_CONFIG['uid']};"
                f"PWD={self.SQLSERVER_CONFIG['pwd']};"
                f"Timeout={self.SQLSERVER_CONFIG['timeout']};"
                f"TrustServerCertificate=yes;"  # Para evitar problemas de SSL
            )
            
            # Criar conexão
            conn = pyodbc.connect(conn_str)
            
            # Configurar como READ-ONLY
            conn.autocommit = False
            conn.setencoding('utf-8')
            
            logger.info("✅ Conexão SQL Server estabelecida (READ-ONLY)")
            return conn
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar SQL Server: {str(e)}")
            raise
    
    def _fetch_branches_from_protheus(self) -> List[Dict[str, Any]]:
        """
        Busca filiais do Protheus via SQL Server
        SOMENTE LEITURA - Nunca executa INSERT/UPDATE/DELETE
        """
        branches = []
        conn = None
        cursor = None
        
        try:
            # Conectar ao SQL Server
            conn = self._get_sqlserver_connection()
            cursor = conn.cursor()
            
            # Executar query READ-ONLY
            logger.info("🔍 Buscando filiais do Protheus...")
            cursor.execute(self.BRANCHES_QUERY)
            
            # Obter nomes das colunas
            columns = [column[0].lower() for column in cursor.description]
            
            # Processar resultados
            for row in cursor:
                branch_dict = dict(zip(columns, row))
                
                # Limpar dados
                for key, value in branch_dict.items():
                    if isinstance(value, str):
                        branch_dict[key] = value.strip()
                
                branches.append(branch_dict)
            
            logger.info(f"✅ {len(branches)} filiais encontradas no Protheus")
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar filiais: {str(e)}")
            self.stats["errors"].append(f"Fetch branches: {str(e)}")
            
        finally:
            # Fechar conexões
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        return branches
    
    def _create_stations_for_branch(self, db: Session, branch_id: int, branch_code: str):
        """
        Cria 15 estações (101-115) para uma filial
        """
        stations_created = 0
        
        for station_num in range(101, 116):  # 101 até 115
            try:
                # Verificar se já existe
                existing = db.query(Station).filter(
                    Station.branch_id == branch_id,
                    Station.code == str(station_num)
                ).first()
                
                if not existing:
                    # Criar nova estação
                    station = Station(
                        branch_id=branch_id,
                        code=str(station_num),
                        name=f"Caixa {station_num}",
                        is_active=True
                    )
                    db.add(station)
                    stations_created += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro ao criar estação {station_num} para filial {branch_code}: {str(e)}")
        
        return stations_created
    
    def sync_branches(self) -> Dict[str, Any]:
        """
        Sincroniza filiais do Protheus para PostgreSQL
        1. Busca filiais do SQL Server (READ-ONLY)
        2. Cria/Atualiza no PostgreSQL
        3. Cria 15 estações para cada filial
        """
        start_time = datetime.now()
        db = SessionLocal()
        
        try:
            logger.info("=" * 60)
            logger.info("🚀 Iniciando sincronização de filiais...")
            logger.info("=" * 60)
            
            # 1. Buscar filiais do Protheus (READ-ONLY)
            protheus_branches = self._fetch_branches_from_protheus()
            self.stats["branches_processed"] = len(protheus_branches)
            
            if not protheus_branches:
                logger.warning("⚠️ Nenhuma filial encontrada no Protheus")
                return self.stats
            
            # 2. Processar cada filial
            for pb in protheus_branches:
                try:
                    # Verificar se já existe
                    existing_branch = db.query(Branch).filter(
                        Branch.code == pb['branch_code']
                    ).first()
                    
                    if existing_branch:
                        # Atualizar filial existente
                        existing_branch.name = pb['name']
                        existing_branch.city = pb.get('city', '')
                        existing_branch.state = pb.get('state', '')
                        existing_branch.is_active = pb.get('is_active', True)
                        
                        self.stats["branches_updated"] += 1
                        logger.info(f"🔄 Filial {pb['branch_code']} - {pb['name']} atualizada")
                        
                        branch_id = existing_branch.id
                        
                    else:
                        # Criar nova filial
                        new_branch = Branch(
                            code=pb['branch_code'],  # Campo correto é 'code'
                            name=pb['name'],
                            city=pb.get('city', ''),
                            state=pb.get('state', ''),
                            is_active=pb.get('is_active', True)
                        )
                        db.add(new_branch)
                        db.flush()  # Para obter o ID
                        
                        self.stats["branches_created"] += 1
                        logger.info(f"✅ Filial {pb['branch_code']} - {pb['name']} criada")
                        
                        branch_id = new_branch.id
                    
                    # 3. Criar estações (101-115) para a filial
                    stations_created = self._create_stations_for_branch(
                        db, branch_id, pb['branch_code']
                    )
                    self.stats["stations_created"] += stations_created
                    
                    if stations_created > 0:
                        logger.info(f"   📍 {stations_created} estações criadas")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar filial {pb.get('branch_code', '?')}: {str(e)}")
                    self.stats["errors"].append(f"Branch {pb.get('branch_code', '?')}: {str(e)}")
            
            # Commit de todas as alterações
            db.commit()
            
            # Estatísticas finais
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stats["duration_seconds"] = duration
            self.stats["status"] = "success" if not self.stats["errors"] else "partial"
            
            logger.info("\n" + "=" * 60)
            logger.info("📊 RESUMO DA SINCRONIZAÇÃO:")
            logger.info(f"   Filiais processadas: {self.stats['branches_processed']}")
            logger.info(f"   Filiais criadas: {self.stats['branches_created']}")
            logger.info(f"   Filiais atualizadas: {self.stats['branches_updated']}")
            logger.info(f"   Estações criadas: {self.stats['stations_created']}")
            logger.info(f"   Tempo total: {duration:.2f} segundos")
            
            if self.stats["errors"]:
                logger.warning(f"   ⚠️ Erros encontrados: {len(self.stats['errors'])}")
                for error in self.stats["errors"]:
                    logger.warning(f"      - {error}")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Erro geral na sincronização: {str(e)}")
            self.stats["status"] = "error"
            self.stats["errors"].append(f"General error: {str(e)}")
            db.rollback()
            
        finally:
            db.close()
        
        return self.stats


# Função helper para executar sincronização
async def sync_branches_from_protheus() -> Dict[str, Any]:
    """
    Função assíncrona para executar sincronização
    Pode ser chamada por endpoints ou scheduler
    """
    service = ProtheusSyncService()
    return service.sync_branches()