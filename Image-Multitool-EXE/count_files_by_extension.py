import os
from collections import Counter

#Added cancellation support.

def count_files_by_extension(folder=".", include_subfolders=False, logger=print, progress_callback=None, cancel_event=None):
    file_paths = []
    processed = 0

    if include_subfolders:
        # First pass: count total files for progress tracking
        total_files = sum(len(files) for _, _, files in os.walk(folder))
        
        #Walk through all subdirectories
        for root, _, files in os.walk(folder):
            if cancel_event and cancel_event.is_set():
                logger("[INFO] Count files cancelled.")
                return
            for f in files:
                if cancel_event and cancel_event.is_set():
                    logger("[INFO] Count files cancelled.")
                    return
                file_paths.append(os.path.join(root, f))
                processed += 1
                if progress_callback and total_files > 0:
                    progress_callback(int((processed / total_files) * 100))
    else:
        #Only the top-level directory
        all_files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        total_files = len(all_files)
        
        for f in all_files:
            if cancel_event and cancel_event.is_set():
                logger("[INFO] Count files cancelled.")
                return
            file_paths.append(os.path.join(folder, f))
            processed += 1
            if progress_callback and total_files > 0:
                progress_callback(int((processed / total_files) * 100))

    #Extract file extensions
    extensions = [os.path.splitext(f)[1] for f in file_paths]
    counts = Counter(extensions)

    logger("\nFiles in Folder:")
    total_count = 0
    for ext, count in sorted(counts.items()):
        #Handles files without exensions
        label = ext if ext else "[no extension]"
        logger(f"{label} - {count}")
        total_count += count
        
    logger(f"\nTotal files: {total_count}")