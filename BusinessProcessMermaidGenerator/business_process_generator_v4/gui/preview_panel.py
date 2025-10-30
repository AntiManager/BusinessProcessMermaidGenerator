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
        
        # Показываем начальное сообщение
        self.show_initial_message()
    
    def show_initial_message(self):
        """Показывает начальное сообщение"""
        initial_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            padding: 40px; 
            text-align: center;
            color: #666;
        }
    </style>
</head>
<body>
    <h2>Business Process Generator v4.0</h2>
    <p>Сгенерируйте диаграмму или введите Markdown код для предпросмотра</p>
</body>
</html>"""
        self.preview_view.setHtml(initial_html)
        self.source_view.setHtml(f"<pre>{initial_html}</pre>")
    
    def update_preview(self, markdown_content):
        """Обновляет предпросмотр с рендерингом Mermaid"""
        try:
            if not markdown_content:
                self.show_initial_message()
                return
                
            html_content = self.mermaid_renderer.render(markdown_content)
            
            # Устанавливаем HTML в предпросмотр
            self.preview_view.setHtml(html_content, QUrl(""))
            
            # Показываем исходный код во второй вкладке
            escaped_html = html_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            source_html = f"<pre style='padding: 20px; font-family: monospace;'>{escaped_html}</pre>"
            self.source_view.setHtml(source_html, QUrl(""))
            
        except Exception as e:
            error_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        .error {{ background: #ffebee; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h3>Ошибка в предпросмотре:</h3>
    <div class="error">
        <pre>{str(e)}</pre>
    </div>
</body>
</html>"""
            self.preview_view.setHtml(error_html)