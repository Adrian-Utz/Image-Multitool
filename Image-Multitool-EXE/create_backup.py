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

    # Walk through subdirectories only if include_subfolders is true.
    if include_subfolders:
        for root, _, files in os.walk(path):
            for file_name in files:
                yield os.path.join(root, file_name)
    # If false, use scandir to enumerate top-level files without sorting.
    else:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file():
                    yield entry.path


def _build_unique_path(target_path, used_paths=None):
    """Generate a unique destination path by appending a suffix when duplicates occur."""

    if used_paths is None:
        return target_path

    candidate = target_path
    counter = 1
    while candidate in used_paths:
        base_name, extension = os.path.splitext(target_path)
        candidate = f"{base_name}_{counter}{extension}"
        counter += 1
    used_paths.add(candidate)
    return candidate


def _copy_file_with_buffer(src, dest, logger=None, log_each_file=False, preserve_metadata=True, created_dirs=None, created_dirs_lock=None):
    """Copy a file using a larger buffer for better throughput on large files."""

    parent_dir = os.path.dirname(dest)
    if created_dirs is None:
        os.makedirs(parent_dir, exist_ok=True)
    else:
        with created_dirs_lock:
            if parent_dir not in created_dirs:
                os.makedirs(parent_dir, exist_ok=True)
                created_dirs.add(parent_dir)

    with open(src, "rb") as src_file, open(dest, "wb") as dst_file:
        shutil.copyfileobj(src_file, dst_file, length=4 * 1024 * 1024)

    if preserve_metadata:
        shutil.copystat(src, dest)
    if log_each_file and logger:
        logger(f"[COPY] {src} -> {dest}")


def _count_source_files(existing_sources, include_subfolders):
    """Count file entries for progress reporting without building a copy list."""

    total_files = 0
    for source in existing_sources:
        if os.path.isfile(source):
            total_files += 1
        elif os.path.isdir(source):
            if include_subfolders:
                for _, _, files in os.walk(source):
                    total_files += len(files)
            else:
                with os.scandir(source) as entries:
                    for entry in entries:
                        if entry.is_file():
                            total_files += 1
    return total_files


def _iter_copy_tasks(existing_sources, backup_root, include_subfolders, used_paths, check_disk_space=True, free_bytes=None, logger=None):
    """Yield copy tasks while scanning sources so copying can begin immediately."""

    scanned_bytes = 0
    for source in existing_sources:
        if os.path.isfile(source):
            if check_disk_space:
                try:
                    file_size = os.path.getsize(source)
                except OSError:
                    logger(f"[WARN] Skipping unreadable file: {source}")
                    continue

                scanned_bytes += file_size
                if free_bytes is not None and scanned_bytes > free_bytes:
                    raise OSError(
                        f"Not enough free space in destination. Need at least ~{scanned_bytes / (1024 * 1024):.1f} MB."
                    )

            dest_path = os.path.join(backup_root, os.path.basename(source))
            dest_path = _build_unique_path(dest_path, used_paths)
            yield source, dest_path

        elif os.path.isdir(source):
            for source_file in _iter_source_files(source, include_subfolders):
                if check_disk_space:
                    try:
                        file_size = os.path.getsize(source_file)
                    except OSError:
                        logger(f"[WARN] Skipping unreadable file: {source_file}")
                        continue

                    scanned_bytes += file_size
                    if free_bytes is not None and scanned_bytes > free_bytes:
                        raise OSError(
                            f"Not enough free space in destination. Need at least ~{scanned_bytes / (1024 * 1024):.1f} MB."
                        )

                relative_path = os.path.relpath(source_file, source)
                dest_path = os.path.join(backup_root, relative_path)
                dest_path = _build_unique_path(dest_path, used_paths)
                yield source_file, dest_path
        else:
            logger(f"[WARN] Unsupported path: {source}")


def create_backup(
    sources,
    destination_root,
    include_subfolders=False,
    logger=print,
    progress_callback=None,
    cancel_event=None,
    max_workers=None,
    preserve_metadata=True,
    check_disk_space=True,
    log_each_file=False,
    fast_mode=False,
):
    """Create a timestamped backup folder and copy the selected files into it.

    fast_mode=True disables disk-space checking and metadata preservation for
    the highest possible throughput on very large file sets.
    """

    source_list = _normalize_sources(sources)
    if not source_list:
        raise ValueError("No files or folders selected for backup.")

    destination_root = os.path.abspath(destination_root)
    os.makedirs(destination_root, exist_ok=True)

    backup_root = os.path.join(
        destination_root,
        f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )
    os.makedirs(backup_root, exist_ok=True)

    logger(f"[INFO] Backup destination: {backup_root}")

    existing_sources = [source for source in source_list if os.path.exists(source)]
    missing_sources = [source for source in source_list if not os.path.exists(source)]
    if missing_sources:
        for missing in missing_sources:
            logger(f"[WARN] Skipping missing path: {missing}")

    if not existing_sources:
        raise FileNotFoundError("None of the selected paths exist.")

    if fast_mode:
        check_disk_space = False
        preserve_metadata = False
        log_each_file = False

    free_bytes = shutil.disk_usage(destination_root).free if check_disk_space else None
    used_paths = set()

    total_files = _count_source_files(existing_sources, include_subfolders) if progress_callback else None
    next_progress = 1
    copied_count = 0
    counter_lock = threading.Lock()
    created_dirs = set()
    created_dirs_lock = threading.Lock()

    def _run_copy(item):
        nonlocal copied_count, next_progress
        source_file, dest_path = item
        if cancel_event and cancel_event.is_set():
            return None
        _copy_file_with_buffer(
            source_file,
            dest_path,
            logger=logger,
            log_each_file=log_each_file,
            preserve_metadata=preserve_metadata,
            created_dirs=created_dirs,
            created_dirs_lock=created_dirs_lock,
        )
        with counter_lock:
            copied_count += 1
            if progress_callback and total_files:
                percent = int((copied_count / total_files) * 100)
                if percent >= next_progress or copied_count % 100 == 0:
                    progress_callback(percent)
                    next_progress = percent + 1
        return dest_path

    if max_workers is None:
        max_workers = min(16, max(4, (os.cpu_count() or 2) * 2))

    copy_tasks = _iter_copy_tasks(
        existing_sources,
        backup_root,
        include_subfolders,
        used_paths,
        check_disk_space=check_disk_space,
        free_bytes=free_bytes,
        logger=logger,
    )

    try:
        if max_workers <= 1:
            for item in copy_tasks:
                if cancel_event and cancel_event.is_set():
                    logger("[INFO] Backup cancelled.")
                    return None
                _run_copy(item)
        else:
            chunksize = 16 if max_workers > 8 else 1
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for _ in executor.map(_run_copy, copy_tasks, chunksize=chunksize):
                    if cancel_event and cancel_event.is_set():
                        logger("[INFO] Backup cancelled.")
                        return None
    except OSError as error:
        logger(f"[WARN] {error}")
        return None

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


def select_backup_options(parent=None):
    """Show backup option checkboxes for GUI-based backups."""
    if filedialog is None or messagebox is None:
        raise RuntimeError("tkinter is unavailable")

    root = parent if parent is not None else tk._default_root
    dialog = tk.Toplevel(root) if root is not None else tk.Tk()
    dialog.title("Backup options")
    dialog.geometry("420x200")
    dialog.transient(root)
    if root is not None:
        dialog.grab_set()

    include_var = tk.BooleanVar(value=False)
    fast_var = tk.BooleanVar(value=False)
    result = {"confirmed": False, "include_subfolders": False, "fast_mode": False}

    tk.Label(dialog, text="Backup options", font=(None, 10, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
    tk.Checkbutton(dialog, text="Include subfolders", variable=include_var).pack(anchor="w", padx=20, pady=2)
    tk.Checkbutton(dialog, text="Enable fast mode", variable=fast_var).pack(anchor="w", padx=20, pady=2)

    warning_text = (
        "Fast mode disables disk-space checking and metadata preservation. "
        "Use only for very large backups on fast network drives."
    )
    tk.Label(dialog, text=warning_text, wraplength=380, justify="left", fg="darkred").pack(anchor="w", padx=20, pady=(10, 5))

    def finish():
        if fast_var.get():
            proceed = messagebox.askyesno(
                "Fast mode warning",
                "Fast mode skips disk space checking and metadata preservation. "
                "This improves speed but may discard file timestamps and fail silently if destination space is insufficient.\n\n"
                "Continue with fast mode?",
                parent=dialog,
            )
            if not proceed:
                return
        result["confirmed"] = True
        result["include_subfolders"] = include_var.get()
        result["fast_mode"] = fast_var.get()
        dialog.destroy()

    def cancel_options():
        dialog.destroy()

    button_frame = tk.Frame(dialog)
    button_frame.pack(fill="x", padx=10, pady=(10, 10))
    tk.Button(button_frame, text="Start Backup", width=12, command=finish).pack(side="right", padx=(0, 5))
    tk.Button(button_frame, text="Cancel", width=12, command=cancel_options).pack(side="right")

    dialog.wait_window()
    if result["confirmed"]:
        return result["include_subfolders"], result["fast_mode"]
    return None


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
    fast_mode = input("Use fast mode? This skips disk checks and metadata (y/n): ").strip().lower() == "y"
    if fast_mode:
        print(
            "WARNING: Fast mode skips disk-space verification and metadata preservation. "
            "Use only for very large backups when speed is essential."
        )

    create_backup(
        selected_sources,
        destination_root,
        include_subfolders=include_subfolders,
        fast_mode=fast_mode,
        logger=print,
    )


def backup_from_dialogs(parent=None):
    """Prompt the user for backup sources and destination, then create the backup."""
    selected_sources = select_backup_sources(parent=parent)
    if not selected_sources:
        return None

    destination_root = filedialog.askdirectory(title="Select backup destination", parent=parent)
    if not destination_root:
        return None

    options = select_backup_options(parent=parent)
    if options is None:
        return None

    include_subfolders, fast_mode = options
    return create_backup(
        selected_sources,
        destination_root,
        include_subfolders=include_subfolders,
        fast_mode=fast_mode,
        logger=print,
    )

