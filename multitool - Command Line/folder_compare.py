import os


#This file is used to compare two folders and find the differences between them. It will print out the files that are in one folder but not in the other.

#Change Log:

#Last Updated: 3/4/2026
#Written by: AJ Utz

def get_files_in_folder(folder_path, ignore_extensions):
    """Returns a set of file names in the given folder."""
    try:
        files = set()

        for file in os.listdir(folder_path):
            full_path = os.path.join(folder_path, file)

            if os.path.isfile(full_path):
                if ignore_extensions:
                    files.add(file)
                else:
                    name_without_ext = os.path.splitext(file)[0]
                    files.add(name_without_ext)

        return files
    
    except FileNotFoundError:
        print(f"Error: The folder '{folder_path}' does not exist.")
        return None
    except PermissionError:
        print(f"Error: Permission denied for folder '{folder_path}'.")
        return None

def get_folder_input(folder_number):
    print(f"Select how to enter Folder {folder_number}:")
    print("1. Enter folder path manually")
    print("2. Use current directory (must be in the current directory)")

    choice = input("Enter your choice (1 or 2): ").strip()

    if choice == "2":
        current_dir = os.getcwd()
        print(f"\nUsing current directory: {current_dir}")

        available_folders = [f for f in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, f))]

        if not available_folders:
            print("No folders found in the current directory. Please enter a folder path manually.")
            return None
        
        print("\nAvailable folders in the current directory:")
        for folder in sorted(available_folders):
            print(f"- {folder}")

        folder_name = input("\nEnter folder name: ").strip()
        return os.path.join(current_dir, folder_name)
    
    else:
        folder_path = input(f"Enter the path of Folder {folder_number}: ").strip()
        return folder_path


def run_folder_compare():
    print("\n=== Folder Comparison Tool ===\n")

    folder1 = get_folder_input(1)
    if folder1 is None:
        return
    
    folder2 = get_folder_input(2)
    if folder2 is None:
        return
    
    ignore_input = input("\nDo you want to compare files types (ignoring extensions)? (y/n): ").strip().lower()
    ignore_extensions = ignore_input == 'y'

    files1 = get_files_in_folder(folder1, ignore_extensions)
    files2 = get_files_in_folder(folder2, ignore_extensions)

    if files1 is None or files2 is None:
        return
    
    missing_files = files1 - files2

    print("\nFiles in the first folder but not in the second:")
    if not missing_files:
        print("None")
        return
    
    if ignore_extensions:
        print(f"\nFiles present in '{folder1}' but not in '{folder2}' (ignoring file extensions):")
    else:
        print(f"\nFiles present in '{folder1}' but not in '{folder2}':")

    for file in sorted(missing_files):
        print(file)

    save_option = input("\nDo you want to save the results to a file? (y/n): ").strip().lower()

    if save_option == 'y':
        output_file = input("Enter the name of the output file (e.g., 'missing_files.txt'): ")
        try:
            with open(output_file, 'w') as f:
                for file in sorted(missing_files):
                    f.write(file + '\n')
            print(f"Results saved to '{output_file}'.")
        except IOError as e:
            print(f"Error writing to file: {e}")


if __name__ == "__main__":
    run_folder_compare()