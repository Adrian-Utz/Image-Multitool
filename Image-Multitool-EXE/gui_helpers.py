import os
from tkinter import filedialog, messagebox, simpledialog

#This file contains helper methods for the GUI to keep the main code cleaner and more focused on logic rather than UI details.

#Written by: AJ Utz on 5/20/2026
#Last updated: 7/3/2026

try:
    import pandas as pd
except Exception:
    pd = None


def select_folder(title):
    """Show a folder selection dialog and return the path or None."""
    return filedialog.askdirectory(title=title) or None


def select_file(title, filetypes=None):
    """Show a file selection dialog and return the path or None."""
    return filedialog.askopenfilename(title=title, filetypes=filetypes) or None


def ask_yes_no(title, message):
    return messagebox.askyesno(title, message)


def ask_string(title, prompt, initial=""):
    return simpledialog.askstring(title, prompt, initialvalue=initial)


def load_excel_columns(path):
    """Load an Excel file and return its column names as a list."""
    if pd is None:
        raise RuntimeError("pandas is required to load Excel files")
    df = pd.read_excel(path)
    return df.columns.tolist()


def parse_size_to_kb(text, default_kb=100):
    """Parse user input like '100KB' or '1MB' and return integer KB value."""
    if not text:
        return default_kb
    t = str(text).strip().upper()
    try:
        if t.endswith("MB"):
            return int(float(t[:-2].strip()) * 1024)
        if t.endswith("KB"):
            return int(float(t[:-2].strip()))
        return int(float(t))
    except Exception:
        return default_kb


def start_tool_task(gui, func, task_name, **kwargs):
    """Centralized starter that logs and calls `gui.run_in_thread`.

    Keeps logger/cancel/progress behavior consistent.
    """
    gui.log(f"[STARTING] {task_name}")
    gui.run_in_thread(func, task_name=task_name, logger=gui.log, **kwargs)


def call_and_capture(gui, func, *args, **kwargs):
    """Call a function and capture stdout/exceptions, logging via gui.log.

    This matches the previous `GUI._call_and_capture` semantics.
    """
    import io
    import contextlib

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            func(*args, **kwargs)
    except Exception as e:
        buf.write(f"[ERROR] {e}\n")
    output = buf.getvalue()
    if output:
        try:
            gui.log(output.rstrip())
        except Exception:
            # If gui.log fails, fallback to printing
            print(output)


def parse_range_input(range_input, columns):
    """Parse range input like '2-5' or '1,3,5-7' and return list of column names.

    Returns empty list on invalid input.
    """
    parsed_cols = []
    if not range_input:
        return parsed_cols
    # Support both comma-separated and dash-separated inputs
    for item in str(range_input).split(','):
        item = item.strip()
        # Skip empty items (e.g. from trailing commas)
        if not item:
            continue
        # Handle range like "2-5"
        if "-" in item:
            try:
                parts = item.split("-")
                start, end = int(parts[0].strip()), int(parts[1].strip())
                # Add columns in the specified range (inclusive)
                for idx in range(start, end + 1):
                    if 0 <= idx < len(columns):
                        parsed_cols.append(columns[idx])
            except Exception:
                # ignore invalid ranges
                continue
        # Handle single index or column name
        else:
            try:
                idx = int(item)
                if 0 <= idx < len(columns):
                    parsed_cols.append(columns[idx])
            except Exception:
                if item in columns:
                    parsed_cols.append(item)
    return parsed_cols


def parse_dimensions(dim_text):
    """Parse dimension strings like '1200x1200', '525px by 700px', or '525 x 700' into (width, height) or None."""
    if not dim_text:
        return None

    text = str(dim_text).strip().lower()
    if not text:
        return None

    if 'by' in text:
        parts = text.split('by', 1)
        if len(parts) != 2:
            return None
        text = f"{parts[0]}x{parts[1]}"

    text = text.replace('px', '').replace(' ', '')

    if 'x' not in text:
        return None

    try:
        w, h = text.split('x', 1)
        return (int(w), int(h))
    except Exception:
        return None


def resource_path(relative_path):
    """Return absolute path to resource (works with PyInstaller)."""
    import sys
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

def queue_task():
    return None

def _default_theme():
    """"Returns the Last used theme or a the default if none is found"""


