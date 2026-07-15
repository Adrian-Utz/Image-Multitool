import os
import sys
import tkinter as tk
import concurrent.futures
import threading

from tkinter import ttk, filedialog, messagebox, simpledialog
from collections import deque

from gui_helpers import (
    select_folder,
    select_file,
    ask_yes_no,
    ask_string,
    parse_size_to_kb,
    load_excel_columns,
    start_tool_task,
    call_and_capture,
    parse_range_input,
    parse_dimensions,
    resource_path,
)
from konami import KonamiEasterEgg
from options import OptionsWindow, apply_theme, set_auto_start, set_dark_mode, set_light_mode

#Version information! Change this variable when you update the application to keep track of versions in the UI and logs.
#Follow semantic versioning (major.minor.patch) for clarity.
VERSION = "1.2.6"

#Description:
#This is the main GUI application layer that integrates all the tools into a single interface. 
#It uses Tkinter for the GUI and concurrent.futures for running tasks in background threads while keeping the UI responsive. 
#Each tool is launched with user-selected options, and progress/status is displayed in the right pane.

#When you want to apply changes to the code. Run this in the terminal to rebuild the application and see the changes:
# .\.venv\Scripts\python.exe -m PyInstaller multitool.spec

#If the EXE is being made from a different location, adjust the path to pyinstaller.exe accordingly. Check out the Readme for more details.

#Written by: AJ Utz - and a little bit with the Ai Agent
#Written on: 3/19/2026
#Last updated: 7/13/2026

class GUI:
    def __init__(self, root):
        self.root = root
        root.title(f"Multitool GUI v{VERSION}")
        root.state("zoomed")  # Start maximized

        # Executor used to run tasks. We'll orchestrate submissions so only one
        # task runs at a time regardless of executor worker count.
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

        # Task queue tracking
        self.task_queue = deque()
        self.active_tasks = []
        self.task_lock = threading.Lock()
        self.current_progress = 0
        self.total_progress = 0
        self.completed_tasks = 0
        self.total_tasks_started = 0
        self.auto_start = True

        # Configure grid
        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        # Left pane (controls)
        left = ttk.Frame(root, padding=(10, 10))
        left.grid(row=0, column=0, sticky="ns")

        ttk.Label(left, text="Tools", font=(None, 12, "bold")).pack(anchor="w")
        ttk.Label(left, text=f"Version {VERSION}").pack(anchor="w", pady=(0, 10))

        # Define tools and their corresponding button commands and requirements
        tools = [
            ("Count files by extension", self.on_count_files, "Requires: A folder to scan for files."),
            ("List filenames", self.on_list_files, "Requires: A folder to list files from."),
            ("Search & Copy", self.on_search_files, "Requires: A source folder to search, search term or .txt file, and destination folder."),
            ("Image reformat", self.on_image_reformat, "Requires: A folder containing images to reformat."),
            ("Excel rename", self.on_rename_excel, "Requires: An Excel file with renaming data and a folder with images."),
            ("TXT <-> Excel Compare", self.on_compare_txt_excel, "Requires: A .txt file, an Excel file (.xlsx or .xls), and a column name."),
            ("Excel image downloader", self.on_download_from_excel, "Requires: An Excel file with image URLs and column names."),
            ("Folder compare", self.on_folder_compare, "Requires: Two folders to compare."),
        ]

        #Create buttons for each tool with help buttons
        #As long as there is a label, command, and requirements defined in the tools list, 
        #this loop will create a button for the tool and a help button that shows the requirements in a message box when clicked.
        for label, command, req in tools:
            frame = ttk.Frame(left)
            frame.pack(fill="x", pady=6)
            btn = ttk.Button(frame, text=label, command=command)
            btn.pack(side="left", fill="x", expand=True)
            help_btn = ttk.Button(frame, text="?", width=3, command=lambda r=req, l=label: messagebox.showinfo(f"Requirements for {l}", r))
            help_btn.pack(side="right")

        #Exit button at the bottom of the left pane with a separator above it
        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=8)
        ttk.Button(left, text="Options", width=28, command=self._open_options).pack(pady=(0, 6))
        ttk.Button(left, text="Exit", width=28, command=root.quit).pack()

        # Right pane (status + options + log)
        self.right = ttk.Frame(root, padding=(10, 10))
        right = self.right
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # Status header - shows current operation state
        status_frame = ttk.Frame(right)
        status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        status_frame.columnconfigure(1, weight=1)

        # Status label to show current status of the application (e.g., Idle, Running...)
        ttk.Label(status_frame, text="Status:", font=(None, 10, "bold")).pack(side="left")
        self.status_label = ttk.Label(status_frame, text="Idle", foreground="green", font=(None, 10))
        self.status_label.pack(side="left", padx=5)

        # Separator and task counter to show how many tasks are active/pending
        ttk.Label(status_frame, text="|", foreground="gray").pack(side="left", padx=3)
        self.task_counter_label = ttk.Label(status_frame, text="Tasks: 0/0", font=(None, 9))
        self.task_counter_label.pack(side="left", padx=5)

        # Separator and action buttons for queue control
        ttk.Label(status_frame, text="|", foreground="gray").pack(side="left", padx=3)
        self.cancel_button = ttk.Button(status_frame, text="Cancel Current", command=self._cancel_current_task, state="disabled")
        self.cancel_button.pack(side="left", padx=5)
        self.start_queue_button = ttk.Button(status_frame, text="Start Queue", command=self._start_queue, state="disabled")
        self.start_queue_button.pack(side="left", padx=5)

        # Resizable paned window for task queue and log
        paned_window = tk.PanedWindow(right, orient="vertical", sashwidth=5, bg="gray")
        paned_window.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.paned_window = paned_window

        # Task queue display
        queue_frame = ttk.LabelFrame(paned_window, text="Active Tasks Queue", height=80)
        queue_frame.rowconfigure(0, weight=1)
        queue_frame.columnconfigure(0, weight=1)

        # Task queue text widget (read-only)
        self.queue_text = tk.Text(queue_frame, wrap="word", height=4, font=(None, 8))
        self.queue_text.grid(row=0, column=0, sticky="nsew")
        queue_scrollbar = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue_text.yview)
        queue_scrollbar.grid(row=0, column=1, sticky="ns")
        self.queue_text.config(yscrollcommand=queue_scrollbar.set)
        self.queue_text.config(state="disabled")

        # Add queue frame to paned window
        paned_window.add(queue_frame, height=80)

        # Simple status / log area
        log_frame = ttk.LabelFrame(paned_window, text="Log")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        #Log text widget to display output and logs from tasks
        self.log_text = tk.Text(log_frame, wrap="word", height=15)
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar for the log text widget
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Add log frame to paned window
        paned_window.add(log_frame, height=200)

        # Initialize theme
        self.style = ttk.Style(self.root)
        self.current_theme = "light"
        self._set_light_mode()
        self._update_start_queue_button_state()
        self._update_status_idle()

        # Bottom progress bar
        bottom = ttk.Frame(right)
        bottom.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        bottom.columnconfigure(0, weight=1)

        # Progress bar with determinate mode (fills left to right)
        self.progress = ttk.Progressbar(bottom, mode="determinate", length=200, maximum=100)
        self.progress.grid(row=0, column=0, sticky="ew")

        # Progress label to show percentage and status
        self.progress_label = ttk.Label(bottom, text="", font=(None, 9))
        self.progress_label.grid(row=0, column=0, sticky="e", padx=5)

        # Initialize Konami easter egg
        self.konami = KonamiEasterEgg(root, self.log, resource_path)

        #Track the currently running task's future, cancel event, and name for cancellation and progress reporting
        self._current_task_future = None
        self._current_cancel_event = None
        self._current_task_name = None

    def _open_options(self):
        """Open the separate options dialog."""
        OptionsWindow(self.root, self)

    def _set_light_mode(self):
        """Switch the interface to light theme."""
        set_light_mode(self)

    def _set_dark_mode(self):
        """Switch the interface to dark theme."""
        set_dark_mode(self)

    def _apply_theme(self, theme):
        apply_theme(self, theme)

    def _update_start_queue_button_state(self):
        """Show or hide the start queue button based on queue state and auto-start setting."""
        try:
            if self.auto_start:
                self.start_queue_button.pack_forget()
            else:
                self.start_queue_button.pack(side="left", padx=5)
                if self._current_task_future is None and self.task_queue:
                    self.start_queue_button.config(state="normal")
                else:
                    self.start_queue_button.config(state="disabled")
        except Exception:
            pass

    def _start_queue(self):
        """Manually start the queued tasks when auto-start is disabled."""
        if self.auto_start:
            return
        if self._current_task_future is None and self.task_queue:
            self._process_queue()
            self._update_start_queue_button_state()

    # Helper method to safely call Tkinter operations from any thread
    def _safe_after(self, delay, func, *args):
        """Safely schedule a Tkinter operation from any thread."""
        try:
            self.root.after(delay, func, *args)
        except RuntimeError:
            # Main thread is not in main loop, silently skip
            pass

    # Thread-safe logging method to append messages to the log text widget
    def log(self, message):
        if not message:
            return

        # Check whether Konami code was typed directly in a log message
        if self.konami.check_konami_message(str(message)):
            self.konami._trigger_konami_reward()

        #This inner function is what actually updates the log text widget.
        #We use _safe_after to schedule it on the main thread, ensuring thread safety when updating the GUI from background tasks.
        def _append():
            try:
                self.log_text.insert(tk.END, str(message) + "\n")
                self.log_text.see(tk.END)
            except RuntimeError:
                pass
        self._safe_after(0, _append)

    # Update the task queue display with current active and pending tasks
    def _update_queue_display(self):
        """Update the task queue display"""
        def _update():
            self.queue_text.config(state="normal")
            self.queue_text.delete(1.0, tk.END)
            
            #Here we acquire the task lock to safely read the active and pending tasks. 
            #We then update the queue_text widget to show a summary of active and pending tasks, showing up to 2 of each with a count of additional tasks if there are more. 
            #Finally, we update the task counter label to show the counts.
            with self.task_lock:
                active_count = len(self.active_tasks)
                pending_count = len(self.task_queue)
                
                if active_count == 0 and pending_count == 0:
                    #Update the queue display to show no active tasks
                    self.queue_text.insert(tk.END, "No active tasks\n")
                    self.task_counter_label.config(text="Tasks: 0 active, 0 pending")
                else:
                    if active_count > 0:
                        self.queue_text.insert(tk.END, f"▶ Running ({active_count} active):\n")
                        for i, task_name in enumerate(self.active_tasks[:2], 1):
                            self.queue_text.insert(tk.END, f"  {i}. {task_name}\n")
                        if active_count > 2:
                            self.queue_text.insert(tk.END, f"  ... +{active_count - 2} more\n")
                    
                    #If there are pending tasks, we show them in the queue display as well, following the same format as active tasks.
                    if pending_count > 0:
                        self.queue_text.insert(tk.END, f"\n⏳ Pending ({pending_count}):\n")
                        for i, task_item in enumerate(list(self.task_queue)[:2], 1):
                            name = task_item.get('task_name') if isinstance(task_item, dict) else str(task_item)
                            self.queue_text.insert(tk.END, f"  {i}. {name}\n")
                        if pending_count > 2:
                            self.queue_text.insert(tk.END, f"  ... +{pending_count - 2} more\n")
                    
                    #Update the task counter label to show counts of active and pending tasks
                    self.task_counter_label.config(text=f"Tasks: {active_count} active, {pending_count} pending")
            
            #Finally, we set the queue_text widget back to read-only after updating it.
            self.queue_text.config(state="disabled")
        
        self._safe_after(0, _update)
        self._update_start_queue_button_state()

    def _cancel_current_task(self):
        """Cancel the currently running task."""
        # If there's a future for the current task, try to cancel it. Most
        # tasks are only submitted when running, so cancellation here often
        # won't succeed; we also treat queued (pending) items separately.
        if self._current_task_future:
            try:
                if self._current_task_future.cancel():
                    self.log("[INFO] Current task cancelled before start.")
                    with self.task_lock:
                        if self._current_task_name and self._current_task_name in self.active_tasks:
                            self.active_tasks.remove(self._current_task_name)
                        # Remove any pending queued item with same name
                        for item in list(self.task_queue):
                            if isinstance(item, dict) and item.get('task_name') == self._current_task_name:
                                try:
                                    self.task_queue.remove(item)
                                except ValueError:
                                    pass
                        self.completed_tasks += 1
                        self._current_task_future = None
                        self._current_cancel_event = None
                        self._current_task_name = None
                    self._update_status_idle()
                    self._update_queue_display()
                    return
            except Exception:
                pass

        #If the task is already running, we set the cancel event which the running task should check periodically to stop its execution.
        if self._current_cancel_event and not self._current_cancel_event.is_set():
            self._current_cancel_event.set()
            self.log("[INFO] Cancelling current task...")
            # remove the active task from the UI immediately
            with self.task_lock:
                if self._current_task_name and self._current_task_name in self.active_tasks:
                    self.active_tasks.remove(self._current_task_name)
                # Also remove any pending queued items that match the current name
                for item in list(self.task_queue):
                    if isinstance(item, dict) and item.get('task_name') == self._current_task_name:
                        try:
                            self.task_queue.remove(item)
                        except ValueError:
                            pass
            # Update status to show cancellation in progress
            try:
                self.status_label.config(text="Cancelling...", foreground="orange")
                self.cancel_button.config(state="disabled")
            except Exception:
                pass
            self._update_status_idle()
            self._update_queue_display()
            self._update_start_queue_button_state()

    def _update_status_idle(self):
        """Update status to idle when no tasks remain"""
        with self.task_lock:
            #If there are no active or pending tasks, we update the status label to show "Idle" and disable the cancel button.
            if len(self.active_tasks) == 0 and len(self.task_queue) == 0:
                self.status_label.config(text="Idle", foreground="green")
                self.cancel_button.config(state="disabled")
                if self.total_tasks_started > 0:
                    self._update_progress(100)
                    self.progress_label.config(text="Complete ✓")
                    # Reset counters for next batch of tasks
                    self.completed_tasks = 0
                    self.total_tasks_started = 0
            else:
                remaining = len(self.active_tasks) + len(self.task_queue)
                if self.total_tasks_started > 0:
                    progress_pct = int((self.completed_tasks / self.total_tasks_started) * 100)
                    self._update_progress(progress_pct)
                    self.progress_label.config(text=f"{progress_pct}% - {remaining} tasks remaining")
        
        self._update_queue_display()

    # Helper method to update progress bar with percentage
    def _update_progress(self, percentage=None):
        """Update progress bar with a percentage value (0-100)."""
        try:
            if percentage is not None:
                self.progress['value'] = percentage
                self.progress_label.config(text=f"{int(percentage)}%")
        except Exception:
            pass

    # Helper method for tasks to report their individual progress
    def _report_task_progress(self, task_name, percentage):
        """Allow running tasks to report their progress (0-100)"""
        try:
            # Only update if this is the currently active task
            with self.task_lock:
                if task_name in self.active_tasks:
                    self._update_progress(percentage)
        except Exception:
            pass

    # Used to update the GUI while a task is running in the background.
    def run_in_thread(self, func, task_name="Task", *args, **kwargs):
        """
        Enqueue a task to run in background threads but ensure only one task
        runs at a time. Tasks are executed in the order they were enqueued.
        """
        # Wrap task data into a dict stored in the deque so we can keep
        # structured info about pending tasks.
        task_item = {
            'func': func,
            'args': args,
            'kwargs': dict(kwargs),
            'task_name': task_name,
        }

        with self.task_lock:
            # Put on queue (pending)
            self.task_queue.append(task_item)
            self.total_tasks_started += 1

        self._update_queue_display()
        self._update_start_queue_button_state()

        # Try to start next task automatically when auto-start is enabled
        if self.auto_start:
            self._process_queue()

    def _process_queue(self):
        """Start the next queued task if no task is currently running."""
        with self.task_lock:
            # If a task is already running, do nothing.
            if self._current_task_future is not None:
                return

            if not self.task_queue:
                # Nothing to do; ensure UI shows idle when appropriate.
                # This branch exits the lock before updating the UI so we do not
                # re-enter the same lock from inside the status/queue methods.
                should_update_idle = True
            else:
                should_update_idle = False
                # Pop the next task (FIFO)
                task_item = self.task_queue.popleft()

                func = task_item['func']
                task_name = task_item['task_name']
                args = task_item.get('args', ())
                kwargs = task_item.get('kwargs', {})

                # Attach progress and cancel hooks
                kwargs['progress_callback'] = lambda pct: self._report_task_progress(task_name, pct)
                cancel_event = threading.Event()
                kwargs['cancel_event'] = cancel_event

                # Track current task
                self._current_cancel_event = cancel_event
                self._current_task_name = task_name
                # Mark as active for UI
                self.active_tasks.append(task_name)

                # Start progress indicator on main thread
                def _start_ui():
                    try:
                        self.status_label.config(text="Running...", foreground="#3cafe0")
                        self.cancel_button.config(state="normal")
                        self._update_progress(0)
                    except Exception:
                        pass

                self._safe_after(0, _start_ui)

                # Submit the task and arrange completion handling
                future = self.executor.submit(call_and_capture, self, func, *args, **kwargs)
                self._current_task_future = future

                def _on_done(fut):
                    def _finish():
                        try:
                            with self.task_lock:
                                self.completed_tasks += 1
                                # Remove from active list if present.
                                if task_name in self.active_tasks:
                                    self.active_tasks.remove(task_name)

                                # Clear current trackers if this was the running future.
                                if self._current_task_future is fut:
                                    self._current_task_future = None
                                    self._current_cancel_event = None
                                    self._current_task_name = None

                                # Update progress percentage.
                                if self.total_tasks_started > 0:
                                    progress_pct = int((self.completed_tasks / self.total_tasks_started) * 100)
                                    self._update_progress(progress_pct)
                        except Exception:
                            pass

                        # Update UI and then process the next queued task.
                        self._update_status_idle()
                        self._update_queue_display()
                        self._safe_after(200, self._process_queue)

                    # Schedule finish on main thread.
                    self._safe_after(500, _finish)

                future.add_done_callback(_on_done)

        if should_update_idle:
            self._update_status_idle()
            self._update_queue_display()
            self._update_start_queue_button_state()
            return

        self._update_queue_display()
        self._update_start_queue_button_state()

    # This method creates a new window with a scrollable list of columns from an Excel file, allowing the user to select one.
    def choose_column(self, title, columns):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("500x600")

        selected = {"value": None}

        #Label for instructions
        instructions_label = ttk.Label(
            win,
            text="Type in the search box to filter columns. Double-click a column to select it.",
            anchor="center",
            font=(None, 10)
        )
        instructions_label.pack(fill="x", padx=5, pady=(10, 5))

        # Search box
        search_var = tk.StringVar()
        search_entry = ttk.Entry(win, textvariable=search_var)
        search_entry.pack(fill="x", padx=5, pady=5)

        # Listbox with scrollbar
        list_frame = ttk.Frame(win)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        # Populate listbox
        def update_list(*args):
            query = search_var.get().lower()
            listbox.delete(0, tk.END)
            for i, col in enumerate(columns):
                if query in str(col).lower():
                    listbox.insert(tk.END, f"[{i}] {col}")

        search_var.trace_add("write", update_list)
        update_list()

        # Handle selection
        def on_select(event):
            sel = listbox.curselection()
            if sel:
                index = sel[0]
                selected_value = listbox.get(index)
                # Extract the actual column name from the string "[i] colname"
                col_name = selected_value.split("] ", 1)[1]
                selected["value"] = col_name
                win.destroy()

        listbox.bind("<Double-1>", on_select)

        # Wait for selection
        win.grab_set()
        win.wait_window()

        return selected["value"]

    def choose_columns(self, title, columns):
        """Choose multiple columns with range support (e.g., 2-5)"""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("600x700")

        selected = {"values": []}

        # Instructions label
        instructions_label = ttk.Label(
            win,
            text="Select columns by clicking, or enter ranges like '2-5' or '1,3,5-7' at the bottom. You can also mix both methods.",
            anchor="center",
            font=(None, 10),
            wraplength=580
        )
        instructions_label.pack(fill="x", padx=5, pady=(10, 5))

        # Search box
        search_var = tk.StringVar()
        search_entry = ttk.Entry(win, textvariable=search_var)
        search_entry.pack(fill="x", padx=5, pady=5)

        # Listbox with scrollbar
        list_frame = ttk.Frame(win)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=tk.MULTIPLE)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        # Populate listbox
        def update_list(*args):
            query = search_var.get().lower()
            listbox.delete(0, tk.END)
            for i, col in enumerate(columns):
                if query in str(col).lower():
                    listbox.insert(tk.END, f"[{i}] {col}")

        search_var.trace_add("write", update_list)
        update_list()

        # Text field for range input
        ttk.Label(win, text="Or enter range/list (e.g., '2-5' or '1,3,5-7'):", font=(None, 9)).pack(anchor="w", padx=5, pady=(5, 2))
        range_var = tk.StringVar()
        range_entry = ttk.Entry(win, textvariable=range_var)
        range_entry.pack(fill="x", padx=5, pady=(0, 5))

        # Buttons frame
        button_frame = ttk.Frame(win)
        button_frame.pack(fill="x", padx=5, pady=5)

        def on_apply():
            # Get selected from listbox or range input
            range_input = range_var.get().strip()
            if range_input:
                parsed_cols = parse_range_input(range_input)
            else:
                # Get from listbox selection
                parsed_cols = []
                for i in listbox.curselection():
                    selected_value = listbox.get(i)
                    col_name = selected_value.split("] ", 1)[1]
                    parsed_cols.append(col_name)
            
            if not parsed_cols:
                messagebox.showwarning("No selection", "Please select at least one column.")
                return

            selected["values"] = parsed_cols
            win.destroy()

        def on_cancel():
            selected["values"] = []
            win.destroy()

        ttk.Button(button_frame, text="OK", command=on_apply).pack(side="right", padx=2)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side="right", padx=2)

        # Wait for selection
        win.grab_set()
        win.wait_window()

        return selected["values"]

    def choose_option(self, title, prompt, options, default=None):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("400x180")
        win.resizable(False, False)

        selected = tk.StringVar(value=default if default in options else options[0])

        ttk.Label(win, text=prompt, wraplength=380).pack(fill="x", padx=10, pady=(10, 5))

        for option in options:
            ttk.Radiobutton(win, text=option.capitalize(), variable=selected, value=option).pack(anchor="w", padx=20, pady=2)

        button_frame = ttk.Frame(win)
        button_frame.pack(fill="x", pady=10, padx=10)
        ttk.Button(button_frame, text="OK", command=win.destroy).pack(side="right")
        ttk.Button(button_frame, text="Cancel", command=lambda: selected.set(default if default else options[0])).pack(side="right", padx=(0, 5))

        win.grab_set()
        win.wait_window()

        return selected.get()

    def on_count_files(self):
        folder = select_folder("Select folder to count files")
        if not folder:
            return
        include = ask_yes_no("Include subfolders?", "Include subfolders in count?")
        task_name = f"Counting files in {folder.split(chr(92))[-1]} (subfolders={include})"
        import count_files_by_extension as cfbe
        start_tool_task(self, cfbe.count_files_by_extension, task_name, folder=folder, include_subfolders=include)

    def on_list_files(self):
        folder = select_folder("Select folder to list files")
        if not folder:
            return
        exts = ask_string("Extensions", "Enter extensions (comma separated, e.g. jpg,png):", initial="jpg")
        if exts is None:
            return
        exts = [e.strip() for e in exts.split(",") if e.strip()]
        include = ask_yes_no("Include subfolders?", "Include subfolders?")
        save = ask_yes_no("Save to txt?", "Save results to a .txt file?")
        txt_file = None
        if save:
            txt_file = ask_string("Output filename", "Enter output filename (e.g. files.txt):", initial="files.txt")
            if not txt_file:
                return
        task_name = f"Listing {exts} files in {folder.split(chr(92))[-1]}"
        import list_files_by_extension as lf
        start_tool_task(
            self,
            lf.list_files_by_extension_gui,
            task_name,
            folder=folder,
            extensions=exts,
            include_subfolders=include,
            save_txt=save,
            txt_file=txt_file,
        )

    def on_search_files(self):
        folder = select_folder("Select folder to search")
        if not folder:
            return

        use_txt = ask_yes_no("Search input", "Load search terms from a .txt file?")

        terms = None
        txt_file = None

        if use_txt:
            txt_file = select_file("Select .txt file with search terms", filetypes=[("Text files", "*.txt")])
            terms = txt_file
            if not txt_file:
                return
        else:
            raw = ask_string("Search terms", "Enter search terms (comma or space separated):")
            if not raw:
                return
            terms = [t.strip().lower() for part in raw.split(",") for t in part.split() if t.strip()]

        include = ask_yes_no("Include subfolders?", "Include subfolders?")
        do_copy = ask_yes_no("Copy results", "Copy matched files to a new folder?")
        parent_dest = "."
        if do_copy:
            parent_dest = select_folder("Select parent folder for copied files") or "."

        task_name = f"Searching for {terms} in {folder.split(chr(92))[-1]}"
        import search_files as sf
        start_tool_task(
            self,
            sf.search_files_gui,
            task_name,
            folder=folder,
            search_terms=terms,
            txt_file=txt_file,
            include_subfolders=include,
            copy=do_copy,
            parent_dest=parent_dest,
        )

    def on_image_reformat(self):
        folder = filedialog.askdirectory(title="Select folder with images")
        if not folder:
            return
        target = simpledialog.askstring("Target extension", "Enter desired extension (e.g. jpg):", initialvalue="jpg")

        if not target:
            return
        if not target.startswith('.'):
            target = '.' + target

        compress = messagebox.askyesno("Compress", "Attempt to compress images to a target size?")
        kb_limit = 100

        #Allow the user to specify a target file size for compression, with support for both KB and MB inputs.
        if compress:
            kb_limit_input = simpledialog.askstring("Size limit", "Enter maximum file size (e.g., 100KB or 1MB):", initialvalue="100KB")
            if kb_limit_input:
                parse_result = parse_size_to_kb(kb_limit_input, default_kb=100)
                if parse_result is not None:
                    kb_limit = parse_result

        resize = None
        resize_mode = "pad"
        if messagebox.askyesno("Resize", "Resize images to specific dimensions?"):
            dims = simpledialog.askstring("Dimensions", "Enter WIDTHxHEIGHT (e.g. 1200x1200):", initialvalue="1200x1200")
            resize = parse_dimensions(dims)
            if resize:
                resize_mode = self.choose_option(
                    "Resize mode",
                    "Choose how images should be resized:",
                    ["pad", "crop"],
                    default="pad"
                )
                if resize_mode not in ("pad", "crop"):
                    messagebox.showwarning("Invalid mode", "Using default resize mode: pad.")
                    resize_mode = "pad"
        
        ppi = None
        if messagebox.askyesno("Set PPI", "Set custom PPI (print resolution)?"):
            try:
                ppi = int(simpledialog.askstring("PPI", "Enter PPI (e.g. 72):", initialvalue="72"))
            except Exception:
                ppi = None

        dpi = None
        if messagebox.askyesno("Set DPI", "Set custom DPI (screen resolution)?"):
            try:
                dpi = int(simpledialog.askstring("DPI", "Enter DPI (e.g. 72):", initialvalue="72"))
            except Exception:
                dpi = None

        include = messagebox.askyesno("Include subfolders?", "Include subfolders in reformatting?")
        task_name = f"Converting images to {target} in {folder.split(chr(92))[-1]}"
        self.log(f"[STARTING] {task_name}")
        import image_reformatting as ir
        self.run_in_thread(
            ir.batch_convert_in_folder,
            task_name=task_name,
            input_folder=folder,
            target_ext=target,
            compress=compress,
            max_size_kb=kb_limit,
            resize=resize,
            resize_mode=resize_mode,
            ppi=ppi,
            dpi=dpi,
            include=include,
            logger=self.log
        )

    def on_rename_excel(self):
        excel = filedialog.askopenfilename(title="Select Excel file", filetypes=[("Excel files","*.xlsx;*.xls")])
        if not excel:
            return

        # Load Excel and show available columns with indices
        try:
            columns = load_excel_columns(excel)
        except Exception as e:
            messagebox.showerror("Error reading Excel file", f"Could not read Excel file: {e}")
            return

        #Prompt the user then call the choose_column method.
        image_col = self.choose_column("Select Image Column", columns)
        
        if not image_col:
            return
        if image_col.isdigit():
            image_col = int(image_col)

        #Ditto for the SKU column.
        sku_col = self.choose_column("Select SKU Column", columns)

        if not sku_col:
            return
        if sku_col.isdigit():
            sku_col = int(sku_col)

        folder = filedialog.askdirectory(title="Select folder with files to rename")
        if not folder:
            return
        
        include = messagebox.askyesno("Include subfolders?", "Include subfolders in renaming?")
        preserve = messagebox.askyesno("Preserve variants", "Preserve variant suffixes in filenames?")
        ignore_ext = messagebox.askyesno("File extension matching", "Ignore file extensions when matching names?\n\nYes: Match 'image' to 'image.jpg'\nNo: Include extension in the name (current behavior)")
        task_name = f"Renaming files using {excel.split(chr(92))[-1]}"
        self.log(f"[STARTING] {task_name}")
        import rename_wt_excel as rn
        self.run_in_thread(
            rn.rename_from_excel_gui,
            task_name=task_name,
            excel_file=excel,
            image_col=image_col,
            sku_col=sku_col,
            preserve_variants=preserve,
            ignore_file_extension=ignore_ext,
            folder_path=folder,
            include=include,
            output_folder='renamed_by_sku',
            logger=self.log
        )
        
    def on_compare_txt_excel(self):
        txt = filedialog.askopenfilename(title="Select TXT file", filetypes=[("Text files","*.txt")])
        if not txt:
            return
        excel = filedialog.askopenfilename(title="Select Excel file", filetypes=[("Excel files","*.xlsx;*.xls")])
        if not excel:
            return
        col = simpledialog.askstring("Column", "Enter Excel column name to compare against:")
        if not col:
            return
        save = messagebox.askyesno("Save results", "Save results to matches.txt / not_found.txt?")
        task_name = f"Comparing {txt.split(chr(92))[-1]} with {excel.split(chr(92))[-1]}"
        self.log(f"[STARTING] {task_name}")
        import compare_txt_to_excel as cmp
        self.run_in_thread(
            cmp.run_txt_excel_compare_gui,
            task_name=task_name,
            txt_file=txt,
            excel_file=excel,
            column=col,
            save=save,
            logger=self.log
        )

    def on_download_from_excel(self):
        excel = filedialog.askopenfilename(title="Select Excel file", filetypes=[("Excel files","*.xlsx;*.xls")])
        if not excel:
            return
        
        # Load the Excel file to show available columns
        try:
            import pandas as pd
            df = pd.read_excel(excel)
            columns = df.columns.tolist()
        except Exception as e:
            messagebox.showerror("Error reading Excel file", f"Could not read Excel file: {e}")
            return
        
        # Use the new choose_columns popup for image columns
        parsed = self.choose_columns("Select Image Columns", columns)
        if not parsed:
            return
        
        # Ask about renaming
        rename_choice = messagebox.askyesno("Rename", "Rename images using a column?")
        rename_col = None
        if rename_choice:
            rename_col = self.choose_column("Select Rename Column", columns)
            if not rename_col:
                rename_choice = False
        
        # Select output directory
        out_folder = filedialog.askdirectory(title="Select folder to download images to")
        if not out_folder:
            return
        
        try:
            task_name = f"Downloading images from {excel.split(chr(92))[-1]} to {out_folder.split(chr(92))[-1]}"
            self.log(f"[STARTING] {task_name}")
            import web_downloading as wd
            self.run_in_thread(
                wd.download_from_excel,
                task_name=task_name,
                file_name=excel,
                image_columns=parsed,
                rename_column=rename_col,
                output_folder=out_folder,
                max_workers=20,
                logger=self.log,
                use_tqdm=False
            )
        except Exception as e:
            self.log(f"Error starting download: {e}")

    def on_folder_compare(self):
        f1 = filedialog.askdirectory(title="Select first folder")
        if not f1:
            return
        f2 = filedialog.askdirectory(title="Select second folder")
        if not f2:
            return
        ignore = messagebox.askyesno("Ignore extensions?", "Compare ignoring file extensions?")
        save = messagebox.askyesno("Save results", "Save results to a file?")
        out_file = None
        if save:
            out_file = simpledialog.askstring("Output filename", "Enter output filename (e.g. missing_files.txt):", initialvalue="missing_files.txt")
        task_name = f"Comparing {f1.split(chr(92))[-1]} vs {f2.split(chr(92))[-1]}"
        self.log(f"[STARTING] {task_name}")
        import folder_compare as fc
        self.run_in_thread(
            fc.run_folder_compare_gui,
            task_name=task_name,
            folder1=f1,
            folder2=f2,
            ignore_extensions=ignore,
            save=save,
            output_file=out_file,
            logger=self.log
        )


def main():
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
