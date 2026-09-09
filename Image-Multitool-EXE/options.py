import tkinter as tk
from tkinter import ttk, messagebox
import os
import json

"""
This is the Options window. Here we can add Theme switchers, Memory settings, and tool starting options.

Last Updated: 9/3/2026
Written on: 6/30/2026
Written by: AJ Utz
"""

# File used to persist user preferences (theme, auto-start) between runs
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".multitool_settings.json")

def _load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_settings(d):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(d, f)
    except Exception:
        pass

def load_saved_theme(default="light"):
    """Return the last-used theme key from disk, falling back to `default`."""
    settings = _load_settings()
    theme = settings.get("theme", default)
    return theme if theme in THEMES else default

def load_saved_auto_start(default=True):
    """Return the last-used auto-start flag from disk, falling back to `default`."""
    settings = _load_settings()
    return bool(settings.get("auto_start", default))

# Registry of available themes. Add a new entry here to make a theme available in the Options dropdown
THEMES = {
    "light": {
        "label": "Light",
        "root_bg": "#f0f0f0",
        "frame_bg": "#f7f7f7",
        "label_fg": "#000000",
        "text_bg": "#ffffff",
        "text_fg": "#000000",
        "button_bg": "#e0e0e0",
        "separator_bg": "#999999",
        "progress_color": "#0fb100",
    },
    "dark": {
        "label": "Dark",
        "root_bg": "#2b2b2b",
        "frame_bg": "#2f2f2f",
        "label_fg": "#f2f2f2",
        "text_bg": "#1e1e1e",
        "text_fg": "#e8e8e8",
        "button_bg": "#3b3b3b",
        "separator_bg": "#555555",
        "progress_color": "#0fb100",
    },
    "forest": {
        "label": "Forest",
        "root_bg": "#254629",
        "frame_bg": "#2B422E",
        "label_fg": "#f2f2f2",
        "text_bg": "#273F2A",
        "text_fg": "#e8e8e8",
        "button_bg": "#406943",
        "separator_bg": "#3C7541",
        "progress_color": "#0fb100",
    },
    "ocean": {
        "label": "Ocean",
        "root_bg": "#6591B9",
        "frame_bg": "#8FBAE2",
        "label_fg": "#000000",
        "text_bg": "#78A4CE",
        "text_fg": "#000000",
        "button_bg": "#5CA0E0",
        "separator_bg": "#4577A5",
        "progress_color": "#0fb100",
    }
}

def apply_theme(gui, theme):
    colors = THEMES.get(theme, THEMES["light"])
    root_bg = colors["root_bg"]
    frame_bg = colors["frame_bg"]
    label_fg = colors["label_fg"]
    text_bg = colors["text_bg"]
    text_fg = colors["text_fg"]
    button_bg = colors["button_bg"]
    separator_bg = colors["separator_bg"]
    progress_color = colors["progress_color"]

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
        focuscolor=progress_color,
        focusthickness=2,
        focussolid=True,
    )
    gui.style.map(
        "TButton",
        background=[("pressed", button_bg), ("active", button_bg), ("!disabled", button_bg)],
        foreground=[("pressed", label_fg), ("active", label_fg), ("!disabled", label_fg)],
        bordercolor=[("focus", progress_color), ("!focus", button_bg)],
    )
    gui.style.configure("TSeparator", background=separator_bg)
    gui.style.configure("Horizontal.TProgressbar", troughcolor=frame_bg, background=progress_color)
    gui.style.configure("TRadiobutton", background=frame_bg, foreground=label_fg)
    gui.style.map(
        "TRadiobutton",
        background=[("active", frame_bg)],
        foreground=[("active", label_fg)],
    )
    gui.style.configure("TCheckbutton", background=frame_bg, foreground=label_fg)
    gui.style.map(
        "TCheckbutton",
        background=[("active", frame_bg)],
        foreground=[("active", label_fg)],
    )

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

def set_theme(gui, theme):
    """Generic theme setter used by the Options dropdown and any theme key in THEMES."""
    if theme not in THEMES:
        theme = "light"
    gui.current_theme = theme
    apply_theme(gui, theme)
    settings = _load_settings()
    settings["theme"] = theme
    _save_settings(settings)

# Here the auto-start option is set.
def set_auto_start(gui, enabled):
    gui.auto_start = bool(enabled)
    if hasattr(gui, "_update_start_queue_button_state"):
        gui._update_start_queue_button_state()
    if bool(enabled) and hasattr(gui, "task_queue") and gui.task_queue and hasattr(gui, "_current_task_future") and gui._current_task_future is None and hasattr(gui, "_process_queue"):
        gui._process_queue()
    settings = _load_settings()
    settings["auto_start"] = bool(enabled)
    _save_settings(settings)


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

        # Theme dropdown -- add new themes to the THEMES registry above and they'll show up here automatically.
        self._theme_keys = list(THEMES.keys())
        theme_labels = [THEMES[key]["label"] for key in self._theme_keys]
        current_key = getattr(gui, "current_theme", "light")
        current_label = THEMES.get(current_key, THEMES["light"])["label"]

        ttk.Label(content, text="Theme:").grid(row=1, column=0, sticky="w", pady=4)
        self.theme_var = tk.StringVar(value=current_label)
        theme_combo = ttk.Combobox(content, textvariable=self.theme_var, values=theme_labels, state="readonly")
        theme_combo.grid(row=1, column=1, sticky="ew", pady=4)
        theme_combo.bind("<<ComboboxSelected>>", self._on_theme_selected)

        #Auto-start queue option
        ttk.Label(content, text="Queue", font=(None, 10, "bold")).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.auto_start_var = tk.BooleanVar(value=getattr(gui, "auto_start", True))
        ttk.Checkbutton(content, text="Auto-start queue", variable=self.auto_start_var, command=self._toggle_auto_start).grid(row=3, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(content, text="More options will be added here later.", foreground="gray").grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))
        # Button to force an update check via the GUI
        ttk.Button(content, text="Check for updates", command=self._check_updates).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Button(content, text="Close", command=self.window.destroy).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))

    #Called when the user picks a theme from the dropdown
    def _on_theme_selected(self, event=None):
        label = self.theme_var.get()
        for key in self._theme_keys:
            if THEMES[key]["label"] == label:
                set_theme(self.gui, key)
                break

    #Call this to toggle the queue's auto-start option
    def _toggle_auto_start(self):
        set_auto_start(self.gui, self.auto_start_var.get())

    def _check_updates(self):
        """Trigger a forced update check using the main GUI's API."""
        try:
            if hasattr(self.gui, 'trigger_update_check'):
                self.gui.trigger_update_check(force=True)
            else:
                # fallback: import and run check directly
                import check_for_update
                available, _, latest = check_for_update.is_update_available(force=True)
                if latest is None:
                    messagebox.showinfo("Update Check", "Could not determine latest version from GitHub.")
                    return
                if available:
                    if messagebox.askyesno("Update available", f"A new version ({latest}) is available. Open releases page?"):
                        if not check_for_update.open_releases_page():
                            messagebox.showinfo("Update Check", f"Could not open browser automatically.\n\nOpen this URL manually:\n{check_for_update.get_latest_release_url()}")
                else:
                    messagebox.showinfo("Update Check", f"You are up to date. Latest: {latest}")
        except Exception:
            messagebox.showinfo("Update Check", "Update check failed.")
