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
class Choices:
    subgroup_column: Optional[str] = None
    show_detailed: bool = False
    critical_min_inputs: int = 3
    critical_min_reuse: int = 3
    no_grouping: bool = False
    output_format: str = "md"

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