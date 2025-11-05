"""
Загрузка и обработка данных с улучшенной валидацией
"""
import pandas as pd
from typing import Dict, List, Optional
from collections import defaultdict
from models import Operation, Choices
from utils import clean_text, merge_strings

class DataValidationError(Exception):
    """Ошибка валидации данных"""
    pass

def load_and_validate_data(excel_path: str, sheet_name: str, required_columns: set) -> Optional[pd.DataFrame]:
    """
    Загружает данные из Excel и проверяет обязательные колонки
    с улучшенной обработкой ошибок
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        raise DataValidationError(f"Ошибка чтения Excel файла: {e}")

    # Проверяем наличие обязательных колонок
    missing = required_columns - set(df.columns)
    if missing:
        raise DataValidationError(
            f"Отсутствуют обязательные колонки: {', '.join(missing)}\n"
            f"Найденные колонки: {', '.join(df.columns)}"
        )

    # Проверяем что есть данные для обработки
    if df.empty:
        raise DataValidationError("Файл Excel не содержит данных")

    # Проверяем наличие хотя бы одной непустой строки
    has_data = False
    for _, row in df.iterrows():
        if pd.notna(row.get("Операция")) or pd.notna(row.get("Выход")):
            has_data = True
            break
    
    if not has_data:
        raise DataValidationError("Файл не содержит данных операций")

    return df

def collect_operations(df: pd.DataFrame, choices: Choices) -> Dict[str, Operation]:
    """
    Собирает операции из DataFrame с поддержкой множественных выходов
    и улучшенной обработкой данных
    """
    operations: Dict[str, Operation] = {}
    operation_rows: Dict[str, List[dict]] = defaultdict(list)

    # Собираем все строки по имени операции
    for _, row in df.iterrows():
        # Пропускаем полностью пустые строки
        if pd.isna(row.get("Операция")) and pd.isna(row.get("Выход")):
            continue

        # Безопасное извлечение имени операции
        op_name = _extract_operation_name(row, len(operations))
        operation_rows[op_name].append(row.to_dict())

    # Обрабатываем каждую операцию
    for op_name, rows in operation_rows.items():
        operation = _merge_operation_data(op_name, rows, df.columns, choices)
        if operation:
            operations[op_name] = operation
    
    return operations

def _extract_operation_name(row: pd.Series, fallback_index: int) -> str:
    """Безопасное извлечение имени операции"""
    operation_value = row.get("Операция")
    
    if pd.isna(operation_value) or not str(operation_value).strip():
        return f"Операция_{fallback_index}"
    
    return str(operation_value).strip()

def _merge_operation_data(op_name: str, rows: List[dict], available_columns: list, choices: Choices) -> Optional[Operation]:
    """Объединение данных операции из нескольких строк с сохранением всех полей"""
    try:
        merged_inputs = []
        merged_outputs = []
        merged_subgroup = None
        merged_group = ""
        merged_owner = ""
        merged_detailed = ""
        
        for row in rows:
            # Объединяем входы
            merged_inputs.extend(_extract_inputs(row))
            
            # Объединяем выходы
            merged_outputs.extend(_extract_outputs(row))
            
            # Объединяем метаданные
            merged_subgroup = _extract_subgroup(row, choices, merged_subgroup)
            merged_group = _extract_group(row, merged_group)
            merged_owner = _extract_owner(row, merged_owner)
            merged_detailed = _extract_detailed(row, merged_detailed)
        
        # Убираем дубликаты и пустые значения
        merged_inputs = list(set(filter(None, merged_inputs)))
        merged_outputs = list(set(filter(None, merged_outputs)))
        
        # Формируем текст узла
        node_text = _build_node_text(op_name, merged_detailed, choices)
        
        additional_data = {}
        for col in available_columns:
            if col not in ['Операция', 'Входы', 'Выход', 'Группа', 'Владелец', 'Подробное описание операции']:
                values = []
                for row in rows:
                    if col in row and pd.notna(row[col]) and str(row[col]).strip():
                        values.append(str(row[col]).strip())
                if values:
                    additional_data[col] = '; '.join(set(values))
        
        operation = Operation(
            name=op_name,
            outputs=merged_outputs,
            inputs=merged_inputs,
            subgroup=merged_subgroup,
            node_text=node_text,
            group=merged_group,
            owner=merged_owner,
            detailed=merged_detailed,
        )
        
        # Добавляем дополнительные данные
        operation.additional_data = additional_data
        
        return operation
        
    except Exception as e:
        print(f"Ошибка обработки операции '{op_name}': {e}")
        return None

def _extract_inputs(row: dict) -> List[str]:
    """Извлечение входов из строки"""
    inputs = []
    if pd.notna(row.get("Входы")):
        input_text = str(row["Входы"])
        if input_text.strip() and input_text.strip() != "—":
            new_inputs = [inp.strip() for inp in input_text.split(";") if inp.strip()]
            inputs.extend(new_inputs)
    return inputs

def _extract_outputs(row: dict) -> List[str]:
    """Извлечение выходов из строки"""
    outputs = []
    if pd.notna(row.get("Выход")):
        output_text = str(row["Выход"]).strip()
        if output_text and output_text != "—":
            new_outputs = [out.strip() for out in output_text.split(";") if out.strip()]
            outputs.extend(new_outputs)
    return outputs

def _extract_subgroup(row: dict, choices: Choices, current_value: str) -> str:
    """Извлечение подгруппы"""
    if not current_value and choices.subgroup_column and pd.notna(row.get(choices.subgroup_column)):
        subgroup_value = str(row[choices.subgroup_column]).strip()
        if subgroup_value and subgroup_value != "—" and subgroup_value != "nan":
            return subgroup_value
    return current_value

def _extract_group(row: dict, current_value: str) -> str:
    """Извлечение группы"""
    if not current_value and "Группа" in row and pd.notna(row.get("Группа")):
        group_value = clean_text(row.get("Группа"))
        if group_value and group_value != "—" and group_value != "nan":
            return group_value
    return current_value

def _extract_owner(row: dict, current_value: str) -> str:
    """Извлечение владельца"""
    if not current_value and "Владелец" in row and pd.notna(row.get("Владелец")):
        owner_value = clean_text(row.get("Владелец"))
        if owner_value and owner_value != "—" and owner_value != "nan":
            return owner_value
    return current_value

def _extract_detailed(row: dict, current_value: str) -> str:
    """Извлечение подробного описания"""
    if "Подробное описание операции" in row and pd.notna(row.get("Подробное описание операции")):
        new_detailed = clean_text(row.get("Подробное описание операции"))
        return merge_strings(current_value, new_detailed, "; ")
    return current_value

def _build_node_text(op_name: str, detailed: str, choices: Choices) -> str:
    """Построение текста узла"""
    if choices.show_detailed and detailed:
        return f"{op_name}: {detailed}"
    return op_name

def load_cld_data(excel_path: str, sheet_name: str) -> Optional[pd.DataFrame]:
    """
    Загружает данные для CLD из отдельного листа Excel
    с улучшенной валидацией
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
        
        # Проверяем обязательные колонки
        required_columns = {"Источник", "Цель", "Знак влияния"}
        missing = required_columns - set(df.columns)
        if missing:
            raise DataValidationError(f"Отсутствуют обязательные колонки для CLD: {missing}")
        
        # Проверяем наличие данных
        if df.empty:
            raise DataValidationError("CLD лист не содержит данных")
            
        return df
        
    except Exception as e:
        if isinstance(e, DataValidationError):
            raise
        raise DataValidationError(f"Ошибка загрузки CLD данных: {e}")