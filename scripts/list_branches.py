#!/usr/bin/env python3
"""
Script para listar todas as filiais cadastradas no banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.database import SessionLocal
from app.models.branch import Branch
from app.models.station import Station
from sqlalchemy import func

def list_all_branches():
    """
    Lista todas as filiais com suas informações e quantidade de estações
    """
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("📍 LISTA DE FILIAIS CADASTRADAS")
        print("=" * 80)
        
        # Buscar todas as filiais ordenadas por código
        branches = db.query(
            Branch,
            func.count(Station.id).label('station_count')
        ).outerjoin(
            Station, Branch.id == Station.branch_id
        ).group_by(
            Branch.id
        ).order_by(
            Branch.code
        ).all()
        
        if not branches:
            print("❌ Nenhuma filial encontrada no banco de dados.")
            return
        
        print(f"\n📊 Total de filiais: {len(branches)}\n")
        
        # Cabeçalho da tabela
        print(f"{'Código':<10} {'Nome':<40} {'Cidade':<20} {'UF':<4} {'Ativa':<7} {'Estações':<10}")
        print("-" * 95)
        
        total_active = 0
        total_inactive = 0
        total_stations = 0
        
        for branch, station_count in branches:
            status = "✅ Sim" if branch.is_active else "❌ Não"
            
            # Contar ativos/inativos
            if branch.is_active:
                total_active += 1
            else:
                total_inactive += 1
            
            total_stations += station_count
            
            # Truncar nome se muito longo
            name = branch.name[:37] + "..." if len(branch.name) > 40 else branch.name
            city = branch.city[:17] + "..." if len(branch.city) > 20 else branch.city
            
            print(f"{branch.code:<10} {name:<40} {city:<20} {branch.state:<4} {status:<7} {station_count:<10}")
        
        print("-" * 95)
        
        # Resumo estatístico
        print("\n📈 RESUMO ESTATÍSTICO:")
        print(f"   • Total de filiais: {len(branches)}")
        print(f"   • Filiais ativas: {total_active}")
        print(f"   • Filiais inativas: {total_inactive}")
        print(f"   • Total de estações: {total_stations}")
        print(f"   • Média de estações por filial: {total_stations/len(branches):.1f}")
        
        # Listar por estado
        states = db.query(
            Branch.state,
            func.count(Branch.id).label('count')
        ).group_by(
            Branch.state
        ).order_by(
            func.count(Branch.id).desc()
        ).all()
        
        print("\n📍 DISTRIBUIÇÃO POR ESTADO:")
        for state, count in states:
            if state:
                print(f"   • {state}: {count} filiais")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Erro ao listar filiais: {str(e)}")
        raise
    finally:
        db.close()

def export_to_csv():
    """
    Exporta a lista de filiais para CSV
    """
    db = SessionLocal()
    
    try:
        import csv
        
        branches = db.query(Branch).order_by(Branch.code).all()
        
        filename = "filiais_lista.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Código', 'Nome', 'Cidade', 'Estado', 'Ativa'])
            
            for branch in branches:
                writer.writerow([
                    branch.code,
                    branch.name,
                    branch.city,
                    branch.state,
                    'Sim' if branch.is_active else 'Não'
                ])
        
        print(f"\n✅ Lista exportada para: {filename}")
        
    except Exception as e:
        print(f"❌ Erro ao exportar: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    # Listar todas as filiais
    list_all_branches()
    
    # Perguntar se deseja exportar
    response = input("\n💾 Deseja exportar para CSV? (s/N): ")
    if response.lower() == 's':
        export_to_csv()