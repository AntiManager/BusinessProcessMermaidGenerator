"""
Экспорт Causal Loop Diagram в интерактивный HTML (Vis.js) - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
import json
from pathlib import Path
from typing import Dict, List
from models import CausalAnalysis, Choices
from utils import safe_id
from config import ENCODING

def build_cld_interactive_data(causal_analysis: CausalAnalysis, choices: Choices) -> Dict:
    """
    Строит данные для интерактивного CLD
    """
    nodes = []
    edges = []
    
    # Узлы - переменные (овалы)
    for variable in sorted(causal_analysis.variables):
        nodes.append({
            "id": safe_id(variable),
            "label": variable,
            "shape": "ellipse",
            "color": {
                "background": "#e3f2fd",
                "border": "#1976d2",
                "highlight": {"background": "#bbdefb", "border": "#1976d2"}
            },
            "font": {"size": 16, "face": "Arial"},
            "margin": 12,
            "widthConstraint": {"minimum": 100, "maximum": 200},
            "shadow": True
        })
    
    # Связи
    for link in causal_analysis.links:
        if not link.include_in_cld:
            continue
            
        # Определяем цвет в зависимости от знака влияния
        color = "#2e7d32" if link.influence == "+" else "#c62828"
        dash_pattern = {"length": 10, "gap": 5} if link.influence == "-" else None
        
        # Формируем заголовок для tooltip
        title_parts = [f"<b>{link.source}</b> → <b>{link.target}</b>"]
        title_parts.append(f"Влияние: {link.influence}")
        if link.operation:
            title_parts.append(f"Операция: {link.operation}")
        if link.strength:
            title_parts.append(f"Сила влияния: {link.strength}")
        if link.description:
            title_parts.append(f"Описание: {link.description}")
        
        # Формируем label для стрелки
        label_parts = []
        if choices.cld_influence_signs:
            label_parts.append(link.influence)
        if choices.show_cld_operations and link.operation:
            op_text = link.operation
            if len(op_text) > 15:
                op_text = op_text[:12] + "..."
            label_parts.append(op_text)
        
        edge_data = {
            "from": safe_id(link.source),
            "to": safe_id(link.target),
            "color": {
                "color": color,
                "highlight": color,
                "hover": color
            },
            "arrows": "to",
            "title": "<br>".join(title_parts),
            "smooth": {"type": "curvedCCW", "roundness": 0.2},
            "width": 2,
            "shadow": True,
            "font": {"color": "#333", "size": 12, "face": "Arial", "strokeWidth": 0}
        }
        
        if dash_pattern:
            edge_data["dashes"] = True
        
        if label_parts:
            edge_data["label"] = " ".join(label_parts)
        
        edges.append(edge_data)
    
    return {
        "nodes": nodes,
        "edges": edges,
        "feedback_loops": causal_analysis.feedback_loops,
        "statistics": {
            "variables": len(causal_analysis.variables),
            "links": len(edges),
            "positive_links": len([l for l in causal_analysis.links if l.include_in_cld and l.influence == "+"]),
            "negative_links": len([l for l in causal_analysis.links if l.include_in_cld and l.influence == "-"]),
            "loops": len(causal_analysis.feedback_loops)
        }
    }

def export_cld_interactive(causal_analysis: CausalAnalysis, choices: Choices,
                          output_base: str = None, output_dir: Path = None) -> Path:
    """
    Экспортирует интерактивный CLD - ИСПРАВЛЕННАЯ ВЕРСИЯ
    """
    # Используем переданную папку или текущую директорию
    if output_dir is None:
        output_dir = Path(".")
    
    output_file = output_dir / f"{output_base}.html"
    
    # Генерация данных
    html_data = build_cld_interactive_data(causal_analysis, choices)
    
    # УЛУЧШЕННЫЙ HTML шаблон с полным функционалом
    html_template = '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Causal Loop Diagram - Интерактивный граф</title>
        <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                overflow: hidden;
                height: 100vh;
            }
            .container {
                display: flex;
                height: 100vh;
                width: 100vw;
                gap: 0;
            }
            .sidebar {
                width: 350px;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 25px;
                overflow-y: auto;
                border-right: 1px solid rgba(255, 255, 255, 0.2);
                box-shadow: 2px 0 10px rgba(0,0,0,0.1);
                z-index: 1000;
            }
            .diagram {
                flex: 1;
                background: #f8f9fa;
                position: relative;
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #2c3e50, #34495e);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            .header h2 {
                margin: 0;
                font-size: 1.5em;
                font-weight: 300;
            }
            .header p {
                margin: 5px 0 0 0;
                opacity: 0.8;
                font-size: 0.9em;
            }
            .statistics {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 25px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 4px solid #3498db;
            }
            .statistics h3 {
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 1.2em;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .statistics h3::before {
                content: "📊";
                font-size: 1.1em;
            }
            .stat-item {
                display: flex;
                justify-content: space-between;
                margin: 8px 0;
                padding: 6px 0;
                border-bottom: 1px solid #ecf0f1;
            }
            .stat-item:last-child {
                border-bottom: none;
            }
            .stat-value {
                font-weight: bold;
                color: #2c3e50;
            }
            .feedback-section {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 25px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 4px solid #e74c3c;
            }
            .feedback-section h3 {
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 1.2em;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .feedback-section h3::before {
                content: "🔄";
                font-size: 1.1em;
            }
            .feedback-loop {
                background: #fffaf0;
                padding: 12px;
                margin: 8px 0;
                border-radius: 6px;
                border: 1px solid #ffeaa7;
                font-size: 0.9em;
                line-height: 1.4;
            }
            .controls {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 25px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 4px solid #27ae60;
            }
            .controls h3 {
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 1.2em;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .controls h3::before {
                content: "🎮";
                font-size: 1.1em;
            }
            .control-buttons {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                margin-bottom: 15px;
            }
            button {
                padding: 10px 15px;
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.9em;
                transition: all 0.3s ease;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                background: linear-gradient(135deg, #2980b9, #2471a3);
            }
            button:active {
                transform: translateY(0);
            }
            .physics-toggle {
                background: linear-gradient(135deg, #e74c3c, #c0392b);
            }
            .node-info {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 4px solid #9b59b6;
            }
            .node-info h3 {
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 1.2em;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .node-info h3::before {
                content: "ℹ️";
                font-size: 1.1em;
            }
            #node-info {
                max-height: 200px;
                overflow-y: auto;
                line-height: 1.5;
                color: #555;
            }
            #network {
                width: 100%;
                height: 100%;
                border: none;
            }
            .legend {
                display: flex;
                flex-direction: column;
                gap: 8px;
                margin-top: 15px;
                padding: 15px;
                background: rgba(255,255,255,0.9);
                border-radius: 6px;
            }
            .legend-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 0.9em;
            }
            .legend-color {
                width: 16px;
                height: 16px;
                border-radius: 50%;
                border: 2px solid;
            }
            .positive { background: #2e7d32; border-color: #1b5e20; }
            .negative { background: #c62828; border-color: #b71c1c; }
            .variable { background: #e3f2fd; border-color: #1976d2; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="sidebar">
                <div class="header">
                    <h2>🌐 Causal Loop Diagram</h2>
                    <p>Диаграмма причинно-следственных связей</p>
                </div>
                
                <div class="statistics">
                    <h3>Статистика системы</h3>
                    <div class="stat-item">
                        <span>Переменные:</span>
                        <span class="stat-value" id="stats-variables">0</span>
                    </div>
                    <div class="stat-item">
                        <span>Связи:</span>
                        <span class="stat-value" id="stats-links">0</span>
                    </div>
                    <div class="stat-item">
                        <span>Положительные влияния:</span>
                        <span class="stat-value" id="stats-positive">0</span>
                    </div>
                    <div class="stat-item">
                        <span>Отрицательные влияния:</span>
                        <span class="stat-value" id="stats-negative">0</span>
                    </div>
                    <div class="stat-item">
                        <span>Петли обратной связи:</span>
                        <span class="stat-value" id="stats-loops">0</span>
                    </div>
                </div>

                <div class="feedback-section" id="feedback-section">
                    <h3>Петли обратной связи</h3>
                    <div id="feedback-loops"></div>
                </div>

                <div class="controls">
                    <h3>Управление графом</h3>
                    <div class="control-buttons">
                        <button onclick="fitToScreen()" title="Вписать в экран">🔍 Вписать</button>
                        <button onclick="resetZoom()" title="Сбросить масштаб">🎯 Сброс</button>
                        <button onclick="togglePhysics()" id="physicsBtn" title="Переключить физику">⚡ Физика: Вкл</button>
                        <button onclick="stabilize()" title="Стабилизировать граф">🔄 Стабилизация</button>
                    </div>
                    <div class="legend">
                        <div class="legend-item">
                            <div class="legend-color variable"></div>
                            <span>Переменные системы</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color positive"></div>
                            <span>Положительное влияние (+) </span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color negative"></div>
                            <span>Отрицательное влияние (-) </span>
                        </div>
                    </div>
                </div>

                <div class="node-info">
                    <h3>Информация об элементе</h3>
                    <div id="node-info">👆 Выберите элемент на диаграмме для просмотра информации</div>
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
                        ...node,
                        borderWidth: 2,
                        shadow: true,
                        font: { 
                            size: 14, 
                            face: 'Arial',
                            color: '#2c3e50',
                            strokeWidth: 2,
                            strokeColor: 'rgba(255,255,255,0.8)'
                        }
                    }))),
                    edges: new vis.DataSet(diagramData.edges.map(edge => ({
                        ...edge,
                        width: 2,
                        shadow: true,
                        font: { 
                            size: 12, 
                            face: 'Arial',
                            color: '#333',
                            strokeWidth: 2,
                            strokeColor: 'rgba(255,255,255,0.8)'
                        },
                        smooth: {
                            enabled: true,
                            type: 'curvedCCW',
                            roundness: 0.2
                        }
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
                        stabilization: { 
                            iterations: 1000,
                            updateInterval: 25
                        },
                        barnesHut: {
                            gravitationalConstant: -8000,
                            springConstant: 0.04,
                            springLength: 150,
                            damping: 0.09
                        }
                    },
                    interaction: {
                        dragNodes: true,
                        dragView: true,
                        zoomView: true,
                        hover: true,
                        hoverConnectedEdges: true,
                        selectable: true,
                        selectConnectedEdges: true
                    },
                    nodes: {
                        shape: 'ellipse',
                        margin: 10,
                        widthConstraint: {
                            minimum: 100,
                            maximum: 200
                        },
                        scaling: {
                            min: 10,
                            max: 30
                        }
                    },
                    edges: {
                        smooth: true,
                        scaling: {
                            min: 1,
                            max: 3
                        },
                        hoverWidth: 1.5
                    },
                    groups: {
                        useDefaultGroups: false
                    }
                };

                network = new vis.Network(container, data, options);

                // Обработчики событий
                network.on("click", function(params) {
                    if (params.nodes.length > 0) {
                        const nodeId = params.nodes[0];
                        showNodeInfo(nodeId);
                    } else if (params.edges.length > 0) {
                        const edgeId = params.edges[0];
                        showEdgeInfo(edgeId);
                    } else {
                        document.getElementById('node-info').innerHTML = 
                            '👆 Выберите элемент на диаграмме для просмотра информации';
                    }
                });

                network.on("doubleClick", function(params) {
                    if (params.nodes.length > 0) {
                        network.focus(params.nodes[0], { 
                            scale: 1.2, 
                            animation: { 
                                duration: 1000,
                                easingFunction: 'easeInOutQuad'
                            } 
                        });
                    }
                });

                network.on("stabilizationIterationsDone", function() {
                    network.fit({ animation: true });
                });

                network.on("stabilized", function() {
                    console.log("Граф стабилизирован");
                });

                // Заполняем статистику
                updateStatistics();
                
                // Автоматически подгоняем под экран после стабилизации
                setTimeout(() => {
                    fitToScreen();
                }, 500);
            }

            function showNodeInfo(nodeId) {
                const node = diagramData.nodes.find(n => n.id === nodeId);
                if (!node) return;

                // Находим связанные связи
                const incoming = diagramData.edges.filter(e => e.to === nodeId);
                const outgoing = diagramData.edges.filter(e => e.from === nodeId);

                let info = `<div style="margin-bottom: 15px;">
                    <h4 style="color: #2c3e50; margin-bottom: 10px;">📊 ${node.label}</h4>
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                        <strong>Тип:</strong> Переменная системы<br>
                        <strong>ID:</strong> ${node.id}
                    </div>
                </div>`;

                if (incoming.length > 0) {
                    info += `<div style="margin-bottom: 15px;">
                        <strong>📥 Входящие связи (${incoming.length}):</strong><br>`;
                    incoming.forEach(edge => {
                        const sourceNode = diagramData.nodes.find(n => n.id === edge.from);
                        const influence = edge.label ? edge.label.split(' ')[0] : '+';
                        const color = influence === '+' ? '#2e7d32' : '#c62828';
                        info += `<div style="margin: 5px 0; padding: 5px; background: ${color}10; border-radius: 3px; border-left: 3px solid ${color};">
                            <span style="color: ${color}; font-weight: bold;">${influence}</span> 
                            ${sourceNode ? sourceNode.label : edge.from} → ${node.label}
                        </div>`;
                    });
                    info += `</div>`;
                }

                if (outgoing.length > 0) {
                    info += `<div>
                        <strong>📤 Исходящие связи (${outgoing.length}):</strong><br>`;
                    outgoing.forEach(edge => {
                        const targetNode = diagramData.nodes.find(n => n.id === edge.to);
                        const influence = edge.label ? edge.label.split(' ')[0] : '+';
                        const color = influence === '+' ? '#2e7d32' : '#c62828';
                        info += `<div style="margin: 5px 0; padding: 5px; background: ${color}10; border-radius: 3px; border-left: 3px solid ${color};">
                            <span style="color: ${color}; font-weight: bold;">${influence}</span> 
                            ${node.label} → ${targetNode ? targetNode.label : edge.to}
                        </div>`;
                    });
                    info += `</div>`;
                }

                document.getElementById('node-info').innerHTML = info;
            }

            function showEdgeInfo(edgeId) {
                const edge = diagramData.edges.find(e => 
                    e.from + '-' + e.to === edgeId || 
                    (e.label && e.from + '-' + e.to + '-' + e.label === edgeId)
                );
                if (!edge) return;

                const sourceNode = diagramData.nodes.find(n => n.id === edge.from);
                const targetNode = diagramData.nodes.find(n => n.id === edge.to);
                const influence = edge.label ? edge.label.split(' ')[0] : '+';
                const color = influence === '+' ? '#2e7d32' : '#c62828';

                let info = `<div style="margin-bottom: 15px;">
                    <h4 style="color: #2c3e50; margin-bottom: 10px;">🔗 Связь влияния</h4>
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                        <strong>Источник:</strong> ${sourceNode ? sourceNode.label : edge.from}<br>
                        <strong>Цель:</strong> ${targetNode ? targetNode.label : edge.to}<br>
                        <strong>Влияние:</strong> <span style="color: ${color}; font-weight: bold;">${influence}</span><br>
                        ${edge.title ? `<strong>Описание:</strong> ${edge.title.replace(/<br>/g, ', ')}` : ''}
                    </div>
                </div>`;

                document.getElementById('node-info').innerHTML = info;
            }

            function updateStatistics() {
                document.getElementById('stats-variables').textContent = diagramData.statistics.variables;
                document.getElementById('stats-links').textContent = diagramData.statistics.links;
                document.getElementById('stats-positive').textContent = diagramData.statistics.positive_links;
                document.getElementById('stats-negative').textContent = diagramData.statistics.negative_links;
                document.getElementById('stats-loops').textContent = diagramData.statistics.loops;

                // Заполняем список петель обратной связи
                const feedbackContainer = document.getElementById('feedback-loops');
                if (diagramData.feedback_loops && diagramData.feedback_loops.length > 0) {
                    let html = '';
                    diagramData.feedback_loops.forEach((loop, index) => {
                        html += `<div class="feedback-loop">
                            <strong>Петля ${index + 1}:</strong><br>
                            ${loop.join(' → ')}
                        </div>`;
                    });
                    feedbackContainer.innerHTML = html;
                } else {
                    feedbackContainer.innerHTML = '<div style="color: #666; text-align: center; padding: 20px;">Петли обратной связи не обнаружены</div>';
                }
            }

            function fitToScreen() {
                if (network) {
                    network.fit({ 
                        animation: { 
                            duration: 1000,
                            easingFunction: 'easeInOutQuad'
                        } 
                    });
                }
            }

            function resetZoom() {
                if (network) {
                    network.moveTo({ 
                        scale: 1, 
                        animation: {
                            duration: 800,
                            easingFunction: 'easeInOutQuad'
                        }
                    });
                }
            }

            function togglePhysics() {
                physicsEnabled = !physicsEnabled;
                if (network) {
                    network.setOptions({ 
                        physics: { enabled: physicsEnabled } 
                    });
                }
                const button = document.getElementById('physicsBtn');
                button.textContent = '⚡ Физика: ' + (physicsEnabled ? 'Вкл' : 'Выкл');
                button.style.background = physicsEnabled ? 
                    'linear-gradient(135deg, #3498db, #2980b9)' : 
                    'linear-gradient(135deg, #e74c3c, #c0392b)';
            }

            function stabilize() {
                if (network) {
                    network.stabilize(1000);
                }
            }

            // Глобальные обработчики клавиш
            document.addEventListener('keydown', function(e) {
                if (e.key === 'f' || e.key === 'а') { // F или А (русская раскладка)
                    e.preventDefault();
                    fitToScreen();
                } else if (e.key === 'r' || e.key === 'к') { // R или К (русская раскладка)
                    e.preventDefault();
                    resetZoom();
                } else if (e.key === 'p' || e.key === 'з') { // P или З (русская раскладка)
                    e.preventDefault();
                    togglePhysics();
                }
            });

            // Инициализация при загрузке
            document.addEventListener('DOMContentLoaded', initNetwork);

            // Обработка изменения размера окна
            window.addEventListener('resize', function() {
                setTimeout(fitToScreen, 100);
            });
        </script>
    </body>
    </html>
    '''
    
    html_content = html_template.replace(
        '{DIAGRAM_DATA}', 
        json.dumps(html_data, ensure_ascii=False, indent=2)
    )
    
    output_file.write_text(html_content, encoding=ENCODING)
    
    print(f"\n" + "="*60)
    print("✓ ИНТЕРАКТИВНЫЙ CAUSAL LOOP DIAGRAM УСПЕШНО СОЗДАН!")
    print("="*60)
    print(f"Файл: {output_file}")
    print("🎯 УЛУЧШЕННЫЙ ИНТЕРФЕЙС:")
    print("   • 🖥️  Полноэкранный режим")
    print("   • 🎮 Полный набор управления")
    print("   • 📊 Детальная статистика")
    print("   • 🔄 Обнаружение петель обратной связи")
    print("   • ⌨️  Горячие клавиши: F-вписать, R-сброс, P-физика")
    
    return output_file