#!/usr/bin/env python3
"""
Script para adicionar dados realistas de filiais e estações.
Códigos numéricos (010101 até 131301) com 10 estações cada.
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


def generate_branch_data():
    """Gera dados de filiais com códigos numéricos realistas."""
    branches_data = []
    
    # Códigos sequenciais com múltiplas filiais por estado
    branch_configs = [
        # São Paulo - múltiplas filiais
        {"base_code": "010101", "count": 8, "state": "SP", "city": "São Paulo"},
        {"base_code": "011101", "count": 3, "state": "SP", "city": "Campinas"},
        {"base_code": "012101", "count": 2, "state": "SP", "city": "Santos"},
        
        # Rio de Janeiro - múltiplas filiais
        {"base_code": "020201", "count": 5, "state": "RJ", "city": "Rio de Janeiro"},
        {"base_code": "021201", "count": 2, "state": "RJ", "city": "Niterói"},
        
        # Minas Gerais - múltiplas filiais
        {"base_code": "030301", "count": 4, "state": "MG", "city": "Belo Horizonte"},
        {"base_code": "031301", "count": 2, "state": "MG", "city": "Uberlândia"},
        
        # Rio Grande do Sul - múltiplas filiais
        {"base_code": "040401", "count": 3, "state": "RS", "city": "Porto Alegre"},
        {"base_code": "041401", "count": 2, "state": "RS", "city": "Caxias do Sul"},
        
        # Bahia
        {"base_code": "050501", "count": 3, "state": "BA", "city": "Salvador"},
        {"base_code": "051501", "count": 2, "state": "BA", "city": "Feira de Santana"},
        
        # Paraná
        {"base_code": "060601", "count": 3, "state": "PR", "city": "Curitiba"},
        {"base_code": "061601", "count": 2, "state": "PR", "city": "Londrina"},
        
        # Santa Catarina
        {"base_code": "070701", "count": 2, "state": "SC", "city": "Florianópolis"},
        {"base_code": "071701", "count": 2, "state": "SC", "city": "Blumenau"},
        
        # Goiás
        {"base_code": "080801", "count": 2, "state": "GO", "city": "Goiânia"},
        {"base_code": "081801", "count": 1, "state": "GO", "city": "Anápolis"},
        
        # Pernambuco
        {"base_code": "090901", "count": 2, "state": "PE", "city": "Recife"},
        {"base_code": "091901", "count": 1, "state": "PE", "city": "Caruaru"},
        
        # Ceará
        {"base_code": "101001", "count": 2, "state": "CE", "city": "Fortaleza"},
        {"base_code": "102001", "count": 1, "state": "CE", "city": "Juazeiro do Norte"},
        
        # Distrito Federal
        {"base_code": "111101", "count": 2, "state": "DF", "city": "Brasília"},
        
        # Espírito Santo
        {"base_code": "121201", "count": 2, "state": "ES", "city": "Vitória"},
        
        # Amazonas
        {"base_code": "131301", "count": 1, "state": "AM", "city": "Manaus"},
    ]
    
    for config in branch_configs:
        base_code = int(config["base_code"])
        for i in range(config["count"]):
            code = f"{base_code + i:06d}"  # Sempre 6 dígitos com zeros à esquerda
            name = f"Filial {config['city']} {i+1:02d}"
            if config["count"] == 1:
                name = f"Filial {config['city']}"
            
            branches_data.append({
                "code": code,
                "name": name,
                "city": config["city"],
                "state": config["state"]
            })
    
    return branches_data


def generate_stations_data(branch_code: str, branch_name: str, city: str):
    """Gera 10 estações para uma filial."""
    stations_data = []
    
    station_types = [
        "Posto Central",
        "Auto Service",
        "Express",
        "Shopping Center", 
        "Rodovia",
        "Aeroporto",
        "Terminal",
        "Centro",
        "Bairro Norte",
        "Bairro Sul"
    ]
    
    for i in range(10):  # 001 até 010
        station_code = f"{i+1:03d}"  # 001, 002, 003...
        station_name = f"{branch_name} - {station_types[i]}"
        address = f"Endereço da {station_types[i]}, {city}"
        
        stations_data.append({
            "code": station_code,
            "name": station_name,
            "address": address
        })
    
    return stations_data


def add_realistic_data():
    """Adiciona dados realistas de filiais e estações."""
    db = next(get_db())
    
    try:
        print("🚀 Iniciando adição de dados realistas...\n")
        
        # Limpar dados existentes se houver
        print("🗑️ Limpando dados existentes...")
        db.query(Station).delete()
        db.query(Branch).delete()
        db.commit()
        
        # Gerar dados de filiais
        branches_data = generate_branch_data()
        
        print(f"📊 Serão criadas {len(branches_data)} filiais")
        print(f"📊 Serão criadas {len(branches_data) * 10} estações\n")
        
        # Criar filiais
        branches = {}
        for i, branch_data in enumerate(branches_data, 1):
            branch = Branch(**branch_data)
            db.add(branch)
            db.flush()
            
            branches[branch_data["code"]] = branch
            
            print(f"✅ [{i:2d}/{len(branches_data):2d}] Filial {branch_data['code']} - {branch_data['name']} ({branch_data['state']})")
        
        print(f"\n🏢 {len(branches_data)} filiais criadas!")
        
        # Criar estações para cada filial
        total_stations = 0
        print(f"\n🏪 Criando estações...")
        
        for branch_code, branch in branches.items():
            stations_data = generate_stations_data(branch_code, branch.name, branch.city)
            
            for station_data in stations_data:
                station = Station(
                    branch_id=branch.id,
                    **station_data
                )
                db.add(station)
                total_stations += 1
            
            print(f"   📍 Filial {branch_code}: 10 estações criadas")
        
        # Commit final
        db.commit()
        print(f"\n✅ CONCLUÍDO!")
        print(f"   🏢 Total de filiais: {len(branches_data)}")
        print(f"   🏪 Total de estações: {total_stations}")
        
        # Estatísticas por região
        print(f"\n📊 DISTRIBUIÇÃO POR REGIÃO:")
        from app.utils.regions import REGIONS, get_states_by_region
        
        for region in REGIONS:
            states = get_states_by_region(region)
            branches_count = db.query(Branch).filter(Branch.state.in_(states)).count()
            if branches_count > 0:
                print(f"   🌎 {region}: {branches_count} filiais")
        
        # Mostrar alguns exemplos
        print(f"\n🎯 EXEMPLOS DE CÓDIGOS CRIADOS:")
        sample_branches = db.query(Branch).limit(5).all()
        for branch in sample_branches:
            stations_count = db.query(Station).filter(Station.branch_id == branch.id).count()
            print(f"   📋 {branch.code} - {branch.name} ({branch.state}) - {stations_count} estações")
            
        print(f"\n🔗 EXEMPLO DE TARGETING:")
        print(f"   # Campanha para filiais de SP")
        sp_codes = [b.code for b in db.query(Branch).filter(Branch.state == "SP").limit(3).all()]
        print(f"   branches: {sp_codes}")
        print(f"   stations: ['001', '002', '003']  # Primeiras 3 estações")
        
        print(f"\n💡 DICA: Use /api/stations/available para ver a estrutura completa")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao adicionar dados: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_realistic_data()