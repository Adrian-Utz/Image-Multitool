import os
import re
import shutil
import datetime
import concurrent.futures

#This module provides a file search and copy tool that can be used both in a command-line interface and integrated into a GUI application. 
#It allows users to search for files based on specified terms, optionally including subfolders, and copy the matched files to a new folder with a timestamped name.
#Added cancellation support

#Written by: AJ Utz on 4/8/2026
#Last updated: 6/11/2026

#Change Log:
#Changed the gui version to allow a .txt file to be used for search terms, and added support for that in the search_files_gui function.
#Optimized the search_files_gui function to support searching multiple root folders in parallel using a thread pool, 
#which can speed up searches across multiple directories.

def filename_matches_search_term(filename, term):
    """Return True when the filename contains the search term as a whole segment.

    Supports separators '-' and '_' around the term. Example matches:
      abc123, abc123.pdf, abc123_alt.pdf, john-abc123.jpg
    Non-matches:
      xabc123.jpg, abc123x.jpg
    """
    filename = filename.lower()
    term = term.lower()
    name, _ = os.path.splitext(filename)

    if name == term:
        return True

    pattern = rf"(?:^|[-_]){re.escape(term)}(?:$|(?=[-_\.]))"
    return bool(re.search(pattern, name))

def search_files():

    print("\n===== File Search Tool =====")

    dest = None

    #Ask once if the user wants to use a .txt file for search terms
    #Make sure to add .txt file to your folder
    print("Would you like to supply a .txt file for your seach?")
    txt_file = input("Type .txt file name here (leave blank to enter manually each search): ").strip()

    search_terms = []

    if txt_file:
        txt_file = txt_file.strip()
        try:
            with open(txt_file, "r", encoding="utf-8-sig") as f:
                #Read all lines and strip whitespace, then put it into a list
                search_terms = [line.strip().lower() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading file {txt_file}: {e}")
            return  #Exit function if the file cannot be read

    #Main search loop
    while True:
        folder = input("\nFolder to search (leave blank for current): ").strip() or "."
        include = input("Include subfolders? (y/n): ").strip().lower()
        include_subfolder = include == "y"

        #If no .txt file provided, ask manually each loop
        if not search_terms:
            #If you want to search for multiple terms, add a comma or space
                raw_terms = input("Enter filename search terms (comma or space separated): ").strip().lower()

                if not raw_terms:
                    print("At least one search term is required.")
                    continue

                #Split the commas first, then spaces
                current_terms = [
                    term.strip()
                    for part in raw_terms.split(",")
                    for term in part.split()
                    if term.strip()
                ]
        else:
                current_terms = search_terms

        matches = []

        #Search for files
        if include_subfolder:
            #Walk through the folder and all its subfolders
            #os.walk yields: current folder path, subfolder names, and filenames
            for root, _, files in os.walk(folder):
                #Loop through each file in he current folder
                for filename in files:
                    #Check the filename against each search term
                    for term in current_terms:
                        #Convert filename to lowercase so the search is case-insensitive
                        if term in filename.lower():
                            #If a term matches, store the full file path
                            matches.append(os.path.join(root, filename))
                            break
        else:
            #Only search files in the given folder
            for filename in os.listdir(folder):
                #Check the filename against each search term
                for term in current_terms:
                    #Case-insensitive comparison
                    if filename_matches_search_term(filename, term):
                        #Store file path
                        matches.append(os.path.join(folder, filename))
                        break


        #Report results
        print(f"\nFound {len(matches)} matching files:\n")
        if not matches:
            print("[No matches found]")
        else:
            for m in matches:
                print(m)

        #Copy option
        copy_choice = input("\nCopy these files to the session folder? (y/n): ").strip().lower()
        if copy_choice == "y" and matches:

            if dest is None:
                parent_dest = input("Parent folder for the copied files (leave blank for current folder): ").strip() or "."

                #Create a timestamp so the folder is alyways named something new
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = os.path.join(parent_dest, f"copied_files_{timestamp}")
                os.makedirs(dest, exist_ok=True)

                print(f"\nCopied files will go to: {dest}")

            for file_path in matches:
                try:
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(dest, filename)

                    #If file already exists, add a suffix
                    counter = 1
                    while os.path.exists(dest_path):
                        name, ext = os.path.splitext(filename)
                        dest_path = os.path.join(dest, f"{name}_{counter}{ext}")
                        counter += 1

                    shutil.copy(file_path, dest_path)
                except Exception as e:
                    print(f"Error copying {file_path}: {e}")

            print(f"\nCopied {len(matches)} files to: {dest}")

        #Exit prompt
        exit_choice = input("\nDo you want to exit to the main menu? (y/n): ").strip().lower()
        if exit_choice == "y":
            break

def search_files_gui(folder='.', search_terms=None, txt_file=None, include_subfolders=False, copy=False, parent_dest='.', logger=print, progress_callback=None, cancel_event=None):
    """Perform a single search pass suitable for GUI integration.

    - folder: directory to search
    - search_terms: list of terms (strings) to search for in filenames
    - include_subfolders: whether to walk subfolders
    - copy: whether to copy matched files into a timestamped folder under parent_dest
    - parent_dest: parent folder for copied files
    - progress_callback: function to call with progress percentage
    - cancel_event: threading event to signal cancellation
    
    Optimizations:
    - Pre-compiles all regex patterns once before searching
    - Batches search terms in groups of 100 for memory efficiency
    - Short-circuits on first match per file
    """
    if txt_file:
        txt_file = txt_file.strip()
        try:
            with open(txt_file, "r", encoding="utf-8-sig") as f:
                search_terms = [line.strip().lower() for line in f if line.strip()]
        except Exception as e:
            logger(f"Error reading file {txt_file}: {e}")
            return

    if search_terms:
        search_terms = [term.lower() for term in search_terms]

    if not search_terms:
        logger("No search terms provided.")
        return

    # Pre-compile all regex patterns once
    compiled_patterns = []
    for term in search_terms:
        pattern = rf"(?:^|[-_]){re.escape(term)}(?:$|(?=[-_\.]))"
        compiled_patterns.append(re.compile(pattern))

    logger(f"[INFO] Pre-compiled {len(compiled_patterns)} search patterns in {(len(compiled_patterns) + 99) // 100} batches of 100")

    matches = []

    def _matches_any_pattern(filename, pattern_batch):
        """Check if filename matches any pattern in the batch."""
        filename_lower = filename.lower()
        name, _ = os.path.splitext(filename_lower)
        for pattern in pattern_batch:
            if pattern.search(name):
                return True
        return False

    def _search_root(root, pattern_batches):
        local_matches = []
        # non-recursive: use scandir for better performance
        if not include_subfolders:
            try:
                # count files for an accurate progress % (cheap for single dir)
                try:
                    total = sum(1 for e in os.scandir(root) if e.is_file())
                except Exception:
                    total = 0

                processed_local = 0
                with os.scandir(root) as it:
                    for entry in it:
                        if cancel_event and cancel_event.is_set():
                            return local_matches
                        if not entry.is_file():
                            continue
                        
                        # Check against each batch of patterns
                        matched = False
                        for batch in pattern_batches:
                            if _matches_any_pattern(entry.name, batch):
                                local_matches.append(os.path.join(root, entry.name))
                                matched = True
                                break  # File matched, no need to check other batches
                        
                        processed_local += 1
                        if progress_callback and total > 0:
                            progress_callback(int((processed_local / total) * 100))
            except FileNotFoundError:
                return local_matches
            except PermissionError:
                return local_matches
            return local_matches

        # recursive search
        for r, _, files in os.walk(root):
            if cancel_event and cancel_event.is_set():
                return local_matches
            for filename in files:
                if cancel_event and cancel_event.is_set():
                    return local_matches
                
                # Check against each batch of patterns
                for batch in pattern_batches:
                    if _matches_any_pattern(filename, batch):
                        local_matches.append(os.path.join(r, filename))
                        break  # File matched, no need to check other batches
        return local_matches

    # Batch search patterns into groups of 100
    batch_size = 100
    pattern_batches = [
        compiled_patterns[i:i + batch_size]
        for i in range(0, len(compiled_patterns), batch_size)
    ]

    # Support searching multiple root folders in parallel by accepting a list/tuple
    roots = folder if isinstance(folder, (list, tuple)) else [folder]

    # Use a thread pool to parallelize across roots (IO-bound tasks)
    max_workers = min(8, len(roots)) or 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_search_root, root, pattern_batches): root for root in roots}
        for fut in concurrent.futures.as_completed(futures):
            try:
                if cancel_event and cancel_event.is_set():
                    logger("[INFO] Search cancelled.")
                    return
                result = fut.result()
                matches.extend(result)
            except Exception as e:
                logger(f"Error searching {futures.get(fut)}: {e}")

    logger(f"\nFound {len(matches)} matching files:\n")

    if not matches:
        logger("[No matches found]")
        return

    for m in matches:
        logger(m)

    if copy and matches:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(parent_dest, f"copied_files_{timestamp}")
        os.makedirs(dest, exist_ok=True)

        logger(f"\nCopied files will go to: {dest}")

        for idx, file_path in enumerate(matches):
            if cancel_event and cancel_event.is_set():
                logger("[INFO] Search cancelled.")
                return
            try:
                filename = os.path.basename(file_path)
                dest_path = os.path.join(dest, filename)

                counter = 1
                while os.path.exists(dest_path):
                    name, ext = os.path.splitext(filename)
                    dest_path = os.path.join(dest, f"{name}_{counter}{ext}")
                    counter += 1

                shutil.copy(file_path, dest_path)
                if progress_callback and len(matches) > 0:
                    progress_callback(int(((idx + 1) / len(matches)) * 100))
            except Exception as e:
                logger(f"Error copying {file_path}: {e}")

        logger(f"\nCopied {len(matches)} files to: {dest}")