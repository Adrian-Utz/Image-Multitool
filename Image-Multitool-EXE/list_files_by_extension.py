import os
from collections import Counter, defaultdict

#Added cancellation support.


def list_files_by_extension(folder=".", extensions=("jpg"), include_subfolders=False, logger=print):
    folder = os.path.abspath(folder)
    found_files = []

    #Normilization of extensions: remove spaces, convert to lowercase, and ensure they start with a dot
    extensions = tuple(ext.lower().lstrip(".") for ext in extensions)

    if include_subfolders:
        #Walk through all subdirectories and find files
        for root, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(extensions):
                    found_files.append(os.path.join(root, f))
    else:
        #Only list files in the top-level directory
        found_files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(extensions)
        ]

    if not found_files:
        logger("[No files found]")
        return

    #Create a dictionary to group files by extension
    grouped = defaultdict(list)

    #Loop through all files found
    for path in found_files:
        ext = os.path.splitext(path)[1].lower() or "[no extension]"
        grouped[ext].append(path)

    #Loop through each file extension in alphabetical order
    for ext in sorted(grouped):
        #Create a header for each group
        header = f"--- {ext} ({len(grouped[ext])} file(s)) ---"
        logger(header)

        #Sort the files in the group by their base name not the full path
        for path in sorted(grouped[ext], key=lambda x: os.path.basename(x)):
            #Extract the base name without the extension
            name = os.path.splitext(os.path.basename(path))[0]
            logger(name)


def list_files_by_extension_gui(folder=".", extensions=("jpg",), include_subfolders=False, save_txt=False, txt_file=None):
    """Non-interactive wrapper suitable for GUI use.

    Parameters:
    - folder: path to search
    - extensions: iterable of extensions (without dot or with)
    - include_subfolders: include subdirectories
    - save_txt: if True, write output names to txt_file
    - txt_file: filename to write (if save_txt True)
    """
def list_files_by_extension_gui(folder=".", extensions=("jpg",), include_subfolders=False, save_txt=False, txt_file=None, logger=print, progress_callback=None, cancel_event=None):
    folder = os.path.abspath(folder)
    extensions = tuple(ext.lower().lstrip(".") for ext in extensions)
    found_files = []
    processed = 0

    if include_subfolders:
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
    else:
        all_files = os.listdir(folder)
        
        for f in all_files:
            if cancel_event and cancel_event.is_set():
                logger("[INFO] List files cancelled.")
                return
            if f.lower().endswith(extensions):
                found_files.append(os.path.join(folder, f))

    if not found_files:
        logger("[No files found]")
        return

    grouped = defaultdict(list)
    txt_lines = []

    for path in found_files:
        ext = os.path.splitext(path)[1].lower() or "[no extension]"
        grouped[ext].append(path)

    # Count total items to log (for progress tracking)
    total_log_items = sum(len(grouped[ext]) for ext in grouped) + len(grouped)  # files + headers
    logged_items = 0

    for ext in sorted(grouped):
        header = f"--- {ext} ({len(grouped[ext])} file(s)) ---"
        logger(header)
        if save_txt and txt_file:
            txt_lines.append(header)
        logged_items += 1
        if progress_callback and total_log_items > 0:
            progress_callback(int((logged_items / total_log_items) * 100))

        for path in sorted(grouped[ext], key=lambda x: os.path.basename(x)):
            if cancel_event and cancel_event.is_set():
                logger("[INFO] List files cancelled.")
                return
            name = os.path.splitext(os.path.basename(path))[0]
            logger(name)
            if save_txt and txt_file:
                txt_lines.append(name)
            logged_items += 1
            if progress_callback and total_log_items > 0:
                progress_callback(int((logged_items / total_log_items) * 100))

        logger("")
        if save_txt and txt_file:
            txt_lines.append("")

    if save_txt and txt_file:
        try:
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write("\n".join(txt_lines))
            logger(f"File list saved to: {os.path.abspath(txt_file)}")
        except Exception as e:
            logger(f"Error writing txt file: {e}")