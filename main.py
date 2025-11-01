import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, scrolledtext
import psutil
import time
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import sys
import webbrowser
from datetime import datetime
import GPUtil
from screeninfo import get_monitors
import platform


class SystemMonitor:
    def __init__(self, root):
        self.start_time = time.time()
        self.root = root
        self.root.title("🚀 System Monitoring Tool v1.0.0")
        self.root.geometry("1400x900")

        self.settings = self.load_settings()
        self.theme_mode = self.settings.get('theme', 'dark')
        self.button_style = self.settings.get('button_style', 'modern')

        self.themes = {
            'dark': {
                'bg': '#2c3e50',
                'card': '#34495e',
                'text': 'white',
                'primary': '#3498db',
                'secondary': '#e74c3c',
                'accent': '#9b59b6'
            },
            'light': {
                'bg': '#ecf0f1',
                'card': '#ffffff',
                'text': '#2c3e50',
                'primary': '#2980b9',
                'secondary': '#c0392b',
                'accent': '#8e44ad'
            }
        }

        self.button_styles = {
            'modern': {'relief': 'flat', 'borderwidth': 2},
            'classic': {'relief': 'raised', 'borderwidth': 4},
            'minimal': {'relief': 'flat', 'borderwidth': 1}
        }

        self.current_theme = self.themes[self.theme_mode]
        self.root.configure(bg=self.current_theme['bg'])
        self.setup_styles()

        self.running = True
        self.cpu_data = []
        self.mem_data = []
        self.disk_data = []
        self.net_data = []
        self.temp_data = []

        self.setup_ui()
        self.update_thread = threading.Thread(target=self.update_data, daemon=True)
        self.update_thread.start()

    def load_settings(self):
        settings_file = Path("system_monitor_settings.json")
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_settings(self):
        settings = {
            'theme': self.theme_mode,
            'button_style': self.button_style
        }
        with open("system_monitor_settings.json", 'w') as f:
            json.dump(settings, f, indent=4)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure('TFrame', background=self.current_theme['bg'])
        self.style.configure('TLabel', background=self.current_theme['bg'],
                             foreground=self.current_theme['text'])
        self.style.configure('TButton', background=self.current_theme['primary'],
                             foreground=self.current_theme['text'], **self.button_styles[self.button_style])
        self.style.configure('Header.TLabel', font=('Arial', 14, 'bold'),
                             foreground=self.current_theme['primary'])
        self.style.configure('Title.TLabel', font=('Arial', 18, 'bold'),
                             foreground=self.current_theme['secondary'])
        self.style.configure('Card.TFrame', background=self.current_theme['card'],
                             relief='raised', borderwidth=1)

        self.style.configure('TNotebook', background=self.current_theme['bg'])
        self.style.configure('TNotebook.Tab', background=self.current_theme['card'],
                             foreground=self.current_theme['text'], padding=[15, 5])
        self.style.map('TNotebook.Tab', background=[('selected', self.current_theme['primary'])])

    def setup_ui(self):
        self.setup_menu()

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        monitor_frame = ttk.Frame(notebook)
        notebook.add(monitor_frame, text="📊 Мониторинг")
        self.setup_monitor_tab(monitor_frame)

        process_frame = ttk.Frame(notebook)
        notebook.add(process_frame, text="⚙️ Процессы")
        self.setup_process_tab(process_frame)

        system_frame = ttk.Frame(notebook)
        notebook.add(system_frame, text="💻 Система")
        self.setup_system_tab(system_frame)

        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="🌐 Сеть")
        self.setup_network_tab(network_frame)

        startup_frame = ttk.Frame(notebook)
        notebook.add(startup_frame, text="🚀 Автозагрузка")
        self.setup_startup_tab(startup_frame)

        clean_frame = ttk.Frame(notebook)
        notebook.add(clean_frame, text="🧹 Очистка")
        self.setup_clean_tab(clean_frame)

        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="ℹ️ О программе")
        self.setup_about_tab(about_frame)

        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="⚙️ Настройки")
        self.setup_settings_tab(settings_frame)

        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', padding=5)
        status_bar.pack(side='bottom', fill='x')

        self.status_var.set("🟢 Готов к работе")
        self.setup_quick_access()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Экспорт отчета", command=self.export_reports)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)

        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Тема", menu=theme_menu)
        theme_menu.add_command(label="Темная", command=lambda: self.change_theme('dark'))
        theme_menu.add_command(label="Светлая", command=lambda: self.change_theme('light'))

        style_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Стиль кнопок", menu=style_menu)
        style_menu.add_command(label="Современный", command=lambda: self.change_button_style('modern'))
        style_menu.add_command(label="Классический", command=lambda: self.change_button_style('classic'))
        style_menu.add_command(label="Минималистичный", command=lambda: self.change_button_style('minimal'))

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
        help_menu.add_command(label="Проверить обновления", command=self.check_updates)

    def setup_settings_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        theme_frame = ttk.LabelFrame(main_frame, text="🎨 Настройки темы", padding=15)
        theme_frame.pack(fill='x', pady=(0, 15))

        ttk.Label(theme_frame, text="Выберите тему интерфейса:",
                  font=('Arial', 11)).pack(anchor='w', pady=(0, 10))

        theme_var = tk.StringVar(value=self.theme_mode)
        theme_frame_inner = ttk.Frame(theme_frame)
        theme_frame_inner.pack(fill='x')

        ttk.Radiobutton(theme_frame_inner, text="🌙 Темная тема", variable=theme_var,
                        value='dark', command=lambda: self.change_theme('dark')).pack(side='left', padx=10)
        ttk.Radiobutton(theme_frame_inner, text="☀️ Светлая тема", variable=theme_var,
                        value='light', command=lambda: self.change_theme('light')).pack(side='left', padx=10)

        style_frame = ttk.LabelFrame(main_frame, text="🔘 Стиль кнопок", padding=15)
        style_frame.pack(fill='x', pady=(0, 15))

        ttk.Label(style_frame, text="Выберите стиль кнопок:",
                  font=('Arial', 11)).pack(anchor='w', pady=(0, 10))

        style_var = tk.StringVar(value=self.button_style)
        style_frame_inner = ttk.Frame(style_frame)
        style_frame_inner.pack(fill='x')

        ttk.Radiobutton(style_frame_inner, text="🔄 Современный", variable=style_var,
                        value='modern', command=lambda: self.change_button_style('modern')).pack(side='left', padx=10)
        ttk.Radiobutton(style_frame_inner, text="🏛️ Классический", variable=style_var,
                        value='classic', command=lambda: self.change_button_style('classic')).pack(side='left', padx=10)
        ttk.Radiobutton(style_frame_inner, text="⚪ Минималистичный", variable=style_var,
                        value='minimal', command=lambda: self.change_button_style('minimal')).pack(side='left', padx=10)

        demo_frame = ttk.LabelFrame(main_frame, text="👀 Предпросмотр", padding=15)
        demo_frame.pack(fill='x', pady=(0, 15))

        ttk.Label(demo_frame, text="Пример кнопок в выбранном стиле:",
                  font=('Arial', 11)).pack(anchor='w', pady=(0, 10))

        demo_buttons = ttk.Frame(demo_frame)
        demo_buttons.pack(fill='x')

        for i, text in enumerate(["Основная", "Дополнительная", "Успех", "Ошибка"]):
            btn = ttk.Button(demo_buttons, text=text, width=15)
            btn.pack(side='left', padx=5)

        advanced_frame = ttk.LabelFrame(main_frame, text="⚙️ Дополнительно", padding=15)
        advanced_frame.pack(fill='x', pady=(0, 15))

        autostart_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Запускать при старте системы",
                        variable=autostart_var).pack(anchor='w', pady=2)

        notifications_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Включить уведомления",
                        variable=notifications_var).pack(anchor='w', pady=2)

        minimal_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Минималистичный режим",
                        variable=minimal_var).pack(anchor='w', pady=2)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=15)

        ttk.Button(control_frame, text="💾 Сохранить настройки",
                   command=self.save_settings, width=20).pack(side='left', padx=5)
        ttk.Button(control_frame, text="🔄 Сбросить настройки",
                   command=self.reset_settings, width=20).pack(side='left', padx=5)
        ttk.Button(control_frame, text="🚀 Применить",
                   command=self.apply_settings, width=20).pack(side='right', padx=5)

    def change_theme(self, theme):
        self.theme_mode = theme
        self.current_theme = self.themes[theme]
        self.setup_styles()
        self.update_ui_colors()

    def change_button_style(self, style):
        self.button_style = style
        self.setup_styles()
        self.save_settings()

    def update_ui_colors(self):
        self.root.configure(bg=self.current_theme['bg'])
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.configure(style='TFrame')
        self.save_settings()

    def reset_settings(self):
        if messagebox.askyesno("Сброс настроек", "Вы уверены, что хотите сбросить все настройки?"):
            self.theme_mode = 'dark'
            self.button_style = 'modern'
            self.current_theme = self.themes[self.theme_mode]
            self.setup_styles()
            self.update_ui_colors()
            messagebox.showinfo("Успех", "Настройки сброшены к значениям по умолчанию")

    def apply_settings(self):
        self.setup_styles()
        self.update_ui_colors()
        messagebox.showinfo("Успех", "Настройки применены")

    def setup_quick_access(self):
        quick_frame = ttk.Frame(self.root, height=50, style='Card.TFrame')
        quick_frame.pack(side='top', fill='x', padx=10, pady=5)
        quick_frame.pack_propagate(False)

        actions = [
            ("🔄 Обновить все", self.update_all, self.current_theme['primary']),
            ("📊 CPU", lambda: self.show_resource("CPU"), "#e74c3c"),
            ("💾 Память", lambda: self.show_resource("Memory"), "#3498db"),
            ("📁 Диск", lambda: self.show_resource("Disk"), "#2ecc71"),
            ("🌐 Сеть", lambda: self.show_resource("Network"), "#9b59b6"),
            ("⚙️ Настройки", lambda: self.show_resource("Settings"), "#f39c12")
        ]

        for text, command, color in actions:
            style_params = self.button_styles[self.button_style].copy()
            if 'relief' in style_params:
                del style_params['relief']

            btn = tk.Button(quick_frame, text=text, font=('Arial', 10, 'bold'),
                            bg=color, fg='white', relief='flat', cursor='hand2',
                            command=command, **style_params)
            btn.pack(side='left', padx=3, ipadx=8, ipady=3)

    def setup_monitor_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True)

        fig = Figure(figsize=(10, 8), dpi=100, facecolor='#2c3e50')
        fig.subplots_adjust(hspace=0.4, wspace=0.3)

        self.ax_cpu = fig.add_subplot(321)
        self.ax_mem = fig.add_subplot(322)
        self.ax_disk = fig.add_subplot(323)
        self.ax_net = fig.add_subplot(324)
        self.ax_temp = fig.add_subplot(325)

        for ax in [self.ax_cpu, self.ax_mem, self.ax_disk, self.ax_net, self.ax_temp]:
            ax.set_facecolor('#34495e')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('#7f8c8d')
            ax.title.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')

        self.canvas = FigureCanvasTkAgg(fig, left_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        right_frame = ttk.Frame(main_frame, width=250)
        right_frame.pack(side='right', fill='y', padx=(10, 0))
        right_frame.pack_propagate(False)

        ttk.Label(right_frame, text="📈 Показатели в реальном времени",
                  style='Header.TLabel').pack(pady=(0, 15))

        self.cpu_var = tk.StringVar(value="Загрузка CPU: 0%")
        self.mem_var = tk.StringVar(value="Исп. памяти: 0%")
        self.disk_var = tk.StringVar(value="Исп. диска: 0%")
        self.net_var = tk.StringVar(value="Сетевой трафик: 0 MB")
        self.temp_var = tk.StringVar(value="Температура: N/A")

        self.create_metric_card(right_frame, "💻 Процессор", self.cpu_var)
        self.create_metric_card(right_frame, "💾 Память", self.mem_var)
        self.create_metric_card(right_frame, "📁 Диск", self.disk_var)
        self.create_metric_card(right_frame, "🌐 Сеть", self.net_var)
        self.create_metric_card(right_frame, "🌡️ Температура", self.temp_var)

    def create_metric_card(self, parent, title, variable):
        card = ttk.Frame(parent, style='Card.TFrame', padding=12)
        card.pack(fill='x', pady=4)

        header_frame = ttk.Frame(card)
        header_frame.pack(fill='x', pady=(0, 8))

        ttk.Label(header_frame, text=title, font=('Arial', 11, 'bold'),
                  foreground=self.current_theme['primary'],
                  background=self.current_theme['card']).pack(side='left')

        value_label = ttk.Label(card, textvariable=variable, font=('Arial', 13, 'bold'),
                                foreground=self.current_theme['secondary'],
                                background=self.current_theme['card'])
        value_label.pack(anchor='w')

    def setup_process_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(filter_frame, text="Поиск:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=(0, 10))
        search_entry.bind('<KeyRelease>', self.filter_processes)

        ttk.Button(filter_frame, text="🔄 Обновить", command=self.update_processes).pack(side='left', padx=5)
        ttk.Button(filter_frame, text="❌ Завершить", command=self.kill_process).pack(side='left', padx=5)
        ttk.Button(filter_frame, text="📊 Детали", command=self.show_process_details).pack(side='left', padx=5)
        ttk.Button(filter_frame, text="🧹 Очистить", command=self.clear_process_filter).pack(side='left', padx=5)

        columns = ('pid', 'name', 'cpu', 'memory', 'status', 'user')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)

        self.tree.heading('pid', text='PID', command=lambda: self.sort_treeview('pid', False))
        self.tree.heading('name', text='Имя процесса', command=lambda: self.sort_treeview('name', False))
        self.tree.heading('cpu', text='CPU %', command=lambda: self.sort_treeview('cpu', False))
        self.tree.heading('memory', text='Память (MB)', command=lambda: self.sort_treeview('memory', False))
        self.tree.heading('status', text='Статус', command=lambda: self.sort_treeview('status', False))
        self.tree.heading('user', text='Пользователь', command=lambda: self.sort_treeview('user', False))

        self.tree.column('pid', width=80, anchor='center')
        self.tree.column('name', width=200)
        self.tree.column('cpu', width=80, anchor='center')
        self.tree.column('memory', width=100, anchor='center')
        self.tree.column('status', width=100, anchor='center')
        self.tree.column('user', width=120)

        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.setup_treeview_context_menu()
        self.update_processes()

    def setup_treeview_context_menu(self):
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Завершить процесс", command=self.kill_process)
        self.context_menu.add_command(label="Подробности", command=self.show_process_details)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Обновить", command=self.update_processes)

        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def setup_system_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        sys_notebook = ttk.Notebook(main_frame)
        sys_notebook.pack(fill='both', expand=True)

        general_frame = ttk.Frame(sys_notebook)
        sys_notebook.add(general_frame, text="Общая информация")

        general_info = scrolledtext.ScrolledText(general_frame, width=80, height=20,
                                                 bg='#34495e', fg='white', font=('Consolas', 10))
        general_info.pack(fill='both', expand=True, padx=10, pady=10)

        info = self.get_system_info()
        general_info.insert('1.0', info)
        general_info.config(state='disabled')

        hardware_frame = ttk.Frame(sys_notebook)
        sys_notebook.add(hardware_frame, text="Аппаратное обеспечение")

        hardware_info = scrolledtext.ScrolledText(hardware_frame, width=80, height=20,
                                                  bg='#34495e', fg='white', font=('Consolas', 10))
        hardware_info.pack(fill='both', expand=True, padx=10, pady=10)

        hw_info = self.get_hardware_info()
        hardware_info.insert('1.0', hw_info)
        hardware_info.config(state='disabled')

    def setup_network_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('proto', 'local', 'remote', 'status', 'pid')
        self.net_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)

        self.net_tree.heading('proto', text='Протокол')
        self.net_tree.heading('local', text='Локальный адрес')
        self.net_tree.heading('remote', text='Удаленный адрес')
        self.net_tree.heading('status', text='Статус')
        self.net_tree.heading('pid', text='PID')

        self.net_tree.column('proto', width=80)
        self.net_tree.column('local', width=200)
        self.net_tree.column('remote', width=200)
        self.net_tree.column('status', width=100)
        self.net_tree.column('pid', width=80)

        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.net_tree.yview)
        self.net_tree.configure(yscrollcommand=scrollbar.set)

        self.net_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(btn_frame, text="🔄 Обновить", command=self.update_network_connections).pack(side='left')

        self.update_network_connections()

    def setup_startup_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('name', 'path', 'status')
        self.startup_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)

        self.startup_tree.heading('name', text='Название')
        self.startup_tree.heading('path', text='Путь')
        self.startup_tree.heading('status', text='Статус')

        self.startup_tree.column('name', width=200)
        self.startup_tree.column('path', width=400)
        self.startup_tree.column('status', width=100)

        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.startup_tree.yview)
        self.startup_tree.configure(yscrollcommand=scrollbar.set)

        self.startup_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(btn_frame, text="🔄 Обновить", command=self.update_startup_programs).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✅ Включить", command=self.enable_startup).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="❌ Отключить", command=self.disable_startup).pack(side='left', padx=5)

        self.update_startup_programs()

    def setup_clean_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame, width=300)
        left_frame.pack(side='left', fill='y', padx=(0, 10))
        left_frame.pack_propagate(False)

        ttk.Label(left_frame, text="🧹 Инструменты очистки", style='Header.TLabel').pack(pady=(0, 15))

        clean_actions = [
            ("🧽 Очистить кэш", self.clean_temp_files),
            ("🗑️ Очистить корзину", self.clean_recycle_bin),
            ("📊 Анализ диска", self.analyze_disk),
            ("🔍 Поиск больших файлов", self.find_large_files),
            ("📋 Очистить историю", self.clear_history)
        ]

        for text, command in clean_actions:
            btn = ttk.Button(left_frame, text=text, command=command, width=25)
            btn.pack(pady=5)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True)

        ttk.Label(right_frame, text="📋 Результаты очистки", style='Header.TLabel').pack(pady=(0, 10))

        self.clean_result = scrolledtext.ScrolledText(right_frame, width=60, height=20,
                                                      bg='#34495e', fg='white', font=('Consolas', 10))
        self.clean_result.pack(fill='both', expand=True)
        self.clean_result.insert('1.0', "Здесь будут отображаться результаты очистки...\n")
        self.clean_result.config(state='disabled')

    def setup_about_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        canvas = tk.Canvas(main_frame, bg=self.current_theme['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill='x', pady=(0, 20))

        icon_label = ttk.Label(header_frame, text="🚀", font=('Arial', 48))
        icon_label.pack(side='left', padx=(0, 20))

        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side='left', fill='y')

        ttk.Label(title_frame, text="System Monitoring Tool v1.0.0",
                  font=('Arial', 24, 'bold'), foreground='#3498db').pack(anchor='w')
        ttk.Label(title_frame, text="Мощный мониторинг системы",
                  font=('Arial', 12), foreground='#7f8c8d').pack(anchor='w')
        ttk.Label(title_frame, text=f"Версия 1.0.0 | Сборка {datetime.now().strftime('%Y%m%d')}",
                  font=('Arial', 10), foreground='#95a5a6').pack(anchor='w')

        info_card = ttk.Frame(scrollable_frame, style='Card.TFrame', padding=20)
        info_card.pack(fill='x', pady=(0, 20))

        info_text = """
    System Monitoring Tool - это комплексное решение для мониторинга и управления 
    системными ресурсами вашего компьютера. Программа сочетает в себе мощный 
    функционал и современный интерфейс для максимального удобства использования.

    Ключевые возможности:
    • Реальный мониторинг CPU, памяти, диска и сети
    • Полный контроль над процессами и службами
    • Мониторинг температуры компонентов
    • Анализ сетевых соединений
    • Управление автозагрузкой приложений
    • Интеллектуальная очистка системы
    • Современный адаптивный интерфейс
    • Поддержка Windows, Linux и macOS
        """

        info_label = ttk.Label(info_card, text=info_text, font=('Arial', 11),
                               justify='left', background='#34495e', foreground='white')
        info_label.pack(anchor='w')

        sys_info_card = ttk.Frame(scrollable_frame, style='Card.TFrame', padding=20)
        sys_info_card.pack(fill='x', pady=(0, 20))

        ttk.Label(sys_info_card, text="📋 Системная информация",
                  font=('Arial', 14, 'bold'), foreground='#3498db').pack(anchor='w', pady=(0, 15))

        sys_grid = ttk.Frame(sys_info_card)
        sys_grid.pack(fill='x')

        sys_data = [
            ("💻 Система", f"{platform.system()} {platform.release()}"),
            ("🏗️ Архитектура", platform.architecture()[0]),
            ("🐍 Python", sys.version.split()[0]),
            ("🚀 Процессор", platform.processor() or "Не определен"),
            ("💾 Память", f"{psutil.virtual_memory().total // 1024 // 1024} MB"),
            ("📦 Версия", "1.0.0 (Stable)"),
            ("📅 Сборка", datetime.now().strftime("%Y-%m-%d %H:%M")),
            ("👤 Пользователь", os.getlogin())
        ]

        for i, (label, value) in enumerate(sys_data):
            row = i // 2
            col = i % 2 * 2

            ttk.Label(sys_grid, text=label, font=('Arial', 10, 'bold'),
                      foreground='#bdc3c7').grid(row=row, column=col, sticky='w', padx=(0, 10), pady=2)
            ttk.Label(sys_grid, text=value, font=('Arial', 10),
                      foreground='#ecf0f1').grid(row=row, column=col + 1, sticky='w', pady=2)

        dev_card = ttk.Frame(scrollable_frame, style='Card.TFrame', padding=20)
        dev_card.pack(fill='x', pady=(0, 20))

        ttk.Label(dev_card, text="👨‍💻 Разработчик",
                  font=('Arial', 14, 'bold'), foreground='#3498db').pack(anchor='w', pady=(0, 15))

        dev_info = """
    Enderiarti 

    Контакты:
    • Email: dimakokulov3@gmail.com
    • GitHub: github.com/Enderiarti
    • Telegram: @Diforo4ka
        """

        ttk.Label(dev_card, text=dev_info, font=('Arial', 11),
                  justify='left', background='#34495e', foreground='white').pack(anchor='w', pady=(0, 15))

        social_frame = ttk.Frame(dev_card)
        social_frame.pack(fill='x', pady=(0, 15))

        social_buttons = [
            ("GitHub", "https://github.com/Enderiarti", "#6cc644"),
            ("Telegram", "https://t.me/lowinolo", "#0088cc")
        ]

        for platform_name, url, color in social_buttons:
            btn = tk.Button(social_frame, text=platform_name, font=('Arial', 10, 'bold'),
                            bg=color, fg='white', relief='flat', cursor='hand2',
                            command=lambda u=url: webbrowser.open(u))
            btn.pack(side='left', padx=(0, 10), ipadx=10, ipady=5)

        license_card = ttk.Frame(scrollable_frame, style='Card.TFrame', padding=20)
        license_card.pack(fill='x', pady=(0, 20))

        ttk.Label(license_card, text="📝 Лицензия",
                  font=('Arial', 14, 'bold'), foreground='#3498db').pack(anchor='w', pady=(0, 15))

        license_text = """
    MIT License

    Copyright (c) 2025 Enderiarti

    Разрешается бесплатное использование, копирование, модификация, объединение, 
    публикация, распространение, сублицензирование и/или продажа копий Программного 
    обеспечения, а также лицам, которым предоставляется Программное обеспечение, 
    при соблюдении следующих условий:

    Указанное выше уведомление об авторском праве и данное уведомление о разрешении 
    должны быть включены во все копии или существенные части Программного обеспечения.
        """

        license_label = ttk.Label(license_card, text=license_text, font=('Arial', 10),
                                  justify='left', background='#34495e', foreground='#bdc3c7')
        license_label.pack(anchor='w')

        action_frame = ttk.Frame(scrollable_frame)
        action_frame.pack(fill='x', pady=(0, 20))

        actions = [
            ("📖 Документация", "https://github.com/Enderiarti/system-monitoring-system", "#27ae60"),
            ("🐛 Сообщить об ошибке", "https://github.com/Enderiarti/system-monitoring-system", "#e74c3c"),
            ("⭐ Оценить на GitHub", "https://github.com/Enderiarti/system-monitoring-system/stargazers", "#f39c12"),
            ("🔄 Проверить обновления", self.check_updates, "#3498db"),
            ("📦 Экспорт отчетов", self.export_reports, "#9b59b6"),
            ("⚙️ Настройки программы", self.open_settings, "#34495e")
        ]

        for i, (text, action, color) in enumerate(actions):
            row = i // 3
            col = i % 3

            if isinstance(action, str):
                cmd = lambda url=action: webbrowser.open(url)
            else:
                cmd = action

            btn = tk.Button(action_frame, text=text, font=('Arial', 10, 'bold'),
                            bg=color, fg='white', relief='flat', cursor='hand2',
                            command=cmd)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            action_frame.columnconfigure(col, weight=1)

        stats_card = ttk.Frame(scrollable_frame, style='Card.TFrame', padding=20)
        stats_card.pack(fill='x', pady=(0, 20))

        ttk.Label(stats_card, text="📈 Статистика",
                  font=('Arial', 14, 'bold'), foreground='#3498db').pack(anchor='w', pady=(0, 15))

        stats_text = f"""
    • Время работы: {time.strftime('%H:%M:%S', time.gmtime(time.time() - self.start_time))}
    • Памяти использовано: {psutil.virtual_memory().used // 1024 // 1024} MB
    • Сетевой трафик: {(psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv) // 1024 // 1024} MB
    • Ошибок: 0
        """

        ttk.Label(stats_card, text=stats_text, font=('Arial', 11),
                  justify='left', background='#34495e', foreground='white').pack(anchor='w')

        footer_frame = ttk.Frame(scrollable_frame)
        footer_frame.pack(fill='x', pady=(20, 0))

        footer_text = f"© 2025 Lowinolo | System Monitoring Tool v1.0.0 | {platform.system()} {platform.release()}"
        ttk.Label(footer_frame, text=footer_text, font=('Arial', 9),
                  foreground='#7f8c8d').pack(anchor='center')

        self.start_time = time.time()

    def check_updates(self):
        messagebox.showinfo("Проверка обновлений",
                            "Проверяем наличие обновлений...\n\nВерсия 1.0.0 актуальна!")

    def export_reports(self):
        try:
            filename = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.get_system_info())
                f.write("\n\n" + self.get_hardware_info())

            messagebox.showinfo("Экспорт отчетов",
                                f"Отчет успешно экспортирован в файл:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать отчет: {e}")

    def open_settings(self):
        messagebox.showinfo("Настройки", "Открываем настройки программы...")

    def update_data(self):
        while self.running:
            try:
                cpu_percent = psutil.cpu_percent()
                mem_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent

                net_io = psutil.net_io_counters()
                net_usage = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024

                temp = self.get_temperature()

                self.cpu_data.append(cpu_percent)
                self.mem_data.append(mem_percent)
                self.disk_data.append(disk_percent)
                self.net_data.append(net_usage)
                self.temp_data.append(temp)

                if len(self.cpu_data) > 50:
                    self.cpu_data = self.cpu_data[-50:]
                    self.mem_data = self.mem_data[-50:]
                    self.disk_data = self.disk_data[-50:]
                    self.net_data = self.net_data[-50:]
                    self.temp_data = self.temp_data[-50:]

                self.update_charts()

                self.cpu_var.set(f"Загрузка CPU: {cpu_percent}%")
                self.mem_var.set(f"Исп. памяти: {mem_percent}%")
                self.disk_var.set(f"Исп. диска: {disk_percent}%")
                self.net_var.set(f"Сетевой трафик: {net_usage:.1f} MB")
                self.temp_var.set(f"Температура: {temp}°C")

                self.status_var.set(
                    f"🟢 CPU: {cpu_percent}% | "
                    f"Память: {mem_percent}% | "
                    f"Диск: {disk_percent}% | "
                    f"Сеть: {net_usage:.1f} MB | "
                    f"Температура: {temp}°C"
                )

                time.sleep(1)

            except Exception as e:
                print(f"Ошибка обновления: {e}")
                time.sleep(5)

    def update_charts(self):
        self.ax_cpu.clear()
        self.ax_mem.clear()
        self.ax_disk.clear()
        self.ax_net.clear()
        self.ax_temp.clear()

        for ax in [self.ax_cpu, self.ax_mem, self.ax_disk, self.ax_net, self.ax_temp]:
            ax.set_facecolor('#34495e')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('#7f8c8d')
            ax.title.set_color('white')

        self.ax_cpu.plot(self.cpu_data, 'r-', linewidth=2)
        self.ax_cpu.set_title('Использование CPU (%)')
        self.ax_cpu.grid(True, color='#7f8c8d', linestyle='--', alpha=0.3)
        self.ax_cpu.set_ylim(0, 100)

        self.ax_mem.plot(self.mem_data, 'b-', linewidth=2)
        self.ax_mem.set_title('Использование памяти (%)')
        self.ax_mem.grid(True, color='#7f8c8d', linestyle='--', alpha=0.3)
        self.ax_mem.set_ylim(0, 100)

        self.ax_disk.plot(self.disk_data, 'g-', linewidth=2)
        self.ax_disk.set_title('Использование диска (%)')
        self.ax_disk.grid(True, color='#7f8c8d', linestyle='--', alpha=0.3)
        self.ax_disk.set_ylim(0, 100)

        self.ax_net.plot(self.net_data, 'm-', linewidth=2)
        self.ax_net.set_title('Сетевой трафик (MB)')
        self.ax_net.grid(True, color='#7f8c8d', linestyle='--', alpha=0.3)

        self.ax_temp.plot(self.temp_data, 'y-', linewidth=2)
        self.ax_temp.set_title('Температура (°C)')
        self.ax_temp.grid(True, color='#7f8c8d', linestyle='--', alpha=0.3)

        self.canvas.draw()

    def get_temperature(self):
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                return int(gpus[0].temperature)

            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps and 'coretemp' in temps:
                    return int(temps['coretemp'][0].current)

            return 0
        except:
            return 0

    def get_system_info(self):
        info = "=== ИНФОРМАЦИЯ О СИСТЕМЕ ===\n\n"

        info += f"Система: {platform.system()} {platform.release()}\n"
        info += f"Версия: {platform.version()}\n"
        info += f"Архитектура: {platform.architecture()[0]}\n"
        info += f"Имя компьютера: {platform.node()}\n\n"

        info += "=== ПРОЦЕССОР ===\n"
        info += f"Процессор: {platform.processor()}\n"
        info += f"Ядер: {psutil.cpu_count()} (логических: {psutil.cpu_count(logical=True)})\n"
        info += f"Тактовая частота: {psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A'} MHz\n\n"

        mem = psutil.virtual_memory()
        info += "=== ПАМЯТЬ ===\n"
        info += f"ОЗУ: {mem.total // 1024 // 1024} MB total\n"
        info += f"Доступно: {mem.available // 1024 // 1024} MB\n"
        info += f"Использовано: {mem.used // 1024 // 1024} MB\n"
        info += f"Процент использования: {mem.percent}%\n\n"

        info += "=== ДИСКИ ===\n"
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                info += f"{part.device} ({part.fstype}): {usage.total // 1024 // 1024 // 1024} GB total, {usage.free // 1024 // 1024 // 1024} GB free\n"
            except:
                continue

        return info

    def get_hardware_info(self):
        info = "=== АППАРАТНОЕ ОБЕСПЕЧЕНИЕ ===\n\n"

        try:
            info += "=== ГРАФИЧЕСКИЙ ПРОЦЕССОР ===\n"
            try:
                gpus = GPUtil.getGPUs()
                for i, gpu in enumerate(gpus):
                    info += f"GPU {i}: {gpu.name}\n"
                    info += f"  Память: {gpu.memoryTotal} MB\n"
                    info += f"  Загрузка: {gpu.load * 100}%\n"
                    info += f"  Температура: {gpu.temperature}°C\n"
            except:
                info += "Информация о GPU недоступна\n"

            info += "\n=== МОНИТОРЫ ===\n"
            try:
                monitors = get_monitors()
                for i, m in enumerate(monitors):
                    info += f"Монитор {i}: {m.width}x{m.height} @ {m.x},{m.y}\n"
            except:
                info += "Информация о мониторах недоступна\n"

            info += "\n=== БАТАРЕЯ ===\n"
            try:
                battery = psutil.sensors_battery()
                if battery:
                    info += f"Заряд: {battery.percent}%\n"
                    info += f"Статус: {'Заряжается' if battery.power_plugged else 'Разряжается'}\n"
                    if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                        info += f"Осталось: {battery.secsleft // 3600} ч. {(battery.secsleft % 3600) // 60} мин.\n"
                else:
                    info += "Батарея не обнаружена\n"
            except:
                info += "Информация о батарее недоступна\n"

        except Exception as e:
            info += f"Ошибка получения информации об аппаратном обеспечении: {e}\n"

        return info

    def update_processes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'username']):
            try:
                mem_mb = proc.info['memory_info'].rss / 1024 / 1024
                username = proc.info['username'] or 'N/A'

                self.tree.insert('', 'end', values=(
                    proc.info['pid'],
                    proc.info['name'],
                    f"{proc.info['cpu_percent']:.1f}",
                    f"{mem_mb:.1f}",
                    proc.info['status'],
                    username
                ))
            except:
                continue

    def filter_processes(self, event=None):
        search_term = self.search_var.get().lower()

        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if search_term in str(values).lower():
                self.tree.item(item, tags=('match',))
                self.tree.detach(item)
            else:
                self.tree.item(item, tags=('no_match',))

        for item in self.tree.get_children():
            if 'match' in self.tree.item(item)['tags']:
                self.tree.reattach(item, '', 'end')

    def clear_process_filter(self):
        self.search_var.set("")
        for item in self.tree.get_children():
            self.tree.reattach(item, '', 'end')

    def sort_treeview(self, column, reverse):
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]

        try:
            items = [(float(item[0].replace('%', '').replace(' MB', '')), item[1]) for item in items]
        except:
            pass

        items.sort(reverse=reverse)

        for index, (value, item) in enumerate(items):
            self.tree.move(item, '', index)

        self.tree.heading(column, command=lambda: self.sort_treeview(column, not reverse))

    def kill_process(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите процесс для завершения")
            return

        item = self.tree.item(selected[0])
        pid = item['values'][0]
        name = item['values'][1]

        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите завершить процесс {name} (PID: {pid})?"):
            try:
                process = psutil.Process(pid)
                process.terminate()
                messagebox.showinfo("Успех", f"Процесс {name} завершен")
                self.update_processes()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось завершить процесс: {e}")

    def show_process_details(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите процесс для просмотра")
            return

        item = self.tree.item(selected[0])
        pid = item['values'][0]

        try:
            process = psutil.Process(pid)
            with process.oneshot():
                details = f"""
Детальная информация о процессе:
PID: {pid}
Имя: {process.name()}
Статус: {process.status()}
CPU: {process.cpu_percent()}%
Память: {process.memory_info().rss // 1024 // 1024} MB
Пользователь: {process.username()}
Создан: {time.ctime(process.create_time())}
Путь: {process.exe() if process.exe() else 'N/A'}
Рабочая директория: {process.cwd()}
Кол-во потоков: {process.num_threads()}
Приоритет: {process.nice()}
                """
            messagebox.showinfo("Детали процесса", details)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить информацию: {e}")

    def update_network_connections(self):
        for item in self.net_tree.get_children():
            self.net_tree.delete(item)

        try:
            connections = psutil.net_connections()
            for conn in connections:
                if conn.status == 'ESTABLISHED':
                    self.net_tree.insert('', 'end', values=(
                        conn.type.name,
                        f"{conn.laddr.ip}:{conn.laddr.port}",
                        f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                        conn.status,
                        conn.pid
                    ))
        except:
            pass

    def update_startup_programs(self):
        for item in self.startup_tree.get_children():
            self.startup_tree.delete(item)

        if os.name == 'nt':
            try:
                import winreg
                keys = [
                    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
                ]

                for hive, key_path in keys:
                    try:
                        key = winreg.OpenKey(hive, key_path)
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                self.startup_tree.insert('', 'end', values=(name, value, "Включено"))
                                i += 1
                            except WindowsError:
                                break
                    except:
                        pass
            except:
                pass
        else:
            try:
                autostart_dirs = [
                    "/etc/xdg/autostart",
                    os.path.expanduser("~/.config/autostart")
                ]

                for autostart_dir in autostart_dirs:
                    if os.path.exists(autostart_dir):
                        for file in os.listdir(autostart_dir):
                            if file.endswith('.desktop'):
                                self.startup_tree.insert('', 'end', values=(
                                    file,
                                    os.path.join(autostart_dir, file),
                                    "Включено"
                                ))
            except:
                pass

    def enable_startup(self):
        selected = self.startup_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите программу для включения")
            return

        messagebox.showinfo("Инфо", "Функция включения автозагрузки в разработке")

    def disable_startup(self):
        selected = self.startup_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите программу для отключения")
            return

        messagebox.showinfo("Инфо", "Функция отключения автозагрузки в разработке")

    def clean_temp_files(self):
        try:
            temp_dirs = [
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                '/tmp',
                '/var/tmp',
                os.path.expanduser('~/AppData/Local/Temp')
            ]

            cleaned = 0
            cleaned_size = 0

            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                filepath = os.path.join(root, file)
                                file_size = os.path.getsize(filepath)
                                os.remove(filepath)
                                cleaned += 1
                                cleaned_size += file_size
                            except:
                                continue

            result_text = f"Очищено {cleaned} временных файлов\n"
            result_text += f"Освобождено {cleaned_size // 1024 // 1024} MB дискового пространства\n"

            self.clean_result.config(state='normal')
            self.clean_result.insert('end', result_text + "\n")
            self.clean_result.see('end')
            self.clean_result.config(state='disabled')

            messagebox.showinfo("Успех", result_text)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить кэш: {e}")

    def clean_recycle_bin(self):
        try:
            if os.name == 'nt':
                import winshell
                winshell.recycle_bin().empty(confirm=False)
                messagebox.showinfo("Успех", "Корзина очищена")

                self.clean_result.config(state='normal')
                self.clean_result.insert('end', "Корзина очищена\n")
                self.clean_result.see('end')
                self.clean_result.config(state='disabled')
            else:
                messagebox.showinfo("Инфо", "Очистка корзины доступна только на Windows")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить корзину: {e}")

    def analyze_disk(self):
        try:
            disk_info = "=== АНАЛИЗ ДИСКА ===\n\n"
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disk_info += f"{part.device} ({part.fstype}):\n"
                    disk_info += f"  Всего: {usage.total // 1024 // 1024 // 1024} GB\n"
                    disk_info += f"  Использовано: {usage.used // 1024 // 1024 // 1024} GB\n"
                    disk_info += f"  Свободно: {usage.free // 1024 // 1024 // 1024} GB\n"
                    disk_info += f"  Заполнение: {usage.percent}%\n\n"
                except:
                    continue

            self.clean_result.config(state='normal')
            self.clean_result.insert('end', disk_info + "\n")
            self.clean_result.see('end')
            self.clean_result.config(state='disabled')

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось проанализировать диск: {e}")

    def find_large_files(self):
        try:
            large_files = "=== БОЛЬШИЕ ФАЙЛЫ (>100 MB) ===\n\n"

            for part in psutil.disk_partitions():
                if os.name == 'nt' and 'cdrom' in part.opts:
                    continue

                large_files += f"На диске {part.mountpoint}:\n"

                for root, dirs, files in os.walk(part.mountpoint):
                    for file in files:
                        try:
                            filepath = os.path.join(root, file)
                            if os.path.getsize(filepath) > 100 * 1024 * 1024:
                                large_files += f"  {filepath} - {os.path.getsize(filepath) // 1024 // 1024} MB\n"
                        except:
                            continue
                    if len(large_files.split('\n')) > 50:
                        break

            self.clean_result.config(state='normal')
            self.clean_result.insert('end', large_files + "\n")
            self.clean_result.see('end')
            self.clean_result.config(state='disabled')

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось найти большие файлы: {e}")

    def clear_history(self):
        try:
            history_dirs = []

            if os.name == 'nt':
                history_dirs = [
                    os.path.expanduser('~\\AppData\\Local\\Microsoft\\Windows\\History'),
                    os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History'),
                    os.path.expanduser('~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles')
                ]
            else:
                history_dirs = [
                    os.path.expanduser('~/.config/google-chrome/Default/History'),
                    os.path.expanduser('~/.mozilla/firefox')
                ]

            cleared = 0
            for history_dir in history_dirs:
                if os.path.exists(history_dir):
                    for root, dirs, files in os.walk(history_dir):
                        for file in files:
                            if 'history' in file.lower() or 'cache' in file.lower():
                                try:
                                    os.remove(os.path.join(root, file))
                                    cleared += 1
                                except:
                                    pass

            result_text = f"Очищено {cleared} файлов истории\n"

            self.clean_result.config(state='normal')
            self.clean_result.insert('end', result_text + "\n")
            self.clean_result.see('end')
            self.clean_result.config(state='disabled')

            messagebox.showinfo("Успех", result_text)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить историю: {e}")

    def update_all(self):
        self.update_processes()
        self.update_network_connections()
        self.update_startup_programs()
        self.status_var.set("✅ Все данные обновлены")

    def show_resource(self, resource):
        tabs = {
            "CPU": 0,
            "Memory": 0,
            "Disk": 0,
            "Network": 3
        }

        if resource in tabs:
            notebook = self.root.winfo_children()[0].winfo_children()[0]
            notebook.select(tabs[resource])

    def show_about(self):
        about_text = f"""
        System Monitoring Tool v2.0

        Тема: {'Темная' if self.theme_mode == 'dark' else 'Светлая'}
        Стиль кнопок: {self.button_style}

        Мощный мониторинг системы с современным интерфейсом
        """
        messagebox.showinfo("О программе", about_text)

    def on_closing(self):
        self.running = False
        self.root.destroy()


def main():
    root = tk.Tk()
    app = SystemMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == "__main__":
    main()
