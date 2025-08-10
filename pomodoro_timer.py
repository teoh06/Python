# Import necessary modules from Python's standard library.
import tkinter as tk
from tkinter import messagebox, simpledialog # Import simpledialog for description input
import json # Import json for handling task data storage, a common format for storing structured data
import os # Import os for file path handling, checking existence, and directory management

# Define default constants for timer settings and styling.
DEFAULT_POMODORO_MINS = 25
DEFAULT_SHORT_BREAK_MINS = 5
DEFAULT_LONG_BREAK_MINS = 15
DEFAULT_LONG_BREAK_INTERVAL = 4 # Every 4 Pomodoros

# Enhanced dark theme colors with a focus on Pomodoro aesthetics
COLOR_BACKGROUND = "#1E1E1E"  # Darker background for deep focus
COLOR_FOREGROUND = "#F0F0F0"  # Bright text for readability
COLOR_ACCENT = "#FF6347"      # Vibrant tomato red for emphasis
COLOR_BUTTON = "#3A3A3A"      # Slightly lighter for buttons
COLOR_BUTTON_ACTIVE = "#5C5C5C"
COLOR_START = "#28A745"       # Bright green for start (Pomodoro active)
COLOR_START_ACTIVE = "#218838" 
COLOR_PAUSE = "#FFC107"       # Amber for pause
COLOR_PAUSE_ACTIVE = "#FFA000"
COLOR_RESET = "#17A2B8"       # Cyan for reset
COLOR_RESET_ACTIVE = "#138496"
COLOR_HIGH_PRIORITY = "#D32F2F"  # Deep red for high priority
COLOR_MEDIUM_PRIORITY = "#FBC02D"  # Bright yellow
COLOR_LOW_PRIORITY = "#388E3C"     # Dark green
COLOR_SESSION_BG = "#2C2C2C"  # Slightly lighter for session panel

# File names for storing tasks and settings.
TASKS_FILE = "pomodoro_tasks.json"
SETTINGS_FILE = "pomodoro_settings.json"

# --- Attempt to import pygame for sound ---
SOUND_MODULE = None
try:
    import pygame
    pygame.mixer.init()
    SOUND_MODULE = 'pygame'
    print("Using pygame for sound playback.")
except ImportError as e:
    print(f"Warning: 'pygame' not found or failed to initialize ({e}). Sound notifications will be system beep or disabled.")
    SOUND_MODULE = None

# --- Settings Window Class ---
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, pomodoro_mins, short_break_mins, long_break_mins, long_break_interval, sound_file_path):
        super().__init__(parent)
        self.title("Timer Settings")
        self.geometry("400x350")
        self.configure(bg=COLOR_BACKGROUND)
        self.parent = parent
        self.result = None

        settings_frame = tk.Frame(self, bg=COLOR_BACKGROUND, padx=20, pady=20)
        settings_frame.pack(fill="both", expand=True)

        tk.Label(settings_frame, text="Pomodoro (minutes):", bg=COLOR_BACKGROUND, fg=COLOR_FOREGROUND, font=("Comic Sans MS", 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.pomodoro_entry = tk.Entry(settings_frame, width=10, bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, insertbackground=COLOR_FOREGROUND, relief="flat")
        self.pomodoro_entry.insert(0, str(pomodoro_mins))
        self.pomodoro_entry.grid(row=0, column=1, sticky='w', pady=5, padx=(10,0))

        tk.Label(settings_frame, text="Short Break (minutes):", bg=COLOR_BACKGROUND, fg=COLOR_FOREGROUND, font=("Comic Sans MS", 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.short_break_entry = tk.Entry(settings_frame, width=10, bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, insertbackground=COLOR_FOREGROUND, relief="flat")
        self.short_break_entry.insert(0, str(short_break_mins))
        self.short_break_entry.grid(row=1, column=1, sticky='w', pady=5, padx=(10,0))

        tk.Label(settings_frame, text="Long Break (minutes):", bg=COLOR_BACKGROUND, fg=COLOR_FOREGROUND, font=("Comic Sans MS", 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.long_break_entry = tk.Entry(settings_frame, width=10, bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, insertbackground=COLOR_FOREGROUND, relief="flat")
        self.long_break_entry.insert(0, str(long_break_mins))
        self.long_break_entry.grid(row=2, column=1, sticky='w', pady=5, padx=(10,0))

        tk.Label(settings_frame, text="Long Break Interval (Pomodoros):", bg=COLOR_BACKGROUND, fg=COLOR_FOREGROUND, font=("Comic Sans MS", 10)).grid(row=3, column=0, sticky='w', pady=5)
        self.interval_entry = tk.Entry(settings_frame, width=10, bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, insertbackground=COLOR_FOREGROUND, relief="flat")
        self.interval_entry.insert(0, str(long_break_interval))
        self.interval_entry.grid(row=3, column=1, sticky='w', pady=5, padx=(10,0))

        tk.Label(settings_frame, text="Sound File Path:", bg=COLOR_BACKGROUND, fg=COLOR_FOREGROUND, font=("Comic Sans MS", 10)).grid(row=4, column=0, sticky='w', pady=5)
        self.sound_path_entry = tk.Entry(settings_frame, bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, insertbackground=COLOR_FOREGROUND, relief="flat")
        self.sound_path_entry.insert(0, sound_file_path)
        self.sound_path_entry.grid(row=4, column=1, columnspan=2, sticky='ew', pady=5, padx=(10,0))
        settings_frame.columnconfigure(1, weight=1)

        browse_btn = tk.Button(settings_frame, text="Browse...", bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, command=self.browse_sound_file, relief="flat")
        browse_btn.grid(row=4, column=3, sticky='w', pady=5, padx=(5,0))

        button_frame = tk.Frame(self, bg=COLOR_BACKGROUND)
        button_frame.pack(pady=10)

        save_btn = tk.Button(button_frame, text="Save", bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, command=self.save_settings, relief="flat")
        save_btn.pack(side="left", padx=10)
        cancel_btn = tk.Button(button_frame, text="Cancel", bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, command=self.destroy, relief="flat")
        cancel_btn.pack(side="left", padx=10)

    def browse_sound_file(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Select Sound File",
            filetypes=[("Audio Files", "*.wav *.mp3"), ("WAV Files", "*.wav"), ("MP3 Files", "*.mp3"), ("All Files", "*.*")]
        )
        if file_path:
            self.sound_path_entry.delete(0, tk.END)
            self.sound_path_entry.insert(0, file_path)

    def save_settings(self):
        try:
            pom_mins = int(self.pomodoro_entry.get())
            short_mins = int(self.short_break_entry.get())
            long_mins = int(self.long_break_entry.get())
            interval = int(self.interval_entry.get())
            sound_path = self.sound_path_entry.get().strip()

            if pom_mins <= 0 or short_mins <= 0 or long_mins <= 0 or interval <= 0:
                raise ValueError("Values must be positive integers.")

            self.result = {
                "pomodoro_mins": pom_mins,
                "short_break_mins": short_mins,
                "long_break_mins": long_mins,
                "long_break_interval": interval,
                "sound_file_path": sound_path
            }
            self.destroy()
        except ValueError as e:
             messagebox.showerror("Invalid Input", f"Please enter valid positive integers for durations and interval.\nError: {e}")

# --- Main Application Class ---
class PomodoroTimer(tk.Tk):
    """
    The main class for the Pomodoro Timer application.
    """
    def __init__(self):
        """
        Initializes the main application window and its components.
        """
        super().__init__()
        # --- State Variables ---
        self.current_mode = "Pomodoro"
        self.settings = self.load_settings()
        self.pomodoro_mins = self.settings.get("pomodoro_mins", DEFAULT_POMODORO_MINS)
        self.short_break_mins = self.settings.get("short_break_mins", DEFAULT_SHORT_BREAK_MINS)
        self.long_break_mins = self.settings.get("long_break_mins", DEFAULT_LONG_BREAK_MINS)
        self.long_break_interval = self.settings.get("long_break_interval", DEFAULT_LONG_BREAK_INTERVAL)
        self.sound_file_path = self.settings.get("sound_file_path", "")
        self.time_left = self.pomodoro_mins * 60

        self.is_running = False
        self.timer_id = None
        self.sessions_completed = 0
        # --- Window Configuration ---
        self.title("Enhanced Study Pomodoro Timer")
        self.geometry("500x750")
        self.config(bg=COLOR_BACKGROUND, padx=20, pady=20)

        # --- GUI Widgets ---
        self.create_menu()
        self.create_session_counter()
        self.create_mode_buttons()
        self.create_timer_display()
        self.create_control_buttons()
        self.create_task_manager()
        self.load_tasks() # Load tasks and descriptions

        # Bind keyboard shortcuts
        self.bind("<space>", lambda event: self.toggle_start_pause())
        self.bind("<p>", lambda event: self.pause_timer())
        self.bind("<r>", lambda event: self.reset_timer())
        self.bind("<Delete>", lambda event: self.delete_task())

    # --- GUI Creation Methods ---
    def create_menu(self):
        """Creates a menu bar for settings."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configure Timers", command=self.open_settings_window)
        settings_menu.add_command(label="Set Sound File", command=self.set_sound_file)
        settings_menu.add_separator()
        settings_menu.add_command(label="Reset Settings", command=self.reset_settings)

    def create_session_counter(self):
        """Creates a panel to display the number of completed sessions."""
        self.session_frame = tk.Frame(self, bg=COLOR_SESSION_BG, relief='groove', borderwidth=2)
        self.session_frame.pack(pady=10, fill='x')
        self.session_label = tk.Label(self.session_frame, text=f"Sessions Completed: {self.sessions_completed}",
                                      font=("Comic Sans MS", 12, "bold"), bg=COLOR_SESSION_BG, fg=COLOR_FOREGROUND)
        self.session_label.pack(pady=10)

    def create_mode_buttons(self):
        """Creates the buttons for switching between timer modes."""
        mode_frame = tk.Frame(self, bg=COLOR_BACKGROUND)
        mode_frame.pack(pady=10)
        modes = [("Pomodoro", self.pomodoro_mins), ("Short Break", self.short_break_mins), ("Long Break", self.long_break_mins)]
        for mode, _ in modes:
            btn = tk.Button(mode_frame, text=mode, bg=COLOR_BUTTON, fg=COLOR_FOREGROUND,
                            activebackground=COLOR_ACCENT, relief="flat", borderwidth=0, font=("Comic Sans MS", 12),
                            command=lambda m=mode: self.switch_mode(m))
            btn.pack(side="left", padx=5)

    def create_timer_display(self):
        """Creates the label that shows the time countdown."""
        self.timer_label = tk.Label(self, text=self.format_time(self.time_left),
                                    font=("Comic Sans MS", 60, "bold"), bg=COLOR_BACKGROUND, fg=COLOR_FOREGROUND)
        self.timer_label.pack(pady=20)

    def create_control_buttons(self):
        """Creates the Start, Pause, and Reset buttons with enhanced colors."""
        control_frame = tk.Frame(self, bg=COLOR_BACKGROUND)
        control_frame.pack(pady=10)
        self.start_button = tk.Button(control_frame, text="Start", bg=COLOR_START, fg=COLOR_FOREGROUND,
                                      activebackground=COLOR_START_ACTIVE, relief="flat", borderwidth=0, font=("Comic Sans MS", 16, "bold"),
                                      command=self.start_timer)
        self.start_button.pack(side="left", padx=10)
        self.pause_button = tk.Button(control_frame, text="Pause", bg=COLOR_PAUSE, fg=COLOR_FOREGROUND,
                                      activebackground=COLOR_PAUSE_ACTIVE, relief="flat", borderwidth=0, font=("Comic Sans MS", 16),
                                      command=self.pause_timer, state="disabled")
        self.pause_button.pack(side="left", padx=10)
        self.reset_button = tk.Button(control_frame, text="Reset", bg=COLOR_RESET, fg=COLOR_FOREGROUND,
                                      activebackground=COLOR_RESET_ACTIVE, relief="flat", borderwidth=0, font=("Comic Sans MS", 16),
                                      command=self.reset_timer)
        self.reset_button.pack(side="left", padx=10)

    def create_task_manager(self):
        """Creates the GUI components for managing tasks."""
        task_frame = tk.Frame(self, bg=COLOR_BACKGROUND)
        task_frame.pack(pady=20, fill="x", expand=True)

        task_label = tk.Label(task_frame, text="Tasks", font=("Comic Sans MS", 14, "bold"), bg=COLOR_BACKGROUND, fg=COLOR_FOREGROUND)
        task_label.pack()

        # Frame for task entry and priority
        task_input_frame = tk.Frame(task_frame, bg=COLOR_BACKGROUND)
        task_input_frame.pack(fill="x", pady=5)

        self.priority_var = tk.StringVar(value="Medium")
        priority_label = tk.Label(task_input_frame, text="Priority:", bg=COLOR_BACKGROUND, fg=COLOR_FOREGROUND, font=("Comic Sans MS", 10))
        priority_label.pack(side="left")
        priority_menu = tk.OptionMenu(task_input_frame, self.priority_var, "High", "Medium", "Low")
        priority_menu.config(bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, relief="flat", font=("Comic Sans MS", 10))
        priority_menu.pack(side="left", padx=5)

        self.task_entry = tk.Entry(task_input_frame, bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, insertbackground=COLOR_FOREGROUND,
                                   relief="flat", font=("Comic Sans MS", 12))
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(5,0))
        self.task_entry.insert(0, "Enter task here...")
        def on_entry_focus_in(event):
            if self.task_entry.get() == "Enter task here...":
                self.task_entry.delete(0, tk.END)
                self.task_entry.config(fg=COLOR_FOREGROUND)
        def on_entry_focus_out(event):
            if not self.task_entry.get():
                self.task_entry.insert(0, "Enter task here...")
                self.task_entry.config(fg=COLOR_FOREGROUND)
        self.task_entry.bind("<FocusIn>", on_entry_focus_in)
        self.task_entry.bind("<FocusOut>", on_entry_focus_out)
        self.task_entry.bind("<Control-Return>", self.add_task) # Ctrl+Enter to add task

        task_button_frame = tk.Frame(task_frame, bg=COLOR_BACKGROUND)
        task_button_frame.pack(pady=5, fill="x")
        add_task_btn = tk.Button(task_button_frame, text="Add Task (Ctrl+Enter)", bg=COLOR_BUTTON, fg=COLOR_FOREGROUND,
                                 command=self.add_task, relief="flat", font=("Comic Sans MS", 10))
        add_task_btn.pack(side="left", padx=5, pady=5)
        delete_task_btn = tk.Button(task_button_frame, text="Delete Selected (Del)", bg=COLOR_BUTTON, fg=COLOR_FOREGROUND,
                                    command=self.delete_task, relief="flat", font=("Comic Sans MS", 10))
        delete_task_btn.pack(side="left", padx=5, pady=5)

        listbox_frame = tk.Frame(task_frame, bg=COLOR_BACKGROUND)
        listbox_frame.pack(fill="both", expand=True)

        self.task_listbox = tk.Listbox(listbox_frame, bg=COLOR_BUTTON, fg=COLOR_FOREGROUND, selectbackground=COLOR_ACCENT,
                                       relief="flat", borderwidth=0, font=("Comic Sans MS", 12), height=10, selectmode=tk.SINGLE)
        self.task_listbox.pack(side="left", fill="both", expand=True)
        # --- Bind double-click event for description ---
        self.task_listbox.bind("<Double-Button-1>", self.edit_task_description)

        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=self.task_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.task_listbox.config(yscrollcommand=scrollbar.set)

    # --- Timer Logic Methods ---
    def start_timer(self):
        """Starts or resumes the timer if it's not already running."""
        if not self.is_running:
            self.is_running = True
            self.start_button.config(text="Start", state="disabled")
            self.pause_button.config(state="normal", text="Pause")
            self.countdown()

    def pause_timer(self):
        """Pauses the timer if running."""
        if self.is_running:
            self.is_running = False
            if self.timer_id:
                self.after_cancel(self.timer_id)
                self.timer_id = None
            self.start_button.config(text="Resume", state="normal")
            self.pause_button.config(state="disabled")

    def reset_timer(self):
        """Resets the timer to the current mode's default time."""
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.is_running = False
        self.switch_mode(self.current_mode)
        self.start_button.config(text="Start", state="normal")
        self.pause_button.config(text="Pause", state="disabled")

    def toggle_start_pause(self):
        """Toggles between start and pause based on the current state."""
        if self.is_running:
            self.pause_timer()
        else:
            self.start_timer()

    def countdown(self):
        """
        The main loop for the timer. Updates the display every second.
        """
        if self.is_running and self.time_left > 0:
            self.time_left -= 1
            self.update_timer_display()
            self.timer_id = self.after(1000, self.countdown)
        elif self.time_left <= 0:
            self.is_running = False
            self.handle_timer_completion()

    def switch_mode(self, mode):
        """
        Switches the timer to a new mode (e.g., 'Pomodoro', 'Short Break').
        """
        self.current_mode = mode
        if mode == "Pomodoro":
            self.time_left = self.pomodoro_mins * 60
        elif mode == "Short Break":
            self.time_left = self.short_break_mins * 60
        elif mode == "Long Break":
            self.time_left = self.long_break_mins * 60

        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.is_running = False
        self.update_timer_display()
        self.start_button.config(text="Start", state="normal")
        self.pause_button.config(text="Pause", state="disabled")

    def handle_timer_completion(self):
        """
        Handles what happens when the timer reaches zero.
        """
        self.play_sound()
        messagebox.showinfo("Timer Finished!", f"{self.current_mode} session is complete!")

        if self.current_mode == "Pomodoro":
            self.sessions_completed += 1
            self.session_label.config(text=f"Sessions Completed: {self.sessions_completed}")

            if self.sessions_completed % self.long_break_interval == 0:
                self.switch_mode("Long Break")
            else:
                self.switch_mode("Short Break")
        else:
            self.switch_mode("Pomodoro")

        self.reset_timer()

    def play_sound(self):
        """Plays a sound file using pygame if available."""
        def play_sound_thread():
            try:
                if SOUND_MODULE == 'pygame' and self.sound_file_path and os.path.isfile(self.sound_file_path):
                    pygame.mixer.music.load(self.sound_file_path)
                    pygame.mixer.music.play()
                else:
                    self.bell()
                    print("Playing system bell as fallback.")
            except Exception as e:
                print(f"Error playing sound: {e}")
                self.bell()
                print("Playing system bell due to playback error.")

        if self.sound_file_path or SOUND_MODULE is None:
            sound_thread = threading.Thread(target=play_sound_thread)
            sound_thread.daemon = True
            sound_thread.start()
        else:
            self.bell()
            print("Playing system bell (no sound file selected).")

    # --- Utility and Task Management Methods ---
    def format_time(self, seconds):
        """
        Formats the given time in seconds into a MM:SS string.
        """
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def update_timer_display(self):
        """Updates the timer label with the current time."""
        self.timer_label.config(text=self.format_time(self.time_left))

    def get_priority_color(self, priority):
        """Returns the color associated with a task priority."""
        if priority == "High":
            return COLOR_HIGH_PRIORITY
        elif priority == "Medium":
            return COLOR_MEDIUM_PRIORITY
        elif priority == "Low":
            return COLOR_LOW_PRIORITY
        return COLOR_FOREGROUND

    def get_priority_from_text(self, text):
        """Extracts priority letter from task text (e.g., '[H] Task' -> 'H')."""
        if text.startswith('[') and text[2:4] == '] ':
            return text[1]
        return 'M' # Default to Medium if not found

    def sort_tasks(self):
        """Sorts tasks in the listbox by priority (High > Medium > Low)."""
        # Get all tasks with their colors
        tasks_with_colors = []
        for i in range(self.task_listbox.size()):
            task_text = self.task_listbox.get(i)
            task_color = self.task_listbox.itemcget(i, 'fg')
            tasks_with_colors.append((task_text, task_color))

        # Sort using a custom key based on priority
        def priority_key(task_tuple):
            task_text, _ = task_tuple
            priority_letter = self.get_priority_from_text(task_text)
            # Map priority letter to a sort value (H=0, M=1, L=2)
            priority_map = {'H': 0, 'M': 1, 'L': 2}
            return priority_map.get(priority_letter, 1) # Default to Medium (1) if unknown

        tasks_with_colors.sort(key=priority_key)

        # Clear the listbox and re-insert sorted tasks
        self.task_listbox.delete(0, tk.END)
        for task_text, task_color in tasks_with_colors:
            self.task_listbox.insert(tk.END, task_text)
            self.task_listbox.itemconfig(tk.END, {'fg': task_color})

    def add_task(self, event=None):
        """
        Adds a new task from the entry field to the task list with priority.
        Implements auto-sorting by priority after adding.
        """
        task_text = self.task_entry.get().strip()
        priority = self.priority_var.get()
        if task_text:
            display_text = f"[{priority[0]}] {task_text}"
            self.task_listbox.insert(tk.END, display_text)
            self.task_listbox.itemconfig(tk.END, {'fg': self.get_priority_color(priority)})
            self.task_entry.delete(0, tk.END)
            self.priority_var.set("Medium")
            self.sort_tasks() # Auto-sort after adding
            self.save_tasks() # Save tasks including descriptions

    def delete_task(self):
        """Deletes the currently selected task from the listbox."""
        try:
            selected_index = self.task_listbox.curselection()[0]
            # Get the task text to remove its description
            task_text = self.task_listbox.get(selected_index)
            # Remove description if it exists
            if hasattr(self, 'task_descriptions'):
                 self.task_descriptions.pop(task_text, None)
            self.task_listbox.delete(selected_index)
            self.save_tasks()
        except IndexError:
            messagebox.showwarning("No Selection", "Please select a task to delete.")

    def edit_task_description(self, event):
        """Opens a dialog to add/edit a description for the double-clicked task."""
        try:
            selected_index = self.task_listbox.curselection()[0]
            task_text = self.task_listbox.get(selected_index)
            # Ensure task_descriptions dict exists
            if not hasattr(self, 'task_descriptions'):
                self.task_descriptions = {}
            # Get existing description or empty string
            current_desc = self.task_descriptions.get(task_text, "")
            # Open dialog
            new_desc = simpledialog.askstring("Task Description", f"Description for:\n{task_text}", initialvalue=current_desc, parent=self)
            # Update description if user provided input (OK) or explicitly cleared it (empty string)
            if new_desc is not None: # Checks for both OK with text and OK with empty input
                self.task_descriptions[task_text] = new_desc
                self.save_tasks() # Save updated descriptions
                # Optional: Visual feedback (e.g., change background slightly)
                # self.task_listbox.itemconfig(selected_index, {'bg': '#555555'})
        except IndexError:
            # No task selected, ignore double-click on empty space
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit description: {e}")

    def save_tasks(self):
        """Save tasks and descriptions to file."""
        attempts = 0
        while attempts < 3:
            try:
                with open(TASKS_FILE, 'w') as f:
                    tasks_to_save = []
                    # Save tasks with color
                    for i in range(self.task_listbox.size()):
                        task_text = self.task_listbox.get(i)
                        task_color = self.task_listbox.itemcget(i, 'fg')
                        tasks_to_save.append({'text': task_text, 'color': task_color})

                    # Save descriptions (ensure task_descriptions exists)
                    descriptions_to_save = getattr(self, 'task_descriptions', {})

                    # Combine into one dictionary to save
                    data_to_save = {
                        'tasks': tasks_to_save,
                        'descriptions': descriptions_to_save
                    }
                    json.dump(data_to_save, f, indent=4) # Use indent for readability
                break
            except Exception as e:
                print(f"Error saving tasks/descriptions (attempt {attempts + 1}): {e}")
                attempts += 1

    def load_tasks(self):
        """Load tasks and descriptions from file."""
        attempts = 0
        while attempts < 3:
            try:
                if os.path.exists(TASKS_FILE):
                    with open(TASKS_FILE, 'r') as f:
                        data = json.load(f)
                        tasks_data = data.get('tasks', [])
                        # Load descriptions into instance variable
                        self.task_descriptions = data.get('descriptions', {}) # Initialize descriptions dict

                        # Load tasks into listbox
                        for task_info in tasks_data:
                            task_text = task_info.get('text', '')
                            task_color = task_info.get('color', COLOR_FOREGROUND)
                            if isinstance(task_text, str) and task_text.strip():
                                self.task_listbox.insert(tk.END, task_text)
                                self.task_listbox.itemconfig(tk.END, {'fg': task_color})
                        # Sort tasks after loading
                        self.sort_tasks()
                break
            except Exception as e:
                 print(f"Error loading tasks/descriptions (attempt {attempts + 1}): {e}")
                 attempts += 1

    # --- Settings Management Methods ---
    def open_settings_window(self):
        """Opens the dedicated settings window."""
        settings_window = SettingsWindow(
            self,
            self.pomodoro_mins,
            self.short_break_mins,
            self.long_break_mins,
            self.long_break_interval,
            self.sound_file_path
        )
        self.wait_window(settings_window)

        if settings_window.result:
            self.pomodoro_mins = settings_window.result["pomodoro_mins"]
            self.short_break_mins = settings_window.result["short_break_mins"]
            self.long_break_mins = settings_window.result["long_break_mins"]
            self.long_break_interval = settings_window.result["long_break_interval"]
            self.sound_file_path = settings_window.result["sound_file_path"]

            self.save_settings()
            self.update_mode_buttons()
            if not self.is_running:
                self.switch_mode(self.current_mode)
            messagebox.showinfo("Settings Updated", "Timer settings updated successfully!")

    def update_mode_buttons(self):
        """Updates the mode buttons to reflect new timer durations."""
        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                children = widget.winfo_children()
                if len(children) > 0 and isinstance(children[0], tk.Button) and children[0].cget('text') in ["Pomodoro", "Short Break", "Long Break"]:
                     widget.destroy()
                     self.create_mode_buttons()
                     break

    def set_sound_file(self):
        """Allows the user to select a sound file."""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(title="Select Sound File", filetypes=[("Audio Files", "*.wav *.mp3"), ("WAV Files", "*.wav"), ("MP3 Files", "*.mp3"), ("All Files", "*.*")])
        if file_path:
            self.sound_file_path = file_path
            self.save_settings()
            messagebox.showinfo("Sound Set", f"Sound file set to: {os.path.basename(file_path)}")

    def reset_settings(self):
        """Resets timer settings to default values."""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to default?"):
            self.pomodoro_mins = DEFAULT_POMODORO_MINS
            self.short_break_mins = DEFAULT_SHORT_BREAK_MINS
            self.long_break_mins = DEFAULT_LONG_BREAK_MINS
            self.long_break_interval = DEFAULT_LONG_BREAK_INTERVAL
            self.sound_file_path = ""
            self.save_settings()
            self.update_mode_buttons()
            if not self.is_running:
                self.switch_mode(self.current_mode)
            messagebox.showinfo("Settings Reset", "Settings have been reset to default values.")

    def save_settings(self):
        """Saves application settings to a JSON file."""
        settings_to_save = {
            "pomodoro_mins": self.pomodoro_mins,
            "short_break_mins": self.short_break_mins,
            "long_break_mins": self.long_break_mins,
            "long_break_interval": self.long_break_interval,
            "sound_file_path": self.sound_file_path
        }
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings_to_save, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def load_settings(self):
        """Loads application settings from a JSON file."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
                messagebox.showwarning("Settings Load Error", "Could not load settings file. Using defaults.")
        return {}

# --- Main Execution Block ---
# Import threading here for sound playback
import threading

if __name__ == "__main__":
    app = PomodoroTimer()
    app.mainloop()