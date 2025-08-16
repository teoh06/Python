import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, font
import os
import json
import csv

class EditCourseWindow(tk.Toplevel):
    """A pop-up window for editing a course."""
    def __init__(self, app, course_data):
        super().__init__(app.master)
        self.app = app
        self.course_data = course_data
        
        self.transient(app.master); self.grab_set(); self.title("Edit Course")
        
        colors = self.app.themes[self.app.current_theme]
        self.configure(bg=colors["frame_bg"])
        
        # Create and layout widgets
        main_frame = ttk.Frame(self, padding=20, style="Left.TFrame")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Edit Course Details", font=("Segoe UI", 14, "bold"), style="TLabel").pack(pady=(0, 20))
        
        # Course Name
        ttk.Label(main_frame, text="Course Name", style="TLabel").pack(fill="x", anchor="w")
        self.course_entry = ttk.Entry(main_frame)
        self.course_entry.pack(fill="x", pady=(5, 15), ipady=4)
        self.course_entry.insert(0, self.course_data['course'])
        
        # Credit Hours
        ttk.Label(main_frame, text="Credit Hours", style="TLabel").pack(fill="x", anchor="w")
        self.credits_entry = ttk.Entry(main_frame)
        self.credits_entry.pack(fill="x", pady=(5, 15), ipady=4)
        self.credits_entry.insert(0, self.course_data['credits'])
        
        # Grade
        ttk.Label(main_frame, text="Grade", style="TLabel").pack(fill="x", anchor="w")
        self.grade_var = tk.StringVar(value=self.course_data['grade'])
        self.grade_menu = ttk.Combobox(main_frame, textvariable=self.grade_var, values=list(self.app.GRADE_POINTS.keys()), state="readonly")
        self.grade_menu.pack(fill="x", pady=5, ipady=4)
        
        ttk.Button(main_frame, text="Save Changes", command=self.save_changes).pack(fill="x", pady=(20, 0), ipady=4)

        self.protocol("WM_DELETE_WINDOW", self.destroy); self.wait_window(self)

    def save_changes(self):
        new_course, new_credits_str, new_grade = self.course_entry.get().strip(), self.credits_entry.get().strip(), self.grade_var.get()
        if not all((new_course, new_credits_str, new_grade)):
            messagebox.showwarning("Input Error", "All fields are required.", parent=self); return
        try:
            new_credits = float(new_credits_str); assert new_credits > 0
        except (ValueError, AssertionError):
            messagebox.showwarning("Input Error", "Credit hours must be a positive number.", parent=self); return
        
        self.course_data.update({'course': new_course, 'credits': new_credits, 'grade': new_grade})
        self.destroy()

class App:
    """The main GPA Calculator application class."""
    CONFIG_FILE = "gpa_config.json"
    GRADE_POINTS = {'A+': 4.0, 'A': 4.0, 'A-': 3.67, 'B+': 3.33, 'B': 3.0, 'B-': 2.67, 'C+': 2.33, 'C': 2.0, 'F': 0.0}

    def __init__(self, master):
        self.master = master
        self.courses = []
        self._setup_theme()
        self._setup_styles()
        self._create_widgets()
        self._apply_theme()

    def _setup_theme(self):
        self.themes = {
            "light": {"bg": "#f0f2f5", "fg": "#1c1e21", "frame_bg": "#ffffff", "border": "#dce1e7", "entry_bg": "#ffffff", "entry_fg": "#1c1e21", "button_bg": "#0078d7", "button_fg": "#ffffff", "button_hover": "#005a9e", "tree_bg": "#ffffff", "tree_fg": "#1c1e21", "tree_head_bg": "#e9ecef", "tree_head_fg": "#495057", "tree_selected": "#0078d7", "gpa_fg": "#0078d7"},
            "dark": {"bg": "#18191a", "fg": "#e4e6eb", "frame_bg": "#242526", "border": "#3a3b3c", "entry_bg": "#3a3b3c", "entry_fg": "#e4e6eb", "button_bg": "#3a3b3c", "button_fg": "#e4e6eb", "button_hover": "#525354", "tree_bg": "#242526", "tree_fg": "#e4e6eb", "tree_head_bg": "#3a3b3c", "tree_head_fg": "#e4e6eb", "tree_selected": "#0078d7", "gpa_fg": "#4dabf7"}
        }
        try: self.current_theme = json.load(open(self.CONFIG_FILE, 'r')).get("theme", "light")
        except (FileNotFoundError, json.JSONDecodeError): self.current_theme = "light"

    def _setup_styles(self):
        self.master.title("Modern GPA Calculator"); self.master.geometry("800x500"); self.master.minsize(700, 450)
        self.style = ttk.Style(self.master); self.style.theme_use('clam')
        self.style.configure("TEntry", borderwidth=1, relief="solid", padding=8, font=("Segoe UI", 10))
        self.style.configure("TButton", padding=8, relief="flat", borderwidth=0, font=("Segoe UI", 10))
        self.style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))
        self.style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    def _create_widgets(self):
        self.left_panel = ttk.Frame(self.master, width=280, style="Left.TFrame")
        self.left_panel.pack(side="left", fill="y", padx=(10, 5), pady=10); self.left_panel.pack_propagate(False)
        self.right_panel = ttk.Frame(self.master); self.right_panel.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        self._create_left_panel_widgets()
        self._create_right_panel_widgets()

    def _create_left_panel_widgets(self):
        form = ttk.Frame(self.left_panel, padding=20, style="Left.TFrame"); form.pack(fill="x", pady=20)
        ttk.Label(form, text="Add a Course", font=("Segoe UI", 14, "bold"), style="TLabel").pack(fill="x", pady=(0, 20))
        ttk.Label(form, text="Course Name", style="TLabel").pack(fill="x", anchor="w"); self.course_entry = ttk.Entry(form); self.course_entry.pack(fill="x", pady=(5, 15), ipady=4)
        ttk.Label(form, text="Credit Hours", style="TLabel").pack(fill="x", anchor="w"); self.credits_entry = ttk.Entry(form); self.credits_entry.pack(fill="x", pady=(5, 15), ipady=4)
        ttk.Label(form, text="Grade", style="TLabel").pack(fill="x", anchor="w"); self.grade_var = tk.StringVar(value="A"); self.grade_menu = ttk.Combobox(form, textvariable=self.grade_var, values=list(self.GRADE_POINTS.keys()), state="readonly"); self.grade_menu.pack(fill="x", pady=5, ipady=4)
        ttk.Button(form, text="✚ Add Course", command=self.add_course).pack(fill="x", pady=(20, 0), ipady=4)

    def _create_right_panel_widgets(self):
        header = ttk.Frame(self.right_panel); header.pack(fill="x", pady=(5, 10))
        ttk.Label(header, text="Your Courses", font=("Segoe UI", 18, "bold"), style="Header.TLabel").pack(side="left")
        self.gpa_label = ttk.Label(header, text="GPA: 0.00", font=("Segoe UI", 14, "bold"), style="GPADisplay.TLabel"); self.gpa_label.pack(side="right")
        
        tree_frame = ttk.Frame(self.right_panel); tree_frame.pack(fill="both", expand=True)
        self.courses_tree = ttk.Treeview(tree_frame, columns=('course', 'credits', 'grade'), show='headings'); self.courses_tree.heading('course', text='Course Name'); self.courses_tree.heading('credits', text='Credits', anchor='center'); self.courses_tree.heading('grade', text='Grade', anchor='center'); self.courses_tree.column('credits', width=100, anchor=tk.CENTER); self.courses_tree.column('grade', width=100, anchor=tk.CENTER); self.courses_tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.courses_tree.yview); self.courses_tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side="right", fill="y")
        self.courses_tree.bind("<Double-1>", self.edit_course)

        actions = ttk.Frame(self.right_panel); actions.pack(fill="x", pady=(10, 0))
        self.delete_btn = ttk.Button(actions, text="🗑️ Delete Selected", command=self.delete_course); self.delete_btn.pack(side="left", padx=(0, 5))
        self.clear_btn = ttk.Button(actions, text="🗑️ Clear All", command=self.clear_all); self.clear_btn.pack(side="left")
        self.theme_btn = ttk.Button(actions, command=self._toggle_theme); self.theme_btn.pack(side="right")
        self.load_btn = ttk.Button(actions, text="📂 Load", command=self.load_courses); self.load_btn.pack(side="right", padx=5)
        self.save_btn = ttk.Button(actions, text="💾 Save", command=self.save_courses); self.save_btn.pack(side="right")
    
    def add_course(self):
        course, credits_str, grade = self.course_entry.get().strip(), self.credits_entry.get().strip(), self.grade_var.get()
        if not all((course, credits_str, grade)): messagebox.showwarning("Input Error", "All fields are required.", parent=self.master); return
        try: credits = float(credits_str); assert credits > 0
        except(ValueError, AssertionError): messagebox.showwarning("Input Error", "Credit hours must be a positive number.", parent=self.master); return
        self.courses.append({'course': course, 'credits': credits, 'grade': grade}); self.update_view()
        self.course_entry.delete(0, tk.END); self.credits_entry.delete(0, tk.END); self.course_entry.focus_set()

    def edit_course(self, event):
        if not (sel_item := self.courses_tree.focus()): return
        course_id = int(self.courses_tree.item(sel_item, 'tags')[0])
        course_to_edit = next((c for c in self.courses if id(c) == course_id), None)
        if course_to_edit: EditCourseWindow(self, course_to_edit); self.update_view()

    def delete_course(self):
        if not self.courses_tree.selection(): messagebox.showwarning("Selection Error", "Please select a course to delete.", parent=self.master); return
        for item_id in self.courses_tree.selection():
            course_id = int(self.courses_tree.item(item_id, 'tags')[0])
            self.courses = [c for c in self.courses if id(c) != course_id]
        self.update_view()

    def clear_all(self):
        if self.courses and messagebox.askyesno("Confirm Clear", "Are you sure you want to delete all courses?", parent=self.master):
            self.courses.clear(); self.update_view()

    def save_courses(self):
        if not (filename := simpledialog.askstring("Save Courses", "Enter filename:", parent=self.master)): return
        if not filename.endswith('.csv'): filename += '.csv'
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f); writer.writerow(['Course', 'Credits', 'Grade'])
                for c in self.courses: writer.writerow([c['course'], c['credits'], c['grade']])
            messagebox.showinfo("Success", "Courses saved successfully.", parent=self.master)
        except Exception as e: messagebox.showerror("Error", f"Failed to save: {e}", parent=self.master)

    def load_courses(self):
        if not (filename := simpledialog.askstring("Load Courses", "Enter filename:", parent=self.master)): return
        fn_csv = f"{filename}.csv" if not filename.endswith('.csv') else filename
        target = fn_csv if os.path.exists(fn_csv) else filename if os.path.exists(filename) else None
        if not target: messagebox.showerror("Error", f"File not found: {filename}", parent=self.master); return
        try:
            with open(target, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f); header = next(reader)
                if header != ['Course', 'Credits', 'Grade']: raise ValueError("Invalid file format.")
                self.courses = [{'course': r[0], 'credits': float(r[1]), 'grade': r[2]} for r in reader]
            self.update_view(); messagebox.showinfo("Success", "Courses loaded successfully.", parent=self.master)
        except Exception as e: messagebox.showerror("Error", f"Failed to load file: {e}", parent=self.master)

    def update_view(self):
        for item in self.courses_tree.get_children(): self.courses_tree.delete(item)
        for c in self.courses: self.courses_tree.insert('', tk.END, values=(c['course'], c['credits'], c['grade']), tags=(id(c),))
        total_credits = sum(c['credits'] for c in self.courses)
        total_points = sum(self.GRADE_POINTS.get(c['grade'], 0) * c['credits'] for c in self.courses)
        gpa = total_points / total_credits if total_credits > 0 else 0.0
        self.gpa_label.config(text=f"GPA: {gpa:.2f}")

    def _apply_theme(self):
        colors = self.themes[self.current_theme]
        self.master.configure(bg=colors["bg"])
        self.style.configure(".", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("Left.TFrame", background=colors["frame_bg"])
        self.style.configure("TLabel", background=colors["frame_bg"])
        self.style.configure("Header.TLabel", background=colors["bg"])
        self.style.configure("GPADisplay.TLabel", background=colors["bg"], foreground=colors["gpa_fg"])
        self.style.configure("TButton", background=colors["button_bg"], foreground=colors["button_fg"])
        self.style.map("TButton", background=[('active', colors["button_hover"])])
        self.style.configure("TEntry", fieldbackground=colors["entry_bg"], foreground=colors["entry_fg"], bordercolor=colors["border"])
        self.master.option_add("*TCombobox*Listbox*Background", colors["entry_bg"]); self.master.option_add("*TCombobox*Listbox*Foreground", colors["entry_fg"])
        self.style.map('TCombobox', fieldbackground=[('readonly', colors["entry_bg"])], foreground=[('readonly', colors["entry_fg"])])
        self.style.configure("Treeview", background=colors["tree_bg"], fieldbackground=colors["tree_bg"], foreground=colors["tree_fg"])
        self.style.configure("Treeview.Heading", background=colors["tree_head_bg"], foreground=colors["tree_head_fg"])
        self.style.map("Treeview", background=[('selected', colors["tree_selected"])])
        self.theme_btn.configure(text="🌙" if self.current_theme == "light" else "☀️")

    def _toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        with open(self.CONFIG_FILE, 'w') as f: json.dump({"theme": self.current_theme}, f)
        self._apply_theme()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
