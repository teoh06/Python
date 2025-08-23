import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import sqlite3
import os
import threading

# Windows sound handling
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

DB_FILE = "reminders.db"

# =========================
# Database helpers
# =========================
def init_db():
    """Initializes the SQLite database, creating tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        message TEXT,
        due_time TEXT NOT NULL,
        recurrence TEXT,
        enabled INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    conn.commit()
    conn.close()

def insert_reminder(title, message, due_time, recurrence, enabled):
    """Inserts a new reminder into the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO reminders (title, message, due_time, recurrence, enabled) VALUES (?, ?, ?, ?, ?)",
        (title, message, due_time, recurrence, enabled)
    )
    conn.commit()
    conn.close()

def update_reminder(reminder_id, title, message, due_time, recurrence, enabled):
    """Updates an existing reminder in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE reminders SET title=?, message=?, due_time=?, recurrence=?, enabled=? WHERE id=?",
        (title, message, due_time, recurrence, enabled, reminder_id)
    )
    conn.commit()
    conn.close()

def delete_reminder(reminder_id):
    """Deletes a reminder from the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
    conn.commit()
    conn.close()

def get_all_reminders():
    """Retrieves all reminders from the database, ordered by due time."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title, message, due_time, recurrence, enabled FROM reminders ORDER BY due_time")
    rows = c.fetchall()
    conn.close()
    return rows

def toggle_reminder_status(reminder_id):
    """Toggles the enabled/disabled status of a reminder."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT enabled FROM reminders WHERE id=?", (reminder_id,))
    current = c.fetchone()
    if current is not None:
        new_status = 0 if current[0] == 1 else 1
        c.execute("UPDATE reminders SET enabled=? WHERE id=?", (new_status, reminder_id))
        conn.commit()
    conn.close()

def advance_due(due_str, recurrence):
    """
    Advances a due_time string based on the recurrence.
    Uses simple day counts for month/year (30/365) for simplicity.
    """
    if not recurrence or recurrence == "None":
        return due_str
    dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
    if recurrence == "Daily":
        dt += timedelta(days=1)
    elif recurrence == "Weekly":
        dt += timedelta(weeks=1)
    elif recurrence == "Monthly":
        dt += timedelta(days=30)  # simple month step
    elif recurrence == "Yearly":
        dt += timedelta(days=365)  # simple year step
    return dt.strftime("%Y-%m-%d %H:%M")

def get_setting(key, default=None):
    """Retrieves a setting value from the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    """Sets or updates a setting value in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def clear_setting(key):
    """Removes a setting from the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM settings WHERE key=?", (key,))
    conn.commit()
    conn.close()

# =========================
# App
# =========================
class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reminder App")
        self.root.geometry("950x500")

        self.style = ttk.Style()
        self.apply_styles()

        self.reminders = []
        self.current_minute = None
        self.fired_this_minute = set()
        
        self.sound_thread = None

        self._build_settings_menu()
        self._build_ui()

        self.refresh_list()
        self.check_reminders()

    def apply_styles(self):
        """Applies custom styles to Tkinter widgets."""
        self.style.theme_use('vista') # or 'clam', 'alt', 'default'

        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', font=('Helvetica', 10), padding=8)
        self.style.configure('TLabel', font=('Helvetica', 10))
        self.style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold'))
        self.style.configure('Treeview', font=('Helvetica', 10))
        self.style.map('TButton',
            background=[('active', '#e1e1e1')],
            foreground=[('active', '#000000')])
        
    def _build_settings_menu(self):
        """Builds the 'Settings' menu in the application."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Choose Sound… (Only accept wav format)", command=self.choose_sound)
        settings_menu.add_command(label="Play Test Sound", command=self.play_test_sound)
        settings_menu.add_separator()
        settings_menu.add_command(label="Clear Sound (Default)", command=self.clear_sound)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
    def _build_ui(self):
        """Constructs the main application UI components."""
        main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("ID", "Title", "Message", "Due Time", "Recurrence", "Status", "Actions")
        self.tree = ttk.Treeview(main_frame, columns=cols, show="headings")
        
        for col in cols:
            self.tree.heading(col, text=col)

        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Title", width=150)
        self.tree.column("Message", width=250)
        self.tree.column("Due Time", width=140, anchor="center")
        self.tree.column("Recurrence", width=100, anchor="center")
        self.tree.column("Status", width=90, anchor="center")
        self.tree.column("Actions", width=120, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Button-1>", self.on_tree_click)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(10, 0))
        ttk.Button(btn_frame, text="Add Reminder", command=self.add_reminder_dialog).pack(side=tk.LEFT, padx=5)

    def refresh_reminders_cache(self):
        """Refreshes the internal cache of reminders from the database."""
        self.reminders = []
        for r in get_all_reminders():
            self.reminders.append({
                "id": r[0],
                "title": r[1],
                "message": r[2] or "",
                "due_time": r[3],
                "recurrence": r[4] or "None",
                "status": "Enabled" if r[5] == 1 else "Disabled",
            })

    def refresh_list(self):
        """Refreshes the Treeview display with current reminder data."""
        self.refresh_reminders_cache()
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in self.reminders:
            actions = "Edit  Delete" # Spaces are intentional for click areas
            self.tree.insert(
                "",
                tk.END,
                values=(r["id"], r["title"], r["message"], r["due_time"], r["recurrence"], r["status"], actions)
            )

    def on_tree_click(self, event):
        """Handles clicks within the Treeview, triggering edit, delete, or status toggle actions."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        item = self.tree.item(row_id)
        vals = item.get("values", [])
        if not vals:
            return

        reminder_id = vals[0]
        col_num = int(col.replace("#", ""))
        
        # Actions are in column 7 in the display, but column 6 in the raw data
        if col_num == 7:
            cell_bbox = self.tree.bbox(row_id, f"#{col_num}")
            if not cell_bbox:
                return
            x0, y0, w, h = cell_bbox
            x_offset = event.x - x0
            if x_offset < w / 2:
                self.edit_reminder_dialog(reminder_id)
            else:
                delete_reminder(reminder_id)
                self.refresh_list()
        # Status is in column 6
        elif col_num == 6:
            toggle_reminder_status(reminder_id)
            self.refresh_list()

    def add_reminder_dialog(self):
        """Opens a dialog for adding a new reminder."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Reminder")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        dialog_frame = ttk.Frame(dialog, padding="15")
        dialog_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(dialog_frame, text="Title:", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        title_entry = ttk.Entry(dialog_frame, width=40)
        title_entry.pack(pady=(0, 10), fill=tk.X)

        ttk.Label(dialog_frame, text="Message:", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        msg_entry = tk.Text(dialog_frame, width=40, height=6)
        msg_entry.pack(pady=(0, 10), fill=tk.BOTH, expand=True)

        ttk.Label(dialog_frame, text="Due Time (YYYY-MM-DD HH:MM):", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        due_entry = ttk.Entry(dialog_frame, width=25)
        due_entry.insert(0, (datetime.now() + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M"))
        due_entry.pack(pady=(0, 10), fill=tk.X)

        ttk.Label(dialog_frame, text="Recurrence:", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        rec_var = tk.StringVar(value="None")
        rec_menu = ttk.Combobox(dialog_frame, textvariable=rec_var, values=["None", "Daily", "Weekly", "Monthly", "Yearly"], state="readonly")
        rec_menu.pack(pady=(0, 10), fill=tk.X)

        ttk.Label(dialog_frame, text="Status:", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        status_var = tk.StringVar(value="Enabled")
        status_menu = ttk.Combobox(dialog_frame, textvariable=status_var, values=["Enabled", "Disabled"], state="readonly")
        status_menu.pack(pady=(0, 20), fill=tk.X)

        def save():
            """Saves the new reminder and closes the dialog."""
            try:
                datetime.strptime(due_entry.get(), "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Error", "Invalid date/time format. Use YYYY-MM-DD HH:MM")
                return

            insert_reminder(
                title_entry.get().strip(),
                msg_entry.get("1.0", tk.END).strip(),
                due_entry.get().strip(),
                rec_var.get(),
                1 if status_var.get() == "Enabled" else 0
            )
            dialog.destroy()
            self.refresh_list()

        btn_row = ttk.Frame(dialog_frame)
        btn_row.pack(pady=10)
        ttk.Button(btn_row, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="Save Reminder", command=save).pack(side=tk.LEFT, padx=6)

    def edit_reminder_dialog(self, reminder_id):
        """Opens a dialog for editing an existing reminder."""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT title, message, due_time, recurrence, enabled FROM reminders WHERE id=?", (reminder_id,))
        r = c.fetchone()
        conn.close()
        if not r:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Reminder")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()

        dialog_frame = ttk.Frame(dialog, padding="15")
        dialog_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(dialog_frame, text="Title:", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        title_entry = ttk.Entry(dialog_frame, width=40)
        title_entry.insert(0, r[0] or "")
        title_entry.pack(pady=(0, 10), fill=tk.X)

        ttk.Label(dialog_frame, text="Message:", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        msg_entry = tk.Text(dialog_frame, width=40, height=6)
        msg_entry.insert("1.0", r[1] or "")
        msg_entry.pack(pady=(0, 10), fill=tk.BOTH, expand=True)

        ttk.Label(dialog_frame, text="Due Time (YYYY-MM-DD HH:MM):", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        due_entry = ttk.Entry(dialog_frame, width=25)
        due_entry.insert(0, r[2])
        due_entry.pack(pady=(0, 10), fill=tk.X)

        ttk.Label(dialog_frame, text="Recurrence:", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        rec_var = tk.StringVar(value=r[3] or "None")
        rec_menu = ttk.Combobox(dialog_frame, textvariable=rec_var, values=["None", "Daily", "Weekly", "Monthly", "Yearly"], state="readonly")
        rec_menu.pack(pady=(0, 10), fill=tk.X)

        ttk.Label(dialog_frame, text="Status:", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(5, 0))
        status_var = tk.StringVar(value="Enabled" if r[4] == 1 else "Disabled")
        status_menu = ttk.Combobox(dialog_frame, textvariable=status_var, values=["Enabled", "Disabled"], state="readonly")
        status_menu.pack(pady=(0, 20), fill=tk.X)

        def save():
            """Saves the edited reminder and closes the dialog."""
            try:
                datetime.strptime(due_entry.get(), "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Error", "Invalid date/time format. Use YYYY-MM-DD HH:MM")
                return
            update_reminder(
                reminder_id,
                title_entry.get().strip(),
                msg_entry.get("1.0", tk.END).strip(),
                due_entry.get().strip(),
                rec_var.get(),
                1 if status_var.get() == "Enabled" else 0
            )
            dialog.destroy()
            self.refresh_list()

        btn_row = ttk.Frame(dialog_frame)
        btn_row.pack(pady=10)
        ttk.Button(btn_row, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="Save Changes", command=save).pack(side=tk.LEFT, padx=6)

    def check_reminders(self):
        """
        Periodically checks for due reminders and triggers notifications.
        Runs every second using `root.after()`.
        """
        now_min = datetime.now().strftime("%Y-%m-%d %H:%M")

        if self.current_minute != now_min:
            self.current_minute = now_min
            self.fired_this_minute.clear()
            self.refresh_reminders_cache() # Refresh the cache every minute to catch new reminders

        for r in self.reminders:
            if r["status"] == "Enabled" and r["due_time"] == now_min:
                if r["id"] not in self.fired_this_minute:
                    self.show_notification(r)
                    self.fired_this_minute.add(r["id"])

        self.root.after(1000, self.check_reminders)

    def choose_sound(self):
        """Opens a file dialog for the user to select a custom sound file."""
        path = filedialog.askopenfilename(
            title="Choose Reminder Sound (WAV only)",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        if path:
            set_setting("sound_file", path)
            messagebox.showinfo("Settings", f"Custom sound set:\n{path}")

    def clear_sound(self):
        """Clears the custom sound setting, reverting to the default system sound."""
        clear_setting("sound_file")
        messagebox.showinfo("Settings", "Custom sound cleared. Using default system sound/bell.")

    def play_test_sound(self):
        """Plays the currently selected custom sound or the system bell for testing."""
        self.stop_sound()
        sound_file = get_setting("sound_file")
        if sound_file and os.path.exists(sound_file):
            if HAS_WINSOUND and sound_file.lower().endswith(".wav"):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                self.root.bell()
        elif HAS_WINSOUND:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        else:
            self.root.bell()

    def stop_sound(self):
        """Stops any currently playing sound."""
        if HAS_WINSOUND:
            winsound.PlaySound(None, winsound.SND_PURGE)

    def show_notification(self, reminder):
        """
        Displays a notification popup for a due reminder.
        Includes options to dismiss or snooze the reminder.
        """
        popup = tk.Toplevel(self.root)
        popup.title(f"Reminder: {reminder['title']}")
        popup.geometry("480x250")
        popup.transient(self.root)
        popup.grab_set()
        popup.attributes("-topmost", True)

        self.start_sound_loop(popup)
        popup.protocol("WM_DELETE_WINDOW", lambda: (self.stop_sound(), popup.destroy()))

        popup_frame = ttk.Frame(popup, padding=15)
        popup_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(popup_frame, text=reminder["title"], font=("Helvetica", 16, "bold"), wraplength=450).pack(pady=(10, 5))
        ttk.Label(popup_frame, text=reminder["message"], wraplength=450).pack(pady=(5, 15))

        def dismiss():
            """Dismisses the reminder, stops the sound, and handles recurrence."""
            self.stop_sound()
            if reminder["recurrence"] and reminder["recurrence"] != "None":
                new_due = advance_due(reminder["due_time"], reminder["recurrence"])
                update_reminder(reminder["id"], reminder["title"], reminder["message"], new_due, reminder["recurrence"], 1)
                self.refresh_list()
            popup.destroy()

        def snooze(minutes):
            """Snoozes the reminder for a specified number of minutes."""
            self.stop_sound()
            new_due = datetime.now() + timedelta(minutes=minutes)
            update_reminder(reminder["id"], reminder["title"], reminder["message"], new_due.strftime("%Y-%m-%d %H:%M"), reminder["recurrence"], 1)
            self.refresh_list()
            popup.destroy()

        btn_row = ttk.Frame(popup_frame)
        btn_row.pack(pady=10)
        ttk.Button(btn_row, text="Dismiss", command=dismiss).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_row, text="Snooze 5 min", command=lambda: snooze(5)).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_row, text="Snooze 10 min", command=lambda: snooze(10)).pack(side=tk.LEFT, padx=10)
    
    def start_sound_loop(self, popup):
        """Starts a continuous sound loop for the notification, until dismissed."""
        self.stop_sound()
        sound_file = get_setting("sound_file")
        if sound_file and os.path.exists(sound_file):
            if HAS_WINSOUND and sound_file.lower().endswith(".wav"):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            else:
                def loop_bell():
                    if popup.winfo_exists():
                        self.root.bell()
                        popup.after(1000, loop_bell)
                loop_bell()
        elif HAS_WINSOUND:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_LOOP)
        else:
            def loop_bell():
                if popup.winfo_exists():
                    self.root.bell()
                    popup.after(1000, loop_bell)
            loop_bell()

def main():
    """Main function to initialize and run the application."""
    init_db()
    root = tk.Tk()
    app = ReminderApp(root)
    root.mainloop()

# =========================
# Run
# =========================
if __name__ == "__main__":
    main()
