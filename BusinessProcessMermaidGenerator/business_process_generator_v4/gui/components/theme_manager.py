"""
Менеджер тем для приложения
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

class ThemeManager:
    def __init__(self):
        self.current_theme = "dark"
    
    def apply_theme(self, widget):
        """Применяет тему к виджету"""
        if self.current_theme == "dark":
            self.apply_dark_theme(widget)
        else:
            self.apply_light_theme(widget)
    
    def apply_dark_theme(self, widget):
        """Применяет темную тему"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        widget.setPalette(palette)
    
    def apply_light_theme(self, widget):
        """Применяет светлую тему"""
        widget.setPalette(QApplication.palette())
    
    def set_theme(self, theme_name):
        """Устанавливает тему по имени"""
        self.current_theme = theme_name.lower()