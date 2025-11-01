"""
Утилиты и вспомогательные функции
"""
import re
import pandas as pd
from pathlib import Path
from typing import List, Set, Tuple, Dict
from config import ENCODING

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

def merge_strings(existing: str, new: str, separator: str = "; ") -> str:
    if not existing:
        return new
    if not new:
        return existing
    
    existing_parts = [part.strip() for part in existing.split(separator) if part.strip()]
    new_parts = [part.strip() for part in new.split(separator) if part.strip()]
    
    merged = set(existing_parts + new_parts)
    return separator.join(sorted(merged))

def get_excel_files() -> List[Path]:
    return list(Path(".").glob("*.xlsx")) + list(Path(".").glob("*.xls"))

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