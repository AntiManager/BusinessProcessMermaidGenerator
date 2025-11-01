"""
Экспорт в HTML с улучшенным дизайном и полной аналитикой
"""
import json
from pathlib import Path
from typing import Dict, List
from models import Operation, Choices, AnalysisData
from exporters.mermaid_exporter import build_mermaid_html
from utils import safe_id, escape_text, clean_text
from config import ENCODING

def create_enhanced_html_table(headers: List[str], data: List[Dict[str, str]], table_id: str = "") -> str:
    """
    Создает улучшенную HTML таблицу с сортировкой
    """
    if not data:
        return "<p>Нет данных для отображения</p>"
    
    html = [f'<table class="sortable-table" id="{table_id}">']
    html.append('<thead><tr>')
    for header in headers:
        html.append(f'<th data-sort="{header}">{header} <span class="sort-icon">↕</span></th>')
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

def create_statistics_cards(analysis_data: AnalysisData, operations: Dict[str, Operation]) -> str:
    """
    Создает карточки со статистикой
    """
    analysis = analysis_data.analysis
    
    # Расчет сложности процесса
    complexity_score = calculate_complexity_score(operations, analysis_data)
    
    cards = [
        {
            'value': analysis.operations_count,
            'label': 'Всего операций',
            'icon': '📊',
            'class': 'stat-primary'
        },
        {
            'value': len(analysis.critical_points),
            'label': 'Критических точек',
            'icon': '⚠️',
            'class': 'stat-warning'
        },
        {
            'value': len(analysis.merge_points),
            'label': 'Точек слияния',
            'icon': '🔗',
            'class': 'stat-info'
        },
        {
            'value': len(analysis.split_points),
            'label': 'Точек разветвления',
            'icon': '🔀',
            'class': 'stat-info'
        },
        {
            'value': len(analysis.external_inputs),
            'label': 'Внешних входов',
            'icon': '📥',
            'class': 'stat-success'
        },
        {
            'value': len(analysis.final_outputs),
            'label': 'Конечных выходов',
            'icon': '📤',
            'class': 'stat-success'
        },
        {
            'value': f"{complexity_score}/10",
            'label': 'Сложность процесса',
            'icon': '🎯',
            'class': 'stat-complexity'
        }
    ]
    
    html = ['<div class="stats-grid">']
    for card in cards:
        html.append(f'''
            <div class="stat-card {card['class']}">
                <div class="stat-icon">{card['icon']}</div>
                <div class="stat-value">{card['value']}</div>
                <div class="stat-label">{card['label']}</div>
            </div>
        ''')
    html.append('</div>')
    return '\n'.join(html)

def calculate_complexity_score(operations: Dict[str, Operation], analysis_data: AnalysisData) -> int:
    """Рассчитать оценку сложности процесса от 1 до 10"""
    analysis = analysis_data.analysis
    
    # Весовые коэффициенты
    weights = {
        'operations': 0.3,
        'merge_points': 0.2,
        'split_points': 0.2,
        'critical_points': 0.3
    }
    
    # Нормализация значений (максимальные ожидаемые значения)
    max_operations = 50
    max_merge = 10
    max_split = 10
    max_critical = 5
    
    # Расчет нормализованных показателей
    op_score = min(len(operations) / max_operations, 1.0)
    merge_score = min(len(analysis.merge_points) / max_merge, 1.0)
    split_score = min(len(analysis.split_points) / max_split, 1.0)
    critical_score = min(len(analysis.critical_points) / max_critical, 1.0)
    
    # Общий счет
    total_score = (
        op_score * weights['operations'] +
        merge_score * weights['merge_points'] +
        split_score * weights['split_points'] +
        critical_score * weights['critical_points']
    )
    
    return min(10, int(total_score * 10) + 1)

def create_analysis_accordion(analysis_data: AnalysisData) -> str:
    """
    Создает аккордеон для аналитических разделов
    """
    analysis = analysis_data.analysis
    
    html = ['<div class="analysis-accordion">']
    
    # Супер-критические операции
    html.append('''
        <div class="accordion-item">
            <div class="accordion-header">
                <h3>⚠️ Супер-критические операции</h3>
                <span class="accordion-badge">{count}</span>
                <span class="accordion-toggle">▼</span>
            </div>
            <div class="accordion-content">
    '''.format(count=len(analysis.critical_points)))
    
    if analysis.critical_points:
        html.append('<div class="critical-list">')
        for cp in sorted(analysis.critical_points, key=lambda x: (x.inputs_count, x.output_reuse), reverse=True):
            html.append(f'''
                <div class="critical-item">
                    <strong>{cp.operation}</strong>
                    <div class="critical-stats">
                        <span class="stat-badge">{cp.inputs_count} входов</span>
                        <span class="stat-badge">{cp.output_reuse} использований выхода</span>
                    </div>
                </div>
            ''')
        html.append('</div>')
    else:
        html.append('<p class="no-data">Супер-критических операций не обнаружено</p>')
    html.append('</div></div>')
    
    # Точки слияния
    html.append('''
        <div class="accordion-item">
            <div class="accordion-header">
                <h3>🔗 Точки слияния</h3>
                <span class="accordion-badge">{count}</span>
                <span class="accordion-toggle">▼</span>
            </div>
            <div class="accordion-content">
    '''.format(count=len(analysis.merge_points)))
    
    if analysis.merge_points:
        html.append('<div class="merge-list">')
        for mp in sorted(analysis.merge_points, key=lambda x: x.input_count, reverse=True):
            html.append(f'''
                <div class="merge-item">
                    <strong>{mp.operation}</strong>
                    <span class="merge-count">{mp.input_count} входов</span>
                </div>
            ''')
        html.append('</div>')
    else:
        html.append('<p class="no-data">Точек слияния не обнаружено</p>')
    html.append('</div></div>')
    
    # Точки разветвления
    html.append('''
        <div class="accordion-item">
            <div class="accordion-header">
                <h3>🔀 Точки разветвления</h3>
                <span class="accordion-badge">{count}</span>
                <span class="accordion-toggle">▼</span>
            </div>
            <div class="accordion-content">
    '''.format(count=len(analysis.split_points)))
    
    if analysis.split_points:
        html.append('<div class="split-list">')
        for sp in sorted(analysis.split_points, key=lambda x: x.target_count, reverse=True):
            html.append(f'''
                <div class="split-item">
                    <strong>{sp.output}</strong>
                    <div class="split-details">
                        <span>из {sp.source_operation}</span>
                        <span class="split-count">→ {sp.target_count} операций</span>
                    </div>
                </div>
            ''')
        html.append('</div>')
    else:
        html.append('<p class="no-data">Точек разветвления не обнаружено</p>')
    html.append('</div></div>')
    
    html.append('</div>')  # закрываем analysis-accordion
    return '\n'.join(html)

def generate_enhanced_html_report(mermaid_code: str, analysis_data: AnalysisData, operations: Dict[str, Operation], 
                                 choices: Choices, available_columns: List[str], output_file: Path) -> None:
    """
    Генерирует улучшенный HTML отчет с полной аналитикой
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
        
        if 'Группа' in available_columns:
            row_data["Группа"] = op.group
        if 'Владелец' in available_columns:
            row_data["Владелец"] = op.owner
        if 'Подробное описание операции' in available_columns:
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
    <title>Диаграмма бизнес-процесса - Полный анализ</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {{
            --primary-color: #007cba;
            --warning-color: #ff6b35;
            --success-color: #28a745;
            --info-color: #17a2b8;
            --complexity-color: #6f42c1;
            --text-color: #333;
            --border-color: #ddd;
            --bg-light: #f8f9fa;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background: #fff;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Навигация */
        .report-nav {{
            background: white;
            padding: 15px 20px;
            border-bottom: 3px solid var(--primary-color);
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        
        .nav-link {{
            padding: 8px 16px;
            text-decoration: none;
            color: var(--text-color);
            border-radius: 5px;
            transition: all 0.3s ease;
            font-weight: 500;
        }}
        
        .nav-link:hover {{
            background: var(--primary-color);
            color: white;
        }}
        
        /* Заголовки */
        .section {{
            margin: 30px 0;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .section h2 {{
            color: var(--primary-color);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-color);
        }}
        
        /* Карточки статистики */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary-color);
        }}
        
        .stat-card.stat-warning {{ border-left-color: var(--warning-color); }}
        .stat-card.stat-success {{ border-left-color: var(--success-color); }}
        .stat-card.stat-info {{ border-left-color: var(--info-color); }}
        .stat-card.stat-complexity {{ border-left-color: var(--complexity-color); }}
        
        .stat-icon {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        /* Аккордеон анализа */
        .analysis-accordion {{
            margin: 20px 0;
        }}
        
        .accordion-item {{
            border: 1px solid var(--border-color);
            border-radius: 5px;
            margin-bottom: 10px;
            overflow: hidden;
        }}
        
        .accordion-header {{
            background: var(--bg-light);
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s ease;
        }}
        
        .accordion-header:hover {{
            background: #e9ecef;
        }}
        
        .accordion-header h3 {{
            margin: 0;
            font-size: 1.1em;
        }}
        
        .accordion-badge {{
            background: var(--primary-color);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }}
        
        .accordion-toggle {{
            transition: transform 0.3s ease;
        }}
        
        .accordion-item.active .accordion-toggle {{
            transform: rotate(180deg);
        }}
        
        .accordion-content {{
            padding: 0;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease, padding 0.3s ease;
        }}
        
        .accordion-item.active .accordion-content {{
            padding: 20px;
            max-height: 1000px;
        }}
        
        /* Списки элементов */
        .critical-list, .merge-list, .split-list {{
            display: grid;
            gap: 10px;
        }}
        
        .critical-item, .merge-item, .split-item {{
            padding: 15px;
            background: var(--bg-light);
            border-radius: 5px;
            border-left: 4px solid var(--warning-color);
        }}
        
        .merge-item {{ border-left-color: var(--info-color); }}
        .split-item {{ border-left-color: var(--info-color); }}
        
        .critical-stats {{
            margin-top: 8px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .stat-badge {{
            background: var(--warning-color);
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
        }}
        
        .merge-count, .split-count {{
            background: var(--info-color);
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        
        .split-details {{
            margin-top: 5px;
            color: #666;
            font-size: 0.9em;
        }}
        
        .no-data {{
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 20px;
        }}
        
        /* Диаграмма */
        .diagram-section {{
            margin: 30px 0;
        }}
        
        .diagram-container {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            background: white;
            position: relative;
            overflow: auto;
            min-height: 400px;
        }}
        
        .mermaid-controls {{
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 100;
            display: flex;
            gap: 5px;
            background: white;
            padding: 5px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .mermaid-controls button {{
            padding: 5px 10px;
            border: 1px solid var(--border-color);
            background: white;
            border-radius: 3px;
            cursor: pointer;
        }}
        
        .mermaid-controls button:hover {{
            background: var(--bg-light);
        }}
        
        /* Таблицы */
        .table-section {{
            margin: 20px 0;
        }}
        
        .sortable-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        
        .sortable-table th {{
            background: var(--primary-color);
            color: white;
            padding: 12px;
            text-align: left;
            cursor: pointer;
            position: relative;
        }}
        
        .sortable-table th:hover {{
            background: #005a87;
        }}
        
        .sort-icon {{
            margin-left: 5px;
            font-size: 0.8em;
        }}
        
        .sortable-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .sortable-table tr:hover {{
            background: var(--bg-light);
        }}
        
        /* Легенда */
        .legend-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px;
            background: var(--bg-light);
            border-radius: 5px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            border: 1px solid #ccc;
        }}
        
        /* Адаптивность */
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }}
            
            .report-nav {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .nav-link {{
                text-align: center;
            }}
            
            .mermaid-controls {{
                position: relative;
                top: 0;
                right: 0;
                justify-content: center;
                margin-bottom: 10px;
            }}
        }}
    </style>
</head>
<body>
    <nav class="report-nav">
        <a href="#overview" class="nav-link">📊 Обзор</a>
        <a href="#diagram" class="nav-link">🔍 Диаграмма</a>
        <a href="#analysis" class="nav-link">📈 Анализ</a>
        <a href="#registry" class="nav-link">📋 Реестры</a>
        <a href="#statistics" class="nav-link">📊 Статистика</a>
        <a href="#legend" class="nav-link">🎨 Легенда</a>
    </nav>

    <div class="container">
        <!-- Секция обзора -->
        <section id="overview" class="section">
            <h2>📊 Обзор бизнес-процесса</h2>
            {create_statistics_cards(analysis_data, operations)}
        </section>

        <!-- Секция диаграммы -->
        <section id="diagram" class="section">
            <h2>🔍 Визуальная диаграмма процесса</h2>
            <div class="diagram-container">
                <div class="mermaid-controls">
                    <button id="zoomInBtn">🔍 +</button>
                    <button id="zoomOutBtn">🔍 -</button>
                    <button id="resetZoomBtn">🗘 Сброс</button>
                    <button id="fitToScreenBtn">📐 Вместить</button>
                </div>
                <div class="mermaid" id="mermaid-diagram">
{mermaid_code}
                </div>
            </div>
        </section>

        <!-- Секция анализа -->
        <section id="analysis" class="section">
            <h2>📈 Анализ критических точек</h2>
            {create_analysis_accordion(analysis_data)}
        </section>

        <!-- Секция реестров -->
        <section id="registry" class="section">
            <h2>📋 Реестры операций и связей</h2>
            
            <div class="table-section">
                <h3>Операции процесса</h3>
                {create_enhanced_html_table(
                    ["Операция"] + 
                    (["Группа"] if available_cols['group'] else []) +
                    (["Владелец"] if available_cols['owner'] else []) +
                    ["Входы", "Выходы", "Тип узла"] +
                    (["Описание"] if available_cols['detailed_desc'] else []),
                    op_rows, "operations-table"
                )}
            </div>

            <div class="table-section">
                <h3>Входы и выходы системы</h3>
                {create_enhanced_html_table(
                    ["Элемент", "Источник", "Потребители"],
                    io_rows, "io-table"
                )}
            </div>
        </section>

        <!-- Секция статистики -->
        <section id="statistics" class="section">
            <h2>📊 Детальная статистика</h2>
            <div class="stats-details">
                <div class="stat-item">
                    <strong>Общая статистика:</strong>
                    <ul>
                        <li>Всего операций: {analysis.operations_count}</li>
                        <li>Внешние входы: {len(analysis.external_inputs)}</li>
                        <li>Конечные выходы: {len(analysis.final_outputs)}</li>
                    </ul>
                </div>
                <div class="stat-item">
                    <strong>Анализ сложности:</strong>
                    <ul>
                        <li>Операций слияния: {len(analysis.merge_points)}</li>
                        <li>Операций разветвления: {len(analysis.split_points)}</li>
                        <li>Супер-критических операций: {len(analysis.critical_points)}</li>
                    </ul>
                </div>
            </div>
        </section>

        <!-- Секция легенды -->
        <section id="legend" class="section">
            <h2>🎨 Легенда диаграммы</h2>
            <div class="legend-grid">
                <div class="legend-item">
                    <div class="legend-color" style="background: yellow;"></div>
                    <span>Желтые овалы - внешние входы</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: red;"></div>
                    <span>Красные овалы - конечные выходы</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: orange;"></div>
                    <span>Оранжевые прямоугольники - операции слияния</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: purple;"></div>
                    <span>Фиолетовые прямоугольники - операции разветвления</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff4444;"></div>
                    <span>Пульсирующие красные - супер-критические операции</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #007cba;"></div>
                    <span>Синие прямоугольники - стандартные операции</span>
                </div>
            </div>
        </section>
    </div>

    <script>
        // Глобальные переменные для управления диаграммой
        let diagramScale = 1.0;
        let mermaidElement = null;
        let diagramContainer = null;

        // Инициализация при загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('DOM loaded, initializing...');
            
            // Инициализация Mermaid
            mermaid.initialize({{ 
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose'
            }});
            
            // Активируем первую секцию аккордеона
            const firstAccordion = document.querySelector('.accordion-item');
            if (firstAccordion) {{
                firstAccordion.classList.add('active');
            }}
            
            // Инициализация элементов управления диаграммой
            initDiagramControls();
            
            // Инициализация навигации и сортировки
            initNavigation();
            initTableSorting();
        }});

        function initDiagramControls() {{
            console.log('Initializing diagram controls...');
            
            mermaidElement = document.getElementById('mermaid-diagram');
            diagramContainer = document.querySelector('.diagram-container');
            
            if (!mermaidElement) {{
                console.error('Mermaid diagram element not found');
                return;
            }}
            
            if (!diagramContainer) {{
                console.error('Diagram container not found');
                return;
            }}
            
            // Назначаем обработчики кнопок
            document.getElementById('zoomInBtn').addEventListener('click', zoomIn);
            document.getElementById('zoomOutBtn').addEventListener('click', zoomOut);
            document.getElementById('resetZoomBtn').addEventListener('click', resetZoom);
            document.getElementById('fitToScreenBtn').addEventListener('click', fitToScreen);
            
            console.log('Diagram controls initialized');
            
            // Автоматически подгоняем диаграмму после загрузки
            setTimeout(fitToScreen, 1000);
        }}

        function zoomIn() {{
            if (!mermaidElement) return;
            diagramScale = Math.min(3.0, diagramScale + 0.1);
            updateDiagramScale();
        }}
        
        function zoomOut() {{
            if (!mermaidElement) return;
            diagramScale = Math.max(0.3, diagramScale - 0.1);
            updateDiagramScale();
        }}
        
        function resetZoom() {{
            if (!mermaidElement) return;
            diagramScale = 1.0;
            updateDiagramScale();
            // Сброс скролла к центру
            setTimeout(() => {{
                if (diagramContainer) {{
                    diagramContainer.scrollLeft = (diagramContainer.scrollWidth - diagramContainer.clientWidth) / 2;
                    diagramContainer.scrollTop = (diagramContainer.scrollHeight - diagramContainer.clientHeight) / 2;
                }}
            }}, 100);
        }}
        
        function fitToScreen() {{
            if (!mermaidElement || !diagramContainer) return;
            
            const svg = mermaidElement.querySelector('svg');
            if (!svg) {{
                console.warn('SVG element not found in mermaid diagram');
                return;
            }}
            
            const containerWidth = diagramContainer.clientWidth - 40;
            const containerHeight = diagramContainer.clientHeight - 40;
            const svgWidth = svg.getBoundingClientRect().width;
            const svgHeight = svg.getBoundingClientRect().height;
            
            if (svgWidth === 0 || svgHeight === 0) {{
                console.warn('SVG dimensions are zero, retrying...');
                setTimeout(fitToScreen, 500);
                return;
            }}
            
            const scaleX = containerWidth / svgWidth;
            const scaleY = containerHeight / svgHeight;
            diagramScale = Math.min(scaleX, scaleY, 1.0);
            updateDiagramScale();
            
            // Центрируем диаграмму после подгонки
            setTimeout(() => {{
                if (diagramContainer) {{
                    diagramContainer.scrollLeft = (diagramContainer.scrollWidth - diagramContainer.clientWidth) / 2;
                    diagramContainer.scrollTop = (diagramContainer.scrollHeight - diagramContainer.clientHeight) / 2;
                }}
            }}, 100);
        }}
        
        function updateDiagramScale() {{
            if (!mermaidElement) return;
            mermaidElement.style.transform = 'scale(' + diagramScale + ')';
            mermaidElement.style.transformOrigin = '0 0';
            console.log('Diagram scale updated to: ' + diagramScale);
        }}
        
        function initNavigation() {{
            // Плавная прокрутка для навигации
            document.querySelectorAll('.nav-link').forEach(link => {{
                link.addEventListener('click', (e) => {{
                    e.preventDefault();
                    const targetId = link.getAttribute('href').substring(1);
                    const targetSection = document.getElementById(targetId);
                    if (targetSection) {{
                        targetSection.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'start'
                        }});
                    }}
                }});
            }});
            
            // Аккордеон
            document.querySelectorAll('.accordion-header').forEach(header => {{
                header.addEventListener('click', () => {{
                    const item = header.parentElement;
                    item.classList.toggle('active');
                }});
            }});
        }}
        
        function initTableSorting() {{
            // Сортировка таблиц
            document.querySelectorAll('.sortable-table th').forEach(header => {{
                header.addEventListener('click', () => {{
                    const table = header.closest('table');
                    const columnIndex = Array.from(header.parentElement.children).indexOf(header);
                    sortTable(table, columnIndex);
                }});
            }});
        }}
        
        function sortTable(table, columnIndex) {{
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Проверяем, являются ли данные числовыми
            const isNumeric = rows.every(row => {{
                const cell = row.children[columnIndex];
                const text = cell.textContent.trim();
                return !isNaN(parseFloat(text)) && isFinite(text);
            }});
            
            rows.sort((a, b) => {{
                const aVal = a.children[columnIndex].textContent.trim();
                const bVal = b.children[columnIndex].textContent.trim();
                
                if (isNumeric) {{
                    return parseFloat(aVal) - parseFloat(bVal);
                }} else {{
                    return aVal.localeCompare(bVal, 'ru');
                }}
            }});
            
            // Удаляем старые строки и добавляем отсортированные
            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
        }}

        // Обработка клавиатуры для масштабирования
        document.addEventListener('keydown', (e) => {{
            if ((e.ctrlKey || e.metaKey) && !e.altKey) {{
                if (e.key === '=' || e.key === '+') {{
                    e.preventDefault();
                    zoomIn();
                }} else if (e.key === '-') {{
                    e.preventDefault();
                    zoomOut();
                }} else if (e.key === '0') {{
                    e.preventDefault();
                    resetZoom();
                }} else if (e.key === '1') {{
                    e.preventDefault();
                    fitToScreen();
                }}
            }}
        }});
    </script>
</body>
</html>'''

    output_file.write_text(html_content, encoding=ENCODING)

def export_html_mermaid(operations: Dict[str, Operation], analysis_data: AnalysisData, 
                       choices: Choices, available_columns: List[str], output_base: str = None) -> None:
    """
    Экспортирует диаграмму в улучшенный HTML с полной аналитикой
    """
    if output_base is None:
        output_base = "business_process_diagram"
    
    output_file = Path(f"{output_base}.html")

    # Генерация Mermaid кода
    mermaid_code = build_mermaid_html(operations, analysis_data, choices)

    # Генерация улучшенного HTML отчета
    generate_enhanced_html_report(mermaid_code, analysis_data, operations, choices, available_columns, output_file)
    
    print(f"\n" + "="*60)
    print("✓ УЛУЧШЕННЫЙ HTML-ОТЧЕТ УСПЕШНО СОЗДАН!")
    print("="*60)
    print(f"Файл: {output_file}")
    print(f"Статистика: {analysis_data.analysis.operations_count} операций")
    print(f"Сложность процесса: {calculate_complexity_score(operations, analysis_data)}/10")