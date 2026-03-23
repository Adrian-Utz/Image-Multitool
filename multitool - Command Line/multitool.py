import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

import image_reformatting
import rename_wt_excel
import compare_txt_to_excel
import web_downloading
import folder_compare
import search_files
import list_files_by_extension
import count_files_by_extension

#This is the multitool! This file will allow you to do multiple things. See the change log for new additions.
#This program will automatically create a __pycache__ folder with a compiled version of this code. You can delete it if you need to.
#It is just to make it faster next time you run it.
#I plan on making this a robust python tool you can use for file management.

#Change Log:
#Merged list_jpg_files into this file. Added option to run it. Added the file search function. Also added the Copy function to the search.
#Updated the manual search input to allow multiple searches at once. Moved the folder creation into the if statement.
#Updated the list_files_by_extension def to make it more robust, and it can handle more file types now.
#Added Image formatting and conversion compatibility.
#Added ranaming with an excel table.
#Added the comparing txt and excel files. To find missing photos.
#Added comments, fixed the numbering menu. Added a Return prompt
#Added the Excel Image Downloader. This will download images from URLs in an Excel file. 
#You can select which columns to use for the URLs. It will also use multithreading to speed up the downloads.
#Added the folder comparison tool. This will compare two folders and find the differences between them. 
#It will print out the files that are in one folder but not in the other. You can also choose to ignore file extensions when comparing.
#Took out all the functions in this file and put them in their own files. This makes it easier to read and maintain. 
#Thought about making a GUI for it but I think the command line is fine for now. Maybe in the future I will add a GUI option. 
#I coded a basic GUI but it was a pain to get it to work with the progress bars and the output. I will save it for a future update when I have more time to work on it.


#Last Update: 3/19/2026

#Written by: AJ Utz on: 12/3/2025


def main_menu():

    RETURN_PROMPT = "\nPress Enter to return to the main menu..."

    while True:
        print("\n===== File Tools Menu =====")
        print("1. Count files by extension")
        print("2. List filenames")
        print("3. Search and Copy files") 
        print("4. Image reformatting / conversion")
        print("5. Excel Renaming Tool")
        print("6. TXT <-> Excel Compare Tool")
        print("7. Excel Image Downloader")
        print("8. Folder Comparison Tool")
        print("9. Exit")
        print("===========================")

        choice = input("Select an option (1-9): ").strip()

        #If you want this to run you need count_files_by_extension.py in the same folder as the multitool.py file
        if choice == "1":
            count_files_by_extension.count_files_by_extension()
            input(RETURN_PROMPT)

        #If you want this to run you need list_files_by_extension.py in the same folder as the multitool.py file
        elif choice == "2":
            list_files_by_extension.list_files_by_extension()
            input(RETURN_PROMPT)

        #If you want this to run you need search_files.py in the same folder as the multitool.py file
        elif choice == "3":
            search_files.search_files()
            input(RETURN_PROMPT)

        #If you want this to run you need image_reformatting.py in the same folder as the multitool.py file
        elif choice == "4":
            image_reformatting.run_image_reformatter()
            input(RETURN_PROMPT)

        #If you want this to run you need rename_wt_excel.py in the same folder as the multitool.py file
        elif choice == "5":
            rename_wt_excel.run_excel_image_sku_tool()
            input(RETURN_PROMPT)

        #If you want this to run you need compare_txt_to_excel.py in the same folder as the multitool.py file
        elif choice == "6":
            compare_txt_to_excel.run_txt_excel_compare()
            input(RETURN_PROMPT)
        
        #If you want this to run you need web_downloading.py in the same folder as the multitool.py file
        elif choice == "7":
            web_downloading.run_excel_image_downloader()
            input(RETURN_PROMPT)

        elif choice == "8":
            folder_compare.run_folder_compare()
            input(RETURN_PROMPT)
            
        
        elif choice == "9":
            print("Exiting the program. Goodbye!")
            break

        else:
            print("Invalid choice — please enter 1-9.")



if __name__ == "__main__":
    main_menu()


'''
def run_count():
    folder = filedialog.askdirectory(title="Select a folder")
    if folder:
        count_files_by_extension.count_files_by_extension(folder)

def run_list():
    folder = filedialog.askdirectory(title="Select a folder")
    if folder:
        list_files_by_extension.list_files_by_extension(folder)

def run_search():
    folder = filedialog.askdirectory(title="Select a folder")
    if folder:
        search_files.search_files(folder)

def run_image():
    folder = filedialog.askdirectory(title="Select a folder")
    if folder:
        image_reformatting.run_image_reformatter(folder)

def run_excel_rename():
    folder = filedialog.askdirectory(title="Select an folder")
    if folder:
        rename_wt_excel.run_excel_image_sku_tool(folder)

def run_compare():
    folder = filedialog.askdirectory(title="Select an folder")
    if folder:
        compare_txt_to_excel.run_txt_excel_compare(folder)

def run_downloader():
    folder = filedialog.askdirectory(title="Select an folder")
    if folder:
        web_downloading.run_excel_image_downloader(folder)

def run_folder_compare():
    folder = filedialog.askdirectory(title="Select an folder")
    if folder:
        folder_compare.run_folder_compare(folder)



def run_with_progress(func):
    progress.start()
    func()
    progress.stop()

def clear_output():
    output.delete(1.0, tk.END)



class TextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
    
    def flush(self):
        pass


def main():
    global progress

    root = tk.Tk()
    root.title("File Management Multitool")
    root.state("zoomed")  # Start maximized
    root.resizable(True, True)
    root.configure(padx=20, pady=20)

    tk.Label(root, text="File Management Multitool", font=("Arial", 16)).pack(pady=10)

    progress = ttk.Progressbar(root, orient="horizontal", mode="indeterminate")
    progress.pack(pady=10)

    output = tk.Text(root, height=15, bg="black", fg="lime", insertbackground="white")
    output.pack(fill="both", expand=True)

    sys.stdout = TextRedirector(output)

    tk.Button(root, text="Count files", command=lambda: run_with_progress(run_count)).pack(pady=5)
    tk.Button(root, text="List files", command=lambda: run_with_progress(run_list)).pack(pady=5)
    tk.Button(root, text="Search and Copy files", command=lambda: run_with_progress(run_search)).pack(pady=5)
    tk.Button(root, text="Image reformatting / conversion", command=lambda: run_with_progress(run_image)).pack(pady=5)
    tk.Button(root, text="Excel Renaming Tool", command=lambda: run_with_progress(run_excel_rename)).pack(pady=5)
    tk.Button(root, text="TXT <-> Excel Compare Tool", command=lambda: run_with_progress(run_compare)).pack(pady=5)
    tk.Button(root, text="Excel Image Downloader", command=lambda: run_with_progress(run_downloader)).pack(pady=5)
    tk.Button(root, text="Folder Comparison Tool", command=lambda: run_with_progress(run_folder_compare)).pack(pady=5)
    #Button for testing
    tk.Button(root, text="Clear Log", command=clear_output).pack(pady=5)

    tk.Button(root, text="Exit", command=root.quit).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
'''

