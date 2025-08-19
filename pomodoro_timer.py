# pomodoro_timer_enhanced.py

# --- 1. Imports ---
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
import threading
import random
from datetime import date

# --- 2. Constants ---

# File Paths
TASKS_FILE = "pomodoro_tasks.json"
SETTINGS_FILE = "pomodoro_settings.json"
GOAL_FILE = "daily_goal.json"

# UI Styling and Configuration
FONT_FAMILY = "Comic Sans MS"
PRIORITIES = ["High", "Medium", "Low"]
PRIORITY_MAP = {p: i for i, p in enumerate(PRIORITIES)} # For sorting

# --- Data Keys (Constants to avoid "magic strings") ---
# Settings Keys
SETTING_POMO_DUR = "pomodoro_duration"
SETTING_SHORT_DUR = "short_break_duration"
SETTING_LONG_DUR = "long_break_duration"
SETTING_INTERVAL = "long_break_interval"
SETTING_SOUND_PATH = "sound_file_path"
SETTING_THEME = "theme"
# Theme Keys
THEME_BG = "BACKGROUND"
THEME_FG = "FOREGROUND"
THEME_ACCENT = "ACCENT"
THEME_BTN = "BUTTON"
THEME_BTN_ACTIVE = "BUTTON_ACTIVE"
THEME_SESSION_BG = "SESSION_BG"
THEME_PRIORITY_HIGH = "HIGH_PRIORITY"
THEME_PRIORITY_MEDIUM = "MEDIUM_PRIORITY"
THEME_PRIORITY_LOW = "LOW_PRIORITY"

# Themes Collection
THEMES = {
    "dark": {
        THEME_BG: "#1E1E1E", THEME_FG: "#F0F0F0", THEME_ACCENT: "#FF6347",
        THEME_BTN: "#3A3A3A", THEME_BTN_ACTIVE: "#5C5C5C", THEME_SESSION_BG: "#2C2C2C",
        THEME_PRIORITY_HIGH: "#D32F2F", THEME_PRIORITY_MEDIUM: "#FBC02D", THEME_PRIORITY_LOW: "#388E3C",
        "START": "#28A745", "START_ACTIVE": "#218838", "PAUSE": "#FFC107",
        "PAUSE_ACTIVE": "#FFA000", "RESET": "#17A2B8", "RESET_ACTIVE": "#138496",
    },
    "light": {
        THEME_BG: "#F0F0F0", THEME_FG: "#1E1E1E", THEME_ACCENT: "#D32F2F",
        THEME_BTN: "#E0E0E0", THEME_BTN_ACTIVE: "#C7C7C7", THEME_SESSION_BG: "#FFFFFF",
        THEME_PRIORITY_HIGH: "#C62828", THEME_PRIORITY_MEDIUM: "#F9A825", THEME_PRIORITY_LOW: "#2E7D32",
        "START": "#4CAF50", "START_ACTIVE": "#45A049", "PAUSE": "#FFEB3B",
        "PAUSE_ACTIVE": "#FDD835", "RESET": "#00BCD4", "RESET_ACTIVE": "#00ACC1",
    }
}

# Timer Modes & Default Durations
MODES = {
    "POMODORO": "Pomodoro", "SHORT_BREAK": "Short Break",
    "LONG_BREAK": "Long Break", "STOPWATCH": "Stopwatch"
}
DEFAULT_SETTINGS = {
    SETTING_POMO_DUR: 25 * 60, SETTING_SHORT_DUR: 5 * 60, SETTING_LONG_DUR: 15 * 60,
    SETTING_INTERVAL: 4, SETTING_SOUND_PATH: "", SETTING_THEME: "dark"
}

MOTIVATIONAL_QUOTES = [
    "The secret of getting ahead is getting started.", "The only way to do great work is to love what you do.",
    "Believe you can and you're halfway there.", "The future depends on what you do today."
]

# --- 3. Sound Module Initialization ---
SOUND_MODULE = None
try:
    import pygame
    SOUND_MODULE = 'pygame'
except ImportError:
    print("Pygame module not found. Sound features will be limited.")


# --- 4. Custom Dialog Windows ---
class CustomDialog(tk.Toplevel):
    """Base class for custom styled dialogs to reduce code duplication."""
    def __init__(self, parent, title, theme, geometry="400x300"):
        super().__init__(parent)
        self.theme = theme
        self.title(title)
        self.geometry(geometry)
        self.configure(bg=self.theme[THEME_BG])
        self.transient(parent)
        self.grab_set()
        self.result = None
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Content frame for subclasses to populate
        self.content_frame = tk.Frame(self, bg=self.theme[THEME_BG], padx=15, pady=15)
        self.content_frame.pack(fill="both", expand=True)

    def _create_buttons(self, show_save=True):
        btn_frame = tk.Frame(self, bg=self.theme[THEME_BG])
        btn_frame.pack(pady=10)
        if show_save:
            tk.Button(btn_frame, text="Save", command=self._on_save, bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG], relief="flat").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Close", command=self._on_cancel, bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG], relief="flat").pack(side="left", padx=10)

    def _on_save(self): raise NotImplementedError
    def _on_cancel(self): self.result = None; self.destroy()

class SettingsWindow(CustomDialog):
    def __init__(self, parent, current_settings, theme):
        super().__init__(parent, "Settings", theme, "450x550")
        self.duration_entries = {}
        
        timer_frame = tk.LabelFrame(self.content_frame, text="Timer Durations", bg=self.theme[THEME_BG], fg=self.theme[THEME_FG], padx=10, pady=10)
        timer_frame.pack(fill="x", expand=True, pady=(0, 10))

        duration_keys = {SETTING_POMO_DUR: "Pomodoro:", SETTING_SHORT_DUR: "Short Break:", SETTING_LONG_DUR: "Long Break:"}
        for i, (key, text) in enumerate(duration_keys.items()):
            tk.Label(timer_frame, text=text, bg=self.theme[THEME_BG], fg=self.theme[THEME_FG], font=(FONT_FAMILY, 10)).grid(row=i, column=0, sticky='w', pady=5)
            mins, secs = divmod(current_settings.get(key, 0), 60)
            min_entry = tk.Entry(timer_frame, width=5, bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG], relief="flat"); min_entry.insert(0, str(mins)); min_entry.grid(row=i, column=1, padx=(10,0))
            tk.Label(timer_frame, text="min", bg=self.theme[THEME_BG], fg=self.theme[THEME_FG]).grid(row=i, column=2, padx=(2,10))
            sec_entry = tk.Entry(timer_frame, width=5, bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG], relief="flat"); sec_entry.insert(0, str(secs)); sec_entry.grid(row=i, column=3)
            tk.Label(timer_frame, text="sec", bg=self.theme[THEME_BG], fg=self.theme[THEME_FG]).grid(row=i, column=4, padx=2)
            self.duration_entries[key] = (min_entry, sec_entry)

        tk.Label(timer_frame, text="Long Break Interval:", bg=self.theme[THEME_BG], fg=self.theme[THEME_FG]).grid(row=3, column=0, sticky='w', pady=5)
        self.interval_entry = tk.Entry(timer_frame, width=5, bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG], relief="flat"); self.interval_entry.insert(0, str(current_settings.get(SETTING_INTERVAL, 4))); self.interval_entry.grid(row=3, column=1, padx=(10,0))
        
        tk.Label(timer_frame, text="Sound File:", bg=self.theme[THEME_BG], fg=self.theme[THEME_FG]).grid(row=4, column=0, sticky='w', pady=10)
        self.sound_entry = tk.Entry(timer_frame, bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG], relief="flat"); self.sound_entry.insert(0, current_settings.get(SETTING_SOUND_PATH, "")); self.sound_entry.grid(row=4, column=1, columnspan=4, sticky='ew', padx=(10,0))
        tk.Button(timer_frame, text="Browse...", bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG], command=self._browse, relief="flat").grid(row=4, column=5, padx=5)

        shortcuts_frame = tk.LabelFrame(self.content_frame, text="Keyboard Shortcuts", bg=self.theme[THEME_BG], fg=self.theme[THEME_FG], padx=10, pady=10)
        shortcuts_frame.pack(fill="x", expand=True)
        
        shortcuts = { "Start / Pause": "Spacebar", "Reset Timer": "R", "Switch to Pomodoro": "Ctrl+P",
            "Switch to Short Break": "Ctrl+S", "Switch to Long Break": "Ctrl+L", "Switch to Stopwatch": "Ctrl+T",
            "Add New Task": "Ctrl+Enter", "Delete Selected": "Delete", "Delete All Tasks": "Ctrl+D", "Quit": "Ctrl+Q" }
        for i, (action, key) in enumerate(shortcuts.items()):
            tk.Label(shortcuts_frame, text=action, bg=self.theme[THEME_BG], fg=self.theme[THEME_FG]).grid(row=i, column=0, sticky="w", padx=5)
            tk.Label(shortcuts_frame, text=key, bg=self.theme[THEME_BG], fg=self.theme[THEME_FG], font=(FONT_FAMILY, 10, "bold")).grid(row=i, column=1, sticky="e", padx=5)
        shortcuts_frame.columnconfigure(1, weight=1)

        self._create_buttons()

    def _browse(self):
        path = filedialog.askopenfilename(title="Select Sound File", filetypes=[("Audio Files", "*.wav *.mp3")])
        if path: self.sound_entry.delete(0, tk.END); self.sound_entry.insert(0, path)

    def _on_save(self):
        try:
            self.result = {}
            for key, (min_e, sec_e) in self.duration_entries.items(): self.result[key] = int(min_e.get() or 0) * 60 + int(sec_e.get() or 0)
            self.result[SETTING_INTERVAL] = int(self.interval_entry.get() or 1)
            self.result[SETTING_SOUND_PATH] = self.sound_entry.get().strip()
            if any(v < 0 for v in self.result.values() if isinstance(v, int)): raise ValueError("Negative values not allowed.")
            self.destroy()
        except (ValueError, TypeError): messagebox.showerror("Invalid Input", "Please enter valid numbers.", parent=self)

class TaskDescriptionDialog(CustomDialog):
    def __init__(self, parent, task_text, current_description, theme):
        super().__init__(parent, "Task Description", theme, "450x300")
        tk.Label(self.content_frame, text=f"Description for: {task_text}", bg=self.theme[THEME_BG], fg=self.theme[THEME_FG], font=(FONT_FAMILY, 12, "bold")).pack(anchor="w", pady=(0, 10))
        text_frame = tk.Frame(self.content_frame, bg=self.theme[THEME_BG]); text_frame.pack(fill="both", expand=True)
        self.desc_text = tk.Text(text_frame, wrap="word", bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG], relief="flat", insertbackground=self.theme[THEME_FG], font=(FONT_FAMILY, 11))
        self.desc_text.pack(side="left", fill="both", expand=True); self.desc_text.insert("1.0", current_description)
        scrollbar = tk.Scrollbar(text_frame, command=self.desc_text.yview, bg=self.theme[THEME_BG], troughcolor=self.theme[THEME_BTN]); scrollbar.pack(side="right", fill="y")
        self.desc_text.config(yscrollcommand=scrollbar.set)
        self._create_buttons(); self.desc_text.focus_set()

    def _on_save(self): self.result = self.desc_text.get("1.0", "end-1c").strip(); self.destroy()

class DailyGoalDialog(CustomDialog):
    def __init__(self, parent, prompt, current_goal, theme):
        super().__init__(parent, "Daily Goal", theme, "450x200")
        tk.Label(self.content_frame, text=prompt, bg=self.theme[THEME_BG], fg=self.theme[THEME_FG], font=(FONT_FAMILY, 12, "bold")).pack(anchor="w", pady=(0, 10))
        self.goal_entry = tk.Entry(self.content_frame, bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG], relief="flat", insertbackground=self.theme[THEME_FG], font=(FONT_FAMILY, 11))
        self.goal_entry.pack(fill="x", ipady=5, pady=10); self.goal_entry.insert(0, current_goal)
        self._create_buttons(); self.goal_entry.focus_set()

    def _on_save(self): self.result = self.goal_entry.get().strip(); self.destroy()

# --- 5. Main Application ---
class PomodoroTimer(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if SOUND_MODULE:
            try:
                pygame.mixer.init()
            except pygame.error:
                messagebox.showwarning("Sound Error", "Could not initialize the sound system. Notifications will be silent.")
                global SOUND_MODULE
                SOUND_MODULE = None

        self.settings = self._load_settings()
        self.theme_name = self.settings.get(SETTING_THEME, "dark")
        self.theme = THEMES[self.theme_name]

        self.current_mode = MODES["POMODORO"]
        self.time_left = self.settings[SETTING_POMO_DUR]
        self.sessions_completed = 0
        self.is_running = False
        self.timer_id = None
        self.stopwatch_time = 0
        self.sound_thread = None
        
        self.tasks = self._load_json(TASKS_FILE, default=[])
        self.mode_buttons = {}
        self.all_widgets = []

        self.title("Study Pomodoro Timer")
        self.geometry("500x800")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.configure(bg=self.theme[THEME_BG])

        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        self.main_frame = tk.Frame(self, bg=self.theme[THEME_BG], padx=10, pady=10)
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        self.all_widgets.append(self.main_frame)
        self._configure_main_grid()

        self._setup_ui()
        self._bind_shortcuts()
        self.after(100, self._check_daily_goal)
    
    def _configure_main_grid(self):
        self.main_frame.grid_rowconfigure(6, weight=1) # Task Manager Frame
        self.main_frame.grid_columnconfigure(0, weight=1)

    def _setup_ui(self):
        self._create_menu()
        
        # --- Using grid layout for all widgets ---
        self.goal_label = self._create_label("Click to set your daily goal!", font=(FONT_FAMILY, 12, "italic"), fg_theme_key=THEME_ACCENT, wraplength=480)
        self.goal_label.grid(row=0, column=0, pady=(0, 5), sticky='ew')
        self.goal_label.bind("<Button-1>", lambda e: self.set_daily_goal())

        self.session_frame = tk.Frame(self.main_frame, relief='groove', borderwidth=2)
        self.session_frame.grid(row=1, column=0, pady=5, sticky='ew')
        self.all_widgets.append(self.session_frame)
        self.session_label = self._create_label("Sessions Completed: 0", parent=self.session_frame, font=(FONT_FAMILY, 12, "bold"), bg_theme_key=THEME_SESSION_BG, pack_instead=True)
        self.session_frame.grid_columnconfigure(0, weight=1)

        self._create_mode_buttons()
        self.mode_frame.grid(row=2, column=0, pady=10, sticky='ew')
        
        self.timer_label = self._create_label(self._format_time(self.time_left), font=(FONT_FAMILY, 60, "bold"))
        self.timer_label.grid(row=3, column=0, pady=20)

        self.quote_label = self._create_label("Let's get started!", font=(FONT_FAMILY, 11, "italic"), wraplength=480)
        self.quote_label.grid(row=4, column=0, pady=(0, 10))

        self._create_control_buttons()
        self.control_frame.grid(row=5, column=0, pady=10)
        
        self._create_task_manager()
        self.task_frame.grid(row=6, column=0, pady=15, sticky='nsew')

        self._apply_theme(animated=False)
        self._load_tasks_to_listbox()

    def _create_label(self, text, parent=None, pack_instead=False, **kwargs):
        parent = parent or self.main_frame
        bg_key = kwargs.pop('bg_theme_key', THEME_BG)
        fg_key = kwargs.pop('fg_theme_key', THEME_FG)
        kwargs['bg'] = self.theme[bg_key]
        kwargs['fg'] = self.theme[fg_key]
        label = tk.Label(parent, text=text, **kwargs)
        if pack_instead: # For simple, single-widget frames like the session label
             label.pack(fill='x', expand=True, pady=10)
        self.all_widgets.append(label)
        return label

    def _create_menu(self):
        self.menubar = tk.Menu(self, tearoff=0)
        self.config(menu=self.menubar)
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="⚙️ Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="Configure Timers", command=self.open_settings_window)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label="Reset Defaults", command=self.reset_settings)
        self.menubar.add_command(label="☀️/🌙", command=self.toggle_theme)

    def _create_mode_buttons(self):
        self.mode_frame = tk.Frame(self.main_frame); self.all_widgets.append(self.mode_frame)
        self.mode_frame.grid_columnconfigure(list(range(len(MODES))), weight=1) # Make buttons expand equally
        for i, mode in enumerate(MODES.values()):
            btn = tk.Button(self.mode_frame, text=mode, relief="flat", font=(FONT_FAMILY, 10), command=lambda m=mode: self.switch_mode(m))
            btn.grid(row=0, column=i, padx=5, sticky='ew')
            self.mode_buttons[mode] = btn

    def _create_control_buttons(self):
        self.control_frame = tk.Frame(self.main_frame); self.all_widgets.append(self.control_frame)
        configs = {"start": self.start_timer, "pause": self.pause_or_stop_timer, "reset": self.reset_timer}
        self.control_buttons = {}
        for i, (name, command) in enumerate(configs.items()):
            btn = tk.Button(self.control_frame, text=name.capitalize(), relief="flat", font=(FONT_FAMILY, 16, "bold"), command=command)
            btn.grid(row=0, column=i, padx=10, ipadx=10, ipady=5)
            self.control_buttons[name] = btn
        self.control_buttons["pause"].config(state="disabled")

    def _create_task_manager(self):
        self.task_frame = tk.Frame(self.main_frame); self.all_widgets.append(self.task_frame)
        self.task_frame.grid_rowconfigure(3, weight=1) # Make listbox frame expand
        self.task_frame.grid_columnconfigure(0, weight=1)

        self._create_label("Tasks", parent=self.task_frame, font=(FONT_FAMILY, 14, "bold")).grid(row=0, column=0, sticky='w')
        
        input_frame = tk.Frame(self.task_frame); input_frame.grid(row=1, column=0, sticky='ew', pady=5); self.all_widgets.append(input_frame)
        input_frame.grid_columnconfigure(1, weight=1)
        self.priority_var = tk.StringVar(value=PRIORITIES[1])
        self.priority_menu = tk.OptionMenu(input_frame, self.priority_var, *PRIORITIES); self.priority_menu.grid(row=0, column=0, padx=(0,5)); self.all_widgets.append(self.priority_menu)
        self.task_entry = tk.Entry(input_frame, fg="grey", relief="flat", font=(FONT_FAMILY, 12)); self.task_entry.grid(row=0, column=1, sticky='ew'); self.all_widgets.append(self.task_entry)
        self.task_entry.insert(0, "Enter task here...")
        self.task_entry.bind("<FocusIn>", lambda e: self.task_entry.get() == "Enter task here..." and (self.task_entry.delete(0, tk.END), self.task_entry.config(fg=self.theme[THEME_FG])))
        self.task_entry.bind("<FocusOut>", lambda e: not self.task_entry.get() and (self.task_entry.config(fg="grey"), self.task_entry.insert(0, "Enter task here...")))
        
        btn_frame = tk.Frame(self.task_frame); btn_frame.grid(row=2, column=0, pady=5, sticky='w'); self.all_widgets.append(btn_frame)
        self.add_task_btn = tk.Button(btn_frame, text="Add Task", command=self.add_task, relief="flat"); self.add_task_btn.pack(side="left", padx=5); self.all_widgets.append(self.add_task_btn)
        self.del_task_btn = tk.Button(btn_frame, text="Delete Selected", command=self.delete_task, relief="flat"); self.del_task_btn.pack(side="left", padx=5); self.all_widgets.append(self.del_task_btn)
        self.del_all_btn = tk.Button(btn_frame, text="Delete All", command=self.delete_all_tasks, relief="flat"); self.del_all_btn.pack(side="left", padx=5); self.all_widgets.append(self.del_all_btn)

        list_frame = tk.Frame(self.task_frame); list_frame.grid(row=3, column=0, sticky='nsew'); self.all_widgets.append(list_frame)
        list_frame.grid_rowconfigure(0, weight=1); list_frame.grid_columnconfigure(0, weight=1)
        self.task_listbox = tk.Listbox(list_frame, relief="flat", font=(FONT_FAMILY, 12), height=8); self.task_listbox.grid(row=0, column=0, sticky='nsew'); self.all_widgets.append(self.task_listbox)
        self.task_listbox.bind("<Double-Button-1>", self.edit_task_description)
        self.scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.task_listbox.yview); self.scrollbar.grid(row=0, column=1, sticky='ns'); self.all_widgets.append(self.scrollbar)
        self.task_listbox.config(yscrollcommand=self.scrollbar.set)

    def _bind_shortcuts(self):
        self.bind("<space>", lambda e: self.toggle_start_pause())
        self.bind("<r>", lambda e: self.reset_timer())
        self.bind("<R>", lambda e: self.reset_timer())
        self.bind("<Control-p>", lambda e: self.switch_mode(MODES["POMODORO"]))
        self.bind("<Control-s>", lambda e: self.switch_mode(MODES["SHORT_BREAK"]))
        self.bind("<Control-l>", lambda e: self.switch_mode(MODES["LONG_BREAK"]))
        self.bind("<Control-t>", lambda e: self.switch_mode(MODES["STOPWATCH"]))
        self.task_entry.bind("<Control-Return>", lambda e: self.add_task())
        self.bind("<Delete>", lambda e: self.delete_task())
        self.bind("<Control-d>", lambda e: self.delete_all_tasks())
        self.bind("<Control-q>", lambda e: self._on_closing())

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.theme = THEMES[self.theme_name]
        self.settings[SETTING_THEME] = self.theme_name
        self._apply_theme(animated=True)

    def _apply_theme(self, animated=False, widget_index=0):
        # Base case for recursion: Apply theme to special widgets at the end
        if not animated or widget_index >= len(self.all_widgets):
            self._configure_special_widgets()
            self._recolor_listbox_tasks()
            return
        
        # Recursive step: Apply theme to one widget
        self._configure_widget_theme(self.all_widgets[widget_index])
        
        # Schedule the next call to create an animation effect
        self.after(10, self._apply_theme, True, widget_index + 1)
        
    def _configure_widget_theme(self, widget):
        widget_class = widget.winfo_class()
        bg, fg = self.theme[THEME_BG], self.theme[THEME_FG]

        if widget in [self.session_frame, self.session_label]: bg = self.theme[THEME_SESSION_BG]
        elif widget == self.goal_label: fg = self.theme[THEME_ACCENT]
        elif widget_class == "Entry":
            bg = self.theme[THEME_BTN]
            fg = "grey" if "Enter task" in widget.get() else self.theme[THEME_FG]
            widget.config(insertbackground=self.theme[THEME_FG])
        elif widget_class in ["Button", "Menubutton"]: bg = self.theme[THEME_BTN]
        elif widget_class == "Listbox":
            bg = self.theme[THEME_BTN]
            widget.config(selectbackground=self.theme[THEME_ACCENT])
        elif widget_class == "Scrollbar": widget.config(troughcolor=self.theme[THEME_BTN])
        
        try: widget.config(bg=bg, fg=fg)
        except tk.TclError:
            try: widget.config(bg=bg)
            except tk.TclError: pass

    def _configure_special_widgets(self):
        self.config(bg=self.theme[THEME_BG])
        self.menubar.config(bg=self.theme[THEME_BG], fg=self.theme[THEME_FG])
        self.settings_menu.config(bg=self.theme[THEME_BG], fg=self.theme[THEME_FG])
        self.priority_menu.config(bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG], activebackground=self.theme[THEME_BTN_ACTIVE], relief='flat')
        self.priority_menu["menu"].config(bg=self.theme[THEME_BTN], fg=self.theme[THEME_FG])
        self._update_mode_buttons_display()
        for name, btn in self.control_buttons.items():
            btn.config(bg=self.theme[name.upper()], fg=self.theme["FOREGROUND"], activebackground=self.theme[f"{name.upper()}_ACTIVE"])

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            if self.current_mode == MODES["STOPWATCH"]: self.run_stopwatch()
            else:
                if self.current_mode == MODES["POMODORO"]: self.quote_label.config(text=random.choice(MOTIVATIONAL_QUOTES))
                self.run_countdown()
            self._update_button_states()

    def pause_or_stop_timer(self):
        if self.is_running:
            self.is_running = False
            self._update_button_states()
            if self.timer_id: self.after_cancel(self.timer_id)

    def reset_timer(self):
        if self.timer_id: self.after_cancel(self.timer_id)
        self.is_running = False
        if self.current_mode == MODES["STOPWATCH"]: self.stopwatch_time = 0
        self.switch_mode(self.current_mode, force_reset=True)

    def toggle_start_pause(self):
        if self.is_running: self.pause_or_stop_timer()
        else: self.start_timer()

    def run_countdown(self):
        if self.is_running and self.time_left > 0:
            self.time_left -= 1
            self._update_timer_display()
            self.timer_id = self.after(1000, self.run_countdown)
        elif self.time_left <= 0:
            self.is_running = False
            self._handle_timer_completion()

    def run_stopwatch(self):
        if self.is_running:
            self.stopwatch_time += 1
            self._update_timer_display()
            self.timer_id = self.after(1000, self.run_stopwatch)

    def switch_mode(self, mode, force_reset=False):
        if self.is_running and not force_reset: return
        self.is_running = False
        if self.timer_id: self.after_cancel(self.timer_id)
        self.current_mode = mode
        if mode == MODES["STOPWATCH"]:
            self.time_left = self.stopwatch_time = 0
        else:
            mode_key_map = {MODES["POMODORO"]: SETTING_POMO_DUR, MODES["SHORT_BREAK"]: SETTING_SHORT_DUR, MODES["LONG_BREAK"]: SETTING_LONG_DUR}
            duration_key = mode_key_map[mode]
            self.time_left = self.settings.get(duration_key, 0)
        self._update_timer_display()
        self._update_button_states()
        self._update_mode_buttons_display()

    def _handle_timer_completion(self):
        self._play_sound()
        messagebox.showinfo("Timer Finished!", f"{self.current_mode} session is complete!")

        next_mode = MODES["POMODORO"]
        if self.current_mode == MODES["POMODORO"]:
            self.sessions_completed += 1
            self.session_label.config(text=f"Sessions Completed: {self.sessions_completed}")
            interval = self.settings[SETTING_INTERVAL]
            is_long_break = self.sessions_completed > 0 and self.sessions_completed % interval == 0
            next_mode = MODES["LONG_BREAK"] if is_long_break else MODES["SHORT_BREAK"]
        self.switch_mode(next_mode, force_reset=True)
        self.attributes('-topmost', 1) # Bring window to front
        self.attributes('-topmost', 0)

    def add_task(self):
        task_text = self.task_entry.get().strip()
        if task_text and task_text != "Enter task here...":
            new_task = { "text": task_text, "priority": self.priority_var.get(), "description": "" }
            self.tasks.append(new_task)
            self.task_entry.delete(0, tk.END)
            self.focus_set()
            self._sort_and_refresh_tasks()
            self._save_tasks()

    def delete_task(self):
        selected_indices = self.task_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select a task to delete.")
            return
        
        # Sort indices in reverse to avoid index shifting issues during deletion
        for index in sorted(selected_indices, reverse=True):
            self.tasks.pop(index)
            self.task_listbox.delete(index)
        
        self._save_tasks()

    def delete_all_tasks(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete all tasks?"):
            self.tasks.clear()
            self.task_listbox.delete(0, tk.END)
            self._save_tasks()

    def edit_task_description(self, event):
        try:
            idx = self.task_listbox.curselection()[0]
            task_obj = self.tasks[idx]
            dialog = TaskDescriptionDialog(self, task_obj['text'], task_obj.get('description', ""), self.theme)
            self.wait_window(dialog)
            if dialog.result is not None:
                task_obj['description'] = dialog.result
                self._save_tasks()
        except IndexError: pass # No item selected

    def open_settings_window(self):
        dialog = SettingsWindow(self, self.settings, self.theme)
        self.wait_window(dialog)
        if dialog.result:
            self.settings.update(dialog.result)
            self._save_json(SETTINGS_FILE, self.settings)
            self.switch_mode(self.current_mode, force_reset=True)
            messagebox.showinfo("Settings Updated", "Timer settings have been saved.")

    def reset_settings(self):
        if messagebox.askyesno("Reset Settings", "Reset all settings to default?"):
            theme = self.settings[SETTING_THEME] # Preserve theme
            self.settings = DEFAULT_SETTINGS.copy()
            self.settings[SETTING_THEME] = theme
            self._save_json(SETTINGS_FILE, self.settings)
            self.switch_mode(self.current_mode, force_reset=True)
            messagebox.showinfo("Settings Reset", "Settings have been reset to default values.")

    def _save_tasks(self):
        self._save_json(TASKS_FILE, self.tasks)

    def _load_tasks_to_listbox(self):
        self.task_listbox.delete(0, tk.END)
        for task in self.tasks:
            display_text = f"[{task['priority'][0]}] {task['text']}"
            self.task_listbox.insert(tk.END, display_text)
        self._recolor_listbox_tasks()
        
    def _recolor_listbox_tasks(self):
        for i, task in enumerate(self.tasks):
            priority_key = f"{task['priority'].upper()}_PRIORITY"
            color = self.theme.get(priority_key, self.theme[THEME_FG])
            self.task_listbox.itemconfig(i, {'fg': color})

    def _check_daily_goal(self):
        goal_data = self._load_json(GOAL_FILE, default={})
        today = str(date.today())
        self.daily_goal = goal_data.get("goal", "") if goal_data.get("date") == today else ""
        self._update_goal_display()
        if not self.daily_goal: self.set_daily_goal(prompt="What is your main goal for today?")

    def set_daily_goal(self, prompt="Edit your daily goal:"):
        dialog = DailyGoalDialog(self, prompt, self.daily_goal, self.theme)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.daily_goal = dialog.result.strip()
            self._save_json(GOAL_FILE, {"date": str(date.today()), "goal": self.daily_goal})
            self._update_goal_display()

    def _update_goal_display(self):
        text = f"Today's Goal: {self.daily_goal}" if self.daily_goal else "Click to set your daily goal!"
        self.goal_label.config(text=text)

    def _update_button_states(self):
        is_stopwatch = self.current_mode == MODES["STOPWATCH"]
        self.control_buttons["pause"].config(text="Stop" if is_stopwatch else "Pause")
        self.control_buttons["start"].config(state="disabled" if self.is_running else "normal")
        self.control_buttons["pause"].config(state="normal" if self.is_running else "disabled")
        if not is_stopwatch:
            mode_key_map = {MODES["POMODORO"]: SETTING_POMO_DUR, MODES["SHORT_BREAK"]: SETTING_SHORT_DUR, MODES["LONG_BREAK"]: SETTING_LONG_DUR}
            duration_key = mode_key_map[self.current_mode]
            is_at_start = self.time_left == self.settings.get(duration_key, 0)
            self.control_buttons["start"].config(text="Start" if is_at_start else "Resume")

    def _update_timer_display(self):
        display_time = self.stopwatch_time if self.current_mode == MODES["STOPWATCH"] else self.time_left
        self.timer_label.config(text=self._format_time(display_time))

    def _update_mode_buttons_display(self):
        for mode, button in self.mode_buttons.items():
            is_active = (mode == self.current_mode)
            button.config(bg=self.theme[THEME_ACCENT] if is_active else self.theme[THEME_BTN], fg=self.theme[THEME_FG], relief="sunken" if is_active else "flat")

    def _format_time(self, seconds):
        if self.current_mode == MODES["STOPWATCH"]:
            h, rem = divmod(seconds, 3600); m, s = divmod(rem, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def _sort_and_refresh_tasks(self):
        """Sorts the internal task list and updates the listbox."""
        self.tasks.sort(key=lambda t: PRIORITY_MAP.get(t['priority'], 99))
        self._load_tasks_to_listbox()
        
    def _run_sound_in_thread(self, path):
        """Target function for the sound playing thread."""
        try:
            pygame.mixer.Sound(path).play()
        except pygame.error as e:
            print(f"Error playing sound in thread: {e}")

    def _play_sound(self):
        sound_path = self.settings.get(SETTING_SOUND_PATH)
        if SOUND_MODULE and pygame.mixer.get_init() and sound_path and os.path.exists(sound_path):
            # Run sound playback in a daemon thread to avoid blocking the GUI
            self.sound_thread = threading.Thread(target=self._run_sound_in_thread, args=(sound_path,), daemon=True)
            self.sound_thread.start()
        else:
            self.bell() # Fallback for no sound file or pygame error

    def _load_settings(self):
        settings = self._load_json(SETTINGS_FILE, default=DEFAULT_SETTINGS.copy())
        # --- Backward compatibility for old settings format ---
        if "pomodoro_mins" in settings:
            settings[SETTING_POMO_DUR] = settings.pop("pomodoro_mins", 25) * 60
            settings[SETTING_SHORT_DUR] = settings.pop("short_break_mins", 5) * 60
            settings[SETTING_LONG_DUR] = settings.pop("long_break_mins", 15) * 60
        return settings

    def _load_json(self, file_path, default=None):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return default if default is not None else {}

    def _save_json(self, file_path, data):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            messagebox.showerror("File Error", f"Could not save data to {file_path}:\n{e}")

    def _on_closing(self):
        self._save_json(SETTINGS_FILE, self.settings)
        self._save_tasks()
        self.destroy()

# --- 6. Main Execution Block ---
def main():
    """Creates and runs the Pomodoro Timer application."""
    app = PomodoroTimer()
    app.mainloop()

if __name__ == "__main__":
    main()
