"""
Генератор диаграмм бизнес-процессов v4.0 - Modern IDE
Точка входа приложения
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDir, QStandardPaths
from gui.main_window import MainWindow

def setup_environment():
    """Настраивает окружение приложения"""
    # Создаем директории для данных приложения
    app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    QDir().mkpath(app_data_dir)
    
    # Настраиваем пути для логов и кэша
    print(f"Данные приложения: {app_data_dir}")

def main():
    # Настройка окружения
    setup_environment()
    
    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName("Business Process Generator")
    app.setApplicationVersion("4.0.0")
    app.setOrganizationName("BPG Team")
    
    # Создание главного окна
    window = MainWindow()
    window.show()
    
    # Запуск приложения
    sys.exit(app.exec())

if __name__ == "__main__":
    main()