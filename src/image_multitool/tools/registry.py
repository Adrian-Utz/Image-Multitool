import importlib
from dataclasses import dataclass

"""
Catalogue of tools shown in the GUI. Each module exposes ``run_dialog(app)``.

Written by: AJ Utz
Written on: 11/18/2026
Latest Update: 11/18/2026
"""

@dataclass(frozen=True)
class ToolInfo:
    label: str
    module: str
    requirement: str

    def launch(self, app):
        importlib.import_module(self.module).run_dialog(app)


_P = "image_multitool.tools."

TOOLS = (
    ToolInfo("Count files by extension", _P + "files.count_files_by_extension", "Requires: A folder to scan for files."),
    ToolInfo("List filenames", _P + "files.list_files_by_extension", "Requires: A folder to list files from."),
    ToolInfo("Search & Copy", _P + "files.search_files", "Requires: A source folder to search, search term or .txt file, and destination folder."),
    ToolInfo("Image reformat", _P + "images.image_reformatting", "Requires: A folder containing images to reformat."),
    ToolInfo("Image optimize", _P + "images.image_optimization", "Requires: A folder containing images to optimize without changing dimensions or format."),
    ToolInfo("Image quality grader", _P + "images.image_quality_grader", "Requires: A folder of images. BRISQUE optionally requires model and range files."),
    ToolInfo("Excel rename", _P + "excel.rename_wt_excel", "Requires: An Excel file with renaming data and a folder with images."),
    ToolInfo("TXT <-> Excel Compare", _P + "excel.compare_txt_to_excel", "Requires: A .txt file, an Excel file (.xlsx or .xls), and a column name."),
    ToolInfo("Excel image downloader", _P + "excel.web_downloading", "Requires: An Excel file with image URLs and column names."),
    ToolInfo("Folder compare", _P + "folders.folder_compare", "Requires: Two folders to compare."),
    ToolInfo("Backup files", _P + "files.create_backup", "Requires: One or more files/folders to back up and a destination folder."),
)
