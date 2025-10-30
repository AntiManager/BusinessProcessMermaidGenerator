"""
Загрузка и валидация данных из Excel
"""
import pandas as pd
from typing import Tuple, Set
from .models import Operation, Choices

def load_and_validate_data(file_path: str, sheet_name: str, required_columns: Set[str]) -> Tuple[pd.DataFrame, str]:
    """
    Загружает и валидирует данные из Excel файла
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        
        # Проверяем обязательные колонки
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            return None, f"Отсутствуют обязательные колонки: {missing_columns}"
            
        return df, None
        
    except Exception as e:
        return None, f"Ошибка загрузки файла: {str(e)}"

def collect_operations(df: pd.DataFrame, choices: Choices) -> dict:
    """
    Собирает операции из DataFrame
    """
    operations = {}
    
    for _, row in df.iterrows():
        operation_name = str(row['Операция']).strip()
        if not operation_name:
            continue
            
        # Получаем входы и выходы
        inputs = []
        if 'Входы' in df.columns and pd.notna(row['Входы']):
            inputs = [inp.strip() for inp in str(row['Входы']).split(',') if inp.strip()]
            
        outputs = []
        if 'Выход' in df.columns and pd.notna(row['Выход']):
            outputs = [out.strip() for out in str(row['Выход']).split(',') if out.strip()]
        
        # Создаем операцию
        operation = Operation(
            name=operation_name,
            inputs=inputs,
            outputs=outputs,
            group=str(row['Группа']) if 'Группа' in df.columns and pd.notna(row.get('Группа')) else None,
            owner=str(row['Владелец']) if 'Владелец' in df.columns and pd.notna(row.get('Владелец')) else None,
            detailed=str(row['Подробное описание операции']) if 'Подробное описание операции' in df.columns and pd.notna(row.get('Подробное описание операции')) else None,
            subgroup=str(row[choices.subgroup_column]) if choices.subgroup_column and choices.subgroup_column in df.columns and pd.notna(row.get(choices.subgroup_column)) else None
        )
        
        operations[operation_name] = operation
    
    return operations