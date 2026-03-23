# Multitool - Command Line File Utilities

A simple Python-based command-line multitool for common file operations and light data workflows.

## Features

- Count files by extension
- List files by extension
- Search and (optionally) copy files
- Image reformatting/conversion
- Rename by Excel SKU mapping
- Compare TXT and Excel content
- Download images from Excel URL list
- Compare folder contents

## Requirements

- Python 3.8+ (recommended)
- Modules in same folder:
  - `multitool.py`
  - `count_files_by_extension.py`
  - `list_files_by_extension.py`
  - `search_files.py`
  - `image_reformatting.py`
  - `rename_wt_excel.py`
  - `compare_txt_to_excel.py`
  - `web_downloading.py`
  - `folder_compare.py`

## Quick Start

1. Open a terminal in project folder.
2. Run:
   ```bash
   python multitool.py
   ```
3. Choose one of the options 1-9 from the menu.

## Notes

- The toolkit is designed as a menu-based command-line app.
- The code includes a commented-out GUI section for future enhancement.
- The `__pycache__` folder may be created automatically by Python and can be deleted safely.

## Author

- AJ Utz
- Last recorded update in source: 3/19/2026
