"""
Анализ бизнес-процессов
"""
from collections import defaultdict
from typing import Dict, Set, Tuple, List
from models import Operation, Choices, ProcessAnalysis, MergePoint, SplitPoint, CriticalPoint, AnalysisData

def analyze_process_patterns(
    operations: Dict[str, Operation],
    input_to_operations: Dict[str, List[str]]
) -> Tuple[List[MergePoint], List[SplitPoint]]:
    """
    Анализирует точки слияния и разветвления в процессах
    """
    merge_points = []
    split_points = []

    for op_name, op_data in operations.items():
        # Анализ точек слияния (по входам)
        if len(op_data.inputs) > 1:
            merge_points.append(MergePoint(
                operation=op_name,
                input_count=len(op_data.inputs),
                inputs=op_data.inputs
            ))
        
        # Анализ точек разветвления (по ВЫХОДАМ)
        for output in op_data.outputs:
            if output in input_to_operations and len(input_to_operations[output]) > 1:
                split_points.append(SplitPoint(
                    output=output,
                    source_operation=op_name,
                    target_count=len(input_to_operations[output]),
                    targets=input_to_operations[output]
                ))
    return merge_points, split_points

def analyse_network(
    operations: Dict[str, Operation], choices: Choices
) -> AnalysisData:
    """
    Основной анализ сети процессов
    """
    all_inputs: Set[str] = set()
    all_outputs: Set[str] = set()
    subgroup_set: Set[str] = set()
    group_set: Set[str] = set()
    owner_set: Set[str] = set()

    for op in operations.values():
        all_inputs.update(op.inputs)
        all_outputs.update(op.outputs)
        # Добавляем только непустые значения
        if op.subgroup and str(op.subgroup).strip() and str(op.subgroup).strip() != "nan":
            subgroup_set.add(op.subgroup)
        if op.group and str(op.group).strip() and str(op.group).strip() != "nan":
            group_set.add(op.group)
        if op.owner and str(op.owner).strip() and str(op.owner).strip() != "nan":
            owner_set.add(op.owner)

    external_inputs = all_inputs - all_outputs
    final_outputs = all_outputs - all_inputs

    # Создаем mapping от выхода к операции (для первого вхождения)
    output_to_operation: Dict[str, str] = {}
    for name, op in operations.items():
        for output in op.outputs:
            if output and output not in output_to_operation:
                output_to_operation[output] = name

    # Создаем mapping от входа к операциям, которые его используют
    input_to_operations: Dict[str, List[str]] = defaultdict(list)
    for name, op in operations.items():
        for inp in op.inputs:
            if inp:
                input_to_operations[inp].append(name)

    merge_points, split_points = analyze_process_patterns(operations, input_to_operations)

    # Анализ супер-критических операций
    critical_points: List[CriticalPoint] = []
    for op_name, op in operations.items():
        if not op.outputs:
            continue
        
        in_cnt = len(op.inputs)
        # Считаем максимальное использование среди всех выходов
        max_out_cnt = max([len(input_to_operations.get(out, [])) for out in op.outputs]) if op.outputs else 0
        
        if in_cnt >= choices.critical_min_inputs and max_out_cnt >= choices.critical_min_reuse:
            critical_points.append(
                CriticalPoint(operation=op_name,
                             inputs_count=in_cnt,
                             output_reuse=max_out_cnt)
            )

    analysis = ProcessAnalysis(
        merge_points=merge_points,
        split_points=split_points,
        critical_points=critical_points,
        external_inputs=external_inputs,
        final_outputs=final_outputs,
        operations_count=len(operations),
        subgroups_count=len(subgroup_set),
        groups_count=len(group_set),
        owners_count=len(owner_set)
    )

    return AnalysisData(
        external_inputs=external_inputs,
        final_outputs=final_outputs,
        output_to_operation=output_to_operation,
        input_to_operations=input_to_operations,
        analysis=analysis
    )

def get_process_complexity_score(operations: Dict[str, Operation], analysis_data: AnalysisData) -> int:
    """
    Рассчитать оценку сложности процесса от 1 до 10
    """
    analysis = analysis_data.analysis
    
    # Весовые коэффициенты
    weights = {
        'operations': 0.3,
        'merge_points': 0.2,
        'split_points': 0.2,
        'critical_points': 0.3
    }
    
    # Нормализация значений (максимальные ожидаемые значения)
    max_operations = 50
    max_merge = 10
    max_split = 10
    max_critical = 5
    
    # Расчет нормализованных показателей
    op_score = min(len(operations) / max_operations, 1.0)
    merge_score = min(len(analysis.merge_points) / max_merge, 1.0)
    split_score = min(len(analysis.split_points) / max_split, 1.0)
    critical_score = min(len(analysis.critical_points) / max_critical, 1.0)
    
    # Общий счет
    total_score = (
        op_score * weights['operations'] +
        merge_score * weights['merge_points'] +
        split_score * weights['split_points'] +
        critical_score * weights['critical_points']
    )
    
    return min(10, int(total_score * 10) + 1)