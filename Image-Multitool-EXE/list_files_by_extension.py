import os
from collections import Counter, defaultdict
from tqdm import tqdm

#Added cancellation support.
#Last Update: 9/15/2026
#Written on: 4/16/2026
#Written by: AJ Utz


def _normalize_txt_export_path(txt_file, default_name="file_list.txt"):
    """Resolve a user-supplied export path to a writable .txt file path.

    Handles the user pointing at an existing folder (appends a default
    filename) and paths missing the .txt extension.
    """
    txt_file = os.path.expanduser(str(txt_file).strip().strip('"'))

    if os.path.isdir(txt_file):
        txt_file = os.path.join(txt_file, default_name)
    elif not os.path.splitext(txt_file)[1]:
        txt_file = txt_file + ".txt"

    parent_dir = os.path.dirname(txt_file)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    return txt_file


def list_files_by_extension(folder=".", extensions=("jpg"), include_subfolders=False, logger=print, use_tqdm=False, save_txt=False, txt_file=None):
    folder = os.path.abspath(folder)
    found_files = []

    #Normilization of extensions: remove spaces, convert to lowercase, and ensure they start with a dot
    extensions = tuple(ext.lower().lstrip(".") for ext in extensions)

    if include_subfolders:
        #Walk through all subdirectories and find files, filling the bar as each file is scanned
        with tqdm(desc="Scanning files", unit="file", disable=not use_tqdm, ascii=True, dynamic_ncols=False) as pbar:
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(extensions):
                        found_files.append(os.path.join(root, f))
                    pbar.update(1)
    else:
        #Only list files in the top-level directory
        all_files = os.listdir(folder)
        for f in tqdm(all_files, desc="Scanning files", disable=not use_tqdm, ascii=True, dynamic_ncols=False):
            if f.lower().endswith(extensions):
                found_files.append(os.path.join(folder, f))

    if not found_files:
        logger("[No files found]")
        return

    #Create a dictionary to group files by extension
    grouped = defaultdict(list)
    txt_lines = []

    #Loop through all files found
    for path in found_files:
        ext = os.path.splitext(path)[1].lower() or "[no extension]"
        grouped[ext].append(path)

    #Loop through each file extension in alphabetical order, after the scan bar has already completed
    for ext in sorted(grouped):
        #Create a header for each group
        header = f"--- {ext} ({len(grouped[ext])} file(s)) ---"
        logger(header)
        if save_txt and txt_file:
            txt_lines.append(header)

        #Sort the files in the group by their base name not the full path
        for path in sorted(grouped[ext], key=lambda x: os.path.basename(x)):
            #Extract the base name without the extension
            name = os.path.splitext(os.path.basename(path))[0]
            logger(name)
            if save_txt and txt_file:
                txt_lines.append(name)

        if save_txt and txt_file:
            txt_lines.append("")

    if save_txt and txt_file:
        try:
            txt_file = _normalize_txt_export_path(txt_file)
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write("\n".join(txt_lines))
            logger(f"\nFile list saved to: {os.path.abspath(txt_file)}")
        except Exception as e:
            logger(f"Error writing txt file: {e}")


def list_files_by_extension_gui(folder=".", extensions=("jpg",), include_subfolders=False, save_txt=False, txt_file=None, logger=print, progress_callback=None, cancel_event=None):
    """Non-interactive wrapper suitable for GUI use.

    Parameters:
    - folder: path to search
    - extensions: iterable of extensions (without dot or with)
    - include_subfolders: include subdirectories
    - save_txt: if True, write output names to txt_file
    - txt_file: filename to write (if save_txt True)
    """
    folder = os.path.abspath(folder)
    extensions = tuple(ext.lower().lstrip(".") for ext in extensions)
    found_files = []

    if include_subfolders:
        # Pre-count so the bar can fill up during the scan, before any names are printed
        total_scanned = sum(len(files) for _, _, files in os.walk(folder))
        scanned = 0
        for root, _, files in os.walk(folder):
            if cancel_event and cancel_event.is_set():
                logger("[INFO] List files cancelled.")
                return
            for f in files:
                if cancel_event and cancel_event.is_set():
                    logger("[INFO] List files cancelled.")
                    return
                if f.lower().endswith(extensions):
                    found_files.append(os.path.join(root, f))
                scanned += 1
                if progress_callback and total_scanned > 0:
                    progress_callback(int((scanned / total_scanned) * 100))
    else:
        all_files = os.listdir(folder)
        total_scanned = len(all_files)

        for scanned, f in enumerate(all_files, start=1):
            if cancel_event and cancel_event.is_set():
                logger("[INFO] List files cancelled.")
                return
            if f.lower().endswith(extensions):
                found_files.append(os.path.join(folder, f))
            if progress_callback and total_scanned > 0:
                progress_callback(int((scanned / total_scanned) * 100))

    if not found_files:
        logger("[No files found]")
        return

    if progress_callback:
        progress_callback(100)

    grouped = defaultdict(list)
    txt_lines = []

    for path in found_files:
        ext = os.path.splitext(path)[1].lower() or "[no extension]"
        grouped[ext].append(path)

    for ext in sorted(grouped):
        header = f"--- {ext} ({len(grouped[ext])} file(s)) ---"
        logger(header)
        if save_txt and txt_file:
            txt_lines.append(header)

        for path in sorted(grouped[ext], key=lambda x: os.path.basename(x)):
            if cancel_event and cancel_event.is_set():
                logger("[INFO] List files cancelled.")
                return
            name = os.path.splitext(os.path.basename(path))[0]
            logger(name)
            if save_txt and txt_file:
                txt_lines.append(name)

        logger("")
        if save_txt and txt_file:
            txt_lines.append("")

    if save_txt and txt_file:
        try:
            txt_file = _normalize_txt_export_path(txt_file)
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write("\n".join(txt_lines))
            logger(f"File list saved to: {os.path.abspath(txt_file)}")
        except Exception as e:
            logger(f"Error writing txt file: {e}")