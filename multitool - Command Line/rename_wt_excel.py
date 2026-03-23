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

#Written by: AJ Utz on: 12/31/2025

#Last Edit: 3/18/2025

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


    #Get JPG files
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

            file_base = os.path.splitext(original_filename)[0]
            file_base_normalized = file_base.strip().lower()
            #Debug messages commented out
            #print("EXCEL BASE:", repr(excel_base))
            #print("FILE BASE:", repr(file_base), "->", repr(original_filename))
            #print("MATCH CONDITION:", file_base == excel_base, file_base.startswith(excel_base + "_"), file_base.startswith(excel_base + "-"))            
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
                base_name, original_ext = os.path.splitext(source_filename)

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
                    print(f"Copied: {source_filename} -> {output_path}/{new_filename}")
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
