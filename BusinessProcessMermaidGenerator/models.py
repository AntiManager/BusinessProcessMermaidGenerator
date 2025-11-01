"""
Data classes и модели данных
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Set

@dataclass
class Operation:
    name: str
    outputs: List[str]
    inputs: List[str]
    subgroup: Optional[str]
    node_text: str
    group: str = ""
    owner: str = ""
    detailed: str = ""

@dataclass
class CausalLink:
    """Причинно-следственная связь для CLD"""
    source: str
    target: str 
    influence: str  # "+" или "-"
    strength: Optional[str] = None
    operation: Optional[str] = None
    include_in_cld: bool = True
    description: str = ""

@dataclass
class CausalAnalysis:
    """Анализ причинно-следственных связей"""
    links: List[CausalLink]
    variables: Set[str]
    feedback_loops: List[List[str]]
    source_type: str  # "manual" или "auto"
    statistics: Dict[str, Any]

@dataclass
class Choices:
    subgroup_column: Optional[str] = None
    show_detailed: bool = False
    critical_min_inputs: int = 3
    critical_min_reuse: int = 3
    no_grouping: bool = False
    output_format: str = "md"
    cld_source_type: str = "auto"  # "auto" из бизнес-процессов или "manual" из отдельной таблицы
    cld_sheet_name: str = ""
    show_cld_operations: bool = True
    cld_influence_signs: bool = True

@dataclass
class MergePoint:
    operation: str
    input_count: int
    inputs: List[str]

@dataclass
class SplitPoint:
    output: str
    source_operation: str
    target_count: int
    targets: List[str]

@dataclass
class CriticalPoint:
    operation: str
    inputs_count: int
    output_reuse: int

@dataclass
class ProcessAnalysis:
    merge_points: List[MergePoint]
    split_points: List[SplitPoint]
    critical_points: List[CriticalPoint]
    external_inputs: Set[str]
    final_outputs: Set[str]
    operations_count: int
    subgroups_count: int
    groups_count: int
    owners_count: int

@dataclass
class AnalysisData:
    external_inputs: Set[str]
    final_outputs: Set[str]
    output_to_operation: Dict[str, str]
    input_to_operations: Dict[str, List[str]]
    analysis: ProcessAnalysis

    def get_complexity_score(self, operations: Dict[str, Operation]) -> int:
        """Рассчитать оценку сложности процесса от 1 до 10"""
        analysis = self.analysis
        
        weights = {
            'operations': 0.3,
            'merge_points': 0.2,
            'split_points': 0.2,
            'critical_points': 0.3
        }
        
        max_operations = 50
        max_merge = 10
        max_split = 10
        max_critical = 5
        
        op_score = min(len(operations) / max_operations, 1.0)
        merge_score = min(len(analysis.merge_points) / max_merge, 1.0)
        split_score = min(len(analysis.split_points) / max_split, 1.0)
        critical_score = min(len(analysis.critical_points) / max_critical, 1.0)
        
        total_score = (
            op_score * weights['operations'] +
            merge_score * weights['merge_points'] +
            split_score * weights['split_points'] +
            critical_score * weights['critical_points']
        )
        
        return min(10, int(total_score * 10) + 1)