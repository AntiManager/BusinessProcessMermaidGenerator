"""
Анализатор причинно-следственных связей для Causal Loop Diagrams
"""
import pandas as pd
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
from models import Operation, CausalLink, CausalAnalysis

def analyze_causal_links_from_operations(operations: Dict[str, Operation]) -> CausalAnalysis:
    """
    Автоматически строит CLD из существующих бизнес-процессов
    """
    links = []
    variables = set()
    
    # Собираем все переменные (входы и выходы)
    for op in operations.values():
        variables.update(op.inputs)
        variables.update(op.outputs)
    
    # Строим причинно-следственные связи
    for op_name, op in operations.items():
        # Каждая операция создает связи: входы -> выходы
        for input_var in op.inputs:
            for output_var in op.outputs:
                if input_var and output_var:  # Пропускаем пустые
                    links.append(CausalLink(
                        source=input_var,
                        target=output_var,
                        influence="+",  # По умолчанию положительное влияние
                        operation=op_name,
                        description=f"Создается операцией: {op_name}"
                    ))
    
    # Анализ петель обратной связи
    feedback_loops = find_feedback_loops(links)
    
    # Статистика
    statistics = {
        "variables": len(variables),
        "links": len(links),
        "positive_links": len([l for l in links if l.influence == "+"]),
        "negative_links": len([l for l in links if l.influence == "-"]),
        "loops": len(feedback_loops)
    }
    
    return CausalAnalysis(
        links=links,
        variables=variables,
        feedback_loops=feedback_loops,
        source_type="auto",
        statistics=statistics
    )

def analyze_causal_links_from_dataframe(df) -> CausalAnalysis:
    """
    Строит CLD из отдельной таблицы с CLD данными
    """
    links = []
    variables = set()
    
    required_columns = {"Источник", "Цель", "Знак влияния"}
    if not required_columns.issubset(set(df.columns)):
        raise ValueError(f"Отсутствуют обязательные колонки для CLD: {required_columns}")
    
    for _, row in df.iterrows():
        # Пропускаем пустые строки
        if pd.isna(row["Источник"]) or pd.isna(row["Цель"]):
            continue
            
        source = str(row["Источник"]).strip()
        target = str(row["Цель"]).strip()
        influence = str(row["Знак влияния"]).strip()
        
        # Валидация знака влияния
        if influence not in ["+", "-"]:
            influence = "+"  # Значение по умолчанию
        
        # Проверяем нужно ли включать связь
        include = True
        if "Учитывать в CLD" in df.columns and pd.notna(row["Учитывать в CLD"]):
            include_value = row["Учитывать в CLD"]
            if isinstance(include_value, bool):
                include = include_value
            elif isinstance(include_value, str):
                include = include_value.lower() in ['true', 'yes', '1', 'да']
            elif isinstance(include_value, (int, float)):
                include = bool(include_value)
        
        # Дополнительные поля
        strength = None
        if "Сила влияния" in df.columns and pd.notna(row["Сила влияния"]):
            strength = str(row["Сила влияния"])
            
        operation = None
        if "Операция" in df.columns and pd.notna(row["Операция"]):
            operation = str(row["Операция"])
            
        description = ""
        if "Описание" in df.columns and pd.notna(row["Описание"]):
            description = str(row["Описание"])
        
        links.append(CausalLink(
            source=source,
            target=target,
            influence=influence,
            strength=strength,
            operation=operation,
            include_in_cld=include,
            description=description
        ))
        
        variables.add(source)
        variables.add(target)
    
    feedback_loops = find_feedback_loops(links)
    
    # Статистика
    statistics = {
        "variables": len(variables),
        "links": len(links),
        "positive_links": len([l for l in links if l.influence == "+"]),
        "negative_links": len([l for l in links if l.influence == "-"]),
        "loops": len(feedback_loops)
    }
    
    return CausalAnalysis(
        links=links,
        variables=variables,
        feedback_loops=feedback_loops,
        source_type="manual",
        statistics=statistics
    )

def find_feedback_loops(links: List[CausalLink]) -> List[List[str]]:
    """
    Находит петли обратной связи в графе
    """
    # Построение графа
    graph = defaultdict(list)
    for link in links:
        if link.include_in_cld:
            graph[link.source].append(link.target)
    
    # Упрощенный поиск петель (можно улучшить алгоритмом Джонсона)
    loops = []
    visited = set()
    
    def dfs(node, path):
        if node in path:
            # Нашли петлю
            loop_start = path.index(node)
            loop = path[loop_start:]
            if len(loop) > 1:  # Исключаем самоссылки
                loops.append(loop)
            return
        
        if node in visited:
            return
            
        visited.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            dfs(neighbor, path)
            
        path.pop()
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return loops