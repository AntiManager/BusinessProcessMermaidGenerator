"""
Обработка текста и утилиты - ОБНОВЛЕННЫЙ МОДУЛЬ
"""
import re
import pandas as pd
from typing import List, Dict

def safe_id(name: str | None) -> str:
    if pd.isna(name) or not str(name).strip():
        return "empty"
    safe = re.sub(r"\W+", "_", str(name).strip(), flags=re.UNICODE)
    safe = re.sub(r"^_+|_+$", "", safe)
    if safe and safe[0].isdigit():
        safe = "id_" + safe
    return safe or "empty"

def escape_text(text: str | None) -> str:
    if not text:
        return ""
    return str(text).replace('"', '#quot;').replace("(", "#40;").replace(")", "#41;")

def clean_text(text: str | None) -> str:
    if not text:
        return ""
    return str(text).replace("\r", "").replace("\t", " ").strip()

def _escape_multiline(text: str | None) -> str:
    if not text:
        return ""
    return str(text).replace("\n", "<br>")

def create_markdown_table(headers: List[str], data: List[Dict[str, str]]) -> str:
    """
    Создает Markdown таблицу из данных
    """
    if not data:
        return "Нет данных для отображения"
    table_lines = []
    table_lines.append("| " + " | ".join(headers) + " |")
    table_lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in data:
        values = [_escape_multiline(str(row.get(h, ""))) for h in headers]
        table_lines.append("| " + " | ".join(values) + " |")
    return "\n".join(table_lines)