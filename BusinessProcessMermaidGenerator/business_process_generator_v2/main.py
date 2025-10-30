"""
Главный файл приложения - ГЕНЕРАТОР ДИАГРАММ БИЗНЕС-ПРОЦЕССОВ
"""
import logging
import webbrowser
from pathlib import Path
from config import REQ_COLUMNS
from models import Choices
from data_loader import load_and_validate_data, collect_operations
from analysis import analyse_network
from exporters.mermaid_exporter import export_mermaid
from exporters.html_exporter import export_html_mermaid
from exporters.interactive_exporter import export_interactive_html
from exporters.svg_exporter import export_svg_html

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

def run_with_gui(excel_path: Path, sheet_name: str, choices: Choices, output_base: str) -> bool:
    """
    Запуск генерации диаграммы с параметрами из GUI
    """
    try:
        print(f"✓ Выбран файл: {excel_path}")
        print(f"✓ Выбран лист: {sheet_name}")
        print(f"✓ Выходной файл: {output_base}")
        
        # Загрузка и валидация данных
        df = load_and_validate_data(excel_path, sheet_name, REQ_COLUMNS)
        if df is None:
            return False
        
        # Сбор операций
        operations = collect_operations(df, choices)
        if not operations:
            log.error("Не найдено ни одной операции для построения диаграммы")
            return False

        # Анализ сети
        analysis_data = analyse_network(operations, choices)

        # Экспорт в выбранный формат с указанием имени файла
        if choices.output_format == "md":
            export_mermaid(operations, analysis_data, choices, df.columns.tolist(), output_base)
        elif choices.output_format == "html_mermaid":
            export_html_mermaid(operations, analysis_data, choices, df.columns.tolist(), output_base)
        elif choices.output_format == "html_interactive":
            export_interactive_html(operations, analysis_data, choices, output_base)
        elif choices.output_format == "html_svg":
            export_svg_html(operations, analysis_data, choices, df.columns.tolist(), output_base)
        else:  # html_interactive
            export_interactive_html(operations, analysis_data, choices, output_base)

        # Вывод общей статистики
        analysis = analysis_data.analysis
        print(f"Источник: {excel_path} (лист: {sheet_name})")
        print(f"Статистика: {analysis.operations_count} операций")
        print(f"Анализ: {len(analysis.merge_points)} узлов слияния, {len(analysis.split_points)} узлов разветвления")
        print(f"Супер-критических операций: {len(analysis.critical_points)}")
        
        output_file = Path(f"{output_base}.{get_file_extension(choices.output_format)}")
        if output_file.exists():
            print(f"\n📊 ОТКРОЙТЕ ФАЙЛ В БРАУЗЕРЕ ДЛЯ ПРОСМОТРА ДИАГРАММЫ")
            print(f"Файл: {output_file}")
            
            # Автоматическое открытие в браузере
            try:
                webbrowser.open(f'file://{output_file.absolute()}')
                print("Диаграмма открыта в браузере")
            except Exception as e:
                print(f"Не удалось открыть в браузере: {e}")
        
        return True
        
    except Exception as e:
        log.error(f"Ошибка при генерации диаграммы: {e}")
        return False

def get_file_extension(output_format: str) -> str:
    """Получение расширения файла по формату вывода"""
    extensions = {
        "md": "md",
        "html_mermaid": "html", 
        "html_interactive": "html",
        "html_svg": "html"
    }
    return extensions.get(output_format, "html")

def main() -> None:
    """
    Главная функция (консольная версия)
    """
    print("="*60)
    print("ГЕНЕРАТОР ДИАГРАММ БИЗНЕС-ПРОЦЕССОВ - ФИНАЛЬНАЯ ВЕРСИЯ")
    print("="*60)
    
    # Проверяем наличие сохраненной конфигурации
    config_file = Path("bp_config.json")
    if config_file.exists():
        use_saved = input("Найдены сохраненные настройки. Использовать их? (y/n): ").strip().lower()
        if use_saved == 'y':
            from gui_interface import run_gui
            run_gui()
            return
    
    # Запуск консольной версии
    from user_input import get_file_path, get_sheet_name, get_user_choices
    
    # 1. Выбор файла
    excel_path = get_file_path()
    print(f"\n✓ Выбран файл: {excel_path}")
    
    # 2. Выбор листа
    sheet_name = get_sheet_name(excel_path)
    print(f"✓ Выбран лист: {sheet_name}")
    
    # 3. Загрузка и валидация данных
    df = load_and_validate_data(excel_path, sheet_name, REQ_COLUMNS)
    if df is None:
        return
    
    # 4. Настройка визуализации
    choices = get_user_choices(df)
    
    # 5. Имя выходного файла (для консольной версии оставляем запрос)
    default_output = "business_process_diagram"
    output_name = input(f"Введите базовое имя для выходного файла (по умолчанию {default_output}): ").strip()
    output_base = output_name if output_name else default_output
    
    # 6. Сбор операций
    operations = collect_operations(df, choices)
    if not operations:
        log.error("Не найдено ни одной операции для построения диаграммы")
        return

    # 7. Анализ сети
    analysis_data = analyse_network(operations, choices)

    # 8. Экспорт в выбранный формат
    if choices.output_format == "md":
        export_mermaid(operations, analysis_data, choices, df.columns.tolist(), output_base)
    elif choices.output_format == "html_mermaid":
        export_html_mermaid(operations, analysis_data, choices, df.columns.tolist(), output_base)
    elif choices.output_format == "html_interactive":
        export_interactive_html(operations, analysis_data, choices, output_base)
    elif choices.output_format == "html_svg":
        export_svg_html(operations, analysis_data, choices, df.columns.tolist(), output_base)
    else:  # По умолчанию интерактивный HTML
        export_interactive_html(operations, analysis_data, choices, output_base)

    # 9. Вывод общей статистики
    analysis = analysis_data.analysis
    print(f"Источник: {excel_path} (лист: {sheet_name})")
    print(f"Статистика: {analysis.operations_count} операций")
    
    output_file = Path(f"{output_base}.{get_file_extension(choices.output_format)}")
    if output_file.exists():
        print(f"\n📊 ОТКРОЙТЕ ФАЙЛ В БРАУЗЕРЕ ДЛЯ ПРОСМОТРА ДИАГРАММЫ")
        print(f"Файл: {output_file}")
        
        # Автоматическое открытие в браузере
        try:
            webbrowser.open(f'file://{output_file.absolute()}')
            print("Диаграмма открыта в браузере")
        except Exception as e:
            print(f"Не удалось открыть в браузере: {e}")

if __name__ == "__main__":
    import sys
    
    # Проверяем, запущено ли приложение как exe
    if getattr(sys, 'frozen', False):
        # В собранной версии всегда запускаем GUI
        from gui_interface import run_gui
        run_gui()
    else:
        # В режиме разработки проверяем аргументы
        if len(sys.argv) > 1 and sys.argv[1] == "--gui":
            from gui_interface import run_gui
            run_gui()
        else:
            main()