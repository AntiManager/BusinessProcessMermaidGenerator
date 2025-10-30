"""
Менеджер конфигурации для сохранения настроек между запусками
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from models import Choices
from config import CRITICAL_MIN_INPUTS, CRITICAL_MIN_REUSE

class ConfigManager:
    def __init__(self, config_file: str = "bp_config.json"):
        # Определяем путь для конфигурации
        if getattr(sys, 'frozen', False):
            # Если программа запущена как exe
            app_data_path = Path(os.getenv('APPDATA')) / 'BusinessProcessGenerator'
            app_data_path.mkdir(exist_ok=True)
            self.config_file = app_data_path / config_file
        else:
            # При разработке - в текущей директории
            self.config_file = Path(config_file)
        
        print(f"Config file path: {self.config_file}")  # Для отладки
    
    def load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из файла"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Объединяем с конфигурацией по умолчанию
                    config = {**self.default_config, **loaded_config}
                    print(f"Loaded config: {config}")  # Для отладки
                    return config
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
        return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]):
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def config_to_choices(self, config: Dict[str, Any]) -> Choices:
        """Преобразование конфигурации в объект Choices"""
        return Choices(
            subgroup_column=config['subgroup_column'] if not config['no_grouping'] else None,
            show_detailed=config['show_detailed'],
            critical_min_inputs=config['critical_min_inputs'],
            critical_min_reuse=config['critical_min_reuse'],
            no_grouping=config['no_grouping'],
            output_format=config['output_format']
        )
    
    def reset_config(self):
        """Сброс конфигурации к значениям по умолчанию"""
        if self.config_file.exists():
            self.config_file.unlink()