"""
API ядра приложения - общие функции для устранения циклических импортов
"""
import logging
import webbrowser
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from core_engine import BusinessProcessEngine
from models import Choices

log = logging.getLogger(__name__)

class DiagramGenerator:
    """Координатор генерации диаграмм - заменяет God Object из старого main.py"""
    
    def __init__(self):
        self.engine = BusinessProcessEngine()
    
    def generate_diagram(self, excel_path: Path, sheet_name: str, choices: Choices, 
                        output_base: str, available_columns: list = None) -> Tuple[bool, str, List[Path]]:
        """
        Генерация диаграммы с улучшенной обработкой ошибок
        Возвращает (успех, сообщение, список_созданных_файлов)
        """
        try:
            log.info(f"Начало генерации: {excel_path}, лист: {sheet_name}")
            
            # Валидация входных параметров
            validation_error = self._validate_inputs(excel_path, sheet_name, output_base, choices)
            if validation_error:
                return False, validation_error, []
            
            # Определяем тип процесса
            is_cld = choices.output_format in ["cld_mermaid", "cld_interactive"]
            
            # Загрузка данных
            if is_cld and choices.cld_source_type == "auto":
                # Для автоматического CLD нужны бизнес-процессы
                if not self.engine.load_business_processes(excel_path, sheet_name, choices):
                    return False, "Не удалось загрузить бизнес-процессы для автоматического CLD", []
            elif not is_cld:
                # Обычные бизнес-процессы
                if not self.engine.load_business_processes(excel_path, sheet_name, choices):
                    return False, "Не удалось загрузить бизнес-процессы", []
            
            # Анализ данных
            if is_cld:
                if not self.engine.load_causal_analysis(excel_path, choices):
                    return False, "Не удалось проанализировать причинно-следственные связи", []
            else:
                if not self.engine.analyze_business_processes(choices):
                    return False, "Не удалось проанализировать бизнес-процессы", []
            
            # Экспорт диаграммы
            output_files = self.engine.export_diagram(choices, output_base, available_columns)
            if not output_files:
                return False, "Не удалось создать файлы диаграммы", []
            
            # Фильтруем None значения
            valid_files = [f for f in output_files if f is not None and isinstance(f, Path)]
            
            if not valid_files:
                return False, "Не удалось создать ни одного файла диаграммы", []
            
            # Статистика и результат
            stats = self.engine.get_statistics()
            success_message = self._build_success_message(valid_files, stats, is_cld)
            
            # Автоматическое открытие ОСНОВНОГО файла в браузере
            main_file = self._get_main_file_to_open(valid_files, choices)
            if main_file:
                self._open_in_browser(main_file)
            
            return True, success_message, valid_files
            
        except Exception as e:
            error_msg = f"Критическая ошибка при генерации диаграммы: {str(e)}"
            log.error(error_msg, exc_info=True)
            return False, error_msg, []
    
    def _validate_inputs(self, excel_path: Path, sheet_name: str, output_base: str, choices: Choices) -> Optional[str]:
        """Валидация входных параметров"""
        if not excel_path or not excel_path.exists():
            return f"Файл не существует: {excel_path}"
        
        if not sheet_name:
            return "Не выбран лист из файла Excel"
        
        if not output_base or not output_base.strip():
            return "Введите имя для выходного файла"
        
        # Валидация для CLD форматов
        if choices.output_format in ["cld_mermaid", "cld_interactive"]:
            if choices.cld_source_type == "manual" and not choices.cld_sheet_name:
                return ("Для ручного источника CLD данных выберите лист с CLD данными.\n\n"
                       "Если вы хотите использовать автоматическое построение CLD из бизнес-процессов, "
                       "измените 'Источник данных' на 'Авто из бизнес-процессов'.")
        
        return None
    
    def _get_main_file_to_open(self, output_files: List[Path], choices: Choices) -> Optional[Path]:
        """Определяет какой файл открывать в браузере по умолчанию"""
        if not output_files:
            return None
        
        # Для интерактивных форматов открываем интерактивный файл
        if choices.output_format in ["html_interactive", "cld_interactive"]:
            return output_files[0]
        
        # Для остальных форматов ищем основной файл (без суффиксов _vis, _cld)
        main_files = [f for f in output_files if f.stem and not f.stem.endswith(('_vis', '_cld'))]
        
        if main_files:
            return main_files[0]
        
        # Если не нашли основной, берем первый
        return output_files[0]
    
    def _build_success_message(self, output_files: List[Path], stats: Dict, is_cld: bool) -> str:
        """Построение сообщения об успехе"""
        if not output_files:
            return "Не удалось создать файлы диаграммы"
        
        main_file = next((f for f in output_files if f.stem and not f.stem.endswith(('_vis', '_cld'))), output_files[0])
        interactive_files = [f for f in output_files if f.stem and f.stem.endswith(('_vis', '_cld'))]
        
        if is_cld:
            message = (f"✅ CAUSAL LOOP DIAGRAM УСПЕШНО СОЗДАН!\n\n"
                      f"📊 Статистика:\n"
                      f"   • Переменных: {stats.get('cld_variables', 0)}\n"
                      f"   • Связей: {stats.get('cld_links', 0)}\n"
                      f"   • Петель обратной связи: {stats.get('cld_loops', 0)}\n\n"
                      f"📁 Созданные файлы:\n"
                      f"   • Основной: {main_file.name}\n")
            
            if interactive_files:
                message += f"   • Интерактивный: {interactive_files[0].name}\n"
            
            message += f"\nОсновная диаграмма автоматически откроется в браузере."
            
        else:
            message = (f"✅ ДИАГРАММА БИЗНЕС-ПРОЦЕССОВ УСПЕШНО СОЗДАНА!\n\n"
                      f"📊 Статистика:\n"
                      f"   • Операций: {stats.get('operations_count', 0)}\n"
                      f"   • Внешних входов: {stats.get('external_inputs', 0)}\n"
                      f"   • Конечных выходов: {stats.get('final_outputs', 0)}\n"
                      f"   • Критических операций: {stats.get('critical_points', 0)}\n\n"
                      f"📁 Созданные файлы:\n"
                      f"   • Основной: {main_file.name}\n")
            
            if interactive_files:
                message += f"   • Интерактивный: {interactive_files[0].name}\n"
            
            message += f"\nОсновная диаграмма автоматически откроется в браузере."
        
        return message
    
    def _open_in_browser(self, output_file: Path):
        """Автоматическое открытие в браузере"""
        try:
            if output_file and output_file.exists():
                webbrowser.open(f'file://{output_file.absolute()}')
                log.info(f"Диаграмма открыта в браузере: {output_file}")
            else:
                log.warning(f"Файл для открытия не существует: {output_file}")
        except Exception as e:
            log.warning(f"Не удалось открыть в браузере: {e}")

def run_with_gui(excel_path: Path, sheet_name: str, choices: Choices, output_base: str) -> bool:
    """
    Запуск генерации диаграммы с параметрами из GUI
    Теперь без циклических импортов!
    """
    generator = DiagramGenerator()
    success, message, output_files = generator.generate_diagram(excel_path, sheet_name, choices, output_base)
    
    # Сообщение будет отображено в GUI
    log.info(message)
    
    # Дополнительная информация о созданных файлах
    if success and output_files:
        log.info(f"Создано файлов: {len(output_files)}")
        for file in output_files:
            if file and isinstance(file, Path):
                log.info(f"  - {file.name}")
    
    return success

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