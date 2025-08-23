import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import sqlite3
import os

# Windows sound handling
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

DB_FILE = "reminders.db"

# A modern color palette
COLORS = {
    "background": "#F7F7F7",
    "foreground": "#333333",
    "primary": "#007ACC",
    "primary_fg": "#FFFFFF",
    "accent": "#E1E1E1",
    "disabled": "#A0A0A0",
    "overdue": "#D16060"
}

# =========================
# Database helpers (Unchanged)
# =========================
def init_db():
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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO reminders (title, message, due_time, recurrence, enabled) VALUES (?, ?, ?, ?, ?)",
        (title, message, due_time, recurrence, enabled)
    )
    conn.commit()
    conn.close()

def update_reminder(reminder_id, title, message, due_time, recurrence, enabled):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE reminders SET title=?, message=?, due_time=?, recurrence=?, enabled=? WHERE id=?",
        (title, message, due_time, recurrence, enabled, reminder_id)
    )
    conn.commit()
    conn.close()

def delete_reminder(reminder_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
    conn.commit()
    conn.close()

def get_all_reminders():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title, message, due_time, recurrence, enabled FROM reminders ORDER BY due_time")
    rows = c.fetchall()
    conn.close()
    return rows

def toggle_reminder_status(reminder_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT enabled FROM reminders WHERE id=?", (reminder_id,))
    current = c.fetchone()
    if current is not None:
        new_status = 0 if current[0] == 1 else 1
        c.execute("UPDATE reminders SET enabled=? WHERE id=?", (new_status, reminder_id))
        conn.commit()
    conn.close()

def update_reminder_recurrence(reminder_id, recurrence):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE reminders SET recurrence=? WHERE id=?", (recurrence, reminder_id))
    conn.commit()
    conn.close()

def advance_due(due_str, recurrence):
    if not recurrence or recurrence == "None": return due_str
    dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
    if recurrence == "Daily": dt += timedelta(days=1)
    elif recurrence == "Weekly": dt += timedelta(weeks=1)
    elif recurrence == "Monthly": dt += timedelta(days=30)
    elif recurrence == "Yearly": dt += timedelta(days=365)
    return dt.strftime("%Y-%m-%d %H:%M")

def get_setting(key, default=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def clear_setting(key):
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
        self.root.geometry("1000x550")
        self.root.configure(bg=COLORS["background"])
        
        self.style = ttk.Style()
        self.apply_styles()

        self.reminders = []
        self.current_minute = None
        self.fired_this_minute = set()
        self.after_id = None

        self._build_settings_menu()
        self._build_ui()

        self.refresh_list()
        self.check_reminders()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.stop_sound()
        if self.after_id: self.root.after_cancel(self.after_id)
        self.root.destroy()

    def apply_styles(self):
        font_family = "Segoe UI"
        self.style.theme_use('vista')
        
        self.style.configure('.', font=(font_family, 10), background=COLORS["background"], foreground=COLORS["foreground"])
        self.style.configure('TFrame', background=COLORS["background"])
        self.style.configure('TLabel', background=COLORS["background"], foreground=COLORS["foreground"])
        self.style.configure('Bold.TLabel', font=(font_family, 10, 'bold'))

        self.style.configure('TButton', font=(font_family, 10), padding=8, background=COLORS["accent"], borderwidth=0)
        self.style.map('TButton', background=[('active', COLORS["primary"]), ('!disabled', COLORS["accent"])])
        
        self.style.configure('Primary.TButton', background=COLORS["primary"], foreground=COLORS["primary_fg"])
        # --- FIXED: Explicitly set the foreground color for the active state to ensure it stays white ---
        self.style.map('Primary.TButton', 
                       background=[('active', '#005a9e')],
                       foreground=[('active', COLORS["primary_fg"])])
        
        self.style.configure('Treeview', rowheight=25, font=(font_family, 10), fieldbackground=COLORS["background"])
        self.style.configure('Treeview.Heading', font=(font_family, 11, 'bold'))
        self.style.map('Treeview', background=[('selected', COLORS["primary"])])

        self.style.configure('TCombobox', padding=5, font=(font_family, 10))
        self.tree_tag_config_applied = False
        
    def _build_settings_menu(self):
        menubar = tk.Menu(self.root, bg=COLORS["background"], fg=COLORS["foreground"])
        self.root.config(menu=menubar)
        settings_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["background"], fg=COLORS["foreground"],
                                activebackground=COLORS["primary"], activeforeground=COLORS["primary_fg"])
        settings_menu.add_command(label="Choose Sound… (WAV format only)", command=self.choose_sound)
        settings_menu.add_command(label="Play Test Sound", command=self.play_test_sound)
        settings_menu.add_separator()
        settings_menu.add_command(label="Clear Sound (Default)", command=self.clear_sound)
        menubar.add_cascade(label="⚙️ Settings", menu=settings_menu)

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        toolbar = ttk.Frame(main_frame)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.add_btn = ttk.Button(toolbar, text="➕ Add Reminder", command=self.add_reminder_dialog)
        self.add_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.edit_btn = ttk.Button(toolbar, text="✎ Edit Selected", state="disabled", command=lambda: self.edit_reminder_dialog(self.get_selected_id()))
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        self.del_btn = ttk.Button(toolbar, text="🗑️ Delete Selected", state="disabled", command=self.delete_selected_reminder)
        self.del_btn.pack(side=tk.LEFT, padx=5)

        cols = ("ID", "Title", "Message", "Due Time", "Recurrence", "Status")
        self.tree = ttk.Treeview(main_frame, columns=cols, show="headings")
        
        for col in cols: self.tree.heading(col, text=col)
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Title", width=200); self.tree.column("Message", width=300)
        self.tree.column("Due Time", width=140, anchor="center"); self.tree.column("Recurrence", width=100, anchor="center")
        self.tree.column("Status", width=90, anchor="center")
        
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Button-1>", self._on_tree_click)

        self.tree.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

    def _on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return
        col_id_str = self.tree.identify_column(event.x); col_num = int(col_id_str.replace("#", ""))
        row_id = self.tree.identify_row(event.y)
        if not row_id: return
        reminder_id = int(self.tree.item(row_id, "values")[0])
        if col_num == 6: self.toggle_selected_status(reminder_id)
        elif col_num == 5: self._show_recurrence_menu(event, reminder_id)

    def _on_selection_changed(self, event):
        if self.tree.selection(): self.edit_btn.config(state="normal"); self.del_btn.config(state="normal")
        else: self.edit_btn.config(state="disabled"); self.del_btn.config(state="disabled")

    def _show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id: return
        self.tree.selection_set(row_id)
        reminder_id = self.get_selected_id()
        if not reminder_id: return
        context_menu = tk.Menu(self.root, tearoff=0, bg=COLORS["background"], fg=COLORS["foreground"],
                               activebackground=COLORS["primary"], activeforeground=COLORS["primary_fg"])
        context_menu.add_command(label="✎ Edit", command=lambda: self.edit_reminder_dialog(reminder_id))
        context_menu.add_command(label="🗑️ Delete", command=self.delete_selected_reminder)
        context_menu.add_separator()
        context_menu.add_command(label="⏯️ Toggle Status", command=lambda: self.toggle_selected_status(reminder_id))
        context_menu.tk_popup(event.x_root, event.y_root)
        
    def _show_recurrence_menu(self, event, reminder_id):
        menu = tk.Menu(self.root, tearoff=0, bg=COLORS["background"], fg=COLORS["foreground"],
                       activebackground=COLORS["primary"], activeforeground=COLORS["primary_fg"])
        recurrence_options = ["None", "Daily", "Weekly", "Monthly", "Yearly"]
        for option in recurrence_options:
            menu.add_command(label=option, command=lambda opt=option: self._change_recurrence(reminder_id, opt))
        menu.tk_popup(event.x_root, event.y_root)
        
    def _change_recurrence(self, reminder_id, new_recurrence):
        update_reminder_recurrence(reminder_id, new_recurrence); self.refresh_list()

    def get_selected_id(self):
        selection = self.tree.selection()
        if not selection: return None
        return int(self.tree.item(selection[0], "values")[0])

    def delete_selected_reminder(self):
        reminder_id = self.get_selected_id()
        if not reminder_id: return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this reminder?"):
            delete_reminder(reminder_id); self.refresh_list()

    def toggle_selected_status(self, reminder_id):
        toggle_reminder_status(reminder_id); self.refresh_list()

    def refresh_reminders_cache(self):
        self.reminders = get_all_reminders()

    def refresh_list(self):
        if not self.tree_tag_config_applied:
            self.tree.tag_configure('disabled', foreground=COLORS["disabled"])
            self.tree.tag_configure('overdue', foreground=COLORS["overdue"])
            self.tree_tag_config_applied = True
        selected_item = self.tree.selection()
        self.refresh_reminders_cache()
        self.tree.delete(*self.tree.get_children())
        now = datetime.now()
        for r_tuple in self.reminders:
            r_id, title, msg, due_time, recur, enabled = r_tuple
            status = "Enabled" if enabled else "Disabled"
            due_dt = datetime.strptime(due_time, "%Y-%m-%d %H:%M")
            tags = []
            if not enabled: tags.append('disabled')
            elif due_dt < now: tags.append('overdue')
            self.tree.insert("", tk.END, iid=r_id, values=(r_id, title, msg, due_time, recur or "None", status), tags=tags)
        if selected_item and self.tree.exists(selected_item[0]):
            self.tree.selection_set(selected_item[0])

    def add_reminder_dialog(self): self._show_edit_add_dialog()
    def edit_reminder_dialog(self, reminder_id):
        if reminder_id is None: return
        self._show_edit_add_dialog(reminder_id)
        
    # =============================================================
    # --- REPLACE THIS ENTIRE FUNCTION IN YOUR SCRIPT ---
    # =============================================================
    def _show_edit_add_dialog(self, reminder_id=None):
        is_edit = reminder_id is not None
        r_data = None
        if is_edit:
            # --- Fetches fresh data directly from the database for editing ---
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT title, message, due_time, recurrence, enabled FROM reminders WHERE id=?", (reminder_id,))
            r_data = c.fetchone()
            conn.close()
            if not r_data:
                messagebox.showerror("Error", "Reminder not found. It may have been deleted.", parent=self.root)
                self.refresh_list()
                return

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Reminder" if is_edit else "Add Reminder")
        dialog.geometry("450x650") # Set dialog geometry as requested
        dialog.transient(self.root); dialog.grab_set(); dialog.configure(bg=COLORS["background"])

        main_frame = ttk.Frame(dialog, padding="20"); main_frame.pack(fill=tk.BOTH, expand=True)
        details_frame = ttk.LabelFrame(main_frame, text=" Reminder Details ", padding="15"); details_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(details_frame, text="Title:", style="Bold.TLabel").pack(anchor='w', pady=(0, 2))
        title_entry = ttk.Entry(details_frame)
        if is_edit: title_entry.insert(0, r_data[0] or "")
        title_entry.pack(pady=(0, 10), fill=tk.X, ipady=4)

        ttk.Label(details_frame, text="Message:", style="Bold.TLabel").pack(anchor='w', pady=(5, 2))
        msg_entry = tk.Text(details_frame, height=6, relief=tk.SOLID, borderwidth=1, font=("Segoe UI", 10), wrap="word",
                           selectbackground=COLORS["primary"])
        if is_edit: msg_entry.insert("1.0", r_data[1] or "")
        msg_entry.pack(pady=(0, 10), fill=tk.BOTH, expand=True)

        timing_frame = ttk.LabelFrame(main_frame, text=" Timing & Recurrence ", padding="15"); timing_frame.pack(fill="x", pady=10)
        ttk.Label(timing_frame, text="Due Time (YYYY-MM-DD HH:MM):", style="Bold.TLabel").pack(anchor='w', pady=(5, 2))
        due_entry = ttk.Entry(timing_frame)
        due_entry.insert(0, r_data[2] if is_edit else (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M"))
        due_entry.pack(pady=(0, 10), fill=tk.X, ipady=4)
        ttk.Label(timing_frame, text="Recurrence:", style="Bold.TLabel").pack(anchor='w', pady=(5, 2))
        rec_var = tk.StringVar(value=r_data[3] or "None" if is_edit else "None")
        rec_menu = ttk.Combobox(timing_frame, textvariable=rec_var, values=["None", "Daily", "Weekly", "Monthly", "Yearly"], state="readonly"); rec_menu.pack(pady=(0, 10), fill=tk.X)
        ttk.Label(timing_frame, text="Status:", style="Bold.TLabel").pack(anchor='w', pady=(5, 2))
        status_var = tk.StringVar(value="Enabled" if not is_edit or r_data[4] == 1 else "Disabled")
        status_menu = ttk.Combobox(timing_frame, textvariable=status_var, values=["Enabled", "Disabled"], state="readonly"); status_menu.pack(pady=(0, 10), fill=tk.X)

        def save():
            try: datetime.strptime(due_entry.get(), "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Error", "Invalid date/time format. Use YYYY-MM-DD HH:MM", parent=dialog); return
            args = (title_entry.get().strip() or "Untitled Reminder", msg_entry.get("1.0", tk.END).strip(),
                    due_entry.get().strip(), rec_var.get(), 1 if status_var.get() == "Enabled" else 0)
            if is_edit: update_reminder(reminder_id, *args)
            else: insert_reminder(*args)
            dialog.destroy(); self.refresh_list()

        btn_row = ttk.Frame(main_frame); btn_row.pack(pady=(15, 0), fill="x", side="bottom")
        btn_row.grid_columnconfigure((0, 1), weight=1)

        # --- FIXED: Switched to tk.Button for reliable color control ---
        font_tuple = ("Segoe UI", 10)
        
        cancel_btn = tk.Button(btn_row, text="Cancel", command=dialog.destroy, 
                              font=font_tuple, bg=COLORS["accent"], fg=COLORS["foreground"],
                              relief="flat", activebackground="#cccccc", activeforeground=COLORS["foreground"])
        cancel_btn.grid(row=0, column=0, padx=(0,5), sticky="ew", ipady=5)

        save_btn = tk.Button(btn_row, text="Save Changes", command=save,
                            font=font_tuple, bg=COLORS["primary"], fg=COLORS["primary_fg"],
                            relief="flat", activebackground="#005a9e", activeforeground=COLORS["primary_fg"])
        save_btn.grid(row=0, column=1, padx=(5,0), sticky="ew", ipady=5)

    def check_reminders(self):
        now_min = datetime.now().strftime("%Y-%m-%d %H:%M")
        if self.current_minute != now_min:
            self.current_minute = now_min; self.fired_this_minute.clear();
            if datetime.now().second % 15 == 0: self.refresh_list()
        
        # We need fresh data for checking
        fresh_reminders = get_all_reminders()

        for r_tuple in fresh_reminders:
            r_id, _, _, due_time, _, enabled = r_tuple
            if enabled and due_time == now_min and r_id not in self.fired_this_minute:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT id, title, message, due_time, recurrence, enabled FROM reminders WHERE id=?", (r_id,))
                reminder_to_show = c.fetchone()
                conn.close()
                self.show_notification(dict(zip(["id", "title", "message", "due_time", "recurrence", "enabled"], reminder_to_show)))
                self.fired_this_minute.add(r_id)

        self.after_id = self.root.after(1000, self.check_reminders)

    def choose_sound(self):
        path = filedialog.askopenfilename(title="Choose Reminder Sound (WAV only)", filetypes=[("WAV files", "*.wav")])
        if path: set_setting("sound_file", path); messagebox.showinfo("Settings", f"Custom sound set:\n{path}")
    def clear_sound(self):
        clear_setting("sound_file"); messagebox.showinfo("Settings", "Custom sound cleared. Using default system sound.")
    def play_test_sound(self):
        self.stop_sound(); sound_file = get_setting("sound_file")
        try:
            if sound_file and os.path.exists(sound_file):
                if HAS_WINSOUND: winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else: self.root.bell()
            elif HAS_WINSOUND: winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
            else: self.root.bell()
        except Exception as e: messagebox.showwarning("Sound Error", f"Could not play sound.\nError: {e}")

    def stop_sound(self):
        if HAS_WINSOUND: winsound.PlaySound(None, winsound.SND_PURGE)

    # =============================================================
    # --- REPLACE THIS FUNCTION IN YOUR SCRIPT ---
    # =============================================================
    def show_notification(self, reminder):
        popup = tk.Toplevel(self.root); popup.title("Reminder!"); popup.geometry("450x300")
        popup.transient(self.root); popup.grab_set(); popup.attributes("-topmost", True); popup.configure(bg=COLORS["background"])

        self.start_sound_loop(); popup.protocol("WM_DELETE_WINDOW", lambda: on_popup_close())
        popup_frame = ttk.Frame(popup, padding=20); popup_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(popup_frame, text="🔔", font=("Segoe UI", 48)).pack(pady=(0, 10))
        ttk.Label(popup_frame, text=reminder['title'], font=("Segoe UI", 16, "bold"), wraplength=400, justify="center").pack(pady=(0, 5))
        ttk.Label(popup_frame, text=reminder['message'], wraplength=400, justify="center").pack(pady=(0, 20))
        btn_row = ttk.Frame(popup_frame); btn_row.pack(pady=10)

        def dismiss():
            recurrence = reminder.get("recurrence")
            if recurrence and recurrence != "None":
                new_due = advance_due(reminder["due_time"], recurrence)
                update_reminder(reminder["id"], reminder["title"], reminder["message"], new_due, recurrence, 1)
            else: update_reminder(reminder["id"], reminder["title"], reminder["message"], reminder["due_time"], "None", 0)
            on_popup_close()
        def snooze(minutes):
            new_due = datetime.now() + timedelta(minutes=minutes)
            update_reminder(reminder["id"], reminder["title"], reminder["message"], new_due.strftime("%Y-%m-%d %H:%M"), reminder.get("recurrence"), 1)
            on_popup_close()
        def on_popup_close(): self.stop_sound(); self.refresh_list(); popup.destroy()

        # --- FIX START: Switched from ttk.Button to tk.Button for reliable color control ---
        font_tuple = ("Segoe UI", 10)
        
        # Standard buttons
        snooze5_btn = tk.Button(btn_row, text="Snooze 5m", command=lambda: snooze(5),
                            font=font_tuple, bg=COLORS["accent"], fg=COLORS["foreground"],
                            relief="flat", activebackground="#cccccc", activeforeground=COLORS["foreground"])
        snooze5_btn.pack(side=tk.LEFT, padx=5, ipady=4, ipadx=8)

        snooze10_btn = tk.Button(btn_row, text="Snooze 10m", command=lambda: snooze(10),
                                font=font_tuple, bg=COLORS["accent"], fg=COLORS["foreground"],
                                relief="flat", activebackground="#cccccc", activeforeground=COLORS["foreground"])
        snooze10_btn.pack(side=tk.LEFT, padx=5, ipady=4, ipadx=8)

        # Primary action button
        dismiss_btn = tk.Button(btn_row, text="Dismiss", command=dismiss,
                            font=font_tuple, bg=COLORS["primary"], fg=COLORS["primary_fg"],
                            relief="flat", activebackground="#005a9e", activeforeground=COLORS["primary_fg"])
        dismiss_btn.pack(side=tk.LEFT, padx=(15, 5), ipady=4, ipadx=8)
        # --- FIX END ---

    def start_sound_loop(self):
        self.stop_sound(); sound_file = get_setting("sound_file")
        try:
            flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
            alias_flags = winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_LOOP
            if HAS_WINSOUND:
                if sound_file and os.path.exists(sound_file): winsound.PlaySound(sound_file, flags)
                else: winsound.PlaySound("SystemAsterisk", alias_flags)
            else: self.root.bell()
        except Exception: self.root.bell()

def main(master=None):
    init_db()
    if master: window = tk.Toplevel(master)
    else: window = tk.Tk()
    app = ReminderApp(window)
    if not master: window.mainloop()

if __name__ == "__main__":
    main()
