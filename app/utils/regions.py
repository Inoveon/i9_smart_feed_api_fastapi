"""
Utilidades para trabalhar com regiões brasileiras.
"""
from typing import Dict, List, Optional

# Mapeamento de estados para regiões
STATE_TO_REGION: Dict[str, str] = {
    # Norte
    "AC": "Norte",
    "AP": "Norte",
    "AM": "Norte",
    "PA": "Norte",
    "RO": "Norte",
    "RR": "Norte",
    "TO": "Norte",
    
    # Nordeste
    "AL": "Nordeste",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "MA": "Nordeste",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "RN": "Nordeste",
    "SE": "Nordeste",
    
    # Centro-Oeste
    "DF": "Centro-Oeste",
    "GO": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    
    # Sudeste
    "ES": "Sudeste",
    "MG": "Sudeste",
    "RJ": "Sudeste",
    "SP": "Sudeste",
    
    # Sul
    "PR": "Sul",
    "RS": "Sul",
    "SC": "Sul"
}

# Regiões válidas
REGIONS = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

# Estados por região
REGION_TO_STATES: Dict[str, List[str]] = {
    "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"]
}

# Alias para compatibilidade
REGIONS_MAPPING = REGION_TO_STATES


def get_region_by_state(state: str) -> Optional[str]:
    """Retorna a região de um estado."""
    return STATE_TO_REGION.get(state.upper())


def get_states_by_region(region: str) -> List[str]:
    """Retorna os estados de uma região."""
    return REGION_TO_STATES.get(region, [])


def is_valid_state(state: str) -> bool:
    """Verifica se é um estado válido."""
    return state.upper() in STATE_TO_REGION


def is_valid_region(region: str) -> bool:
    """Verifica se é uma região válida."""
    return region in REGIONS