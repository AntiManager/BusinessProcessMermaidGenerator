"""
Панель предпросмотра Markdown с рендерингом Mermaid
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl
from utils.mermaid_renderer import MermaidRenderer

class PreviewPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.mermaid_renderer = MermaidRenderer()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        # Вкладка предпросмотра
        self.preview_view = QWebEngineView()
        self.preview_view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, True
        )
        self.tabs.addTab(self.preview_view, "👀 Предпросмотр")
        
        # Вкладка исходного HTML
        self.source_view = QWebEngineView()
        self.tabs.addTab(self.source_view, "📄 Исходник")
        
        layout.addWidget(self.tabs)
    
    def update_preview(self, markdown_content):
        """Обновляет предпросмотр с рендерингом Mermaid"""
        if not markdown_content:
            return
            
        html_content = self.mermaid_renderer.render(markdown_content)
        self.preview_view.setHtml(html_content)
        
        # Показываем чистый HTML во второй вкладке
        self.source_view.setHtml(f"<pre>{html_content}</pre>")