"""
Экспорт в HTML с минималистичной визуализацией Mermaid диаграмм
"""
import json
from pathlib import Path
from typing import Dict, List
from models import Operation, Choices, AnalysisData
from utils import safe_id, escape_text, clean_text
from config import ENCODING

def create_simple_table(headers: List[str], data: List[Dict[str, str]]) -> str:
    """
    Создает минималистичную HTML таблицу
    """
    if not data:
        return "<p>Нет данных для отображения</p>"
    
    html = ['<table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px;">']
    html.append('<thead><tr>')
    for header in headers:
        html.append(f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left; background: #f9f9f9;">{header}</th>')
    html.append('</tr></thead>')
    html.append('<tbody>')
    for i, row in enumerate(data):
        bg_color = '#f9f9f9' if i % 2 == 0 else '#fff'
        html.append(f'<tr style="background: {bg_color};">')
        for header in headers:
            value = str(row.get(header, ""))
            value = value.replace('\n', '<br>')
            html.append(f'<td style="border: 1px solid #ddd; padding: 8px;">{value}</td>')
        html.append('</tr>')
    html.append('</tbody></table>')
    return '\n'.join(html)

def generate_minimal_html_report(mermaid_code: str, analysis_data: AnalysisData, operations: Dict[str, Operation], 
                               choices: Choices, available_columns: List[str], output_file: Path) -> None:
    """
    Генерирует минималистичный HTML отчет с акцентом на диаграмму
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

    # Генерация HTML для критических операций
    critical_ops_html = ""
    if analysis.critical_points:
        critical_items = []
        for cp in sorted(analysis.critical_points, key=lambda x: (x.inputs_count, x.output_reuse), reverse=True):
            critical_items.append(f'''
                <div class="critical-item">
                    <strong>{cp.operation}</strong><br>
                    {cp.inputs_count} входов, выход используется в {cp.output_reuse} операциях
                </div>
            ''')
        critical_ops_html = f'''
            <div class="section">
                <h2 class="section-header">Критические операции</h2>
                {''.join(critical_items)}
            </div>
        '''

    html_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Диаграмма бизнес-процесса</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11.0.1/dist/mermaid.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.5;
            color: #333;
            background: #fff;
            padding: 0;
        }}
        
        .container {{
            max-width: 100%;
            margin: 0;
            padding: 0;
        }}
        
        /* Секция диаграммы - ПЕРВАЯ И ГЛАВНАЯ */
        .diagram-section {{
            background: #fff;
            border-bottom: 1px solid #e1e5e9;
            margin: 0;
        }}
        
        .diagram-header {{
            background: #f8f9fa;
            padding: 12px 20px;
            border-bottom: 1px solid #e1e5e9;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .diagram-controls {{
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .control-btn {{
            background: #6c757d;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        }}
        
        .control-btn:hover {{
            background: #5a6268;
        }}
        
        .download-btn {{
            background: #28a745;
        }}
        
        .download-btn:hover {{
            background: #218838;
        }}
        
        .zoom-info {{
            background: #fff;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            min-width: 60px;
            text-align: center;
            border: 1px solid #ddd;
        }}
        
        .diagram-container {{
            width: 100%;
            height: 75vh;
            min-height: 500px;
            overflow: auto;
            background: #fafafa;
            cursor: grab;
        }}
        
        .diagram-container.dragging {{
            cursor: grabbing;
        }}
        
        #mermaid-diagram {{
            padding: 30px;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100%;
        }}
        
        /* Минималистичные стили Mermaid */
        .mermaid {{
            text-align: center;
        }}
        
        .mermaid .node rect {{
            stroke-width: 1.5px;
            rx: 4px;
            ry: 4px;
        }}
        
        /* Секции с таблицами - ПОСЛЕ ДИАГРАММЫ */
        .content-section {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 20px;
        }}
        
        .section {{
            margin: 0 0 30px 0;
            background: #fff;
        }}
        
        .section-header {{
            font-size: 1.4em;
            font-weight: 600;
            margin: 0 0 15px 0;
            padding: 0 0 10px 0;
            border-bottom: 2px solid #e1e5e9;
            color: #2c3e50;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        
        .stat-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        
        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
            display: block;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 5px;
        }}
        
        .nav-hint {{
            font-size: 0.8em;
            color: #6c757d;
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-top: 1px solid #e1e5e9;
        }}
        
        .critical-item {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            margin: 8px 0;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .diagram-controls {{
                justify-content: center;
            }}
            
            .diagram-container {{
                height: 60vh;
                padding: 15px;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .content-section {{
                padding: 20px 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- ДИАГРАММА - ПЕРВАЯ И ГЛАВНАЯ -->
        <div class="diagram-section">
            <div class="diagram-header">
                <div style="font-weight: 600; color: #2c3e50;">Диаграмма бизнес-процесса</div>
                <div class="diagram-controls">
                    <button class="control-btn" onclick="zoomOut()" title="Уменьшить">−</button>
                    <div class="zoom-info" id="zoomInfo">100%</div>
                    <button class="control-btn" onclick="zoomIn()" title="Увеличить">+</button>
                    <button class="control-btn" onclick="resetView()" title="Сбросить вид">Сброс</button>
                    <button class="control-btn" onclick="fitToScreen()" title="Вместить в экран">Вместить</button>
                    <button class="control-btn download-btn" onclick="downloadPNG()" title="Скачать PNG">PNG</button>
                </div>
            </div>
            <div class="diagram-container" id="diagramContainer">
                <div class="mermaid" id="mermaid-diagram">
{mermaid_code}
                </div>
            </div>
            <div class="nav-hint">
                Колесо мыши - масштаб • ЛКМ + перетаскивание - навигация • Ctrl+колесо - точный масштаб
            </div>
        </div>

        <!-- СТАТИСТИКА И АНАЛИЗ -->
        <div class="content-section">
            <div class="section">
                <h2 class="section-header">Статистика процесса</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-value">{analysis.operations_count}</span>
                        <span class="stat-label">Операций</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{len(analysis.external_inputs)}</span>
                        <span class="stat-label">Внешние входы</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{len(analysis.final_outputs)}</span>
                        <span class="stat-label">Конечные выходы</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{len(analysis.critical_points)}</span>
                        <span class="stat-label">Критические операции</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{len(analysis.merge_points)}</span>
                        <span class="stat-label">Точек слияния</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{len(analysis.split_points)}</span>
                        <span class="stat-label">Точек разветвления</span>
                    </div>
                </div>
            </div>

            <!-- Критические операции -->
            {critical_ops_html}

            <!-- Реестр операций -->
            <div class="section">
                <h2 class="section-header">Реестр операций</h2>
                {create_simple_table(
                    ["Операция"] + 
                    (["Группа"] if available_cols['group'] else []) +
                    (["Владелец"] if available_cols['owner'] else []) +
                    ["Входы", "Выходы", "Тип узла"] +
                    (["Описание"] if available_cols['detailed_desc'] else []),
                    op_rows
                )}
            </div>

            <!-- Реестр входов/выходов -->
            <div class="section">
                <h2 class="section-header">Входы и выходы системы</h2>
                {create_simple_table(
                    ["Элемент", "Источник", "Потребители"],
                    io_rows
                )}
            </div>
        </div>
    </div>

    <script>
        // Минималистичная конфигурация Mermaid
        const mermaidConfig = {{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            fontFamily: 'Arial, sans-serif',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis',
                padding: 15,
                rankSpacing: 40,
                nodeSpacing: 80,
                rankSep: 80,
                wrap: true,
                wrappingWidth: 150
            }}
        }};

        // Состояние навигации
        let scale = 1.0;
        let isDragging = false;
        let startX, startY, startScrollX, startScrollY;
        
        // Элементы DOM
        const diagramContainer = document.getElementById('diagramContainer');
        const mermaidElement = document.getElementById('mermaid-diagram');
        const zoomInfo = document.getElementById('zoomInfo');
        
        // Инициализация при загрузке
        document.addEventListener('DOMContentLoaded', async function() {{
            // Инициализация Mermaid
            mermaid.initialize(mermaidConfig);
            
            try {{
                // Переинициализация Mermaid для преобразования диаграммы
                await mermaid.run({{ querySelector: '.mermaid' }});
                
                // После рендеринга Mermaid подгоняем диаграмму под экран
                setTimeout(() => {{
                    fitToScreen();
                    setupNavigation();
                }}, 100);
                
            }} catch (error) {{
                console.error('Ошибка рендеринга Mermaid:', error);
            }}
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
            const newScale = Math.max(0.1, Math.min(10, scale + delta)); // УВЕЛИЧЕНО ДО 1000%
            
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
                }} else if (e.key === '1') {{
                    e.preventDefault();
                    fitToScreen();
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
            scale = Math.min(10, scale + 0.1); // УВЕЛИЧЕНО ДО 1000%
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
            const fitScale = Math.min(scaleX, scaleY) * 0.9;
            
            scale = Math.max(0.1, Math.min(1.0, fitScale));
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
            tempContainer.style.padding = '30px';
            
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
    Экспортирует диаграмму в минималистичный HTML с акцентом на диаграмму
    """
    if output_base is None:
        output_base = "business_process_diagram"
    
    output_file = Path(f"{output_base}.html")

    # Генерация Mermaid кода
    from exporters.mermaid_exporter import build_mermaid_html
    mermaid_code = build_mermaid_html(operations, analysis_data, choices)

    # Генерация минималистичного HTML отчета
    generate_minimal_html_report(mermaid_code, analysis_data, operations, choices, available_columns, output_file)
    
    print(f"\n" + "="*60)
    print("✓ МИНИМАЛИСТИЧНЫЙ HTML-ОТЧЕТ СОЗДАН!")
    print("="*60)
    print(f"Файл: {output_file}")
    print("🎯 ОСОБЕННОСТИ:")
    print("   • 🎯 Диаграмма на первом месте - сразу при открытии")
    print("   • 🎨 Минималистичный дизайн как в Markdown")
    print("   • 🔍 Увеличенный масштаб до 1000% для больших процессов")
    print("   • 📊 Чистая статистика после диаграммы")
    print("   • 🖱️  Простая навигация без избыточных элементов")
    print(f"   • 📈 {analysis_data.analysis.operations_count} операций, {len(analysis_data.analysis.critical_points)} критических")