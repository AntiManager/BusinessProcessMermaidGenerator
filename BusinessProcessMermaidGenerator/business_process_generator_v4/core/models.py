"""
Модели данных
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Set

@dataclass
class Operation:
    name: str
    inputs: List[str]
    outputs: List[str]
    group: Optional[str] = None
    owner: Optional[str] = None
    detailed: Optional[str] = None
    subgroup: Optional[str] = None
    
    @property
    def node_text(self) -> str:
        """Текст для отображения в узле диаграммы"""
        if self.detailed:
            return f"{self.name}\n{self.detailed}"
        return self.name

@dataclass
class Choices:
    subgroup_column: Optional[str]
    show_detailed: bool
    critical_min_inputs: int
    critical_min_reuse: int
    output_format: str
    
    @property
    def no_grouping(self) -> bool:
        return self.subgroup_column is None

@dataclass
class CriticalPoint:
    operation: str
    inputs_count: int
    output_reuse: int

@dataclass
class MergePoint:
    operation: str
    input_count: int

@dataclass
class SplitPoint:
    output: str
    source_operation: str
    target_count: int

@dataclass
class ProcessAnalysis:
    operations_count: int
    external_inputs: Set[str]
    final_outputs: Set[str]
    merge_points: List[MergePoint]
    split_points: List[SplitPoint]
    critical_points: List[CriticalPoint]
    subgroups_count: int
    groups_count: int
    owners_count: int

@dataclass
class AnalysisData:
    external_inputs: Set[str]
    final_outputs: Set[str]
    input_to_operations: Dict[str, List[str]]
    output_to_operation: Dict[str, str]
    analysis: ProcessAnalysis