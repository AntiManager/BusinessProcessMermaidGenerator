"""
Графический интерфейс для генератора диаграмм бизнес-процессов
РЕФАКТОРИНГ: Устранение циклических импортов
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any
from models import Choices
from config import CRITICAL_MIN_INPUTS, CRITICAL_MIN_REUSE
# ИСПРАВЛЕННЫЙ ИМПОРТ - без цикла!
from core_api import run_with_gui

class BusinessProcessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор диаграмм бизнес-процессов v3.0")
        self.root.geometry("950x750")
        self.root.minsize(850, 700)
        
        # Загрузка конфигурации
        self.config_file = Path("bp_config.json")
        self.config = self.load_config()
        
        # Инициализация переменных интерфейса
        self._init_variables()
        self.create_widgets()
        
        # Загружаем листы если файл уже выбран
        if self.excel_path.get() and Path(self.excel_path.get()).exists():
            self.load_sheet_names()
        
    def _init_variables(self):
        """Инициализация переменных интерфейса"""
        # Основные переменные
        self.excel_path = tk.StringVar(value=self.config.get('excel_path', ''))
        self.sheet_name = tk.StringVar(value=self.config.get('sheet_name', ''))
        self.sheet_names = []
        self.output_base = tk.StringVar(value=self.config.get('output_base', 'business_process_diagram'))
        self.output_format = tk.StringVar(value=self.config.get('output_format', 'html_mermaid'))
        self.subgroup_column = tk.StringVar(value=self.config.get('subgroup_column', ''))
        self.show_detailed = tk.BooleanVar(value=self.config.get('show_detailed', False))
        self.critical_min_inputs = tk.IntVar(value=self.config.get('critical_min_inputs', CRITICAL_MIN_INPUTS))
        self.critical_min_reuse = tk.IntVar(value=self.config.get('critical_min_reuse', CRITICAL_MIN_REUSE))
        self.no_grouping = tk.BooleanVar(value=self.config.get('no_grouping', True))
        
        # CLD переменные
        self.cld_source_type = tk.StringVar(value=self.config.get('cld_source_type', 'auto'))
        self.cld_sheet_name = tk.StringVar(value=self.config.get('cld_sheet_name', ''))
        self.show_cld_operations = tk.BooleanVar(value=self.config.get('show_cld_operations', True))
        self.cld_influence_signs = tk.BooleanVar(value=self.config.get('cld_influence_signs', True))
        
        # UI элементы
        self.sheet_combobox = None
        self.cld_sheet_combobox = None
        self.cld_frame = None
        self.group_combo = None
        self.status_var = tk.StringVar(value="Готов к работе. Выберите файл Excel.")
        
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
                'no_grouping': self.no_grouping.get(),
                'cld_source_type': self.cld_source_type.get(),
                'cld_sheet_name': self.cld_sheet_name.get(),
                'show_cld_operations': self.show_cld_operations.get(),
                'cld_influence_signs': self.cld_influence_signs.get()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def load_sheet_names(self):
        """Загрузка списка листов из выбранного файла Excel"""
        try:
            excel_file = pd.ExcelFile(self.excel_path.get(), engine="openpyxl")
            self.sheet_names = excel_file.sheet_names
            
            # Обновляем combobox основного листа
            self.sheet_combobox['values'] = self.sheet_names
            
            # Обновляем combobox для CLD листа
            self.cld_sheet_combobox['values'] = self.sheet_names
            
            # Устанавливаем значение по умолчанию для основного листа
            if self.sheet_names:
                if self.sheet_name.get() in self.sheet_names:
                    self.sheet_combobox.set(self.sheet_name.get())
                else:
                    # Ищем лист с типичными названиями
                    default_sheets = ['БП_1', 'Sheet1', 'Лист1', 'Data']
                    for sheet in default_sheets:
                        if sheet in self.sheet_names:
                            self.sheet_combobox.set(sheet)
                            self.sheet_name.set(sheet)
                            break
                    else:
                        # Берем первый лист
                        self.sheet_combobox.set(self.sheet_names[0])
                        self.sheet_name.set(self.sheet_names[0])
            
            self.status_var.set(f"Загружено {len(self.sheet_names)} листов")
            
        except Exception as e:
            self.status_var.set(f"Ошибка чтения файла: {e}")
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл Excel:\n{e}")
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Основной фрейм с прокруткой
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройки колонок и строк для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Генератор диаграмм бизнес-процессов v3.0", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        row = 1
        
        # Выбор файла Excel
        ttk.Label(main_frame, text="Файл Excel:*", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=2)
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        file_frame.columnconfigure(0, weight=1)
        
        file_entry = ttk.Entry(file_frame, textvariable=self.excel_path)
        file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(file_frame, text="Обзор...", command=self.browse_file).grid(row=0, column=1)
        row += 1
        
        # Выбор листа
        ttk.Label(main_frame, text="Лист:*", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=2)
        sheet_frame = ttk.Frame(main_frame)
        sheet_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        self.sheet_combobox = ttk.Combobox(sheet_frame, textvariable=self.sheet_name, state="readonly", width=30)
        self.sheet_combobox.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.sheet_combobox.bind('<<ComboboxSelected>>', self.on_sheet_selected)
        
        ttk.Button(sheet_frame, text="Обновить", command=self.load_sheet_names, width=10).grid(row=0, column=1, padx=(5, 0))
        sheet_frame.columnconfigure(0, weight=1)
        row += 1
        
        # Имя выходного файла
        ttk.Label(main_frame, text="Имя выходного файла:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.output_base, width=30).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Формат вывода
        ttk.Label(main_frame, text="Формат вывода:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=2)
        format_frame = ttk.Frame(main_frame)
        format_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)

        formats = [
            ("📄 Markdown с Mermaid", "md"),
            ("🌐 HTML с Mermaid (рекомендуется)", "html_mermaid"),
            ("🎮 Интерактивный HTML", "html_interactive"),
            ("🔄 Causal Loop Diagram (Mermaid)", "cld_mermaid"),
            ("🔄 Causal Loop Diagram (Interactive)", "cld_interactive")
        ]

        for i, (text, value) in enumerate(formats):
            rb = ttk.Radiobutton(format_frame, text=text, variable=self.output_format, 
                                value=value, command=self.on_format_change)
            rb.grid(row=i//3, column=i%3, sticky=tk.W, padx=(0, 20), pady=2)
        row += 2  # Уменьшил с 3 до 2 тк меньше форматов
        
        # Секция настроек CLD (изначально скрыта)
        self.cld_frame = ttk.LabelFrame(main_frame, text="Настройки Causal Loop Diagram", padding="10")
        self.cld_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        self.cld_frame.grid_remove()  # Скрываем по умолчанию
        
        # Источник данных CLD
        ttk.Label(self.cld_frame, text="Источник данных:").grid(row=0, column=0, sticky=tk.W, pady=2)
        source_frame = ttk.Frame(self.cld_frame)
        source_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Radiobutton(source_frame, text="Авто из бизнес-процессов", 
                       variable=self.cld_source_type, value="auto", 
                       command=self.on_cld_source_change).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(source_frame, text="Из отдельного листа", 
                       variable=self.cld_source_type, value="manual",
                       command=self.on_cld_source_change).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Выбор листа для CLD
        ttk.Label(self.cld_frame, text="Лист CLD данных:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.cld_sheet_combobox = ttk.Combobox(self.cld_frame, textvariable=self.cld_sheet_name, 
                                              state="readonly", width=30)
        self.cld_sheet_combobox.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.cld_sheet_combobox.bind('<<ComboboxSelected>>', self.on_cld_sheet_selected)
        
        # Настройки отображения CLD
        ttk.Checkbutton(self.cld_frame, text="Показывать операции на связях",
                       variable=self.show_cld_operations).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Checkbutton(self.cld_frame, text="Показывать знаки влияния (+/-)",
                       variable=self.cld_influence_signs).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        row += 1
        
        # Группировка
        ttk.Label(main_frame, text="Группировка операций:").grid(row=row, column=0, sticky=tk.W, pady=2)
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
        ttk.Checkbutton(main_frame, text="Показывать подробное описание в узлах", 
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
        button_frame.grid(row=row, column=0, columnspan=3, pady=25)
        
        ttk.Button(button_frame, text="🎯 Сгенерировать диаграмму", 
                  command=self.generate_diagram, style='Accent.TButton', width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="💾 Сохранить настройки", 
                  command=self.save_config, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🔄 Сбросить настройки", 
                  command=self.reset_config, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ Выход", 
                  command=self.root.quit, width=10).pack(side=tk.LEFT)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе. Выберите файл Excel.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, padding=(5, 5))
        status_bar.grid(row=row+1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        
        # Информация о возможностях
        info_frame = ttk.LabelFrame(main_frame, text="Возможности форматов", padding="10")
        info_frame.grid(row=row+2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        info_frame.columnconfigure(0, weight=1)

        features = [
            "📄 Markdown - для документации и GitHub",
            "🌐 HTML с Mermaid - панорамирование и масштабирование", 
            "🎮 Интерактивный HTML - динамическая навигация",
            "🔄 Causal Loop - системная динамика и причинно-следственные связи"
        ]

        for i, feature in enumerate(features):
            ttk.Label(info_frame, text=feature).grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # Инициализация состояния
        self.on_format_change()
        self.on_grouping_change()
        self.on_cld_source_change()
    
    def on_sheet_selected(self, event):
        """Обработка выбора листа"""
        self.sheet_name.set(self.sheet_combobox.get())
    
    def on_cld_sheet_selected(self, event):
        """Обработка выбора листа для CLD"""
        self.cld_sheet_name.set(self.cld_sheet_combobox.get())
    
    def browse_file(self):
        """Выбор файла через диалоговое окно"""
        filename = filedialog.askopenfilename(
            title="Выберите файл Excel",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.excel_path.set(filename)
            # Загружаем список листов
            self.load_sheet_names()
            # Предложить имя выходного файла на основе имени Excel файла
            if not self.output_base.get() or self.output_base.get() == 'business_process_diagram':
                excel_stem = Path(filename).stem
                self.output_base.set(excel_stem + '_diagram')
            self.save_config()
    
    def on_format_change(self):
        """Обработка изменения формата вывода"""
        current_format = self.output_format.get()
        
        # Показываем/скрываем секцию CLD настроек
        if current_format in ["cld_mermaid", "cld_interactive"]:
            self.cld_frame.grid()  # Показываем
        else:
            self.cld_frame.grid_remove()  # Скрываем
        
        # Ограничения для других форматов
        if current_format == "html_interactive":
            self.no_grouping.set(True)
            self.show_detailed.set(False)
            self.on_grouping_change()
        elif current_format == "html_svg":
            self.no_grouping.set(True)
            self.show_detailed.set(True)
            self.on_grouping_change()
    
    def on_cld_source_change(self):
        """Обработчик изменения источника CLD данных"""
        if self.cld_source_type.get() == "manual":
            self.cld_sheet_combobox.config(state="readonly")
        else:
            self.cld_sheet_combobox.config(state="disabled")
    
    def on_grouping_change(self):
        """Обработка изменения группировки"""
        if self.no_grouping.get():
            self.group_combo.config(state='disabled')
        else:
            self.group_combo.config(state='readonly')
    
    def reset_config(self):
        """Сброс настроек к значениям по умолчанию"""
        self.excel_path.set('')
        self.sheet_name.set('')
        self.sheet_combobox.set('')
        self.sheet_combobox['values'] = []
        self.cld_sheet_combobox.set('')
        self.cld_sheet_combobox['values'] = []
        self.output_base.set('business_process_diagram')
        self.output_format.set('html_svg')
        self.subgroup_column.set('')
        self.show_detailed.set(False)
        self.critical_min_inputs.set(CRITICAL_MIN_INPUTS)
        self.critical_min_reuse.set(CRITICAL_MIN_REUSE)
        self.no_grouping.set(True)
        
        # Сброс настроек CLD
        self.cld_source_type.set('auto')
        self.cld_sheet_name.set('')
        self.show_cld_operations.set(True)
        self.cld_influence_signs.set(True)
        
        if self.config_file.exists():
            self.config_file.unlink()
        
        self.on_format_change()
        self.on_grouping_change()
        self.on_cld_source_change()
        self.status_var.set("Настройки сброшены. Выберите файл Excel.")
        messagebox.showinfo("Сброс настроек", "Настройки сброшены к значениям по умолчанию")
    
    def generate_diagram(self):
        """Генерация диаграммы - обновленный метод для использования нового API"""
        # Валидация выполняется в core_api.py, здесь только базовая проверка
        if not self.excel_path.get():
            messagebox.showerror("Ошибка", "Выберите файл Excel")
            return
        
        excel_path = Path(self.excel_path.get())
        if not excel_path.exists():
            messagebox.showerror("Ошибка", f"Файл не существует: {excel_path}")
            return
        
        try:
            self.status_var.set("Генерация диаграммы...")
            self.root.update_idletasks()
            
            # Создание объекта Choices из настроек GUI
            choices = Choices(
                subgroup_column=self.subgroup_column.get() if not self.no_grouping.get() else None,
                show_detailed=self.show_detailed.get(),
                critical_min_inputs=self.critical_min_inputs.get(),
                critical_min_reuse=self.critical_min_reuse.get(),
                no_grouping=self.no_grouping.get(),
                output_format=self.output_format.get(),
                cld_source_type=self.cld_source_type.get(),
                cld_sheet_name=self.cld_sheet_name.get(),
                show_cld_operations=self.show_cld_operations.get(),
                cld_influence_signs=self.cld_influence_signs.get()
            )
            
            # Сохранение конфигурации
            self.save_config()
            
            # Запуск генерации через новый core_api.py
            success = run_with_gui(excel_path, self.sheet_name.get(), choices, self.output_base.get())
            
            if success:
                self.status_var.set("Диаграмма успешно создана!")
                messagebox.showinfo("Успех", 
                    f"Диаграмма успешно создана!\n\n"
                    f"Файл: {self.output_base.get()}.html\n\n"
                    f"Диаграмма автоматически откроется в браузере.")
            else:
                self.status_var.set("Ошибка при создании диаграммы")
                # Сообщение об ошибке будет показано через logging в core_api.py
                
        except Exception as e:
            self.status_var.set(f"Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Произошла ошибка при создании диаграммы:\n{str(e)}")
        finally:
            self.root.update_idletasks()

def run_gui():
    """Запуск графического интерфейса"""
    root = tk.Tk()
    
    # Стиль для акцентных кнопок
    style = ttk.Style()
    style.configure('Accent.TButton', foreground='white', background='#007cba')
    
    app = BusinessProcessGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()