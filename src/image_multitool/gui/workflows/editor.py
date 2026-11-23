import copy
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from image_multitool.gui.workflows.task_dialog import TaskDialog
from image_multitool.workflows.models import TASK_TYPES, new_workflow, prepare_workflow_tasks, validate_workflow
from image_multitool.workflows.storage import (
    _is_managed_workflow,
    _reserve_workflow_path,
    load_workflow,
    migrate_legacy_workflows,
    save_workflow,
    workflow_directory,
)

"""
Workflow editor window: create, save, load and queue workflows.

Written by: AJ Utz
Written on: 11/18/2026
Latest Update: 11/18/2026
"""

class WorkflowEditor:
    def __init__(self, parent, enqueue_tasks):
        self.window = tk.Toplevel(parent)
        self.window.title("Workflow editor")
        self.window.transient(parent)
        self.window.geometry("1000x520")
        self.workflow = new_workflow()
        self.saved = copy.deepcopy(self.workflow)
        self.path = None
        self.name = tk.StringVar()
        self.enqueue_tasks = enqueue_tasks
        self.saved_paths = []

        layout = ttk.Frame(self.window)
        layout.pack(fill="both", expand=True)
        library = ttk.LabelFrame(layout, text="Saved workflows", padding=10)
        library.pack(side="left", fill="y", padx=(10, 0), pady=10)
        library_list = ttk.Frame(library)
        library_list.pack(fill="both", expand=True)
        self.saved_list = tk.Listbox(library_list, width=30, exportselection=False)
        self.saved_list.pack(side="left", fill="both", expand=True)
        library_vertical = ttk.Scrollbar(library_list, orient="vertical", command=self.saved_list.yview)
        library_vertical.pack(side="right", fill="y")
        library_scroll = ttk.Scrollbar(library, orient="horizontal", command=self.saved_list.xview)
        library_scroll.pack(fill="x")
        self.saved_list.config(xscrollcommand=library_scroll.set, yscrollcommand=library_vertical.set)
        for label, command in (("Open Selected", self._open_selected),
                               ("Queue Selected", self._queue_selected),
                               ("Refresh", self._refresh_saved_list)):
            ttk.Button(library, text=label, command=command).pack(fill="x", pady=(5, 0))
        self.saved_list.bind("<Double-Button-1>", lambda _event: self._open_selected())

        editor = ttk.Frame(layout)
        editor.pack(side="left", fill="both", expand=True)
        top = ttk.Frame(editor, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Workflow name:").pack(side="left")
        ttk.Entry(top, textvariable=self.name).pack(side="left", fill="x", expand=True, padx=8)

        files = ttk.Frame(editor, padding=(10, 0))
        files.pack(fill="x")
        for label, command in (("New", self._new), ("Import...", self._open), ("Save", self._save),
                               ("Duplicate...", self._duplicate), ("Delete", self._delete)):
            ttk.Button(files, text=label, command=command).pack(side="left", padx=(0, 5))
        self.queue_editor_button = ttk.Button(files, text="Add to Queue", command=self._activate)
        self.queue_editor_button.pack(side="right")

        body = ttk.Frame(editor, padding=10)
        body.pack(fill="both", expand=True)
        self.tasks = tk.Listbox(body, exportselection=False)
        self.tasks.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.tasks.yview)
        scrollbar.pack(side="left", fill="y")
        self.tasks.config(yscrollcommand=scrollbar.set)
        actions = ttk.Frame(body, padding=(10, 0))
        actions.pack(side="left", fill="y")
        for label, command in (("Add...", self._add), ("Edit...", self._edit), ("Remove", self._remove),
                               ("Move up", lambda: self._move(-1)), ("Move down", lambda: self._move(1))):
            ttk.Button(actions, text=label, command=command).pack(fill="x", pady=(0, 5))
        self.tasks.bind("<Double-Button-1>", lambda _event: self._edit())
        ttk.Label(editor, text="Add to Queue uses current settings, including unsaved edits; auto-start still applies.",
                  padding=(10, 0, 10, 10)).pack(anchor="w")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self._refresh_saved_list()

    def _current(self):
        workflow = copy.deepcopy(self.workflow)
        workflow["name"] = self.name.get().strip()
        return workflow

    def _confirm_discard(self):
        if self._current() == self.saved:
            return True
        answer = messagebox.askyesnocancel("Unsaved workflow", "Save changes to this workflow?",
                                           parent=self.window)
        if answer is None:
            return False
        return self._save() if answer else True

    def _set_workflow(self, workflow, path):
        self.workflow = copy.deepcopy(workflow)
        self.saved = copy.deepcopy(workflow)
        self.path = path
        self.name.set(workflow["name"])
        self._refresh()
        self.window.title(f"Workflow editor - {workflow['name']}" if workflow["name"] else "Workflow editor")

    def _refresh(self, selected=None):
        self.tasks.delete(0, tk.END)
        for index, task in enumerate(self.workflow["tasks"], 1):
            self.tasks.insert(tk.END, f"{index}. {TASK_TYPES[task['type']][0]}")
        if selected is not None and 0 <= selected < len(self.workflow["tasks"]):
            self.tasks.selection_set(selected)
            self.tasks.activate(selected)
            self.tasks.see(selected)

    def _new(self):
        if self._confirm_discard():
            self._set_workflow(new_workflow(), None)

    def _refresh_saved_list(self, select_path=None):
        if select_path is None:
            selected = self.saved_list.curselection()
            if selected:
                select_path = self.saved_paths[selected[0]]
        try:
            migrate_legacy_workflows()
        except OSError as exc:
            messagebox.showerror("Cannot migrate workflows", str(exc), parent=self.window)
            return
        try:
            with os.scandir(workflow_directory()) as entries:
                paths = [entry.path for entry in entries
                         if entry.is_file() and entry.name.lower().endswith(".json")]
        except FileNotFoundError:
            paths = []
        except OSError as exc:
            messagebox.showerror("Cannot list workflows", str(exc), parent=self.window)
            return

        items = []
        for path in paths:
            filename = os.path.basename(path)
            try:
                name = load_workflow(path)["name"]
                label = f"{name} ({filename})"
            except (OSError, UnicodeError, ValueError) as exc:
                label = f"{filename} [Invalid or unreadable: {' '.join(str(exc).splitlines())}]"
            items.append((label, path))
        items.sort(key=lambda item: item[0].casefold())
        self.saved_list.delete(0, tk.END)
        self.saved_paths = []
        for index, (label, path) in enumerate(items):
            self.saved_list.insert(tk.END, label)
            self.saved_paths.append(path)
            if select_path and os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(select_path)):
                self.saved_list.selection_set(index)
                self.saved_list.activate(index)
                self.saved_list.see(index)

    def _selected_saved_path(self):
        selection = self.saved_list.curselection()
        if not selection:
            messagebox.showinfo("Select a workflow", "Select a saved workflow first.", parent=self.window)
            return None
        return self.saved_paths[selection[0]]

    def _open_selected(self):
        path = self._selected_saved_path()
        if not path or not self._confirm_discard():
            return
        try:
            document = load_workflow(path)
        except (OSError, UnicodeError, ValueError) as exc:
            messagebox.showerror("Cannot open workflow", str(exc), parent=self.window)
            return
        self._set_workflow(document, path if _is_managed_workflow(path) else None)
        self._refresh_saved_list(path)

    def _queue_selected(self):
        path = self._selected_saved_path()
        if not path:
            return
        try:
            document = load_workflow(path)
        except (OSError, UnicodeError, ValueError) as exc:
            messagebox.showerror("Cannot add workflow", str(exc), parent=self.window)
            return
        self._queue_workflow(document)

    def _open(self):
        if not self._confirm_discard():
            return
        directory = workflow_directory()
        initialdir = directory if os.path.isdir(directory) else os.path.dirname(directory)
        path = filedialog.askopenfilename(parent=self.window, title="Open workflow",
                                          initialdir=initialdir,
                                          filetypes=[("Workflow JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            workflow = load_workflow(path)
        except (OSError, UnicodeError, ValueError) as exc:
            messagebox.showerror("Cannot open workflow", str(exc), parent=self.window)
            return
        managed_path = path if _is_managed_workflow(path) else None
        self._set_workflow(workflow, managed_path)
        if managed_path:
            self._refresh_saved_list(managed_path)

    def _save_to(self, workflow, path):
        try:
            save_workflow(path, workflow)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot save workflow", str(exc), parent=self.window)
            return False
        self._set_workflow(workflow, path)
        self._refresh_saved_list(path)
        return True

    def _save_new(self, workflow):
        path = None
        try:
            path = _reserve_workflow_path(workflow["name"])
            save_workflow(path, workflow)
        except (OSError, ValueError) as exc:
            if path:
                try:
                    os.remove(path)
                except OSError as cleanup_error:
                    messagebox.showerror(
                        "Cannot save workflow",
                        f"{exc}\nCould not remove incomplete file {path}: {cleanup_error}",
                        parent=self.window,
                    )
                    return False
            messagebox.showerror("Cannot save workflow", str(exc), parent=self.window)
            return False
        self._set_workflow(workflow, path)
        self._refresh_saved_list(path)
        return True

    def _save(self):
        workflow = self._current()
        try:
            validate_workflow(workflow)
        except ValueError as exc:
            messagebox.showerror("Cannot save workflow", str(exc), parent=self.window)
            return False
        return self._save_to(workflow, self.path) if self.path else self._save_new(workflow)

    def _activate(self):
        self._queue_workflow(self._current())

    def _queue_workflow(self, document):
        try:
            tasks = prepare_workflow_tasks(document)
            if not tasks:
                raise ValueError("Add at least one task to the workflow.")
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Cannot add workflow", str(exc), parent=self.window)
            return
        self.enqueue_tasks(tasks)
        messagebox.showinfo("Workflow queued", f"Added {len(tasks)} task(s) to the queue.",
                            parent=self.window)

    def _duplicate(self):
        name = simpledialog.askstring("Duplicate workflow", "Name for the copy:",
                                      initialvalue=self.name.get() + " copy", parent=self.window)
        if name is None:
            return
        workflow = self._current()
        workflow["name"] = name.strip()
        try:
            validate_workflow(workflow)
        except ValueError as exc:
            messagebox.showerror("Cannot duplicate workflow", str(exc), parent=self.window)
            return
        self._save_new(workflow)

    def _delete(self):
        if not self.path:
            messagebox.showinfo("Delete workflow", "Save this workflow before deleting it.", parent=self.window)
            return
        if not messagebox.askyesno("Delete workflow", f"Delete the saved workflow file?\n\n{self.path}\n\nUnsaved changes will also be lost.",
                                   parent=self.window):
            return
        try:
            os.remove(self.path)
        except OSError as exc:
            messagebox.showerror("Cannot delete workflow", str(exc), parent=self.window)
            return
        self._set_workflow(new_workflow(), None)
        self._refresh_saved_list()

    def _selection(self):
        selection = self.tasks.curselection()
        if not selection:
            messagebox.showinfo("Select a task", "Select a task first.", parent=self.window)
            return None
        return selection[0]

    def _add(self):
        task = TaskDialog(self.window).result
        if task is not None:
            self.workflow["tasks"].append(task)
            self._refresh(len(self.workflow["tasks"]) - 1)

    def _edit(self):
        index = self._selection()
        if index is None:
            return
        task = TaskDialog(self.window, self.workflow["tasks"][index]).result
        if task is not None:
            self.workflow["tasks"][index] = task
            self._refresh(index)

    def _remove(self):
        index = self._selection()
        if index is not None:
            del self.workflow["tasks"][index]
            self._refresh(min(index, len(self.workflow["tasks"]) - 1))

    def _move(self, direction):
        index = self._selection()
        if index is None:
            return
        target = index + direction
        tasks = self.workflow["tasks"]
        if 0 <= target < len(tasks):
            tasks[index], tasks[target] = tasks[target], tasks[index]
            self._refresh(target)

    def close(self):
        if self._confirm_discard():
            self.window.destroy()
            return True
        return False
