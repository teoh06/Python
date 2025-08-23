import tkinter as tk
from tkinter import font, messagebox

# --- Import your applications (keep as-is) ---
import pomodoro_timer
import gpa_calculator
import reminder_app


class HoverCard(tk.Frame):
    def __init__(self, master, icon, title, subtitle, description, button_text, command, accent="#6366F1", *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.command = command
        self.accent = accent
        self.bg_normal = "#0F172A"       # card base
        self.bg_hover = "#111B33"        # slightly lighter on hover
        self.border_normal = "#1E293B"
        self.border_hover = accent

        # Card styling
        self.configure(bg=self.bg_normal, highlightthickness=0, bd=0)
        self.container = tk.Frame(self, bg=self.bg_normal, highlightbackground=self.border_normal,
                                  highlightthickness=1, bd=0)
        self.container.pack(fill="both", expand=True, padx=1, pady=1)

        # Top row: icon + title/subtitle
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

        # Description
        desc = tk.Label(self.container, text=description, bg=self.bg_normal, fg="#CBD5E1",
                        wraplength=360, justify="left", font=("Helvetica Neue", 10))
        desc.pack(fill="x", padx=16, pady=(8, 10))

        # Button
        self.button = tk.Button(self.container, text=button_text, command=self._on_click,
                                bg=accent, fg="white", activebackground=self._darken(accent),
                                activeforeground="white", relief="flat", cursor="hand2",
                                font=("Helvetica Neue", 10, "bold"))
        self.button.pack(fill="x", padx=16, pady=(4, 16), ipady=8)

        # Make whole card clickable
        for w in [self, self.container, top, icon_wrap, icon_label, titles, title_label, subtitle_label, desc]:
            w.bind("<Button-1>", lambda e: self._on_click())
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

        # Hover feedback for button too
        self.button.bind("<Enter>", lambda e: self.button.config(bg=self._darken(accent)))
        self.button.bind("<Leave>", lambda e: self.button.config(bg=accent))

        # Rounded look via small padding illusion
        self._roundify(self.container)

    def _on_click(self):
        if callable(self.command):
            self.command()

    def _on_enter(self, event=None):
        self.container.config(highlightbackground=self.border_hover)
        self.container.config(bg=self.bg_hover)
        self.config(bg=self.bg_hover)

    def _on_leave(self, event=None):
        self.container.config(highlightbackground=self.border_normal)
        self.container.config(bg=self.bg_normal)
        self.config(bg=self.bg_normal)

    def _darken(self, hex_color, factor=0.9):
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _grad_color(self, base_hex):
        # Simulate a gradient look with a slightly lighter tone for solid fills
        return self._darken(base_hex, 1.05)

    def _roundify(self, widget):
        # Tkinter doesn't have native rounded corners; we simulate with spacing and subtle borders.
        # This keeps spacing consistent and avoids sharp edges visually.
        widget.pack_configure(padx=1, pady=1)


class StudentAssistantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Assistant Program")
        self.geometry("960x750")
        self.minsize(860, 600)

        # Colors
        self.bg_body = "#0B1220"
        self.header_bg = "#0B1220"
        self.card_bg = "#0F172A"
        self.border = "#1E293B"
        self.fg_primary = "white"
        self.fg_secondary = "#CBD5E1"
        self.accent_indigo = "#6366F1"
        self.accent_sky = "#0EA5E9"
        self.accent_pink = "#EC4899"
        self.accent_emerald = "#10B981"

        self.configure(bg=self.bg_body)

        # Fonts
        self.title_font = font.Font(family="Helvetica Neue", size=22, weight="bold")
        self.subtitle_font = font.Font(family="Helvetica Neue", size=11)

        # Header
        self._build_header()

        # Tip banner
        self._build_tip()

        # Grid of cards
        self._build_cards()

        # Footer
        self._build_footer()

        # Center window (nice touch)
        self.after(100, self._center_window)

    def _build_header(self):
        header_wrap = tk.Frame(self, bg=self.header_bg)
        header_wrap.pack(fill="x", padx=24, pady=(24, 10))

        header_card = tk.Frame(header_wrap, bg="#0D1426", highlightbackground=self.border, highlightthickness=1)
        header_card.pack(fill="x", padx=0, pady=0)

        # Left: icon
        row = tk.Frame(header_card, bg="#0D1426")
        row.pack(fill="x", padx=18, pady=16)

        icon_wrap = tk.Frame(row, bg=self.accent_indigo, width=50, height=50)
        icon_wrap.pack_propagate(False)
        icon_wrap.grid(row=0, column=0, sticky="w")

        icon_label = tk.Label(icon_wrap, text="✨", bg=self.accent_indigo, fg="white", font=("Segoe UI Emoji", 20))
        icon_label.pack(expand=True, fill="both")

        # Title/subtitle
        title_area = tk.Frame(row, bg="#0D1426")
        title_area.grid(row=0, column=1, sticky="w", padx=12)

        tk.Label(title_area, text="Student Assistant", bg="#0D1426", fg=self.fg_primary, font=self.title_font)\
            .pack(anchor="w")
        tk.Label(title_area, text="Focus, calculate, and remember — all in one place.", bg="#0D1426",
                 fg="#94A3B8", font=self.subtitle_font).pack(anchor="w", pady=(2, 0))

        # Right action button
        action_btn = tk.Button(row, text="Quick Start →", command=self.open_pomodoro,
                               bg=self.accent_indigo, fg="white", activebackground="#4F46E5",
                               activeforeground="white", relief="flat", cursor="hand2",
                               font=("Helvetica Neue", 10, "bold"))
        action_btn.grid(row=0, column=2, sticky="e", padx=(12, 0))
        row.grid_columnconfigure(1, weight=1)

        # Hover feedback
        action_btn.bind("<Enter>", lambda e: action_btn.config(bg="#4F46E5"))
        action_btn.bind("<Leave>", lambda e: action_btn.config(bg=self.accent_indigo))

    def _build_tip(self):
        tip_wrap = tk.Frame(self, bg=self.bg_body)
        tip_wrap.pack(fill="x", padx=24, pady=(6, 18))

        tip = tk.Frame(tip_wrap, bg="#0D1426", highlightbackground=self.border, highlightthickness=1)
        tip.pack(fill="x")

        inner = tk.Frame(tip, bg="#0D1426")
        inner.pack(fill="x", padx=14, pady=10)

        tk.Label(inner, text="💡", bg="#0D1426", fg=self.fg_primary, font=("Segoe UI Emoji", 16)).pack(side="left")
        tk.Label(inner, text="Tip: You can open multiple tools at once.", bg="#0D1426", fg="#A7B4C5",
                 font=("Helvetica Neue", 10)).pack(side="left", padx=8)

    def _build_cards(self):
        grid_wrap = tk.Frame(self, bg=self.bg_body)
        grid_wrap.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Responsive-like grid using weight; 2 columns on medium+ sizes
        for i in range(2):
            grid_wrap.grid_columnconfigure(i, weight=1, uniform="col")
        # Three rows
        for r in range(2):
            grid_wrap.grid_rowconfigure(r, weight=1)

        # Cards
        cards = [
            {
                "icon": "⏱️",
                "title": "Pomodoro Timer",
                "subtitle": "Stay focused with 25/5 cycles",
                "desc": "Use focused sprints with short breaks to boost productivity.",
                "btn": "Open Pomodoro →",
                "accent": self.accent_pink,
                "cmd": self.open_pomodoro
            },
            {
                "icon": "📊",
                "title": "GPA Calculator",
                "subtitle": "Quickly compute your GPA",
                "desc": "Add courses and credits to see your overall performance.",
                "btn": "Open Calculator →",
                "accent": self.accent_emerald,
                "cmd": self.open_calculator
            },
            {
                "icon": "🗓️",
                "title": "Reminder App",
                "subtitle": "Never miss important tasks",
                "desc": "Set simple reminders to stay on top of deadlines.",
                "btn": "Open Reminders →",
                "accent": self.accent_sky,
                "cmd": self.open_reminder
            },
            {
                "icon": "✨",
                "title": "Coming Soon",
                "subtitle": "New tools are on the way",
                "desc": "Have an idea? Share what you’d like to see next.",
                "btn": "Notify Me →",
                "accent": self.accent_indigo,
                "cmd": self.coming_soon
            }
        ]

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for cfg, (r, c) in zip(cards, positions):
            card = HoverCard(
                grid_wrap,
                icon=cfg["icon"],
                title=cfg["title"],
                subtitle=cfg["subtitle"],
                description=cfg["desc"],
                button_text=cfg["btn"],
                command=cfg["cmd"],
                accent=cfg["accent"],
                bg=self.card_bg,
            )
            card.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)

    def _build_footer(self):
        footer = tk.Frame(self, bg=self.bg_body)
        footer.pack(fill="x", padx=24, pady=(0, 20))

        line = tk.Frame(footer, bg=self.border, height=1)
        line.pack(fill="x", pady=(0, 10))

        label = tk.Label(footer, text="Student Assistant • Built for focus and clarity",
                         bg=self.bg_body, fg="#94A3B8", font=("Helvetica Neue", 9))
        label.pack(anchor="center")
        
        # --- ADDED EXIT BUTTON ---
        exit_button = tk.Button(footer, text="Exit Program", 
                        command=self.destroy,
                        bg="#FF0000",  # red background
                        fg=self.fg_secondary,
                        activebackground="#CC0000",  # darker red on hover
                        activeforeground="white",
                        relief="flat",
                        cursor="hand2",
                        font=("Helvetica Neue", 9, "bold"))
        exit_button.pack(pady=(12, 0), ipady=5, ipadx=10)
        
        # Hover feedback for exit button
        exit_button.bind("<Enter>", lambda e: exit_button.config(bg="#FF0000", fg="white"))
        exit_button.bind("<Leave>", lambda e: exit_button.config(bg="#CC0000", fg=self.fg_secondary))
        # --- END OF ADDITION ---

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # --- Your original openings preserved ---
    def open_pomodoro(self):
        pomodoro_timer.main()

    def open_calculator(self):
        gpa_calculator.main()

    def open_reminder(self):
        reminder_app.main()

    def coming_soon(self):
        messagebox.showinfo("Coming Soon", "This feature is under development.")


if __name__ == "__main__":
    app = StudentAssistantApp()
    app.mainloop()
