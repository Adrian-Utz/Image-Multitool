import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from image_multitool.workflows.models import TASK_TYPES, validate_task

"""
Dialog for adding or editing a single workflow task.

Written by: AJ Utz
Written on: 11/18/2026
Latest Update: 11/18/2026
"""

def _parse_value(field, value):
    if field.kind == "bool":
        return value
    value = value.strip()
    if field.kind in ("list", "paths"):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if field.kind in ("optional_int", "optional_text", "optional_file", "optional_choice") and not value:
        return None
    if field.kind in ("int", "optional_int"):
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{field.label}: enter a whole number.") from exc
    if field.kind == "dimensions":
        if not value:
            return None
        try:
            return [int(part.strip()) for part in value.lower().split("x")]
        except ValueError as exc:
            raise ValueError(f"{field.label}: use WIDTHxHEIGHT.") from exc
    if field.kind == "column" and value.isdigit():
        return int(value)
    return value


class TaskDialog:
    def __init__(self, parent, task=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Edit task" if task else "Add task")
        self.window.transient(parent)
        self.window.geometry("650x650")
        self.result = None
        self.controls = {}

        header = ttk.Frame(self.window, padding=10)
        header.pack(fill="x")
        ttk.Label(header, text="Tool:").pack(side="left")
        self.tool = ttk.Combobox(header, state="readonly", values=[item[0] for item in TASK_TYPES.values()])
        self.tool.pack(side="left", fill="x", expand=True, padx=8)
        self.tool.current(list(TASK_TYPES).index(task["type"]) if task else 0)
        self.tool.bind("<<ComboboxSelected>>", self._change_tool)
        if task:
            self.tool.config(state="disabled")

        container = ttk.Frame(self.window)
        container.pack(fill="both", expand=True, padx=10)
        self.canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.form = ttk.Frame(self.canvas, padding=5)
        self.form_window = self.canvas.create_window((0, 0), window=self.form, anchor="nw")
        self.form.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.form_window, width=event.width))

        buttons = ttk.Frame(self.window, padding=10)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Cancel", command=self.window.destroy).pack(side="right")
        ttk.Button(buttons, text="Save task", command=self._save).pack(side="right", padx=5)
        self._build_form(task["settings"] if task else None)
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        self.window.grab_set()
        self.window.wait_window()

    def _type(self):
        return list(TASK_TYPES)[self.tool.current()]

    def _change_tool(self, _event=None):
        self._build_form(None)

    def _build_form(self, settings):
        for child in self.form.winfo_children():
            child.destroy()
        self.controls = {}
        self.form.columnconfigure(1, weight=1)
        for row, field in enumerate(TASK_TYPES[self._type()][1]):
            value = settings[field.key] if settings is not None else field.default
            ttk.Label(self.form, text=field.label, wraplength=230).grid(row=row, column=0, sticky="nw", padx=5, pady=5)
            if field.kind == "bool":
                control = tk.BooleanVar(value=value)
                ttk.Checkbutton(self.form, variable=control).grid(row=row, column=1, sticky="w", pady=5)
            elif field.kind in ("list", "paths"):
                control = tk.Text(self.form, height=3, width=35)
                control.insert("1.0", "\n".join(value))
                control.grid(row=row, column=1, sticky="ew", pady=5)
                if field.kind == "paths":
                    ttk.Button(self.form, text="Add file", command=lambda c=control: self._browse_list(c, False)).grid(row=row, column=2, sticky="n")
                    ttk.Button(self.form, text="Add folder", command=lambda c=control: self._browse_list(c, True)).grid(row=row, column=3, sticky="n")
            else:
                if field.kind == "dimensions" and value is not None:
                    value = "x".join(str(part) for part in value)
                control = tk.StringVar(value="" if value is None else str(value))
                if field.kind in ("choice", "optional_choice"):
                    choices = (("",) if field.kind == "optional_choice" else ()) + field.choices
                    widget = ttk.Combobox(self.form, textvariable=control, values=choices, state="readonly")
                else:
                    widget = ttk.Entry(self.form, textvariable=control)
                widget.grid(row=row, column=1, sticky="ew", pady=5)
                if field.kind in ("folder", "file", "optional_file"):
                    ttk.Button(self.form, text="Browse...", command=lambda f=field, v=control: self._browse(f, v)).grid(row=row, column=2, padx=4)
            self.controls[field.key] = control
        self.canvas.yview_moveto(0)

    def _browse(self, field, variable):
        if field.kind == "folder":
            path = filedialog.askdirectory(parent=self.window)
        else:
            path = filedialog.askopenfilename(parent=self.window)
        if path:
            variable.set(path)

    def _browse_list(self, control, folder):
        path = (filedialog.askdirectory(parent=self.window) if folder
                else filedialog.askopenfilename(parent=self.window))
        if path:
            existing = control.get("1.0", "end-1c")
            control.insert("end", ("\n" if existing and not existing.endswith("\n") else "") + path)

    def _save(self):
        try:
            settings = {}
            for field in TASK_TYPES[self._type()][1]:
                control = self.controls[field.key]
                value = control.get("1.0", "end-1c") if field.kind in ("list", "paths") else control.get()
                settings[field.key] = _parse_value(field, value)
            task = {"type": self._type(), "settings": settings}
            validate_task(task)
        except ValueError as exc:
            messagebox.showerror("Invalid task", str(exc), parent=self.window)
            return
        self.result = task
        self.window.destroy()
