"""
Взаимодействие с пользователем
"""
import pandas as pd
from pathlib import Path
from typing import List
from utils import get_excel_files
from models import Choices
from config import CRITICAL_MIN_INPUTS, CRITICAL_MIN_REUSE

def get_file_path() -> Path:
    # Если программа запущена как exe, возвращаемся к GUI
    if getattr(sys, 'frozen', False):
        return None
    
    excel_files = get_excel_files()
    
    if not excel_files:
        print("\nВ текущей директории не найдено Excel-файлов (*.xlsx, *.xls)")
        while True:
            file_path = input("Введите полный путь к Excel-файлу: ").strip()
            if not file_path:
                print("Путь не может быть пустым.")
                continue
                
            path = Path(file_path)
            if path.exists():
                return path
            else:
                print(f"Файл '{file_path}' не существует. Попробуйте снова.")
    
    print("\nНайдены Excel-файлы в текущей директории:")
    for i, file_path in enumerate(excel_files, 1):
        print(f"{i}. {file_path}")
    print(f"{len(excel_files) + 1}. Указать другой файл")
    
    while True:
        try:
            choice = input(f"\nВыберите файл (1-{len(excel_files) + 1}): ").strip()
            if not choice:
                continue
                
            idx = int(choice)
            if 1 <= idx <= len(excel_files):
                return excel_files[idx - 1]
            elif idx == len(excel_files) + 1:
                file_path = input("Введите полный путь к Excel-файлу: ").strip()
                if not file_path:
                    print("Путь не может быть пустым.")
                    continue
                    
                path = Path(file_path)
                if path.exists():
                    return path
                else:
                    print(f"Файл '{file_path}' не существует.")
            else:
                print("Неверный выбор.")
        except ValueError:
            print("Введите число.")

def get_sheet_name(excel_path: Path) -> str:
    if getattr(sys, 'frozen', False):
        return "БП_1"
    
    try:
        excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
        sheet_names = excel_file.sheet_names
        
        if len(sheet_names) == 1:
            print(f"\nВ файле найден 1 лист: '{sheet_names[0]}'")
            return sheet_names[0]
        
        print(f"\nДоступные листы в файле '{excel_path}':")
        for i, sheet_name in enumerate(sheet_names, 1):
            print(f"{i}. {sheet_name}")
        
        while True:
            try:
                choice = input(f"Выберите лист (1-{len(sheet_names)}): ").strip()
                if not choice:
                    continue
                    
                idx = int(choice)
                if 1 <= idx <= len(sheet_names):
                    return sheet_names[idx - 1]
                else:
                    print("Неверный выбор.")
            except ValueError:
                print("Введите число.")
                
    except Exception as e:
        print(f"Ошибка чтения Excel-файла: {e}")
        return "БП_1"

def get_user_choices(df: pd.DataFrame) -> Choices:
    choices = Choices()
    
    print("\n" + "="*50)
    print("НАСТРОЙКИ ВИЗУАЛИЗАЦИИ")
    print("="*50)
    
    # Выбор формата вывода
    print("\nВыбор формата выходного файла:")
    print("1. Markdown с Mermaid (для документации)")
    print("2. HTML с Mermaid (панорамирование и масштабирование)")  
    print("3. Интерактивный HTML граф (vis-network)")
    print("4. HTML с SVG (ПРЕДПОЧТИТЕЛЬНЫЙ - улучшенная навигация)")
    
    while True:
        format_choice = input("Выберите формат (1-4): ").strip()
        if format_choice == "1":
            choices.output_format = "md"
            print("Выбран формат: Markdown с Mermaid")
            break
        elif format_choice == "2":
            choices.output_format = "html_mermaid"
            print("Выбран формат: HTML с Mermaid")
            break
        elif format_choice == "3":
            choices.output_format = "html_interactive"
            print("Выбран формат: Интерактивный HTML граф")
            break
        elif format_choice == "4":
            choices.output_format = "html_svg"
            print("Выбран формат: HTML с SVG - улучшенная навигация")
            print("  • 🖱️  Перетаскивание мышью")
            print("  • 🔍 Масштабирование колесом")
            print("  • 📍 Подсказки при наведении")
            print("  • 📊 Отображение координат")
            break
        else:
            print("Введите 1, 2, 3 или 4")
    
    # Для интерактивного HTML упрощаем настройки
    if choices.output_format == "html_interactive":
        choices.no_grouping = True
        choices.show_detailed = False
        print("\nДля интерактивного графа применены упрощенные настройки:")
        print("- Без группировки")
        print("- Без подробных описаний")
        return choices
    
    # Для SVG также упрощаем настройки
    if choices.output_format == "html_svg":
        choices.no_grouping = True
        choices.show_detailed = True  # В SVG текст переносится, можно показывать
        print("\nДля SVG диаграммы применены упрощенные настройки:")
        print("- Без группировки")
        print("- С подробными описаниями")
        return choices
    
    # Выбор группировки для Mermaid форматов
    candidates = []
    if "Группа" in df.columns:
        candidates.append("Группа")
    if "Владелец" in df.columns:
        candidates.append("Владелец")

    if candidates:
        print("\nНастройка группировки операций:")
        for i, candidate in enumerate(candidates, 1):
            print(f"{i}. Группировать по '{candidate}'")
        print(f"{len(candidates) + 1}. Без группировки")
        
        while True:
            try:
                choice = input(f"Выберите вариант (1-{len(candidates) + 1}): ").strip()
                if not choice:
                    continue
                    
                idx = int(choice)
                if 1 <= idx <= len(candidates):
                    choices.subgroup_column = candidates[idx - 1]
                    choices.no_grouping = False
                    print(f"Выбрана группировка по '{choices.subgroup_column}'")
                    break
                elif idx == len(candidates) + 1:
                    choices.subgroup_column = None
                    choices.no_grouping = True
                    print("Выбрано отображение без группировки")
                    break
                else:
                    print("Неверный выбор.")
            except ValueError:
                print("Введите число.")
    else:
        print("\nВ данных не найдено столбцов для группировки (Группа, Владелец)")
        choices.no_grouping = True
    
    # Подробное описание
    if "Подробное описание операции" in df.columns:
        print("\nОтображение подробного описания:")
        print("1. Да")
        print("2. Нет")
        
        while True:
            choice = input("Выберите вариант (1-2): ").strip()
            if choice == "1":
                choices.show_detailed = True
                print("Подробное описание будет отображаться")
                break
            elif choice == "2":
                choices.show_detailed = False
                print("Подробное описание не будет отображаться")
                break
            else:
                print("Введите 1 или 2")
    
    # Пороги для критических операций
    print("\nНастройка порогов для супер-критических операций:")
    print("(операции с большим количеством входов и выходов)")
    
    while True:
        try:
            min_inputs = input(f"Минимальное число входов (по умолчанию {CRITICAL_MIN_INPUTS}): ").strip()
            if min_inputs:
                choices.critical_min_inputs = int(min_inputs)
            else:
                choices.critical_min_inputs = CRITICAL_MIN_INPUTS
            
            min_reuse = input(f"Минимальное число использования выхода (по умолчанию {CRITICAL_MIN_REUSE}): ").strip()
            if min_reuse:
                choices.critical_min_reuse = int(min_reuse)
            else:
                choices.critical_min_reuse = CRITICAL_MIN_REUSE
                
            break
        except ValueError:
            print("Введите целые числа. Попробуйте снова.")
    
    print(f"\nПороги установлены: ≥{choices.critical_min_inputs} входов и ≥{choices.critical_min_reuse} использований выхода")
    
    return choices