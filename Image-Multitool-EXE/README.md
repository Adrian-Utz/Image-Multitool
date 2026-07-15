# Multitool GUI

A comprehensive file management and processing application with a modern, responsive GUI. Convert images, rename files using Excel data, search and copy files, download images from URLs, compare folders, and more—all with real-time progress tracking and background threading.

**Version:** 1.2.6
**Last Updated:** July 13, 2026  
**Status:** ✓ Production Ready

## Features

### Core Tools
- **Count Files by Extension** — Analyze file distribution in a folder with optional subfolder traversal.
- **List Filenames** — List and export files by extension with optional txt output.
- **Search & Copy** — Find files by name and optionally copy matches to a timestamped folder.
- **Image Reformat/Convert** — Batch convert images between formats (jpg, png, webp, tiff, bmp, avif, heic, heif) with optional resizing, compression, and PPI settings.
- **Excel Rename Tool** — Rename files based on Excel data mapping (e.g., match image file numbers to SKU names).
- **TXT ↔ Excel Compare** — Compare a text file against an Excel column to find matches and missing items.
- **Excel Image Downloader** — Download images from URLs listed in an Excel file with multi-threaded support.
- **Folder Comparison** — Compare two folders and find files that differ, with optional extension-ignore mode.

### Advanced Features
- ✓ **Background Threading** — All tools run asynchronously; UI stays responsive during long operations
- ✓ **Real-time Logging** — Watch results stream live in the GUI log area
- ✓ **Task Queue Display** — Monitor active and pending tasks with visual indicators (fixed in v1.2.4)
- ✓ **Resizable Task Queue and Log** — Drag the divider between queue and log to adjust size dynamically (new in v1.0.1)
- ✓ **Progress Tracking** — Visual progress bar and status updates for each operation
- ✓ **Cancel Operations** — Stop long-running tasks with a single click (fixed in v1.1.3)
- ✓ **Thread-Safe Output** — Proper synchronization prevents log corruption
- ✓ **Light/Dark Mode** — User can change their background to be easier on the eyes (new in v1.1.3)

## Installation

### Option 1: Run from Source (Requires Python)

#### Prerequisites
- Python 3.8 or later
- pip (Python package manager)

#### Setup
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the GUI:**
   ```bash
   python gui.py
   ```

### Option 2: Use Standalone Executable (Recommended)

No Python installation required!

1. **Download or build:**
   - Pre-built: `dist/Multitool.exe` (64 MB)
   - Double-click to run

2. **That's it!** The GUI will launch with all dependencies bundled.

## Usage

### Launching the Application

**From Source:**
```bash
python gui.py
```

**From Executable:**
- Double-click `Multitool.exe` (or right-click → Open)
- Or run from command line: `.\dist\Multitool.exe`

### Building the Executable

**Prerequisites:**
```bash
pip install pyinstaller
```

**Build command:**
```bash
.\.venv\Scripts\python.exe -m PyInstaller multitool.spec
```

**Output:**
- `dist/Multitool.exe` — Standalone executable
- `build/` — Intermediate build files (safe to delete)
- `multitool.spec` — PyInstaller configuration file

**File Size:** ~64 MB (includes Python interpreter + all dependencies)

**Distribution:**
- Copy `dist/Multitool.exe` to any Windows machine
- No Python, no dependencies, no installation required
- Should work on Windows 7 and later

### GUI Layout

```
┌─────────────────────────┬──────────────────────────────────┐
│  Tools (Left Panel)     │  Status & Controls (Top Right)   │
│                         │  ├─ Status: Idle/Running         │
│  • Count files          │  ├─ Task Counter                 │
│  • List files           │  └─ Cancel Button                │
│  • Search & Copy        │                                  │
│  • Image Reformat       │                                  │
│  • Excel Rename         │                                  │
│  • TXT ↔ Excel          │                                  │
│  • Image Downloader     │  Active Tasks Queue              │
│  • Folder Compare       │  ├─ Running tasks                │
│                         │  └─ Pending tasks                │
│  [Options]              │                                  │
│  [Exit]                 │  Log Area (scrollable)           │
│                         │  [Real-time operation output]    │
│                         │                                  │
│                         │  Progress Bar + Status           │
└─────────────────────────┴──────────────────────────────────┘
```

### Quick Workflow Examples

#### Example 1: Batch Convert Images to JPG
1. Click **Image reformat** button
2. Select folder with images
3. Enter target extension: `jpg`
4. Choose options: compression, resizing, PPI
5. Watch progress in log; results appear in console
6. Check "Complete ✓" status when done

#### Example 2: Rename Files Using Excel
1. Prepare Excel file with columns:
   - Column A: Original filenames (e.g., `IMG001.jpg`)
   - Column B: New names (e.g., `PROD_SKU123.jpg`)
2. Click **Excel rename** button
3. Select Excel file
4. Enter column names when prompted
5. Files are copied and renamed to `renamed_by_sku` folder

#### Example 3: Download Images from URLs
1. Create Excel file with:
   - Column A: Image URLs (e.g., `https://example.com/img.jpg`)
   - Column B (optional): New filenames
2. Click **Excel image downloader**
3. Select Excel file, specify URL column
4. Download starts; streams to `downloaded_images` folder
5. Monitor progress in task queue

#### Example 4: Compare Two Folders
1. Click **Folder compare**
2. Select first folder
3. Select second folder
4. Optionally ignore extensions
5. Results show files in folder 1 not in folder 2
6. Optionally save to `missing_files.txt`

## Task Queue & Threading

### Status Indicators
- **Green "Idle"** — No active operations
- **Blue "Running..."** — One or more tasks executing in background
- **Green "Complete ✓"** — Most recent task finished

### Task Queue Display
Shows top 2 active and pending tasks:
```
▶ Running (1 active):
  1. Converting images to .jpg in Desktop
  
⏳ Pending (2):
  1. Listing files in Documents
  2. Comparing folders
  ... +1 more
```

### Cancelling Operations
1. Click the **Cancel Current** button (active when running)
2. Current task will stop gracefully
3. Any pending tasks remain in queue

### Threading Safety
- All background work isolated from GUI thread
- Logging synchronized to prevent corruption
- UI remains responsive even during heavy operations
- Thread pool limited to 4 workers (prevents system overload)

## File Structure

```
multitool/
├── gui.py                            # Main GUI application (enhanced threading)
├── count_files_by_extension.py       # Count files tool (logger support)
├── list_files_by_extension.py        # List files tool (GUI wrapper)
├── search_files.py                   # Search & copy tool (GUI wrapper)
├── image_reformatting.py             # Image conversion (batch processor)
├── rename_wt_excel.py                # Excel rename tool (file mapping)
├── compare_txt_to_excel.py           # TXT/Excel comparison tool
├── web_downloading.py                # Image downloader (multi-threaded)
├── folder_compare.py                 # Folder diff tool (GUI wrapper)
├── gui_helper.py                     # Helper functions for the GUI
├── options.py                        # Seperate Options window
├── requirements.txt                  # Python dependencies
├── multitool.spec                    # PyInstaller spec (auto-generated)
├── README.md                         # This file
├── changelog.md                      # Documentation of Changes
└── dist/
    └── Multitool.exe                 # Standalone executable (64 MB)
```

## Dependencies

All included in `requirements.txt`:

| Package | Purpose |
|---------|---------|
| Pillow | Image processing (convert, resize, compress) |
| pillow-heif | HEIC/HEIF read/write support for Pillow |
| pandas | Excel file reading/writing |
| openpyxl | Excel engine for pandas |
| requests | HTTP downloads |
| tqdm | Progress bars (disabled in GUI mode, only for CLI) |
| jinja2 | A very fast and expressive template engine |
| pillow-heif | Ability to convert to heif files |

## Troubleshooting

### Problem: GUI doesn't launch from source
**Solution:**
```bash
# Verify Python installation
python --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Run with verbose output
python -u gui.py
```

### Problem: Executable crashes on startup
**Solution:**
- Ensure Windows 7 or later (check with `winver`)
- Try running as Administrator
- Verify no other Multitool process running
- Check desktop for error logs

### Problem: Image conversion very slow
**Solution:**
- Disable compression (increases speed, larger files)
- Skip resizing if not needed
- Convert smaller batches
- Check disk space (output requires ~same size as input)

### Problem: Excel file not found
**Solution:**
- Ensure file path doesn't contain special characters
- Try using absolute paths (e.g., `C:\Users\...\file.xlsx`)
- Verify Excel file is not open in another program
- Try saving as .xlsx (not .xls if possible)

### Problem: Downloads fail with 404 errors
**Solution:**
- Verify URLs are valid and accessible
- Check internet connection
- Ensure URL column is correct in Excel
- Try with 1-2 test URLs first
- Check firewall rules


## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Image conversion fails
```bash
pip install --upgrade Pillow
```

### Excel files not recognized
- Ensure file is `.xlsx` format (not in use by another app).
- Verify column names match exactly (case-sensitive).

### Downloads failing
- Check internet connection.
- Verify URLs are valid and publicly accessible.

## Advanced Usage

### Command Line Arguments (From Source)
Currently, the GUI requires interactive dialogs. For automation, modify `gui.py` or create custom wrapper scripts using the individual tool modules.

### Custom Integration
Each tool module is independently importable:
```python
from count_files_by_extension import count_files_by_extension

# Use with custom logger
def my_logger(msg):
    print(f"[CUSTOM] {msg}")

count_files_by_extension("/path/to/folder", include_subfolders=True, logger=my_logger)
```

### Extending the Application
1. Create new tool module (import pattern from existing tools)
2. Add `logger=print` parameter support
3. Add button to `gui.py` with handler function
4. Rebuild executable with PyInstaller

## Performance Metrics

Tested on Windows 11, Intel i7-9700, 32GB RAM:

| Operation | Time (100 MB data) |
|-----------|------------------|
| File counting (10k files) | ~0.5 seconds |
| Image batch convert (50 MB → JPG) | ~2-3 seconds |
| File search (recursive) | ~1 second |
| Excel rename (1000 files) | ~0.5 seconds |
| Folder comparison | ~0.3 seconds |
| Image download (10 files @ 1 MB each) | ~3-5 seconds |

## Support

For issues, feature requests, or improvements:
1. Review the Troubleshooting section above.
2. Check file paths and permissions. (If you are using the CLI)
3. Ensure all dependencies are installed. (If you are using the CLI)
4. Try running from source to capture detailed error messages
5. Check the log output in the GUI for error messages.
6. Verify input files and paths are correct. (If you are using the CLI)
7. Ensure all dependencies are installed. (`pip install -r requirements.txt`).

## License

**This application is provided as-is for personal and commercial use.**

---

**Made with blood, sweat, and tears using Python, tkinter, and community libraries.**