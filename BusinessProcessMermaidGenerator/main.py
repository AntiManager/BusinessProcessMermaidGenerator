"""
Главный файл приложения - ГЕНЕРАТОР ДИАГРАММ БИЗНЕС-ПРОЦЕССОВ
РЕФАКТОРИНГ: Устранение циклических импортов
"""
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

def main() -> None:
    """
    Главная функция - всегда запускает GUI
    """
    from gui_interface import run_gui
    run_gui()

if __name__ == "__main__":
    main()