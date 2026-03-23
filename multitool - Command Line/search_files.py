import os
import shutil
import datetime



def search_files():

    print("\n===== File Search Tool =====")

    dest = None

    #Ask once if the user wants to use a .txt file for search terms
    #Make sure to add .txt file to your folder
    print("Would you like to supply a .txt file for your seach?")
    txt_file = input("Type .txt file name here (leave blank to enter manually each search): ").strip()

    search_terms = []

    if txt_file:
        try:
            with open(txt_file, "r") as f:
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
                    if term in filename.lower():
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