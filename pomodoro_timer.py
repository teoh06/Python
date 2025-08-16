# pomodoro_timer.py

# --- 1. Imports ---
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import json
import os
import threading
import random
from datetime import date

# --- 2. Constants ---
TASKS_FILE = "pomodoro_tasks.json"
SETTINGS_FILE = "pomodoro_settings.json"
GOAL_FILE = "daily_goal.json"

# UI Styling and Configuration
FONT_FAMILY = "Comic Sans MS"
THEMES = {
    "dark": {
        "BACKGROUND": "#1E1E1E", "FOREGROUND": "#F0F0F0", "ACCENT": "#FF6347",
        "BUTTON": "#3A3A3A", "BUTTON_ACTIVE": "#5C5C5C", "SESSION_BG": "#2C2C2C",
        "HIGH_PRIORITY": "#D32F2F", "MEDIUM_PRIORITY": "#FBC02D", "LOW_PRIORITY": "#388E3C",
        "START": "#28A745", "START_ACTIVE": "#218838", "PAUSE": "#FFC107",
        "PAUSE_ACTIVE": "#FFA000", "RESET": "#17A2B8", "RESET_ACTIVE": "#138496",
    },
    "light": {
        "BACKGROUND": "#F0F0F0", "FOREGROUND": "#1E1E1E", "ACCENT": "#D32F2F",
        "BUTTON": "#E0E0E0", "BUTTON_ACTIVE": "#C7C7C7", "SESSION_BG": "#FFFFFF",
        "HIGH_PRIORITY": "#C62828", "MEDIUM_PRIORITY": "#F9A825", "LOW_PRIORITY": "#2E7D32",
        "START": "#4CAF50", "START_ACTIVE": "#45A049", "PAUSE": "#FFEB3B",
        "PAUSE_ACTIVE": "#FDD835", "RESET": "#00BCD4", "RESET_ACTIVE": "#00ACC1",
    }
}

# Timer Modes & Default Durations (in seconds)
MODES = {
    "POMODORO": "Pomodoro", "SHORT_BREAK": "Short Break",
    "LONG_BREAK": "Long Break", "STOPWATCH": "Stopwatch"
}

DEFAULT_SETTINGS = {
    "pomodoro_duration": 25 * 60, "short_break_duration": 5 * 60, "long_break_duration": 15 * 60,
    "long_break_interval": 4, "sound_file_path": "", "theme": "dark"
}

PRIORITIES = ["High", "Medium", "Low"]

MOTIVATIONAL_QUOTES = [
    "The secret of getting ahead is getting started.", "The only way to do great work is to love what you do.",
    "Believe you can and you're halfway there.", "The future depends on what you do today."
]

# --- 3. Sound Module Initialization ---
try:
    import pygame
    SOUND_MODULE = 'pygame'
except ImportError:
    SOUND_MODULE = None

# --- 4. Custom Dialog Windows ---
class CustomDialog(tk.Toplevel):
    """Base class for custom styled dialogs."""
    def __init__(self, parent, title, theme, geometry="400x300"):
        super().__init__(parent)
        self.theme = theme
        self.title(title); self.geometry(geometry)
        self.configure(bg=self.theme["BACKGROUND"])
        self.transient(parent); self.grab_set()
        self.result = None
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _create_buttons(self, show_save=True):
        btn_frame = tk.Frame(self, bg=self.theme["BACKGROUND"]); btn_frame.pack(pady=15)
        if show_save:
            tk.Button(btn_frame, text="Save", command=self._on_save, bg=self.theme["BUTTON"], fg=self.theme["FOREGROUND"], relief="flat").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Close", command=self._on_cancel, bg=self.theme["BUTTON"], fg=self.theme["FOREGROUND"], relief="flat").pack(side="left", padx=10)

    def _on_save(self): raise NotImplementedError
    def _on_cancel(self): self.result = None; self.destroy()

class SettingsWindow(CustomDialog):
    def __init__(self, parent, current_settings, theme):
        super().__init__(parent, "Settings", theme, "450x550")
        self.duration_entries = {}
        
        main_frame = tk.Frame(self, bg=self.theme["BACKGROUND"], padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        timer_frame = tk.LabelFrame(main_frame, text="Timer Durations", bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"], padx=10, pady=10)
        timer_frame.pack(fill="x", expand=True, pady=(0, 10))

        for i, (key, text) in enumerate({"pomodoro_duration": "Pomodoro:", "short_break_duration": "Short Break:", "long_break_duration": "Long Break:"}.items()):
            tk.Label(timer_frame, text=text, bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"], font=(FONT_FAMILY, 10)).grid(row=i, column=0, sticky='w', pady=5)
            mins, secs = divmod(current_settings.get(key, 0), 60)
            min_entry = tk.Entry(timer_frame, width=5, bg=self.theme["BUTTON"], fg=self.theme["FOREGROUND"], relief="flat"); min_entry.insert(0, str(mins)); min_entry.grid(row=i, column=1, padx=(10,0))
            tk.Label(timer_frame, text="min", bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"]).grid(row=i, column=2, padx=(2,10))
            sec_entry = tk.Entry(timer_frame, width=5, bg=self.theme["BUTTON"], fg=self.theme["FOREGROUND"], relief="flat"); sec_entry.insert(0, str(secs)); sec_entry.grid(row=i, column=3)
            tk.Label(timer_frame, text="sec", bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"]).grid(row=i, column=4, padx=2)
            self.duration_entries[key] = (min_entry, sec_entry)

        tk.Label(timer_frame, text="Long Break Interval:", bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"]).grid(row=3, column=0, sticky='w', pady=5)
        self.interval_entry = tk.Entry(timer_frame, width=5, bg=self.theme["BUTTON"], fg=self.theme["FOREGROUND"], relief="flat"); self.interval_entry.insert(0, str(current_settings.get("long_break_interval", 4))); self.interval_entry.grid(row=3, column=1, padx=(10,0))
        
        tk.Label(timer_frame, text="Sound File:", bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"]).grid(row=4, column=0, sticky='w', pady=10)
        self.sound_entry = tk.Entry(timer_frame, bg=self.theme["BUTTON"], fg=self.theme["FOREGROUND"], relief="flat"); self.sound_entry.insert(0, current_settings.get("sound_file_path", "")); self.sound_entry.grid(row=4, column=1, columnspan=4, sticky='ew', padx=(10,0))
        tk.Button(timer_frame, text="Browse...", bg=self.theme["BUTTON"], fg=self.theme["FOREGROUND"], command=self._browse, relief="flat").grid(row=4, column=5, padx=5)

        shortcuts_frame = tk.LabelFrame(main_frame, text="Keyboard Shortcuts", bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"], padx=10, pady=10)
        shortcuts_frame.pack(fill="x", expand=True)
        
        shortcuts = {
            "Start / Pause Timer": "Spacebar", "Reset Timer": "R", "Switch to Pomodoro": "Ctrl + P",
            "Switch to Short Break": "Ctrl + S", "Switch to Long Break": "Ctrl + L", "Switch to Stopwatch": "Ctrl + T",
            "Add New Task": "Ctrl + Enter", "Delete Selected Task": "Delete", "Delete All Tasks": "Ctrl + D",
            "Quit Application": "Ctrl + Q"
        }
        for i, (action, key) in enumerate(shortcuts.items()):
            tk.Label(shortcuts_frame, text=action, bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"]).grid(row=i, column=0, sticky="w", padx=5)
            tk.Label(shortcuts_frame, text=key, bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"], font=(FONT_FAMILY, 10, "bold")).grid(row=i, column=1, sticky="e", padx=5)
        shortcuts_frame.columnconfigure(1, weight=1)

        self._create_buttons()

    def _browse(self):
        path = filedialog.askopenfilename(title="Select Sound File", filetypes=[("Audio Files", "*.wav *.mp3")])
        if path: self.sound_entry.delete(0, tk.END); self.sound_entry.insert(0, path)

    def _on_save(self):
        try:
            self.result = {}
            for key, (min_e, sec_e) in self.duration_entries.items(): self.result[key] = int(min_e.get() or 0) * 60 + int(sec_e.get() or 0)
            self.result["long_break_interval"] = int(self.interval_entry.get() or 1)
            self.result["sound_file_path"] = self.sound_entry.get().strip()
            if any(v < 0 for v in self.result.values() if isinstance(v, int)): raise ValueError("Negative values not allowed.")
            self.destroy()
        except (ValueError, TypeError): messagebox.showerror("Invalid Input", "Please enter valid numbers.", parent=self)

class TaskDescriptionDialog(CustomDialog):
    def __init__(self, parent, task_text, current_description, theme):
        super().__init__(parent, "Task Description", theme, "450x300")
        frame = tk.Frame(self, bg=self.theme["BACKGROUND"], padx=15, pady=15); frame.pack(fill="both", expand=True)
        tk.Label(frame, text=f"Description for: {task_text}", bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"], font=(FONT_FAMILY, 12, "bold")).pack(anchor="w", pady=(0, 10))
        text_frame = tk.Frame(frame, bg=self.theme["BACKGROUND"]); text_frame.pack(fill="both", expand=True)
        self.desc_text = tk.Text(text_frame, wrap="word", bg=self.theme["BUTTON"], fg=self.theme["FOREGROUND"], relief="flat", insertbackground=self.theme["FOREGROUND"], font=(FONT_FAMILY, 11))
        self.desc_text.pack(side="left", fill="both", expand=True); self.desc_text.insert("1.0", current_description)
        scrollbar = tk.Scrollbar(text_frame, command=self.desc_text.yview, bg=self.theme["BACKGROUND"], troughcolor=self.theme["BUTTON"]); scrollbar.pack(side="right", fill="y")
        self.desc_text.config(yscrollcommand=scrollbar.set)
        self._create_buttons(); self.desc_text.focus_set()

    def _on_save(self): self.result = self.desc_text.get("1.0", "end-1c").strip(); self.destroy()

class DailyGoalDialog(CustomDialog):
    def __init__(self, parent, prompt, current_goal, theme):
        super().__init__(parent, "Daily Goal", theme, "450x200")
        frame = tk.Frame(self, bg=self.theme["BACKGROUND"], padx=15, pady=15); frame.pack(fill="both", expand=True)
        tk.Label(frame, text=prompt, bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"], font=(FONT_FAMILY, 12, "bold")).pack(anchor="w", pady=(0, 10))
        self.goal_entry = tk.Entry(frame, bg=self.theme["BUTTON"], fg=self.theme["FOREGROUND"], relief="flat", insertbackground=self.theme["FOREGROUND"], font=(FONT_FAMILY, 11))
        self.goal_entry.pack(fill="x", ipady=5, pady=10); self.goal_entry.insert(0, current_goal)
        self._create_buttons(); self.goal_entry.focus_set()

    def _on_save(self): self.result = self.goal_entry.get().strip(); self.destroy()

# --- 5. Main Application ---
class PomodoroTimer(tk.Tk):
    def __init__(self):
        super().__init__()
        if SOUND_MODULE:
            try:
                pygame.mixer.init()
            except pygame.error:
                print("Pygame mixer could not be initialized.")

        self.settings = self._load_settings()
        self.theme_name = self.settings.get("theme", "dark")
        self.theme = THEMES[self.theme_name]

        self.current_mode = MODES["POMODORO"]
        self.time_left = self.settings["pomodoro_duration"]
        self.sessions_completed = 0
        self.is_running = False
        self.timer_id = None
        self.stopwatch_time = 0
        self.sound_channel = None
        self.task_data = self._load_json(TASKS_FILE, default={'tasks': [], 'descriptions': {}})
        self.task_descriptions = self.task_data.get('descriptions', {})
        self.mode_buttons = {}
        self.all_widgets = []

        self.title("Study Pomodoro Timer"); self.geometry("500x800")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Centering Frame
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        self.main_frame = tk.Frame(self); self.main_frame.grid(row=0, column=0)
        self.all_widgets.append(self.main_frame)

        self._setup_ui()
        self._bind_shortcuts()
        self.after(100, self._check_daily_goal)

    def _setup_ui(self):
        self._create_menu()
        self.goal_label = self._create_label("Click to set your daily goal!", font=(FONT_FAMILY, 12, "italic"), fg_theme_key="ACCENT", wraplength=480, pady=(0, 5))
        self.goal_label.bind("<Button-1>", lambda e: self.set_daily_goal())
        self.session_frame = tk.Frame(self.main_frame, relief='groove', borderwidth=2); self.session_frame.pack(pady=5, fill='x'); self.all_widgets.append(self.session_frame)
        self.session_label = self._create_label("Sessions Completed: 0", parent=self.session_frame, font=(FONT_FAMILY, 12, "bold"), bg_theme_key="SESSION_BG", pady=10)
        self._create_mode_buttons()
        self.timer_label = self._create_label(self._format_time(self.time_left), font=(FONT_FAMILY, 60, "bold"), pady=20)
        self.quote_label = self._create_label("Let's get started!", font=(FONT_FAMILY, 11, "italic"), wraplength=480, pady=(0, 10))
        self._create_control_buttons()
        self._create_task_manager()
        self._apply_theme()
        self._load_tasks_to_listbox()

    def _create_label(self, text, parent=None, **kwargs):
        parent = parent or self.main_frame
        pack_opts = {k: kwargs.pop(k) for k in ['pady', 'padx', 'fill', 'expand', 'side'] if k in kwargs}
        kwargs['bg'] = self.theme[kwargs.pop('bg_theme_key', 'BACKGROUND')]
        kwargs['fg'] = self.theme[kwargs.pop('fg_theme_key', 'FOREGROUND')]
        label = tk.Label(parent, text=text, **kwargs); label.pack(**pack_opts)
        self.all_widgets.append(label)
        return label

    def _create_menu(self):
        self.menubar = tk.Menu(self, tearoff=0); self.config(menu=self.menubar)
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="⚙️ Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="Configure Timers", command=self.open_settings_window)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label="Reset Defaults", command=self.reset_settings)
        self.menubar.add_command(label="☀️ Light /🌙 Dark", command=self.toggle_theme)

    def _create_mode_buttons(self):
        self.mode_frame = tk.Frame(self.main_frame); self.mode_frame.pack(pady=10); self.all_widgets.append(self.mode_frame)
        for mode in MODES.values():
            btn = tk.Button(self.mode_frame, text=mode, relief="flat", font=(FONT_FAMILY, 10), command=lambda m=mode: self.switch_mode(m))
            btn.pack(side="left", padx=5, ipadx=5, ipady=2)
            self.mode_buttons[mode] = btn

    def _create_control_buttons(self):
        self.control_frame = tk.Frame(self.main_frame); self.control_frame.pack(pady=10); self.all_widgets.append(self.control_frame)
        configs = {"start": self.start_timer, "pause": self.pause_or_stop_timer, "reset": self.reset_timer}
        self.control_buttons = {}
        for name, command in configs.items():
            btn = tk.Button(self.control_frame, text=name.capitalize(), relief="flat", font=(FONT_FAMILY, 16, "bold"), command=command)
            btn.pack(side="left", padx=10)
            self.control_buttons[name] = btn
        self.control_buttons["pause"].config(state="disabled")

    def _create_task_manager(self):
        self.task_frame = tk.Frame(self.main_frame); self.task_frame.pack(pady=15, fill="both", expand=True); self.all_widgets.append(self.task_frame)
        self._create_label("Tasks", parent=self.task_frame, font=(FONT_FAMILY, 14, "bold"))
        input_frame = tk.Frame(self.task_frame); input_frame.pack(fill="x", pady=5); self.all_widgets.append(input_frame)
        self.priority_var = tk.StringVar(value=PRIORITIES[1])
        self.priority_menu = tk.OptionMenu(input_frame, self.priority_var, *PRIORITIES); self.priority_menu.pack(side="left", padx=(0, 5)); self.all_widgets.append(self.priority_menu)
        self.task_entry = tk.Entry(input_frame, fg="grey", relief="flat", font=(FONT_FAMILY, 12)); self.task_entry.pack(side="left", fill="x", expand=True); self.all_widgets.append(self.task_entry)
        self.task_entry.insert(0, "Enter task here...")
        self.task_entry.bind("<FocusIn>", lambda e: self.task_entry.get() == "Enter task here..." and (self.task_entry.delete(0, tk.END), self.task_entry.config(fg=self.theme["FOREGROUND"])))
        self.task_entry.bind("<FocusOut>", lambda e: not self.task_entry.get() and (self.task_entry.config(fg="grey"), self.task_entry.insert(0, "Enter task here...")))
        btn_frame = tk.Frame(self.task_frame); btn_frame.pack(pady=5, fill="x"); self.all_widgets.append(btn_frame)
        self.add_task_btn = tk.Button(btn_frame, text="Add Task", command=self.add_task, relief="flat"); self.add_task_btn.pack(side="left", padx=5); self.all_widgets.append(self.add_task_btn)
        self.del_task_btn = tk.Button(btn_frame, text="Delete Selected", command=self.delete_task, relief="flat"); self.del_task_btn.pack(side="left", padx=5); self.all_widgets.append(self.del_task_btn)
        self.del_all_btn = tk.Button(btn_frame, text="Delete All", command=self.delete_all_tasks, relief="flat"); self.del_all_btn.pack(side="left", padx=5); self.all_widgets.append(self.del_all_btn)
        list_frame = tk.Frame(self.task_frame); list_frame.pack(fill="both", expand=True); self.all_widgets.append(list_frame)
        self.task_listbox = tk.Listbox(list_frame, relief="flat", font=(FONT_FAMILY, 12), height=8); self.task_listbox.pack(side="left", fill="both", expand=True); self.all_widgets.append(self.task_listbox)
        self.task_listbox.bind("<Double-Button-1>", self.edit_task_description)
        self.scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.task_listbox.yview); self.scrollbar.pack(side="right", fill="y"); self.all_widgets.append(self.scrollbar)
        self.task_listbox.config(yscrollcommand=self.scrollbar.set)

    def _bind_shortcuts(self):
        self.bind("<space>", lambda e: self.toggle_start_pause())
        self.bind("<r>", lambda e: self.reset_timer())
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
        self.settings['theme'] = self.theme_name
        self._apply_theme()

    def _apply_theme(self):
        self.config(bg=self.theme["BACKGROUND"])
        self.menubar.config(bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"])
        self.settings_menu.config(bg=self.theme["BACKGROUND"], fg=self.theme["FOREGROUND"])

        for widget in self.all_widgets:
            widget_class = widget.winfo_class()
            bg_color, fg_color = self.theme["BACKGROUND"], self.theme["FOREGROUND"]

            if widget in [self.session_frame, self.session_label]: bg_color = self.theme["SESSION_BG"]
            elif widget == self.goal_label: fg_color = self.theme["ACCENT"]
            elif widget_class == "Entry":
                bg_color = self.theme["BUTTON"]
                fg_color = "grey" if widget.get() == "Enter task here..." else self.theme["FOREGROUND"]
                widget.config(insertbackground=self.theme["FOREGROUND"])
            elif widget_class in ["Button", "Menubutton", "TMenubutton"]: bg_color = self.theme["BUTTON"]
            elif widget_class == "Listbox":
                bg_color = self.theme["BUTTON"]
                widget.config(selectbackground=self.theme["ACCENT"])
            elif widget_class == "Scrollbar": widget.config(troughcolor=self.theme["BUTTON"])
            
            try: widget.config(bg=bg_color, fg=fg_color)
            except tk.TclError:
                try: widget.config(bg=bg_color)
                except tk.TclError: pass
        
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
            self.is_running = False; self._update_button_states()
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
            self.time_left -= 1; self._update_timer_display()
            self.timer_id = self.after(1000, self.run_countdown)
        elif self.time_left <= 0:
            self.is_running = False; self._handle_timer_completion()

    def run_stopwatch(self):
        if self.is_running:
            self.stopwatch_time += 1; self._update_timer_display()
            self.timer_id = self.after(1000, self.run_stopwatch)

    def switch_mode(self, mode, force_reset=False):
        if self.is_running and not force_reset: return
        self.is_running = False
        if self.timer_id: self.after_cancel(self.timer_id)
        self.current_mode = mode
        if mode == MODES["STOPWATCH"]: self.time_left = self.stopwatch_time = 0
        else:
            mode_key = next(k for k, v in MODES.items() if v == mode).lower()
            self.time_left = self.settings.get(f"{mode_key}_duration", 0)
        self._update_timer_display(); self._update_button_states(); self._update_mode_buttons_display()

    def _handle_timer_completion(self):
        self._play_sound()
        messagebox.showinfo("Timer Finished!", f"{self.current_mode} session is complete!")
        if self.sound_channel:
            self.sound_channel.stop()
            self.sound_channel = None

        next_mode = MODES["POMODORO"]
        if self.current_mode == MODES["POMODORO"]:
            self.sessions_completed += 1
            self.session_label.config(text=f"Sessions Completed: {self.sessions_completed}")
            next_mode = MODES["LONG_BREAK"] if self.sessions_completed % self.settings["long_break_interval"] == 0 else MODES["SHORT_BREAK"]
        self.switch_mode(next_mode, force_reset=True)

    def add_task(self):
        task_text = self.task_entry.get().strip()
        if task_text and task_text != "Enter task here...":
            priority = self.priority_var.get()
            self.task_listbox.insert(tk.END, f"[{priority[0]}] {task_text}")
            self.task_listbox.itemconfig(tk.END, {'fg': self.theme[f"{priority.upper()}_PRIORITY"]})
            self.task_entry.delete(0, tk.END); self.focus_set()
            self._sort_tasks(); self._save_tasks()

    def delete_task(self):
        try:
            idx = self.task_listbox.curselection()[0]
            self.task_descriptions.pop(self.task_listbox.get(idx), None)
            self.task_listbox.delete(idx); self._save_tasks()
        except IndexError: messagebox.showwarning("No Selection", "Please select a task to delete.")

    def delete_all_tasks(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete all tasks?"):
            self.task_listbox.delete(0, tk.END); self.task_descriptions.clear(); self._save_tasks()

    def edit_task_description(self, event):
        try:
            idx = self.task_listbox.curselection()[0]; task_text = self.task_listbox.get(idx)
            dialog = TaskDescriptionDialog(self, task_text, self.task_descriptions.get(task_text, ""), self.theme)
            self.wait_window(dialog)
            if dialog.result is not None: self.task_descriptions[task_text] = dialog.result; self._save_tasks()
        except IndexError: pass

    def open_settings_window(self):
        dialog = SettingsWindow(self, self.settings, self.theme); self.wait_window(dialog)
        if dialog.result:
            self.settings.update(dialog.result); self._save_json(SETTINGS_FILE, self.settings)
            self.switch_mode(self.current_mode, force_reset=True)
            messagebox.showinfo("Settings Updated", "Timer settings have been saved.")

    def reset_settings(self):
        if messagebox.askyesno("Reset Settings", "Reset all settings to default?"):
            theme = self.settings['theme'] # Preserve theme
            self.settings = DEFAULT_SETTINGS.copy()
            self.settings['theme'] = theme
            self._save_json(SETTINGS_FILE, self.settings)
            self.switch_mode(self.current_mode, force_reset=True)
            messagebox.showinfo("Settings Reset", "Settings have been reset to default values.")

    def _save_tasks(self):
        tasks = [{'text': self.task_listbox.get(i), 'color': self.task_listbox.itemcget(i, 'fg')} for i in range(self.task_listbox.size())]
        self._save_json(TASKS_FILE, {'tasks': tasks, 'descriptions': self.task_descriptions})

    def _load_tasks_to_listbox(self):
        for task in self.task_data.get('tasks', []):
            self.task_listbox.insert(tk.END, task['text'])
            priority_char = task['text'][1]
            priority = next((p for p in PRIORITIES if p.startswith(priority_char)), None)
            if priority: self.task_listbox.itemconfig(tk.END, {'fg': self.theme[f"{priority.upper()}_PRIORITY"]})
        self._sort_tasks()

    def _check_daily_goal(self):
        goal_data = self._load_json(GOAL_FILE, default={})
        self.daily_goal = goal_data.get("goal", "") if goal_data.get("date") == str(date.today()) else ""
        self._update_goal_display()
        if not self.daily_goal: self.set_daily_goal(prompt="What is your main goal for today?")

    def set_daily_goal(self, prompt="Edit your daily goal:"):
        dialog = DailyGoalDialog(self, prompt, self.daily_goal, self.theme); self.wait_window(dialog)
        if dialog.result is not None:
            self.daily_goal = dialog.result.strip()
            self._save_json(GOAL_FILE, {"date": str(date.today()), "goal": self.daily_goal})
            self._update_goal_display()

    def _update_goal_display(self): self.goal_label.config(text=f"Today's Goal: {self.daily_goal}" if self.daily_goal else "Click to set your daily goal!")

    def _update_button_states(self):
        is_stopwatch = self.current_mode == MODES["STOPWATCH"]
        self.control_buttons["pause"].config(text="Stop" if is_stopwatch else "Pause")
        self.control_buttons["start"].config(state="disabled" if self.is_running else "normal")
        self.control_buttons["pause"].config(state="normal" if self.is_running else "disabled")
        if not is_stopwatch:
            mode_key = next(k for k, v in MODES.items() if v == self.current_mode).lower()
            self.control_buttons["start"].config(text="Start" if self.time_left == self.settings.get(f"{mode_key}_duration", 0) else "Resume")

    def _update_timer_display(self):
        display_time = self.stopwatch_time if self.current_mode == MODES["STOPWATCH"] else self.time_left
        self.timer_label.config(text=self._format_time(display_time))

    def _update_mode_buttons_display(self):
        for mode, button in self.mode_buttons.items():
            is_active = mode == self.current_mode
            button.config(bg=self.theme["ACCENT"] if is_active else self.theme["BUTTON"], fg=self.theme["FOREGROUND"], relief="sunken" if is_active else "flat")

    def _format_time(self, seconds):
        if self.current_mode == MODES["STOPWATCH"]:
            h, rem = divmod(seconds, 3600); m, s = divmod(rem, 60); return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def _sort_tasks(self):
        tasks = [(self.task_listbox.get(i), self.task_listbox.itemcget(i, 'fg')) for i in range(self.task_listbox.size())]
        priority_map = {f"[{p[0]}]": i for i, p in enumerate(PRIORITIES)}
        tasks.sort(key=lambda item: priority_map.get(item[0][:3], 99))
        self.task_listbox.delete(0, tk.END)
        for text, color in tasks: self.task_listbox.insert(tk.END, text); self.task_listbox.itemconfig(tk.END, {'fg': color})

    def _play_sound(self):
        sound_path = self.settings.get("sound_file_path")
        if SOUND_MODULE and pygame.mixer.get_init() and sound_path and os.path.exists(sound_path):
            try: 
                sound = pygame.mixer.Sound(sound_path)
                self.sound_channel = sound.play()
            except pygame.error as e: 
                print(f"Error playing sound: {e}")
                self.bell()
        else: 
            self.bell()

    def _load_settings(self):
        settings = self._load_json(SETTINGS_FILE, default=DEFAULT_SETTINGS.copy())
        if "pomodoro_mins" in settings: # Backward compatibility
            settings["pomodoro_duration"] = settings.pop("pomodoro_mins", 25) * 60
            settings["short_break_duration"] = settings.pop("short_break_mins", 5) * 60
            settings["long_break_duration"] = settings.pop("long_break_mins", 15) * 60
        return settings

    def _load_json(self, file_path, default=None):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f: return json.load(f)
            except (json.JSONDecodeError, IOError): pass
        return default if default is not None else {}

    def _save_json(self, file_path, data):
        try:
            with open(file_path, 'w') as f: json.dump(data, f, indent=4)
        except IOError: pass

    def _on_closing(self): self._save_json(SETTINGS_FILE, self.settings); self._save_tasks(); self.destroy()

# --- 6. Main Execution Block ---
if __name__ == "__main__":
    app = PomodoroTimer()
    app.mainloop()
