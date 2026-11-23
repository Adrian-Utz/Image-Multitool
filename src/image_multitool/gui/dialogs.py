import tkinter as tk
from tkinter import ttk, messagebox

from image_multitool.core.helpers import parse_range_input

"""Themed modal dialogs shared by every tool handler.

``DialogMixin`` expects the host to provide ``root`` (Tk) and ``style`` (ttk.Style).

Written by: AJ Utz
Written on: 11/18/2026
Latest Update: 11/18/2026
"""

class DialogMixin:
    def _center_window(self, win):
        """Position a Toplevel window centered over the main application window."""
        win.update_idletasks()
        width = win.winfo_width() or win.winfo_reqwidth()
        height = win.winfo_height() or win.winfo_reqheight()
        x = self.root.winfo_rootx() + max((self.root.winfo_width() - width) // 2, 0)
        y = self.root.winfo_rooty() + max((self.root.winfo_height() - height) // 2, 0)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def _bind_lr_toggle(self, widgets):
        """Let Left/Right arrows cycle focus across a row of buttons (e.g. OK/Cancel)."""
        def handler(event):
            try:
                idx = widgets.index(event.widget)
            except ValueError:
                idx = 0
            direction = 1 if event.keysym == "Right" else -1
            widgets[(idx + direction) % len(widgets)].focus_set()
            return "break"
        for w in widgets:
            w.bind("<Left>", handler)
            w.bind("<Right>", handler)

    def _build_column_list(self, win, columns, instructions, wraplength=None, multiple=False):
        """Shared search box + listbox used by the column pickers. Returns (search_entry, listbox)."""
        options = {"wraplength": wraplength} if wraplength else {}
        ttk.Label(win, text=instructions, anchor="center", font=(None, 10), **options).pack(fill="x", padx=5, pady=(10, 5))

        search_var = tk.StringVar()
        search_entry = ttk.Entry(win, textvariable=search_var)
        search_entry.pack(fill="x", padx=5, pady=5)

        list_frame = ttk.Frame(win)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=tk.MULTIPLE if multiple else tk.BROWSE)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        def update_list(*_args):
            query = search_var.get().lower()
            listbox.delete(0, tk.END)
            for i, col in enumerate(columns):
                if query in str(col).lower():
                    listbox.insert(tk.END, f"[{i}] {col}")

        search_var.trace_add("write", update_list)
        update_list()
        return search_entry, listbox

    @staticmethod
    def _focus_listbox(listbox):
        def handler(event=None):
            if listbox.size() > 0:
                listbox.focus_set()
                if not listbox.curselection():
                    listbox.selection_set(0)
                    listbox.activate(0)
            return "break"
        return handler

    def choose_column(self, title, columns):
        """Pick a single column from a searchable list; returns the name or None."""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("500x600")
        self._center_window(win)

        selected = {"value": None}
        search_entry, listbox = self._build_column_list(
            win, columns, "Type in the search box to filter columns. Double-click a column to select it."
        )

        def on_select(event):
            sel = listbox.curselection()
            if sel:
                # Entries look like "[i] colname"
                selected["value"] = listbox.get(sel[0]).split("] ", 1)[1]
                win.destroy()

        listbox.bind("<Double-1>", on_select)
        listbox.bind("<Return>", on_select)

        focus_listbox = self._focus_listbox(listbox)
        win.bind("<Escape>", lambda e: win.destroy())
        search_entry.bind("<Return>", focus_listbox)
        search_entry.bind("<Down>", focus_listbox)
        search_entry.focus_set()

        win.lift()
        win.focus_force()
        win.grab_set()
        win.wait_window()
        return selected["value"]

    def choose_columns(self, title, columns):
        """Choose multiple columns with range support (e.g., 2-5)."""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("600x700")
        self._center_window(win)

        selected = {"values": []}
        search_entry, listbox = self._build_column_list(
            win,
            columns,
            "Select columns by clicking, or enter ranges like '2-5' or '1,3,5-7' at the bottom. You can also mix both methods.",
            wraplength=580,
            multiple=True,
        )

        ttk.Label(win, text="Or enter range/list (e.g., '2-5' or '1,3,5-7'):", font=(None, 9)).pack(anchor="w", padx=5, pady=(5, 2))
        range_var = tk.StringVar()
        range_entry = ttk.Entry(win, textvariable=range_var)
        range_entry.pack(fill="x", padx=5, pady=(0, 5))

        button_frame = ttk.Frame(win)
        button_frame.pack(fill="x", padx=5, pady=5)

        def on_apply():
            range_input = range_var.get().strip()
            if range_input:
                parsed_cols = parse_range_input(range_input, columns)
            else:
                parsed_cols = [listbox.get(i).split("] ", 1)[1] for i in listbox.curselection()]

            if not parsed_cols:
                messagebox.showwarning("No selection", "Please select at least one column.")
                return

            selected["values"] = parsed_cols
            win.destroy()

        def on_cancel():
            selected["values"] = []
            win.destroy()

        ok_btn = ttk.Button(button_frame, text="OK", command=on_apply)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=on_cancel)
        ok_btn.pack(side="right", padx=2)
        cancel_btn.pack(side="right", padx=2)

        def _toggle_active(event=None):
            active = listbox.index("active")
            if active in listbox.curselection():
                listbox.selection_clear(active)
            else:
                listbox.selection_set(active)
            return "break"

        # Multi-select listboxes don't select-on-arrow, so <space> toggles the active item.
        listbox.bind("<space>", _toggle_active)
        listbox.bind("<Return>", lambda e: on_apply())

        self._bind_lr_toggle([ok_btn, cancel_btn])

        focus_listbox = self._focus_listbox(listbox)
        win.bind("<Escape>", lambda e: on_cancel())
        search_entry.bind("<Return>", focus_listbox)
        search_entry.bind("<Down>", focus_listbox)
        range_entry.bind("<Return>", lambda e: on_apply())
        search_entry.focus_set()

        win.lift()
        win.focus_force()
        win.grab_set()
        win.wait_window()
        return selected["values"]

    def choose_option(self, title, prompt, options, default=None):
        """Custom option selection box."""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=self.style.lookup("TFrame", "background"))

        selected = tk.StringVar(value=default if default in options else options[0])

        ttk.Label(win, text=prompt, wraplength=380).pack(fill="x", padx=10, pady=(10, 5))

        radio_buttons = []
        for option in options:
            rb = ttk.Radiobutton(win, text=option.capitalize(), variable=selected, value=option)
            rb.pack(anchor="w", padx=20, pady=2)
            radio_buttons.append(rb)

        def _cancel():
            selected.set(default if default else options[0])
            win.destroy()

        button_frame = ttk.Frame(win)
        button_frame.pack(fill="x", pady=10, padx=10)
        ok_btn = ttk.Button(button_frame, text="OK", command=win.destroy)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=_cancel)
        ok_btn.pack(side="right")
        cancel_btn.pack(side="right", padx=(0, 5))

        # Arrow keys move focus/selection between radio options like a native radio group.
        def _move_focus(delta):
            def handler(event):
                try:
                    idx = radio_buttons.index(event.widget)
                except ValueError:
                    idx = 0
                next_widget = radio_buttons[(idx + delta) % len(radio_buttons)]
                next_widget.focus_set()
                next_widget.invoke()
                return "break"
            return handler

        for rb in radio_buttons:
            rb.bind("<Down>", _move_focus(1))
            rb.bind("<Right>", _move_focus(1))
            rb.bind("<Up>", _move_focus(-1))
            rb.bind("<Left>", _move_focus(-1))
            rb.bind("<Return>", lambda e: win.destroy())

        # <Return> on OK/Cancel is handled by the app-wide TButton class binding.
        self._bind_lr_toggle([ok_btn, cancel_btn])

        win.bind("<Escape>", lambda e: _cancel())
        win.bind("<Return>", lambda e: win.destroy())

        # Size after all controls exist so the action buttons stay visible.
        win.update_idletasks()
        win.geometry(f"{max(400, win.winfo_reqwidth())}x{max(150, win.winfo_reqheight())}")
        win.resizable(False, False)
        self._center_window(win)

        win.lift()
        win.focus_force()
        win.grab_set()
        # Must run after focus_force(), otherwise the toplevel steals focus back.
        for rb in radio_buttons:
            if rb.cget("value") == selected.get():
                rb.focus_set()
                break
        win.wait_window()

        return selected.get()

    def _simple_dialog(self, title, min_size):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=self.style.lookup("TFrame", "background"))
        win.resizable(False, False)
        win.transient(self.root)
        return win

    def _finish_simple_dialog(self, win, min_width, min_height):
        win.update_idletasks()
        win.geometry(f"{max(min_width, win.winfo_reqwidth())}x{max(min_height, win.winfo_reqheight())}")
        self._center_window(win)
        win.lift()
        win.focus_force()
        win.grab_set()

    def ask_yes_no(self, title, message, default="yes"):
        """Themed replacement for messagebox.askyesno so the dialog follows the active theme."""
        win = self._simple_dialog(title, None)
        result = {"value": default == "yes"}

        ttk.Label(win, text=message, wraplength=360, justify="left").pack(fill="x", padx=15, pady=(15, 10))

        def _choose(value):
            result["value"] = value
            win.destroy()

        button_frame = ttk.Frame(win)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        yes_btn = ttk.Button(button_frame, text="Yes", command=lambda: _choose(True))
        no_btn = ttk.Button(button_frame, text="No", command=lambda: _choose(False))
        first, second = (yes_btn, no_btn) if default == "yes" else (no_btn, yes_btn)
        first.pack(side="right")
        second.pack(side="right", padx=(0, 5))

        self._bind_lr_toggle([yes_btn, no_btn])
        win.protocol("WM_DELETE_WINDOW", lambda: _choose(False))
        win.bind("<Escape>", lambda e: _choose(False))
        self._finish_simple_dialog(win, 320, 120)
        first.focus_set()
        win.wait_window()
        return result["value"]

    def ask_string(self, title, prompt, initial=""):
        """Themed replacement for simpledialog.askstring."""
        win = self._simple_dialog(title, None)
        result = {"value": None}

        ttk.Label(win, text=prompt, wraplength=360, justify="left").pack(fill="x", padx=15, pady=(15, 5))
        entry_var = tk.StringVar(value=initial)
        entry = ttk.Entry(win, textvariable=entry_var, width=40)
        entry.pack(fill="x", padx=15, pady=(0, 10))
        entry.focus_set()
        entry.icursor(tk.END)

        def _ok(event=None):
            result["value"] = entry_var.get()
            win.destroy()

        def _cancel():
            result["value"] = None
            win.destroy()

        button_frame = ttk.Frame(win)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        ok_btn = ttk.Button(button_frame, text="OK", command=_ok)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=_cancel)
        ok_btn.pack(side="right")
        cancel_btn.pack(side="right", padx=(0, 5))

        entry.bind("<Return>", _ok)
        self._bind_lr_toggle([ok_btn, cancel_btn])
        win.protocol("WM_DELETE_WINDOW", _cancel)
        win.bind("<Escape>", lambda e: _cancel())
        self._finish_simple_dialog(win, 320, 120)
        win.wait_window()
        return result["value"]

    def ask_integer(self, title, prompt, initial=None, minvalue=None, maxvalue=None):
        """Themed replacement for simpledialog.askinteger."""
        win = self._simple_dialog(title, None)
        result = {"value": None}

        ttk.Label(win, text=prompt, wraplength=360, justify="left").pack(fill="x", padx=15, pady=(15, 5))
        entry_var = tk.StringVar(value="" if initial is None else str(initial))
        entry = ttk.Entry(win, textvariable=entry_var, width=20)
        entry.pack(fill="x", padx=15, pady=(0, 5))
        entry.focus_set()
        entry.icursor(tk.END)

        error_label = ttk.Label(win, text="", foreground="red")
        error_label.pack(fill="x", padx=15)

        def _ok(event=None):
            try:
                value = int(entry_var.get().strip())
            except ValueError:
                error_label.config(text="Please enter a whole number.")
                return
            if minvalue is not None and value < minvalue:
                error_label.config(text=f"Value must be at least {minvalue}.")
                return
            if maxvalue is not None and value > maxvalue:
                error_label.config(text=f"Value must be at most {maxvalue}.")
                return
            result["value"] = value
            win.destroy()

        def _cancel():
            result["value"] = None
            win.destroy()

        button_frame = ttk.Frame(win)
        button_frame.pack(fill="x", padx=10, pady=(5, 10))
        ok_btn = ttk.Button(button_frame, text="OK", command=_ok)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=_cancel)
        ok_btn.pack(side="right")
        cancel_btn.pack(side="right", padx=(0, 5))

        entry.bind("<Return>", _ok)
        self._bind_lr_toggle([ok_btn, cancel_btn])
        win.protocol("WM_DELETE_WINDOW", _cancel)
        win.bind("<Escape>", lambda e: _cancel())
        self._finish_simple_dialog(win, 320, 140)
        win.wait_window()
        return result["value"]
