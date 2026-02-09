import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
from pynput import keyboard
from pynput.mouse import Button, Controller
from pynput.keyboard import Key

class Autoclicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Автокликер v1.0")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        # Настройки по умолчанию
        self.clicking = False
        self.click_thread = None
        self.hotkey_listener = None
        
        # Загружаем сохраненные настройки
        self.load_settings()
        
        # Настраиваем стили
        self.setup_styles()
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Запускаем слушатель горячих клавиш
        self.start_hotkey_listener()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настраиваем цвета и шрифты
        self.root.configure(bg='#f0f0f0')
        
    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = tk.Label(main_frame, text="АВТОКЛИКЕР", 
                               font=('Arial', 18, 'bold'), bg='#f0f0f0')
        title_label.pack(pady=(0, 15))
        
        # Фрейм настроек кликов
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки кликов", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Интервал между кликами
        interval_frame = ttk.Frame(settings_frame)
        interval_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(interval_frame, text="Интервал (сек):").pack(side=tk.LEFT, padx=(0, 10))
        self.interval_var = tk.DoubleVar(value=self.settings.get("interval", 0.5))
        self.interval_spinbox = ttk.Spinbox(interval_frame, from_=0.05, to=10, increment=0.05, 
                                           textvariable=self.interval_var, width=10)
        self.interval_spinbox.pack(side=tk.LEFT)
        
        # Тип клика
        click_type_frame = ttk.Frame(settings_frame)
        click_type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(click_type_frame, text="Тип клика:").pack(side=tk.LEFT, padx=(0, 10))
        self.click_type_var = tk.StringVar(value=self.settings.get("click_type", "Левый"))
        click_type_combo = ttk.Combobox(click_type_frame, textvariable=self.click_type_var, 
                                       values=["Левый", "Правый", "Средний"], state="readonly", width=15)
        click_type_combo.pack(side=tk.LEFT)
        
        # Количество кликов за цикл
        clicks_frame = ttk.Frame(settings_frame)
        clicks_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(clicks_frame, text="Кликов за цикл:").pack(side=tk.LEFT, padx=(0, 10))
        self.clicks_per_cycle_var = tk.IntVar(value=self.settings.get("clicks_per_cycle", 1))
        clicks_spinbox = ttk.Spinbox(clicks_frame, from_=1, to=1000, 
                                     textvariable=self.clicks_per_cycle_var, width=10)
        clicks_spinbox.pack(side=tk.LEFT)
        
        # Режим работы
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="Режим:").pack(side=tk.LEFT, padx=(0, 10))
        self.mode_var = tk.StringVar(value=self.settings.get("mode", "Постоянно"))
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, 
                                 values=["Постоянно", "Ограниченное количество"], state="readonly", width=20)
        mode_combo.pack(side=tk.LEFT)
        
        # Количество циклов (если режим ограниченный)
        self.cycles_frame = ttk.Frame(settings_frame)
        
        ttk.Label(self.cycles_frame, text="Количество циклов:").pack(side=tk.LEFT, padx=(0, 10))
        self.cycles_var = tk.IntVar(value=self.settings.get("cycles", 10))
        cycles_spinbox = ttk.Spinbox(self.cycles_frame, from_=1, to=10000, 
                                     textvariable=self.cycles_var, width=10)
        cycles_spinbox.pack(side=tk.LEFT)
        
        if self.mode_var.get() == "Ограниченное количество":
            self.cycles_frame.pack(fill=tk.X, pady=5)
        
        # Обработчик изменения режима
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_changed)
        
        # Фрейм управления
        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Кнопки старт/стоп
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(btn_frame, text="СТАРТ (F8)", command=self.start_clicking, 
                                    style="Start.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.stop_btn = ttk.Button(btn_frame, text="СТОП (F9)", command=self.stop_clicking, 
                                   style="Stop.TButton", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Информация о горячих клавишах
        hotkey_frame = ttk.Frame(control_frame)
        hotkey_frame.pack(fill=tk.X, pady=(10, 0))
        
        hotkey_label = tk.Label(hotkey_frame, text="Горячие клавиши: F8 - старт, F9 - стоп", 
                                font=('Arial', 9), bg='#f0f0f0', fg='#555555')
        hotkey_label.pack()
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Настраиваем стили кнопок
        style = ttk.Style()
        style.configure("Start.TButton", foreground="green", font=('Arial', 10, 'bold'))
        style.configure("Stop.TButton", foreground="red", font=('Arial', 10, 'bold'))
    
    def on_mode_changed(self, event=None):
        if self.mode_var.get() == "Ограниченное количество":
            self.cycles_frame.pack(fill=tk.X, pady=5)
        else:
            self.cycles_frame.pack_forget()
    
    def start_clicking(self):
        if self.clicking:
            return
        
        self.clicking = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Автокликер запущен")
        
        # Сохраняем настройки перед запуском
        self.save_settings()
        
        # Запускаем поток для кликов
        self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
        self.click_thread.start()
    
    def stop_clicking(self):
        self.clicking = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Автокликер остановлен")
    
    def click_loop(self):
        mouse_controller = Controller()
        
        # Определяем кнопку для клика
        click_button = Button.left
        if self.click_type_var.get() == "Правый":
            click_button = Button.right
        elif self.click_type_var.get() == "Средний":
            click_button = Button.middle
        
        cycles_done = 0
        max_cycles = self.cycles_var.get() if self.mode_var.get() == "Ограниченное количество" else float('inf')
        
        while self.clicking and cycles_done < max_cycles:
            try:
                # Выполняем клики в текущей позиции курсора
                for _ in range(self.clicks_per_cycle_var.get()):
                    if not self.clicking:
                        break
                    mouse_controller.click(click_button, 1)
                
                cycles_done += 1
                
                # Обновляем статус
                if self.mode_var.get() == "Ограниченное количество":
                    self.root.after(0, self.update_status, f"Выполнено циклов: {cycles_done}/{max_cycles}")
                
                # Ждем указанный интервал
                interval = self.interval_var.get()
                time.sleep(interval)
                
            except Exception as e:
                print(f"Ошибка в потоке кликов: {e}")
                break
        
        # Останавливаем клики после завершения циклов
        self.root.after(0, self.stop_clicking)
    
    def update_status(self, message):
        self.status_var.set(message)
    
    def on_press(self, key):
        try:
            # F8 - старт автокликера
            if key == Key.f8:
                self.root.after(0, self.start_clicking)
            
            # F9 - стоп автокликера
            elif key == Key.f9:
                self.root.after(0, self.stop_clicking)
        
        except AttributeError:
            pass
    
    def start_hotkey_listener(self):
        # Слушатель для горячих клавиш
        self.hotkey_listener = keyboard.Listener(on_press=self.on_press)
        self.hotkey_listener.start()
    
    def load_settings(self):
        self.settings_file = "autoclicker_settings.json"
        self.settings = {}
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
                    
            except Exception as e:
                print(f"Ошибка загрузки настроек: {e}")
                self.settings = {}
    
    def save_settings(self):
        try:
            # Обновляем текущие настройки
            self.settings.update({
                "interval": self.interval_var.get(),
                "click_type": self.click_type_var.get(),
                "clicks_per_cycle": self.clicks_per_cycle_var.get(),
                "mode": self.mode_var.get(),
                "cycles": self.cycles_var.get()
            })
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
                
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
    
    def on_closing(self):
        # Сохраняем настройки перед закрытием
        self.save_settings()
        
        # Останавливаем клики
        self.clicking = False
        
        # Закрываем окно
        self.root.destroy()

def main():
    # Проверяем наличие необходимых библиотек
    try:
        import pynput
    except ImportError:
        print("Библиотека pynput не установлена. Установите ее командой:")
        print("pip install pynput")
        
        # Создаем окно с сообщением об ошибке
        error_root = tk.Tk()
        error_root.withdraw()
        messagebox.showerror("Ошибка", 
            "Библиотека pynput не установлена.\n\n"
            "Установите ее командой:\n"
            "pip install pynput")
        error_root.destroy()
        return
    
    # Создаем и запускаем приложение
    root = tk.Tk()
    app = Autoclicker(root)
    
    # Центрируем окно на экране
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()