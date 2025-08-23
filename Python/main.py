# Student Assistant Program - Main Launcher
# This is the central hub that launches all student productivity tools

import tkinter as tk
from tkinter import font, messagebox
import random

# Import all student applications
import pomodoro_timer    # Focus timer with 25/5 minute cycles
import gpa_calculator    # Grade point average calculator
import reminder_app      # Task reminder system
import home_planner      # Homework assignment planner


# Custom widget that creates an interactive card with hover effects
class HoverCard(tk.Frame):
    """Interactive card widget with hover animations and click handling"""
    def __init__(self, master, icon, title, subtitle, description, button_text, command, accent="#6366F1", *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.command = command
        self.accent = accent
        
        self.body_bg = "#0B1220" 
        self.bg_normal = "#0F172A"
        self.bg_hover = "#111B33"
        self.border_normal = "#1E293B"
        self.border_hover = accent

        self.configure(bg=self.body_bg)
        
        self.container = tk.Frame(self, bg=self.bg_normal, highlightbackground=self.border_normal,
                                  highlightthickness=1, bd=0)
        self.container.pack(fill="both", expand=True, padx=4, pady=4)

        top = tk.Frame(self.container, bg=self.bg_normal)
        top.pack(fill="x", padx=16, pady=(16, 8))

        icon_wrap = tk.Frame(top, bg=self._grad_color(accent), width=44, height=44)
        icon_wrap.pack_propagate(False)
        icon_wrap.pack(side="left")

        icon_label = tk.Label(icon_wrap, text=icon, bg=self._grad_color(accent), fg="white",
                              font=("Segoe UI Emoji", 18))
        icon_label.pack(expand=True, fill="both")

        titles = tk.Frame(top, bg=self.bg_normal)
        titles.pack(side="left", padx=12, fill="x", expand=True)

        title_label = tk.Label(titles, text=title, bg=self.bg_normal, fg="white",
                               font=("Helvetica Neue", 14, "bold"))
        title_label.pack(anchor="w")
        subtitle_label = tk.Label(titles, text=subtitle, bg=self.bg_normal, fg="#94A3B8",
                                  font=("Helvetica Neue", 10))
        subtitle_label.pack(anchor="w", pady=(2, 0))

        desc = tk.Label(self.container, text=description, bg=self.bg_normal, fg="#CBD5E1",
                        wraplength=360, justify="left", font=("Helvetica Neue", 10))
        desc.pack(fill="x", padx=16, pady=(8, 10))

        self.button = tk.Button(self.container, text=button_text, command=self._on_click,
                                bg=accent, fg="white", activebackground=self._darken(accent),
                                activeforeground="white", relief="flat", cursor="hand2",
                                font=("Helvetica Neue", 10, "bold"))
        self.button.pack(fill="x", padx=16, pady=(4, 16), ipady=8)

        # Bind click events for visual feedback
        self.clickable_widgets = [self, self.container, top, icon_wrap, icon_label, titles, title_label, subtitle_label, desc]
        for w in self.clickable_widgets:
            w.bind("<Button-1>", self._on_press)
            w.bind("<ButtonRelease-1>", self._on_release)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

        self.button.bind("<Enter>", lambda e: self.button.config(bg=self._darken(accent)))
        self.button.bind("<Leave>", lambda e: self.button.config(bg=accent))
        self.button.bind("<Button-1>", self._on_btn_press, add="+")
        self.button.bind("<ButtonRelease-1>", self._on_btn_release, add="+")

    def _on_click(self):
        if callable(self.command):
            self.command()

    def _on_press(self, event=None):
        self.container.config(relief="sunken", highlightthickness=0)

    def _on_release(self, event=None):
        self.container.config(relief="flat", highlightthickness=1)
        self._on_click()

    def _on_btn_press(self, event=None):
        self.button.config(relief="sunken")

    def _on_btn_release(self, event=None):
        self.button.config(relief="flat")
            
    def _on_enter(self, event=None):
        self.config(bg=self.border_hover)
        self.container.config(highlightbackground=self.border_hover, bg=self.bg_hover)
        self.container.pack_configure(padx=(2, 6), pady=(2, 6))

    def _on_leave(self, event=None):
        self.config(bg=self.body_bg)
        self.container.config(highlightbackground=self.border_normal, bg=self.bg_normal)
        self.container.pack_configure(padx=4, pady=4)

    def _darken(self, hex_color, factor=0.9):
        """Darken or lighten a hex color by a factor"""
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = (int(min(255, max(0, c * factor))) for c in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _grad_color(self, base_hex):
        """Create gradient color for icon background"""
        return self._darken(base_hex, 1.05)


# Main application class that creates the launcher interface
class StudentAssistantApp(tk.Tk):
    """Main dashboard that provides access to all student tools"""
    def __init__(self):
        super().__init__()
        self.title("Student Assistant Program")
        self.geometry("960x780")
        self.minsize(860, 600)

        self.bg_grad_start = "#0B1220"
        self.bg_grad_end = "#030712"
        self.header_bg = self.bg_grad_start
        self.card_bg = "#0F172A"
        self.border = "#1E293B"
        self.fg_primary = "white"
        self.fg_secondary = "#CBD5E1"
        self.accent_indigo = "#6366F1"
        self.accent_sky = "#0EA5E9"
        self.accent_pink = "#EC4899"
        self.accent_emerald = "#10B981"

        self._create_gradient_background()

        self.tips = [
            "Tip: Use the Pomodoro technique to improve focus during study sessions.",
            "Tip: Short, frequent breaks can boost overall productivity.",
            "Tip: Keep your GPA calculator updated to track academic progress.",
            "Tip: Use the reminder app for deadlines, exams, and important events.",
            "Tip: Plan your homework to avoid last-minute stress.",
            "Tip: You can open and use multiple tools at the same time."
        ]

        self.title_font = font.Font(family="Helvetica Neue", size=22, weight="bold")
        self.subtitle_font = font.Font(family="Helvetica Neue", size=11)

        self._build_header()
        self._build_tip()
        self._build_cards()
        self._build_footer()
        
        self.after(7000, self._update_tip)
        self.after(100, self._center_window)

    def _create_gradient_background(self):
        """Create a smooth gradient background for visual appeal"""
        self.background_canvas = tk.Canvas(self, highlightthickness=0)
        self.background_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        def _draw_gradient(event=None):
            self.background_canvas.delete("gradient")
            width = self.winfo_width()
            height = self.winfo_height()
            
            (r1, g1, b1) = self.winfo_rgb(self.bg_grad_start)
            (r2, g2, b2) = self.winfo_rgb(self.bg_grad_end)
            r_ratio = float(r2-r1) / height
            g_ratio = float(g2-g1) / height
            b_ratio = float(b2-b1) / height

            for i in range(height):
                nr = int(r1 + (r_ratio * i))
                ng = int(g1 + (g_ratio * i))
                nb = int(b1 + (b_ratio * i))
                color = f"#{nr:04x}{ng:04x}{nb:04x}"
                self.background_canvas.create_line(0, i, width, i, tags=("gradient",), fill=color)
        
        self.background_canvas.bind("<Configure>", _draw_gradient)

    def _build_header(self):
        header_wrap = tk.Frame(self.background_canvas, bg=self.header_bg)
        header_wrap.pack(fill="x", padx=24, pady=(24, 10))
        header_card = tk.Frame(header_wrap, bg="#0D1426", highlightbackground=self.border, highlightthickness=1)
        header_card.pack(fill="x")
        row = tk.Frame(header_card, bg="#0D1426")
        row.pack(fill="x", padx=18, pady=16)

        icon_wrap = tk.Frame(row, bg=self.accent_indigo, width=50, height=50)
        icon_wrap.pack_propagate(False)
        icon_wrap.grid(row=0, column=0, sticky="w")
        icon_label = tk.Label(icon_wrap, text="✨", bg=self.accent_indigo, fg="white", font=("Segoe UI Emoji", 20))
        icon_label.pack(expand=True, fill="both")

        title_area = tk.Frame(row, bg="#0D1426")
        title_area.grid(row=0, column=1, sticky="w", padx=12)
        tk.Label(title_area, text="Student Assistant", bg="#0D1426", fg=self.fg_primary, font=self.title_font).pack(anchor="w")
        tk.Label(title_area, text="Focus, calculate, and remember — all in one place.", bg="#0D1426", fg="#94A3B8", font=self.subtitle_font).pack(anchor="w", pady=(2, 0))
                 
        action_btn = tk.Button(row, text="Quick Start →", command=self._open_random_app,
                               bg=self.accent_indigo, fg="white", activebackground="#4F46E5",
                               activeforeground="white", relief="flat", cursor="hand2",
                               font=("Helvetica Neue", 10, "bold"))
        action_btn.grid(row=0, column=2, sticky="e", padx=(12, 0))
        row.grid_columnconfigure(1, weight=1)

        self._apply_button_effects(action_btn, self.accent_indigo, "#4F46E5")

    def _build_tip(self):
        tip_wrap = tk.Frame(self.background_canvas, bg=self.bg_grad_start)
        tip_wrap.pack(fill="x", padx=24, pady=(6, 18))
        tip = tk.Frame(tip_wrap, bg="#0D1426", highlightbackground=self.border, highlightthickness=1)
        tip.pack(fill="x")
        inner = tk.Frame(tip, bg="#0D1426")
        inner.pack(fill="x", padx=14, pady=10)
        tk.Label(inner, text="💡", bg="#0D1426", fg=self.fg_primary, font=("Segoe UI Emoji", 16)).pack(side="left")
        self.tip_label = tk.Label(inner, text=random.choice(self.tips), bg="#0D1426", fg="#A7B4C5", font=("Helvetica Neue", 10))
        self.tip_label.pack(side="left", padx=8)
        
    def _update_tip(self):
        current_tip = self.tip_label.cget("text")
        new_tip = random.choice(self.tips)
        while new_tip == current_tip and len(self.tips) > 1:
            new_tip = random.choice(self.tips)
        self.tip_label.config(text=new_tip)
        self.after(7000, self._update_tip)

    def _build_cards(self):
        grid_wrap = tk.Frame(self.background_canvas, bg=self.bg_grad_start)
        grid_wrap.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        for i in range(2):
            grid_wrap.grid_columnconfigure(i, weight=1, uniform="col")
        for r in range(2):
            grid_wrap.grid_rowconfigure(r, weight=1)
            
        # --- MODIFIED: Replaced the "Coming Soon" card with the "Homework Planner" ---
        cards_data = [
            {"icon": "⏱️", "title": "Pomodoro Timer", "subtitle": "Stay focused with 25/5 cycles", "desc": "Use focused sprints with short breaks to boost productivity.", "btn": "Open Pomodoro →", "accent": self.accent_pink, "cmd": self.open_pomodoro},
            {"icon": "📊", "title": "GPA Calculator", "subtitle": "Quickly compute your GPA", "desc": "Add courses and credits to see your overall performance.", "btn": "Open Calculator →", "accent": self.accent_emerald, "cmd": self.open_calculator},
            {"icon": "🗓️", "title": "Reminder App", "subtitle": "Never miss important tasks", "desc": "Set simple reminders to stay on top of deadlines.", "btn": "Open Reminders →", "accent": self.accent_sky, "cmd": self.open_reminder},
            {"icon": "📚", "title": "Homework Planner", "subtitle": "Organize your assignments", "desc": "Track subjects, titles, and deadlines to stay on top of your work.", "btn": "Open Planner →", "accent": self.accent_indigo, "cmd": self.open_homework_planner}
        ]
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for cfg, (r, c) in zip(cards_data, positions):
            card = HoverCard(grid_wrap, icon=cfg["icon"], title=cfg["title"], subtitle=cfg["subtitle"], description=cfg["desc"], button_text=cfg["btn"], command=cfg["cmd"], accent=cfg["accent"], bg=self.card_bg)
            card.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)
            card.body_bg = self.bg_grad_start 

    def _build_footer(self):
        footer = tk.Frame(self.background_canvas, bg=self.bg_grad_start)
        footer.pack(fill="x", padx=24, pady=(0, 20))
        line = tk.Frame(footer, bg=self.border, height=1)
        line.pack(fill="x", pady=(0, 10))
        label = tk.Label(footer, text="Student Assistant • Built for focus and clarity", bg=self.bg_grad_start, fg="#94A3B8", font=("Helvetica Neue", 9))
        label.pack(anchor="center")
        
        exit_button = tk.Button(footer, text="Exit Program →", command=self.destroy, bg="#CC0000", fg=self.fg_secondary, activebackground="#990000", activeforeground="white", relief="flat", cursor="hand2", font=("Helvetica Neue", 9, "bold"))
        
        exit_button.pack(pady=(12, 10), ipady=5, ipadx=10)
        
        self._apply_button_effects(exit_button, "#CC0000", "#FF0000", leave_fg=self.fg_secondary)

    def _apply_button_effects(self, button, bg_normal, bg_hover, leave_fg="white"):
        button.bind("<Enter>", lambda e: button.config(bg=bg_hover))
        button.bind("<Leave>", lambda e: button.config(bg=bg_normal, fg=leave_fg))
        button.bind("<Button-1>", lambda e: button.config(relief="sunken"), add="+")
        button.bind("<ButtonRelease-1>", lambda e: button.config(relief="flat"), add="+")

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw // 2) - (w // 2), (sh // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _open_random_app(self):
        # --- MODIFIED: Added homework planner to the random choices ---
        possible_actions = [self.open_pomodoro, self.open_calculator, self.open_reminder, self.open_homework_planner]
        random_action = random.choice(possible_actions)
        random_action()

    def open_pomodoro(self):
        pomodoro_timer.main()

    def open_calculator(self):
        gpa_calculator.main()

    def open_reminder(self):
        reminder_app.main()

    # --- MODIFIED: Added method to launch the homework planner ---
    def open_homework_planner(self):
        home_planner.main()

if __name__ == "__main__":
    app = StudentAssistantApp()
    app.mainloop()
