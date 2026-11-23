import tkinter as tk
from tkinter import ttk, messagebox

from image_multitool.gui.options_window import THEMES

"""
Right-hand pane: queue status, queue/log text areas, and progress bar.

Written by: AJ Utz
Written on: 11/18/2026
Latest Update: 11/18/2026
"""

class QueuePanel(ttk.Frame):
    """Displays a ``TaskQueue`` and forwards user actions (cancel/start) to it."""

    def __init__(self, parent, gui):
        super().__init__(parent, padding=(10, 10))
        self.gui = gui # Reference the GUI object
        self.columnconfigure(0, weight=1) # Configure column for resizing
        self.rowconfigure(1, weight=1) # Configure row for resizing
        self._build_status_bar() # build and display the status bar
        self._build_text_areas() # Build and display the text areas
        self._build_progress_bar() # Build and display the progress bar

    @property
    def queue(self):
        return self.gui.queue # Getter for the TaskQueue instance

    def _build_status_bar(self):
        status_frame = ttk.Frame(self) #Ceate a frame for the status bar
        status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8)) #Position the status frame
        status_frame.columnconfigure(1, weight=1) #Configure the "Idle" status label

        ttk.Label(status_frame, text="Status:", font=(None, 10, "bold")).pack(side="left") #Display "Status:" label
        self.status_label = ttk.Label(status_frame, text="Idle", foreground="green", font=(None, 10)) #Display "Idle" status lable
        self.status_label.pack(side="left", padx=5) #position the "Idle" label

        ttk.Label(status_frame, text="|", foreground="gray").pack(side="left", padx=3) #Display vertical separator
        self.task_counter_label = ttk.Label(status_frame, text="Tasks: 0/0", font=(None, 9)) # Display "Tasks: 0/0" label
        self.task_counter_label.pack(side="left", padx=5) # Position the "Tasks: 0/0" label

        ttk.Label(status_frame, text="|", foreground="gray").pack(side="left", padx=3) # Display vertical separator
        self.cancel_button = ttk.Button(status_frame, text="Cancel Current", command=self.cancel_current, state="disabled") # Create "Cancel Current" button
        self.cancel_button.pack(side="left", padx=5) # Position the "Cancel Current" button
        self.cancel_pending_button = ttk.Button(status_frame, text="Cancel Pending...", command=self.cancel_pending, state="disabled") # Create "Cancel Pending..." button
        self.cancel_pending_button.pack(side="left", padx=5) # Position the "Cancel Pending..." button
        self.start_queue_button = ttk.Button(status_frame, text="Start Queue", command=self.start_queue, state="disabled") # Create "Start Queue" button
        self.start_queue_button.pack(side="left", padx=5) # Position the "Start Queue" button

    def _build_text_areas(self):
        self.paned_window = tk.PanedWindow(self, orient="vertical", sashwidth=5, bg="gray") # Create a vertical PanedWindow
        self.paned_window.grid(row=1, column=0, sticky="nsew", pady=(10, 0)) # Position the PanedWindow

        queue_frame = ttk.LabelFrame(self.paned_window, text="Active Tasks Queue", height=80) # Create a LabelFrame for the active tasks queue
        queue_frame.rowconfigure(0, weight=1) # Configure row for resizing
        queue_frame.columnconfigure(0, weight=1) # Configure column for resizing
        self.queue_text = tk.Text(queue_frame, wrap="word", height=4, font=(None, 8)) # Create a Text widget for the queue
        self.queue_text.grid(row=0, column=0, sticky="nsew") # Position the Text widget
        queue_scrollbar = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue_text.yview) # Create a vertical Scrollbar 
        queue_scrollbar.grid(row=0, column=1, sticky="ns") # Position the Scrollbar
        self.queue_text.config(yscrollcommand=queue_scrollbar.set, state="disabled")  # Configure Scrollbar for the queue
        self.paned_window.add(queue_frame, height=80) # Add the queue frame to the PanedWindow

        log_frame = ttk.LabelFrame(self.paned_window, text="Log") # Create a LabelFrame for the log
        log_frame.rowconfigure(0, weight=1) # Configure row for resizing
        log_frame.columnconfigure(0, weight=1) # Configure column for resizing
        self.log_text = tk.Text(log_frame, wrap="word", height=15) # Create a Text widget for the log
        self.log_text.grid(row=0, column=0, sticky="nsew") # Position the Text widget
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview) # Create a vertical Scrollbar for the log
        scrollbar.grid(row=0, column=1, sticky="ns") # Position the Scrollbar
        self.log_text.config(yscrollcommand=scrollbar.set) # Configure Scrollbar for the log

        # Text widgets swallow Tab by default, which traps keyboard users.
        self.log_text.bind("<Tab>", lambda e: (e.widget.tk_focusNext().focus_set(), "break")[1]) # Bind Tab key to switch focus
        self.log_text.bind("<Shift-Tab>", lambda e: (e.widget.tk_focusPrev().focus_set(), "break")[1]) # Bind Shift-Tab key to switch focus
        self.paned_window.add(log_frame, height=200) # Add the log frame to the PanedWindow

    def _build_progress_bar(self):
        bottom = ttk.Frame(self) # Create a frame for the progress bar
        bottom.grid(row=2, column=0, sticky="ew", pady=(8, 0)) # Position the progress bar frame
        bottom.columnconfigure(0, weight=1) # Configure column for resizing
        self.progress = ttk.Progressbar(bottom, mode="determinate", length=200, maximum=100) # Create a Progressbar widget
        self.progress.grid(row=0, column=0, sticky="ew") # Position the Progressbar widget
        self.progress_label = ttk.Label(bottom, text="", font=(None, 9))  # Create a Label widget for displaying progress information
        self.progress_label.grid(row=0, column=0, sticky="e", padx=5) # Position the Label widget

    def connect(self):
        """Hook the queue's callbacks up to this panel's widgets."""
        q = self.queue  # Get the TaskQueue instance
        q.on_change = self.refresh  # Set callback for queue changes
        q.on_running = self.show_running  # Set callback for running tasks
        q.on_cancelling = self.show_cancelling  # Set callback for tasks being cancelled
        q.on_idle = self.show_idle  # Set callback for idle queue
        q.on_progress = self.set_progress  # Set callback for progress updates
        self.show_idle(False)  # Show idle status
        self.refresh()  # Refresh the display

    # --- queue -> widgets -------------------------------------------------

    def show_running(self):
        """Update the status label to indicate that the queue is running and enable the cancel button."""
        self.status_label.config(text="Running...", foreground="#3cafe0")
        self.cancel_button.config(state="normal")

    def show_cancelling(self):
        """Update the status label to indicate that the queue is cancelling and disable the cancel button."""
        self.status_label.config(text="Cancelling...", foreground="orange")
        self.cancel_button.config(state="disabled")

    def show_idle(self, complete=False):
        """Update the status label to indicate that the queue is idle and disable the cancel button.
        If 'complete' is True, the label will be green, otherwise it will be grey."""
        self.status_label.config(text="Idle", foreground="green")
        self.cancel_button.config(state="disabled")

    def set_progress(self, percentage, text=None):
        """
        Set the progress bar value and update the progress label text.
        If 'text' is provided, it will be used instead of the percentage text.
        """
        try:
            self.progress["value"] = percentage
            self.progress_label.config(text=text if text is not None else f"{int(percentage)}%")
        except Exception:
            pass

    def refresh(self):
        """Redraw the queue summary in a thread-safe manner. This function can be called from any thread."""
        active, pending = self.queue.snapshot()
        self.gui._safe_after(0, self._render, active, pending)

    def _render(self, active, pending):
        """Render the queue summary text and update the UI elements."""
        try:
            self.queue_text.config(state="normal")
            self.queue_text.delete(1.0, tk.END)
            if not active and not pending:
                self.queue_text.insert(tk.END, "No active tasks\n")
            else:
                if active:
                    self.queue_text.insert(tk.END, f"▶ Running ({len(active)} active):\n")
                    for i, name in enumerate(active[:2], 1):
                        self.queue_text.insert(tk.END, f"  {i}. {name}\n")
                    if len(active) > 2:
                        self.queue_text.insert(tk.END, f"  ... +{len(active) - 2} more\n")
                if pending:
                    self.queue_text.insert(tk.END, f"\n⏳ Pending ({len(pending)}):\n")
                    for i, item in enumerate(pending[:2], 1):
                        name = item.get("task_name") if isinstance(item, dict) else str(item)
                        self.queue_text.insert(tk.END, f"  {i}. {name}\n")
                    if len(pending) > 2:
                        self.queue_text.insert(tk.END, f"  ... +{len(pending) - 2} more\n")
            self.queue_text.config(state="disabled")
            self.task_counter_label.config(text=f"Tasks: {len(active)} active, {len(pending)} pending")
            self.cancel_pending_button.config(state="normal" if pending else "disabled")
            self.update_start_button(bool(active), bool(pending))
        except tk.TclError:
            pass

    def update_start_button(self, running=None, has_pending=None):
        """
        Update the start queue button visibility based on the queue state.
        If auto-start is on, the button will be hidden. Otherwise, it will be shown.
        The start button will be enabled only if there are pending tasks and the queue is not running.
        """
        if running is None:
            running = self.queue.is_running
        if has_pending is None:
            has_pending = bool(self.queue.pending_tasks())
        try:
            if self.queue.auto_start:
                self.start_queue_button.pack_forget()
            else:
                self.start_queue_button.pack(side="left", padx=5)
                self.start_queue_button.config(state="normal" if (not running and has_pending) else "disabled")
        except tk.TclError:
            pass

    # --- user actions -----------------------------------------------------

    def start_queue(self):
        """Start the queue. After starting, update the start button to indicate that the queue is running."""
        self.queue.start()
        self.update_start_button()

    def cancel_current(self):
        """Cancel the currently running task in the queue."""
        self.queue.cancel_current()

    def cancel_pending(self):
        """Let the user pick a task that has not started yet and remove it from the queue."""
        pending_tasks = self.queue.pending_tasks()
        if not pending_tasks:
            return

        gui = self.gui
        dialog = tk.Toplevel(gui.root)
        dialog.title("Cancel Pending Task")
        dialog.transient(gui.root)
        dialog.resizable(True, True)
        dialog.geometry("360x240")
        dialog.configure(bg=gui.style.lookup("TFrame", "background"))
        dialog.minsize(360, 200)
        colors = THEMES.get(gui.current_theme, THEMES["light"])

        # Pack the buttons first so they keep their space when the dialog shrinks.
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=(5, 10))
        cancel_button = ttk.Button(button_frame, text="Cancel Selected Task", state="disabled")
        cancel_button.pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side="right")

        ttk.Label(dialog, text="Select a pending task to remove from the queue:").pack(
            side="top", anchor="w", padx=10, pady=(10, 5)
        )
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        task_list = tk.Listbox(
            list_frame,
            exportselection=False,
            bg=colors["text_bg"],
            fg=colors["text_fg"],
            selectbackground=colors["progress_color"],
            selectforeground=colors["text_bg"],
            highlightthickness=0,
            relief="flat",
        )
        task_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=task_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        task_list.config(yscrollcommand=scrollbar.set)
        for index, task_item in enumerate(pending_tasks, 1):
            task_list.insert(tk.END, f"{index}. {task_item['task_name']}")

        def _update_cancel_button(event):
            """Update the cancel button's state based on the selected task."""
            cancel_button.config(state="normal" if event.widget.curselection() else "disabled")

        def _cancel_selected(event=None):
            """Cancel the selected pending task from the queue."""
            if event is not None and event.widget is not task_list:
                return
            selection = task_list.curselection()
            if not selection:
                return
            task_item = pending_tasks[selection[0]]
            removed = self.queue.remove_pending(task_item)
            if not removed:
                messagebox.showinfo(
                    "Task Already Started",
                    f'"{task_item["task_name"]}" is no longer pending. Use Cancel Current if it is running.',
                    parent=dialog,
                )
            dialog.destroy()
            self.queue.update_status()

        task_list.bind("<<ListboxSelect>>", _update_cancel_button)
        task_list.bind("<Double-Button-1>", _cancel_selected)
        cancel_button.config(command=_cancel_selected)
        dialog.grab_set()
