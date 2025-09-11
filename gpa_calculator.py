# GPA Calculator - Calculate Grade Point Average
# A modern interface for students to track their academic performance

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, font
import os
import json
import csv

class EditCourseWindow(tk.Toplevel):
    """A modern pop-up window for editing a course."""
    def __init__(self, app, course_data):
        super().__init__(app.master)
        self.app = app
        self.course_data = course_data
        
        self.transient(app.master)
        self.grab_set()
        self.title("Edit Course")
        self.geometry("1000x1500")
        self.resizable(True, True)
        
        colors = self.app.themes[self.app.current_theme]
        self.configure(bg=colors["frame_bg"])
        
        # Center the dialog on the parent window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"450x400+{x}+{y}")
        
        self._create_widgets()
        self._apply_dialog_theme()
        
        # Focus on the first entry field
        self.course_entry.focus_set()
        self.course_entry.select_range(0, tk.END)
        
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)
    
    def _create_widgets(self):
        # Main container with modern padding
        main_frame = ttk.Frame(self, padding=40, style="Left.TFrame")
        main_frame.pack(fill="both", expand=True)
        
        # Modern header
        header_frame = ttk.Frame(main_frame, style="Left.TFrame")
        header_frame.pack(fill="x", pady=(0, 30))
        
        ttk.Label(header_frame, text="Edit Course", 
                 font=("Inter", 18, "bold"), 
                 style="FormHeader.TLabel").pack(anchor="w")
        
        ttk.Label(header_frame, text="Modify the course details below", 
                 font=("Inter", 11), 
                 style="FormSubheader.TLabel").pack(anchor="w", pady=(5, 0))
        
        # Course Name Field
        course_frame = ttk.Frame(main_frame, style="Left.TFrame")
        course_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(course_frame, text="Course Name", 
                 font=("Inter", 11, "bold"), 
                 style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 8))
        
        self.course_entry = ttk.Entry(course_frame, font=("Inter", 11))
        self.course_entry.pack(fill="x")
        self.course_entry.insert(0, self.course_data['course'])
        
        # Credit Hours Field
        credits_frame = ttk.Frame(main_frame, style="Left.TFrame")
        credits_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(credits_frame, text="Credit Hours", 
                 font=("Inter", 11, "bold"), 
                 style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 8))
        
        self.credits_entry = ttk.Entry(credits_frame, font=("Inter", 11))
        self.credits_entry.pack(fill="x")
        self.credits_entry.insert(0, str(self.course_data['credits']))
        
        # Grade Field
        grade_frame = ttk.Frame(main_frame, style="Left.TFrame")
        grade_frame.pack(fill="x", pady=(0, 30))
        
        ttk.Label(grade_frame, text="Grade", 
                 font=("Inter", 11, "bold"), 
                 style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 8))
        
        self.grade_menu = ttk.Combobox(grade_frame, 
                                     values=list(self.app.GRADE_POINTS.keys()), 
                                     state="readonly", 
                                     font=("Inter", 11))
        self.grade_menu.set(self.course_data['grade'])
        self.grade_menu.pack(fill="x")
        
        # Button frame
        button_frame = ttk.Frame(main_frame, style="Left.TFrame")
        button_frame.pack(fill="x")
        
        # Cancel and Save buttons
        ttk.Button(button_frame, text="Cancel", 
                  command=self.destroy,
                  style="Secondary.TButton").pack(side="right", padx=(10, 0))
        
        ttk.Button(button_frame, text="Save Changes", 
                  command=self.save_changes,
                  style="Primary.TButton").pack(side="right")
    
    def _apply_dialog_theme(self):
        """Apply theme styling specifically for the dialog"""
        colors = self.app.themes[self.app.current_theme]
        
        # Apply the main app's theme to this dialog
        self.app._apply_theme()

    def save_changes(self):
        new_course, new_credits_str, new_grade = self.course_entry.get().strip(), self.credits_entry.get().strip(), self.grade_menu.get().strip()
        if not all((new_course, new_credits_str, new_grade)):
            messagebox.showwarning("Input Error", "All fields are required.", parent=self); return
        try:
            new_credits = float(new_credits_str)
            if new_credits <= 0 or new_credits > 4:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Input Error", "Credit hours must be a positive number or not greater than 4.", parent=self); return
        
        self.course_data.update({'course': new_course, 'credits': new_credits, 'grade': new_grade})
        self.destroy()

class App:
    """The main GPA Calculator application class."""
    CONFIG_FILE = "gpa_config.json"
    GRADE_POINTS = {'A+': 4.0, 'A': 4.0, 'A-': 3.67, 'B+': 3.33, 'B': 3.0, 'B-': 2.67, 'C+': 2.33, 'C': 2.0, 'F': 0.0}

    def __init__(self, master, initial_courses=None):
        self.master = master
        # Initialize courses with provided data or as an empty list
        self.courses = initial_courses or []
        self._setup_theme()
        self._setup_styles()
        self._create_widgets()
        self._apply_theme()
        # Populate the view with initial data if it exists
        self.update_view()

    def _setup_theme(self):
        self.themes = {
            "light": {
                "bg": "#f8fafc", 
                "fg": "#1e293b", 
                "frame_bg": "#ffffff", 
                "border": "#e2e8f0", 
                "entry_bg": "#ffffff", 
                "entry_fg": "#334155", 
                "entry_border": "#cbd5e1",
                "entry_focus": "#3b82f6",
                "button_bg": "#3b82f6", 
                "button_fg": "#ffffff", 
                "button_hover": "#2563eb",
                "button_secondary_bg": "#f1f5f9",
                "button_secondary_fg": "#475569",
                "button_secondary_hover": "#e2e8f0",
                "danger_bg": "#ef4444",
                "danger_hover": "#dc2626",
                "tree_bg": "#ffffff", 
                "tree_fg": "#334155", 
                "tree_head_bg": "#f8fafc", 
                "tree_head_fg": "#1e293b", 
                "tree_selected": "#3b82f6",
                "tree_alternate": "#f8fafc",
                "gpa_fg": "#059669",
                "shadow": "#0000000a"
            },
            "dark": {
                "bg": "#0f172a", 
                "fg": "#e2e8f0", 
                "frame_bg": "#1e293b", 
                "border": "#334155", 
                "entry_bg": "#1e293b", 
                "entry_fg": "#e2e8f0", 
                "entry_border": "#475569",
                "entry_focus": "#60a5fa",
                "button_bg": "#3b82f6", 
                "button_fg": "#ffffff", 
                "button_hover": "#2563eb",
                "button_secondary_bg": "#334155",
                "button_secondary_fg": "#cbd5e1",
                "button_secondary_hover": "#475569",
                "danger_bg": "#ef4444",
                "danger_hover": "#dc2626",
                "tree_bg": "#1e293b", 
                "tree_fg": "#e2e8f0", 
                "tree_head_bg": "#0f172a", 
                "tree_head_fg": "#f1f5f9", 
                "tree_selected": "#3b82f6",
                "tree_alternate": "#334155",
                "gpa_fg": "#34d399",
                "shadow": "#00000020"
            }
        }
        config_path = os.path.join("data", self.CONFIG_FILE)
        try: self.current_theme = json.load(open(config_path, 'r')).get("theme", "light")
        except (FileNotFoundError, json.JSONDecodeError): self.current_theme = "light"

    def _setup_styles(self):
        self.master.title("GPA Calculator")
        self.master.geometry("1200x700")
        self.master.minsize(900, 600)
        
        self.style = ttk.Style(self.master)
        self.style.theme_use('clam')
        
        # Modern entry styling with better spacing and typography
        self.style.configure("TEntry", 
                           borderwidth=2, 
                           relief="solid", 
                           padding=(12, 10), 
                           font=("Inter", 11),
                           insertwidth=2)
        
        # Modern button styling with improved padding
        self.style.configure("TButton", 
                           padding=(16, 12), 
                           relief="flat", 
                           borderwidth=0, 
                           font=("Inter", 10, "bold"))
        
        # Secondary button style
        self.style.configure("Secondary.TButton",
                           padding=(12, 8),
                           relief="flat",
                           borderwidth=0,
                           font=("Inter", 9))
        
        # Danger button style
        self.style.configure("Danger.TButton",
                           padding=(12, 8),
                           relief="flat",
                           borderwidth=0,
                           font=("Inter", 9))
        
        # Modern treeview with better spacing
        self.style.configure("Treeview", 
                           rowheight=36, 
                           font=("Inter", 10),
                           borderwidth=0,
                           relief="flat")
        
        self.style.configure("Treeview.Heading", 
                           font=("Inter", 11, "bold"),
                           padding=(12, 12),
                           relief="flat",
                           borderwidth=0)
        
        # Remove treeview borders for modern look
        self.style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        
        # Modern combobox styling
        self.style.configure("TCombobox",
                           borderwidth=2,
                           relief="solid",
                           padding=(12, 10),
                           font=("Inter", 11))

    def _create_widgets(self):
        # Create main container with better spacing
        main_container = ttk.Frame(self.master)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.left_panel = ttk.Frame(main_container, width=350, style="Left.TFrame")
        self.left_panel.pack(side="left", fill="y", padx=(0, 20))
        self.left_panel.pack_propagate(False)
        
        self.right_panel = ttk.Frame(main_container)
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        self._create_left_panel_widgets()
        self._create_right_panel_widgets()

    def _create_left_panel_widgets(self):
        # Main form container with modern padding
        form = ttk.Frame(self.left_panel, padding=30, style="Left.TFrame")
        form.pack(fill="both", expand=True)
        
        # Modern header section
        header_frame = ttk.Frame(form, style="Left.TFrame")
        header_frame.pack(fill="x", pady=(0, 30))
        
        ttk.Label(header_frame, text="Add Course", 
                 font=("Inter", 20, "bold"), 
                 style="FormHeader.TLabel").pack(anchor="w")
        
        ttk.Label(header_frame, text="Enter course details below", 
                 font=("Inter", 11), 
                 style="FormSubheader.TLabel").pack(anchor="w", pady=(5, 0))
        
        # Course Name Field
        course_frame = ttk.Frame(form, style="Left.TFrame")
        course_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(course_frame, text="Course Name", 
                 font=("Inter", 11, "bold"), 
                 style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 8))
        
        self.course_entry = ttk.Entry(course_frame, font=("Inter", 11))
        self.course_entry.pack(fill="x")
        
        # Credit Hours Field
        credits_frame = ttk.Frame(form, style="Left.TFrame")
        credits_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(credits_frame, text="Credit Hours", 
                 font=("Inter", 11, "bold"), 
                 style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 8))
        
        self.credits_entry = ttk.Entry(credits_frame, font=("Inter", 11))
        self.credits_entry.pack(fill="x")
        
        # Grade Field
        grade_frame = ttk.Frame(form, style="Left.TFrame")
        grade_frame.pack(fill="x", pady=(0, 30))
        
        ttk.Label(grade_frame, text="Grade", 
                 font=("Inter", 11, "bold"), 
                 style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 8))
        
        self.grade_menu = ttk.Combobox(grade_frame, 
                                     values=list(self.GRADE_POINTS.keys()), 
                                     state="readonly", 
                                     font=("Inter", 11))
        self.grade_menu.set("A")
        self.grade_menu.pack(fill="x")
        
        # Add Course Button
        ttk.Button(form, text="Add Course", 
                  command=self.add_course,
                  style="Primary.TButton").pack(fill="x", pady=(10, 0))

    def _create_right_panel_widgets(self):
        # Modern header section with improved spacing
        header = ttk.Frame(self.right_panel)
        header.pack(fill="x", pady=(0, 25))
        
        # Title and GPA display with better typography
        title_frame = ttk.Frame(header)
        title_frame.pack(fill="x")
        
        ttk.Label(title_frame, text="Course Overview", 
                 font=("Inter", 24, "bold"), 
                 style="PageTitle.TLabel").pack(side="left")
        
        # GPA display with modern styling
        gpa_frame = ttk.Frame(title_frame)
        gpa_frame.pack(side="right")
        
        ttk.Label(gpa_frame, text="Current GPA", 
                 font=("Inter", 10), 
                 style="GPALabel.TLabel").pack()
        
        self.gpa_label = ttk.Label(gpa_frame, text="0.00", 
                                  font=("Inter", 28, "bold"), 
                                  style="GPADisplay.TLabel")
        self.gpa_label.pack()
        
        # Modern table container with padding
        table_container = ttk.Frame(self.right_panel, style="TableContainer.TFrame")
        table_container.pack(fill="both", expand=True, pady=(0, 20))
        
        # Treeview with modern styling
        tree_frame = ttk.Frame(table_container)
        tree_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        self.courses_tree = ttk.Treeview(tree_frame, 
                                       columns=('course', 'credits', 'grade'), 
                                       show='headings')
        
        # Configure headings with better text
        self.courses_tree.heading('course', text='Course Name', anchor='w')
        self.courses_tree.heading('credits', text='Credits', anchor='center')
        self.courses_tree.heading('grade', text='Grade', anchor='center')
        
        # Configure columns with better spacing
        self.courses_tree.column('course', anchor='w', minwidth=200)
        self.courses_tree.column('credits', width=120, anchor=tk.CENTER, minwidth=80)
        self.courses_tree.column('grade', width=120, anchor=tk.CENTER, minwidth=80)
        
        self.courses_tree.pack(side="left", fill="both", expand=True)
        
        # Modern scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.courses_tree.yview)
        self.courses_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        self.courses_tree.bind("<Double-1>", self.edit_course)
        
        # Modern action buttons layout
        actions = ttk.Frame(self.right_panel)
        actions.pack(fill="x")
        
        # Left side - destructive actions
        left_actions = ttk.Frame(actions)
        left_actions.pack(side="left")
        
        self.delete_btn = ttk.Button(left_actions, text="Delete Selected", 
                                   command=self.delete_course, 
                                   style="Danger.TButton")
        self.delete_btn.pack(side="left", padx=(0, 10))
        
        self.clear_btn = ttk.Button(left_actions, text="Clear All", 
                                  command=self.clear_all, 
                                  style="Danger.TButton")
        self.clear_btn.pack(side="left")
        
        # Right side - utility actions
        right_actions = ttk.Frame(actions)
        right_actions.pack(side="right")
        
        self.theme_btn = ttk.Button(right_actions, 
                                  command=self._toggle_theme,
                                  style="Secondary.TButton")
        self.theme_btn.pack(side="right", padx=(10, 0))
        
        self.load_btn = ttk.Button(right_actions, text="Load Data", 
                                 command=self.load_courses,
                                 style="Secondary.TButton")
        self.load_btn.pack(side="right", padx=(10, 0))
        
        self.save_btn = ttk.Button(right_actions, text="Save Data", 
                                 command=self.save_courses,
                                 style="Secondary.TButton")
        self.save_btn.pack(side="right", padx=(10, 0))
    
    def add_course(self):
        course = self.course_entry.get().strip()
        credits_str = self.credits_entry.get().strip() 
        grade = self.grade_menu.get().strip()
        
        if not all((course, credits_str, grade)):
            messagebox.showwarning("Input Error", "All fields are required.", parent=self.master)
            return
            
        try:
            credits = float(credits_str)
            if credits <= 0 or credits > 4:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Input Error", "Credit hours must be a positive number or not greater than 4.", parent=self.master)
            return
            
        self.courses.append({'course': course, 'credits': credits, 'grade': grade})
        self.update_view()
        self._clear_form()
    
    def _clear_form(self):
        """Clear the input form and reset focus"""
        self.course_entry.delete(0, tk.END)
        self.credits_entry.delete(0, tk.END)
        self.grade_menu.set("A")
        self.course_entry.focus_set()

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
        # Modified: Prepend 'data/' to the filename
        
        filepath = os.path.join("data", filename)
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f); writer.writerow(['Course', 'Credits', 'Grade'])
                for c in self.courses: writer.writerow([c['course'], c['credits'], c['grade']])
            messagebox.showinfo("Success", "Courses saved successfully.", parent=self.master)
        except Exception as e: messagebox.showerror("Error", f"Failed to save: {e}", parent=self.master)

    def load_courses(self):
        if not (filename := simpledialog.askstring("Load Courses", "Enter filename:", parent=self.master)): return
        fn_csv = f"{filename}.csv" if not filename.endswith('.csv') else filename
        
        # Modified: Construct paths within the 'data' directory
        path_csv = os.path.join("data", fn_csv)
        path_no_ext = os.path.join("data", filename)
        target = path_csv if os.path.exists(path_csv) else path_no_ext if os.path.exists(path_no_ext) else None
        
        if not target: messagebox.showerror("Error", f"File not found: {filename}", parent=self.master); return
        try:
            with open(target, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f); header = next(reader)
                if header != ['Course', 'Credits', 'Grade']: raise ValueError("Invalid file format.")
                self.courses = [{'course': r[0], 'credits': float(r[1]), 'grade': r[2]} for r in reader]
            self.update_view(); messagebox.showinfo("Success", "Courses loaded successfully.", parent=self.master)
        except Exception as e: messagebox.showerror("Error", f"Failed to load file: {e}", parent=self.master)

    def update_view(self):
        for item in self.courses_tree.get_children(): 
            self.courses_tree.delete(item)
            
        for i, c in enumerate(self.courses): 
            tags = (str(id(c)), 'evenrow' if i % 2 == 0 else 'oddrow')
            self.courses_tree.insert('', tk.END, 
                                   values=(c['course'], c['credits'], c['grade']), 
                                   tags=tags)
        
        total_credits = sum(c['credits'] for c in self.courses)
        total_points = sum(self.GRADE_POINTS.get(c['grade'], 0) * c['credits'] for c in self.courses)
        gpa = total_points / total_credits if total_credits > 0 else 0.0
        self.gpa_label.config(text=f"{gpa:.2f}")

    def _apply_theme(self):
        colors = self.themes[self.current_theme]
        
        # Main window and frame styling
        self.master.configure(bg=colors["bg"])
        self.style.configure(".", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("Left.TFrame", background=colors["frame_bg"], relief="flat")
        self.style.configure("TableContainer.TFrame", background=colors["border"], relief="flat")
        
        # Label styling with improved hierarchy
        self.style.configure("TLabel", background=colors["frame_bg"], foreground=colors["fg"])
        self.style.configure("FormHeader.TLabel", background=colors["frame_bg"], foreground=colors["fg"])
        self.style.configure("FormSubheader.TLabel", background=colors["frame_bg"], foreground=colors["fg"])
        self.style.configure("FieldLabel.TLabel", background=colors["frame_bg"], foreground=colors["fg"])
        self.style.configure("PageTitle.TLabel", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("GPALabel.TLabel", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("GPADisplay.TLabel", background=colors["bg"], foreground=colors["gpa_fg"])
        
        # Modern button styling
        # Primary button
        self.style.configure("Primary.TButton", 
                           background=colors["button_bg"], 
                           foreground=colors["button_fg"])
        self.style.map("Primary.TButton", 
                      background=[('active', colors["button_hover"])])
        
        # Secondary button
        self.style.configure("Secondary.TButton", 
                           background=colors["button_secondary_bg"], 
                           foreground=colors["button_secondary_fg"])
        self.style.map("Secondary.TButton", 
                      background=[('active', colors["button_secondary_hover"])])
        
        # Danger button
        self.style.configure("Danger.TButton", 
                           background=colors["danger_bg"], 
                           foreground="white")
        self.style.map("Danger.TButton", 
                      background=[('active', colors["danger_hover"])])
        
        # Default button fallback
        self.style.configure("TButton", 
                           background=colors["button_bg"], 
                           foreground=colors["button_fg"])
        self.style.map("TButton", 
                      background=[('active', colors["button_hover"])])
        
        # Modern entry and combobox styling
        self.style.configure("TEntry", 
                           fieldbackground=colors["entry_bg"], 
                           foreground=colors["entry_fg"], 
                           bordercolor=colors["entry_border"],
                           focuscolor=colors["entry_focus"])
        
        self.style.map("TEntry",
                      bordercolor=[('focus', colors["entry_focus"])])
        
        self.style.configure("TCombobox", 
                           fieldbackground=colors["entry_bg"], 
                           foreground=colors["entry_fg"], 
                           bordercolor=colors["entry_border"])
        
        self.style.map("TCombobox", 
                      fieldbackground=[('readonly', colors["entry_bg"])], 
                      foreground=[('readonly', colors["entry_fg"])],
                      bordercolor=[('focus', colors["entry_focus"])])
        
        # Combobox dropdown styling
        self.master.option_add("*TCombobox*Listbox*Background", colors["entry_bg"])
        self.master.option_add("*TCombobox*Listbox*Foreground", colors["entry_fg"])
        
        # Modern treeview with alternating rows
        self.style.configure("Treeview", 
                           background=colors["tree_bg"], 
                           fieldbackground=colors["tree_bg"], 
                           foreground=colors["tree_fg"])
        
        self.style.configure("Treeview.Heading", 
                           background=colors["tree_head_bg"], 
                           foreground=colors["tree_head_fg"])
        
        # Configure alternating row colors and selection
        self.courses_tree.tag_configure('evenrow', background=colors["tree_bg"])
        self.courses_tree.tag_configure('oddrow', background=colors["tree_alternate"])
        
        self.style.map("Treeview", 
                      background=[('selected', colors["tree_selected"])],
                      foreground=[('selected', 'white')])
        
        # Theme toggle button
        self.theme_btn.configure(text="🌙 Dark" if self.current_theme == "light" else "☀️ Light")

    def _toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        # Modified: Save config file to 'data/'
        config_path = os.path.join("data", self.CONFIG_FILE)
        with open(config_path, 'w') as f: json.dump({"theme": self.current_theme}, f)
        self._apply_theme()

def main(parent, initial_courses=None):
    """
    Launches the GPA Calculator application.

    Args:
        initial_courses (list, optional): A list of course dictionaries to pre-populate the calculator.
                                          Each dictionary should have 'course', 'credits', and 'grade' keys.
                                          Defaults to None.

    Returns:
        list: The final list of course dictionaries after the application window is closed.
    """
    try:
        window = tk.Toplevel(parent)
        app = App(window, initial_courses=initial_courses)
        return window
    except Exception as e:
        messagebox.showerror("Application Error", f"Failed to launch GPA Calculator: {e}", parent=parent)
        return None

if __name__ == "__main__":
    # This block is kept for standalone testing of the module.
    root = tk.Tk()
    # Hide the blank root window when running standalone.
    root.withdraw()
    main(root)
    root.mainloop()
