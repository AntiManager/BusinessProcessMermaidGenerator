"""
Data classes и модели данных с улучшенной валидацией
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
import re

@dataclass
class Operation:
    name: str
    outputs: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    subgroup: Optional[str] = None
    node_text: str = ""
    group: str = ""
    owner: str = ""
    detailed: str = ""
    
    def __post_init__(self):
        """Валидация данных после инициализации"""
        self._validate()
    
    def _validate(self):
        """Валидация данных операции"""
        if not self.name or not self.name.strip():
            raise ValueError("Имя операции не может быть пустым")
        
        # Очистка данных
        self.name = self.name.strip()
        self.outputs = [out.strip() for out in self.outputs if out and str(out).strip()]
        self.inputs = [inp.strip() for inp in self.inputs if inp and str(inp).strip()]
        
        if self.subgroup:
            self.subgroup = str(self.subgroup).strip()
            if self.subgroup.lower() == 'nan':
                self.subgroup = None

@dataclass
class CausalLink:
    """Причинно-следственная связь для CLD с валидацией"""
    source: str
    target: str 
    influence: str  # "+" или "-"
    strength: Optional[str] = None
    operation: Optional[str] = None
    include_in_cld: bool = True
    description: str = ""
    
    def __post_init__(self):
        """Валидация связи"""
        self._validate()
    
    def _validate(self):
        """Валидация данных связи"""
        if not self.source or not self.source.strip():
            raise ValueError("Источник связи не может быть пустым")
        
        if not self.target or not self.target.strip():
            raise ValueError("Цель связи не может быть пустой")
        
        if self.influence not in ["+", "-"]:
            raise ValueError(f"Некорректный знак влияния: {self.influence}. Допустимы '+' или '-'")
        
        # Очистка данных
        self.source = self.source.strip()
        self.target = self.target.strip()
        self.influence = self.influence.strip()

# Остальные data classes остаются без изменений, но добавляем валидацию где необходимо
@dataclass
class Choices:
    subgroup_column: Optional[str] = None
    show_detailed: bool = False
    critical_min_inputs: int = 3
    critical_min_reuse: int = 3
    no_grouping: bool = False
    output_format: str = "md"
    cld_source_type: str = "auto"
    cld_sheet_name: str = ""
    show_cld_operations: bool = True
    cld_influence_signs: bool = True
    
    def __post_init__(self):
        """Валидация настроек"""
        valid_formats = ["md", "html_mermaid", "html_interactive", "cld_mermaid", "cld_interactive"]
        if self.output_format not in valid_formats:
            raise ValueError(f"Некорректный формат вывода: {self.output_format}")
        
        if self.cld_source_type not in ["auto", "manual"]:
            raise ValueError(f"Некорректный тип источника CLD: {self.cld_source_type}")

# Остальные data classes остаются без изменений...
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

@dataclass
class CausalAnalysis:
    """Анализ причинно-следственных связей"""
    links: List[CausalLink]
    variables: Set[str]
    feedback_loops: List[List[str]]
    source_type: str  # "manual" или "auto"
    statistics: Dict[str, Any]