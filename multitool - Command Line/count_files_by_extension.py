import os
from collections import Counter


def count_files_by_extension(folder=".", include_subfolders=False):
    file_paths = []

    if include_subfolders:
        #Walk through all subdirectories
        for root, _, files in os.walk(folder):
            for f in files:
                file_paths.append(os.path.join(root, f))
    else:
        #Only the top-level directory
        file_paths = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
        ]

    #Extract file extensions
    extensions = [os.path.splitext(f)[1] for f in file_paths]
    counts = Counter(extensions)

    print("\nFiles in Folder:")
    for ext, count in sorted(counts.items()):
        #Handles files without exensions
        label = ext if ext else "[no extension]"
        print(f"{label} - {count}")