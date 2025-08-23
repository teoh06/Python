import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
from pathlib import Path

DATA_FILE = Path("homework.json")
DATE_FORMAT = "%Y-%m-%d"

# ---------- Data Storage ----------
def load_tasks():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# ---------- Main GUI ----------
class HomeworkPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Homework Planner")
        self.tasks = load_tasks()

        # Input area
        frame = tk.Frame(root)
        frame.pack(pady=10)

        tk.Label(frame, text="Subject:").grid(row=0, column=0)
        self.subject_entry = tk.Entry(frame)
        self.subject_entry.grid(row=0, column=1)

        tk.Label(frame, text="Title:").grid(row=0, column=2)
        self.title_entry = tk.Entry(frame)
        self.title_entry.grid(row=0, column=3)

        tk.Label(frame, text="Deadline:").grid(row=1, column=0)
        self.deadline_entry = tk.Entry(frame)
        self.deadline_entry.insert(0, datetime.now().strftime(DATE_FORMAT))
        self.deadline_entry.grid(row=1, column=1)

        tk.Label(frame, text="Priority:").grid(row=1, column=2)
        self.priority_var = tk.StringVar(value="Medium")
        ttk.Combobox(
            frame, textvariable=self.priority_var, values=["Low", "Medium", "High"], width=7
        ).grid(row=1, column=3)

        tk.Label(frame, text="Notes:").grid(row=2, column=0)
        self.notes_entry = tk.Entry(frame, width=50)
        self.notes_entry.grid(row=2, column=1, columnspan=3)

        tk.Button(frame, text="Add Task", command=self.add_task).grid(row=3, column=0, pady=5)
        tk.Button(frame, text="Delete Selected", command=self.delete_task).grid(row=3, column=1, pady=5)
        tk.Button(frame, text="Mark as Done", command=self.mark_done).grid(row=3, column=2, pady=5)
        tk.Button(frame, text="Mark as Not Done", command=self.mark_not_done).grid(row=3, column=3, pady=5)

        # Table
        columns = ("Subject", "Title", "Deadline", "Priority", "Status", "Notes")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(fill="both", expand=True)

        self.refresh_table()

    def refresh_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        self.tasks.sort(key=lambda t: (
            datetime.strptime(t["deadline"], DATE_FORMAT) if t["deadline"] else datetime.max,
            {"Low": 1, "Medium": 2, "High": 3}[t.get("priority", "Medium")]
        ))

        for task in self.tasks:
            self.tree.insert("", "end", values=(
                task["subject"],
                task["title"],
                task["deadline"],
                task["priority"],
                task["status"],
                task.get("notes", "")
            ))

    def add_task(self):
        subject = self.subject_entry.get().strip()
        title = self.title_entry.get().strip()
        deadline = self.deadline_entry.get().strip()
        priority = self.priority_var.get()
        notes = self.notes_entry.get().strip()

        if not subject or not title:
            messagebox.showerror("Error", "Subject and Title cannot be empty.")
            return

        try:
            datetime.strptime(deadline, DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Error", "Deadline must be in YYYY-MM-DD format.")
            return

        task = {
            "subject": subject,
            "title": title,
            "deadline": deadline,
            "priority": priority,
            "status": "Not Done",
            "notes": notes
        }
        self.tasks.append(task)
        save_tasks(self.tasks)
        self.refresh_table()
        self.clear_inputs()

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = self.tree.index(selected[0])
        self.tasks.pop(idx)
        save_tasks(self.tasks)
        self.refresh_table()

    def mark_done(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = self.tree.index(selected[0])
        self.tasks[idx]["status"] = "Done"
        save_tasks(self.tasks)
        self.refresh_table()

    def mark_not_done(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = self.tree.index(selected[0])
        self.tasks[idx]["status"] = "Not Done"
        save_tasks(self.tasks)
        self.refresh_table()

    def clear_inputs(self):
        self.subject_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)
        self.deadline_entry.delete(0, tk.END)
        self.deadline_entry.insert(0, datetime.now().strftime(DATE_FORMAT))
        self.priority_var.set("Medium")
        self.notes_entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = HomeworkPlanner(root)
    root.mainloop()
