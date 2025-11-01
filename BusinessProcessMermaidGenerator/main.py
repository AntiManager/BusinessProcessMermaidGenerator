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
from cld_analyzer import analyze_causal_links_from_operations, analyze_causal_links_from_dataframe
from exporters.cld_mermaid_exporter import export_cld_mermaid
from exporters.cld_interactive_exporter import export_cld_interactive
from data_loader import load_cld_data

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
        
        # 🔥 ИСПРАВЛЕНИЕ: Обработка CLD форматов ДОЛЖНА БЫТЬ ПЕРВОЙ
        if choices.output_format in ["cld_mermaid", "cld_interactive"]:
            try:
                if choices.cld_source_type == "manual" and choices.cld_sheet_name:
                    # Загрузка из отдельной таблицы CLD
                    cld_df = load_cld_data(excel_path, choices.cld_sheet_name)
                    if cld_df is None:
                        return False
                    causal_analysis = analyze_causal_links_from_dataframe(cld_df)
                else:
                    # Автоматическое построение из бизнес-процессов
                    df = load_and_validate_data(excel_path, sheet_name, REQ_COLUMNS)
                    if df is None:
                        return False
                    operations = collect_operations(df, choices)
                    if not operations:
                        log.error("Не найдено ни одной операции для построения CLD")
                        return False
                    causal_analysis = analyze_causal_links_from_operations(operations)
                
                # Экспорт
                if choices.output_format == "cld_mermaid":
                    output_file = export_cld_mermaid(causal_analysis, choices, output_base)
                else:
                    output_file = export_cld_interactive(causal_analysis, choices, output_base)
                
                # Вывод статистики CLD
                print(f"Статистика CLD: {len(causal_analysis.variables)} переменных, "
                    f"{len([l for l in causal_analysis.links if l.include_in_cld])} связей")
                print(f"Петли обратной связи: {len(causal_analysis.feedback_loops)}")
                
                # АВТОМАТИЧЕСКОЕ ОТКРЫТИЕ В БРАУЗЕРЕ ДЛЯ CLD
                if output_file and output_file.exists():
                    print(f"\n📊 ОТКРОЙТЕ ФАЙЛ В БРАУЗЕРЕ ДЛЯ ПРОСМОТРА CLD ДИАГРАММЫ")
                    print(f"Файл: {output_file}")
                    
                    try:
                        webbrowser.open(f'file://{output_file.absolute()}')
                        print("✅ CLD диаграмма открыта в браузере")
                    except Exception as e:
                        print(f"⚠️ Не удалось открыть в браузере: {e}")
                
                return True
                
            except Exception as e:
                log.error(f"Ошибка при генерации CLD: {e}")
                return False

        # 🔥 ОБЫЧНЫЕ БИЗНЕС-ПРОЦЕССЫ (только если НЕ CLD формат)
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
        # УБРАЛ УСЛОВИЕ ДЛЯ html_svg
        else:  # для CLD форматов обработка уже выше
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
        "cld_mermaid": "md",
        "cld_interactive": "html"
    }
    return extensions.get(output_format, "html")

def main() -> None:
    """
    Главная функция - всегда запускает GUI
    """
    from gui_interface import run_gui
    run_gui()

if __name__ == "__main__":
    main()