"""
Панель редактора Markdown с подсветкой синтаксиса
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QToolBar, 
                             QComboBox, QPushButton, QLabel)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont, QTextCharFormat, QSyntaxHighlighter, QColor
from PyQt6.QtCore import QRegularExpression

class MermaidHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlight_rules = []
        
        # Mermaid блоки
        mermaid_format = QTextCharFormat()
        mermaid_format.setForeground(QColor(86, 156, 214))
        self.highlight_rules.append(('```mermaid.*?```', mermaid_format))
        
        # Заголовки
        header_format = QTextCharFormat()
        header_format.setForeground(QColor(220, 220, 170))
        header_format.setFontWeight(75)
        self.highlight_rules.append(('^#{1,6}.*$', header_format))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlight_rules:
            expression = QRegularExpression(pattern)
            matches = expression.globalMatch(text)
            while matches.hasNext():
                match = matches.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class EditorPanel(QWidget):
    content_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = QToolBar()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        
        self.font_size = QComboBox()
        self.font_size.addItems(["12", "14", "16", "18"])
        self.font_size.setCurrentText("14")
        self.font_size.currentTextChanged.connect(self.change_font_size)
        
        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.save_file)
        
        toolbar.addWidget(QLabel("Тема:"))
        toolbar.addWidget(self.theme_combo)
        toolbar.addWidget(QLabel("Размер:"))
        toolbar.addWidget(self.font_size)
        toolbar.addWidget(save_btn)
        
        # Редактор
        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.on_text_changed)
        
        # Настраиваем шрифт
        font = QFont("Consolas", 14)
        self.editor.setFont(font)
        
        # Подсветка синтаксиса
        self.highlighter = MermaidHighlighter(self.editor.document())
        
        layout.addWidget(toolbar)
        layout.addWidget(self.editor)
    
    def on_text_changed(self):
        content = self.editor.toPlainText()
        self.content_changed.emit(content)
    
    def load_content(self, content):
        self.editor.setPlainText(content)
    
    def change_theme(self, theme):
        # Реализация смены темы редактора
        if theme == "Dark":
            self.editor.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    selection-background-color: #264f78;
                }
            """)
        else:
            self.editor.setStyleSheet("")
    
    def change_font_size(self, size):
        font = self.editor.font()
        font.setPointSize(int(size))
        self.editor.setFont(font)
    
    def save_file(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить Markdown", "", "Markdown Files (*.md)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                self.current_file = file_path
            except Exception as e:
                print(f"Ошибка сохранения: {e}")
    
    def update_settings(self, settings):
        """Обновляет настройки редактора"""
        pass