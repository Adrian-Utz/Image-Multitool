import os
from collections import Counter, defaultdict




def list_files_by_extension(folder=".", extensions=("jpg"), include_subfolders=False):
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
        print("[No files found]")
        return

    #Ask user if they want txt output
    save_txt = input("Output filenames to a .txt file? (y/n): ").strip().lower()
    txt_file = None
    txt_lines = []
    
    #If the user chose to save the results to a txt file, ask for the filename and make sure it ends with .txt
    if save_txt == "y":
        txt_file = input("Enter output filename (e.g. files.txt): ").strip()
        if not txt_file.lower().endswith(".txt"):
            txt_file += ".txt"

    #Create a dictionary to group files by extension
    grouped = defaultdict(list)

    #Loop through all files found
    for path in found_files:
        ext = os.path.splitext(path)[1].lower() or "[no extension]"
        grouped[ext].append(path)

    #Loop throught each file extension in alphabetical order
    for ext in sorted(grouped):
        #Create a header for each group
        header = f"--- {ext} ({len(grouped[ext])} file(s)) ---"
        print(header)

        #If txt output is enabled, add the header to the list of lines to write to the file
        if txt_file:
            txt_lines.append(header)

        #Sort the files in the group by their base name not the full path
        for path in sorted(grouped[ext], key=lambda x: os.path.basename(x)):
            #Extract the base name withoutht the extension
            name = os.path.splitext(os.path.basename(path))[0]
            print(name)
            #Add filename to the txt output if enabled
            if txt_file:
                txt_lines.append(name)

        #Blank line between extension groups for readability
        print()

        #Blank line to the txt ouput as well
        if txt_file:
            txt_lines.append("")

    #Write txt file if requested
    if txt_file:
        try:
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write("\n".join(txt_lines))
            print(f"File list saved to: {os.path.abspath(txt_file)}")
        except Exception as e:
            print(f"Error writing txt file: {e}")