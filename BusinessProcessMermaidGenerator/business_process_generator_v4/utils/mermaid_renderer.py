"""
Рендерер Mermaid для live preview в GUI
"""
import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re

class MermaidExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(MermaidPreprocessor(md), 'mermaid', 25)

class MermaidPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_mermaid = False
        mermaid_block = []
        
        for line in lines:
            if line.strip() == '```mermaid':
                in_mermaid = True
                mermaid_block = []
                new_lines.append('<div class="mermaid">')
            elif line.strip() == '```' and in_mermaid:
                in_mermaid = False
                new_lines.extend(mermaid_block)
                new_lines.append('</div>')
            elif in_mermaid:
                mermaid_block.append(line)
            else:
                new_lines.append(line)
        
        return new_lines

class MermaidRenderer:
    def __init__(self):
        self.md = markdown.Markdown(extensions=[MermaidExtension(), 'fenced_code', 'tables'])
        
        self.html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
            line-height: 1.6;
        }
        .mermaid { 
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            text-align: center;
        }
        pre:not(.mermaid) { 
            background: #2d2d2d;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }
        code:not(.mermaid) {
            background: #2d2d2d;
            padding: 2px 6px;
            border-radius: 3px;
        }
        blockquote {
            border-left: 4px solid #007acc;
            margin: 0;
            padding-left: 16px;
            color: #9cdcfe;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }
        th, td {
            border: 1px solid #3c3c3c;
            padding: 8px 12px;
            text-align: left;
        }
        th {
            background: #2a2d2e;
        }
    </style>
</head>
<body>
    <div id="content">
        {content}
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose',
            flowchart: {{ 
                useMaxWidth: true,
                htmlLabels: true
            }}
        }});
        
        // Перерисовываем Mermaid при изменении
        function renderMermaid() {{
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
        }}
        
        // Автоматическая перерисовка при изменении размера
        window.addEventListener('resize', renderMermaid);
        setTimeout(renderMermaid, 100);
    </script>
</body>
</html>"""
    
    def render(self, markdown_text):
        """Рендерит Markdown с Mermaid в HTML"""
        try:
            if not markdown_text:
                return "<html><body><p>Нет контента для отображения</p></body></html>"
            
            # Сбрасываем состояние парсера Markdown для каждого рендера
            self.md.reset()
            html_content = self.md.convert(markdown_text)
            
            # Заменяем {content} в шаблоне, экранируя фигурные скобки
            final_html = self.html_template.replace('{content}', html_content)
            return final_html
            
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
    <h3>Ошибка рендеринга:</h3>
    <div class="error">
        <pre>{str(e)}</pre>
    </div>
</body>
</html>"""
            return error_html