import builtins
import os
import string
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


#This program is to download images from URLs listed in an Excel file. 
#The user can select which columns contain the URLs, and the program will download the images to a specified folder. 

#Change Log: 
#Changed the way file extensions are determined to be more robust, including checking the URL and content type.
#Added better handling for HYPERLINK formulas in Excel, with warnings if they can't be parsed.
#Added an interactive wrapper to make it easier for users to select columns and options without modifying the code directly.
#Added handling of different types of content (images, videos, PDFs) and assigned appropriate extensions.
#Added documentation and comments for better readability and maintainability.

#Written by AJ Utz on: 2/26/2026 
#Last Edit: 3/3/2026



def download_from_excel(
    file_name,
    image_columns,
    rename_column=None,
    output_folder="downloaded_images",
    max_workers=20
):
    df = pd.read_excel(file_name)

    #Convert column indexes to names
    def normalize_column(col):
        if isinstance(col, int):
            return df.columns[col]
        return col

    image_columns = [normalize_column(col) for col in image_columns]

    if rename_column is not None:
        rename_column = normalize_column(rename_column)

    #Validate columns
    for col in image_columns:
        if col not in df.columns:
            raise ValueError(f"Image column '{col}' not found.")

    if rename_column and rename_column not in df.columns:
        raise ValueError(f"Rename column '{rename_column}' not found.")

    os.makedirs(output_folder, exist_ok=True)

    download_jobs = []

    #Iterate through each row and create download jobs for valid URLs in the specified image columns
    for row_index, row in df.iterrows():
        base_name = None

        if rename_column:
            base_name = str(row[rename_column]).strip()
            base_name = "".join(c for c in base_name if c not in r'<>:"/\|?*')

        letter_index = 0

        def get_suffix(index):
            #Return letters like A, B, ..., Z, AA, AB, ...
            letters = string.ascii_uppercase
            result = ""
            while True:
                result = letters[index % 26] + result
                index = index // 26 - 1
                if index < 0:
                    break
            return "_" + result if result else ""
        
        #Iterate through the specified image columns and create download jobs for valid URLs
        for col in image_columns:
            url = row[col]

            if pd.isna(url):
                continue

            if isinstance(url, builtins.str):
                url = url.strip()
                
                #Only process HYPERLINK formulas if you actually have them
                if url.upper().startswith("=HYPERLINK"):
                    try:
                        #This regex safely extracts the first URL in quotes
                        import re
                        match = re.search(r'"(http[s]?://[^"]+)"', url)
                        if match:
                            url = match.group(1)
                        else:
                            print(f"Warning: Could not parse HYPERLINK in row {row_index}, column '{col}'. Skipping.")
                            continue
                    except Exception:
                        print(f"Warning: Could not parse HYPERLINK in row {row_index}, column '{col}'. Skipping.")
                        continue
            else:
                url = builtins.str(url)

            #Skip anything that doesn't look like a URL
            if not url.lower().startswith("http"):
                continue
            
            #Add the download job with the URL, base name, suffix, and row index for naming
            download_jobs.append((url, base_name, get_suffix(letter_index), row_index))

            letter_index += 1

    print(f"\nFound {len(download_jobs)} images to download.")

    def download_file(job, pbar):
        url, base_name, suffix, index = job

        #Determine file extension from URL or content type, and sanitize filename
        try:
            r = requests.get(url, timeout=15, stream=True)
            r.raise_for_status()
            content_type = r.headers.get("Content-Type", "").lower()

            ext = None

            #First try to determine the extension from the URL
            last_part = url.split("/")[-1]
            if "." in last_part:
                possible_ext = last_part.split(".")[-1].split("?")[0].lower()
                if len(possible_ext) <= 5:
                    ext = possible_ext
            
            #If we couldn't determine the extension from the URL, try to infer it from the content type
            if not ext:
                if "video/" in content_type:
                    ext = content_type.split("video/")[-1].split(";")[0]
                elif "image/" in content_type:
                    ext = content_type.split("image/")[-1].split(";")[0]
                elif "application/pdf" in content_type:
                    ext = "pdf"
                elif "application/" in content_type:
                    ext = content_type.split("application/")[-1].split(";")[0]
                else:
                    ext = "bin"
            
            #Sanitize extension
            if base_name:
                filename = f"{base_name}{suffix}.{ext}"
            else:
                filename = f"image_{index}.{ext}"

            filepath = os.path.join(output_folder, filename)

            #Prevent overwriting duplicates
            counter = 1
            original_path = filepath
            while os.path.exists(filepath):
                name, ext = os.path.splitext(original_path)
                filepath = f"{name}_{counter}{ext}"
                counter += 1

            #Stream download to handle large files without consuming too much memory
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        except Exception as e:
            print(f"Failed: {url} | {e}")

    with tqdm(total=len(download_jobs), desc="Downloading", ascii=True, dynamic_ncols=False) as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(download_file, job, pbar) for job in download_jobs]
            
            for future in as_completed(futures):
                future.result()
                pbar.update(1)

    print("\nDownload complete.")



#INTERACTIVE WRAPPER


def run_excel_image_downloader():
    print("\n===== Excel Image Downloader =====")

    file_name = input("Enter Excel file name (include .xlsx): ").strip()

    #Check if file exists
    try:
        df = pd.read_excel(file_name)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    #Display available columns for user selection
    print("\nAvailable columns:")
    for i, col in enumerate(df.columns):
        print(f"{i}: {col}")

    selected = input(
        "\nEnter image column numbers or names (comma separated, or a range like 2-5): "
    ).strip()

    image_cols = []

    #Process user input for image columns, allowing for both column names and indexes, as well as ranges like 2-5
    for item in selected.split(","):
        item = item.strip()
        
        #Check for a range like 2-10
        if "-" in item:
            start, end = item.split("-")
            start = start.strip()
            end = end.strip()
            #Validate that both start and end are digits before converting to integers
            if start.isdigit() and end.isdigit():
                start = int(start)
                end = int(end)
                #Add all column indexes in the range
                image_cols.extend(range(start, end + 1))
            else:
                print(f"Ignoring invalid range: {item}")
        else:
            #Single column
            if item.isdigit():
                image_cols.append(int(item))
            else:
                image_cols.append(item)

    rename_choice = input(
        "\nRename images using a column? (y/n): "
    ).strip().lower()

    rename_column = None

    if rename_choice == "y":
        rename_input = input(
            "Enter rename column number or name: "
        ).strip()

        #Process user input for rename column, allowing for both column names and indexes
        if rename_input.isdigit():
            rename_column = int(rename_input)
        else:
            rename_column = rename_input

    output_folder = input(
        "Output folder name (leave blank for 'downloaded_images'): "
    ).strip() or "downloaded_images"

    #Run the downloader with the specified options
    #And handle any exceptions that occur during the download process
    try:
        download_from_excel(
            file_name,
            image_cols,
            rename_column,
            output_folder
        )
    except Exception as e:
        print(f"Error: {e}")


#STANDALONE MODE


if __name__ == "__main__":
    run_excel_image_downloader()