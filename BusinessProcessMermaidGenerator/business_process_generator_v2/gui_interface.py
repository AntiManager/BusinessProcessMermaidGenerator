"""
Графический интерфейс для генератора диаграмм бизнес-процессов
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from pathlib import Path
from typing import Dict, Any, Optional
from models import Choices
from config import CRITICAL_MIN_INPUTS, CRITICAL_MIN_REUSE

class BusinessProcessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор диаграмм бизнес-процессов")
        self.root.geometry("800x650")
        
        # Загрузка конфигурации
        self.config_file = Path("bp_config.json")
        self.config = self.load_config()
        
        # Переменные интерфейса
        self.excel_path = tk.StringVar(value=self.config.get('excel_path', ''))
        self.sheet_name = tk.StringVar(value=self.config.get('sheet_name', 'БП_1'))
        self.output_base = tk.StringVar(value=self.config.get('output_base', 'business_process_diagram'))
        self.output_format = tk.StringVar(value=self.config.get('output_format', 'html_interactive'))
        self.subgroup_column = tk.StringVar(value=self.config.get('subgroup_column', ''))
        self.show_detailed = tk.BooleanVar(value=self.config.get('show_detailed', False))
        self.critical_min_inputs = tk.IntVar(value=self.config.get('critical_min_inputs', CRITICAL_MIN_INPUTS))
        self.critical_min_reuse = tk.IntVar(value=self.config.get('critical_min_reuse', CRITICAL_MIN_REUSE))
        self.no_grouping = tk.BooleanVar(value=self.config.get('no_grouping', True))
        
        self.create_widgets()
        
    def load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из файла"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
        return {}
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            config = {
                'excel_path': self.excel_path.get(),
                'sheet_name': self.sheet_name.get(),
                'output_base': self.output_base.get(),
                'output_format': self.output_format.get(),
                'subgroup_column': self.subgroup_column.get(),
                'show_detailed': self.show_detailed.get(),
                'critical_min_inputs': self.critical_min_inputs.get(),
                'critical_min_reuse': self.critical_min_reuse.get(),
                'no_grouping': self.no_grouping.get()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройки колонок и строк для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Генератор диаграмм бизнес-процессов", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        row = 1
        
        # Выбор файла Excel
        ttk.Label(main_frame, text="Файл Excel:").grid(row=row, column=0, sticky=tk.W, pady=2)
        file_entry = ttk.Entry(main_frame, textvariable=self.excel_path, width=50)
        file_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 5))
        ttk.Button(main_frame, text="Обзор...", command=self.browse_file).grid(row=row, column=2, pady=2)
        row += 1
        
        # Имя листа
        ttk.Label(main_frame, text="Имя листа:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.sheet_name, width=30).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # Имя выходного файла
        ttk.Label(main_frame, text="Имя выходного файла:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.output_base, width=30).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Формат вывода
        ttk.Label(main_frame, text="Формат вывода:").grid(row=row, column=0, sticky=tk.W, pady=2)
        format_frame = ttk.Frame(main_frame)
        format_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        formats = [
            ("Markdown с Mermaid", "md"),
            ("HTML с Mermaid", "html_mermaid"),
            ("Интерактивный HTML", "html_interactive")
        ]
        
        for i, (text, value) in enumerate(formats):
            rb = ttk.Radiobutton(format_frame, text=text, variable=self.output_format, 
                                value=value, command=self.on_format_change)
            rb.grid(row=0, column=i, sticky=tk.W, padx=(0, 20))
        row += 1
        
        # Группировка
        ttk.Label(main_frame, text="Группировка:").grid(row=row, column=0, sticky=tk.W, pady=2)
        group_frame = ttk.Frame(main_frame)
        group_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Radiobutton(group_frame, text="Без группировки", variable=self.no_grouping,
                       value=True, command=self.on_grouping_change).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(group_frame, text="Группировать по:", variable=self.no_grouping,
                       value=False, command=self.on_grouping_change).grid(row=0, column=1, sticky=tk.W)
        
        self.group_combo = ttk.Combobox(group_frame, textvariable=self.subgroup_column, 
                                       values=['Группа', 'Владелец'], state='readonly', width=15)
        self.group_combo.grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        row += 1
        
        # Подробное описание
        ttk.Checkbutton(main_frame, text="Показывать подробное описание", 
                       variable=self.show_detailed).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1
        
        # Пороговые значения
        ttk.Label(main_frame, text="Пороги критических операций:").grid(row=row, column=0, sticky=tk.W, pady=2)
        threshold_frame = ttk.Frame(main_frame)
        threshold_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(threshold_frame, text="Мин. входов:").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(threshold_frame, from_=1, to=20, textvariable=self.critical_min_inputs,
                   width=5).grid(row=0, column=1, sticky=tk.W, padx=(5, 15))
        
        ttk.Label(threshold_frame, text="Мин. использований выхода:").grid(row=0, column=2, sticky=tk.W)
        ttk.Spinbox(threshold_frame, from_=1, to=20, textvariable=self.critical_min_reuse,
                   width=5).grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        row += 1
        
        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Сгенерировать диаграмму", 
                  command=self.generate_diagram, style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Сохранить настройки", 
                  command=self.save_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Сбросить настройки", 
                  command=self.reset_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Выход", 
                  command=self.root.quit).pack(side=tk.LEFT)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=row+1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Инициализация состояния
        self.on_format_change()
        self.on_grouping_change()
    
    def browse_file(self):
        """Выбор файла через диалоговое окно"""
        filename = filedialog.askopenfilename(
            title="Выберите файл Excel",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.excel_path.set(filename)
            # Предложить имя выходного файла на основе имени Excel файла
            if not self.output_base.get() or self.output_base.get() == 'business_process_diagram':
                excel_stem = Path(filename).stem
                self.output_base.set(excel_stem + '_diagram')
            self.save_config()
    
    def on_format_change(self):
        """Обработка изменения формата вывода"""
        if self.output_format.get() == "html_interactive":
            self.no_grouping.set(True)
            self.show_detailed.set(False)
            self.on_grouping_change()
    
    def on_grouping_change(self):
        """Обработка изменения группировки"""
        if self.no_grouping.get():
            self.group_combo.config(state='disabled')
        else:
            self.group_combo.config(state='readonly')
    
    def reset_config(self):
        """Сброс настроек к значениям по умолчанию"""
        self.excel_path.set('')
        self.sheet_name.set('БП_1')
        self.output_base.set('business_process_diagram')
        self.output_format.set('html_interactive')
        self.subgroup_column.set('')
        self.show_detailed.set(False)
        self.critical_min_inputs.set(CRITICAL_MIN_INPUTS)
        self.critical_min_reuse.set(CRITICAL_MIN_REUSE)
        self.no_grouping.set(True)
        
        if self.config_file.exists():
            self.config_file.unlink()
        
        self.on_format_change()
        self.on_grouping_change()
        messagebox.showinfo("Сброс настроек", "Настройки сброшены к значениям по умолчанию")
    
    def generate_diagram(self):
        """Генерация диаграммы"""
        if not self.excel_path.get():
            messagebox.showerror("Ошибка", "Выберите файл Excel")
            return
        
        excel_path = Path(self.excel_path.get())
        if not excel_path.exists():
            messagebox.showerror("Ошибка", f"Файл не существует: {excel_path}")
            return
        
        if not self.output_base.get().strip():
            messagebox.showerror("Ошибка", "Введите имя для выходного файла")
            return
        
        try:
            self.status_var.set("Генерация диаграммы...")
            self.root.update()
            
            # Создание объекта Choices из настроек GUI
            choices = Choices(
                subgroup_column=self.subgroup_column.get() if not self.no_grouping.get() else None,
                show_detailed=self.show_detailed.get(),
                critical_min_inputs=self.critical_min_inputs.get(),
                critical_min_reuse=self.critical_min_reuse.get(),
                no_grouping=self.no_grouping.get(),
                output_format=self.output_format.get()
            )
            
            # Сохранение конфигурации
            self.save_config()
            
            # Импорт здесь чтобы избежать циклических импортов
            from main import run_with_gui
            success = run_with_gui(excel_path, self.sheet_name.get(), choices, self.output_base.get())
            
            if success:
                self.status_var.set("Диаграмма успешно создана!")
                messagebox.showinfo("Успех", f"Диаграмма успешно создана!\nФайл: {self.output_base.get()}.html")
            else:
                self.status_var.set("Ошибка при создании диаграммы")
                
        except Exception as e:
            self.status_var.set(f"Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
        finally:
            self.root.update()

def run_gui():
    """Запуск графического интерфейса"""
    root = tk.Tk()
    app = BusinessProcessGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()