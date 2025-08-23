import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
from pathlib import Path

DATA_FILE = Path("homework.json")
DATE_FORMAT = "%Y-%m-%d"

# ---------- Data Storage Logic (Unchanged) ----------
def load_tasks():
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

# ---------- Modern GUI Class (Unchanged from previous version) ----------
class HomeworkPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 Homework Planner")
        self.root.geometry("900x650")
        self.root.minsize(750, 550)

        # --- State Management ---
        self.editing_task_index = None # Will store the index of the task being edited

        # --- Color Palette & Fonts ---
        self.BG_PRIMARY = "#0D1117"
        self.BG_SECONDARY = "#161B22"
        self.BORDER_COLOR = "#30363D"
        self.TEXT_PRIMARY = "#C9D1D9"
        self.TEXT_SECONDARY = "#8B949E"
        
        self.ACCENT_BLUE = "#388BFD"
        self.ACCENT_BLUE_HOVER = "#58A6FF"
        self.ACCENT_RED = "#DA3633"
        self.ACCENT_RED_HOVER = "#F85149"
        self.ACCENT_GREEN = "#2EA043"
        self.ACCENT_GREEN_HOVER = "#3FB950"
        self.ACCENT_AMBER = "#D29922"
        self.ACCENT_AMBER_HOVER = "#E7B138"
        self.ACCENT_GREY = "#21262D"
        self.ACCENT_GREY_HOVER = "#30363D"


        self.FONT_LABEL = ("Segoe UI", 10)
        self.FONT_INPUT = ("Segoe UI", 10)
        self.FONT_BUTTON = ("Segoe UI", 10, "bold")

        self.root.configure(bg=self.BG_PRIMARY)
        self.tasks = load_tasks()
        
        self._configure_ttk_styles()
        self._create_widgets()
        self.refresh_table()

    def _configure_ttk_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("Treeview",
                        background=self.BG_SECONDARY,
                        foreground=self.TEXT_PRIMARY,
                        fieldbackground=self.BG_SECONDARY,
                        borderwidth=0,
                        rowheight=25)
        style.map("Treeview", background=[("selected", self.ACCENT_BLUE)])
        
        style.configure("Treeview.Heading",
                        background=self.BG_PRIMARY,
                        foreground=self.TEXT_SECONDARY,
                        font=self.FONT_BUTTON,
                        relief="flat",
                        padding=(10, 5))
        style.map("Treeview.Heading", background=[("active", self.BG_SECONDARY)])

        self.root.option_add("*TCombobox*Listbox*Background", self.BG_SECONDARY)
        self.root.option_add("*TCombobox*Listbox*Foreground", self.TEXT_PRIMARY)
        self.root.option_add("*TCombobox*Listbox*selectBackground", self.ACCENT_BLUE)
        
        style.configure("TCombobox",
                        fieldbackground=self.BG_SECONDARY,
                        background=self.BG_SECONDARY,
                        foreground=self.TEXT_PRIMARY,
                        arrowcolor=self.TEXT_PRIMARY,
                        bordercolor=self.BORDER_COLOR,
                        insertcolor=self.TEXT_PRIMARY,
                        lightcolor=self.BG_SECONDARY,
                        darkcolor=self.BG_SECONDARY)
        style.map("TCombobox", fieldbackground=[("readonly", self.BG_SECONDARY)])
        
        style.configure("Vertical.TScrollbar", background=self.BG_PRIMARY, troughcolor=self.BG_SECONDARY, bordercolor=self.BG_PRIMARY, arrowcolor=self.TEXT_PRIMARY)
        style.map("Vertical.TScrollbar", background=[("active", self.BG_SECONDARY)])


    def _create_widgets(self):
        main_frame = tk.Frame(self.root, bg=self.BG_PRIMARY, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        input_card = tk.Frame(main_frame, bg=self.BG_SECONDARY, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        input_card.pack(fill="x", pady=(0, 20))
        input_frame = tk.Frame(input_card, bg=self.BG_SECONDARY, padx=15, pady=15)
        input_frame.pack(fill="x")
        
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(3, weight=1)

        self._create_labeled_entry(input_frame, "Subject:", 0, 0).bind("<Return>", lambda e: self.title_entry.focus())
        self.subject_entry = self._create_styled_entry(input_frame)
        self.subject_entry.grid(row=0, column=1, sticky="ew", padx=(0, 15))
        
        self._create_labeled_entry(input_frame, "Title:", 0, 2)
        self.title_entry = self._create_styled_entry(input_frame)
        self.title_entry.grid(row=0, column=3, sticky="ew")

        self._create_labeled_entry(input_frame, "Deadline:", 1, 0)
        self.deadline_entry = self._create_styled_entry(input_frame)
        self.deadline_entry.insert(0, datetime.now().strftime(DATE_FORMAT))
        self.deadline_entry.grid(row=1, column=1, sticky="ew", padx=(0, 15))
        
        self._create_labeled_entry(input_frame, "Priority:", 1, 2)
        self.priority_var = tk.StringVar(value="Medium")
        priority_cb = ttk.Combobox(input_frame, textvariable=self.priority_var, values=["Low", "Medium", "High"], state="readonly", font=self.FONT_INPUT, style="TCombobox")
        priority_cb.grid(row=1, column=3, sticky="ew")

        self._create_labeled_entry(input_frame, "Notes:", 2, 0)
        self.notes_entry = self._create_styled_entry(input_frame)
        self.notes_entry.grid(row=2, column=1, columnspan=3, sticky="ew")

        btn_frame = tk.Frame(main_frame, bg=self.BG_PRIMARY)
        btn_frame.pack(fill="x", pady=(0, 20))
        
        # --- Action Buttons ---
        self.add_save_button = self._create_styled_button(btn_frame, "Add Task", self.ACCENT_BLUE, self.ACCENT_BLUE_HOVER, self._commit_task)
        self.add_save_button.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.edit_button = self._create_styled_button(btn_frame, "Load for Edit", self.ACCENT_AMBER, self.ACCENT_AMBER_HOVER, self._load_task_for_edit)
        self.edit_button.pack(side="left", expand=True, fill="x", padx=5)

        self.delete_button = self._create_styled_button(btn_frame, "Delete Selected", self.ACCENT_RED, self.ACCENT_RED_HOVER, self._delete_task)
        self.delete_button.pack(side="left", expand=True, fill="x", padx=5)

        # --- Status Buttons ---
        self.mark_done_button = self._create_styled_button(btn_frame, "Mark as Done", self.ACCENT_GREEN, self.ACCENT_GREEN_HOVER, self._mark_done)
        self.mark_done_button.pack(side="left", expand=True, fill="x", padx=5)

        self.mark_not_done_button = self._create_styled_button(btn_frame, "Mark as Not Done", self.ACCENT_GREY, self.ACCENT_GREY_HOVER, self._mark_not_done)
        self.mark_not_done_button.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # This button is hidden until we are in edit mode
        self.cancel_edit_button = self._create_styled_button(btn_frame, "Cancel Edit", self.ACCENT_GREY, self.ACCENT_GREY_HOVER, self._cancel_edit_mode)
        
        table_card = tk.Frame(main_frame, bg=self.BG_SECONDARY, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        table_card.pack(fill="both", expand=True)
        
        columns = ("Status", "Subject", "Title", "Deadline", "Priority", "Notes")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings")
        self.tree.bind("<Double-1>", lambda e: self._load_task_for_edit()) # Double-click to edit
        
        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True, padx=(1,0), pady=(1,1))
        
        self.tree.column("Status", width=100, anchor="center")
        self.tree.column("Subject", width=150)
        self.tree.column("Title", width=200)
        self.tree.column("Deadline", width=100, anchor="center")
        self.tree.column("Priority", width=100, anchor="center")
        self.tree.column("Notes", width=250)

        for col in columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self._sort_column(_col, False))

        self.tree.tag_configure('oddrow', background=self.BG_SECONDARY)
        self.tree.tag_configure('evenrow', background="#1A202A")
        self.tree.tag_configure('done', foreground=self.TEXT_SECONDARY)


    def _create_labeled_entry(self, parent, text, r, c):
        label = tk.Label(parent, text=text, bg=self.BG_SECONDARY, fg=self.TEXT_SECONDARY, font=self.FONT_LABEL)
        label.grid(row=r, column=c, sticky="w", padx=5, pady=(5, 5))
        return label
        
    def _create_styled_entry(self, parent):
        entry = tk.Entry(parent, bg=self.BG_SECONDARY, fg=self.TEXT_PRIMARY, font=self.FONT_INPUT,
                         insertbackground=self.TEXT_PRIMARY, relief="solid", bd=1,
                         highlightthickness=1, highlightcolor=self.ACCENT_BLUE, highlightbackground=self.BORDER_COLOR)
        entry.bind("<FocusIn>", lambda e: e.widget.config(highlightcolor=self.ACCENT_BLUE))
        entry.bind("<FocusOut>", lambda e: e.widget.config(highlightcolor=self.BORDER_COLOR))
        return entry

    def _create_styled_button(self, parent, text, bg, bg_hover, command):
        btn = tk.Button(parent, text=text, bg=bg, fg="white", activebackground=bg_hover,
                        activeforeground="white", relief="flat", cursor="hand2",
                        font=self.FONT_BUTTON, command=command, pady=5)
        btn.bind("<Enter>", lambda e: e.widget.config(bg=bg_hover))
        btn.bind("<Leave>", lambda e: e.widget.config(bg=bg))
        return btn
    
    def _toggle_buttons_state(self, state):
        """Enable or disable action buttons during edit mode."""
        for button in [self.edit_button, self.delete_button, self.mark_done_button, self.mark_not_done_button]:
            button.config(state=state)

    def _sort_column(self, col, reverse):
        try:
            data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
            data.sort(reverse=reverse)
            for i, item in enumerate(data):
                self.tree.move(item[1], '', i)
            self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))
        except tk.TclError:
            pass

    def refresh_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        priority_map = {"Low": 2, "Medium": 1, "High": 0}
        self.tasks.sort(key=lambda t: (
            t["status"] == "Done",
            datetime.strptime(t["deadline"], DATE_FORMAT),
            priority_map.get(t.get("priority", "Medium"), 1)
        ))

        for i, task in enumerate(self.tasks):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            status_tag = 'done' if task["status"] == "Done" else ''
            
            self.tree.insert("", "end", values=(
                task.get("status", ""), task.get("subject", ""), task.get("title", ""),
                task.get("deadline", ""), task.get("priority", ""), task.get("notes", "")
            ), tags=(tag, status_tag))

    def _commit_task(self):
        subject = self.subject_entry.get().strip()
        title = self.title_entry.get().strip()
        deadline = self.deadline_entry.get().strip()
        
        if not subject or not title:
            messagebox.showerror("Error", "Subject and Title are required.", parent=self.root)
            return
        try:
            datetime.strptime(deadline, DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Error", "Deadline must be in YYYY-MM-DD format.", parent=self.root)
            return

        task_data = {
            "subject": subject, "title": title, "deadline": deadline,
            "priority": self.priority_var.get(), "status": "Not Done",
            "notes": self.notes_entry.get().strip()
        }

        if self.editing_task_index is not None:
            # Save changes to an existing task
            task_data["status"] = self.tasks[self.editing_task_index].get("status", "Not Done") # Preserve status
            self.tasks[self.editing_task_index] = task_data
            self._cancel_edit_mode() # Exit edit mode
        else:
            # Add a new task
            self.tasks.append(task_data)

        save_tasks(self.tasks)
        self.refresh_table()
        self._clear_inputs()

    def _get_selected_task_index(self, show_warning=True):
        selected_item = self.tree.selection()
        if not selected_item:
            if show_warning:
                messagebox.showwarning("No Selection", "Please select a task from the list.", parent=self.root)
            return None
        
        selected_values = self.tree.item(selected_item[0])['values']
        for i, task in enumerate(self.tasks):
            if (task['status'] == selected_values[0] and task['subject'] == selected_values[1] and
                task['title'] == selected_values[2] and task['deadline'] == selected_values[3]):
                return i
        return None

    def _load_task_for_edit(self):
        idx = self._get_selected_task_index()
        if idx is not None:
            self.editing_task_index = idx
            task = self.tasks[idx]
            
            self._clear_inputs()
            self.subject_entry.insert(0, task.get("subject", ""))
            self.title_entry.insert(0, task.get("title", ""))
            self.deadline_entry.insert(0, task.get("deadline", ""))
            self.priority_var.set(task.get("priority", "Medium"))
            self.notes_entry.insert(0, task.get("notes", ""))
            
            # --- Enter Edit Mode ---
            self.add_save_button.config(text="Save Changes")
            self.cancel_edit_button.pack(side="left", expand=True, fill="x", padx=5)
            self._toggle_buttons_state("disabled")
            self.tree.config(selectmode="none") # Disable selection in the list

    def _cancel_edit_mode(self):
        self.editing_task_index = None
        self._clear_inputs()
        
        # --- Exit Edit Mode ---
        self.add_save_button.config(text="Add Task")
        self.cancel_edit_button.pack_forget() # Hide the cancel button
        self._toggle_buttons_state("normal")
        self.tree.config(selectmode="browse") # Re-enable selection

    def _delete_task(self):
        idx = self._get_selected_task_index()
        if idx is not None:
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?", parent=self.root):
                self.tasks.pop(idx)
                save_tasks(self.tasks)
                self.refresh_table()

    def _mark_done(self):
        idx = self._get_selected_task_index()
        if idx is not None:
            self.tasks[idx]["status"] = "Done"
            save_tasks(self.tasks)
            self.refresh_table()

    def _mark_not_done(self):
        idx = self._get_selected_task_index()
        if idx is not None:
            self.tasks[idx]["status"] = "Not Done"
            save_tasks(self.tasks)
            self.refresh_table()

    def _clear_inputs(self):
        self.subject_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)
        self.notes_entry.delete(0, tk.END)
        self.deadline_entry.delete(0, tk.END)
        self.deadline_entry.insert(0, datetime.now().strftime(DATE_FORMAT))
        self.priority_var.set("Medium")
        self.subject_entry.focus()


# --- MODIFIED: Corrected launch logic ---

def main():
    """
    This function is called when imported by main.py.
    It creates a Toplevel window that exists on top of the main application window.
    """
    root = tk.Toplevel()
    app = HomeworkPlanner(root)
    root.grab_set() # Makes the Toplevel window modal

# This block is the entry point when you run `python home_planner.py` directly.
if __name__ == "__main__":
    """
    This block is only executed when the script is run directly.
    It creates the main Tk() window for standalone operation.
    """
    standalone_root = tk.Tk()
    app = HomeworkPlanner(standalone_root)
    standalone_root.mainloop()
