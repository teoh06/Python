# Homework Planner - Organize Your Assignments
# Track subjects, deadlines, and priorities to stay organized
# Added features:
# - Calendar popup with month grid + weekday headers (pure Tkinter)
# - Search filter (Subject/Title/Notes)
# - Overdue highlighting
# - Unique IDs for tasks (backward-compatible with old JSON)
# - Optional Category field
# - Monthly Calendar View window showing tasks per day

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import calendar
import json
import uuid
from pathlib import Path

# Configuration for data storage
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "homework.json"
DATE_FORMAT = "%Y-%m-%d"

# ---------- Data Storage Functions ----------
def ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_tasks():
    ensure_data_dir()
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        tasks = []
    # Backward compatibility: ensure each task has an 'id' and default fields
    changed = False
    for t in tasks:
        if "id" not in t:
            t["id"] = str(uuid.uuid4())
            changed = True
        t.setdefault("category", "")
        t.setdefault("priority", "Medium")
        t.setdefault("status", "Not Done")
        t.setdefault("notes", "")
    if changed:
        save_tasks(tasks)
    return tasks

def save_tasks(tasks):
    ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

# ---------- Calendar Popup (pure Tkinter) ----------
class CalendarPopup(tk.Toplevel):
    """
    A lightweight month-view calendar:
    - shows Mon..Sun headers
    - month navigation
    - clicking a day shows "YYYY-MM-DD (Weekday)" below
    - OK inserts date (YYYY-MM-DD) into target Entry
    """
    def __init__(self, parent, target_entry, theme):
        super().__init__(parent)
        self.configure(bg=theme["BG_PRIMARY"])
        self.title("Select Date")
        self.resizable(False, False)
        self.target_entry = target_entry
        self.theme = theme

        today = datetime.today()
        self.year = today.year
        self.month = today.month
        self.selected_date = None

        container = tk.Frame(self, bg=self.theme["BG_PRIMARY"], padx=12, pady=12)
        container.pack()

        # Header with navigation
        header = tk.Frame(container, bg=self.theme["BG_PRIMARY"])
        header.pack(fill="x", pady=(0, 8))

        prev_btn = tk.Button(
            header, text="◀", command=self._prev_month,
            bg=self.theme["ACCENT_GREY"], fg="white", relief="flat", width=3
        )
        prev_btn.pack(side="left")

        self.header_label = tk.Label(
            header, text="", font=("Segoe UI", 12, "bold"),
            bg=self.theme["BG_PRIMARY"], fg=self.theme["TEXT_PRIMARY"]
        )
        self.header_label.pack(side="left", expand=True)

        next_btn = tk.Button(
            header, text="▶", command=self._next_month,
            bg=self.theme["ACCENT_GREY"], fg="white", relief="flat", width=3
        )
        next_btn.pack(side="right")

        # Weekday headers
        self.grid_frame = tk.Frame(container, bg=self.theme["BG_PRIMARY"])
        self.grid_frame.pack()

        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for c, wd in enumerate(weekdays):
            tk.Label(
                self.grid_frame, text=wd, width=4,
                bg=self.theme["BG_PRIMARY"], fg=self.theme["TEXT_SECONDARY"],
                font=("Segoe UI", 10, "bold")
            ).grid(row=0, column=c, padx=2, pady=4)

        # days grid area
        self.days_frame = tk.Frame(self.grid_frame, bg=self.theme["BG_PRIMARY"])
        self.days_frame.grid(row=1, column=0, columnspan=7)

        # footer
        self.selected_label = tk.Label(
            container, text="No date selected", bg=self.theme["BG_PRIMARY"],
            fg=self.theme["TEXT_SECONDARY"], font=("Segoe UI", 10)
        )
        self.selected_label.pack(pady=(10, 6))

        ok_btn = tk.Button(
            container, text="OK", command=self._apply,
            bg=self.theme["ACCENT_BLUE"], fg="white", relief="flat",
            activebackground=self.theme["ACCENT_BLUE_HOVER"], width=12
        )
        ok_btn.pack()

        self._draw_month()

    def _draw_month(self):
        # header text
        self.header_label.config(text=f"{calendar.month_name[self.month]} {self.year}")

        # clear old day buttons
        for w in self.days_frame.winfo_children():
            w.destroy()

        cal = calendar.Calendar(firstweekday=0)  # Monday=0
        weeks = cal.monthdayscalendar(self.year, self.month)

        for r, week in enumerate(weeks):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(
                        self.days_frame, text="", width=4,
                        bg=self.theme["BG_PRIMARY"]
                    ).grid(row=r, column=c, padx=2, pady=2)
                else:
                    btn = tk.Button(
                        self.days_frame, text=str(day), width=4,
                        bg=self.theme["BG_SECONDARY"], fg=self.theme["TEXT_PRIMARY"],
                        relief="flat",
                        command=lambda d=day: self._pick(d)
                    )
                    btn.grid(row=r, column=c, padx=2, pady=2)

    def _pick(self, d):
        dt = datetime(self.year, self.month, d)
        self.selected_date = dt.strftime(DATE_FORMAT)
        self.selected_label.config(
            text=dt.strftime(f"%Y-%m-%d (%A)")
        )

    def _apply(self):
        if not self.selected_date:
            messagebox.showwarning("No date", "Please select a date.", parent=self)
            return
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, self.selected_date)
        self.destroy()

    def _prev_month(self):
        if self.month == 1:
            self.month, self.year = 12, self.year - 1
        else:
            self.month -= 1
        self._draw_month()

    def _next_month(self):
        if self.month == 12:
            self.month, self.year = 1, self.year + 1
        else:
            self.month += 1
        self._draw_month()

# ---------- Monthly Calendar View ----------
class CalendarView(tk.Toplevel):
    """
    A monthly calendar view that shows the count of tasks on each day.
    - Click a day to list tasks below (Subject / Title / Status)
    - Navigate months
    """
    def __init__(self, parent, tasks, theme):
        super().__init__(parent)
        self.title("Calendar View")
        self.configure(bg=theme["BG_PRIMARY"])
        self.resizable(False, False)
        self.theme = theme
        self.tasks = tasks  # reference to list

        today = date.today()
        self.year = today.year
        self.month = today.month

        outer = tk.Frame(self, bg=self.theme["BG_PRIMARY"], padx=12, pady=12)
        outer.pack()

        header = tk.Frame(outer, bg=self.theme["BG_PRIMARY"])
        header.pack(fill="x")

        tk.Button(
            header, text="◀", width=3, relief="flat",
            bg=self.theme["ACCENT_GREY"], fg="white",
            command=self._prev_month
        ).pack(side="left")

        self.h_label = tk.Label(
            header, text="", bg=self.theme["BG_PRIMARY"],
            fg=self.theme["TEXT_PRIMARY"], font=("Segoe UI", 12, "bold")
        )
        self.h_label.pack(side="left", expand=True)

        tk.Button(
            header, text="▶", width=3, relief="flat",
            bg=self.theme["ACCENT_GREY"], fg="white",
            command=self._next_month
        ).pack(side="right")

        # 修改网格布局配置
        grid = tk.Frame(outer, bg=self.theme["BG_PRIMARY"])
        grid.pack(pady=(8, 8))
        
        # 确保所有列宽度相等
        for i in range(7):
            grid.grid_columnconfigure(i, weight=1, minsize=120)

        # weekday headers
        for c, wd in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            tk.Label(grid, text=wd, width=12, bg=self.theme["BG_PRIMARY"],
                     fg=self.theme["TEXT_SECONDARY"],
                     font=("Segoe UI", 10, "bold")).grid(row=0, column=c, padx=2, pady=4, sticky="nsew")

        self.cells_frame = tk.Frame(grid, bg=self.theme["BG_PRIMARY"])
        self.cells_frame.grid(row=1, column=0, columnspan=7)

        # 确保单元格行高一致
        for i in range(6):  # 日历最多6行
            self.cells_frame.grid_rowconfigure(i, minsize=70)
        for i in range(7):  # 7列
            self.cells_frame.grid_columnconfigure(i, minsize=120)

        # task list area
        self.list_label = tk.Label(outer, text="Tasks on selected day",
                                   bg=self.theme["BG_PRIMARY"], fg=self.theme["TEXT_SECONDARY"])
        self.list_label.pack(anchor="w")
        self.listbox = tk.Listbox(outer, width=84, height=8, bg=self.theme["BG_SECONDARY"],
                                  fg=self.theme["TEXT_PRIMARY"], selectmode="browse")
        self.listbox.pack(fill="x")

        self._draw_month()

    def _draw_month(self):
        self.h_label.config(text=f"{calendar.month_name[self.month]} {self.year}")
        for w in self.cells_frame.winfo_children():
            w.destroy()

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.year, self.month)

        for r, week in enumerate(weeks):
            for c, d in enumerate(week):
                frame = tk.Frame(self.cells_frame, bg=self.theme["BG_SECONDARY"], bd=1, relief="solid")
                frame.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
                
                # 移除这两行，让单元格跟随grid配置
                # frame.grid_propagate(False)
                # frame.config(width=120, height=70)

                if d == 0:
                    continue

                # date label
                tk.Label(frame, text=str(d), anchor="w",
                         bg=self.theme["BG_SECONDARY"], fg=self.theme["TEXT_PRIMARY"]
                         ).pack(anchor="nw", padx=4, pady=2)

                # count tasks
                date_str = f"{self.year:04d}-{self.month:02d}-{d:02d}"
                day_tasks = [t for t in self.tasks if t.get("deadline") == date_str]

                # show up to 2 titles
                for t in day_tasks[:2]:
                    small = f"· {t.get('subject','')} - {t.get('title','')[:14]}"
                    tk.Label(frame, text=small, anchor="w",
                             bg=self.theme["BG_SECONDARY"], fg=self.theme["TEXT_SECONDARY"]
                             ).pack(anchor="w", padx=6)

                # button to select day
                tk.Button(frame, text="View", relief="flat",
                          bg=self.theme["ACCENT_BLUE"], fg="white",
                          activebackground=self.theme["ACCENT_BLUE_HOVER"],
                          command=lambda ds=date_str: self._list_day(ds)
                          ).pack(anchor="se", padx=4, pady=4)

    def _list_day(self, date_str):
        self.list_label.config(text=f"Tasks on {date_str}")
        self.listbox.delete(0, tk.END)
        items = []
        for t in self.tasks:
            if t.get("deadline") == date_str:
                items.append(f"[{t.get('status','Not Done')}] {t.get('subject','')} - {t.get('title','')}")
        if not items:
            self.listbox.insert(tk.END, "No tasks.")
        else:
            for it in items:
                self.listbox.insert(tk.END, it)

    def _prev_month(self):
        if self.month == 1:
            self.month, self.year = 12, self.year - 1
        else:
            self.month -= 1
        self._draw_month()

    def _next_month(self):
        if self.month == 12:
            self.month, self.year = 1, self.year + 1
        else:
            self.month += 1
        self._draw_month()

# ---------- Modern GUI Class ----------
class TaskListWindow(tk.Toplevel):
    def __init__(self, parent, tasks, status, theme):
        super().__init__(parent)
        self.title(f"{status} Tasks")
        self.configure(bg=theme["BG_PRIMARY"])
        self.geometry("800x500")
        
        # 主框架
        main_frame = tk.Frame(self, bg=theme["BG_PRIMARY"], padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # 表格
        table_card = tk.Frame(main_frame, bg=theme["BG_SECONDARY"],
                            highlightbackground=theme["BORDER_COLOR"], highlightthickness=1)
        table_card.pack(fill="both", expand=True)

        columns = ("Status", "Subject", "Title", "Category", "Deadline", "Priority", "Notes")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", selectmode="browse")

        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=(1, 1))

        # 设置列宽
        self.tree.column("Status", width=90, anchor="center")
        self.tree.column("Subject", width=140)
        self.tree.column("Title", width=220)
        self.tree.column("Category", width=110, anchor="center")
        self.tree.column("Deadline", width=110, anchor="center")
        self.tree.column("Priority", width=90, anchor="center")
        self.tree.column("Notes", width=300)

        for col in columns:
            self.tree.heading(col, text=col)

        # 样式设置
        self.tree.tag_configure('oddrow', background=theme["BG_SECONDARY"])
        self.tree.tag_configure('evenrow', background="#1A202A")
        self.tree.tag_configure('done', foreground=theme["TEXT_SECONDARY"])
        self.tree.tag_configure('overdue', foreground=theme["ACCENT_RED"])

        # 填充数据
        filtered_tasks = [t for t in tasks if t.get("status") == status]
        for i, task in enumerate(filtered_tasks):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            status_text = "✅ Done" if task.get("status") == "Done" else "❌ Not Done"
            
            self.tree.insert("", "end", values=(
                status_text, task.get("subject", ""), task.get("title", ""),
                task.get("category", ""), task.get("deadline", ""), task.get("priority", ""),
                task.get("notes", "")
            ), tags=(tag,))

class HomeworkPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 Homework Planner")
        self.root.geometry("1000x720")
        self.root.minsize(850, 600)

        # --- Theme ---
        self.theme = {
            "BG_PRIMARY": "#0D1117",
            "BG_SECONDARY": "#161B22",
            "BORDER_COLOR": "#30363D",
            "TEXT_PRIMARY": "#C9D1D9",
            "TEXT_SECONDARY": "#8B949E",
            "ACCENT_BLUE": "#388BFD",
            "ACCENT_BLUE_HOVER": "#58A6FF",
            "ACCENT_RED": "#DA3633",
            "ACCENT_RED_HOVER": "#F85149",
            "ACCENT_GREEN": "#2EA043",
            "ACCENT_GREEN_HOVER": "#3FB950",
            "ACCENT_AMBER": "#D29922",
            "ACCENT_AMBER_HOVER": "#E7B138",
            "ACCENT_GREY": "#21262D",
            "ACCENT_GREY_HOVER": "#30363D",
        }

        self.FONT_LABEL = ("Segoe UI", 10)
        self.FONT_INPUT = ("Segoe UI", 10)
        self.FONT_BUTTON = ("Segoe UI", 10, "bold")

        self.root.configure(bg=self.theme["BG_PRIMARY"])
        self.tasks = load_tasks()
        self.filtered_tasks = list(self.tasks)  # for search/filter
        self.editing_task_index = None  # index in self.tasks when editing

        self._configure_ttk_styles()
        self._create_widgets()
        self.refresh_table()

    def _configure_ttk_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("Treeview",
                        background=self.theme["BG_SECONDARY"],
                        foreground=self.theme["TEXT_PRIMARY"],
                        fieldbackground=self.theme["BG_SECONDARY"],
                        borderwidth=0,
                        rowheight=26)
        style.map("Treeview", background=[("selected", self.theme["ACCENT_BLUE"])])

        style.configure("Treeview.Heading",
                        background=self.theme["BG_PRIMARY"],
                        foreground=self.theme["TEXT_SECONDARY"],
                        font=self.FONT_BUTTON,
                        relief="flat",
                        padding=(10, 5))
        style.map("Treeview.Heading", background=[("active", self.theme["BG_SECONDARY"])])

        self.root.option_add("*TCombobox*Listbox*Background", self.theme["BG_SECONDARY"])
        self.root.option_add("*TCombobox*Listbox*Foreground", self.theme["TEXT_PRIMARY"])
        self.root.option_add("*TCombobox*Listbox*selectBackground", self.theme["ACCENT_BLUE"])

        style.configure("TCombobox",
                        fieldbackground=self.theme["BG_SECONDARY"],
                        background=self.theme["BG_SECONDARY"],
                        foreground=self.theme["TEXT_PRIMARY"],
                        arrowcolor=self.theme["TEXT_PRIMARY"],
                        bordercolor=self.theme["BORDER_COLOR"],
                        insertcolor=self.theme["TEXT_PRIMARY"],
                        lightcolor=self.theme["BG_SECONDARY"],
                        darkcolor=self.theme["BG_SECONDARY"])
        style.map("TCombobox", fieldbackground=[("readonly", self.theme["BG_SECONDARY"])])

        style.configure("Vertical.TScrollbar",
                        background=self.theme["BG_PRIMARY"],
                        troughcolor=self.theme["BG_SECONDARY"],
                        bordercolor=self.theme["BG_PRIMARY"],
                        arrowcolor=self.theme["TEXT_PRIMARY"])
        style.map("Vertical.TScrollbar", background=[("active", self.theme["BG_SECONDARY"])])

    def _create_widgets(self):
        main_frame = tk.Frame(self.root, bg=self.theme["BG_PRIMARY"], padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # ---------- Input Card ----------
        input_card = tk.Frame(main_frame, bg=self.theme["BG_SECONDARY"],
                              highlightbackground=self.theme["BORDER_COLOR"], highlightthickness=1)
        input_card.pack(fill="x", pady=(0, 16))
        input_frame = tk.Frame(input_card, bg=self.theme["BG_SECONDARY"], padx=15, pady=15)
        input_frame.pack(fill="x")

        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(3, weight=1)
        input_frame.grid_columnconfigure(5, weight=1)

        self._create_labeled_entry(input_frame, "Subject:", 0, 0)
        self.subject_entry = self._create_styled_entry(input_frame)
        self.subject_entry.grid(row=0, column=1, sticky="ew", padx=(0, 15))

        self._create_labeled_entry(input_frame, "Title:", 0, 2)
        self.title_entry = self._create_styled_entry(input_frame)
        self.title_entry.grid(row=0, column=3, sticky="ew", padx=(0, 15))

        self._create_labeled_entry(input_frame, "Category:", 0, 4)
        self.category_var = tk.StringVar(value="")
        self.category_cb = ttk.Combobox(
            input_frame, textvariable=self.category_var,
            values=["", "Math", "Science", "English", "History", "Computer", "Other"],
            state="readonly", font=self.FONT_INPUT, style="TCombobox"
        )
        self.category_cb.grid(row=0, column=5, sticky="ew")

        # Deadline input with spinboxes
        self._create_labeled_entry(input_frame, "Deadline:", 1, 0)
        
        # Create frame for date spinboxes
        date_frame = tk.Frame(input_frame, bg=self.theme["BG_SECONDARY"])
        date_frame.grid(row=1, column=1, sticky="ew", padx=(0, 15))
        
        # Year spinbox
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        year_sb = ttk.Spinbox(date_frame, from_=1900, to=2100, width=6,
                             textvariable=self.year_var)
        year_sb.pack(side="left", padx=2)
        
        tk.Label(date_frame, text="-", bg=self.theme["BG_SECONDARY"],
                fg=self.theme["TEXT_PRIMARY"]).pack(side="left")
        
        # Month spinbox
        self.month_var = tk.StringVar(value=str(datetime.now().month))
        month_sb = ttk.Spinbox(date_frame, from_=1, to=12, width=4,
                              textvariable=self.month_var)
        month_sb.pack(side="left", padx=2)
        
        tk.Label(date_frame, text="-", bg=self.theme["BG_SECONDARY"],
                fg=self.theme["TEXT_PRIMARY"]).pack(side="left")
        
        # Day spinbox
        self.day_var = tk.StringVar(value=str(datetime.now().day))
        day_sb = ttk.Spinbox(date_frame, from_=1, to=31, width=4,
                            textvariable=self.day_var)
        day_sb.pack(side="left", padx=2)

        # Remove calendar popup button and its references
        self._create_labeled_entry(input_frame, "Priority:", 1, 2)
        self.priority_var = tk.StringVar(value="Medium")
        priority_cb = ttk.Combobox(
            input_frame, textvariable=self.priority_var,
            values=["Low", "Medium", "High"], state="readonly",
            font=self.FONT_INPUT, style="TCombobox"
        )
        priority_cb.grid(row=1, column=3, sticky="ew", padx=(0, 15))

        self._create_labeled_entry(input_frame, "Notes:", 2, 0)
        self.notes_entry = self._create_styled_entry(input_frame)
        self.notes_entry.grid(row=2, column=1, columnspan=5, sticky="ew")

        # ---------- Actions ----------
        btn_frame = tk.Frame(main_frame, bg=self.theme["BG_PRIMARY"])
        btn_frame.pack(fill="x", pady=(0, 12))

        self.add_save_button = self._create_styled_button(
            btn_frame, "Add Task", self.theme["ACCENT_BLUE"], self.theme["ACCENT_BLUE_HOVER"], self._commit_task
        )
        self.add_save_button.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.edit_button = self._create_styled_button(
            btn_frame, "Load for Edit", self.theme["ACCENT_AMBER"], self.theme["ACCENT_AMBER_HOVER"], self._load_task_for_edit
        )
        self.edit_button.pack(side="left", expand=True, fill="x", padx=5)

        self.delete_button = self._create_styled_button(
            btn_frame, "Delete Selected", self.theme["ACCENT_RED"], self.theme["ACCENT_RED_HOVER"], self._delete_task
        )
        self.delete_button.pack(side="left", expand=True, fill="x", padx=5)

        self.mark_done_button = self._create_styled_button(
            btn_frame, "Mark as Done", self.theme["ACCENT_GREEN"], self.theme["ACCENT_GREEN_HOVER"], self._mark_done
        )
        self.mark_done_button.pack(side="left", expand=True, fill="x", padx=5)

        self.mark_not_done_button = self._create_styled_button(
            btn_frame, "Mark as Not Done", self.theme["ACCENT_GREY"], self.theme["ACCENT_GREY_HOVER"], self._mark_not_done
        )
        self.mark_not_done_button.pack(side="left", expand=True, fill="x", padx=5)

        # Calendar view + Cancel edit (hidden initially)
        btn_frame2 = tk.Frame(main_frame, bg=self.theme["BG_PRIMARY"])
        btn_frame2.pack(fill="x", pady=(0, 12))

        self.list_done_button = self._create_styled_button(
            btn_frame2, "List Done", self.theme["ACCENT_GREEN"], self.theme["ACCENT_GREEN_HOVER"],
            self._list_done_tasks
        )
        self.list_done_button.pack(side="left", expand=True, fill="x", padx=5)

        self.list_not_done_button = self._create_styled_button(
            btn_frame2, "List Not Done", self.theme["ACCENT_RED"], self.theme["ACCENT_RED_HOVER"],
            self._list_not_done_tasks
        )
        self.list_not_done_button.pack(side="left", expand=True, fill="x", padx=5)

        self.calview_button = self._create_styled_button(
            btn_frame2, "Calendar View", self.theme["ACCENT_BLUE"], self.theme["ACCENT_BLUE_HOVER"],
            lambda: CalendarView(self.root, self.tasks, self.theme)
        )
        self.calview_button.pack(side="left", expand=True, fill="x", padx=5)

        self.cancel_edit_button = self._create_styled_button(
            btn_frame, "Cancel Edit", self.theme["ACCENT_GREY"], self.theme["ACCENT_GREY_HOVER"], self._cancel_edit_mode
        )

        # ---------- Search Bar ----------
        search_card = tk.Frame(main_frame, bg=self.theme["BG_SECONDARY"],
                               highlightbackground=self.theme["BORDER_COLOR"], highlightthickness=1)
        search_card.pack(fill="x", pady=(0, 12))
        search_frame = tk.Frame(search_card, bg=self.theme["BG_SECONDARY"], padx=12, pady=8)
        search_frame.pack(fill="x")

        tk.Label(search_frame, text="Search:", bg=self.theme["BG_SECONDARY"], fg=self.theme["TEXT_SECONDARY"]
                 ).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     bg=self.theme["BG_SECONDARY"], fg=self.theme["TEXT_PRIMARY"],
                                     insertbackground=self.theme["TEXT_PRIMARY"], relief="solid", bd=1,
                                     highlightthickness=1, highlightcolor=self.theme["ACCENT_BLUE"],
                                     highlightbackground=self.theme["BORDER_COLOR"])
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(8, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self._apply_search())

        clear_btn = self._create_styled_button(
            search_frame, "Clear", self.theme["ACCENT_GREY"], self.theme["ACCENT_GREY_HOVER"],
            self._clear_search
        )
        clear_btn.pack(side="left")

        # ---------- Table ----------
        table_card = tk.Frame(main_frame, bg=self.theme["BG_SECONDARY"],
                              highlightbackground=self.theme["BORDER_COLOR"], highlightthickness=1)
        table_card.pack(fill="both", expand=True)

        columns = ("Status", "Subject", "Title", "Category", "Deadline", "Priority", "Notes")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", selectmode="browse")
        self.tree.bind("<Double-1>", lambda e: self._load_task_for_edit())

        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=(1, 1))

        # column widths
        self.tree.column("Status", width=90, anchor="center")
        self.tree.column("Subject", width=140)
        self.tree.column("Title", width=220)
        self.tree.column("Category", width=110, anchor="center")
        self.tree.column("Deadline", width=110, anchor="center")
        self.tree.column("Priority", width=90, anchor="center")
        self.tree.column("Notes", width=300)

        for col in columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self._sort_column(_col, False))

        # row styles
        self.tree.tag_configure('oddrow', background=self.theme["BG_SECONDARY"])
        self.tree.tag_configure('evenrow', background="#1A202A")
        self.tree.tag_configure('done', foreground=self.theme["TEXT_SECONDARY"])
        self.tree.tag_configure('overdue', foreground=self.theme["ACCENT_RED"])

    # ---------- helpers / widgets ----------
    def _create_labeled_entry(self, parent, text, r, c):
        label = tk.Label(parent, text=text, bg=self.theme["BG_SECONDARY"], fg=self.theme["TEXT_SECONDARY"], font=self.FONT_LABEL)
        label.grid(row=r, column=c, sticky="w", padx=5, pady=(5, 5))
        return label

    def _create_styled_entry(self, parent):
        entry = tk.Entry(parent, bg=self.theme["BG_SECONDARY"], fg=self.theme["TEXT_PRIMARY"], font=self.FONT_INPUT,
                         insertbackground=self.theme["TEXT_PRIMARY"], relief="solid", bd=1,
                         highlightthickness=1, highlightcolor=self.theme["ACCENT_BLUE"], highlightbackground=self.theme["BORDER_COLOR"])
        entry.bind("<FocusIn>", lambda e: e.widget.config(highlightcolor=self.theme["ACCENT_BLUE"]))
        entry.bind("<FocusOut>", lambda e: e.widget.config(highlightcolor=self.theme["BORDER_COLOR"]))
        return entry

    def _create_styled_button(self, parent, text, bg, bg_hover, command):
        btn = tk.Button(parent, text=text, bg=bg, fg="white", activebackground=bg_hover,
                        activeforeground="white", relief="flat", cursor="hand2",
                        font=self.FONT_BUTTON, command=command, pady=5)
        btn.bind("<Enter>", lambda e: e.widget.config(bg=bg_hover))
        btn.bind("<Leave>", lambda e: e.widget.config(bg=bg))
        return btn

    def _toggle_buttons_state(self, state):
        for button in [self.edit_button, self.delete_button, self.mark_done_button, self.mark_not_done_button]:
            button.config(state=state)

    # ---------- sorting / search ----------
    def _sort_column(self, col, reverse):
        try:
            data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
            data.sort(reverse=reverse)
            for i, item in enumerate(data):
                self.tree.move(item[1], '', i)
            self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))
        except tk.TclError:
            pass

    def _apply_search(self):
        query = self.search_var.get().strip().lower()
        if not query:
            self.filtered_tasks = list(self.tasks)
        else:
            def match(t):
                return any(
                    query in str(t.get(k, "")).lower()
                    for k in ("subject", "title", "notes", "category", "priority", "status")
                )
            self.filtered_tasks = [t for t in self.tasks if match(t)]
        self.refresh_table()

    def _clear_search(self):
        self.search_var.set("")
        self.filtered_tasks = list(self.tasks)
        self.refresh_table()

    # ---------- table refresh ----------
    def refresh_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        # sort by: Done last, deadline, priority
        priority_map = {"Low": 2, "Medium": 1, "High": 0}

        def safe_dt(s):
            try:
                return datetime.strptime(s, DATE_FORMAT)
            except Exception:
                return datetime.max

        self.filtered_tasks.sort(key=lambda t: (
            t.get("status") == "Done",
            safe_dt(t.get("deadline", "9999-12-31")),
            priority_map.get(t.get("priority", "Medium"), 1)
        ))

        today = date.today()
        for i, task in enumerate(self.filtered_tasks):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            status_tag = 'done' if task.get("status") == "Done" else ''
            
            # 添加状态图标
            status_text = "✅ Done" if task.get("status") == "Done" else "❌ Not Done"

            # overdue?
            over_tag = ''
            try:
                d = datetime.strptime(task.get("deadline", ""), DATE_FORMAT).date()
                if task.get("status") != "Done" and d < today:
                    over_tag = 'overdue'
            except Exception:
                pass

            tags = tuple(t for t in (tag, status_tag, over_tag) if t)

            # use iid=task['id'] for reliable selection
            self.tree.insert("", "end", iid=task.get("id"), values=(
                status_text, task.get("subject", ""), task.get("title", ""),
                task.get("category", ""), task.get("deadline", ""), task.get("priority", ""),
                task.get("notes", "")
            ), tags=tags)

    # ---------- CRUD ----------
    def _commit_task(self):
        subject = self.subject_entry.get().strip()
        title = self.title_entry.get().strip()
        
        # Get date from spinboxes
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            deadline = f"{year:04d}-{month:02d}-{day:02d}"
            # Validate date
            datetime.strptime(deadline, DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid input！", parent=self.root)
            return

        if not subject or not title:
            messagebox.showerror("Error", "Subject and Title are required.", parent=self.root)
            return

        task_data = {
            "subject": subject,
            "title": title,
            "deadline": deadline,
            "category": self.category_var.get().strip(),
            "priority": self.priority_var.get(),
            "notes": self.notes_entry.get().strip()
        }

        if self.editing_task_index is not None:
            # update existing (preserve id & status)
            task_data["id"] = self.tasks[self.editing_task_index].get("id")
            task_data["status"] = self.tasks[self.editing_task_index].get("status", "Not Done")
            self.tasks[self.editing_task_index] = task_data
            self._cancel_edit_mode()
        else:
            # new task
            task_data["id"] = str(uuid.uuid4())
            task_data["status"] = "Not Done"
            self.tasks.append(task_data)

        save_tasks(self.tasks)
        self.filtered_tasks = list(self.tasks)
        self.refresh_table()
        self._clear_inputs()

    def _get_selected_task_id(self, show_warning=True):
        selected_item = self.tree.selection()
        if not selected_item:
            if show_warning:
                messagebox.showwarning("No Selection", "Please select a task from the list.", parent=self.root)
            return None
        return selected_item[0]

    def _find_task_index_by_id(self, tid):
        for i, t in enumerate(self.tasks):
            if t.get("id") == tid:
                return i
        return None

    def _load_task_for_edit(self):
        tid = self._get_selected_task_id()
        if not tid:
            return
        idx = self._find_task_index_by_id(tid)
        if idx is None:
            return
        self.editing_task_index = idx
        task = self.tasks[idx]

        self._clear_inputs()
        self.subject_entry.insert(0, task.get("subject", ""))
        self.title_entry.insert(0, task.get("title", ""))
        
        # Set date spinboxes from task deadline
        try:
            deadline_date = datetime.strptime(task.get("deadline", ""), DATE_FORMAT)
            self.year_var.set(str(deadline_date.year))
            self.month_var.set(str(deadline_date.month))
            self.day_var.set(str(deadline_date.day))
        except ValueError:
            today = datetime.now()
            self.year_var.set(str(today.year))
            self.month_var.set(str(today.month))
            self.day_var.set(str(today.day))
            
        self.category_var.set(task.get("category", ""))
        self.priority_var.set(task.get("priority", "Medium"))
        self.notes_entry.insert(0, task.get("notes", ""))

        self.add_save_button.config(text="Save Changes")
        self.cancel_edit_button.pack(side="left", expand=True, fill="x", padx=5)
        self._toggle_buttons_state("disabled")
        self.tree.config(selectmode="none")

    def _cancel_edit_mode(self):
        self.editing_task_index = None
        self._clear_inputs()
        self.add_save_button.config(text="Add Task")
        self.cancel_edit_button.pack_forget()
        self._toggle_buttons_state("normal")
        self.tree.config(selectmode="browse")

    def _delete_task(self):
        tid = self._get_selected_task_id()
        if not tid:
            return
        idx = self._find_task_index_by_id(tid)
        if idx is not None:
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?", parent=self.root):
                self.tasks.pop(idx)
                save_tasks(self.tasks)
                self.filtered_tasks = list(self.tasks)
                self.refresh_table()

    def _mark_done(self):
        tid = self._get_selected_task_id()
        if not tid:
            return
        idx = self._find_task_index_by_id(tid)
        if idx is not None:
            self.tasks[idx]["status"] = "Done"
            save_tasks(self.tasks)
            self.refresh_table()

    def _mark_not_done(self):
        tid = self._get_selected_task_id()
        if not tid:
            return
        idx = self._find_task_index_by_id(tid)
        if idx is not None:
            self.tasks[idx]["status"] = "Not Done"
            save_tasks(self.tasks)
            self.refresh_table()

    def _list_done_tasks(self):
        TaskListWindow(self.root, self.tasks, "Done", self.theme)

    def _list_not_done_tasks(self):
        TaskListWindow(self.root, self.tasks, "Not Done", self.theme)

    def _clear_inputs(self):
        self.subject_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)
        self.notes_entry.delete(0, tk.END)
        
        # Reset date spinboxes to current date
        today = datetime.now()
        self.year_var.set(str(today.year))
        self.month_var.set(str(today.month))
        self.day_var.set(str(today.day))
        
        self.priority_var.set("Medium")
        self.category_var.set("")
        self.subject_entry.focus()

# --- Entry point ---
def main(parent=None):
    if parent is None:
        root = tk.Tk()
        app = HomeworkPlanner(root)
        root.mainloop()
        return root
    else:
        win = tk.Toplevel(parent)
        app = HomeworkPlanner(win)
        return win



if __name__ == "__main__":
    main()

