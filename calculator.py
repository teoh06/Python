import tkinter as tk
from tkinter import messagebox, simpledialog
import os

# Base class for GPA calculation (encapsulation, inheritance)
class GPACalculatorBase:
    GRADE_POINTS = {
        'A+': 4.0, 'A': 4.0, 'A-': 3.67,
        'B+': 3.33, 'B': 3.0, 'B-': 2.67,
        'C+': 2.33, 'C': 2.0, 'F': 0.0
    }

    def __init__(self):
        self.courses = []  # collection of (course, credits, grade)

    def add_course(self, course, credits, grade):
        self.courses.append((course, credits, grade))

    def calculate_gpa(self):
        total_credits = 0
        total_points = 0
        for course, credits, grade in self.courses:
            if grade in self.GRADE_POINTS:
                total_credits += credits
                total_points += self.GRADE_POINTS[grade] * credits
        if total_credits == 0:
            return 0.0
        return total_points / total_credits

    def save_to_file(self, filename):
        with open(filename, 'w') as f:
            for course, credits, grade in self.courses:
                f.write(f"{course},{credits},{grade}\n")

    def load_from_file(self, filename):
        if not os.path.exists(filename):
            return
        with open(filename, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    course, credits, grade = parts
                    try:
                        self.add_course(course, float(credits), grade)
                    except ValueError:
                        continue

# Derived class for GUI (inheritance)
class GPACalculatorGUI(GPACalculatorBase):
    def __init__(self, master):
        super().__init__()
        self.master = master
        master.title("GPA Calculator")
        master.geometry("500x400")

        # GUI widgets
        self.course_label = tk.Label(master, text="Course Name:")
        self.course_label.grid(row=0, column=0)
        self.course_entry = tk.Entry(master)
        self.course_entry.grid(row=0, column=1)

        self.credits_label = tk.Label(master, text="Credit Hours:")
        self.credits_label.grid(row=1, column=0)
        self.credits_entry = tk.Entry(master)
        self.credits_entry.grid(row=1, column=1)

        self.grade_label = tk.Label(master, text="Grade:")
        self.grade_label.grid(row=2, column=0)
        self.grade_entry = tk.Entry(master)
        self.grade_entry.grid(row=2, column=1)

        self.add_button = tk.Button(master, text="Add Course", command=self.add_course_gui)
        self.add_button.grid(row=3, column=0, columnspan=2)

        self.calc_button = tk.Button(master, text="Calculate GPA", command=self.show_gpa)
        self.calc_button.grid(row=4, column=0, columnspan=2)

        self.save_button = tk.Button(master, text="Save Courses", command=self.save_courses)
        self.save_button.grid(row=5, column=0)

        self.load_button = tk.Button(master, text="Load Courses", command=self.load_courses)
        self.load_button.grid(row=5, column=1)

        self.courses_listbox = tk.Listbox(master, width=40)
        self.courses_listbox.grid(row=6, column=0, columnspan=2)

    def add_course_gui(self):
        course = self.course_entry.get().strip()
        credits = self.credits_entry.get().strip()
        grade = self.grade_entry.get().strip().upper()
        # String processing, selection, exception handling
        if not course or not credits or not grade:
            messagebox.showerror("Input Error", "All fields are required.")
            return
        if grade not in self.GRADE_POINTS:
            messagebox.showerror("Input Error", "Invalid grade entered.")
            return
        try:
            credits = float(credits)
        except ValueError:
            messagebox.showerror("Input Error", "Credit hours must be a number.")
            return
        self.add_course(course, credits, grade)
        self.courses_listbox.insert(tk.END, f"{course} ({credits} credits): {grade}")
        self.course_entry.delete(0, tk.END)
        self.credits_entry.delete(0, tk.END)
        self.grade_entry.delete(0, tk.END)

    def show_gpa(self):
        gpa = self.calculate_gpa()
        messagebox.showinfo("GPA Result", f"Your GPA is: {gpa:.2f}")

    def save_courses(self):
        filename = simpledialog.askstring("Save", "Enter filename to save:")
        if filename:
            try:
                self.save_to_file(filename)
                messagebox.showinfo("Saved", "Courses saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

    def load_courses(self):
        filename = simpledialog.askstring("Load", "Enter filename to load:")
        if filename:
            try:
                self.courses.clear()
                self.courses_listbox.delete(0, tk.END)
                self.load_from_file(filename)
                for course, credits, grade in self.courses:
                    self.courses_listbox.insert(tk.END, f"{course} ({credits} credits): {grade}")
                messagebox.showinfo("Loaded", "Courses loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")

# Execution entry point
if __name__ == "__main__":
    # Comments and execution
    root = tk.Tk()
    app = GPACalculatorGUI(root)

    root.mainloop()
