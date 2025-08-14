import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sqlite3

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

def advance_due(due_str, recurrence):
    """Advance due_time string by recurrence. Uses simple day counts for month/year (30/365)."""
    if not recurrence or recurrence == "None":
        return due_str
    dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
    if recurrence == "Daily":
        dt += timedelta(days=1)
    elif recurrence == "Weekly":
        dt += timedelta(weeks=1)
    elif recurrence == "Monthly":
        dt += timedelta(days=30)   # simple month step
    elif recurrence == "Yearly":
        dt += timedelta(days=365)  # simple year step
    return dt.strftime("%Y-%m-%d %H:%M")

# =========================
# App
# =========================
class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reminder App")
        self.root.geometry("950x500")

        # cache of reminders for quick per-second checks
        self.reminders = []
        self.current_minute = None
        self.fired_this_minute = set()

        # Tree
        cols = ("ID", "Title", "Message", "Due Time", "Recurrence", "Status", "Actions")
        self.tree = ttk.Treeview(root, columns=cols, show="headings")
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

        # Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Add Reminder", command=self.add_reminder_dialog).pack(side=tk.LEFT, padx=5)

        # load + start
        self.refresh_list()
        self.check_reminders()

    # --------- cache + list ---------
    def refresh_reminders_cache(self):
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
        # NOTE: we do NOT clear fired_this_minute here; protected by per-minute gate in check_reminders

    def refresh_list(self):
        self.refresh_reminders_cache()
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in self.reminders:
            actions = "Edit   Delete"
            self.tree.insert(
                "",
                tk.END,
                values=(r["id"], r["title"], r["message"], r["due_time"], r["recurrence"], r["status"], actions)
            )

    # --------- clicks in tree ---------
    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)  # like "#4"
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        item = self.tree.item(row_id)
        vals = item.get("values", [])
        if not vals:
            return

        reminder_id = vals[0]
        col_num = int(col.replace("#", ""))

        if col_num == 4:  # Due Time column
            self.edit_reminder_dialog(reminder_id)
        elif col_num == 6:  # Status column
            toggle_reminder_status(reminder_id)
            self.refresh_list()
        elif col_num == 7:  # Actions column ("Edit   Delete")
            # IMPORTANT: bbox needs the column name like "#7", not integer 7
            cell_bbox = self.tree.bbox(row_id, f"#{col_num}")
            if not cell_bbox:
                return
            x0, y0, w, h = cell_bbox
            x_offset = event.x - x0
            # left half = Edit, right half = Delete
            if x_offset < w / 2:
                self.edit_reminder_dialog(reminder_id)
            else:
                delete_reminder(reminder_id)
                self.refresh_list()

    # --------- dialogs ---------
    def add_reminder_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Reminder")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        # Title
        ttk.Label(dialog, text="Title:", anchor="center", justify="center").pack(anchor="center", fill="x", pady=(10, 2))
        title_entry = ttk.Entry(dialog, width=42, justify="center")
        title_entry.pack(pady=2)

        # Message (multiline)
        ttk.Label(dialog, text="Message:", anchor="center", justify="center").pack(anchor="center", fill="x", pady=(10, 2))
        msg_entry = tk.Text(dialog, width=42, height=6)
        msg_entry.pack(pady=2)

        # Due Time
        ttk.Label(dialog, text="Due Time (YYYY-MM-DD HH:MM):").pack(pady=(10, 2))
        due_entry = ttk.Entry(dialog, width=20, justify="center")
        # default to NEXT minute
        due_entry.insert(0, (datetime.now() + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M"))
        due_entry.pack()

        # Recurrence
        ttk.Label(dialog, text="Recurrence:").pack(pady=(10, 2))
        rec_var = tk.StringVar(value="None")
        rec_menu = ttk.Combobox(dialog, textvariable=rec_var, values=["None", "Daily", "Weekly", "Monthly", "Yearly"], state="readonly")
        rec_menu.pack()

        # Status
        ttk.Label(dialog, text="Status:").pack(pady=(10, 2))
        status_var = tk.StringVar(value="Enabled")
        status_menu = ttk.Combobox(dialog, textvariable=status_var, values=["Enabled", "Disabled"], state="readonly")
        status_menu.pack()

        def save():
            # validate time format
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

        btns = ttk.Frame(dialog)
        btns.pack(pady=12)
        ttk.Button(btns, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Save Reminder", command=save).pack(side=tk.LEFT, padx=6)

    def edit_reminder_dialog(self, reminder_id):
        # fetch one
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT title, message, due_time, recurrence, enabled FROM reminders WHERE id=?", (reminder_id,))
        r = c.fetchone()
        conn.close()
        if not r:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Reminder")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Title:", anchor="center").pack(fill="x", pady=(10, 2))
        title_entry = ttk.Entry(dialog, width=42, justify="center")
        title_entry.insert(0, r[0] or "")
        title_entry.pack(pady=2)

        ttk.Label(dialog, text="Message:").pack(pady=(10, 2))
        msg_entry = tk.Text(dialog, width=42, height=6)
        msg_entry.insert("1.0", r[1] or "")
        msg_entry.pack(pady=2)

        ttk.Label(dialog, text="Due Time (YYYY-MM-DD HH:MM):").pack(pady=(10, 2))
        due_entry = ttk.Entry(dialog, width=20, justify="center")
        due_entry.insert(0, r[2])
        due_entry.pack()

        ttk.Label(dialog, text="Recurrence:").pack(pady=(10, 2))
        rec_var = tk.StringVar(value=r[3] or "None")
        rec_menu = ttk.Combobox(dialog, textvariable=rec_var, values=["None", "Daily", "Weekly", "Monthly", "Yearly"], state="readonly")
        rec_menu.pack()

        ttk.Label(dialog, text="Status:").pack(pady=(10, 2))
        status_var = tk.StringVar(value="Enabled" if r[4] == 1 else "Disabled")
        status_menu = ttk.Combobox(dialog, textvariable=status_var, values=["Enabled", "Disabled"], state="readonly")
        status_menu.pack()

        def save():
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

        ttk.Button(dialog, text="Save", command=save).pack(pady=12)

    # --------- reminder loop ---------
    def check_reminders(self):
        now_min = datetime.now().strftime("%Y-%m-%d %H:%M")

        # reset fired list on minute change
        if self.current_minute != now_min:
            self.current_minute = now_min
            self.fired_this_minute.clear()

        # check due
        for r in self.reminders:
            if r["status"] == "Enabled" and r["due_time"] == now_min:
                if r["id"] not in self.fired_this_minute:
                    self.show_notification(r)
                    self.fired_this_minute.add(r["id"])

        self.root.after(1000, self.check_reminders)

    # --------- popup ---------
    def show_notification(self, reminder):
        popup = tk.Toplevel(self.root)
        popup.title(f"Reminder: {reminder['title']}")
        popup.geometry("480x250")
        popup.transient(self.root)
        popup.grab_set()
        popup.attributes("-topmost", True)  # keep on top

        # Sound loop (until dismissed / snoozed)
        if HAS_WINSOUND:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_LOOP)
        else:
            def loop_bell():
                if popup.winfo_exists():
                    self.root.bell()
                    popup.after(1000, loop_bell)
            loop_bell()

        def stop_sound():
            if HAS_WINSOUND:
                winsound.PlaySound(None, winsound.SND_PURGE)

        popup.protocol("WM_DELETE_WINDOW", lambda: (stop_sound(), popup.destroy()))

        ttk.Label(popup, text=reminder["title"], font=("Helvetica", 14, "bold")).pack(pady=10)
        ttk.Label(popup, text=reminder["message"], wraplength=350).pack(pady=5)

        def dismiss():
            stop_sound()
            # advance by recurrence if any
            if reminder["recurrence"] and reminder["recurrence"] != "None":
                new_due = advance_due(reminder["due_time"], reminder["recurrence"])
                update_reminder(reminder["id"], reminder["title"], reminder["message"], new_due, reminder["recurrence"], 1)
                self.refresh_list()
            popup.destroy()

        def snooze(minutes):
            stop_sound()
            new_due = datetime.now() + timedelta(minutes=minutes)
            update_reminder(reminder["id"], reminder["title"], reminder["message"], new_due.strftime("%Y-%m-%d %H:%M"), reminder["recurrence"], 1)
            self.refresh_list()
            popup.destroy()

        btn_row = ttk.Frame(popup)
        btn_row.pack(pady=12)
        ttk.Button(btn_row, text="Dismiss", command=dismiss).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_row, text="Snooze 5 min", command=lambda: snooze(5)).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_row, text="Snooze 10 min", command=lambda: snooze(10)).pack(side=tk.LEFT, padx=10)

# =========================
# Run
# =========================
if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = ReminderApp(root)
    root.mainloop()
