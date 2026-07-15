import os
import re
import math
import shutil
import pandas as pd

#This program is to make bulk renaming faster. This program should look at the filename, find the cell with matching info, then rename it to the SKU name.

#Change Log:
#Added Comments to clearly explain each step of the process.
#Added error handling for file operations to catch and report any issues during copying.
#Added a summary at the end to report how many files were copied, how many were missing, how many were skipped due to existing files, and how many errors occurred.
#Added Documentation
#Added the ignore_file_extension option to allow matching based on base name regardless of file extension, providing more flexibility in handling different image formats.
#Added cancellation support.
#Fixed a potential bug. This line: print(f"Copied: {source_filename} -> {output_path}\{new_filename}") was using a single backslash which could cause issues on some systems. 
#I changed it to this: print(f"Copied: {source_filename} -> {output_path}\\{new_filename}") could be seen as a invalid escape sequence. 
#By using a double backslash, we ensure that it is treated as a literal backslash in the output string, which is important for correctly displaying file paths on Windows systems.

#Written by: AJ Utz on: 1/14/2025

#Last Edit: 5/8/2026

def sanitize_filename(name):

    if not isinstance(name, str):
        return ""
    
    name = name.strip() #Remove leading and trailing whitespace

    name = re.sub(r'[\\/*?:"<>|]', '_', name) #Replace invalid characters with underscores

    name = re.sub(r'[\x00-\x1f\x7f]', '', name) #Remove control characters

    name = name.replace("..", "") #Remove double dots to prevent directory traversal issues

    return name

def run_excel_image_sku_tool():
    print("\n===== Excel Image -> SKU Copy Tool =====")
    
    folder_path = '.'
    valid_extensions = ('.jpg', '.jpeg')
    output_folder = 'renamed_by_sku'

    copied_count = 0
    missing_count = 0
    skipped_count = 0
    error_count = 0

    include_subfolders = input("Include subfolders? (y/n): ").strip().lower() == 'y'

    #Ask for Excel file
    excel_file = input("Enter Excel file name(example: images.xlsx): ").strip()

    #Check if file exists
    if not os.path.exists(excel_file):
        print(f"File does not exist")
        exit()

    #Load Excel file
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        exit()

    #Show Available Columns
    print("Available Columns in excel: ")
    for col in df.columns:
        print(f" - {col}")

    #Get column names from user
    image_col = input("\nEnter column name for Image names: ").strip()
    sku_col = input("Enter column name for SKU names: ").strip()

    preserve_variants_input = input("Preserve variant suffixes in filenames? (y/n): ").strip().lower()
    preserve_variants = preserve_variants_input == 'y'

    #Validate columns
    if image_col not in df.columns or sku_col not in df.columns:
        print(f"Excel must contain columns: '{image_col}' and '{sku_col}'")
        exit()

    #Prepare Output
    output_path = os.path.join(folder_path, output_folder)
    os.makedirs(output_path, exist_ok=True)

    #Get JPG files (optionally including subfolders, but skip output folder)
    if include_subfolders:
        jpg_files = {}
        abs_output_path = os.path.abspath(output_path)
        for root, dirs, files in os.walk(folder_path):
            # Don't walk into the output folder
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != abs_output_path]
            for f in files:
                if f.lower().endswith(valid_extensions):
                    rel_path = os.path.relpath(os.path.join(root, f), folder_path)
                    jpg_files[rel_path.lower()] = rel_path
    else:
        jpg_files = {f.lower(): f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)}

    if not jpg_files:
        print("No JPG files found in the folder.")
        exit()

    #Loop through each row in the Excel file and attempt to match and copy files
    for _, row in df.iterrows():

        raw_image = row[image_col] #Get raw image name from Excel, which could be a string or a number
        raw_sku = row[sku_col] #Get raw SKU name from Excel, which could also be a string or a number

        #Handle NaN properly
        if pd.isna(raw_image) or pd.isna(raw_sku):
            continue

        #Convert Excel image name to string safely, handling numbers (like 4352019.0)
        if isinstance(raw_image, float):
            image_name = str(int(raw_image))  #e.g., 4352019.0 -> "4352019"
        else:
            image_name = str(raw_image)

        #Convert SKU to string safely, handling numbers as well
        image_name = sanitize_filename(image_name).strip()
        sku_name = sanitize_filename(str(raw_sku)).strip()

        #Skip rows with empty names
        if not image_name or not sku_name:
            continue

        #Ensure image name has a valid extension
        if not image_name.lower().endswith(valid_extensions):
            image_name += ".jpg"

        #Get base name without extension from Excel
        excel_base = os.path.splitext(image_name)[0].strip().lower()
        
        #Find all matching files in the folder
        exact_match = None
        variant_matches = []

        #We loop through the jpg files and check for matches based on the base name. 
        #We look for an exact match first, and if we find it, we store it as the exact match. 
        #We also look for variant matches that start with the base name followed by an underscore or hyphen, and we store those in a list of variant matches.
        #This way, we can prioritize the exact match when copying, but also include any relevant variants if the user chooses to preserve them.
        for original_filename in jpg_files.values():
            file_base = os.path.splitext(os.path.basename(original_filename))[0]
            file_base_normalized = file_base.strip().lower()
            if file_base_normalized == excel_base:
                exact_match = original_filename
            elif file_base_normalized.startswith(excel_base + "_") or file_base_normalized.startswith(excel_base + "-"):
                variant_matches.append(original_filename)

        #Build final matching list
        matching_files = []
        if exact_match:
            matching_files.append(exact_match)
        matching_files.extend(variant_matches)

        #Copy matched files
        if matching_files:
            for source_filename in matching_files:

                source_path = os.path.join(folder_path, source_filename)
                base_name, original_ext = os.path.splitext(os.path.basename(source_filename))

                if preserve_variants:
                    match = re.search(r'[-_](.+)$', base_name)
                    #Suffix preservation logic: If the original filename has a suffix after the base name (like "_1" or "-variant")
                    #We capture that and append it to the new filename after the SKU name, preserving the original extension. 
                    #If there is no suffix, we just use the SKU name with the original extension.
                    if match:
                        separator = match.group(0)[0]
                        suffix_part = match.group(1)
                        new_filename = f"{sku_name}{separator}{suffix_part}{original_ext}"
                    else:
                        new_filename = f"{sku_name}{original_ext}"
                else:
                    new_filename = f"{sku_name}{original_ext}"

                dest_path = os.path.join(output_path, new_filename)

                if os.path.exists(dest_path):
                    print(f"Skipping (already exists): {new_filename}")
                    skipped_count += 1
                    continue

                try:
                    shutil.copy2(source_path, dest_path)
                    print(f"Copied: {source_filename} -> {output_path}\\{new_filename}")
                    copied_count += 1
                except Exception as e:
                    print(f"Error copying {source_filename}: {e}")
                    error_count += 1

        else:
            print(f"No match found for image: {image_name}")
            missing_count += 1

    print(f"""
Summary:
Copied: {copied_count}
Missing Images: {missing_count}
Skipped (Already Exists): {skipped_count}
Errors: {error_count}
""")


if __name__ == "__main__":
    run_excel_image_sku_tool()


def rename_from_excel_gui(
        excel_file,
        image_col,
        sku_col,
        preserve_variants=False,
        ignore_file_extension=False,
        folder_path='.',
        output_folder='renamed_by_sku',
        include=False,
        logger=print,
        progress_callback=None,
        cancel_event=None
    ):
    
    """Non-interactive wrapper for GUI use. Mirrors the behavior of run_excel_image_sku_tool but accepts parameters."""
    folder_path = folder_path or '.'
    valid_extensions = ('.jpg', '.jpeg')
    output_path = os.path.join(folder_path, output_folder)
    os.makedirs(output_path, exist_ok=True)

    try:
        df = pd.read_excel(
            excel_file,
            converters={
                image_col: lambda x: str(x).strip(), #Convert image column to string and strip whitespace, handling numbers as well
                sku_col: lambda x: str(x).strip() #Convert SKU column to string and strip whitespace, handling numbers as well
            }
            )
    except Exception as e:
        logger(f"Error loading Excel file: {e}")
        return

    # Convert column numbers to column names
    if isinstance(image_col, int):
        if image_col < 0 or image_col >= len(df.columns):
            logger(f"Image column index {image_col} is out of range. Available columns: {len(df.columns)}")
            return
        image_col = df.columns[image_col]
    
    if isinstance(sku_col, int):
        if sku_col < 0 or sku_col >= len(df.columns):
            logger(f"SKU column index {sku_col} is out of range. Available columns: {len(df.columns)}")
            return
        sku_col = df.columns[sku_col]

    if image_col not in df.columns or sku_col not in df.columns:
        logger(f"Excel must contain columns: '{image_col}' and '{sku_col}'")
        return

    # Build file list based on extension matching preference and include flag
    abs_output_path = os.path.abspath(output_path)
    if include:
        files_to_check = {}
        for root, dirs, files in os.walk(folder_path):
            if cancel_event and cancel_event.is_set():
                logger("[INFO] Rename from Excel cancelled.")
                return
            # Don't walk into the output folder
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != abs_output_path]
            for f in files:
                if cancel_event and cancel_event.is_set():
                    logger("[INFO] Rename from Excel cancelled.")
                    return
                if ignore_file_extension or f.lower().endswith(valid_extensions):
                    rel_path = os.path.relpath(os.path.join(root, f), folder_path)
                    files_to_check[rel_path.lower()] = rel_path
    else:
        if ignore_file_extension:
            all_files = {f.lower(): f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))}
            files_to_check = all_files
        else:
            files_to_check = {f.lower(): f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)}

    copied_count = 0
    missing_count = 0
    skipped_count = 0
    error_count = 0
    total_rows = len(df)

    for row_idx, (_, row) in enumerate(df.iterrows()):
        if cancel_event and cancel_event.is_set():
            logger("[INFO] Rename from Excel cancelled.")
            return
        if progress_callback and total_rows > 0:
            progress_callback(int(((row_idx) / total_rows) * 100))
        raw_image = row[image_col]
        raw_sku = row[sku_col]

        if pd.isna(raw_image) or pd.isna(raw_sku):
            continue

        if isinstance(raw_image, float):
            image_name = str(int(raw_image))
        else:
            image_name = str(raw_image)

        image_name = sanitize_filename(image_name).strip()
        sku_name = sanitize_filename(str(raw_sku)).strip()

        if not image_name or not sku_name:
            continue

        # Handle file extension matching based on user preference
        if ignore_file_extension:
            # Strip extension for matching
            excel_base = os.path.splitext(image_name)[0].strip().lower()
        else:
            # Add .jpg if missing (original behavior)
            if not image_name.lower().endswith(valid_extensions):
                image_name += ".jpg"
            excel_base = os.path.splitext(image_name)[0].strip().lower()

        exact_match = None
        variant_matches = []

        #We loop through the files to check and look for matches based on the base name.
        #If ignore_file_extension is True, we will match based on the base name regardless of the file extension,
        #allowing for more flexibility in handling different image formats.
        for original_filename in files_to_check.values():
            file_base = os.path.splitext(os.path.basename(original_filename))[0]
            file_base_normalized = file_base.strip().lower()
            if file_base_normalized == excel_base:
                exact_match = original_filename
            elif file_base_normalized.startswith(excel_base + "_") or file_base_normalized.startswith(excel_base + "-"):
                variant_matches.append(original_filename)

        matching_files = []
        if exact_match:
            matching_files.append(exact_match)
        matching_files.extend(variant_matches)

        #If we found any matching files, we proceed to copy them to the output folder with the new SKU-based name.
        if matching_files:
            for source_filename in matching_files:
                if cancel_event and cancel_event.is_set():
                    logger("[INFO] Rename from Excel cancelled.")
                    return
                source_path = os.path.join(folder_path, source_filename)
                base_name, original_ext = os.path.splitext(os.path.basename(source_filename))

                if preserve_variants:
                    match = re.search(r'[-_](.+)$', base_name)
                    if match:
                        separator = match.group(0)[0]
                        suffix_part = match.group(1)
                        new_filename = f"{sku_name}{separator}{suffix_part}{original_ext}"
                    else:
                        new_filename = f"{sku_name}{original_ext}"
                else:
                    new_filename = f"{sku_name}{original_ext}"

                dest_path = os.path.join(output_path, new_filename)

                #Before copying, we check if a file with the new name already exists in the output folder. 
                #If it does, we skip copying that file and log a message indicating that it was skipped due to already existing.
                if os.path.exists(dest_path):
                    logger(f"Skipping (already exists): {new_filename}")
                    skipped_count += 1
                    continue

                try:
                    shutil.copy2(source_path, dest_path)
                    logger(f"Copied: {source_filename} -> {output_path}/{new_filename}")
                    copied_count += 1
                except Exception as e:
                    logger(f"Error copying {source_filename}: {e}")
                    error_count += 1
        else:
            logger(f"No match found for image: {image_name}")
            missing_count += 1

    logger(f"\nSummary:\nCopied: {copied_count}\nMissing Images: {missing_count}\nSkipped (Already Exists): {skipped_count}\nErrors: {error_count}\n")
