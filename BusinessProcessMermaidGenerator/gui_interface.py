"""
Графический интерфейс для генератора диаграмм бизнес-процессов
РАЗДЕЛЕНИЕ: БП-диаграммы и CLD из разных источников
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, List
from models import Choices
from config import CRITICAL_MIN_INPUTS, CRITICAL_MIN_REUSE
from core_api import run_with_gui

class BusinessProcessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор диаграмм бизнес-процессов v3.5")
        self.root.geometry("900x750")  # Увеличили высоту для новой кнопки
        self.root.minsize(850, 600)
        
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
        self.output_directory = tk.StringVar(value=self.config.get('output_directory', ''))  # НОВАЯ ПЕРЕМЕННАЯ
        
        # Переменные для мультивыбора форматов - БП + авто-CLD
        self.bp_formats = {
            'md': tk.BooleanVar(value=self.config.get('bp_md', False)),
            'html_mermaid': tk.BooleanVar(value=self.config.get('bp_html_mermaid', True)),
            'html_interactive': tk.BooleanVar(value=self.config.get('bp_html_interactive', False)),
            'cld_mermaid_auto': tk.BooleanVar(value=self.config.get('cld_mermaid_auto', False)),  # CLD авто из БП
            'cld_interactive_auto': tk.BooleanVar(value=self.config.get('cld_interactive_auto', False))  # CLD авто из БП
        }
        
        # Переменные для CLD вкладки (только ручной режим)
        self.cld_formats = {
            'cld_mermaid_manual': tk.BooleanVar(value=self.config.get('cld_mermaid_manual', False)),
            'cld_interactive_manual': tk.BooleanVar(value=self.config.get('cld_interactive_manual', True))
        }
        
        # Общие настройки для БП
        self.subgroup_column = tk.StringVar(value=self.config.get('subgroup_column', ''))
        self.show_detailed = tk.BooleanVar(value=self.config.get('show_detailed', False))
        self.critical_min_inputs = tk.IntVar(value=self.config.get('critical_min_inputs', CRITICAL_MIN_INPUTS))
        self.critical_min_reuse = tk.IntVar(value=self.config.get('critical_min_reuse', CRITICAL_MIN_REUSE))
        self.no_grouping = tk.BooleanVar(value=self.config.get('no_grouping', True))
        
        # CLD переменные (только для ручного режима)
        self.cld_sheet_name = tk.StringVar(value=self.config.get('cld_sheet_name', ''))
        self.show_cld_operations = tk.BooleanVar(value=self.config.get('show_cld_operations', True))
        self.cld_influence_signs = tk.BooleanVar(value=self.config.get('cld_influence_signs', True))
        
        # UI элементы
        self.sheet_combobox = None
        self.cld_sheet_combobox = None
        self.notebook = None
        
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
                'output_directory': self.output_directory.get(),  # СОХРАНЯЕМ ПУТЬ
                
                # Сохраняем состояния форматов
                'bp_md': self.bp_formats['md'].get(),
                'bp_html_mermaid': self.bp_formats['html_mermaid'].get(),
                'bp_html_interactive': self.bp_formats['html_interactive'].get(),
                'cld_mermaid_auto': self.bp_formats['cld_mermaid_auto'].get(),
                'cld_interactive_auto': self.bp_formats['cld_interactive_auto'].get(),
                'cld_mermaid_manual': self.cld_formats['cld_mermaid_manual'].get(),
                'cld_interactive_manual': self.cld_formats['cld_interactive_manual'].get(),
                
                'subgroup_column': self.subgroup_column.get(),
                'show_detailed': self.show_detailed.get(),
                'critical_min_inputs': self.critical_min_inputs.get(),
                'critical_min_reuse': self.critical_min_reuse.get(),
                'no_grouping': self.no_grouping.get(),
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
            if self.sheet_combobox:
                self.sheet_combobox['values'] = self.sheet_names
            
            # Обновляем combobox для CLD листа
            if self.cld_sheet_combobox:
                self.cld_sheet_combobox['values'] = self.sheet_names
            
            # Устанавливаем значение по умолчанию для основного листа
            if self.sheet_names and self.sheet_combobox:
                if self.sheet_name.get() in self.sheet_names:
                    self.sheet_combobox.set(self.sheet_name.get())
                else:
                    default_sheets = ['БП_1', 'Sheet1', 'Лист1', 'Data']
                    for sheet in default_sheets:
                        if sheet in self.sheet_names:
                            self.sheet_combobox.set(sheet)
                            self.sheet_name.set(sheet)
                            break
                    else:
                        self.sheet_combobox.set(self.sheet_names[0])
                        self.sheet_name.set(self.sheet_names[0])
            
            # Автоматически устанавливаем папку для отчетов в папку с Excel-файлом, если не задана
            if not self.output_directory.get():
                excel_dir = Path(self.excel_path.get()).parent
                self.output_directory.set(str(excel_dir))
            
            self.status_var.set(f"Загружено {len(self.sheet_names)} листов")
            
        except Exception as e:
            self.status_var.set(f"Ошибка чтения файла: {e}")
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл Excel:\n{e}")
    
    def create_widgets(self):
        """Создание компактного интерфейса с вкладками"""
        # Основной контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Настройки растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_container, 
                               text="Генератор диаграмм бизнес-процессов v3.5", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        # Область с вкладками
        self.notebook = ttk.Notebook(main_container)
        self.notebook.grid(row=1, column=0, sticky=tk.NSEW, pady=(0, 8))
        
        # Создаем вкладки
        self.bp_frame = self.create_bp_tab()
        self.cld_frame = self.create_cld_tab()
        
        self.notebook.add(self.bp_frame, text="📊 Бизнес-процессы")
        self.notebook.add(self.cld_frame, text="🔄 Causal Loop Diagrams")
        
        # НОВЫЙ БЛОК: Выбор папки для отчетов
        output_dir_frame = ttk.LabelFrame(main_container, text="📁 Папка для сохранения отчетов", padding="5")
        output_dir_frame.grid(row=2, column=0, sticky=tk.EW, pady=(0, 8))
        output_dir_frame.columnconfigure(0, weight=1)
        
        dir_selection_frame = ttk.Frame(output_dir_frame)
        dir_selection_frame.grid(row=0, column=0, sticky=tk.EW, pady=2)
        dir_selection_frame.columnconfigure(0, weight=1)
        
        # Поле для отображения пути и кнопка выбора
        dir_entry = ttk.Entry(dir_selection_frame, textvariable=self.output_directory)
        dir_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        
        ttk.Button(dir_selection_frame, text="Обзор...", 
                  command=self.browse_output_directory).grid(row=0, column=1)
        
        ttk.Button(dir_selection_frame, text="Сбросить", 
                  command=self.reset_output_directory).grid(row=0, column=2, padx=(5, 0))
        
        # Подсказка
        hint_label = ttk.Label(output_dir_frame, 
                              text="По умолчанию: папка с Excel-файлом. Нажмите 'Обзор...' для выбора другой папки.",
                              font=('Arial', 8), 
                              foreground='#666666')
        hint_label.grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        
        # Кнопки управления
        self.create_control_buttons(main_container)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе. Выберите файл Excel.")
        status_bar = ttk.Label(main_container, textvariable=self.status_var, 
                              relief=tk.SUNKEN, padding=(3, 3))
        status_bar.grid(row=4, column=0, sticky=tk.EW, pady=(5, 0))
    
    def create_bp_tab(self) -> ttk.Frame:
        """Создание вкладки бизнес-процессов с авто-CLD"""
        frame = ttk.Frame(self.notebook, padding="5")
        
        # Настройки grid для компактности
        for i in range(10):
            frame.rowconfigure(i, weight=0)
        frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Выбор файла Excel
        ttk.Label(frame, text="Файл Excel:*", font=('Arial', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=1)
        file_frame = ttk.Frame(frame)
        file_frame.grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=1)
        file_frame.columnconfigure(0, weight=1)
        
        file_entry = ttk.Entry(file_frame, textvariable=self.excel_path)
        file_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        ttk.Button(file_frame, text="Обзор...", command=self.browse_file).grid(row=0, column=1)
        row += 1
        
        # Выбор листа с бизнес-процессами
        ttk.Label(frame, text="Лист с БП:*", font=('Arial', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=1)
        sheet_frame = ttk.Frame(frame)
        sheet_frame.grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=1)
        
        self.sheet_combobox = ttk.Combobox(sheet_frame, textvariable=self.sheet_name, 
                                          state="readonly")
        self.sheet_combobox.grid(row=0, column=0, sticky=tk.EW)
        self.sheet_combobox.bind('<<ComboboxSelected>>', self.on_sheet_selected)
        
        ttk.Button(sheet_frame, text="Обновить", command=self.load_sheet_names, 
                  width=8).grid(row=0, column=1, padx=(5, 0))
        sheet_frame.columnconfigure(0, weight=1)
        row += 1
        
        # Имя выходного файла
        ttk.Label(frame, text="Имя файла:").grid(
            row=row, column=0, sticky=tk.W, pady=1)
        ttk.Entry(frame, textvariable=self.output_base).grid(
            row=row, column=1, sticky=tk.EW, pady=1)
        row += 1
        
        # Разделитель
        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=tk.EW, pady=8)
        row += 1
        
        # Форматы вывода (БП + авто-CLD)
        ttk.Label(frame, text="Форматы БП:", font=('Arial', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=1)
        format_frame = ttk.Frame(frame)
        format_frame.grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=1)
        
        bp_formats = [
            ("📄 Markdown + интерактивная", "md"),
            ("🌐 HTML + интерактивная", "html_mermaid"),
            ("🎮 Только интерактивная", "html_interactive")
        ]
        
        for i, (text, key) in enumerate(bp_formats):
            cb = ttk.Checkbutton(format_frame, text=text, variable=self.bp_formats[key])
            cb.grid(row=0, column=i, sticky=tk.W, padx=(0, 10))
        row += 1
        
        # CLD форматы (авто из БП)
        ttk.Label(frame, text="CLD (авто из БП):", font=('Arial', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=1)
        cld_format_frame = ttk.Frame(frame)
        cld_format_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=1)
        
        cld_formats = [
            ("🔄 CLD Mermaid + интерактивная", "cld_mermaid_auto"),
            ("🎮 Только интерактивный CLD", "cld_interactive_auto")
        ]
        
        for i, (text, key) in enumerate(cld_formats):
            cb = ttk.Checkbutton(cld_format_frame, text=text, variable=self.bp_formats[key])
            cb.grid(row=0, column=i, sticky=tk.W, padx=(0, 15))
        row += 1
        
        # Группировка
        ttk.Label(frame, text="Группировка:").grid(
            row=row, column=0, sticky=tk.W, pady=2)
        group_frame = ttk.Frame(frame)
        group_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)
        
        ttk.Radiobutton(group_frame, text="Без группировки", variable=self.no_grouping,
                       value=True, command=self.on_grouping_change).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(group_frame, text="Группировать по:", variable=self.no_grouping,
                       value=False, command=self.on_grouping_change).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        self.group_combo = ttk.Combobox(group_frame, textvariable=self.subgroup_column, 
                                       values=['Группа', 'Владелец'], state='readonly', width=10)
        self.group_combo.grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        row += 1
        
        # Настройки
        settings_frame = ttk.Frame(frame)
        settings_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=2)
        
        ttk.Checkbutton(settings_frame, text="Подробное описание", 
                       variable=self.show_detailed).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(settings_frame, text="Мин. входов:").grid(row=0, column=1, sticky=tk.W, padx=(15, 0))
        ttk.Spinbox(settings_frame, from_=1, to=20, textvariable=self.critical_min_inputs,
                   width=4).grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(settings_frame, text="Исп. выходов:").grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        ttk.Spinbox(settings_frame, from_=1, to=20, textvariable=self.critical_min_reuse,
                   width=4).grid(row=0, column=4, sticky=tk.W, padx=(5, 0))
        
        settings_frame.columnconfigure(0, weight=1)
        
        return frame
    
    def create_cld_tab(self) -> ttk.Frame:
        """Создание вкладки CLD (только ручной режим из отдельного листа)"""
        frame = ttk.Frame(self.notebook, padding="5")
        
        # Настройки grid для компактности
        for i in range(8):
            frame.rowconfigure(i, weight=0)
        frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Выбор файла Excel
        ttk.Label(frame, text="Файл Excel:*", font=('Arial', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=1)
        file_frame = ttk.Frame(frame)
        file_frame.grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=1)
        file_frame.columnconfigure(0, weight=1)
        
        file_entry = ttk.Entry(file_frame, textvariable=self.excel_path)
        file_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        ttk.Button(file_frame, text="Обзор...", command=self.browse_file).grid(row=0, column=1)
        row += 1
        
        # Выбор листа с CLD данными
        ttk.Label(frame, text="Лист с CLD:*", font=('Arial', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=1)
        cld_sheet_frame = ttk.Frame(frame)
        cld_sheet_frame.grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=1)
        
        self.cld_sheet_combobox = ttk.Combobox(cld_sheet_frame, textvariable=self.cld_sheet_name, 
                                              state="readonly")
        self.cld_sheet_combobox.grid(row=0, column=0, sticky=tk.EW)
        self.cld_sheet_combobox.bind('<<ComboboxSelected>>', self.on_cld_sheet_selected)
        cld_sheet_frame.columnconfigure(0, weight=1)
        row += 1
        
        # Имя выходного файла
        ttk.Label(frame, text="Имя файла:").grid(
            row=row, column=0, sticky=tk.W, pady=1)
        ttk.Entry(frame, textvariable=self.output_base).grid(
            row=row, column=1, sticky=tk.EW, pady=1)
        row += 1
        
        # Разделитель
        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=tk.EW, pady=8)
        row += 1
        
        # Форматы вывода CLD (только ручной режим)
        ttk.Label(frame, text="Форматы CLD:", font=('Arial', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=1)
        format_frame = ttk.Frame(frame)
        format_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=1)
        
        formats = [
            ("🔄 CLD Mermaid + интерактивная", "cld_mermaid_manual"),
            ("🎮 Только интерактивный CLD", "cld_interactive_manual")
        ]
        
        for i, (text, key) in enumerate(formats):
            cb = ttk.Checkbutton(format_frame, text=text, variable=self.cld_formats[key])
            cb.grid(row=0, column=i, sticky=tk.W, padx=(0, 15))
        row += 1
        
        # Настройки CLD
        ttk.Label(frame, text="Настройки:").grid(
            row=row, column=0, sticky=tk.W, pady=2)
        settings_frame = ttk.Frame(frame)
        settings_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(settings_frame, text="Операции на связях",
                       variable=self.show_cld_operations).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(settings_frame, text="Знаки влияния",
                       variable=self.cld_influence_signs).grid(row=0, column=1, sticky=tk.W, padx=(15, 0))
        
        # Информация о формате данных
        info_frame = ttk.Frame(frame)
        info_frame.grid(row=row+1, column=0, columnspan=3, sticky=tk.EW, pady=5)
        info_label = ttk.Label(info_frame, 
                              text="📋 Формат CLD данных: колонки 'Источник', 'Цель', 'Знак влияния'",
                              font=('Arial', 8), foreground='#666666')
        info_label.pack()
        
        return frame
    
    def create_control_buttons(self, parent):
        """Создание компактных кнопок управления"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, sticky=tk.EW, pady=8)
        
        # Конфигурация колонок для равномерного распределения
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)
        
        # Кнопки с правильными цветами
        generate_btn = tk.Button(button_frame, text="🎯 Сгенерировать диаграммы", 
                               command=self.generate_diagrams,
                               bg="#007cba", fg="white",
                               font=('Arial', 10, 'bold'),
                               relief=tk.RAISED, bd=2)
        generate_btn.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        
        save_btn = tk.Button(button_frame, text="💾 Сохранить настройки", 
                           command=self.save_config,
                           bg="#28a745", fg="white",
                           font=('Arial', 9),
                           relief=tk.RAISED, bd=1)
        save_btn.grid(row=0, column=1, sticky=tk.EW, padx=2)
        
        reset_btn = tk.Button(button_frame, text="🔄 Сбросить настройки", 
                            command=self.reset_config,
                            bg="#ffc107", fg="black",
                            font=('Arial', 9),
                            relief=tk.RAISED, bd=1)
        reset_btn.grid(row=0, column=2, sticky=tk.EW, padx=2)
        
        exit_btn = tk.Button(button_frame, text="❌ Выход", 
                           command=self.root.quit,
                           bg="#dc3545", fg="white",
                           font=('Arial', 9),
                           relief=tk.RAISED, bd=1)
        exit_btn.grid(row=0, column=3, sticky=tk.EW, padx=(5, 0))
    
    def browse_output_directory(self):
        """Выбор папки для сохранения отчетов"""
        directory = filedialog.askdirectory(
            title="Выберите папку для сохранения отчетов"
        )
        if directory:
            self.output_directory.set(directory)
            self.save_config()
    
    def reset_output_directory(self):
        """Сброс папки для отчетов к папке с Excel-файлом"""
        if self.excel_path.get():
            excel_dir = Path(self.excel_path.get()).parent
            self.output_directory.set(str(excel_dir))
        else:
            self.output_directory.set("")
        self.save_config()
    
    def get_selected_formats(self) -> List[str]:
        """Получение списка выбранных форматов с учетом типа источника"""
        formats = []
        active_tab = self.notebook.index(self.notebook.select())
        
        if active_tab == 0:  # Вкладка БП
            for fmt, var in self.bp_formats.items():
                if var.get():
                    # Для авто-CLD форматов добавляем суффикс
                    if fmt in ['cld_mermaid_auto', 'cld_interactive_auto']:
                        # Убираем суффикс '_auto' для совместимости с core_api
                        formats.append(fmt.replace('_auto', ''))
                    else:
                        formats.append(fmt)
        else:  # Вкладка CLD (ручной режим)
            for fmt, var in self.cld_formats.items():
                if var.get():
                    # Для ручных CLD форматов добавляем суффикс
                    if fmt in ['cld_mermaid_manual', 'cld_interactive_manual']:
                        # Убираем суффикс '_manual' для совместимости с core_api
                        formats.append(fmt.replace('_manual', ''))
        
        return formats
    
    def generate_diagrams(self):
        """Генерация диаграмм для выбранных форматов"""
        if not self.excel_path.get():
            messagebox.showerror("Ошибка", "Выберите файл Excel")
            return
        
        excel_path = Path(self.excel_path.get())
        if not excel_path.exists():
            messagebox.showerror("Ошибка", f"Файл не существует: {excel_path}")
            return
        
        selected_formats = self.get_selected_formats()
        if not selected_formats:
            messagebox.showwarning("Внимание", "Выберите хотя бы один формат вывода")
            return
        
        try:
            self.status_var.set("Генерация диаграмм...")
            self.root.update_idletasks()
            
            # Сохранение конфигурации
            self.save_config()
            
            success_count = 0
            total_count = len(selected_formats)
            active_tab = self.notebook.index(self.notebook.select())
            
            for output_format in selected_formats:
                try:
                    # Определяем параметры в зависимости от вкладки и типа формата
                    if active_tab == 0:  # Вкладка БП
                        # Все форматы на вкладке БП используют авто-CLD
                        sheet_to_use = self.sheet_name.get()
                        cld_source_type = "auto"
                        cld_sheet_to_use = ""  # Для авто-CLD не нужен отдельный лист
                    else:  # Вкладка CLD
                        # Все форматы на вкладке CLD используют ручной режим
                        sheet_to_use = self.cld_sheet_name.get()  # Главный лист - CLD данные
                        cld_source_type = "manual"
                        cld_sheet_to_use = self.cld_sheet_name.get()
                    
                    if not sheet_to_use:
                        messagebox.showerror("Ошибка", "Не выбран лист для генерации")
                        continue
                    
                    # Для CLD форматов на вкладке БП используем настройки БП, для CLD вкладки - CLD настройки
                    choices = Choices(
                        subgroup_column=self.subgroup_column.get() if not self.no_grouping.get() and active_tab == 0 else None,
                        show_detailed=self.show_detailed.get() if active_tab == 0 else False,
                        critical_min_inputs=self.critical_min_inputs.get() if active_tab == 0 else 3,
                        critical_min_reuse=self.critical_min_reuse.get() if active_tab == 0 else 3,
                        no_grouping=self.no_grouping.get() if active_tab == 0 else True,
                        output_format=output_format,
                        cld_source_type=cld_source_type,
                        cld_sheet_name=cld_sheet_to_use,
                        show_cld_operations=self.show_cld_operations.get(),
                        cld_influence_signs=self.cld_influence_signs.get(),
                        output_directory=self.output_directory.get()  # ПЕРЕДАЕМ ПУТЬ СОХРАНЕНИЯ
                    )
                    
                    success = run_with_gui(excel_path, sheet_to_use, choices, self.output_base.get())
                    if success:
                        success_count += 1
                    
                except Exception as e:
                    print(f"Ошибка при генерации формата {output_format}: {e}")
            
            if success_count > 0:
                self.status_var.set(f"Успешно создано {success_count}/{total_count} форматов")
                messagebox.showinfo("Успех", 
                    f"Диаграммы успешно созданы!\n\n"
                    f"Успешно сгенерировано: {success_count} из {total_count} форматов\n\n"
                    f"Основные диаграммы автоматически открываются в браузере.")
            else:
                self.status_var.set("Ошибка при создании диаграмм")
                
        except Exception as e:
            self.status_var.set(f"Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Произошла ошибка при создании диаграмм:\n{str(e)}")
        finally:
            self.root.update_idletasks()

    # Остальные методы остаются без изменений
    def on_sheet_selected(self, event):
        self.sheet_name.set(self.sheet_combobox.get())
    
    def on_cld_sheet_selected(self, event):
        self.cld_sheet_name.set(self.cld_sheet_combobox.get())
    
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите файл Excel",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.excel_path.set(filename)
            self.load_sheet_names()
            if not self.output_base.get() or self.output_base.get() == 'business_process_diagram':
                excel_stem = Path(filename).stem
                self.output_base.set(excel_stem + '_diagram')
            
            # Автоматически устанавливаем папку для отчетов в папку с Excel-файлом, если не задана
            if not self.output_directory.get():
                excel_dir = Path(filename).parent
                self.output_directory.set(str(excel_dir))
            
            self.save_config()
    
    def on_grouping_change(self):
        if self.no_grouping.get():
            if self.group_combo:
                self.group_combo.config(state='disabled')
        else:
            if self.group_combo:
                self.group_combo.config(state='readonly')
    
    def reset_config(self):
        """Сброс настроек к значениям по умолчанию"""
        self.excel_path.set('')
        self.sheet_name.set('')
        if self.sheet_combobox:
            self.sheet_combobox.set('')
            self.sheet_combobox['values'] = []
        if self.cld_sheet_combobox:
            self.cld_sheet_combobox.set('')
            self.cld_sheet_combobox['values'] = []
        self.output_base.set('business_process_diagram')
        self.output_directory.set('')  # СБРАСЫВАЕМ ПУТЬ
        
        # Сброс форматов
        self.bp_formats['md'].set(False)
        self.bp_formats['html_mermaid'].set(True)
        self.bp_formats['html_interactive'].set(False)
        self.bp_formats['cld_mermaid_auto'].set(False)
        self.bp_formats['cld_interactive_auto'].set(False)
        self.cld_formats['cld_mermaid_manual'].set(False)
        self.cld_formats['cld_interactive_manual'].set(True)
        
        self.subgroup_column.set('')
        self.show_detailed.set(False)
        self.critical_min_inputs.set(CRITICAL_MIN_INPUTS)
        self.critical_min_reuse.set(CRITICAL_MIN_REUSE)
        self.no_grouping.set(True)
        
        # Сброс настроек CLD
        self.cld_sheet_name.set('')
        self.show_cld_operations.set(True)
        self.cld_influence_signs.set(True)
        
        if self.config_file.exists():
            self.config_file.unlink()
        
        self.on_grouping_change()
        self.status_var.set("Настройки сброшены. Выберите файл Excel.")
        messagebox.showinfo("Сброс настроек", "Настройки сброшены к значениям по умолчанию")

def run_gui():
    """Запуск графического интерфейса"""
    root = tk.Tk()
    app = BusinessProcessGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()