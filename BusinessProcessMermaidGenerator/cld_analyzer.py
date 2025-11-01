"""
Анализатор причинно-следственных связей для Causal Loop Diagrams
с улучшенной валидацией и обработкой ошибок
"""
import pandas as pd
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from models import Operation, CausalLink, CausalAnalysis

class CLDValidationError(Exception):
    """Ошибка валидации CLD данных"""
    pass

def analyze_causal_links_from_operations(operations: Dict[str, Operation]) -> CausalAnalysis:
    """
    Автоматически строит CLD из существующих бизнес-процессов
    с улучшенной обработкой ошибок
    """
    try:
        links = []
        variables = set()
        
        # Валидация входных данных
        if not operations:
            raise CLDValidationError("Нет операций для анализа")
        
        # Собираем все переменные (входы и выходы)
        for op in operations.values():
            variables.update(filter(None, op.inputs))
            variables.update(filter(None, op.outputs))
        
        # Проверяем что есть переменные для анализа
        if not variables:
            raise CLDValidationError("Не найдено переменных для построения CLD")
        
        # Строим причинно-следственные связи
        for op_name, op in operations.items():
            # Каждая операция создает связи: входы -> выходы
            for input_var in filter(None, op.inputs):
                for output_var in filter(None, op.outputs):
                    links.append(CausalLink(
                        source=input_var,
                        target=output_var,
                        influence="+",  # По умолчанию положительное влияние
                        operation=op_name,
                        description=f"Создается операцией: {op_name}",
                        include_in_cld=True
                    ))
        
        # Анализ петель обратной связи
        feedback_loops = find_feedback_loops(links)
        
        # Статистика
        statistics = _calculate_cld_statistics(links, variables, feedback_loops)
        
        return CausalAnalysis(
            links=links,
            variables=variables,
            feedback_loops=feedback_loops,
            source_type="auto",
            statistics=statistics
        )
        
    except Exception as e:
        if isinstance(e, CLDValidationError):
            raise
        raise CLDValidationError(f"Ошибка анализа CLD из операций: {e}")

def analyze_causal_links_from_dataframe(df: pd.DataFrame) -> CausalAnalysis:
    """
    Строит CLD из отдельной таблицы с CLD данными
    с улучшенной валидацией
    """
    try:
        links = []
        variables = set()
        
        required_columns = {"Источник", "Цель", "Знак влияния"}
        if not required_columns.issubset(set(df.columns)):
            raise CLDValidationError(f"Отсутствуют обязательные колонки для CLD: {required_columns}")
        
        # Проверяем наличие данных
        if df.empty:
            raise CLDValidationError("CLD таблица не содержит данных")
        
        valid_rows = 0
        
        for index, row in df.iterrows():
            # Пропускаем пустые строки
            if pd.isna(row["Источник"]) or pd.isna(row["Цель"]):
                continue
                
            source = str(row["Источник"]).strip()
            target = str(row["Цель"]).strip()
            
            # Проверяем что переменные не пустые
            if not source or not target:
                continue
            
            # Валидация и нормализация знака влияния
            influence = _validate_influence_sign(row["Знак влияния"])
            
            # Определяем включение связи в CLD
            include_in_cld = _determine_inclusion(row)
            
            # Дополнительные поля
            strength = _extract_optional_field(row, "Сила влияния")
            operation = _extract_optional_field(row, "Операция")
            description = _extract_optional_field(row, "Описание", default="")
            
            links.append(CausalLink(
                source=source,
                target=target,
                influence=influence,
                strength=strength,
                operation=operation,
                include_in_cld=include_in_cld,
                description=description
            ))
            
            variables.add(source)
            variables.add(target)
            valid_rows += 1
        
        # Проверяем что есть валидные связи
        if valid_rows == 0:
            raise CLDValidationError("Не найдено валидных причинно-следственных связей")
        
        feedback_loops = find_feedback_loops(links)
        statistics = _calculate_cld_statistics(links, variables, feedback_loops)
        
        return CausalAnalysis(
            links=links,
            variables=variables,
            feedback_loops=feedback_loops,
            source_type="manual",
            statistics=statistics
        )
        
    except Exception as e:
        if isinstance(e, CLDValidationError):
            raise
        raise CLDValidationError(f"Ошибка анализа CLD из DataFrame: {e}")

def _validate_influence_sign(influence_value) -> str:
    """Валидация и нормализация знака влияния"""
    if pd.isna(influence_value):
        return "+"  # Значение по умолчанию
    
    influence_str = str(influence_value).strip()
    
    if influence_str in ["+", "положительное", "positive", "pos"]:
        return "+"
    elif influence_str in ["-", "отрицательное", "negative", "neg"]:
        return "-"
    else:
        # Логируем предупреждение, но используем значение по умолчанию
        print(f"Предупреждение: неизвестный знак влияния '{influence_str}', используется '+'")
        return "+"

def _determine_inclusion(row: pd.Series) -> bool:
    """Определение включения связи в CLD"""
    if "Учитывать в CLD" not in row or pd.isna(row["Учитывать в CLD"]):
        return True
    
    include_value = row["Учитывать в CLD"]
    
    if isinstance(include_value, bool):
        return include_value
    elif isinstance(include_value, str):
        return include_value.lower() in ['true', 'yes', '1', 'да', 'включить']
    elif isinstance(include_value, (int, float)):
        return bool(include_value)
    
    return True

def _extract_optional_field(row: pd.Series, field_name: str, default: any = None) -> any:
    """Извлечение опционального поля"""
    if field_name in row and pd.notna(row[field_name]):
        return str(row[field_name])
    return default

def _calculate_cld_statistics(links: List[CausalLink], variables: Set[str], feedback_loops: List[List[str]]) -> Dict:
    """Расчет статистики CLD"""
    included_links = [l for l in links if l.include_in_cld]
    
    return {
        "variables": len(variables),
        "links": len(included_links),
        "positive_links": len([l for l in included_links if l.influence == "+"]),
        "negative_links": len([l for l in included_links if l.influence == "-"]),
        "loops": len(feedback_loops),
        "total_rows_processed": len(links)
    }

def find_feedback_loops(links: List[CausalLink]) -> List[List[str]]:
    """
    Находит петли обратной связи в графе
    с улучшенным алгоритмом
    """
    try:
        # Строим граф только из включенных связей
        graph = defaultdict(list)
        for link in links:
            if link.include_in_cld:
                graph[link.source].append(link.target)
        
        # Упрощенный поиск петель (для больших графов можно использовать алгоритм Джонсона)
        loops = []
        visited = set()
        
        def dfs(node: str, path: List[str]) -> None:
            if node in path:
                # Нашли петлю
                loop_start = path.index(node)
                loop = path[loop_start:]
                if len(loop) > 1:  # Исключаем самоссылки
                    # Нормализуем петлю (начинаем с наименьшего элемента для устранения дубликатов)
                    min_index = loop.index(min(loop))
                    normalized_loop = loop[min_index:] + loop[:min_index]
                    if normalized_loop not in loops:
                        loops.append(normalized_loop)
                return
            
            if node in visited:
                return
                
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path.copy())
                
            path.pop()
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return loops
        
    except Exception as e:
        print(f"Ошибка поиска петель обратной связи: {e}")
        return []