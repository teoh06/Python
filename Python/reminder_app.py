# Reminder App - Never Miss Important Tasks
# Set audio reminders with recurring options and custom sounds

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import sqlite3
import os

# Sound handling - try to import pygame for MP3 support
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

# Windows sound handling for WAV files
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# Modified: Define DATA_DIR and construct DB_FILE path
DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "reminders.db")

# Colors
COLORS = {
    "bg": "#f8f9fa",
    "fg": "#212529",
    "accent": "#007bff",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "light": "#f8f9fa",
    "dark": "#343a40",
    "border": "#dee2e6",
    "card_bg": "#ffffff",
    "hover": "#e9ecef"
}

# =========================
# Database helpers
# =========================
def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create reminders table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        message TEXT,
        due_time TEXT NOT NULL,
        recurrence TEXT,
        enabled INTEGER DEFAULT 1
    )''')
    
    # Check and add new columns if they don't exist
    c.execute("PRAGMA table_info(reminders)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'created_at' not in columns:
        c.execute("ALTER TABLE reminders ADD COLUMN created_at TEXT")
    
    if 'last_modified' not in columns:
        c.execute("ALTER TABLE reminders ADD COLUMN last_modified TEXT")
    
    # Set default values for existing records
    c.execute("UPDATE reminders SET created_at = datetime('now'), last_modified = datetime('now') WHERE created_at IS NULL OR last_modified IS NULL")
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    conn.commit()
    conn.close()

def execute_db_query(query, params=(), fetch=False, fetchone=False):
    """Execute a database query with consistent connection handling"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    
    if fetch:
        result = c.fetchall()
    elif fetchone:
        result = c.fetchone()
    else:
        result = None
        
    conn.commit()
    conn.close()
    return result

def get_reminders():
    return execute_db_query("SELECT * FROM reminders ORDER BY due_time", fetch=True)

def add_reminder(title, message, due_time, recurrence=None):
    execute_db_query("INSERT INTO reminders (title, message, due_time, recurrence) VALUES (?, ?, ?, ?)",
                    (title, message, due_time, recurrence))

def update_reminder(reminder_id, title, message, due_time, recurrence=None):
    execute_db_query("UPDATE reminders SET title=?, message=?, due_time=?, recurrence=?, last_modified=datetime('now') WHERE id=?",
                    (title, message, due_time, recurrence, reminder_id))

def delete_reminder(reminder_id):
    execute_db_query("DELETE FROM reminders WHERE id=?", (reminder_id,))

def toggle_reminder(reminder_id, enabled):
    execute_db_query("UPDATE reminders SET enabled=?, last_modified=datetime('now') WHERE id=?", 
                    (enabled, reminder_id))

def get_setting(key, default=None):
    result = execute_db_query("SELECT value FROM settings WHERE key=?", (key,), fetchone=True)
    return result[0] if result else default

def set_setting(key, value):
    execute_db_query("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

def clear_setting(key):
    execute_db_query("DELETE FROM settings WHERE key=?", (key,))

# =========================
# App
# =========================
class ReminderApp:
    def __init__(self, master):
        self.master = master
        self.root = tk.Toplevel(master)
        self.root.title("Reminder App")
        self.root.geometry("1000x700")
        self.root.configure(bg=COLORS["bg"])
        
        # Initialize pygame mixer if available
        self.pygame_initialized = False
        if HAS_PYGAME:
            try:
                pygame.mixer.init()
                self.pygame_initialized = True
            except pygame.error:
                print("Pygame mixer could not be initialized.")
        
        # Track which reminders have been notified to prevent looping
        self.notified_reminders = set()
        # Track active notification windows
        self.active_notifications = []
        
        init_db()
        self.create_widgets()
        self.load_reminders()
        self.check_reminders()
        
        # Schedule periodic checking
        self.root.after(1000, self.periodic_check)

    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg=COLORS["bg"], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Frame(main_frame, bg=COLORS["bg"])
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header, text="📅 Reminder App", font=("Arial", 24, "bold"), 
                bg=COLORS["bg"], fg=COLORS["dark"]).pack(side=tk.LEFT)
        
        # Statistics
        stats_frame = tk.Frame(header, bg=COLORS["bg"])
        stats_frame.pack(side=tk.RIGHT)
        
        self.total_label = tk.Label(stats_frame, text="Total: 0", bg=COLORS["bg"], fg=COLORS["dark"])
        self.total_label.pack(side=tk.LEFT, padx=10)
        
        self.active_label = tk.Label(stats_frame, text="Active: 0", bg=COLORS["bg"], fg=COLORS["success"])
        self.active_label.pack(side=tk.LEFT, padx=10)
        
        self.inactive_label = tk.Label(stats_frame, text="Inactive: 0", bg=COLORS["bg"], fg=COLORS["danger"])
        self.inactive_label.pack(side=tk.LEFT, padx=10)
        
        # Add reminder button
        add_btn = tk.Button(header, text="+ Add Reminder", command=self.add_reminder_window,
                           bg=COLORS["accent"], fg="white", font=("Arial", 10, "bold"),
                           padx=15, pady=5, relief=tk.FLAT)
        add_btn.pack(side=tk.RIGHT)
        add_btn.bind("<Enter>", lambda e: add_btn.config(bg="#0056b3"))
        add_btn.bind("<Leave>", lambda e: add_btn.config(bg=COLORS["accent"]))
        
        # Filter frame
        filter_frame = tk.Frame(main_frame, bg=COLORS["bg"], pady=10)
        filter_frame.pack(fill=tk.X)
        
        tk.Label(filter_frame, text="Filter:", bg=COLORS["bg"], font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.filter_var = tk.StringVar(value="all")
        ttk.Radiobutton(filter_frame, text="All", variable=self.filter_var, value="all", 
                       command=self.load_reminders).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Active Only", variable=self.filter_var, value="active", 
                       command=self.load_reminders).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Inactive Only", variable=self.filter_var, value="inactive", 
                       command=self.load_reminders).pack(side=tk.LEFT, padx=5)
        
        # Reminders list
        list_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview with scrollbar
        tree_frame = tk.Frame(list_frame, bg=COLORS["bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("id", "title", "message", "due_time", "recurrence", "status", "created", "modified")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("message", text="Message")
        self.tree.heading("due_time", text="Due Time")
        self.tree.heading("recurrence", text="Recurrence")
        self.tree.heading("status", text="Status")
        self.tree.heading("created", text="Created")
        self.tree.heading("modified", text="Last Modified")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("title", width=150)
        self.tree.column("message", width=200)
        self.tree.column("due_time", width=120)
        self.tree.column("recurrence", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=80, anchor=tk.CENTER)
        self.tree.column("created", width=120)
        self.tree.column("modified", width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.tree.bind("<Double-1>", self.edit_reminder)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click
        self.tree.bind("<Motion>", self.on_tree_hover)
        self.tree.bind("<Leave>", self.on_tree_leave)  # Reset cursor when leaving tree
        
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.add_reminder_window())
        self.root.bind("<Control-e>", lambda e: self.edit_selected())
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<space>", lambda e: self.toggle_selected())
        self.root.bind("<Control-a>", lambda e: self.enable_all())
        self.root.bind("<Control-d>", lambda e: self.disable_all())
        self.root.bind("<F5>", lambda e: self.load_reminders())
        self.root.bind("<F1>", lambda e: self.show_help())
        self.root.bind("<Escape>", lambda e: self.tree.selection_remove(*self.tree.selection()))
        
        # Focus the tree so keyboard shortcuts work
        self.tree.focus_set()
        
        # Create context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📝 Edit Reminder", command=self.edit_selected)
        self.context_menu.add_separator()
        
        # Status submenu
        self.status_menu = tk.Menu(self.context_menu, tearoff=0)
        self.status_menu.add_command(label="✅ Set Active", command=lambda: self.quick_change_status(True))
        self.status_menu.add_command(label="❌ Set Disabled", command=lambda: self.quick_change_status(False))
        self.status_menu.add_command(label="🔄 Toggle Status", command=self.toggle_selected)
        self.context_menu.add_cascade(label="📊 Status", menu=self.status_menu)
        
        # Recurrence submenu
        self.recurrence_menu = tk.Menu(self.context_menu, tearoff=0)
        self.recurrence_menu.add_command(label="🚫 None", command=lambda: self.quick_change_recurrence(None))
        self.recurrence_menu.add_command(label="📅 Daily", command=lambda: self.quick_change_recurrence("Daily"))
        self.recurrence_menu.add_command(label="📅 Weekly", command=lambda: self.quick_change_recurrence("Weekly"))
        self.recurrence_menu.add_command(label="📅 Monthly", command=lambda: self.quick_change_recurrence("Monthly"))
        self.context_menu.add_cascade(label="🔁 Recurrence", menu=self.recurrence_menu)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Delete Reminder", command=self.delete_selected)
        
        # Action buttons frame
        action_frame = tk.Frame(list_frame, bg=COLORS["bg"], pady=10)
        action_frame.pack(fill=tk.X)
        
        edit_btn = tk.Button(action_frame, text="Edit", command=self.edit_selected,
                           bg=COLORS["warning"], fg=COLORS["dark"], font=("Arial", 10),
                           padx=15, pady=5)
        edit_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(action_frame, text="Delete", command=self.delete_selected,
                             bg=COLORS["danger"], fg="white", font=("Arial", 10),
                             padx=15, pady=5)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        toggle_btn = tk.Button(action_frame, text="Toggle Status", command=self.toggle_selected,
                             bg=COLORS["success"], fg="white", font=("Arial", 10),
                             padx=15, pady=5)
        toggle_btn.pack(side=tk.LEFT, padx=5)
        
        enable_btn = tk.Button(action_frame, text="Enable All", command=self.enable_all,
                             bg="#17a2b8", fg="white", font=("Arial", 10),
                             padx=15, pady=5)
        enable_btn.pack(side=tk.LEFT, padx=5)
        
        disable_btn = tk.Button(action_frame, text="Disable All", command=self.disable_all,
                               bg="#6c757d", fg="white", font=("Arial", 10),
                               padx=15, pady=5)
        disable_btn.pack(side=tk.LEFT, padx=5)
        
        # Help and Settings buttons
        help_btn = tk.Button(action_frame, text="Help (F1)", command=self.show_help,
                           bg="#6f42c1", fg="white", font=("Arial", 10),
                           padx=15, pady=5)
        help_btn.pack(side=tk.RIGHT, padx=5)
        
        settings_btn = tk.Button(action_frame, text="Sound Settings", command=self.sound_settings,
                               bg=COLORS["accent"], fg="white", font=("Arial", 10),
                               padx=15, pady=5)
        settings_btn.pack(side=tk.RIGHT, padx=5)

    def load_reminders(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        reminders = get_reminders()
        filter_type = self.filter_var.get()
        
        total_count = 0
        active_count = 0
        inactive_count = 0
        
        for reminder in reminders:
            status = "Active" if reminder[5] else "Disabled"
            total_count += 1
            if reminder[5]:
                active_count += 1
            else:
                inactive_count += 1
            
            # Apply filter
            if filter_type == "active" and not reminder[5]:
                continue
            elif filter_type == "inactive" and reminder[5]:
                continue
            
            # Format dates
            created_date = reminder[6][:16] if reminder[6] else "N/A"
            modified_date = reminder[7][:16] if reminder[7] else "N/A"
            
            self.tree.insert("", tk.END, values=(
                reminder[0], reminder[1], reminder[2] or "",
                reminder[3], reminder[4] or "None", status,
                created_date, modified_date
            ))
        
        # Update statistics
        self.total_label.config(text=f"Total: {total_count}")
        self.active_label.config(text=f"Active: {active_count}")
        self.inactive_label.config(text=f"Inactive: {inactive_count}")

    def add_reminder_window(self):
        window = tk.Toplevel(self.root)
        window.title("Add Reminder")
        window.geometry("400x400")
        window.configure(bg=COLORS["bg"])
        
        tk.Label(window, text="Add New Reminder", font=("Arial", 16, "bold"),
                bg=COLORS["bg"], fg=COLORS["dark"]).pack(pady=10)
        
        # Title
        tk.Label(window, text="Title:", bg=COLORS["bg"]).pack(anchor=tk.W, padx=20)
        title_entry = tk.Entry(window, font=("Arial", 11), width=40)
        title_entry.pack(padx=20, pady=(0, 10))
        
        # Message
        tk.Label(window, text="Message:", bg=COLORS["bg"]).pack(anchor=tk.W, padx=20)
        message_entry = tk.Entry(window, font=("Arial", 11), width=40)
        message_entry.pack(padx=20, pady=(0, 10))
        
        # Due time
        tk.Label(window, text="Due Time (YYYY-MM-DD HH:MM):", bg=COLORS["bg"]).pack(anchor=tk.W, padx=20)
        due_entry = tk.Entry(window, font=("Arial", 11), width=40)
        due_entry.pack(padx=20, pady=(0, 10))
        due_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        # Recurrence
        tk.Label(window, text="Recurrence:", bg=COLORS["bg"]).pack(anchor=tk.W, padx=20)
        recur_var = tk.StringVar(value="None")
        recur_menu = ttk.Combobox(window, textvariable=recur_var, width=37,
                                 values=["None", "Daily", "Weekly", "Monthly"])
        recur_menu.pack(padx=20, pady=(0, 20))
        
        # Initial status
        status_frame = tk.Frame(window, bg=COLORS["bg"])
        status_frame.pack(padx=20, pady=(0, 10), fill=tk.X)
        tk.Label(status_frame, text="Initial Status:", bg=COLORS["bg"]).pack(side=tk.LEFT)
        status_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(status_frame, text="Active", variable=status_var).pack(side=tk.LEFT, padx=10)
        
        def submit():
            title = title_entry.get().strip()
            message = message_entry.get().strip()
            due_time = due_entry.get().strip()
            recurrence = recur_var.get() if recur_var.get() != "None" else None
            
            if not title or not due_time:
                messagebox.showerror("Error", "Title and Due Time are required!")
                return
            
            try:
                datetime.strptime(due_time, "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD HH:MM")
                return
            
            add_reminder(title, message, due_time, recurrence)
            # Set initial status
            reminder_id = self._get_last_inserted_id()
            if reminder_id:
                toggle_reminder(reminder_id, status_var.get())
            
            self.load_reminders()
            window.destroy()
            messagebox.showinfo("Success", "Reminder added successfully!")
        
        tk.Button(window, text="Add Reminder", command=submit,
                 bg=COLORS["success"], fg="white", font=("Arial", 10, "bold"),
                 padx=20, pady=5).pack(pady=10)

    def _get_last_inserted_id(self):
        """Get the ID of the last inserted reminder"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT last_insert_rowid()")
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def edit_reminder(self, event):
        self.edit_selected()

    def edit_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a reminder to edit!")
            return
        
        item = self.tree.item(selection[0])
        reminder_id = item['values'][0]
        
        reminders = get_reminders()
        reminder = next((r for r in reminders if r[0] == reminder_id), None)
        
        if not reminder:
            return
        
        window = tk.Toplevel(self.root)
        window.title("Edit Reminder")
        window.geometry("400x300")
        window.configure(bg=COLORS["bg"])
        
        tk.Label(window, text="Edit Reminder", font=("Arial", 16, "bold"),
                bg=COLORS["bg"], fg=COLORS["dark"]).pack(pady=10)
        
        # Title
        tk.Label(window, text="Title:", bg=COLORS["bg"]).pack(anchor=tk.W, padx=20)
        title_entry = tk.Entry(window, font=("Arial", 11), width=40)
        title_entry.pack(padx=20, pady=(0, 10))
        title_entry.insert(0, reminder[1])
        
        # Message
        tk.Label(window, text="Message:", bg=COLORS["bg"]).pack(anchor=tk.W, padx=20)
        message_entry = tk.Entry(window, font=("Arial", 11), width=40)
        message_entry.pack(padx=20, pady=(0, 10))
        message_entry.insert(0, reminder[2] or "")
        
        # Due time
        tk.Label(window, text="Due Time (YYYY-MM-DD HH:MM):", bg=COLORS["bg"]).pack(anchor=tk.W, padx=20)
        due_entry = tk.Entry(window, font=("Arial", 11), width=40)
        due_entry.pack(padx=20, pady=(0, 10))
        due_entry.insert(0, reminder[3])
        
        # Recurrence
        tk.Label(window, text="Recurrence:", bg=COLORS["bg"]).pack(anchor=tk.W, padx=20)
        recur_var = tk.StringVar(value=reminder[4] or "None")
        recur_menu = ttk.Combobox(window, textvariable=recur_var, width=37,
                                 values=["None", "Daily", "Weekly", "Monthly"])
        recur_menu.pack(padx=20, pady=(0, 10))
        
        # Status checkbox
        status_frame = tk.Frame(window, bg=COLORS["bg"])
        status_frame.pack(padx=20, pady=(0, 10), fill=tk.X)
        tk.Label(status_frame, text="Status:", bg=COLORS["bg"]).pack(side=tk.LEFT)
        status_var = tk.BooleanVar(value=bool(reminder[5]))
        ttk.Checkbutton(status_frame, text="Active", variable=status_var).pack(side=tk.LEFT, padx=10)
        
        def submit():
            title = title_entry.get().strip()
            message = message_entry.get().strip()
            due_time = due_entry.get().strip()
            recurrence = recur_var.get() if recur_var.get() != "None" else None
            
            if not title or not due_time:
                messagebox.showerror("Error", "Title and Due Time are required!")
                return
            
            try:
                datetime.strptime(due_time, "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD HH:MM")
                return
            
            update_reminder(reminder_id, title, message, due_time, recurrence)
            # Update status if changed
            if status_var.get() != bool(reminder[5]):
                toggle_reminder(reminder_id, status_var.get())
            
            self.load_reminders()
            window.destroy()
            messagebox.showinfo("Success", "Reminder updated successfully!")
        
        tk.Button(window, text="Update Reminder", command=submit,
                 bg=COLORS["success"], fg="white", font=("Arial", 10, "bold"),
                 padx=20, pady=5).pack(pady=10)

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a reminder to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this reminder?"):
            item = self.tree.item(selection[0])
            reminder_id = item['values'][0]
            delete_reminder(reminder_id)
            self.load_reminders()
            messagebox.showinfo("Success", "Reminder deleted successfully!")

    def toggle_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a reminder to toggle!")
            return
        
        items = self.tree.selection()
        for item in items:
            item_data = self.tree.item(item)
            reminder_id = item_data['values'][0]
            current_status = item_data['values'][5] == "Active"
            
            toggle_reminder(reminder_id, not current_status)
        
        self.load_reminders()
        if len(items) == 1:
            status = "disabled" if current_status else "enabled"
            messagebox.showinfo("Success", f"Reminder {status} successfully!")
        else:
            messagebox.showinfo("Success", f"{len(items)} reminders status updated!")

    def enable_all(self):
        reminders = get_reminders()
        disabled_reminders = [r[0] for r in reminders if not r[5]]
        
        if not disabled_reminders:
            messagebox.showinfo("Info", "All reminders are already enabled!")
            return
        
        if messagebox.askyesno("Confirm", f"Enable all {len(disabled_reminders)} disabled reminders?"):
            for reminder_id in disabled_reminders:
                toggle_reminder(reminder_id, True)
            self.load_reminders()
            messagebox.showinfo("Success", f"Enabled {len(disabled_reminders)} reminders!")

    def disable_all(self):
        reminders = get_reminders()
        active_reminders = [r[0] for r in reminders if r[5]]
        
        if not active_reminders:
            messagebox.showinfo("Info", "All reminders are already disabled!")
            return
        
        if messagebox.askyesno("Confirm", f"Disable all {len(active_reminders)} active reminders?"):
            for reminder_id in active_reminders:
                toggle_reminder(reminder_id, False)
            self.load_reminders()
            messagebox.showinfo("Success", f"Disabled {len(active_reminders)} reminders!")
    
    def on_tree_click(self, event):
        """Handle single click on tree items for quick actions"""
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
        
        column = self.tree.identify('column', event.x, event.y)
        
        # Quick toggle status on status column click
        if column == "#6":  # Status column
            self.tree.selection_set(item)
            self.toggle_selected()
            return "break"  # Prevent normal selection
        
        # Quick cycle recurrence on recurrence column click
        elif column == "#5":  # Recurrence column
            self.tree.selection_set(item)
            current_recurrence = self.tree.item(item)['values'][4]
            next_recurrence = self.cycle_recurrence(current_recurrence)
            reminder_id = self.tree.item(item)['values'][0]
            
            # Get current reminder data
            reminders = get_reminders()
            reminder = next((r for r in reminders if r[0] == reminder_id), None)
            if reminder:
                update_reminder(reminder_id, reminder[1], reminder[2], reminder[3], next_recurrence)
                self.load_reminders()
            return "break"
    
    def on_tree_hover(self, event):
        """Show cursor changes on hoverable columns"""
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            self.tree.configure(cursor="")
            return
        
        column = self.tree.identify('column', event.x, event.y)
        
        # Change cursor for clickable columns
        if column in ["#5", "#6"]:  # Recurrence and Status columns
            self.tree.configure(cursor="hand2")
        else:
            self.tree.configure(cursor="")
    
    def show_context_menu(self, event):
        """Show right-click context menu"""
        item = self.tree.identify('item', event.x, event.y)
        if item:
            self.tree.selection_set(item)
            # Get reminder data for context menu updates
            reminder_id = self.tree.item(item)['values'][0]
            current_status = self.tree.item(item)['values'][5]
            current_recurrence = self.tree.item(item)['values'][4]
            
            # Update context menu labels based on current values
            self.update_context_menu_labels(current_status, current_recurrence)
            
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def update_context_menu_labels(self, current_status, current_recurrence):
        """Update context menu labels to show current state"""
        # Update status menu labels
        active_label = "✅ Set Active" if current_status != "Active" else "✅ Set Active (current)"
        disabled_label = "❌ Set Disabled" if current_status != "Disabled" else "❌ Set Disabled (current)"
        toggle_label = f"🔄 Toggle Status (currently {current_status})"
        
        self.status_menu.entryconfig(0, label=active_label)
        self.status_menu.entryconfig(1, label=disabled_label)
        self.status_menu.entryconfig(2, label=toggle_label)
        
        # Update recurrence menu labels
        recurrence_options = {
            "None": "🚫 None",
            "Daily": "📅 Daily", 
            "Weekly": "📅 Weekly",
            "Monthly": "📅 Monthly"
        }
        
        for i, (recur_type, label) in enumerate(recurrence_options.items()):
            if current_recurrence == recur_type:
                self.recurrence_menu.entryconfig(i, label=f"{label} (current)")
            else:
                self.recurrence_menu.entryconfig(i, label=label)
    
    def quick_change_status(self, new_status):
        """Quickly change status without opening edit dialog"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a reminder!")
            return
        
        item = self.tree.item(selection[0])
        reminder_id = item['values'][0]
        current_status = item['values'][5] == "Active"
        
        if current_status == new_status:
            status_text = "active" if new_status else "disabled"
            messagebox.showinfo("Info", f"Reminder is already {status_text}!")
            return
        
        toggle_reminder(reminder_id, new_status)
        self.load_reminders()
        
        status_text = "enabled" if new_status else "disabled"
        messagebox.showinfo("Success", f"Reminder {status_text} successfully!", master=self.root)
    
    def quick_change_recurrence(self, new_recurrence):
        """Quickly change recurrence without opening edit dialog"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a reminder!")
            return
        
        item = self.tree.item(selection[0])
        reminder_id = item['values'][0]
        current_recurrence = item['values'][4]
        
        # Convert None display to actual None
        if current_recurrence == "None":
            current_recurrence = None
        
        if current_recurrence == new_recurrence:
            recur_text = new_recurrence or "None"
            messagebox.showinfo("Info", f"Recurrence is already set to {recur_text}!")
            return
        
        # Get current reminder data
        reminders = get_reminders()
        reminder = next((r for r in reminders if r[0] == reminder_id), None)
        if not reminder:
            return
        
        update_reminder(reminder_id, reminder[1], reminder[2], reminder[3], new_recurrence)
        self.load_reminders()
        
        recur_text = new_recurrence or "None"
        messagebox.showinfo("Success", f"Recurrence set to {recur_text} successfully!", master=self.root)
    
    def cycle_recurrence(self, current_recurrence):
        """Cycle through recurrence options"""
        options = [None, "Daily", "Weekly", "Monthly"]
        
        # Handle display value "None"
        if current_recurrence == "None":
            current_recurrence = None
        
        try:
            current_index = options.index(current_recurrence)
            next_index = (current_index + 1) % len(options)
            return options[next_index]
        except ValueError:
            return "Daily"  # Default if current value not found

    def check_reminders(self):
        now = datetime.now()
        reminders = get_reminders()
        
        for reminder in reminders:
            if not reminder[5]:  # Skip disabled reminders
                continue
            
            due_time = datetime.strptime(reminder[3], "%Y-%m-%d %H:%M")
            reminder_id = reminder[0]
            
            if due_time <= now:
                # Check if we've already notified for this reminder
                if reminder_id not in self.notified_reminders:
                    self.show_notification(reminder)
                    self.notified_reminders.add(reminder_id)
                    
                    # Handle recurrence
                    if reminder[4]:
                        new_due_time = self.calculate_next_occurrence(due_time, reminder[4])
                        update_reminder(reminder[0], reminder[1], reminder[2], 
                                       new_due_time.strftime("%Y-%m-%d %H:%M"), reminder[4])
                        # Remove from notified set since it's rescheduled
                        self.notified_reminders.discard(reminder_id)
                    
                    self.load_reminders()
            else:
                # Reset notification status if due time is in the future
                self.notified_reminders.discard(reminder_id)

    def calculate_next_occurrence(self, due_time, recurrence):
        if recurrence == "Daily":
            return due_time + timedelta(days=1)
        elif recurrence == "Weekly":
            return due_time + timedelta(weeks=1)
        elif recurrence == "Monthly":
            # Simple monthly calculation - add 30 days
            return due_time + timedelta(days=30)
        return due_time

    def show_notification(self, reminder):
        self.start_sound_loop()
        
        # Create notification window
        notif = tk.Toplevel(self.root)
        notif.title("🔔 REMINDER!")
        notif.geometry("500x300")
        notif.configure(bg="#fff3cd")
        notif.attributes('-topmost', True)
        
        # Add to active notifications list
        self.active_notifications.append(notif)
        
        # Ensure sound stops when window is closed (via X button or any method)
        def on_close():
            self.stop_sound()
            if notif in self.active_notifications:
                self.active_notifications.remove(notif)
            try:
                notif.destroy()
            except tk.TclError:
                pass  # Window already destroyed
        
        # Bind the close event
        notif.protocol("WM_DELETE_WINDOW", on_close)
        
        # Center the window
        notif.update_idletasks()
        x = (notif.winfo_screenwidth() // 2) - (notif.winfo_width() // 2)
        y = (notif.winfo_screenheight() // 2) - (notif.winfo_height() // 2)
        notif.geometry(f"+{x}+{y}")
        
        # Header
        header = tk.Frame(notif, bg="#ffc107", height=40)
        header.pack(fill=tk.X)
        tk.Label(header, text="🔔 REMINDER", font=("Arial", 16, "bold"),
                bg="#ffc107", fg="#856404").pack(pady=8)
        
        # Content
        content = tk.Frame(notif, bg="#fff3cd", padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text=reminder[1], font=("Arial", 14, "bold"),
                bg="#fff3cd", fg="#856404").pack(pady=5)
        
        if reminder[2]:
            tk.Label(content, text=reminder[2], font=("Arial", 12),
                    bg="#fff3cd", fg="#856404", wraplength=450).pack(pady=5)
        
        tk.Label(content, text=f"Due: {reminder[3]}", font=("Arial", 10),
                bg="#fff3cd", fg="#856404").pack(pady=5)
        
        if reminder[4]:
            tk.Label(content, text=f"Recurrence: {reminder[4]}", font=("Arial", 10),
                    bg="#fff3cd", fg="#856404").pack(pady=2)
        
        def dismiss():
            on_close()
        
        tk.Button(content, text="Dismiss", command=dismiss,
                 bg="#dc3545", fg="white", font=("Arial", 12, "bold"),
                 padx=30, pady=10).pack(pady=15)

    def periodic_check(self):
        self.check_reminders()
        self.root.after(1000, self.periodic_check)

    def sound_settings(self):
        window = tk.Toplevel(self.root)
        window.title("Sound Settings")
        window.geometry("400x250")
        window.configure(bg=COLORS["bg"])
        
        tk.Label(window, text="Sound Settings", font=("Arial", 16, "bold"),
                bg=COLORS["bg"], fg=COLORS["dark"]).pack(pady=10)
        
        current_sound = get_setting("sound_file")
        sound_label = tk.Label(window, text=f"Current: {current_sound or 'Default system sound'}",
                              bg=COLORS["bg"], fg=COLORS["dark"], wraplength=350)
        sound_label.pack(pady=5)
        
        btn_frame = tk.Frame(window, bg=COLORS["bg"])
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Choose Sound File", command=lambda: self.choose_sound(sound_label),
                 bg=COLORS["accent"], fg="white", font=("Arial", 10),
                 padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Clear Custom Sound", command=lambda: self.clear_sound(sound_label),
                 bg=COLORS["danger"], fg="white", font=("Arial", 10),
                 padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        test_frame = tk.Frame(window, bg=COLORS["bg"])
        test_frame.pack(pady=10)
        
        tk.Button(test_frame, text="Test Sound", command=self.play_test_sound,
                 bg=COLORS["success"], fg="white", font=("Arial", 10),
                 padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(test_frame, text="Stop Sound", command=self.stop_sound,
                 bg=COLORS["warning"], fg=COLORS["dark"], font=("Arial", 10),
                 padx=15, pady=5).pack(side=tk.LEFT, padx=5)

    def choose_sound(self, label_widget=None):
        # Modified: Accept both WAV and MP3 files
        path = filedialog.askopenfilename(
            title="Choose Reminder Sound", 
            filetypes=[("Sound files", "*.wav *.mp3"), ("WAV files", "*.wav"), ("MP3 files", "*.mp3")]
        )
        
        # Modified: Store relative path if sound file is within DATA_DIR, otherwise store absolute path
        if path:
            relative_path = os.path.relpath(path, DATA_DIR)
            if not relative_path.startswith('..') and not os.path.isabs(relative_path):
                set_setting("sound_file", relative_path)
                if label_widget:
                    label_widget.config(text=f"Current: {relative_path}")
                messagebox.showinfo("Settings", f"Custom sound set:\n{relative_path}")
            else:
                set_setting("sound_file", path) # Store absolute path if outside data directory
                if label_widget:
                    label_widget.config(text=f"Current: {path}")
                messagebox.showinfo("Settings", f"Custom sound set:\n{path}")

    def clear_sound(self, label_widget=None):
        clear_setting("sound_file")
        if label_widget:
            label_widget.config(text="Current: Default system sound")
        messagebox.showinfo("Settings", "Custom sound cleared. Using default system sound.")
    
    def play_test_sound(self):
        self.stop_sound()
        sound_file = get_setting("sound_file")
        
        # Modified: Construct full path for sound file if it's a relative path
        if sound_file and not os.path.isabs(sound_file):
            sound_file = os.path.join(DATA_DIR, sound_file)

        try:
            if sound_file and os.path.exists(sound_file):
                # Use pygame for MP3 files and WAV files if available
                if self.pygame_initialized:
                    try:
                        pygame.mixer.music.load(sound_file)
                        pygame.mixer.music.play()
                        return
                    except pygame.error:
                        print(f"Pygame could not play: {sound_file}")
                
                # Fallback to winsound for WAV files on Windows
                if HAS_WINSOUND and sound_file.lower().endswith('.wav'):
                    winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    self.root.bell()
            else:
                # Default system sound
                if HAS_WINSOUND:
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                else:
                    self.root.bell()
        except Exception as e:
            messagebox.showwarning("Sound Error", f"Could not play sound.\nError: {e}")
            self.root.bell()

    def stop_sound(self):
        # Stop pygame music if playing
        if self.pygame_initialized and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        # Stop winsound if playing
        if HAS_WINSOUND:
            winsound.PlaySound(None, winsound.SND_PURGE)

    def start_sound_loop(self):
        self.stop_sound()
        sound_file = get_setting("sound_file")
        
        # Modified: Construct full path for sound file if it's a relative path
        if sound_file and not os.path.isabs(sound_file):
            sound_file = os.path.join(DATA_DIR, sound_file)

        try:
            # Try to use pygame for looping (supports both WAV and MP3)
            if self.pygame_initialized and sound_file and os.path.exists(sound_file):
                try:
                    pygame.mixer.music.load(sound_file)
                    pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                    return
                except pygame.error:
                    print(f"Pygame could not loop: {sound_file}")
            
            # Fallback to winsound for WAV files on Windows (no native looping for MP3)
            if HAS_WINSOUND and sound_file and os.path.exists(sound_file) and sound_file.lower().endswith('.wav'):
                flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
                winsound.PlaySound(sound_file, flags)
            elif HAS_WINSOUND:
                alias_flags = winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_LOOP
                winsound.PlaySound("SystemAsterisk", alias_flags)
            else:
                self.root.bell()
        except Exception:
            self.root.bell()

    def on_tree_leave(self, event):
        """Reset cursor when mouse leaves the tree widget"""
        self.tree.configure(cursor="")

    def show_help(self):
        """Show help dialog with keyboard shortcuts and usage information"""
        help_window = tk.Toplevel(self.root)
        help_window.title("📚 Reminder App - Help")
        help_window.geometry("600x500")
        help_window.configure(bg=COLORS["bg"])
        
        # Make help window modal
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Center the window
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (help_window.winfo_width() // 2)
        y = (help_window.winfo_screenheight() // 2) - (help_window.winfo_height() // 2)
        help_window.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(help_window, bg=COLORS["accent"], height=50)
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="📚 Reminder App Help", font=("Arial", 18, "bold"),
                bg=COLORS["accent"], fg="white").pack(pady=12)
        
        # Scrollable content
        canvas = tk.Canvas(help_window, bg=COLORS["bg"])
        scrollbar = ttk.Scrollbar(help_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Content
        content_frame = tk.Frame(scrollable_frame, bg=COLORS["bg"], padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Keyboard shortcuts section
        tk.Label(content_frame, text="⌨️ Keyboard Shortcuts", font=("Arial", 14, "bold"),
                bg=COLORS["bg"], fg=COLORS["dark"]).pack(anchor=tk.W, pady=(0, 10))
        
        shortcuts = [
            ("Ctrl+N", "Add new reminder"),
            ("Ctrl+E", "Edit selected reminder"),
            ("Delete", "Delete selected reminder"),
            ("Space", "Toggle status of selected reminder"),
            ("Ctrl+A", "Enable all reminders"),
            ("Ctrl+D", "Disable all reminders"),
            ("F5", "Reload reminders list"),
            ("F1", "Show this help dialog"),
            ("Escape", "Clear current selection")
        ]
        
        for key, desc in shortcuts:
            shortcut_frame = tk.Frame(content_frame, bg=COLORS["bg"])
            shortcut_frame.pack(fill=tk.X, pady=2)
            tk.Label(shortcut_frame, text=key, font=("Courier", 10, "bold"),
                    bg=COLORS["light"], fg=COLORS["dark"], padx=8, pady=2,
                    relief=tk.RAISED, borderwidth=1).pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(shortcut_frame, text=desc, font=("Arial", 10),
                    bg=COLORS["bg"], fg=COLORS["dark"]).pack(side=tk.LEFT)
        
        # Mouse actions section
        tk.Label(content_frame, text="\n🖱️ Mouse Actions", font=("Arial", 14, "bold"),
                bg=COLORS["bg"], fg=COLORS["dark"]).pack(anchor=tk.W, pady=(15, 10))
        
        mouse_actions = [
            ("Double-click reminder", "Edit reminder"),
            ("Click Status column", "Toggle reminder enabled/disabled"),
            ("Click Recurrence column", "Cycle through recurrence options"),
            ("Right-click reminder", "Show context menu")
        ]
        
        for action, desc in mouse_actions:
            action_frame = tk.Frame(content_frame, bg=COLORS["bg"])
            action_frame.pack(fill=tk.X, pady=2)
            tk.Label(action_frame, text=action, font=("Arial", 10, "bold"),
                    bg=COLORS["bg"], fg=COLORS["accent"]).pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(action_frame, text=desc, font=("Arial", 10),
                    bg=COLORS["bg"], fg=COLORS["dark"]).pack(side=tk.LEFT)
        
        # Features section
        tk.Label(content_frame, text="\n✨ Features", font=("Arial", 14, "bold"),
                bg=COLORS["bg"], fg=COLORS["dark"]).pack(anchor=tk.W, pady=(15, 10))
        
        features = [
            "📝 Create, edit, and delete reminders",
            "🔔 Audio notifications with custom sounds (WAV/MP3)",
            "🔁 Recurring reminders (Daily, Weekly, Monthly)",
            "📊 Filter reminders by status (Active/Inactive/All)",
            "🎯 Quick status and recurrence changes via clicks",
            "📋 Right-click context menu for quick actions",
            "💾 Automatic database backup and persistence",
            "📱 Modern, responsive user interface"
        ]
        
        for feature in features:
            tk.Label(content_frame, text=f"• {feature}", font=("Arial", 10),
                    bg=COLORS["bg"], fg=COLORS["dark"]).pack(anchor=tk.W, pady=1)
        
        # Tips section
        tk.Label(content_frame, text="\n💡 Tips", font=("Arial", 14, "bold"),
                bg=COLORS["bg"], fg=COLORS["dark"]).pack(anchor=tk.W, pady=(15, 10))
        
        tips = [
            "Use the filter options to focus on active or inactive reminders",
            "Custom sound files are stored relative to the data directory",
            "Recurring reminders automatically reschedule after triggering",
            "Right-click on reminders for quick access to common actions",
            "The status column shows current state and can be clicked to toggle"
        ]
        
        for tip in tips:
            tk.Label(content_frame, text=f"• {tip}", font=("Arial", 10),
                    bg=COLORS["bg"], fg=COLORS["dark"], wraplength=520,
                    justify=tk.LEFT).pack(anchor=tk.W, pady=1)
        
        # Pack the scrollable content
        canvas.pack(side="left", fill="both", expand=True, padx=(0, 0))
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        close_frame = tk.Frame(help_window, bg=COLORS["bg"], pady=15)
        close_frame.pack(fill=tk.X)
        
        close_btn = tk.Button(close_frame, text="Close (ESC)", command=help_window.destroy,
                             bg=COLORS["accent"], fg="white", font=("Arial", 11, "bold"),
                             padx=25, pady=8)
        close_btn.pack()
        
        # Bind ESC key to close
        help_window.bind("<Escape>", lambda e: help_window.destroy())
        
        # Focus the help window so ESC works
        help_window.focus_set()

# Add this main function at the end of the file
def main():
    root = tk.Tk()
    root.withdraw()
    app = ReminderApp(root)
    root.mainloop()

# For standalone testing (keep this as is)
if __name__ == "__main__":
    main()