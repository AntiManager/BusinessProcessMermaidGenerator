"""
Экспорт в Mermaid формат (Markdown и HTML) с улучшениями
"""
from typing import Dict, Set, List, Tuple
from pathlib import Path
from models import Operation, Choices, ProcessAnalysis, AnalysisData
from utils import safe_id, escape_text, _escape_multiline, create_markdown_table
from config import ENCODING, STYLES

def build_mermaid_md(
    operations: Dict[str, Operation],
    analysis_data: AnalysisData,
    choices: Choices,
) -> str:
    """
    Строит Mermaid код для Markdown
    """
    external_inputs = analysis_data.external_inputs
    final_outputs = analysis_data.final_outputs
    output_to_operation = analysis_data.output_to_operation
    input_to_operations = analysis_data.input_to_operations
    analysis = analysis_data.analysis
    
    lines = ["```mermaid", "graph LR"]
    for k, v in STYLES.items():
        lines.append(f"    classDef {k} {v};")

    critical_ops = {c.operation for c in analysis.critical_points}

    for inp in sorted(external_inputs):
        if inp:
            lines.append(f'    {safe_id(inp)}(["{escape_text(inp)}"]):::external')
    for out in sorted(final_outputs):
        if out:
            lines.append(f'    {safe_id(out)}(["{escape_text(out)}"]):::final')

    # Если отключена группировка или нет столбца для группировки
    if choices.no_grouping or not choices.subgroup_column:
        for name in sorted(operations):
            lines.append(_node_line_md(name, operations[name], input_to_operations, critical_ops))
    else:
        from collections import defaultdict
        subgroup_ops = defaultdict(list)
        for name, op in operations.items():
            # Добавляем только операции с указанной подгруппой
            if op.subgroup and str(op.subgroup).strip() and str(op.subgroup).strip() != "nan":
                subgroup_ops[op.subgroup].append(name)
            else:
                # Операции без подгруппы добавляем в отдельную категорию
                subgroup_ops[None].append(name)

        # Сначала добавляем подгруппы с определенными значениями
        for subgroup in sorted([sg for sg in subgroup_ops.keys() if sg is not None]):
            # ИСПРАВЛЕНИЕ: Добавляем префикс к идентификатору группы чтобы избежать циклов
            sg_id = "group_" + safe_id(subgroup)
            lines.append(f'    subgraph {sg_id}["{escape_text(subgroup)}"]')
            for name in sorted(subgroup_ops[subgroup]):
                lines.append(_node_line_md(name, operations[name], input_to_operations, critical_ops))
            lines.append("    end")
        
        # Затем добавляем операции без подгруппы (если есть)
        if None in subgroup_ops and subgroup_ops[None]:
            for name in sorted(subgroup_ops[None]):
                lines.append(_node_line_md(name, operations[name], input_to_operations, critical_ops))

    added = set()
    for name, op in operations.items():
        src_id = safe_id(name)
        
        # Обрабатываем ВСЕ выходы операции
        for output in op.outputs:
            if output and output in final_outputs:
                key = (src_id, output, safe_id(output))
                if key not in added:
                    added.add(key)
                    lines.append(f'    {src_id}-- "{escape_text(output)}" -->{safe_id(output)}')
            
            # Связываем выходы с операциями, которые их используют
            if output in input_to_operations:
                for target_op in input_to_operations[output]:
                    key = (src_id, output, safe_id(target_op))
                    if key not in added:
                        added.add(key)
                        lines.append(f'    {src_id}-- "{escape_text(output)}" -->{safe_id(target_op)}')
        
        # Обрабатываем входы из внешних источников
        for inp in op.inputs:
            if not inp:
                continue
            if inp in external_inputs:
                key = (safe_id(inp), inp, src_id)
                if key not in added:
                    added.add(key)
                    lines.append(f'    {safe_id(inp)}-- "{escape_text(inp)}" -->{src_id}')

    lines.append("```")
    return "\n".join(lines)

def _node_line_md(name: str, op: Operation,
               input_to_operations: Dict[str, List[str]],
               critical_ops: Set[str]) -> str:
    node_id = safe_id(name)
    if name in critical_ops:
        style = ":::critical"
    else:
        is_merge = len(op.inputs) > 1
        # Проверяем разветвление по всем выходам
        is_split = any(len(input_to_operations.get(out, [])) > 1 for out in op.outputs)
        style = (
            ":::merge" if is_merge and is_split else
            ":::merge" if is_merge else
            ":::split" if is_split else
            ""
        )
    return f'    {node_id}["{escape_text(op.node_text)}"]{style}'

def build_mermaid_html(
    operations: Dict[str, Operation],
    analysis_data: AnalysisData,
    choices: Choices,
) -> str:
    """
    Генерирует Mermaid код для вставки в HTML с улучшениями
    """
    external_inputs = analysis_data.external_inputs
    final_outputs = analysis_data.final_outputs
    output_to_operation = analysis_data.output_to_operation
    input_to_operations = analysis_data.input_to_operations
    analysis = analysis_data.analysis
    
    lines = ["graph LR"]
    for k, v in STYLES.items():
        lines.append(f"    classDef {k} {v};")

    critical_ops = {c.operation for c in analysis.critical_points}

    for inp in sorted(external_inputs):
        if inp:
            lines.append(f'    {safe_id(inp)}(["{escape_text(inp)}"]):::external')
    for out in sorted(final_outputs):
        if out:
            lines.append(f'    {safe_id(out)}(["{escape_text(out)}"]):::final')

    # Группировка для HTML Mermaid
    from collections import defaultdict
    subgroup_ops = defaultdict(list)
    for name, op in operations.items():
        # Добавляем только операции с указанной подгруппой
        if op.subgroup and str(op.subgroup).strip() and str(op.subgroup).strip() != "nan":
            subgroup_ops[op.subgroup].append(name)
        else:
            # Операции без подгруппы добавляем в отдельную категорию
            subgroup_ops[None].append(name)

    if choices.subgroup_column and not choices.no_grouping:
        # Сначала добавляем подгруппы с определенными значениями
        for subgroup in sorted([sg for sg in subgroup_ops.keys() if sg is not None]):
            # ИСПРАВЛЕНИЕ: Добавляем префикс к идентификатору группы чтобы избежать циклов
            sg_id = "group_" + safe_id(subgroup)
            lines.append(f'    subgraph {sg_id}["{escape_text(subgroup)}"]')
            for name in sorted(subgroup_ops[subgroup]):
                lines.append(_node_line_html(name, operations[name], input_to_operations, critical_ops))
            lines.append("    end")
        
        # Затем добавляем операции без подгруппы (если есть)
        if None in subgroup_ops and subgroup_ops[None]:
            for name in sorted(subgroup_ops[None]):
                lines.append(_node_line_html(name, operations[name], input_to_operations, critical_ops))
    else:
        for name in sorted(operations):
            lines.append(_node_line_html(name, operations[name], input_to_operations, critical_ops))

    added = set()
    for name, op in operations.items():
        src_id = safe_id(name)
        
        # Обрабатываем ВСЕ выходы операции
        for output in op.outputs:
            if output and output in final_outputs:
                key = (src_id, output, safe_id(output))
                if key not in added:
                    added.add(key)
                    lines.append(f'    {src_id}-- "{escape_text(output)}" -->{safe_id(output)}')
            
            # Связываем выходы с операциями, которые их используют
            if output in input_to_operations:
                for target_op in input_to_operations[output]:
                    key = (src_id, output, safe_id(target_op))
                    if key not in added:
                        added.add(key)
                        lines.append(f'    {src_id}-- "{escape_text(output)}" -->{safe_id(target_op)}')
        
        # Обрабатываем входы из внешних источников
        for inp in op.inputs:
            if not inp:
                continue
            if inp in external_inputs:
                key = (safe_id(inp), inp, src_id)
                if key not in added:
                    added.add(key)
                    lines.append(f'    {safe_id(inp)}-- "{escape_text(inp)}" -->{src_id}')

    return "\n".join(lines)

def _node_line_html(name: str, op: Operation,
                   input_to_operations: Dict[str, List[str]],
                   critical_ops: Set[str]) -> str:
    node_id = safe_id(name)
    if name in critical_ops:
        style = ":::critical"
    else:
        is_merge = len(op.inputs) > 1
        is_split = any(len(input_to_operations.get(out, [])) > 1 for out in op.outputs)
        style = (
            ":::merge" if is_merge and is_split else
            ":::merge" if is_merge else
            ":::split" if is_split else
            ""
        )
    return f'    {node_id}["{escape_text(op.node_text)}"]{style}'

def _build_io_registry(
    external_inputs: Set[str],
    final_outputs: Set[str],
    output_to_operation: Dict[str, str],
    input_to_operations: Dict[str, List[str]],
) -> List[Dict[str, str]]:
    """
    Строит реестр входов/выходов
    """
    rows = []
    items = external_inputs | final_outputs | set(output_to_operation) | set(input_to_operations)
    for item in sorted(items):
        if not item:
            continue
        src = "ВНЕШНИЙ ВХОД" if item in external_inputs else output_to_operation.get(item, "-")
        tgts = input_to_operations.get(item, [])
        if item in final_outputs and not tgts:
            tgts = ["КОНЕЧНЫЙ ВЫХОД"]
        rows.append({
            "Вход/Выход": item,
            "Исходная операция": src,
            "Последующие операции": ", ".join(tgts) if tgts else "-",
        })
    return rows

def _build_op_registry(operations: Dict[str, Operation],
                       input_to_operations: Dict[str, List[str]],
                       critical_ops: Set[str]) -> List[Dict[str, str]]:
    """
    Строит реестр операций
    """
    rows = []
    for name, op in operations.items():
        is_merge = len(op.inputs) > 1
        is_split = any(len(input_to_operations.get(out, [])) > 1 for out in op.outputs)
        node_type = (
            "Супер-критичная" if name in critical_ops else
            "Слияние+Разветвление" if is_merge and is_split else
            "Слияние" if is_merge else
            "Разветвление" if is_split else
            "Обычный"
        )
        rows.append({
            "Операция": name,
            "Группа": op.group,
            "Владелец": op.owner,
            "Входы": ", ".join(op.inputs) if op.inputs else "-",
            "Выход": ", ".join(op.outputs) if op.outputs else "-",
            "Тип узла": node_type,
            "Подробное описание": op.detailed,
        })
    return rows

def export_mermaid(operations: Dict[str, Operation], analysis_data: AnalysisData, 
                  choices: Choices, available_columns: List[str], output_base: str = None) -> Path:
    """
    Экспортирует диаграмму в Markdown с Mermaid - ВОЗВРАЩАЕТ Path
    """
    # Используем переданное имя файла или значение по умолчанию
    if output_base is None:
        output_base = "business_process_diagram"
    
    output_file = Path(f"{output_base}.md")

    # Генерация Mermaid кода
    mermaid_code = build_mermaid_md(operations, analysis_data, choices)

    # Подготовка данных для таблиц
    io_rows = _build_io_registry(
        analysis_data.external_inputs,
        analysis_data.final_outputs,
        analysis_data.output_to_operation,
        analysis_data.input_to_operations
    )
    
    critical_ops = {c.operation for c in analysis_data.analysis.critical_points}
    op_rows = _build_op_registry(operations, analysis_data.input_to_operations, critical_ops)

    # Определение доступных колонок
    available_cols = {
        'group': 'Группа' in available_columns,
        'owner': 'Владелец' in available_columns,
        'detailed_desc': 'Подробное описание операции' in available_columns
    }

    # Сборка Markdown контента
    md_parts = [
        f"# Диаграмма бизнес-процесса\n\n",
        f"## Визуальное представление процесса\n\n",
        mermaid_code,
        f"\n\n## Дополнительные представления\n\n",
        f"### 📊 Интерактивная версия\n\n",
        f"Для более удобного исследования диаграммы доступна [интерактивная версия]({output_base}_vis.html).\n\n",
        f"**Возможности интерактивной версии:**\n",
        f"- 🔍 Динамическое масштабирование и панорамирование\n",
        f"- 🎯 Поиск и фильтрация элементов\n", 
        f"- 📊 Интерактивная статистика и аналитика\n",
        f"- 🖱️  Простое перетаскивание узлов\n\n",
        f"## Анализ узлов слияния, разветвления и супер-критичных точек\n\n",
        f"### Супер-критические операции (одновременно ≥ "
        f"{choices.critical_min_inputs} входов и выход используется ≥ {choices.critical_min_reuse} раз):\n",
    ]
    
    if analysis_data.analysis.critical_points:
        for cp in sorted(analysis_data.analysis.critical_points, key=lambda x: (x.inputs_count, x.output_reuse), reverse=True):
            md_parts.append(f"- **{cp.operation}**: {cp.inputs_count} входов, выход идёт в {cp.output_reuse} операций\n")
    else:
        md_parts.append("- Таких операций нет\n")

    md_parts.extend([
        "\n### Критические точки слияния:\n",
    ])
    if analysis_data.analysis.merge_points:
        for point in sorted(analysis_data.analysis.merge_points, key=lambda x: x.input_count, reverse=True):
            md_parts.append(f"- **{point.operation}**: {point.input_count} входов\n")
    else:
        md_parts.append("- Нет точек слияния\n")

    md_parts.extend([
        "\n### Критические точки разветвления:\n",
    ])
    if analysis_data.analysis.split_points:
        for point in sorted(analysis_data.analysis.split_points, key=lambda x: x.target_count, reverse=True):
            md_parts.append(f"- **{point.output}** (из {point.source_operation}): идёт в {point.target_count} операций\n")
    else:
        md_parts.append("- Нет точек разветвления\n")

    md_parts.extend([
        "\n## Реестр входов/выходов\n\n",
        create_markdown_table(["Вход/Выход", "Исходная операция", "Последующие операции"], io_rows),
        "\n\n## Реестр операций\n\n",
    ])

    table_headers = ["Операция"]
    if available_cols['group']:
        table_headers.append("Группа")
    if available_cols['owner']:
        table_headers.append("Владелец")
    table_headers.extend(["Входы", "Выход", "Тип узла"])
    if available_cols['detailed_desc']:
        table_headers.append("Подробное описание")
    md_parts.append(create_markdown_table(table_headers, op_rows))

    md_parts.extend([
        f"\n\n## Статистика процесса\n\n",
        f"- **Всего операций**: {analysis_data.analysis.operations_count}\n",
    ])
    if choices.subgroup_column and not choices.no_grouping:
        md_parts.append(f"- **{choices.subgroup_column} для диаграммы**: {analysis_data.analysis.subgroups_count}\n")
    if available_cols['group'] and choices.subgroup_column != 'Группа':
        md_parts.append(f"- **Группы в данных**: {analysis_data.analysis.groups_count}\n")
    if available_cols['owner'] and choices.subgroup_column != 'Владелец':
        md_parts.append(f"- **Владельцы в данных**: {analysis_data.analysis.owners_count}\n")

    md_parts.extend([
        f"- **Внешние входы**: {len(analysis_data.analysis.external_inputs)}\n",
        f"- **Конечные выходы**: {len(analysis_data.analysis.final_outputs)}\n",
        f"- **Операций слияния**: {len(analysis_data.analysis.merge_points)}\n",
        f"- **Операций разветвления**: {len(analysis_data.analysis.split_points)}\n",
        f"- **Супер-критических операций**: {len(analysis_data.analysis.critical_points)}\n",
        f"\n\n## Легенда\n\n",
        f"- **Желтые овалы** – внешние входы\n",
        f"- **Красные овалы** – конечные выходы\n",
        f"- **Оранжевые прямоугольники** – операции слияния\n",
        f"- **Фиолетовые прямоугольники** – операции разветвления\n",
        f"- **Пульсирующие красные прямоугольники** – супер-критические операции\n",
        f"- **Обычные прямоугольники** – стандартные операции\n",
    ])
    if choices.subgroup_column and not choices.no_grouping:
        md_parts.append(f"- **Группы на диаграмме** – зоны ответственности {choices.subgroup_column.lower()}\n")
    if choices.show_detailed:
        md_parts.append(f"- **Текст узлов** – содержит подробное описание операций\n")

    # Сохранение файла
    output_file.write_text("".join(md_parts), encoding=ENCODING)

    print(f"\n" + "="*60)
    print("✓ MARKDOWN-ДИАГРАММА УСПЕШНО СОЗДАНА!")
    print("="*60)
    print(f"Файл: {output_file}")
    print(f"Статистика: {analysis_data.analysis.operations_count} операций")
    
    return output_file