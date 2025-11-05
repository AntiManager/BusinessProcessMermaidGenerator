"""
Экспорт Causal Loop Diagram в Mermaid формат
"""
from pathlib import Path
from typing import List, Dict
from models import CausalAnalysis, Choices
from utils import safe_id, escape_text
from config import ENCODING

def build_cld_mermaid(causal_analysis: CausalAnalysis, choices: Choices) -> str:
    """
    Строит Mermaid код для Causal Loop Diagram - ИСПРАВЛЕННАЯ ВЕРСИЯ
    """
    lines = ["```mermaid", "graph TD"]
    
    # Добавляем узлы (переменные) как овалы
    for variable in sorted(causal_analysis.variables):
        lines.append(f'    {safe_id(variable)}(["{escape_text(variable)}"])')
    
    # Добавляем связи
    for link in causal_analysis.links:
        if not link.include_in_cld:
            continue
            
        source_id = safe_id(link.source)
        target_id = safe_id(link.target)
        
        # Формируем label для стрелки
        label_parts = []
        
        if choices.cld_influence_signs:
            # 🔥 ИСПРАВЛЕНИЕ: Экранирование знаков + и - для Mermaid
            if link.influence == "+":
                influence_symbol = '"+"'  # Экранируем плюс в кавычках
            elif link.influence == "-":
                influence_symbol = '"-"'  # Экранируем минус в кавычках  
            else:
                influence_symbol = link.influence
            label_parts.append(influence_symbol)
        
        if choices.show_cld_operations and link.operation:
            # Ограничиваем длину названия операции
            op_text = link.operation
            if len(op_text) > 20:
                op_text = op_text[:17] + "..."
            label_parts.append(op_text)
        
        label = " ".join(label_parts)
        
        # 🔥 ИСПРАВЛЕНИЕ: Упрощенное экранирование для Mermaid
        # Вместо escape_text используем простое экранирование кавычек
        escaped_label = label.replace('"', '&quot;')
        
        # 🔥 АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ: Используем HTML entities для специальных символов
        # escaped_label = label.replace('+', '&#43;').replace('-', '&#45;').replace('"', '&quot;')
        
        lines.append(f'    {source_id} -- "{escaped_label}" --> {target_id}')
    
    lines.append("```")
    return "\n".join(lines)

def export_cld_mermaid(causal_analysis: CausalAnalysis, choices: Choices, 
                      output_base: str = None, output_dir: Path = None) -> Path:
    """
    Экспортирует CLD в Markdown файл - ОБНОВЛЕННАЯ ВЕРСИЯ С ВОЗВРАТОМ Path
    """
    # Используем переданную папку или текущую директорию
    if output_dir is None:
        output_dir = Path(".")
    
    output_file = output_dir / f"{output_base}.md"
    
    # Генерация Mermaid кода
    mermaid_code = build_cld_mermaid(causal_analysis, choices)
    
    # Сборка контента
    content_parts = [
        "# Causal Loop Diagram\n\n",
        "## Диаграмма причинно-следственных связей\n\n",
        mermaid_code,
        "\n\n## Дополнительные представления\n\n",
        f"### 🎮 Интерактивная версия\n\n",
        f"Для более удобного исследования причинно-следственных связей доступна [интерактивная версия]({output_base}_cld.html).\n\n",
        f"**Возможности интерактивной версии:**\n",
        f"- 🔍 Динамическое исследование связей\n", 
        f"- 📊 Автоматическое обнаружение петель обратной связи\n",
        f"- 🎯 Фильтрация по типам влияния\n",
        f"- 📈 Расширенная статистика системы\n\n",
        "## Реестр причинно-следственных связей\n\n"
    ]
    
    # Таблица связей
    headers = ["Источник", "Цель", "Влияние", "Операция", "Сила влияния", "Описание"]
    rows = []
    
    for link in causal_analysis.links:
        if link.include_in_cld:
            rows.append({
                "Источник": link.source,
                "Цель": link.target,
                "Влияние": link.influence,
                "Операция": link.operation or "-",
                "Сила влияния": link.strength or "-",
                "Описание": link.description
            })
    
    # Создаем Markdown таблицу
    if rows:
        content_parts.append("| " + " | ".join(headers) + " |\n")
        content_parts.append("|" + "|".join(["---"] * len(headers)) + "|\n")
        
        for row in rows:
            values = [str(row.get(h, "")) for h in headers]
            content_parts.append("| " + " | ".join(values) + " |\n")
    else:
        content_parts.append("Нет данных о связях\n")
    
    # Информация о петлях обратной связи
    if causal_analysis.feedback_loops:
        content_parts.append("\n## Обнаруженные петли обратной связи\n\n")
        for i, loop in enumerate(causal_analysis.feedback_loops, 1):
            content_parts.append(f"{i}. {' → '.join(loop)}\n")
    
    # Статистика
    content_parts.extend([
        f"\n\n## Статистика системы\n\n",
        f"- **Переменных**: {len(causal_analysis.variables)}\n",
        f"- **Связей**: {len([l for l in causal_analysis.links if l.include_in_cld])}\n",
        f"- **Положительных влияний**: {len([l for l in causal_analysis.links if l.include_in_cld and l.influence == '+' ])}\n",
        f"- **Отрицательных влияний**: {len([l for l in causal_analysis.links if l.include_in_cld and l.influence == '-' ])}\n",
        f"- **Петель обратной связи**: {len(causal_analysis.feedback_loops)}\n",
    ])
    
    # Сохранение файла
    output_file.write_text("".join(content_parts), encoding=ENCODING)
    
    print(f"\n" + "="*60)
    print("✓ CAUSAL LOOP DIAGRAM УСПЕШНО СОЗДАН!")
    print("="*60)
    print(f"Файл: {output_file}")
    print(f"Связей: {len([l for l in causal_analysis.links if l.include_in_cld])}")
    print(f"Переменных: {len(causal_analysis.variables)}")
    print(f"Петель обратной связи: {len(causal_analysis.feedback_loops)}")
    
    return output_file