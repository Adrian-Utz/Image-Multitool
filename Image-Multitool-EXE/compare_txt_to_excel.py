import os
import pandas as pd

#Greetings! This tool will help see which photos you are missing!

#Changelog: Fixed bug where it was comparing the xlsx to txt instead of txt to xlsx.
#Added cancellation support.

#Written by: AJ Utz on: 1/28/2026
#Last Update: 5/8/2026

def run_txt_excel_compare():
    print("\n==== TXT <-> Excel Column Compare Tool ====")

    txt_file = input("Enter .txt file name: ").strip()
    excel_file = input("Enter Excel file name (.xlsx): ").strip()

    if not os.path.exists(txt_file):
        print("TXT file not found.")
        return

    if not os.path.exists(excel_file):
        print("Excel file not found.")
        return

    #Load txt values
    try:
        with open(txt_file, "r", encoding="utf-8")as f:
            txt_values = {
                line.strip().lower()
                for line in f
                if line.strip()
            }
    except Exception as e:
        print(f"Error reading txt file: {e}")
        return

    #Load excel
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        print(f"Error reading excel file: {e}")
        return

    #Show Columns
    print("\nAvailable Excel Columns:")
    for col in df.columns:
        print(f" - {col}")

    column = input("\nEnter column name to compare against: ").strip()

    if column not in df.columns:
        print("Invalid column name.")
        return

    excel_values = {
        str(val).strip().lower()
        for val in df[column]
        if pd.notna(val)
    }

    matches = sorted(excel_values & txt_values)
    missing = sorted(excel_values - txt_values)

    print(f"\nMatches found: {len(matches)}")
    for m in matches:
        print(f" ✓ {m}")

    print(f"\nNot found: {len(missing)}")
    for m in missing:
        print(f" ✕ {m}")

    #Output
    save = input("\nSave results to a txt file? (y/n): ").lower().strip()
    if save == "y":
        with open("matches.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(matches))

        with open("not_found.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(missing))

        print("\nSaved:")
        print(" - matches.txt")
        print(" - not_found.txt")

if __name__ == "__main__":
    run_txt_excel_compare()


def run_txt_excel_compare_gui(
        txt_file,
        excel_file,
        column,
        save=False,
        matches_filename='matches.txt',
        not_found_filename='not_found.txt',
        logger=print,
        progress_callback=None,
        cancel_event=None
    ):
    
    if not os.path.exists(txt_file):
        logger("TXT file not found.")
        return

    if not os.path.exists(excel_file):
        logger("Excel file not found.")
        return

    try:
        with open(txt_file, "r", encoding="utf-8")as f:
            txt_values = {
                line.strip().lower()
                for line in f
                if line.strip()
            }
    except Exception as e:
        logger(f"Error reading txt file: {e}")
        return

    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        logger(f"Error reading excel file: {e}")
        return

    if column not in df.columns:
        logger("Invalid column name.")
        return

    # Compare with progress tracking
    total_rows = len(df)
    excel_values = set()
    
    for idx, val in enumerate(df[column]):
        if cancel_event and cancel_event.is_set():
            logger("[INFO] TXT/Excel compare cancelled.")
            return
        if pd.notna(val):
            excel_values.add(str(val).strip().lower())
        if progress_callback and total_rows > 0:
            progress_callback(int(((idx + 1) / total_rows) * 100))

    matches = sorted(excel_values & txt_values)
    missing = sorted(excel_values - txt_values)

    logger(f"\nMatches found: {len(matches)}")
    for m in matches:
        logger(f" ✓ {m}")

    logger(f"\nNot found: {len(missing)}")
    for m in missing:
        logger(f" ✕ {m}")

    if save:
        try:
            with open(matches_filename, "w", encoding="utf-8") as f:
                f.write("\n".join(matches))

            with open(not_found_filename, "w", encoding="utf-8") as f:
                f.write("\n".join(missing))

            logger("\nSaved:")
            logger(f" - {matches_filename}")
            logger(f" - {not_found_filename}")
        except Exception as e:
            logger(f"Error saving results: {e}")
