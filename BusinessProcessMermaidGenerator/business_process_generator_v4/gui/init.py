"""
Современный графический интерфейс на PyQt6
"""

from .main_window import MainWindow
from .setup_panel import SetupPanel
from .editor_panel import EditorPanel
from .preview_panel import PreviewPanel

__all__ = ['MainWindow', 'SetupPanel', 'EditorPanel', 'PreviewPanel']