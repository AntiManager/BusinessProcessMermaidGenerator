"""
Ядро системы - основные модули для работы с бизнес-процессами
"""

from .data_loader import load_and_validate_data, collect_operations
from .analysis import analyse_network
from .models import Operation, Choices, ProcessAnalysis, AnalysisData

__all__ = [
    'load_and_validate_data',
    'collect_operations', 
    'analyse_network',
    'Operation',
    'Choices',
    'ProcessAnalysis',
    'AnalysisData'
]