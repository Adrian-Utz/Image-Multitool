import os
import pandas as pd

#Greetings! This tool will help see which photos you are missing!

#Changelog: Fixed bug where it was comparing the xlsx to txt instead of txt to xlsx.

#Written by: AJ Utz on: 1/28/2026
#Last Update: 1/29/2026

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
