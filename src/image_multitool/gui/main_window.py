import threading
import tkinter as tk
from tkinter import ttk, messagebox

from image_multitool.core.helpers import call_and_capture, resource_path
from image_multitool.core.settings import load_saved_auto_start
from image_multitool.core.task_queue import TaskQueue
from image_multitool.gui.dialogs import DialogMixin
from image_multitool.gui.konami import KonamiEasterEgg
from image_multitool.gui.options_window import OptionsWindow, apply_theme, load_saved_theme, set_theme
from image_multitool.gui.queue_panel import QueuePanel
from image_multitool.gui.workflows.editor import WorkflowEditor
from image_multitool.tools.registry import TOOLS
from image_multitool.version import VERSION

"""Main window: layout and callback wiring only.

Tool behaviour lives in ``image_multitool.tools.*.run_dialog``, queueing in
``core.task_queue``, dialogs in ``gui.dialogs`` and the queue/log pane in
``gui.queue_panel``.

Written by: AJ Utz
Written on: 11/18/2026
Latest Update: 11/18/2026
"""

class GUI(DialogMixin):
    def __init__(self, root):
        self.root = root
        root.title(f"Multitool GUI v{VERSION}")
        try:
            root.state("zoomed")
        except tk.TclError:
            try:
                root.attributes("-zoomed", True)
            except tk.TclError:
                root.state("normal")
        root.protocol("WM_DELETE_WINDOW", self._on_exit)

        self.workflow_editor = None
        self.style = ttk.Style(root)
        self.current_theme = "light"

        self.queue = TaskQueue(
            log=self.log,
            schedule=self._safe_after,
            runner=lambda func, *a, **kw: call_and_capture(self, func, *a, **kw),
            auto_start=load_saved_auto_start(),
        )

        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        self._build_tool_list(root)

        self.panel = QueuePanel(root, self)
        self.panel.grid(row=0, column=1, sticky="nsew")
        # Names the theme code (options_window.apply_theme) looks up on the GUI.
        self.right = self.panel
        for name in ("paned_window", "queue_text", "log_text", "status_label",
                     "task_counter_label", "cancel_button", "progress", "progress_label"):
            setattr(self, name, getattr(self.panel, name))

        set_theme(self, load_saved_theme())
        self.panel.connect()

        # ttk buttons only invoke on <space>; make <Return> work app-wide.
        root.bind_class("TButton", "<Return>", lambda e: e.widget.invoke())

        self.konami = KonamiEasterEgg(root, self.log, resource_path)

        try:
            self.executor.submit(self._run_update_check, False)
        except Exception:
            pass

    def _build_tool_list(self, root):
        left = ttk.Frame(root, padding=(10, 10))
        left.grid(row=0, column=0, sticky="ns")

        ttk.Label(left, text="Tools", font=(None, 12, "bold")).pack(anchor="w")
        ttk.Label(left, text=f"Version {VERSION}").pack(anchor="w", pady=(0, 10))

        for tool in TOOLS:
            frame = ttk.Frame(left)
            frame.pack(fill="x", pady=6)
            ttk.Button(frame, text=tool.label, command=lambda t=tool: t.launch(self)).pack(side="left", fill="x", expand=True)
            ttk.Button(
                frame, text="?", width=3,
                command=lambda t=tool: messagebox.showinfo(f"Requirements for {t.label}", t.requirement),
            ).pack(side="right")

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=8)
        ttk.Button(left, text="Workflows", width=28, command=self._open_workflows).pack(pady=(0, 6))
        ttk.Button(left, text="Options", width=28, command=self._open_options).pack(pady=(0, 6))
        ttk.Button(left, text="Exit", width=28, command=self._on_exit).pack()

    # --- queue access used by tools, options and tests --------------------

    @property
    def executor(self):
        return self.queue.executor

    @property
    def task_queue(self):
        return self.queue.task_queue

    @property
    def auto_start(self):
        return self.queue.auto_start

    def run_in_thread(self, func, task_name="Task", *args, **kwargs):
        """Queue ``func`` to run in the background, one task at a time, in order."""
        self.queue.submit(func, task_name, *args, **kwargs)

    def _enqueue_workflow_tasks(self, prepared_tasks):
        self.queue.submit_items([
            {
                "func": task.func,
                "args": (),
                "kwargs": dict(task.kwargs, logger=self.log),
                "task_name": task.task_name,
            }
            for task in prepared_tasks
        ])

    # --- logging ------------------------------------------------------------

    def _safe_after(self, delay, func, *args):
        """Schedule a Tk call from any thread; ignore it if the loop isn't running."""
        try:
            self.root.after(delay, func, *args)
        except RuntimeError:
            pass

    def log(self, message):
        """Thread-safe append to the log pane."""
        if not message:
            return
        if self.konami.check_konami_message(str(message)):
            self.konami._trigger_konami_reward()

        def _append():
            try:
                self.log_text.insert(tk.END, str(message) + "\n")
                self.log_text.see(tk.END)
            except RuntimeError:
                pass
        self._safe_after(0, _append)

    # --- windows ------------------------------------------------------------

    def _apply_theme(self, theme):
        apply_theme(self, theme)

    def _open_options(self):
        OptionsWindow(self.root, self)

    def _open_workflows(self):
        if self.workflow_editor is not None and self.workflow_editor.window.winfo_exists():
            self.workflow_editor.window.lift()
        else:
            self.workflow_editor = WorkflowEditor(self.root, self._enqueue_workflow_tasks)

    def _on_exit(self):
        """Close the app and stop background workers."""
        if (self.workflow_editor is not None and self.workflow_editor.window.winfo_exists()
                and not self.workflow_editor.close()):
            return
        self.queue.shutdown()
        try:
            self.root.destroy()
        except Exception:
            pass

    # --- update check -------------------------------------------------------

    def trigger_update_check(self, force=False):
        """Run an update check off the UI thread."""
        try:
            self.executor.submit(self._run_update_check, bool(force))
        except Exception:
            threading.Thread(target=self._run_update_check, args=(bool(force),), daemon=True).start()

    def _run_update_check(self, force=False):
        try:
            from image_multitool.services import updates

            available, local, latest = updates.is_update_available(force=force)
        except Exception as e:
            try:
                self.log(f"Update check failed: {e}")
            except Exception:
                pass
            return

        def _notify():
            if latest is None:
                if force:
                    messagebox.showinfo("Update Check", "Could not determine latest version from GitHub.")
                return

            self.log(f"Local version: {local or '(unknown)'}; Latest: {latest}")
            if available:
                if self.ask_yes_no("Update available", f"A new version ({latest}) is available. Open releases page?"):
                    try:
                        if not updates.open_releases_page():
                            self.log("Could not open release page automatically. URL: " + updates.get_latest_release_url())
                    except Exception:
                        pass
            elif force:
                messagebox.showinfo("Update Check", f"You are up to date. Latest: {latest}")

        try:
            self._safe_after(0, _notify)
        except Exception:
            _notify()
