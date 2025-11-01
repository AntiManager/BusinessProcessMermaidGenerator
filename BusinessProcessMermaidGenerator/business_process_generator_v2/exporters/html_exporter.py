"""
Экспорт в HTML с упрощенным дизайном и базовой навигацией
"""
import json
from pathlib import Path
from typing import Dict, List
from models import Operation, Choices, AnalysisData
from exporters.mermaid_exporter import build_mermaid_html
from utils import safe_id, escape_text, clean_text
from config import ENCODING

def create_simple_html_table(headers: List[str], data: List[Dict[str, str]]) -> str:
    """
    Создает простую HTML таблицу без сортировки
    """
    if not data:
        return "<p>Нет данных для отображения</p>"
    
    html = ['<table class="simple-table">']
    html.append('<thead><tr>')
    for header in headers:
        html.append(f'<th>{header}</th>')
    html.append('</tr></thead>')
    html.append('<tbody>')
    for row in data:
        html.append('<tr>')
        for header in headers:
            value = str(row.get(header, ""))
            value = value.replace('\n', '<br>')
            html.append(f'<td>{value}</td>')
        html.append('</tr>')
    html.append('</tbody></table>')
    return '\n'.join(html)

def generate_simple_html_report(mermaid_code: str, analysis_data: AnalysisData, operations: Dict[str, Operation], 
                               choices: Choices, available_columns: List[str], output_file: Path) -> None:
    """
    Генерирует упрощенный HTML отчет с навигацией по диаграмме
    """
    analysis = analysis_data.analysis
    
    # Подготовка данных для таблиц
    from collections import defaultdict
    input_to_operations = defaultdict(list)
    for op in operations.values():
        for inp in op.inputs:
            if inp:
                input_to_operations[inp].append(op.name)
    
    # Реестр операций
    op_rows = []
    critical_ops = {c.operation for c in analysis.critical_points}
    
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
            "Выходы": ", ".join(op.outputs) if op.outputs else "-",
            "Тип узла": node_type,
        }
        
        if 'Группа' in available_columns and op.group:
            row_data["Группа"] = op.group
        if 'Владелец' in available_columns and op.owner:
            row_data["Владелец"] = op.owner
        if 'Подробное описание операции' in available_columns and op.detailed:
            row_data["Описание"] = op.detailed
            
        op_rows.append(row_data)
    
    # Реестр входов/выходов
    io_rows = []
    items = analysis.external_inputs | analysis.final_outputs | set(analysis_data.output_to_operation) | set(input_to_operations)
    for item in sorted(items):
        if not item:
            continue
        src = "ВНЕШНИЙ ВХОД" if item in analysis.external_inputs else analysis_data.output_to_operation.get(item, "-")
        tgts = input_to_operations.get(item, [])
        if item in analysis.final_outputs and not tgts:
            tgts = ["КОНЕЧНЫЙ ВЫХОД"]
        io_rows.append({
            "Элемент": item,
            "Источник": src,
            "Потребители": ", ".join(tgts) if tgts else "-",
        })
    
    # Определение доступных колонок
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
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #fff;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e1e5e9;
        }}
        
        .header h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.2em;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 15px 0;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            background: #f8f9fa;
            padding: 8px 15px;
            border-radius: 6px;
            border-left: 3px solid #3498db;
            font-size: 0.9em;
        }}
        
        /* Секция диаграммы с навигацией */
        .diagram-section {{
            margin: 30px 0;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .diagram-header {{
            background: #2c3e50;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .diagram-controls {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        
        .control-btn {{
            background: #34495e;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.2s;
        }}
        
        .control-btn:hover {{
            background: #4a6b8a;
        }}
        
        .download-btn {{
            background: #27ae60;
        }}
        
        .download-btn:hover {{
            background: #2ecc71;
        }}
        
        .zoom-info {{
            background: rgba(255,255,255,0.1);
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 11px;
            min-width: 50px;
            text-align: center;
        }}
        
        .diagram-container {{
            width: 100%;
            height: 600px;
            overflow: auto;
            position: relative;
            background: 
                linear-gradient(90deg, #f8f9fa 1px, transparent 1px),
                linear-gradient(#f8f9fa 1px, transparent 1px);
            background-size: 20px 20px;
            cursor: grab;
        }}
        
        .diagram-container.dragging {{
            cursor: grabbing;
        }}
        
        #mermaid-diagram {{
            padding: 40px;
            min-width: fit-content;
            min-height: fit-content;
        }}
        
        .mermaid {{
            text-align: center;
        }}
        
        /* Увеличиваем размеры Mermaid по умолчанию */
        .mermaid svg {{
            transform: scale(1);
            transform-origin: 0 0;
        }}
        
        /* Секции с таблицами */
        .section {{
            margin: 30px 0;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .section-header {{
            background: #34495e;
            color: white;
            padding: 15px 20px;
            font-size: 1.1em;
        }}
        
        .section-content {{
            padding: 20px;
        }}
        
        /* Простые таблицы */
        .simple-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 0.9em;
        }}
        
        .simple-table th {{
            background: #f8f9fa;
            padding: 12px 15px;
            text-align: left;
            border-bottom: 2px solid #e1e5e9;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .simple-table td {{
            padding: 10px 15px;
            border-bottom: 1px solid #e1e5e9;
        }}
        
        .simple-table tr:hover {{
            background: #f8f9fa;
        }}
        
        /* Легенда */
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85em;
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            border: 1px solid #ccc;
        }}
        
        /* Адаптивность */
        @media (max-width: 768px) {{
            .stats {{
                flex-direction: column;
                align-items: center;
            }}
            
            .diagram-controls {{
                flex-wrap: wrap;
                justify-content: center;
            }}
            
            .diagram-container {{
                height: 400px;
            }}
            
            .legend {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .nav-hint {{
            font-size: 0.8em;
            color: #7f8c8d;
            text-align: center;
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Диаграмма бизнес-процесса</h1>
        <div class="stats">
            <div class="stat-item">Операций: {analysis.operations_count}</div>
            <div class="stat-item">Входы: {len(analysis.external_inputs)}</div>
            <div class="stat-item">Выходы: {len(analysis.final_outputs)}</div>
            <div class="stat-item">Критические: {len(analysis.critical_points)}</div>
        </div>
    </div>

    <!-- Секция диаграммы -->
    <div class="diagram-section">
        <div class="diagram-header">
            <h2>Визуализация процесса</h2>
            <div class="diagram-controls">
                <button class="control-btn" onclick="zoomOut()" title="Уменьшить">−</button>
                <div class="zoom-info" id="zoomInfo">100%</div>
                <button class="control-btn" onclick="zoomIn()" title="Увеличить">+</button>
                <button class="control-btn" onclick="resetView()" title="Сбросить вид">Сброс</button>
                <button class="control-btn" onclick="fitToScreen()" title="Вместить в экран">Вместить</button>
                <button class="control-btn download-btn" onclick="downloadPNG()" title="Скачать PNG">📥 PNG</button>
            </div>
        </div>
        <div class="diagram-container" id="diagramContainer">
            <div class="mermaid" id="mermaid-diagram">
{mermaid_code}
            </div>
        </div>
        <div class="nav-hint">
            🖱️ <strong>Колесо мыши</strong> - масштаб • <strong>ЛКМ + перетаскивание</strong> - навигация • 
            <strong>Ctrl+колесо</strong> - точный масштаб • <strong>Ctrl+0</strong> - сброс
        </div>
    </div>

    <!-- Легенда -->
    <div class="section">
        <div class="section-header">Легенда диаграммы</div>
        <div class="section-content">
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background: #fff9c4; border-color: #f57f17;"></div>
                    <span>Внешние входы</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffcdd2; border-color: #c62828;"></div>
                    <span>Конечные выходы</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffb74d; border-color: #ef6c00;"></div>
                    <span>Операции слияния</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ba68c8; border-color: #6a1b9a;"></div>
                    <span>Операции разветвления</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff4444; border-color: #000;"></div>
                    <span>Супер-критические операции</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #90caf9; border-color: #1565c0;"></div>
                    <span>Обычные операции</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Реестр операций -->
    <div class="section">
        <div class="section-header">Реестр операций</div>
        <div class="section-content">
            {create_simple_html_table(
                ["Операция"] + 
                (["Группа"] if available_cols['group'] else []) +
                (["Владелец"] if available_cols['owner'] else []) +
                ["Входы", "Выходы", "Тип узла"] +
                (["Описание"] if available_cols['detailed_desc'] else []),
                op_rows
            )}
        </div>
    </div>

    <!-- Реестр входов/выходов -->
    <div class="section">
        <div class="section-header">Входы и выходы системы</div>
        <div class="section-content">
            {create_simple_html_table(
                ["Элемент", "Источник", "Потребители"],
                io_rows
            )}
        </div>
    </div>

    <script>
        // Состояние навигации
        let scale = 1.0; // Начальный масштаб 100%
        let isDragging = false;
        let startX, startY, startScrollX, startScrollY;
        
        // Элементы DOM
        const diagramContainer = document.getElementById('diagramContainer');
        const mermaidElement = document.getElementById('mermaid-diagram');
        const zoomInfo = document.getElementById('zoomInfo');
        
        // Инициализация при загрузке
        document.addEventListener('DOMContentLoaded', function() {{
            // Инициализация Mermaid
            mermaid.initialize({{ 
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose',
                fontFamily: 'Arial, sans-serif',
                flowchart: {{
                    useMaxWidth: false,
                    htmlLabels: true,
                    curve: 'basis'
                }}
            }});
            
            // Переинициализация Mermaid для преобразования диаграммы
            mermaid.init(undefined, document.querySelectorAll('.mermaid')).then(() => {{
                // После рендеринга Mermaid подгоняем диаграмму под экран
                setTimeout(() => {{
                    fitToScreen();
                    setupNavigation();
                }}, 100);
            }});
        }});
        
        function setupNavigation() {{
            // Перетаскивание для панорамирования
            diagramContainer.addEventListener('mousedown', startDragging);
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', stopDragging);
            
            // Масштабирование колесом мыши
            diagramContainer.addEventListener('wheel', onWheel, {{ passive: false }});
            
            // Обработка клавиатуры
            document.addEventListener('keydown', onKeyDown);
        }}
        
        function startDragging(e) {{
            if (e.button === 0) {{ // Левая кнопка мыши
                isDragging = true;
                diagramContainer.classList.add('dragging');
                startX = e.clientX;
                startY = e.clientY;
                startScrollX = diagramContainer.scrollLeft;
                startScrollY = diagramContainer.scrollTop;
                e.preventDefault();
            }}
        }}
        
        function drag(e) {{
            if (!isDragging) return;
            
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            
            diagramContainer.scrollLeft = startScrollX - deltaX;
            diagramContainer.scrollTop = startScrollY - deltaY;
            
            e.preventDefault();
        }}
        
        function stopDragging() {{
            isDragging = false;
            diagramContainer.classList.remove('dragging');
        }}
        
        function onWheel(e) {{
            e.preventDefault();
            
            const rect = diagramContainer.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            // Сохраняем текущую позицию скролла
            const scrollX = diagramContainer.scrollLeft;
            const scrollY = diagramContainer.scrollTop;
            
            const delta = -Math.sign(e.deltaY) * (e.ctrlKey ? 0.05 : 0.1);
            const newScale = Math.max(0.1, Math.min(10, scale + delta));
            
            if (newScale !== scale) {{
                const oldScale = scale;
                scale = newScale;
                updateScale();
                updateZoomInfo();
                
                // Корректируем скролл для сохранения позиции под курсором
                const scaleRatio = newScale / oldScale;
                diagramContainer.scrollLeft = mouseX * scaleRatio - (mouseX - scrollX);
                diagramContainer.scrollTop = mouseY * scaleRatio - (mouseY - scrollY);
            }}
        }}
        
        function onKeyDown(e) {{
            // Горячие клавиши для масштабирования
            if ((e.ctrlKey || e.metaKey) && !e.altKey) {{
                if (e.key === '=' || e.key === '+') {{
                    e.preventDefault();
                    zoomIn();
                }} else if (e.key === '-') {{
                    e.preventDefault();
                    zoomOut();
                }} else if (e.key === '0') {{
                    e.preventDefault();
                    resetView();
                }}
            }}
            
            // Escape для выхода из режима перетаскивания
            if (e.key === 'Escape' && isDragging) {{
                stopDragging();
            }}
        }}
        
        function zoomIn() {{
            const rect = diagramContainer.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const scrollX = diagramContainer.scrollLeft;
            const scrollY = diagramContainer.scrollTop;
            
            const oldScale = scale;
            scale = Math.min(10, scale + 0.1);
            updateScale();
            updateZoomInfo();
            
            // Корректируем скролл для сохранения центра
            const scaleRatio = scale / oldScale;
            diagramContainer.scrollLeft = centerX * scaleRatio - (centerX - scrollX);
            diagramContainer.scrollTop = centerY * scaleRatio - (centerY - scrollY);
        }}
        
        function zoomOut() {{
            const rect = diagramContainer.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const scrollX = diagramContainer.scrollLeft;
            const scrollY = diagramContainer.scrollTop;
            
            const oldScale = scale;
            scale = Math.max(0.1, scale - 0.1);
            updateScale();
            updateZoomInfo();
            
            // Корректируем скролл для сохранения центра
            const scaleRatio = scale / oldScale;
            diagramContainer.scrollLeft = centerX * scaleRatio - (centerX - scrollX);
            diagramContainer.scrollTop = centerY * scaleRatio - (centerY - scrollY);
        }}
        
        function resetView() {{
            scale = 1.0;
            updateScale();
            updateZoomInfo();
            centerDiagram();
        }}
        
        function fitToScreen() {{
            const svg = mermaidElement.querySelector('svg');
            if (!svg) return;
            
            const container = diagramContainer;
            const svgRect = svg.getBoundingClientRect();
            const containerRect = container.getBoundingClientRect();
            
            // Вычисляем масштаб для вписывания диаграммы в контейнер
            const scaleX = containerRect.width / svgRect.width;
            const scaleY = containerRect.height / svgRect.height;
            const fitScale = Math.min(scaleX, scaleY) * 0.9; // 90% для отступов
            
            scale = Math.max(0.1, Math.min(1.0, fitScale)); // Ограничиваем сверху 100%
            updateScale();
            updateZoomInfo();
            centerDiagram();
        }}
        
        function centerDiagram() {{
            const svg = mermaidElement.querySelector('svg');
            if (!svg) return;
            
            const svgRect = svg.getBoundingClientRect();
            const container = diagramContainer;
            
            diagramContainer.scrollLeft = (svgRect.width * scale - container.clientWidth) / 2;
            diagramContainer.scrollTop = (svgRect.height * scale - container.clientHeight) / 2;
        }}
        
        function updateScale() {{
            const svg = mermaidElement.querySelector('svg');
            if (svg) {{
                svg.style.transform = `scale(${{scale}})`;
                svg.style.transformOrigin = '0 0';
            }}
        }}
        
        function updateZoomInfo() {{
            const percentage = Math.round(scale * 100);
            zoomInfo.textContent = `${{percentage}}%`;
        }}
        
        function downloadPNG() {{
            const svg = mermaidElement.querySelector('svg');
            if (!svg) {{
                alert('SVG элемент не найден');
                return;
            }}
            
            // Создаем временный контейнер для рендеринга
            const tempContainer = document.createElement('div');
            tempContainer.style.position = 'absolute';
            tempContainer.style.left = '-9999px';
            tempContainer.style.top = '-9999px';
            tempContainer.style.backgroundColor = 'white';
            tempContainer.style.padding = '40px';
            
            // Клонируем SVG и сбрасываем трансформацию для полного размера
            const clonedSvg = svg.cloneNode(true);
            clonedSvg.style.transform = 'scale(1)';
            clonedSvg.style.transformOrigin = '0 0';
            
            tempContainer.appendChild(clonedSvg);
            document.body.appendChild(tempContainer);
            
            html2canvas(tempContainer, {{
                backgroundColor: '#ffffff',
                scale: 2,
                useCORS: true,
                allowTaint: false,
                logging: false
            }}).then(canvas => {{
                const link = document.createElement('a');
                link.download = 'business_process_diagram.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
                document.body.removeChild(tempContainer);
            }}).catch(error => {{
                console.error('Ошибка при создании PNG:', error);
                document.body.removeChild(tempContainer);
                alert('Ошибка при создании PNG файла');
            }});
        }}
        
        // Обработка изменения размера окна
        window.addEventListener('resize', function() {{
            setTimeout(updateZoomInfo, 100);
        }});
    </script>
</body>
</html>'''

    output_file.write_text(html_content, encoding=ENCODING)

def export_html_mermaid(operations: Dict[str, Operation], analysis_data: AnalysisData, 
                       choices: Choices, available_columns: List[str], output_base: str = None) -> None:
    """
    Экспортирует диаграмму в упрощенный HTML с навигацией
    """
    if output_base is None:
        output_base = "business_process_diagram"
    
    output_file = Path(f"{output_base}.html")

    # Генерация Mermaid кода
    mermaid_code = build_mermaid_html(operations, analysis_data, choices)

    # Генерация упрощенного HTML отчета
    generate_simple_html_report(mermaid_code, analysis_data, operations, choices, available_columns, output_file)
    
    print(f"\n" + "="*60)
    print("✓ УПРОЩЕННЫЙ HTML-ОТЧЕТ С НАВИГАЦИЕЙ УСПЕШНО СОЗДАН!")
    print("="*60)
    print(f"Файл: {output_file}")
    print("🎯 ОСНОВНЫЕ ВОЗМОЖНОСТИ:")
    print("   • 🔍 Автоматическое вписывание в экран при открытии")
    print("   • 🖱️  Колесо мыши - масштабирование диаграммы (10% - 1000%)")
    print("   • 🖱️  ЛКМ + перетаскивание - панорамирование во всех направлениях")
    print("   • 📥  Экспорт в PNG в полном размере")
    print("   • 🎯  Кнопка 'Вместить' для автоматического подгона под экран")
    print("   • ⌨️  Горячие клавиши: Ctrl++/-/0, Escape для отмены перетаскивания")
    print(f"   • 📊 {analysis_data.analysis.operations_count} операций, {len(analysis_data.analysis.critical_points)} критических")