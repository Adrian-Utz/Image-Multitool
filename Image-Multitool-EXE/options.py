import tkinter as tk
from tkinter import ttk

#This is the Options window. Here we can add Theme switchers, Memory settings, and tool starting options.

#written by: AJ Utz on 6/30/2026
#Last Updated: 7/3/2026

def apply_theme(gui, theme):
    if theme == "dark":
        root_bg = "#2b2b2b"
        frame_bg = "#2f2f2f"
        label_fg = "#f2f2f2"
        text_bg = "#1e1e1e"
        text_fg = "#e8e8e8"
        button_bg = "#3b3b3b"
        separator_bg = "#555555"
        progress_color = "#0fb100"
    else:
        root_bg = "#f0f0f0"
        frame_bg = "#f7f7f7"
        label_fg = "#000000"
        text_bg = "#ffffff"
        text_fg = "#000000"
        button_bg = "#e0e0e0"
        separator_bg = "#999999"
        progress_color = "#0fb100"

    try:
        gui.style.theme_use("clam")
    except Exception:
        pass

    gui.style.configure("TFrame", background=frame_bg)
    gui.style.configure("TLabelframe", background=frame_bg, foreground=label_fg)
    gui.style.configure("TLabelframe.Label", background=frame_bg, foreground=label_fg)
    gui.style.configure("TLabel", background=frame_bg, foreground=label_fg)
    gui.style.configure(
        "TButton",
        background=button_bg,
        foreground=label_fg,
        bordercolor=button_bg,
        lightcolor=button_bg,
        darkcolor=button_bg,
        focuscolor=button_bg,
    )
    gui.style.map(
        "TButton",
        background=[("pressed", button_bg), ("active", button_bg), ("!disabled", button_bg)],
        foreground=[("pressed", label_fg), ("active", label_fg), ("!disabled", label_fg)],
    )
    gui.style.configure("TSeparator", background=separator_bg)
    gui.style.configure("Horizontal.TProgressbar", troughcolor=frame_bg, background=progress_color)

    gui.root.configure(bg=root_bg)
    if hasattr(gui, "right"):
        gui.right.configure(style="TFrame")
    if hasattr(gui, "paned_window"):
        gui.paned_window.configure(bg=separator_bg)

    if hasattr(gui, "queue_text"):
        gui.queue_text.config(bg=text_bg, fg=text_fg, insertbackground=text_fg)
    if hasattr(gui, "log_text"):
        gui.log_text.config(bg=text_bg, fg=text_fg, insertbackground=text_fg)

    if hasattr(gui, "status_label"):
        gui.status_label.config(background=frame_bg, foreground=label_fg)
    if hasattr(gui, "task_counter_label"):
        gui.task_counter_label.config(background=frame_bg, foreground=label_fg)
    if hasattr(gui, "cancel_button"):
        gui.cancel_button.config(style="TButton")

    if hasattr(gui, "_update_status_idle"):
        gui._update_status_idle()


def set_light_mode(gui):
    gui.current_theme = "light"
    apply_theme(gui, "light")


def set_dark_mode(gui):
    gui.current_theme = "dark"
    apply_theme(gui, "dark")


def set_auto_start(gui, enabled):
    gui.auto_start = bool(enabled)
    if hasattr(gui, "_update_start_queue_button_state"):
        gui._update_start_queue_button_state()
    if bool(enabled) and hasattr(gui, "task_queue") and gui.task_queue and hasattr(gui, "_current_task_future") and gui._current_task_future is None and hasattr(gui, "_process_queue"):
        gui._process_queue()


class OptionsWindow:
    def __init__(self, parent, gui):
        self.gui = gui
        self.window = tk.Toplevel(parent)
        self.window.title("Options")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        # Configure grid layout
        self.window.columnconfigure(0, weight=1)
        self.window.columnconfigure(1, weight=1)

        # Create content frame
        content = ttk.Frame(self.window, padding=12)
        content.grid(row=0, column=0, sticky="nsew")

        ttk.Label(content, text="Appearance", font=(None, 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Button(content, text="Light Mode", command=self._set_light_mode).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=4)
        ttk.Button(content, text="Dark Mode", command=self._set_dark_mode).grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=4)

        #Auto-start queue option
        ttk.Label(content, text="Queue", font=(None, 10, "bold")).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.auto_start_var = tk.BooleanVar(value=getattr(gui, "auto_start", True))
        ttk.Checkbutton(content, text="Auto-start queue", variable=self.auto_start_var, command=self._toggle_auto_start).grid(row=3, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(content, text="More options can be added here later.", foreground="gray").grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))

        ttk.Button(content, text="Close", command=self.window.destroy).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))

    #Call this to set the GUI to light mode
    def _set_light_mode(self):
        set_light_mode(self.gui)

    #Call this to set the GUI to dark mode
    def _set_dark_mode(self):
        set_dark_mode(self.gui)

    #Call this to toggle the queue's auto-start option
    def _toggle_auto_start(self):
        set_auto_start(self.gui, self.auto_start_var.get())
