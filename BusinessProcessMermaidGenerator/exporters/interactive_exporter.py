"""
Экспорт в интерактивный HTML граф
"""
import json
from pathlib import Path
from typing import Dict, Any, Set
from models import Operation, Choices, AnalysisData
from utils import safe_id
from config import ENCODING

def build_interactive_html_data(
    operations: Dict[str, Operation],
    analysis_data: AnalysisData,
) -> Dict[str, Any]:
    """
    Строит структуру данных для интерактивного HTML-графа
    """
    external_inputs = analysis_data.external_inputs
    final_outputs = analysis_data.final_outputs
    analysis = analysis_data.analysis
    
    nodes = []
    edges = []
    
    # Добавляем внешние входы
    for inp in sorted(external_inputs):
        if inp:
            nodes.append({
                "id": safe_id(inp),
                "label": inp,
                "type": "external",
                "shape": "ellipse",
                "color": {"background": "#fff9c4", "border": "#f57f17"},
                "font": {"size": 14}
            })
    
    # Добавляем конечные выходы
    for out in sorted(final_outputs):
        if out:
            nodes.append({
                "id": safe_id(out),
                "label": out,
                "type": "final", 
                "shape": "ellipse",
                "color": {"background": "#ffcdd2", "border": "#c62828"},
                "font": {"size": 14, "color": "#ffffff"}
            })
    
    # Создаем mapping от входа к операциям, которые его используют
    from collections import defaultdict
    input_to_operations = defaultdict(list)
    for name, op in operations.items():
        for inp in op.inputs:
            if inp:
                input_to_operations[inp].append(name)
    
    # Добавляем операции
    critical_ops = {c.operation for c in analysis.critical_points}
    
    for name, op in operations.items():
        is_merge = len(op.inputs) > 1
        is_split = any(len(input_to_operations.get(out, [])) > 1 for out in op.outputs)
        
        node_type = "critical" if name in critical_ops else (
            "merge_split" if is_merge and is_split else
            "merge" if is_merge else
            "split" if is_split else
            "normal"
        )
        
        # Определяем цвет в зависимости от типа узла
        color_config = {
            "critical": {"background": "#ff4444", "border": "#000000", "font": {"color": "#ffffff"}},
            "merge": {"background": "#ffb74d", "border": "#ef6c00"},
            "split": {"background": "#ba68c8", "border": "#6a1b9a", "font": {"color": "#ffffff"}},
            "merge_split": {"background": "#ff8a65", "border": "#d84315"},
            "normal": {"background": "#90caf9", "border": "#1565c0"}
        }
        
        color = color_config.get(node_type, color_config["normal"])
        
        nodes.append({
            "id": safe_id(name),
            "label": name,  # В интерактивном графе показываем только название
            "type": node_type,
            "shape": "box",
            "color": color,
            "font": {"size": 14},
            "title": f"<b>{name}</b><br>{op.detailed}" if op.detailed else name,
            "group": op.group,
            "owner": op.owner,
            "detailed": op.detailed
        })
    
    # Добавляем связи
    added_edges = set()
    
    for name, op in operations.items():
        src_id = safe_id(name)
        
        # Связи от операций к конечным выходам
        for output in op.outputs:
            if output and output in final_outputs:
                edge_id = f"{src_id}-{safe_id(output)}"
                if edge_id not in added_edges:
                    added_edges.add(edge_id)
                    edges.append({
                        "from": src_id,
                        "to": safe_id(output),
                        "label": output,
                        "arrows": "to"
                    })
            
            # Связи между операциями
            if output in input_to_operations:
                for target_op in input_to_operations[output]:
                    edge_id = f"{src_id}-{safe_id(target_op)}"
                    if edge_id not in added_edges:
                        added_edges.add(edge_id)
                        edges.append({
                            "from": src_id,
                            "to": safe_id(target_op),
                            "label": output,
                            "arrows": "to"
                        })
        
        # Связи от внешних входов к операциям
        for inp in op.inputs:
            if not inp:
                continue
            if inp in external_inputs:
                edge_id = f"{safe_id(inp)}-{src_id}"
                if edge_id not in added_edges:
                    added_edges.add(edge_id)
                    edges.append({
                        "from": safe_id(inp),
                        "to": src_id,
                        "label": inp,
                        "arrows": "to"
                    })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "statistics": {
            "operations_count": analysis.operations_count,
            "external_inputs": len(analysis.external_inputs),
            "final_outputs": len(analysis.final_outputs),
            "merge_points": len(analysis.merge_points),
            "split_points": len(analysis.split_points),
            "critical_points": len(analysis.critical_points)
        },
        "critical_operations": [
            {
                "operation": cp.operation,
                "inputs_count": cp.inputs_count,
                "output_reuse": cp.output_reuse
            }
            for cp in analysis.critical_points
        ]
    }

def generate_interactive_html_file(html_data: Dict[str, Any], output_file: Path) -> None:
    """
    Генерирует HTML-файл с интерактивной диаграммой на vis-network
    """
    
    html_template = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Диаграмма бизнес-процесса</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }
        .container {
            display: flex;
            height: 100vh;
        }
        .sidebar {
            width: 300px;
            background: white;
            border-right: 1px solid #ddd;
            padding: 20px;
            overflow-y: auto;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
        }
        .diagram {
            flex: 1;
            background: white;
        }
        .statistics {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .stat-item {
            margin: 5px 0;
            font-size: 14px;
        }
        .critical-list {
            background: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border: 1px solid #ffeaa7;
        }
        .controls {
            margin: 15px 0;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 15px;
            margin: 2px;
            border-radius: 3px;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
        .node-info {
            background: white;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #ddd;
            margin-top: 20px;
        }
        h1, h2, h3 {
            color: #333;
            margin-top: 0;
        }
        #network {
            width: 100%;
            height: 100%;
            border: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h1>Бизнес-процесс</h1>
            
            <div class="statistics">
                <h3>Статистика</h3>
                <div class="stat-item">Операций: <strong id="stats-operations">0</strong></div>
                <div class="stat-item">Внешние входы: <strong id="stats-inputs">0</strong></div>
                <div class="stat-item">Конечные выходы: <strong id="stats-outputs">0</strong></div>
                <div class="stat-item">Точек слияния: <strong id="stats-merge">0</strong></div>
                <div class="stat-item">Точек разветвления: <strong id="stats-split">0</strong></div>
                <div class="stat-item">Критических операций: <strong id="stats-critical">0</strong></div>
            </div>

            <div class="critical-list" id="critical-section">
                <h3>Критические операции</h3>
                <div id="critical-list"></div>
            </div>

            <div class="controls">
                <h3>Управление</h3>
                <button onclick="fitToScreen()">Вписать в экран</button>
                <button onclick="resetZoom()">Сбросить масштаб</button>
                <button onclick="togglePhysics()">Физика: Вкл</button>
            </div>

            <div class="node-info">
                <h3>Информация</h3>
                <div id="node-info">Выберите элемент на диаграмме</div>
            </div>
        </div>

        <div class="diagram">
            <div id="network"></div>
        </div>
    </div>

    <script>
        // Данные диаграммы
        const diagramData = {DIAGRAM_DATA};

        // Инициализация сети
        let network = null;
        let physicsEnabled = true;

        function initNetwork() {
            const container = document.getElementById('network');
            const data = {
                nodes: new vis.DataSet(diagramData.nodes.map(node => ({
                    id: node.id,
                    label: node.label,
                    shape: node.shape,
                    color: node.color,
                    borderWidth: 2,
                    font: node.font,
                    shadow: true,
                    title: getNodeTooltip(node)
                }))),
                edges: new vis.DataSet(diagramData.edges.map(edge => ({
                    from: edge.from,
                    to: edge.to,
                    label: edge.label,
                    arrows: 'to',
                    font: { size: 12, align: 'middle' },
                    width: 2,
                    smooth: { enabled: true, type: 'dynamic' }
                })))
            };

            const options = {
                layout: {
                    improvedLayout: true,
                    hierarchical: {
                        enabled: false,
                        direction: 'LR',
                        sortMethod: 'directed'
                    }
                },
                physics: {
                    enabled: true,
                    stabilization: { iterations: 1000 },
                    barnesHut: {
                        gravitationalConstant: -80000,
                        springConstant: 0.04,
                        springLength: 95
                    }
                },
                interaction: {
                    dragNodes: true,
                    dragView: true,
                    zoomView: true,
                    hover: true
                },
                nodes: {
                    shape: 'box',
                    margin: 10,
                    widthConstraint: {
                        maximum: 150
                    }
                },
                edges: {
                    smooth: true
                }
            };

            network = new vis.Network(container, data, options);

            // Обработчики событий
            network.on("click", function(params) {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    showNodeInfo(nodeId);
                } else {
                    document.getElementById('node-info').innerHTML = 'Выберите элемент на диаграмме';
                }
            });

            network.on("doubleClick", function(params) {
                if (params.nodes.length > 0) {
                    network.focus(params.nodes[0], { scale: 1.2, animation: true });
                }
            });

            // Заполняем статистику
            updateStatistics();
        }

        function getNodeTooltip(node) {
            let tooltip = `<b>${node.label}</b>`;
            if (node.detailed) tooltip += `\\n\\n${node.detailed}`;
            if (node.group) tooltip += `\\n\\nГруппа: ${node.group}`;
            if (node.owner) tooltip += `\\nВладелец: ${node.owner}`;
            return tooltip;
        }

        function showNodeInfo(nodeId) {
            const node = diagramData.nodes.find(n => n.id === nodeId);
            if (!node) return;

            let info = `<b>${node.label}</b>`;
            if (node.detailed) info += `<br><br>${node.detailed}`;
            if (node.group) info += `<br><br><b>Группа:</b> ${node.group}`;
            if (node.owner) info += `<br><b>Владелец:</b> ${node.owner}`;
            if (node.type) info += `<br><b>Тип:</b> ${getNodeTypeName(node.type)}`;

            // Находим связанные элементы
            const incoming = diagramData.edges.filter(e => e.to === nodeId);
            const outgoing = diagramData.edges.filter(e => e.from === nodeId);

            if (incoming.length > 0) {
                info += `<br><br><b>Входящие связи (${incoming.length}):</b>`;
                incoming.forEach(edge => {
                    const sourceNode = diagramData.nodes.find(n => n.id === edge.from);
                    const sourceLabel = sourceNode ? sourceNode.label : edge.from;
                    info += `<br>• ${sourceLabel} → ${edge.label}`;
                });
            }

            if (outgoing.length > 0) {
                info += `<br><br><b>Исходящие связи (${outgoing.length}):</b>`;
                outgoing.forEach(edge => {
                    const targetNode = diagramData.nodes.find(n => n.id === edge.to);
                    const targetLabel = targetNode ? targetNode.label : edge.to;
                    info += `<br>• ${edge.label} → ${targetLabel}`;
                });
            }

            document.getElementById('node-info').innerHTML = info;
        }

        function getNodeTypeName(type) {
            const names = {
                external: 'Внешний вход',
                final: 'Конечный выход',
                critical: 'Супер-критическая операция',
                merge: 'Точка слияния',
                split: 'Точка разветвления',
                merge_split: 'Слияние и разветвление',
                normal: 'Обычная операция'
            };
            return names[type] || type;
        }

        function updateStatistics() {
            document.getElementById('stats-operations').textContent = diagramData.statistics.operations_count;
            document.getElementById('stats-inputs').textContent = diagramData.statistics.external_inputs;
            document.getElementById('stats-outputs').textContent = diagramData.statistics.final_outputs;
            document.getElementById('stats-merge').textContent = diagramData.statistics.merge_points;
            document.getElementById('stats-split').textContent = diagramData.statistics.split_points;
            document.getElementById('stats-critical').textContent = diagramData.statistics.critical_points;

            // Заполняем список критических операций
            const criticalList = document.getElementById('critical-list');
            if (diagramData.critical_operations.length > 0) {
                let html = '';
                diagramData.critical_operations.forEach(op => {
                    html += `<div style="margin: 5px 0; padding: 5px; background: #ffeaa7; border-radius: 3px;">
                        <b>${op.operation}</b><br>
                        Входов: ${op.inputs_count}, Использований выхода: ${op.output_reuse}
                    </div>`;
                });
                criticalList.innerHTML = html;
            } else {
                criticalList.innerHTML = '<div style="color: #666;">Критических операций нет</div>';
            }
        }

        function fitToScreen() {
            if (network) {
                network.fit({ animation: true });
            }
        }

        function resetZoom() {
            if (network) {
                network.moveTo({ scale: 1, animation: true });
            }
        }

        function togglePhysics() {
            physicsEnabled = !physicsEnabled;
            if (network) {
                network.setOptions({ physics: { enabled: physicsEnabled } });
            }
            const button = event.target;
            button.textContent = 'Физика: ' + (physicsEnabled ? 'Вкл' : 'Выкл');
        }

        // Инициализация при загрузке
        document.addEventListener('DOMContentLoaded', initNetwork);
    </script>
</body>
</html>'''

    # Заменяем данные в шаблоне
    html_content = html_template.replace(
        '{DIAGRAM_DATA}', 
        json.dumps(html_data, ensure_ascii=False, indent=2)
    )
    
    output_file.write_text(html_content, encoding=ENCODING)

def export_interactive_html(operations: Dict[str, Operation], analysis_data: AnalysisData, 
                           choices: Choices, output_base: str = None) -> Path:
    """
    Экспортирует диаграмму в интерактивный HTML - ВОЗВРАЩАЕТ Path
    """
    # Используем переданное имя файла или значение по умолчанию
    if output_base is None:
        output_base = "business_process_diagram"
    
    output_file = Path(f"{output_base}.html")

    # Генерация данных для интерактивного графа
    html_data = build_interactive_html_data(operations, analysis_data)
    
    # Генерация HTML файла
    generate_interactive_html_file(html_data, output_file)
    
    print(f"\n" + "="*60)
    print("✓ ИНТЕРАКТИВНАЯ HTML-ДИАГРАММА УСПЕШНО СОЗДАНА!")
    print("="*60)
    print(f"Файл: {output_file}")
    
    return output_file  # Явно возвращаем Path