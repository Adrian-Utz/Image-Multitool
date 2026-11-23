import concurrent.futures
import threading
from collections import deque

"""Background task queue: thread pool, FIFO queue, cancellation and progress.

This module has no tkinter dependency. A front end (the GUI) subscribes to the
``on_*`` callbacks to redraw itself and supplies ``schedule`` so that deferred
work runs on its own thread.

Written by: AJ Utz
Written on: 11/18/2026
Latest Update: 11/19/2026
"""

def _noop(*_args, **_kwargs):
    """Does nothing"""
    return None


class TaskQueue:
    """
    A class to manage a queue of tasks that are executed one at a time on a worker thread.
    The tasks can be scheduled to run at a specific delay, and they can be cancelled if needed.
    """

    def __init__(self, *, log=_noop, schedule=None, runner=None, auto_start=True, max_workers=4):
        """Initialize the TaskQueue with the specified logging and execution parameters."""
        self.log = log
        # schedule(delay_ms, func, *args) must be safe to call from any thread.
        self.schedule = schedule or (lambda _delay, func, *args: func(*args))
        # runner(func, *args, **kwargs) executes the task body on the worker thread.
        self.runner = runner or (lambda func, *args, **kwargs: func(*args, **kwargs))
        self.auto_start = auto_start

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = deque() # Queue to hold tasks
        self.active_tasks = [] # List of currently active tasks
        self.task_lock = threading.Lock() # Lock to protect the task queue and active tasks
        self.completed_tasks = 0 
        self.total_tasks_started = 0
        self._current_task_future = None
        self._current_cancel_event = None
        self._current_task_name = None

        # Front-end hooks; all optional.
        self.on_change = _noop      # Callback when a queue contents or active tasks changed
        self.on_running = _noop     # Callback whena task just started
        self.on_cancelling = _noop  # Callback when the running task was asked to stop
        self.on_progress = _noop    # Callback for on_progress(percentage, text=None)
        self.on_idle = _noop        # Callback when the queue is on_idle(complete: bool)

    @property
    def is_running(self):
        """Return True if a task is currently running, False otherwise."""
        return self._current_task_future is not None

    def pending_tasks(self):
        """Return a list of tasks that are currently pending in the queue."""
        with self.task_lock:
            return list(self.task_queue)

    def snapshot(self):
        """Return a snapshot of the current state of the queue and active tasks."""
        with self.task_lock:
            return list(self.active_tasks), list(self.task_queue)

    def submit(self, func, task_name="Task", *args, **kwargs):
        """Submit a new task to the queue with the given function, task name, and arguments."""
        self.submit_items([{"func": func, "args": args, "kwargs": dict(kwargs), "task_name": task_name}])

    def submit_items(self, task_items):
        """
        Submit multiple tasks to the queue. Each task is a dictionary with a function,
        arguments, keyword arguments, and a task name.
        """
        with self.task_lock:
            self.task_queue.extend(task_items)
            self.total_tasks_started += len(task_items)
        self.on_change() # Notify the front end that the queue has changed
        if self.auto_start: # if auto start is enabled, process the queue
            self.process()

    def set_auto_start(self, enabled):
        """Set whether the queue should automatically start when tasks are added if it was not already running."""
        self.auto_start = bool(enabled)
        self.on_change() # Notify the front end that the queue has changed
        if self.auto_start and self.task_queue and self._current_task_future is None:
            self.process()

    def start(self):
        """Manually start the queue when auto-start is disabled."""
        if self.auto_start:
            return
        if self._current_task_future is None and self.task_queue:
            self.process()

    def process(self):
        """Process the next task in the queue if no task is currently running."""
        with self.task_lock:
            if self._current_task_future is not None:
                return
            if not self.task_queue:
                task_item = None
            else:
                task_item = self.task_queue.popleft()
                self._launch(task_item)
        if task_item is None:
            self.update_status() # Update queue status
        self.on_change() # Notify the front end that the queue has changed

    def _launch(self, task_item):
        """
        Launch a new task by submitting it to the worker thread. This method initializes
        the task's future and sets up event handlers for progress and cancellation.
        """
        func = task_item["func"]
        task_name = task_item["task_name"]
        args = task_item.get("args", ())
        kwargs = task_item.get("kwargs", {})

        cancel_event = threading.Event()
        kwargs["progress_callback"] = lambda pct: self.report_progress(task_name, pct, cancel_event)
        kwargs["cancel_event"] = cancel_event

        self._current_cancel_event = cancel_event
        self._current_task_name = task_name
        self.active_tasks.append(task_name)

        self.schedule(0, self._notify_running) # Schedule the task to start

        future = self.executor.submit(self.runner, func, *args, **kwargs)
        self._current_task_future = future
        future.add_done_callback(lambda fut: self.schedule(500, self._finish, fut, task_name))

    def _notify_running(self):
        self.on_running() # Front end hook for task start
        self.on_progress(0) # Initial progress fro the task

    def _finish(self, future, task_name):
        """Handle the completion of a task. This method updates the queue state and notifies the front end."""
        try:
            with self.task_lock:
                self.completed_tasks += 1 # Increment the completed task counter
                if task_name in self.active_tasks: # If task was active, remove it
                    self.active_tasks.remove(task_name)
                if self._current_task_future is future: # Clear surrent task if it matches the future
                    self._clear_current()
                if self.total_tasks_started > 0: # Calculate and set the progress
                    self.on_progress(int(self.completed_tasks / self.total_tasks_started * 100))
        except Exception:
            pass # Handle any exceptions that occure during the task completion
        self.update_status() # Update the queue status
        self.schedule(200, self.process) # Schedule the next task to process

    def _clear_current(self):
        """Clear the current task state by resetting the future and event."""
        self._current_task_future = None
        self._current_cancel_event = None
        self._current_task_name = None

    def cancel_current(self):
        """
        Cancel the running task, or its future if it has not started yet. This method
        handles both cancelling the task and the cancellation event.
        """
        if self._current_task_future:
            try:
                if self._current_task_future.cancel(): # Cancel the task if it's not already cancelled
                    self.log("[INFO] Current task cancelled before start.")
                    with self.task_lock:
                        if self._current_task_name in self.active_tasks: # If the task was active, remove it
                            self.active_tasks.remove(self._current_task_name)
                        self.completed_tasks += 1 # Increment the completed tasks count
                        self._clear_current() # Clear the current task state
                    self.update_status() # Update the queue status
                    return
            except Exception:
                pass # Handle any exceptions that occur during cancellation

        if self._current_cancel_event and not self._current_cancel_event.is_set(): # If the event is not set, set it
            self._current_cancel_event.set() # Set the cancellation event
            self.log("[INFO] Cancelling current task...")
            with self.task_lock:
                if self._current_task_name in self.active_tasks: # If the task was active, remove it
                    self.active_tasks.remove(self._current_task_name)
            self.on_cancelling() # Front end hook for task cancellation
            self.update_status() # Update the queue status
            self.on_change() # Notify the front end that the queue has changed

    def remove_pending(self, task_item):
        """
        Remove a task from the pending queue if it exists. Returns False if the task
        has already left the queue.
        """
        with self.task_lock:
            index = next((i for i, queued in enumerate(self.task_queue) if queued is task_item), None)
            if index is None:
                return False
            del self.task_queue[index] # Remove the task from the queue
            self.completed_tasks += 1 # Increment the completed tasks count
        self.log(f"[INFO] Removed pending task: {task_item['task_name']}")
        return True

    def report_progress(self, task_name, percentage, cancel_event):
        """Progress from a running task; ignored unless it belongs to the active task."""
        def _apply():
            with self.task_lock:
                is_active = self._current_cancel_event is cancel_event and task_name in self.active_tasks
            if is_active:
                self.on_progress(percentage) # Update the progress for the task

        self.schedule(0, _apply) # Schedule the progress update

    def update_status(self):
        """
        Update the front end with the current status of the queue. This method checks if the queue
        is idle and calculates the progress if tasks are still running.
        """
        idle = complete = False
        progress = remaining = None
        with self.task_lock:
            if not self.active_tasks and not self.task_queue: # If no tasks are active or pending
                idle = True
                if self.total_tasks_started > 0: # If there were tasks started, set complete to True
                    complete = True
                    self.completed_tasks = 0 # Reset the completed tasks count
                    self.total_tasks_started = 0 # Reset the total tasks started count
            elif self.total_tasks_started > 0: # If tasks are running
                remaining = len(self.active_tasks) + len(self.task_queue) # Calculate the number of remaining tasks
                progress = int(self.completed_tasks / self.total_tasks_started * 100) # Calculate the progress percentage
        if idle: # If the queue is idle, notify the front end
            self.on_idle(complete) # Front end hook for idle state
            if complete: # If all tasks were completed
                self.on_progress(100, "Complete ✓") # Notify the front end that all tasks are completed
        elif progress is not None: # If tasks are still running, update the progress
            self.on_progress(progress, f"{progress}% - {remaining} tasks remaining") # Update the progress for the queue
        self.on_change()

    def shutdown(self):
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            try:
                self.executor.shutdown(wait=False)
            except Exception:
                pass
        except Exception:
            pass
