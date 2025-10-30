"""
Главное окно приложения - Modern IDE для бизнес-процессов
"""
import sys
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QSplitter, QTabWidget, QStatusBar, QLabel)
from PyQt6.QtCore import Qt, QSettings
from .setup_panel import SetupPanel
from .editor_panel import EditorPanel
from .preview_panel import PreviewPanel
from .components.theme_manager import ThemeManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("BusinessProcessGenerator", "v4.0")
        self.theme_manager = ThemeManager()
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        self.setWindowTitle("Business Process Generator v4.0 - IDE")
        self.setGeometry(100, 100, 1600, 900)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Создаем сплиттер для редактора и предпросмотра
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - настройки и редактор
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Вкладки для левой панели
        left_tabs = QTabWidget()
        
        # Вкладка настройки генерации
        self.setup_panel = SetupPanel()
        left_tabs.addTab(self.setup_panel, "⚙️ Генерация")
        
        # Вкладка редактора
        self.editor_panel = EditorPanel()
        left_tabs.addTab(self.editor_panel, "📝 Редактор")
        
        left_layout.addWidget(left_tabs)
        
        # Правая панель - предпросмотр
        self.preview_panel = PreviewPanel()
        
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(self.preview_panel)
        main_splitter.setSizes([800, 800])
        
        layout.addWidget(main_splitter)
        
        # Статус бар
        self.statusBar().showMessage("Готов к работе")
        
        # Подключаем сигналы
        self.connect_signals()
        
        # Применяем тему
        self.theme_manager.apply_theme(self)
    
    def connect_signals(self):
        """Подключает взаимодействие между компонентами"""
        self.setup_panel.generation_complete.connect(self.on_generation_complete)
        self.editor_panel.content_changed.connect(self.preview_panel.update_preview)
        self.setup_panel.settings_changed.connect(self.editor_panel.update_settings)
    
    def on_generation_complete(self, file_path, content):
        """Обрабатывает завершение генерации"""
        self.editor_panel.load_content(content)
        self.preview_panel.update_preview(content)
        self.statusBar().showMessage(f"Диаграмма создана: {file_path}")
    
    def load_settings(self):
        """Загружает настройки окна"""
        geometry = self.settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
    
    def closeEvent(self, event):
        """Сохраняет настройки при закрытии"""
        self.settings.setValue("window_geometry", self.saveGeometry())
        super().closeEvent(event)