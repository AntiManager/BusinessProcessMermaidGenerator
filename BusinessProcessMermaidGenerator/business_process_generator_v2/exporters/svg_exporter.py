"""
Экспорт в HTML с SVG диаграммой
"""
import json
from pathlib import Path
from typing import Dict, List
from models import Operation, Choices, AnalysisData
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

def build_svg_diagram(operations: Dict[str, Operation], analysis_data: AnalysisData, choices: Choices) -> str:
    """
    Строит SVG диаграмму бизнес-процессов
    """
    external_inputs = analysis_data.external_inputs
    final_outputs = analysis_data.final_outputs
    input_to_operations = analysis_data.input_to_operations
    analysis = analysis_data.analysis
    
    critical_ops = {c.operation for c in analysis.critical_points}
    
    # Рассчитываем размеры и позиционирование
    node_width = 200
    node_height = 60
    horizontal_spacing = 250
    vertical_spacing = 120
    
    # Собираем все узлы
    nodes = []
    node_positions = {}
    
    # Внешние входы
    y_offset = 50
    for i, inp in enumerate(sorted(external_inputs)):
        if inp:
            nodes.append({
                'id': safe_id(inp),
                'text': inp,
                'type': 'external',
                'x': 50,
                'y': y_offset + i * vertical_spacing
            })
            node_positions[safe_id(inp)] = (50, y_offset + i * vertical_spacing)
    
    # Операции
    op_x = 300
    for i, (name, op) in enumerate(operations.items()):
        is_merge = len(op.inputs) > 1
        is_split = any(len(input_to_operations.get(out, [])) > 1 for out in op.outputs)
        
        node_type = "critical" if name in critical_ops else (
            "merge_split" if is_merge and is_split else
            "merge" if is_merge else
            "split" if is_split else
            "normal"
        )
        
        nodes.append({
            'id': safe_id(name),
            'text': op.node_text,
            'type': node_type,
            'x': op_x + (i % 3) * horizontal_spacing,
            'y': 100 + (i // 3) * vertical_spacing
        })
        node_positions[safe_id(name)] = (op_x + (i % 3) * horizontal_spacing, 100 + (i // 3) * vertical_spacing)
    
    # Конечные выходы
    final_x = op_x + 3 * horizontal_spacing
    for i, out in enumerate(sorted(final_outputs)):
        if out:
            nodes.append({
                'id': safe_id(out),
                'text': out,
                'type': 'final',
                'x': final_x,
                'y': y_offset + i * vertical_spacing
            })
            node_positions[safe_id(out)] = (final_x, y_offset + i * vertical_spacing)
    
    # Собираем все связи
    links = []
    added_links = set()
    
    for name, op in operations.items():
        src_id = safe_id(name)
        
        # Связи к конечным выходам
        for output in op.outputs:
            if output and output in final_outputs:
                link_key = f"{src_id}-{safe_id(output)}"
                if link_key not in added_links:
                    added_links.add(link_key)
                    links.append({
                        'from': src_id,
                        'to': safe_id(output),
                        'label': output
                    })
            
            # Связи между операциями
            if output in input_to_operations:
                for target_op in input_to_operations[output]:
                    link_key = f"{src_id}-{safe_id(target_op)}"
                    if link_key not in added_links:
                        added_links.add(link_key)
                        links.append({
                            'from': src_id,
                            'to': safe_id(target_op),
                            'label': output
                        })
        
        # Связи от внешних входов
        for inp in op.inputs:
            if not inp:
                continue
            if inp in external_inputs:
                link_key = f"{safe_id(inp)}-{src_id}"
                if link_key not in added_links:
                    added_links.add(link_key)
                    links.append({
                        'from': safe_id(inp),
                        'to': src_id,
                        'label': inp
                    })
    
    # Генерируем SVG
    svg_width = final_x + 200
    svg_height = max([node['y'] for node in nodes]) + 200
    
    svg_parts = [
        f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" id="processDiagram">',
        '<defs>',
        '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
        '<polygon points="0 0, 10 3.5, 0 7" fill="#333"/>',
        '</marker>',
        '</defs>'
    ]
    
    # Стили для узлов
    node_styles = {
        'external': {'fill': '#fff9c4', 'stroke': '#f57f17', 'stroke-width': '2'},
        'final': {'fill': '#ffcdd2', 'stroke': '#c62828', 'stroke-width': '2'},
        'critical': {'fill': '#ff4444', 'stroke': '#000', 'stroke-width': '3', 'stroke-dasharray': '5,5'},
        'merge': {'fill': '#ffb74d', 'stroke': '#ef6c00', 'stroke-width': '2'},
        'split': {'fill': '#ba68c8', 'stroke': '#6a1b9a', 'stroke-width': '2'},
        'merge_split': {'fill': '#ff8a65', 'stroke': '#d84315', 'stroke-width': '2'},
        'normal': {'fill': '#90caf9', 'stroke': '#1565c0', 'stroke-width': '2'}
    }
    
    # Рисуем связи
    for link in links:
        from_node = next((n for n in nodes if n['id'] == link['from']), None)
        to_node = next((n for n in nodes if n['id'] == link['to']), None)
        
        if from_node and to_node:
            from_x, from_y = from_node['x'] + node_width, from_node['y'] + node_height / 2
            to_x, to_y = to_node['x'], to_node['y'] + node_height / 2
            
            # Кривая Безье для связи
            control_x1 = from_x + (to_x - from_x) * 0.5
            control_x2 = from_x + (to_x - from_x) * 0.5
            
            path_d = f"M {from_x} {from_y} C {control_x1} {from_y} {control_x2} {to_y} {to_x} {to_y}"
            
            svg_parts.append(f'<path d="{path_d}" stroke="#333" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>')
            
            # Текст метки
            text_x = (from_x + to_x) / 2
            text_y = (from_y + to_y) / 2 - 10
            
            svg_parts.append(f'<text x="{text_x}" y="{text_y}" text-anchor="middle" font-size="12" fill="#333">{escape_text(link["label"])}</text>')
    
    # Рисуем узлы
    for node in nodes:
        style = node_styles.get(node['type'], node_styles['normal'])
        
        # Прямоугольник узла
        svg_parts.append(f'<rect x="{node["x"]}" y="{node["y"]}" width="{node_width}" height="{node_height}" rx="5" ry="5" style="fill:{style["fill"]};stroke:{style["stroke"]};stroke-width:{style["stroke-width"]};{"stroke-dasharray:" + style["stroke-dasharray"] + ";" if "stroke-dasharray" in style else ""}"/>')
        
        # Текст узла - разбиваем на строки
        text_lines = []
        words = node['text'].split()
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if len(test_line) * 6 <= node_width - 20:  # Примерная оценка ширины текста
                current_line.append(word)
            else:
                if current_line:
                    text_lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            text_lines.append(' '.join(current_line))
        
        # Ограничиваем количество строк
        text_lines = text_lines[:3]
        
        # Рисуем строки текста
        for i, line in enumerate(text_lines):
            text_y = node['y'] + 20 + i * 15
            svg_parts.append(f'<text x="{node["x"] + node_width / 2}" y="{text_y}" text-anchor="middle" font-size="12" fill="#333">{escape_text(line)}</text>')
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)

def generate_svg_html_file(svg_content: str, analysis_data: AnalysisData, operations: Dict[str, Operation], 
                          choices: Choices, available_columns: List[str], output_file: Path) -> None:
    """
    Генерирует HTML файл с SVG диаграммой
    """
    analysis = analysis_data.analysis
    
    # Сбор данных для таблиц
    op_rows = []
    critical_ops = {c.operation for c in analysis.critical_points}
    
    input_to_operations = analysis_data.input_to_operations
    
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
    <title>Диаграмма бизнес-процесса (SVG)</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
            overflow-x: hidden;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .diagram-wrapper {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-bottom: 20px;
        }}
        .diagram-container {{
            width: 100%;
            height: 70vh;
            position: relative;
            background: 
                linear-gradient(90deg, #f0f0f0 1px, transparent 1px),
                linear-gradient(#f0f0f0 1px, transparent 1px);
            background-size: 20px 20px;
            cursor: grab;
            overflow: hidden;
        }}
        .diagram-container:active {{
            cursor: grabbing;
        }}
        .diagram-container.dragging {{
            cursor: grabbing;
        }}
        .controls {{
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
            padding: 15px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        button {{
            padding: 8px 16px;
            background: #007cba;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }}
        button:hover {{
            background: #005a87;
        }}
        .zoom-info {{
            padding: 8px 16px;
            background: #e7f3ff;
            border-radius: 4px;
            font-size: 14px;
            min-width: 80px;
            text-align: center;
            font-weight: bold;
        }}
        h1, h2, h3 {{
            color: #333;
            margin: 0 0 15px 0;
        }}
        .analysis-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border: 2px solid #333;
            border-radius: 3px;
        }}
        table {{
            width: 100%;
            margin: 15px 0;
            border-collapse: collapse;
        }}
        #processDiagram {{
            transition: transform 0.1s ease;
        }}
        .fullscreen {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: white;
            z-index: 10000;
            margin: 0;
            padding: 0;
        }}
        .fullscreen .diagram-container {{
            height: 100vh;
        }}
        .fullscreen-controls {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10001;
            display: flex;
            gap: 10px;
            background: rgba(255,255,255,0.9);
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .zoom-slider {{
            width: 120px;
            margin: 0 10px;
        }}
        .control-group {{
            display: flex;
            align-items: center;
            gap: 5px;
            margin: 0 10px;
        }}
        .download-btn {{
            background: #28a745;
        }}
        .download-btn:hover {{
            background: #218838;
        }}
        .reset-btn {{
            background: #6c757d;
        }}
        .reset-btn:hover {{
            background: #5a6268;
        }}
        .view-controls {{
            display: flex;
            gap: 5px;
            margin-left: auto;
        }}
        .coordinates {{
            padding: 8px 12px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 12px;
            color: #666;
            font-family: monospace;
        }}
        .tooltip {{
            position: absolute;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            max-width: 300px;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Диаграмма бизнес-процесса (SVG)</h1>
        
        <div class="controls">
            <strong>Навигация:</strong>
            <div class="control-group">
                <button onclick="zoomOut()" title="Уменьшить (Ctrl+-)">−</button>
                <input type="range" min="10" max="300" value="100" class="zoom-slider" id="zoomSlider" oninput="updateZoomFromSlider(this.value)" title="Масштаб">
                <button onclick="zoomIn()" title="Увеличить (Ctrl++)">+</button>
                <div class="zoom-info" id="zoomInfo">100%</div>
            </div>
            <button onclick="resetView()" class="reset-btn" title="Сбросить вид (Ctrl+0)">Сброс</button>
            <button onclick="fitToScreen()" title="Вместить в экран (Ctrl+1)">Вместить</button>
            
            <div class="view-controls">
                <button onclick="downloadPNG()" class="download-btn" title="Скачать как PNG">📥 PNG</button>
                <button onclick="toggleFullscreen()" title="Полный экран (F11)">⛶ Полный экран</button>
            </div>
        </div>
        
        <div style="display: flex; gap: 15px; align-items: center; margin-top: 10px; font-size: 12px; color: #666;">
            <div>🖱️ <strong>ЛКМ</strong> - перетаскивание</div>
            <div>🔍 <strong>Колесо</strong> - масштаб</div>
            <div>⌨️ <strong>Ctrl+колесо</strong> - точный масштаб</div>
            <div class="coordinates" id="coordinates">x: 0, y: 0</div>
        </div>
    </div>
    
    <div class="diagram-wrapper">
        <div class="diagram-container" id="diagramContainer">
            <div id="svgContainer" style="position: absolute; top: 0; left: 0;">
                {svg_content}
            </div>
        </div>
    </div>
    
    <div class="legend">
        <div class="legend-item"><div class="legend-color" style="background: #fff9c4;"></div> Внешние входы</div>
        <div class="legend-item"><div class="legend-color" style="background: #ffcdd2;"></div> Конечные выходы</div>
        <div class="legend-item"><div class="legend-color" style="background: #ffb74d;"></div> Операции слияния</div>
        <div class="legend-item"><div class="legend-color" style="background: #ba68c8;"></div> Операции разветвления</div>
        <div class="legend-item"><div class="legend-color" style="background: #ff4444;"></div> Супер-критические операции</div>
        <div class="legend-item"><div class="legend-color" style="background: #90caf9;"></div> Обычные операции</div>
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

    <div class="analysis-section">
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
    </div>

    <script>
        // Состояние навигации
        let scale = 1.0;
        let translateX = 0;
        let translateY = 0;
        let isDragging = false;
        let isPanning = false;
        let startX, startY;
        let lastX, lastY;
        
        // Элементы DOM
        const diagramContainer = document.getElementById('diagramContainer');
        const svgElement = document.getElementById('processDiagram');
        const svgContainer = document.getElementById('svgContainer');
        const zoomInfo = document.getElementById('zoomInfo');
        const zoomSlider = document.getElementById('zoomSlider');
        const coordinates = document.getElementById('coordinates');
        
        // Размеры SVG
        const svgWidth = svgElement.width.baseVal.value;
        const svgHeight = svgElement.height.baseVal.value;
        
        // Тултип для узлов
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.style.display = 'none';
        document.body.appendChild(tooltip);
        
        // Инициализация
        function initNavigation() {
            updateTransform();
            updateZoomInfo();
            setupEventListeners();
            fitToScreen();
            
            // Добавляем tooltip для узлов
            setupTooltips();
        }
        
        function setupEventListeners() {
            // Перетаскивание
            diagramContainer.addEventListener('mousedown', startDragging);
            diagramContainer.addEventListener('mousemove', onMouseMove);
            diagramContainer.addEventListener('mouseup', stopDragging);
            diagramContainer.addEventListener('mouseleave', stopDragging);
            
            // Масштабирование колесом
            diagramContainer.addEventListener('wheel', onWheel, { passive: false });
            
            // Клавиатура
            document.addEventListener('keydown', onKeyDown);
            
            // Полный экран
            document.addEventListener('fullscreenchange', onFullscreenChange);
        }
        
        function setupTooltips() {
            const nodes = svgElement.querySelectorAll('rect');
            nodes.forEach(node => {
                const textElement = node.parentNode.querySelector('text');
                if (textElement) {
                    const nodeText = textElement.textContent;
                    node.addEventListener('mouseenter', (e) => {
                        const rect = node.getBoundingClientRect();
                        tooltip.innerHTML = nodeText.replace(/<br>/g, '\\n');
                        tooltip.style.left = (rect.left + rect.width / 2) + 'px';
                        tooltip.style.top = (rect.top - 10) + 'px';
                        tooltip.style.display = 'block';
                    });
                    
                    node.addEventListener('mouseleave', () => {
                        tooltip.style.display = 'none';
                    });
                    
                    node.addEventListener('mousemove', (e) => {
                        tooltip.style.left = (e.clientX + 10) + 'px';
                        tooltip.style.top = (e.clientY + 10) + 'px';
                    });
                }
            });
        }
        
        function startDragging(e) {
            if (e.button === 0) { // Левая кнопка мыши
                isDragging = true;
                isPanning = true;
                startX = e.clientX - translateX;
                startY = e.clientY - translateY;
                diagramContainer.classList.add('dragging');
                e.preventDefault();
            }
        }
        
        function onMouseMove(e) {
            // Обновление координат
            const rect = diagramContainer.getBoundingClientRect();
            const x = (e.clientX - rect.left - translateX) / scale;
            const y = (e.clientY - rect.top - translateY) / scale;
            coordinates.textContent = `x: ${Math.round(x)}, y: ${Math.round(y)}`;
            
            // Перетаскивание
            if (isDragging && isPanning) {
                translateX = e.clientX - startX;
                translateY = e.clientY - startY;
                updateTransform();
            }
            
            // Перемещение тултипа
            if (tooltip.style.display === 'block') {
                tooltip.style.left = (e.clientX + 15) + 'px';
                tooltip.style.top = (e.clientY + 15) + 'px';
            }
        }
        
        function stopDragging() {
            isDragging = false;
            isPanning = false;
            diagramContainer.classList.remove('dragging');
        }
        
        function onWheel(e) {
            e.preventDefault();
            
            const rect = diagramContainer.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            const delta = -Math.sign(e.deltaY) * (e.ctrlKey ? 0.1 : 0.25);
            const newScale = Math.max(0.1, Math.min(5, scale + delta));
            
            if (newScale !== scale) {
                // Масштабирование относительно курсора
                const scaleChange = newScale / scale;
                translateX = mouseX - (mouseX - translateX) * scaleChange;
                translateY = mouseY - (mouseY - translateY) * scaleChange;
                
                scale = newScale;
                updateTransform();
                updateZoomInfo();
            }
        }
        
        function onKeyDown(e) {
            // Масштабирование клавишами
            if ((e.ctrlKey || e.metaKey) && !e.altKey) {
                if (e.key === '=' || e.key === '+') {
                    e.preventDefault();
                    zoomIn();
                } else if (e.key === '-') {
                    e.preventDefault();
                    zoomOut();
                } else if (e.key === '0') {
                    e.preventDefault();
                    resetView();
                } else if (e.key === '1') {
                    e.preventDefault();
                    fitToScreen();
                }
            }
            
            // Полный экран
            if (e.key === 'F11') {
                e.preventDefault();
                toggleFullscreen();
            }
            
            // Escape для выхода из полноэкранного режима
            if (e.key === 'Escape' && document.fullscreenElement) {
                toggleFullscreen();
            }
        }
        
        function updateTransform() {
            svgContainer.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
        }
        
        function updateZoomInfo() {
            const percentage = Math.round(scale * 100);
            zoomInfo.textContent = `${percentage}%`;
            zoomSlider.value = percentage;
        }
        
        function updateZoomFromSlider(value) {
            const newScale = parseInt(value) / 100;
            
            // Масштабирование относительно центра
            const rect = diagramContainer.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const scaleChange = newScale / scale;
            translateX = centerX - (centerX - translateX) * scaleChange;
            translateY = centerY - (centerY - translateY) * scaleChange;
            
            scale = newScale;
            updateTransform();
            updateZoomInfo();
        }
        
        function zoomIn() {
            const rect = diagramContainer.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const newScale = Math.min(5, scale + 0.25);
            const scaleChange = newScale / scale;
            translateX = centerX - (centerX - translateX) * scaleChange;
            translateY = centerY - (centerY - translateY) * scaleChange;
            
            scale = newScale;
            updateTransform();
            updateZoomInfo();
        }
        
        function zoomOut() {
            const rect = diagramContainer.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const newScale = Math.max(0.1, scale - 0.25);
            const scaleChange = newScale / scale;
            translateX = centerX - (centerX - translateX) * scaleChange;
            translateY = centerY - (centerY - translateY) * scaleChange;
            
            scale = newScale;
            updateTransform();
            updateZoomInfo();
        }
        
        function resetView() {
            scale = 1.0;
            translateX = 0;
            translateY = 0;
            updateTransform();
            updateZoomInfo();
        }
        
        function fitToScreen() {
            const containerWidth = diagramContainer.clientWidth;
            const containerHeight = diagramContainer.clientHeight;
            
            const scaleX = containerWidth / svgWidth;
            const scaleY = containerHeight / svgHeight;
            scale = Math.min(scaleX, scaleY, 1.0); // Не увеличивать больше 100%
            
            // Центрируем
            translateX = (containerWidth - svgWidth * scale) / 2;
            translateY = (containerHeight - svgHeight * scale) / 2;
            
            updateTransform();
            updateZoomInfo();
        }
        
        function downloadPNG() {
            // Создаем временный SVG с текущим масштабом и позицией для рендеринга
            const tempSvg = svgElement.cloneNode(true);
            tempSvg.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
            
            html2canvas(diagramContainer, {
                backgroundColor: '#ffffff',
                scale: 2,
                useCORS: true,
                allowTaint: true,
                logging: false
            }).then(canvas => {
                const link = document.createElement('a');
                link.download = 'business_process_diagram.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            });
        }
        
        function toggleFullscreen() {
            if (!document.fullscreenElement) {
                diagramContainer.parentElement.classList.add('fullscreen');
                if (diagramContainer.requestFullscreen) {
                    diagramContainer.requestFullscreen();
                }
                // Обновляем размер после перехода в полноэкранный режим
                setTimeout(fitToScreen, 100);
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                }
            }
        }
        
        function onFullscreenChange() {
            if (!document.fullscreenElement) {
                diagramContainer.parentElement.classList.remove('fullscreen');
                resetView();
            }
        }
        
        // Инициализация при загрузке
        document.addEventListener('DOMContentLoaded', initNavigation);
        
        // Обработка изменения размера окна
        window.addEventListener('resize', () => {
            if (document.fullscreenElement) {
                setTimeout(fitToScreen, 100);
            }
        });
    </script>
</body>
</html>'''

    output_file.write_text(html_content, encoding=ENCODING)

def export_svg_html(operations: Dict[str, Operation], analysis_data: AnalysisData, 
                   choices: Choices, available_columns: List[str], output_base: str = None) -> None:
    """
    Экспортирует диаграмму в HTML с SVG
    """
    if output_base is None:
        output_base = "business_process_diagram_svg"
    
    output_file = Path(f"{output_base}.html")

    # Генерация SVG диаграммы
    svg_content = build_svg_diagram(operations, analysis_data, choices)

    # Генерация HTML файла
    generate_svg_html_file(svg_content, analysis_data, operations, choices, available_columns, output_file)
    
    print(f"\n" + "="*60)
    print("✓ HTML-ДИАГРАММА С SVG УСПЕШНО СОЗДАНА!")
    print("="*60)
    print(f"Файл: {output_file}")
    print("🎯 УЛУЧШЕННАЯ НАВИГАЦИЯ:")
    print("   • 🖱️  ЛКМ - перетаскивание диаграммы")
    print("   • 🔍 Колесо мыши - масштабирование")
    print("   • ⌨️  Ctrl+колесо - точное масштабирование")
    print("   • 📍 Подсказки при наведении на узлы")
    print("   • 📊 Отображение координат")