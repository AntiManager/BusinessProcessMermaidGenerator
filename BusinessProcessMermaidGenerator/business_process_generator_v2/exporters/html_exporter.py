"""
Экспорт в HTML с Mermaid диаграммой
"""
import json
from pathlib import Path
from typing import Dict, List
from models import Operation, Choices, AnalysisData
from exporters.mermaid_exporter import build_mermaid_html
from utils import safe_id, escape_text, clean_text
from config import ENCODING

def create_html_table(headers: List[str], data: List[Dict[str, str]]) -> str:
    """
    Создает HTML таблицу из данных
    """
    if not data:
        return "<p>Нет данных для отображения</p>"
    
    html = ['<table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">']
    html.append('<thead><tr>')
    for header in headers:
        html.append(f'<th style="padding: 8px; background: #f0f0f0;">{header}</th>')
    html.append('</tr></thead>')
    html.append('<tbody>')
    for row in data:
        html.append('<tr>')
        for header in headers:
            value = str(row.get(header, ""))
            value = value.replace('\n', '<br>')
            html.append(f'<td style="padding: 8px;">{value}</td>')
        html.append('</tr>')
    html.append('</tbody></table>')
    return '\n'.join(html)

def generate_mermaid_html_file(mermaid_code: str, analysis_data: AnalysisData, operations: Dict[str, Operation], 
                              choices: Choices, available_columns: List[str], output_file: Path) -> None:
    """
    Генерирует HTML файл с Mermaid диаграммой и улучшенным управлением
    """
    analysis = analysis_data.analysis
    
    # Сбор данных для таблиц
    external_inputs = analysis.external_inputs
    final_outputs = analysis.final_outputs
    
    # Реестр операций
    op_rows = []
    critical_ops = {c.operation for c in analysis.critical_points}
    
    # Создаем mapping от входа к операциям, которые его используют
    from collections import defaultdict
    input_to_operations = defaultdict(list)
    for op in operations.values():
        for inp in op.inputs:
            if inp:
                input_to_operations[inp].append(op.name)
    
    for name, op in operations.items():
        is_merge = len(op.inputs) > 1
        is_split = any(len(input_to_operations.get(out, [])) > 1 for out in op.outputs)
        node_type = (
            "Супер-критичная" if name in critical_ops else
            "Слияние+Разветвление" if is_merge and is_split else
            "Слияние" if is_merge else
            "Разветвление" if is_split else
            "Обычный"
        )
        row_data = {
            "Операция": name,
            "Входы": ", ".join(op.inputs) if op.inputs else "-",
            "Выход": ", ".join(op.outputs) if op.outputs else "-",
            "Тип узла": node_type,
        }
        if 'Группа' in available_columns:
            row_data["Группа"] = op.group
        if 'Владелец' in available_columns:
            row_data["Владелец"] = op.owner
        if 'Подробное описание операции' in available_columns:
            row_data["Подробное описание"] = op.detailed
            
        op_rows.append(row_data)

    # Определение доступных колонок для таблицы
    available_cols = {
        'group': 'Группа' in available_columns,
        'owner': 'Владелец' in available_columns,
        'detailed_desc': 'Подробное описание операции' in available_columns
    }

    html_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Диаграмма бизнес-процесса</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose'
        }});
    </script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
            overflow-x: hidden;
        }}
        .diagram-container {{
            border: 1px solid #ccc;
            padding: 20px;
            margin: 20px 0;
            background: white;
            border-radius: 5px;
            overflow: auto;
            width: 100%;
            min-height: 600px;
            cursor: move;
        }}
        .diagram-container:active {{
            cursor: grabbing;
        }}
        .controls {{
            margin: 10px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }}
        button {{
            padding: 8px 15px;
            background: #007cba;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 14px;
        }}
        button:hover {{
            background: #005a87;
        }}
        .zoom-info {{
            padding: 8px 15px;
            background: #e7f3ff;
            border-radius: 3px;
            font-size: 14px;
            min-width: 120px;
            text-align: center;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .analysis-section {{
            background: #f9f9f9;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-right: 20px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 5px;
            border: 1px solid #333;
        }}
        table {{
            width: 100%;
            margin: 15px 0;
        }}
        .mermaid {{
            transform-origin: 0 0;
            transition: transform 0.2s ease;
            min-width: min-content;
        }}
        .fullscreen {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: white;
            z-index: 1000;
            padding: 20px;
        }}
        .fullscreen-controls {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1001;
            display: flex;
            gap: 10px;
        }}
        .zoom-slider {{
            width: 150px;
            margin: 0 10px;
        }}
        .control-group {{
            display: flex;
            align-items: center;
            gap: 5px;
            margin: 0 10px;
        }}
    </style>
</head>
<body>
    <h1>Диаграмма бизнес-процесса</h1>
    
    <div class="controls">
        <strong>Управление диаграммой:</strong>
        <div class="control-group">
            <button onclick="zoomOut()">−</button>
            <input type="range" min="10" max="300" value="100" class="zoom-slider" id="zoomSlider" oninput="updateZoomFromSlider(this.value)">
            <button onclick="zoomIn()">+</button>
            <div class="zoom-info" id="zoomInfo">100%</div>
        </div>
        <button onclick="resetZoom()">Сброс (100%)</button>
        <button onclick="fitToScreen()">Вместить в экран</button>
        <button onclick="toggleFullscreen()">Полный экран ⛶</button>
        <div style="margin-left: auto; font-size: 12px; color: #666;">
            🔍 Ctrl+колесо для зума • 🖱️ Перетаскивание для навигации
        </div>
    </div>
    
    <div class="diagram-container" id="diagramContainer">
        <div class="mermaid" id="mermaidDiagram">
{mermaid_code}
        </div>
    </div>
    
    <div class="legend">
        <div class="legend-item"><div class="legend-color" style="background: yellow;"></div> Внешние входы</div>
        <div class="legend-item"><div class="legend-color" style="background: red;"></div> Конечные выходы</div>
        <div class="legend-item"><div class="legend-color" style="background: orange;"></div> Операции слияния</div>
        <div class="legend-item"><div class="legend-color" style="background: purple;"></div> Операции разветвления</div>
        <div class="legend-item"><div class="legend-color" style="background: #ff4444;"></div> Супер-критические операции</div>
    </div>

    <div class="analysis-section">
        <h2>Анализ процесса</h2>
        <h3>Супер-критические операции</h3>
'''

    if analysis.critical_points:
        html_content += '<ul>'
        for cp in sorted(analysis.critical_points, key=lambda x: (x.inputs_count, x.output_reuse), reverse=True):
            html_content += f'<li><strong>{cp.operation}</strong>: {cp.inputs_count} входов, выход идёт в {cp.output_reuse} операций</li>'
        html_content += '</ul>'
    else:
        html_content += '<p>Таких операций нет</p>'
    
    html_content += f'''
        <h3>Статистика процесса</h3>
        <p><strong>Всего операций:</strong> {analysis.operations_count}</p>
        <p><strong>Внешние входы:</strong> {len(analysis.external_inputs)}</p>
        <p><strong>Конечные выходы:</strong> {len(analysis.final_outputs)}</p>
        <p><strong>Операций слияния:</strong> {len(analysis.merge_points)}</p>
        <p><strong>Операций разветвления:</strong> {len(analysis.split_points)}</p>
        <p><strong>Супер-критических операций:</strong> {len(analysis.critical_points)}</p>
    </div>

    <h2>Реестр операций</h2>
'''

    table_headers = ["Операция"]
    if available_cols['group']:
        table_headers.append("Группа")
    if available_cols['owner']:
        table_headers.append("Владелец")
    table_headers.extend(["Входы", "Выход", "Тип узла"])
    if available_cols['detailed_desc']:
        table_headers.append("Подробное описание")
    
    html_content += create_html_table(table_headers, op_rows)

    html_content += '''
    <script>
        let scale = 1.0;
        let isFullscreen = false;
        let isDragging = false;
        let startX, startY, scrollLeft, scrollTop;
        const mermaidDiagram = document.getElementById('mermaidDiagram');
        const zoomInfo = document.getElementById('zoomInfo');
        const zoomSlider = document.getElementById('zoomSlider');
        const diagramContainer = document.getElementById('diagramContainer');
        
        function updateZoomInfo() {
            const percentage = Math.round(scale * 100);
            zoomInfo.textContent = `${percentage}%`;
            zoomSlider.value = percentage;
            mermaidDiagram.style.transform = `scale(${scale})`;
        }
        
        function updateZoomFromSlider(value) {
            scale = parseInt(value) / 100;
            updateZoomInfo();
        }
        
        function zoomIn() {
            scale = Math.min(3.0, scale + 0.1);
            updateZoomInfo();
        }
        
        function zoomOut() {
            scale = Math.max(0.1, scale - 0.1);
            updateZoomInfo();
        }
        
        function resetZoom() {
            scale = 1.0;
            updateZoomInfo();
            // Сброс скролла к центру
            setTimeout(() => {
                diagramContainer.scrollLeft = (diagramContainer.scrollWidth - diagramContainer.clientWidth) / 2;
                diagramContainer.scrollTop = (diagramContainer.scrollHeight - diagramContainer.clientHeight) / 2;
            }, 100);
        }
        
        function fitToScreen() {
            const svg = mermaidDiagram.querySelector('svg');
            if (svg) {
                const containerWidth = diagramContainer.clientWidth - 40;
                const containerHeight = diagramContainer.clientHeight - 40;
                const svgWidth = svg.getBoundingClientRect().width;
                const svgHeight = svg.getBoundingClientRect().height;
                
                const scaleX = containerWidth / svgWidth;
                const scaleY = containerHeight / svgHeight;
                scale = Math.min(scaleX, scaleY);
                updateZoomInfo();
                
                // Центрируем диаграмму после подгонки
                setTimeout(() => {
                    diagramContainer.scrollLeft = (diagramContainer.scrollWidth - diagramContainer.clientWidth) / 2;
                    diagramContainer.scrollTop = (diagramContainer.scrollHeight - diagramContainer.clientHeight) / 2;
                }, 100);
            }
        }
        
        function toggleFullscreen() {
            if (!isFullscreen) {
                diagramContainer.classList.add('fullscreen');
                isFullscreen = true;
                // Добавляем кнопку выхода из полноэкранного режима
                const exitButton = document.createElement('button');
                exitButton.textContent = '✕ Выйти';
                exitButton.onclick = toggleFullscreen;
                exitButton.style.cssText = 'padding: 10px 15px; background: #dc3545; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px;';
                exitButton.id = 'exitFullscreen';
                
                const fullscreenControls = document.createElement('div');
                fullscreenControls.className = 'fullscreen-controls';
                fullscreenControls.appendChild(exitButton);
                document.body.appendChild(fullscreenControls);
                
                // Подгоняем под размер экрана
                setTimeout(fitToScreen, 100);
            } else {
                diagramContainer.classList.remove('fullscreen');
                isFullscreen = false;
                const fullscreenControls = document.querySelector('.fullscreen-controls');
                if (fullscreenControls) {
                    fullscreenControls.remove();
                }
                resetZoom();
            }
        }
        
        // Функции для перетаскивания диаграммы
        diagramContainer.addEventListener('mousedown', (e) => {
            if (e.button === 0) { // Левая кнопка мыши
                isDragging = true;
                startX = e.pageX - diagramContainer.offsetLeft;
                startY = e.pageY - diagramContainer.offsetTop;
                scrollLeft = diagramContainer.scrollLeft;
                scrollTop = diagramContainer.scrollTop;
                diagramContainer.style.cursor = 'grabbing';
            }
        });
        
        diagramContainer.addEventListener('mouseleave', () => {
            isDragging = false;
            diagramContainer.style.cursor = 'move';
        });
        
        diagramContainer.addEventListener('mouseup', () => {
            isDragging = false;
            diagramContainer.style.cursor = 'move';
        });
        
        diagramContainer.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - diagramContainer.offsetLeft;
            const y = e.pageY - diagramContainer.offsetTop;
            const walkX = (x - startX) * 2; // Множитель для скорости скролла
            const walkY = (y - startY) * 2;
            diagramContainer.scrollLeft = scrollLeft - walkX;
            diagramContainer.scrollTop = scrollTop - walkY;
        });
        
        // Обработка клавиатуры
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isFullscreen) {
                toggleFullscreen();
            }
            if ((e.ctrlKey || e.metaKey) && !e.altKey) {
                if (e.key === '=' || e.key === '+') {
                    e.preventDefault();
                    zoomIn();
                } else if (e.key === '-') {
                    e.preventDefault();
                    zoomOut();
                } else if (e.key === '0') {
                    e.preventDefault();
                    resetZoom();
                } else if (e.key === '1') {
                    e.preventDefault();
                    fitToScreen();
                }
            }
        });
        
        // Масштабирование колесом мыши с зажатым Ctrl
        diagramContainer.addEventListener('wheel', (e) => {
            if (e.ctrlKey) {
                e.preventDefault();
                const rect = diagramContainer.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;
                
                const zoomIntensity = 0.001;
                const wheel = e.deltaY < 0 ? 1 : -1;
                const newScale = Math.max(0.1, Math.min(3.0, scale + wheel * zoomIntensity * 50));
                
                // Сохраняем позицию мыши относительно диаграммы
                const scaleChange = newScale / scale;
                diagramContainer.scrollLeft = (diagramContainer.scrollLeft + mouseX) * scaleChange - mouseX;
                diagramContainer.scrollTop = (diagramContainer.scrollTop + mouseY) * scaleChange - mouseY;
                
                scale = newScale;
                updateZoomInfo();
            }
        }, { passive: false });
        
        // Инициализация после загрузки Mermaid
        setTimeout(() => {
            updateZoomInfo();
            // Автоматически подгоняем под экран при загрузке
            setTimeout(() => {
                fitToScreen();
                // Устанавливаем курсор для перетаскивания
                diagramContainer.style.cursor = 'move';
            }, 500);
        }, 1000);
        
        // Обработка изменения размера окна
        window.addEventListener('resize', () => {
            if (isFullscreen) {
                setTimeout(fitToScreen, 100);
            }
        });
    </script>
</body>
</html>'''

    output_file.write_text(html_content, encoding=ENCODING)

def export_html_mermaid(operations: Dict[str, Operation], analysis_data: AnalysisData, 
                       choices: Choices, available_columns: List[str], output_base: str = None) -> None:
    """
    Экспортирует диаграмму в HTML с Mermaid
    """
    # Используем переданное имя файла или значение по умолчанию
    if output_base is None:
        output_base = "business_process_diagram"
    
    output_file = Path(f"{output_base}.html")

    # Генерация Mermaid кода
    mermaid_code = build_mermaid_html(operations, analysis_data, choices)

    # Генерация HTML файла
    generate_mermaid_html_file(mermaid_code, analysis_data, operations, choices, available_columns, output_file)
    
    print(f"\n" + "="*60)
    print("✓ HTML-ДИАГРАММА С MERMAID УСПЕШНО СОЗДАНА!")
    print("="*60)
    print(f"Файл: {output_file}")