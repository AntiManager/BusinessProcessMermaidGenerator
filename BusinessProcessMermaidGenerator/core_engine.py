"""
Ядро приложения - бизнес-логика и координация процессов
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from models import Operation, Choices, AnalysisData, CausalAnalysis
from data_loader import load_and_validate_data, collect_operations, load_cld_data
from analysis import analyse_network
from cld_analyzer import analyze_causal_links_from_operations, analyze_causal_links_from_dataframe
from exporters import (
    export_mermaid, 
    export_html_mermaid, 
    export_interactive_html,
    export_cld_mermaid, 
    export_cld_interactive
)
from config import REQ_COLUMNS

logger = logging.getLogger(__name__)

class BusinessProcessEngine:
    """Движок бизнес-процессов - координирует всю логику приложения"""
    
    def __init__(self):
        self.operations: Optional[Dict[str, Operation]] = None
        self.analysis_data: Optional[AnalysisData] = None
        self.causal_analysis: Optional[CausalAnalysis] = None
    
    def load_business_processes(self, excel_path: Path, sheet_name: str, choices: Choices) -> bool:
        """Загрузка и валидация данных бизнес-процессов"""
        try:
            df = load_and_validate_data(excel_path, sheet_name, REQ_COLUMNS)
            if df is None:
                return False
            
            self.operations = collect_operations(df, choices)
            if not self.operations:
                logger.error("Не найдено операций для анализа")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки бизнес-процессов: {e}")
            return False
    
    def analyze_business_processes(self, choices: Choices) -> bool:
        """Анализ бизнес-процессов"""
        try:
            if not self.operations:
                logger.error("Операции не загружены")
                return False
                
            self.analysis_data = analyse_network(self.operations, choices)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка анализа бизнес-процессов: {e}")
            return False
    
    def load_causal_analysis(self, excel_path: Path, choices: Choices) -> bool:
        """Загрузка и анализ причинно-следственных связей"""
        try:
            if choices.cld_source_type == "manual" and choices.cld_sheet_name:
                # Загрузка из отдельной таблицы CLD
                cld_df = load_cld_data(excel_path, choices.cld_sheet_name)
                if cld_df is None:
                    return False
                self.causal_analysis = analyze_causal_links_from_dataframe(cld_df)
            else:
                # Автоматическое построение из бизнес-процессов
                if not self.operations:
                    logger.error("Бизнес-процессы не загружены для автоматического CLD")
                    return False
                self.causal_analysis = analyze_causal_links_from_operations(self.operations)
            
            return self.causal_analysis is not None
            
        except Exception as e:
            logger.error(f"Ошибка загрузки CLD анализа: {e}")
            return False
    
    def export_diagram(self, choices: Choices, output_base: str, available_columns: list = None, output_dir: Path = None) -> List[Path]:
        """Экспорт диаграммы в выбранный формат - ВОЗВРАЩАЕТ СПИСОК ФАЙЛОВ"""
        try:
            output_files = []
            
            # ИЗМЕНЕНИЕ: Упрощенная логика определения папки
            if output_dir is None:
                output_dir = choices.output_directory
            
            # Создаем папку если она не существует
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if choices.output_format in ["cld_mermaid", "cld_interactive"]:
                if not self.causal_analysis:
                    logger.error("CLD анализ не выполнен")
                    return []
                
                if choices.output_format == "cld_mermaid":
                    # Основной файл CLD + интерактивная версия
                    main_file = self._safe_export(export_cld_mermaid, self.causal_analysis, choices, output_base, output_dir)
                    if main_file:
                        output_files.append(main_file)
                    
                    # Автоматически создаем интерактивную версию с суффиксом _cld
                    interactive_base = f"{output_base}_cld"
                    interactive_file = self._safe_export(export_cld_interactive, self.causal_analysis, choices, interactive_base, output_dir)
                    if interactive_file:
                        output_files.append(interactive_file)
                    
                else:  # cld_interactive
                    interactive_file = self._safe_export(export_cld_interactive, self.causal_analysis, choices, output_base, output_dir)
                    if interactive_file:
                        output_files.append(interactive_file)
                    
            else:
                if not self.analysis_data or not self.operations:
                    logger.error("Анализ бизнес-процессов не выполнен")
                    return []
                
                if choices.output_format == "md":
                    # Основной Markdown + интерактивная версия
                    main_file = self._safe_export(export_mermaid, self.operations, self.analysis_data, choices, available_columns or [], output_base, output_dir)
                    if main_file:
                        output_files.append(main_file)
                    
                    # Автоматически создаем интерактивную версию с суффиксом _vis
                    interactive_base = f"{output_base}_vis"
                    interactive_file = self._safe_export(export_interactive_html, self.operations, self.analysis_data, choices, interactive_base, output_dir)
                    if interactive_file:
                        output_files.append(interactive_file)
                    
                elif choices.output_format == "html_mermaid":
                    # Основной HTML + интерактивная версия
                    main_file = self._safe_export(export_html_mermaid, self.operations, self.analysis_data, choices, available_columns or [], output_base, output_dir)
                    if main_file:
                        output_files.append(main_file)
                    
                    # Автоматически создаем интерактивную версию с суффиксом _vis
                    interactive_base = f"{output_base}_vis"
                    interactive_file = self._safe_export(export_interactive_html, self.operations, self.analysis_data, choices, interactive_base, output_dir)
                    if interactive_file:
                        output_files.append(interactive_file)
                    
                elif choices.output_format == "html_interactive":
                    interactive_file = self._safe_export(export_interactive_html, self.operations, self.analysis_data, choices, output_base, output_dir)
                    if interactive_file:
                        output_files.append(interactive_file)
                else:
                    logger.error(f"Неизвестный формат: {choices.output_format}")
                    return []
            
            return output_files
            
        except Exception as e:
            logger.error(f"Ошибка экспорта диаграммы: {e}")
            return []
    
    def _safe_export(self, export_func, *args, **kwargs) -> Optional[Path]:
        """Безопасный вызов экспортера с обработкой ошибок"""
        try:
            return export_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка в экспортере {export_func.__name__}: {e}")
            return None
    
    def get_statistics(self) -> Dict:
        """Получение статистики для отображения в UI"""
        stats = {
            "operations_count": 0,
            "external_inputs": 0,
            "final_outputs": 0,
            "critical_points": 0,
            "merge_points": 0,
            "split_points": 0
        }
        
        if self.analysis_data:
            analysis = self.analysis_data.analysis
            stats.update({
                "operations_count": analysis.operations_count,
                "external_inputs": len(analysis.external_inputs),
                "final_outputs": len(analysis.final_outputs),
                "critical_points": len(analysis.critical_points),
                "merge_points": len(analysis.merge_points),
                "split_points": len(analysis.split_points)
            })
        
        if self.causal_analysis:
            stats.update({
                "cld_variables": len(self.causal_analysis.variables),
                "cld_links": len([l for l in self.causal_analysis.links if l.include_in_cld]),
                "cld_loops": len(self.causal_analysis.feedback_loops)
            })
        
        return stats
    
    def reset(self):
        """Сброс состояния движка"""
        self.operations = None
        self.analysis_data = None
        self.causal_analysis = None

    # В core_engine.py добавляем метод

    def export_registries(self, output_base: str, available_columns: list = None, output_dir: Path = None) -> Path:
        """Экспорт полного комплекта реестров в Excel"""
        try:
            if output_dir is None:
                output_dir = Path(".")
                
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Проверяем наличие данных
            if not self.operations or not self.analysis_data:
                logger.error("Нет данных для экспорта реестров")
                return None
                
            from exporters.excel_exporter import export_complete_registry
            
            output_file = export_complete_registry(
                operations=self.operations,
                analysis_data=self.analysis_data,
                causal_analysis=self.causal_analysis,
                original_columns=available_columns or [],
                output_base=output_base,
                output_dir=output_dir
            )
            
            return output_file
            
        except Exception as e:
            logger.error(f"Ошибка экспорта реестров: {e}")
            return None