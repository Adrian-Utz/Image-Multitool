import datetime
import os
import shutil
import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor

"""
Backup utility for the multitool suite.

This module can:
- back up one or more selected files or folders
- optionally include subfolders
- create a timestamped backup folder in the chosen destination
- warn the user if the destination does not have enough free space

Written by AJ Utz on: 8/1/2026
Last Update: 8/3/2026
"""

# This try block checks if tkinter is available for GUI
try:
    from tkinter import filedialog, messagebox
except Exception:  # pragma: no cover - tkinter may be unavailable in headless environments
    filedialog = None
    messagebox = None


def _normalize_sources(sources):
    """
    Normalize the input sources into a list of strings
    sources: can be paths to files or directories
    """
    if isinstance(sources, (str, os.PathLike)):
        #If source is a single sring or path-like object, convert it into a list
        return [str(sources)]
    return [str(source) for source in sources if source]


def _estimate_size(path):
    """
    Estimate size of a given path
    path: string of a path to a file or directory
    total: the total size of the files or directory in bytes. 
    """

    #check if the path is a file
    if os.path.isfile(path):
        return os.path.getsize(path)

    #Check if the path is a directory
    if not os.path.isdir(path):
        return 0

    total = 0
    #Walkthrough the directory and it's subdirectories
    for root, _, files in os.walk(path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                #Try to get the size of each file
                total += os.path.getsize(file_path)
            except OSError:
                #If an error occures skip the file. Check the permissions on the file.
                continue
    return total


def _iter_source_files(path, include_subfolders):
    """Iterate files over a given path"""

    #Check if the file is a path
    if os.path.isfile(path):
        yield path
        return

    #Check if the path is a directory
    if not os.path.isdir(path):
        return

    #Walkthrough subdirectories only if include_subfolders is true.
    if include_subfolders:
        for root, _, files in os.walk(path):
            for file_name in sorted(files):
                yield os.path.join(root, file_name)
    #If false use scandir to get top level files
    else:
        with os.scandir(path) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                if entry.is_file():
                    yield entry.path


def _build_unique_path(target_path, used_paths=None):
    """Generate a unique path by appending a suffix to the target path if it already exists"""


    if used_paths is None:
        #Validation check
        if not os.path.exists(target_path):
            return target_path

        #Base name extraction from path
        base_name, extension = os.path.splitext(target_path)
        counter = 1

        #Loop to find a unique path
        while True:
            #construct the candidate path by appening a suffix
            candidate = f"{base_name}_{counter}{extension}"

            #Check if candidate does not exist and is not in use
            if not os.path.exists(candidate):
                return candidate
            #Increment for next candidate
            counter += 1
        return target_path

    candidate = target_path
    counter = 1
    while candidate in used_paths or os.path.exists(candidate):
        base_name, extension = os.path.splitext(target_path)
        candidate = f"{base_name}_{counter}{extension}"
        counter += 1
    used_paths.add(candidate)
    return candidate


def _copy_file_with_buffer(src, dest, logger=None):
    """Copy a file using a larger buffer for better throughput on large files."""

    #Ensure the destination exists
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    #Open the source and destination file in binary read/write mode
    with open(src, "rb") as src_file, open(dest, "wb") as dst_file:
        #copy files contents using a large buffer
        shutil.copyfileobj(src_file, dst_file, length=1024 * 1024)
    #copy file metadata
    shutil.copystat(src, dest)
    #if run in the GUI send a message to the log
    if logger:
        logger(f"[COPY] {src} -> {dest}")


def create_backup(sources, destination_root, include_subfolders=False, logger=print, progress_callback=None, cancel_event=None, max_workers=None):
    """Create a timestamped backup folder and copy the selected files into it."""

    #Normilize the list of source paths
    source_list = _normalize_sources(sources)
    if not source_list:
        raise ValueError("No files or folders selected for backup.")

    #get absolute path
    destination_root = os.path.abspath(destination_root)
    #create destination dirs if it doesn't exist
    os.makedirs(destination_root, exist_ok=True)

    #determine the backup root with a timestamped folder name
    backup_root = os.path.join(
        destination_root,
        f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )
    os.makedirs(backup_root, exist_ok=True)

    logger(f"[INFO] Backup destination: {backup_root}")

    #Collect existing and missing source paths
    existing_sources = [source for source in source_list if os.path.exists(source)]
    missing_sources = [source for source in source_list if not os.path.exists(source)]
    if missing_sources:
        for missing in missing_sources:
            logger(f"[WARN] Skipping missing path: {missing}")

    if not existing_sources:
        raise FileNotFoundError("None of the selected paths exist.")

    #Calculate availabe free space in the dest
    total_bytes = sum(_estimate_size(source) for source in existing_sources)
    free_bytes = shutil.disk_usage(destination_root).free
    if total_bytes and free_bytes < total_bytes:
        logger(
            f"[WARN] Not enough free space in destination. Need ~{total_bytes / (1024 * 1024):.1f} MB, available ~{free_bytes / (1024 * 1024):.1f} MB."
        )
        return None

    #Plan the copy operations
    copy_plan = []
    used_paths = set()
    for source in existing_sources:
        if os.path.isfile(source):
            dest_path = os.path.join(backup_root, os.path.basename(source))
            dest_path = _build_unique_path(dest_path, used_paths)
            copy_plan.append((source, dest_path))
        elif os.path.isdir(source):
            for source_file in _iter_source_files(source, include_subfolders):
                relative_path = os.path.relpath(source_file, source)
                dest_path = os.path.join(backup_root, relative_path)
                dest_path = _build_unique_path(dest_path, used_paths)
                copy_plan.append((source_file, dest_path))
        else:
            logger(f"[WARN] Unsupported path: {source}")

    # Total number of files to be copied
    total_files = len(copy_plan)
    #Counter
    copied_count = 0
    # Lock to ensure thread safe updating of the counter
    counter_lock = threading.Lock()

    def _run_copy(item):
        nonlocal copied_count
        #Unpack the tuple into vars
        source_file, dest_path = item
        #Check if the user wants to cancel the tool
        if cancel_event and cancel_event.is_set():
            return None
        #copy files, then safely update the copied_count
        _copy_file_with_buffer(source_file, dest_path, logger=logger)
        with counter_lock:
            copied_count += 1
            if progress_callback and total_files > 0:
                progress_callback(int((copied_count / total_files) * 100))
        return dest_path

    if max_workers is None:
        if total_files > 20:
            max_workers = min(4, max(2, os.cpu_count() or 2))
        else:
            max_workers = 1

    if total_files <= 1 or max_workers <= 1:
        for item in copy_plan:
            if cancel_event and cancel_event.is_set():
                logger("[INFO] Backup cancelled.")
                return None
            _run_copy(item)
    else:
        #Process then submit all tasks to the executor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_copy, item) for item in copy_plan]
            #Iterate over each completed furture while checking for cancelation
            for future in futures:
                if cancel_event and cancel_event.is_set():
                    logger("[INFO] Backup cancelled.")
                    return None
                future.result()

    logger(f"[INFO] Backup complete. Copied {copied_count} file(s) to {backup_root}")
    return backup_root


def select_backup_sources(parent=None):
    """Show a popup that lets the user add files and/or folders for backup."""
    if filedialog is None or messagebox is None:
        raise RuntimeError("tkinter is unavailable")

    root = parent if parent is not None else tk._default_root
    dialog = tk.Toplevel(root) if root is not None else tk.Tk()
    dialog.title("Select backup sources")
    dialog.geometry("460x260")
    dialog.transient(root)
    if root is not None:
        dialog.grab_set()

    selected_paths = []

    def refresh_list():
        listbox.delete(0, tk.END)
        for path in selected_paths:
            listbox.insert(tk.END, path)

    def add_files():
        paths = list(filedialog.askopenfilenames(title="Select files to back up", parent=dialog))
        if paths:
            selected_paths.extend(paths)
            refresh_list()

    def add_folder():
        folder = filedialog.askdirectory(title="Select folder to back up", parent=dialog)
        if folder:
            selected_paths.append(folder)
            refresh_list()

    def finish():
        dialog.destroy()

    def cancel():
        selected_paths.clear()
        dialog.destroy()

    tk.Label(dialog, text="Add files and/or folders to back up:", anchor="w").pack(fill="x", padx=10, pady=(10, 5))
    listbox = tk.Listbox(dialog, height=8)
    listbox.pack(fill="both", expand=True, padx=10, pady=5)

    button_frame = tk.Frame(dialog)
    button_frame.pack(fill="x", padx=10, pady=(0, 10))
    tk.Button(button_frame, text="Add files", width=12, command=add_files).pack(side="left", padx=(0, 5))
    tk.Button(button_frame, text="Add folder", width=12, command=add_folder).pack(side="left", padx=(0, 5))
    tk.Button(button_frame, text="Done", width=10, command=finish).pack(side="right")
    tk.Button(button_frame, text="Cancel", width=10, command=cancel).pack(side="right", padx=(0, 5))

    dialog.wait_window()
    return selected_paths


def backup_selected_files():
    """
    Command-line entry point for creating a backup.
    """
    print("\n===== Backup Tool =====")

    selected_sources = []
    while True:
        source_path = input("Enter a file or folder to back up (leave blank to finish): ").strip()
        if not source_path:
            break
        selected_sources.append(source_path)

    if not selected_sources:
        print("No files or folders selected.")
        return

    destination_root = input("Destination folder for the backup (leave blank for current folder): ").strip() or "."
    include_subfolders = input("Include subfolders? (y/n): ").strip().lower() == "y"

    create_backup(selected_sources, destination_root, include_subfolders=include_subfolders, logger=print)


def backup_from_dialogs(parent=None):
    """Prompt the user for backup sources and destination, then create the backup."""
    selected_sources = select_backup_sources(parent=parent)
    if not selected_sources:
        return None

    destination_root = filedialog.askdirectory(title="Select backup destination", parent=parent)
    if not destination_root:
        return None

    include_subfolders = messagebox.askyesno("Include subfolders?", "Include subfolders in the backup?")
    return create_backup(selected_sources, destination_root, include_subfolders=include_subfolders, logger=print)

