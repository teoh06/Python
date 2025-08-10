# main.py
# This file serves as the main entry point for the TAR UMT Student Assistant App.
# It provides a main menu with links to different features developed by the group members.

import tkinter as tk
from tkinter import messagebox, Toplevel
import sys
import os

# Ensure the main app can find and import other application files.
# This assumes the files are in the same directory.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Import other components here as they become available ---
# For now, we only import the PomodoroTimer.
# The other imports will be uncommented or added by your group members.
try:
    from pomodoro_timer import PomodoroTimer
except ImportError:
    # This handles the case where the file is not yet available,
    # so the app can still run without it.
    PomodoroTimer = None

# --- Custom Button with Hover Effect for a more modern feel ---
class HoverButton(tk.Button):
    """A custom tkinter button that changes color on mouse hover."""
    def __init__(self, master, hover_color, **kwargs):
        super().__init__(master, **kwargs)
        self.hover_color = hover_color
        self.default_color = self["bg"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        """Change color when mouse enters the button."""
        self['background'] = self.hover_color

    def on_leave(self, e):
        """Change back to default color when mouse leaves the button."""
        self['background'] = self.default_color

# --- GUI Class for the Main Menu ---
class StudentAssistantApp(tk.Tk):
    """
    Main application class for the student assistant app.
    It handles the main menu and launches other features.
    """
    def __init__(self):
        super().__init__()
        self.title("TAR UMT Student Assistant App")
        self.geometry("700x500")  # Slightly larger for a better look
        self.resizable(False, False)
        # Use a more modern and deep charcoal background
        self.configure(bg="#282c34")

        # Main frame to hold all content, centered
        main_frame = tk.Frame(self, bg="#282c34")
        main_frame.pack(expand=True, padx=40, pady=40)

        # Main title label with a custom font
        title_label = tk.Label(
            main_frame,
            text="TAR UMT Student Assistant",
            font=("Segoe UI", 28, "bold"), # Segoe UI is a clean, modern font
            fg="#e06c75",  # Vibrant red for the title
            bg="#282c34"
        )
        title_label.pack(pady=(0, 40))

        # Sub-title or welcome message
        subtitle_label = tk.Label(
            main_frame,
            text="Please select an application:",
            font=("Segoe UI", 16),
            fg="#abb2bf", # Light gray for text
            bg="#282c34"
        )
        subtitle_label.pack(pady=(0, 20))

        # Frame for the buttons
        button_frame = tk.Frame(main_frame, bg="#282c34")
        button_frame.pack(pady=10)

        # --- Create buttons for each application ---
        # 1. Study Pomodoro Timer
        # The button is now a custom HoverButton for better aesthetics.
        pomodoro_button = HoverButton(
            button_frame,
            text="Study Pomodoro Timer",
            font=("Segoe UI", 14, "bold"),
            command=self.run_pomodoro_timer,
            bg="#98c379",  # A soft green for the active feature
            hover_color="#7ba269", # Darker green on hover
            fg="#282c34",
            activebackground="#7ba269",
            relief="flat",
            bd=0,
            width=30,
            height=2
        )
        pomodoro_button.pack(pady=15)

        # 2. Placeholder 1 - Homework Planner, etc.
        coming_soon_1 = HoverButton(
            button_frame,
            text="Homework Planner (Coming Soon...)",
            font=("Segoe UI", 14, "bold"),
            command=lambda: self.show_coming_soon("Homework Planner"),
            bg="#5c6370",  # A muted grey for placeholders
            hover_color="#4f555e",
            fg="#abb2bf",
            activebackground="#4f555e",
            relief="flat",
            bd=0,
            width=30,
            height=2
        )
        coming_soon_1.pack(pady=15)

        # 3. Placeholder 2
        coming_soon_2 = HoverButton(
            button_frame,
            text="Grade Calculator (Coming Soon...)",
            font=("Segoe UI", 14, "bold"),
            command=lambda: self.show_coming_soon("Grade Calculator"),
            bg="#5c6370",
            hover_color="#4f555e",
            fg="#abb2bf",
            activebackground="#4f555e",
            relief="flat",
            bd=0,
            width=30,
            height=2
        )
        coming_soon_2.pack(pady=15)

        # 4. Placeholder 3
        coming_soon_3 = HoverButton(
            button_frame,
            text="Timetable (Coming Soon...)",
            font=("Segoe UI", 14, "bold"),
            command=lambda: self.show_coming_soon("Timetable"),
            bg="#5c6370",
            hover_color="#4f555e",
            fg="#abb2bf",
            activebackground="#4f555e",
            relief="flat",
            bd=0,
            width=30,
            height=2
        )
        coming_soon_3.pack(pady=15)


    def run_pomodoro_timer(self):
        """
        Launches the Pomodoro Timer application in a new Toplevel window.
        """
        if PomodoroTimer:
            self.withdraw()
            pomodoro_app = PomodoroTimer()
            # This protocol handles closing the child window and returning to the main menu
            pomodoro_app.protocol("WM_DELETE_WINDOW", lambda: self.show_main_menu(pomodoro_app))
        else:
            messagebox.showerror(
                "Error",
                "The 'pomodoro_timer.py' file could not be found. Please ensure it's in the same directory."
            )

    def show_main_menu(self, app_to_close):
        """
        Destroys the child window and re-shows the main menu.
        """
        app_to_close.destroy()
        self.deiconify()

    def show_coming_soon(self, feature_name):
        """
        Displays a message box for features that are not yet implemented.
        """
        messagebox.showinfo(
            "Coming Soon",
            f"{feature_name} is under development and will be available soon."
        )


# --- Main Execution Block ---
if __name__ == "__main__":
    app = StudentAssistantApp()
    app.mainloop()
