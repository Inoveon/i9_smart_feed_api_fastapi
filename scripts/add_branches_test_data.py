#!/usr/bin/env python3
"""
Script para adicionar dados de teste de filiais e estações.
"""
import sys
import os
from uuid import uuid4
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.config.database import engine, get_db
from app.models.branch import Branch
from app.models.station import Station


def add_test_data():
    """Adiciona filiais e estações de teste."""
    db = next(get_db())
    
    try:
        # Dados das filiais com regiões
        branches_data = [
            # Sudeste
            {"code": "SP", "name": "São Paulo", "city": "São Paulo", "state": "SP"},
            {"code": "RJ", "name": "Rio de Janeiro", "city": "Rio de Janeiro", "state": "RJ"},
            {"code": "MG", "name": "Minas Gerais", "city": "Belo Horizonte", "state": "MG"},
            {"code": "ES", "name": "Espírito Santo", "city": "Vitória", "state": "ES"},
            
            # Sul
            {"code": "RS", "name": "Rio Grande do Sul", "city": "Porto Alegre", "state": "RS"},
            {"code": "SC", "name": "Santa Catarina", "city": "Florianópolis", "state": "SC"},
            {"code": "PR", "name": "Paraná", "city": "Curitiba", "state": "PR"},
            
            # Nordeste
            {"code": "BA", "name": "Bahia", "city": "Salvador", "state": "BA"},
            {"code": "PE", "name": "Pernambuco", "city": "Recife", "state": "PE"},
            {"code": "CE", "name": "Ceará", "city": "Fortaleza", "state": "CE"},
            
            # Norte
            {"code": "AM", "name": "Amazonas", "city": "Manaus", "state": "AM"},
            {"code": "PA", "name": "Pará", "city": "Belém", "state": "PA"},
            
            # Centro-Oeste
            {"code": "DF", "name": "Distrito Federal", "city": "Brasília", "state": "DF"},
            {"code": "GO", "name": "Goiás", "city": "Goiânia", "state": "GO"},
            {"code": "MT", "name": "Mato Grosso", "city": "Cuiabá", "state": "MT"},
        ]
        
        # Criar filiais
        branches = {}
        for branch_data in branches_data:
            # Verificar se já existe
            existing = db.query(Branch).filter(Branch.code == branch_data["code"]).first()
            
            if existing:
                print(f"Filial {branch_data['code']} já existe")
                branches[branch_data["code"]] = existing
            else:
                branch = Branch(**branch_data)
                db.add(branch)
                db.flush()
                branches[branch_data["code"]] = branch
                print(f"Filial {branch_data['code']} - {branch_data['name']} criada")
        
        # Dados das estações (vamos criar 3-5 estações por filial principal)
        stations_data = [
            # São Paulo
            {"branch": "SP", "code": "001", "name": "Posto Shell Paulista", "address": "Av. Paulista, 1000"},
            {"branch": "SP", "code": "002", "name": "Posto BR Centro", "address": "Rua da Consolação, 500"},
            {"branch": "SP", "code": "003", "name": "Posto Ipiranga Vila Mariana", "address": "Av. Domingos de Morais, 200"},
            {"branch": "SP", "code": "004", "name": "Posto Shell Moema", "address": "Av. Ibirapuera, 800"},
            {"branch": "SP", "code": "005", "name": "Posto BR Pinheiros", "address": "Rua Teodoro Sampaio, 1500"},
            
            # Rio de Janeiro
            {"branch": "RJ", "code": "001", "name": "Posto Shell Copacabana", "address": "Av. Atlântica, 2000"},
            {"branch": "RJ", "code": "002", "name": "Posto BR Botafogo", "address": "Praia de Botafogo, 300"},
            {"branch": "RJ", "code": "003", "name": "Posto Ipiranga Ipanema", "address": "Rua Visconde de Pirajá, 400"},
            {"branch": "RJ", "code": "004", "name": "Posto Shell Barra", "address": "Av. das Américas, 5000"},
            
            # Minas Gerais
            {"branch": "MG", "code": "001", "name": "Posto Shell Savassi", "address": "Av. Getúlio Vargas, 1000"},
            {"branch": "MG", "code": "002", "name": "Posto BR Funcionários", "address": "Rua Pernambuco, 500"},
            {"branch": "MG", "code": "003", "name": "Posto Ipiranga Centro", "address": "Av. Afonso Pena, 2000"},
            
            # Rio Grande do Sul
            {"branch": "RS", "code": "001", "name": "Posto Shell Moinhos", "address": "Rua 24 de Outubro, 800"},
            {"branch": "RS", "code": "002", "name": "Posto BR Centro", "address": "Av. Borges de Medeiros, 1500"},
            {"branch": "RS", "code": "003", "name": "Posto Ipiranga Zona Sul", "address": "Av. Ipiranga, 3000"},
            
            # Bahia
            {"branch": "BA", "code": "001", "name": "Posto Shell Barra", "address": "Av. Oceânica, 2000"},
            {"branch": "BA", "code": "002", "name": "Posto BR Pituba", "address": "Av. Paulo VI, 1000"},
            {"branch": "BA", "code": "003", "name": "Posto Ipiranga Rio Vermelho", "address": "Rua da Paciência, 500"},
            
            # Distrito Federal
            {"branch": "DF", "code": "001", "name": "Posto Shell Asa Sul", "address": "SQS 308, Bloco A"},
            {"branch": "DF", "code": "002", "name": "Posto BR Asa Norte", "address": "SQN 210, Bloco B"},
            {"branch": "DF", "code": "003", "name": "Posto Ipiranga Lago Sul", "address": "SHIS QI 15, Conjunto 8"},
        ]
        
        # Criar estações
        for station_data in stations_data:
            branch_code = station_data.pop("branch")
            
            if branch_code not in branches:
                print(f"Filial {branch_code} não encontrada, pulando estação {station_data['code']}")
                continue
            
            branch = branches[branch_code]
            
            # Verificar se já existe
            existing = db.query(Station).filter(
                Station.branch_id == branch.id,
                Station.code == station_data["code"]
            ).first()
            
            if existing:
                print(f"Estação {station_data['code']} já existe na filial {branch_code}")
            else:
                station = Station(
                    branch_id=branch.id,
                    **station_data
                )
                db.add(station)
                print(f"Estação {station_data['code']} - {station_data['name']} criada na filial {branch_code}")
        
        # Commit final
        db.commit()
        print("\n✅ Dados de teste adicionados com sucesso!")
        
        # Estatísticas
        total_branches = db.query(Branch).count()
        total_stations = db.query(Station).count()
        print(f"\n📊 Estatísticas:")
        print(f"  - Total de filiais: {total_branches}")
        print(f"  - Total de estações: {total_stations}")
        
        # Mostrar distribuição por região
        print(f"\n🌎 Distribuição por Região:")
        from app.utils.regions import REGIONS
        
        for region in REGIONS:
            branches_in_region = db.query(Branch).filter(
                Branch.state.in_(["SP", "RJ", "MG", "ES"] if region == "Sudeste"
                               else ["RS", "SC", "PR"] if region == "Sul"
                               else ["BA", "PE", "CE", "AL", "SE", "PB", "MA", "PI", "RN"] if region == "Nordeste"
                               else ["AM", "PA", "AC", "AP", "RO", "RR", "TO"] if region == "Norte"
                               else ["DF", "GO", "MT", "MS"])
            ).count()
            
            if branches_in_region > 0:
                print(f"  - {region}: {branches_in_region} filiais")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao adicionar dados de teste: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Adicionando dados de teste de filiais e estações...\n")
    add_test_data()