"""
Панель настройки генерации диаграмм
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
                             QLineEdit, QPushButton, QComboBox, QCheckBox,
                             QSpinBox, QRadioButton, QButtonGroup, QFileDialog,
                             QHBoxLayout, QLabel)
from PyQt6.QtCore import pyqtSignal, QThread
from pathlib import Path
import pandas as pd
from core.data_loader import load_and_validate_data, collect_operations
from core.analysis import analyse_network
from core.models import Choices
from exporters.mermaid_exporter import generate_mermaid_full_markdown

class GenerationThread(QThread):
    finished = pyqtSignal(str, str)  # file_path, content
    
    def __init__(self, excel_path, sheet_name, choices):
        super().__init__()
        self.excel_path = excel_path
        self.sheet_name = sheet_name
        self.choices = choices
    
    def run(self):
        try:
            # Выполняем генерацию
            df, error = load_and_validate_data(self.excel_path, self.sheet_name, {"Операция", "Входы", "Выход"})
            if error:
                print(f"Ошибка валидации: {error}")
                return
                
            operations = collect_operations(df, self.choices)
            analysis_data = analyse_network(operations, self.choices)
            
            # Генерируем Markdown контент
            content = generate_mermaid_full_markdown(
                operations, analysis_data, self.choices, df.columns.tolist()
            )
            
            # Сохраняем во временный файл
            output_path = Path("temp_diagram.md")
            output_path.write_text(content, encoding='utf-8')
            
            self.finished.emit(str(output_path), content)
            
        except Exception as e:
            print(f"Ошибка генерации: {e}")

class SetupPanel(QWidget):
    generation_complete = pyqtSignal(str, str)
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.excel_path = ""
        self.sheet_names = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Группа источника данных
        source_group = QGroupBox("📁 Источник данных")
        source_layout = QFormLayout(source_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Выберите файл Excel...")
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.browse_file)
        
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(browse_btn)
        
        source_layout.addRow("Файл Excel:", file_layout)
        
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)
        source_layout.addRow("Лист:", self.sheet_combo)
        
        # Группа параметров
        params_group = QGroupBox("⚡ Параметры генерации")
        params_layout = QFormLayout(params_group)
        
        # Формат вывода
        self.format_group = QButtonGroup()
        format_layout = QHBoxLayout()
        
        formats = [
            ("Mermaid", "md", True),
            ("HTML", "html", False),
            ("SVG", "svg", False)
        ]
        
        for text, value, checked in formats:
            rb = QRadioButton(text)
            rb.setProperty('format', value)
            rb.setChecked(checked)
            self.format_group.addButton(rb)
            format_layout.addWidget(rb)
        
        params_layout.addRow("Формат:", format_layout)
        
        # Дополнительные опции
        self.grouping_cb = QCheckBox("Группировать по подгруппам")
        params_layout.addRow("", self.grouping_cb)
        
        self.detailed_cb = QCheckBox("Показать детальное описание")
        params_layout.addRow("", self.detailed_cb)
        
        # Пороги
        thresholds_layout = QHBoxLayout()
        self.min_inputs = QSpinBox()
        self.min_inputs.setRange(1, 10)
        self.min_inputs.setValue(3)
        thresholds_layout.addWidget(self.min_inputs)
        thresholds_layout.addWidget(QLabel("мин. входов"))
        
        self.min_reuse = QSpinBox()
        self.min_reuse.setRange(1, 10)
        self.min_reuse.setValue(3)
        thresholds_layout.addWidget(self.min_reuse)
        thresholds_layout.addWidget(QLabel("мин. использований"))
        
        params_layout.addRow("Критические точки:", thresholds_layout)
        
        # Кнопка генерации
        self.generate_btn = QPushButton("🎯 Сгенерировать диаграмму")
        self.generate_btn.clicked.connect(self.generate_diagram)
        self.generate_btn.setEnabled(False)
        
        layout.addWidget(source_group)
        layout.addWidget(params_group)
        layout.addWidget(self.generate_btn)
        layout.addStretch()
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите Excel файл", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.excel_path = file_path
            self.file_path_edit.setText(file_path)
            self.load_sheets()
            self.generate_btn.setEnabled(True)
    
    def load_sheets(self):
        try:
            excel_file = pd.ExcelFile(self.excel_path, engine="openpyxl")
            self.sheet_names = excel_file.sheet_names
            self.sheet_combo.clear()
            self.sheet_combo.addItems(self.sheet_names)
        except Exception as e:
            print(f"Ошибка загрузки листов: {e}")
    
    def on_sheet_changed(self, sheet_name):
        """Обработчик изменения выбранного листа"""
        pass
    
    def generate_diagram(self):
        if not self.excel_path or not self.sheet_combo.currentText():
            return
        
        # Создаем объект Choices
        choices = Choices(
            subgroup_column="Подгруппа" if self.grouping_cb.isChecked() else None,
            show_detailed=self.detailed_cb.isChecked(),
            critical_min_inputs=self.min_inputs.value(),
            critical_min_reuse=self.min_reuse.value(),
            output_format=self.get_selected_format()
        )
        
        # Запускаем в отдельном потоке
        self.thread = GenerationThread(
            self.excel_path, 
            self.sheet_combo.currentText(), 
            choices
        )
        self.thread.finished.connect(self.generation_complete.emit)
        self.thread.start()
    
    def get_selected_format(self):
        for button in self.format_group.buttons():
            if button.isChecked():
                return button.property('format')
        return 'md'