"""
Конфигурация приложения и константы с улучшенной структурой
"""
from typing import Dict, Any

# Стили для визуализации
STYLES: Dict[str, str] = {
    "external": "fill:yellow,stroke:#333,stroke-width:2px;",
    "final": "fill:red,stroke:#333,stroke-width:2px,color:white;",
    "merge": "fill:orange,stroke:#333,stroke-width:2px;",
    "split": "fill:purple,stroke:#333,stroke-width:2px,color:white;",
    "critical": "fill:#ff4444,stroke:#000,stroke-width:3px,color:white,stroke-dasharray:5 5;",
}

# Пороговые значения для анализа
CRITICAL_MIN_INPUTS: int = 3
CRITICAL_MIN_REUSE: int = 3

# Обязательные колонки
REQ_COLUMNS: set = {"Операция", "Входы", "Выход"}
CLD_REQUIRED_COLUMNS: set = {"Источник", "Цель", "Знак влияния"}

# НОВЫЕ КОЛОНКИ ДЛЯ АНАЛИТИКИ ПОТОКА ЦЕННОСТИ
VALUE_STREAM_COLUMNS: set = {
    "Время операции (мин)",
    "Количество циклов", 
    "Период цикла",
    "Количество персонала",
    "Стоимость часа работы (руб)"
}

# Кодировка файлов
ENCODING: str = "utf-8"

# Настройки производительности
MAX_OPERATIONS_FOR_COMPLEX_ANALYSIS: int = 1000
MAX_CLD_VARIABLES: int = 500

# Настройки валидации
MIN_OPERATIONS_FOR_ANALYSIS: int = 1
MAX_FILENAME_LENGTH: int = 255

# Допустимые периоды циклов
VALID_CYCLE_PERIODS: list = ["смена", "день", "неделя", "месяц", "квартал", "год"]

def validate_config() -> None:
    """Валидация конфигурации при запуске"""
    if CRITICAL_MIN_INPUTS < 1:
        raise ValueError("CRITICAL_MIN_INPUTS должен быть >= 1")
    
    if CRITICAL_MIN_REUSE < 1:
        raise ValueError("CRITICAL_MIN_REUSE должен быть >= 1")
    
    if not REQ_COLUMNS:
        raise ValueError("REQ_COLUMNS не может быть пустым")
    
    # Проверяем допустимые периоды циклов
    for period in VALID_CYCLE_PERIODS:
        if not isinstance(period, str):
            raise ValueError("Все периоды циклов должны быть строками")

# Валидация при импорте модуля
validate_config()