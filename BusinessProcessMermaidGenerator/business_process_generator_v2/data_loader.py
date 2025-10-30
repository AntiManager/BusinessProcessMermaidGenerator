"""
Загрузка и обработка данных
"""
import pandas as pd
from typing import Dict, List
from collections import defaultdict
from models import Operation, Choices
from utils import clean_text, merge_strings

def load_and_validate_data(excel_path: str, sheet_name: str, required_columns: set) -> pd.DataFrame:
    """
    Загружает данные из Excel и проверяет обязательные колонки
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"Ошибка чтения Excel: {e}")
        return None

    missing = required_columns - set(df.columns)
    if missing:
        print(f"Отсутствуют обязательные колонки: {', '.join(missing)}")
        print(f"Найденные колонки: {', '.join(df.columns)}")
        return None

    return df

def collect_operations(df: pd.DataFrame, choices: Choices) -> Dict[str, Operation]:
    """
    Собирает операции из DataFrame с поддержкой множественных выходов
    """
    operations: Dict[str, Operation] = {}
    operation_rows: Dict[str, List[dict]] = defaultdict(list)

    # Собираем все строки по имени операции
    for _, row in df.iterrows():
        if pd.isna(row["Операция"]) and pd.isna(row["Выход"]):
            continue

        op_name = str(row["Операция"]).strip() if pd.notna(row["Операция"]) else f"Операция_{len(operations)}"
        operation_rows[op_name].append(row.to_dict())

    # Обрабатываем каждую операцию (возможно, из нескольких строк)
    for op_name, rows in operation_rows.items():
        # Объединяем данные из всех строк
        merged_inputs = []
        merged_outputs = []  # Список выходов
        merged_subgroup = None
        merged_group = ""
        merged_owner = ""
        merged_detailed = ""
        
        for row in rows:
            # Объединяем входы
            if pd.notna(row["Входы"]):
                input_text = str(row["Входы"])
                if input_text.strip() != "—":
                    new_inputs = [inp.strip() for inp in input_text.split(";") if inp.strip()]
                    merged_inputs.extend(new_inputs)
            
            # Объединяем выходы (собираем все выходы)
            if pd.notna(row["Выход"]):
                output_text = str(row["Выход"]).strip()
                if output_text and output_text != "—":
                    # Разделяем выходы по точке с запятой
                    new_outputs = [out.strip() for out in output_text.split(";") if out.strip()]
                    merged_outputs.extend(new_outputs)
            
            # Объединяем подгруппу (берем первую непустую)
            if not merged_subgroup and choices.subgroup_column and pd.notna(row.get(choices.subgroup_column)):
                merged_subgroup = str(row[choices.subgroup_column]).strip()
            
            # Объединяем группу (берем первую непустую)
            if not merged_group and "Группа" in df.columns and pd.notna(row.get("Группа")):
                merged_group = clean_text(row.get("Группа"))
            
            # Объединяем владельца (берем первого непустого)
            if not merged_owner and "Владелец" in df.columns and pd.notna(row.get("Владелец")):
                merged_owner = clean_text(row.get("Владелец"))
            
            # Объединяем описание (объединяем через точку с запятой)
            if "Подробное описание операции" in df.columns and pd.notna(row.get("Подробное описание операции")):
                new_detailed = clean_text(row.get("Подробное описание операции"))
                merged_detailed = merge_strings(merged_detailed, new_detailed, "; ")

        # Убираем дубликаты входов и выходов
        merged_inputs = list(set(merged_inputs))
        merged_outputs = list(set(merged_outputs))
        
        # Формируем текст узла
        node_text = f"{op_name}: {merged_detailed}" if choices.show_detailed and merged_detailed else op_name

        operations[op_name] = Operation(
            name=op_name,
            outputs=merged_outputs,  # Множественные выходы
            inputs=merged_inputs,
            subgroup=merged_subgroup,
            node_text=node_text,
            group=merged_group,
            owner=merged_owner,
            detailed=merged_detailed,
        )
    
    return operations