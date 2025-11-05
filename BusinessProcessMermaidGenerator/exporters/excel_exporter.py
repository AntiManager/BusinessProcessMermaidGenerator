# exporters/excel_exporter.py
"""
Экспорт реестров в Excel формат для дальнейшего анализа и переиспользования
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set
from models import Operation, AnalysisData, CausalAnalysis, CausalLink
from utils import safe_id
from config import ENCODING

def export_operations_registry(operations: Dict[str, Operation], 
                             original_columns: List[str],
                             output_file: Path) -> None:
    """
    Экспорт реестра операций со всеми исходными данными
    """
    data = []
    
    for op_name, op in operations.items():
        row = {
            'Операция': op_name,
            'Входы': '; '.join(op.inputs) if op.inputs else '',
            'Выходы': '; '.join(op.outputs) if op.outputs else '',
            'Группа': op.group or '',
            'Владелец': op.owner or '',
            'Подгруппа': op.subgroup or '',
            'Подробное_описание': op.detailed or '',
            'Текст_узла': op.node_text or '',
        }
        
        # Добавляем дополнительные поля если они есть в операции
        if hasattr(op, 'additional_data'):
            for key, value in op.additional_data.items():
                row[key] = value
                
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Сохраняем в Excel
    with pd.ExcelWriter(output_file, mode='w', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Реестр_операций', index=False)

def export_io_registry(analysis_data: AnalysisData, output_file: Path) -> None:
    """
    Экспорт реестра входов/выходов с категориями
    """
    external_inputs = analysis_data.external_inputs
    final_outputs = analysis_data.final_outputs
    output_to_operation = analysis_data.output_to_operation
    input_to_operations = analysis_data.input_to_operations
    
    data = []
    items = external_inputs | final_outputs | set(output_to_operation.keys()) | set(input_to_operations.keys())
    
    for item in sorted(items):
        if not item:
            continue
            
        # Определяем тип элемента
        if item in external_inputs:
            element_type = "Внешний вход"
        elif item in final_outputs:
            element_type = "Конечный выход"
        else:
            element_type = "Промежуточный"
            
        # Определяем источник
        source = "Внешний" if item in external_inputs else output_to_operation.get(item, "")
        
        # Определяем потребителей
        consumers = input_to_operations.get(item, [])
        
        row = {
            'Элемент': item,
            'Тип': element_type,
            'Источник': source,
            'Потребители': '; '.join(consumers) if consumers else '',
            'Категория_данных': '',  # Для ручного заполнения: материальные, информационные, финансовые
            'Примечания': ''
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Добавляем в существующий файл
    with pd.ExcelWriter(output_file, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name='Реестр_входов_выходов', index=False)

def export_cld_registry(causal_analysis: CausalAnalysis, output_file: Path) -> None:
    """
    Экспорт реестра причинно-следственных связей
    """
    # Экспорт переменных
    variables_data = []
    for variable in sorted(causal_analysis.variables):
        variables_data.append({
            'Переменная': variable,
            'Тип_переменной': '',  # Для ручного заполнения
            'Категория': '',       # Для ручного заполнения
            'Описание': ''
        })
    
    # Экспорт связей
    links_data = []
    for link in causal_analysis.links:
        if link.include_in_cld:
            links_data.append({
                'Источник': link.source,
                'Цель': link.target,
                'Влияние': link.influence,
                'Сила_влияния': link.strength or '',
                'Операция': link.operation or '',
                'Описание': link.description or '',
                'Учитывать_в_CLD': 'Да' if link.include_in_cld else 'Нет',
                'Категория_связи': ''  # Для ручного заполнения
            })
    
    variables_df = pd.DataFrame(variables_data)
    links_df = pd.DataFrame(links_data)
    
    # Добавляем в существующий файл
    with pd.ExcelWriter(output_file, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
        variables_df.to_excel(writer, sheet_name='CLD_Переменные', index=False)
        links_df.to_excel(writer, sheet_name='CLD_Связи', index=False)
        
        # Экспорт петель обратной связи если есть
        if causal_analysis.feedback_loops:
            loops_data = []
            for i, loop in enumerate(causal_analysis.feedback_loops, 1):
                loops_data.append({
                    'Петля': f'Петля_{i}',
                    'Цикл': ' → '.join(loop),
                    'Тип_петли': '',  # Для ручного заполнения
                    'Описание': ''
                })
            loops_df = pd.DataFrame(loops_data)
            loops_df.to_excel(writer, sheet_name='CLD_Петли', index=False)

def export_complete_registry(operations: Dict[str, Operation],
                           analysis_data: AnalysisData,
                           causal_analysis: CausalAnalysis,
                           original_columns: List[str],
                           output_base: str,
                           output_dir: Path = None) -> Path:
    """
    Полный экспорт всех реестров в один Excel файл
    """
    if output_dir is None:
        output_dir = Path(".")
    
    output_file = output_dir / f"{output_base}_реестры.xlsx"
    
    # Экспорт всех реестров
    export_operations_registry(operations, original_columns, output_file)
    export_io_registry(analysis_data, output_file)
    
    if causal_analysis:
        export_cld_registry(causal_analysis, output_file)
    
    print(f"\n" + "="*60)
    print("✓ ПОЛНЫЙ КОМПЛЕКТ РЕЕСТРОВ ЭКСПОРТИРОВАН В EXCEL!")
    print("="*60)
    print(f"Файл: {output_file}")
    print("📊 СОДЕРЖАНИЕ:")
    print("   • 📋 Реестр операций (для переиспользования как исходник)")
    print("   • 🔄 Реестр входов/выходов (для категоризации данных)")
    print("   • 🔗 Реестр CLD переменных и связей")
    print("   • 🔄 Петли обратной связи (если обнаружены)")
    print("\n🎯 ВОЗМОЖНОСТИ ПЕРЕИСПОЛЬЗОВАНИЯ:")
    print("   • Реестр операций → исходник для новых диаграмм")
    print("   • Реестр входов/выходов → расширенный анализ потоков")
    print("   • Реестр CLD → доработка и дополнение связей")
    
    return output_file