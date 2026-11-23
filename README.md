# Multitool GUI

A comprehensive file management and processing application with a modern, responsive GUI. Convert images, rename files using Excel data, search and copy files, download images from URLs, compare folders, and more—all with real-time progress tracking and background threading.

**Version:** 1.3.6  
**Last Updated:** 11/17/2026  
**Status:** ✓ Production Ready

## Features

### Core Tools
- **Count Files by Extension** — Analyze file distribution in a folder with optional subfolder traversal.
- **List Filenames** — List and export files by extension with optional txt output.
- **Search & Copy** — Find files by name and optionally copy matches to a timestamped folder.
- **Image Reformat/Convert** — Batch convert images between formats (jpg, png, webp, tiff, bmp, avif, heic, heif) with optional resizing, compression, and PPI settings.
- **Image Optimization** — Batch optimize images to improve their size. Useful for websites.
- **Image Quality Grader** — Grade images in a folder by sharpness and exposure, with optional BRISQUE distortion scoring.
- **Excel Rename Tool** — Rename files based on Excel data mapping (e.g., match image file numbers to SKU names).
- **TXT ↔ Excel Compare** — Compare a text file against an Excel column to find matches and missing items.
- **Excel Image Downloader** — Download images from URLs listed in an Excel file with multi-threaded support.
- **Folder Comparison** — Compare two folders and find files that differ, with optional extension-ignore mode.
- **File Backup** — Backup your files from multiple folder locations all at once.

### Advanced Features
- ✓ **Background Threading** — All tools run asynchronously; UI stays responsive during long operations
- ✓ **Real-time Logging** — Watch results stream live in the GUI log area
- ✓ **Task Queue Display** — Monitor active and pending tasks with visual indicators (fixed in v1.2.4)
- ✓ **Workflow Editor** — Save, edit, and queue ordered collections of configured tasks.
- ✓ **Resizable Task Queue and Log** — Drag the divider between queue and log to adjust size dynamically (new in v1.0.1)
- ✓ **Progress Tracking** — Visual progress bar and status updates for each operation
- ✓ **Cancel Operations** — Stop long-running tasks with a single click (fixed in v1.1.3)
- ✓ **Thread-Safe Output** — Proper synchronization prevents log corruption
- ✓ **Light/Dark Mode** — User can change their background to be easier on the eyes (new in v1.1.3)
- ✓ **EXE Version Checking** — Around once a week the exe version will check the github repo for the latest version (new in v1.2.8)

## Installation

### Option 1: Run from Source Code (Requires Python)

#### Prerequisites
- Python 3.8 or later
- pip (Python package manager)

#### Setup
1. **Create and activate the venv:**
   ```bash
   python3 -m venv .venv #Linux
   python -m venv .venv #Windows
   ```
   ```bash
   source .venv/bin/activate #Linux
   .venv\Scripts\Activate.ps1 #Windows
   ```

2. **Install the project and its dependencies:**
   ```bash
   python -m pip install -e .
   ```

### Option 2: Use Standalone Executable (Recommended)

No Python installation required!

1. **Download or build:**
   - Pre-built: Download [Multitool.exe](https://github.com/Adrian-Utz/Image-Multitool/releases) from the release list. (114 MB)
   - Double-click to run

2. **That's it!** The GUI will launch with all dependencies bundled.

## Usage

### Dependencies

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
| numpy | Image quality metric calculations |
| opencv-contrib-python-headless | Image decoding, sharpness, and optional BRISQUE scoring |

### Launching the Application

**Run From Source Code:**

1. Open a terminal in the project root (the folder containing `requirements.txt`).
2. Activate the virtual environment if you created one:
   ```powershell
   source .venv/bin/activate
   .venv\Scripts\Activate.ps1
   ```
3. If you have not installed the project yet, install it and its dependencies:
   ```bash
   python -m pip install -e .
   ```
4. Start the GUI:
   ```bash
   python -m image_multitool
   ```
   To start the command-line interface instead, run:
   ```bash
   python -m image_multitool --cli
   ```

You can also open the project folder in VS Code and run these commands from the
integrated terminal, using the same Python environment where you installed the project.

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
.\.venv\Scripts\python.exe -m PyInstaller .\packaging\multitool.spec
```

**Output:**
- `dist/Multitool.exe` — Standalone executable
- `build/` — Intermediate build files (safe to delete)
- `multitool.spec` — PyInstaller configuration file

**File Size:** ~114 MB (includes Python interpreter + all dependencies)

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
│  • List files           │  ├─ Cancel Current / Pending     │
│  • Search & Copy        │  └─ (Optional)Start Button       │
│  • Image Reformat       │                                  │
│  • Image Optimization   │                                  │
│  • Image quality grader │                                  │
│  • Excel Rename         │                                  │
│  • TXT ↔ Excel          │                                  │
│  • Image Downloader     │  Active Tasks Queue              │
│  • Folder Compare       │  ├─ Running tasks                │
│  • Backup Files         │  └─ Pending tasks                │
│                         │                                  │
│  [Workflows]            │                                  │
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
4. Choose options: compression, resizing, PPI, DPI, subfolders included
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

### Image Quality Grader
Choose **Image quality grader** in the GUI or option 6 in the CLI, select a folder, and choose whether to include subfolders. Reports appear in the GUI log or terminal. The tool scans BMP, JPEG, JPEG 2000, PNG, WebP, TIFF, AVIF, and GIF extensions; actual decoding support depends on the installed OpenCV build. Unreadable files are reported and skipped.

At the end, grade totals show how many images received each grade (A through F), including zero counts. Failed images are excluded; an image still counts if grading succeeded but copying or moving failed. If cancelled, the totals cover images graded before cancellation.

Choose whether the quality grade uses **both** sharpness and brightness (the default), **sharpness** alone, or **brightness** alone. Both metrics are shown; the unused one is informational. These heuristic thresholds assign each selected metric a grade, and the lowest grade wins:

| Grade | Sharpness (Laplacian variance) | Mean brightness |
|---|---|---|
| A | >500 | 40–215 |
| B | >250–500 | 30–<40 or >215–225 |
| C | >100–250 | 20–<30 or >225–235 |
| D | >50–100 | 10–<20 or >235–245 |
| E | >20–50 | 5–<10 or >245–250 |
| F | ≤20 | <5 or >250 |

If BRISQUE is enabled, a score of 30 or more caps an otherwise A quality grade at B; when similarity grading is enabled, it can also lower the final grade. Grade folders and totals use the final grade.

Optionally choose to copy or move all successfully graded images into folders named for their grades. Each run creates a uniquely named sibling folder beside the selected folder and logs its location; the original subfolder structure is retained inside each grade folder. Copies leave the source images in place; moves remove each original only after its copy succeeds. Failed or cancelled operations may leave a partially populated output folder. Choose **none** to leave all images in place.

Optionally select a base image to compare metrics. Each report shows image-minus-base differences for sharpness variance, mean brightness, and BRISQUE when enabled. By default, this comparison does not change grades. The base is evaluated before the batch; if it is in the selected folder, it is also processed normally, including copying or moving when selected. An unreadable base stops the operation before images are separated.

With a base image selected, you may also enable visual similarity grading. OpenCV SSIM compares grayscale images: similarity grades are A for scores of at least 0.95, B at least 0.85, C at least 0.70, D at least 0.50, E at least 0.25, and F otherwise. The final grade is the lower of the quality grade and the similarity grade; reports show both. Images must have the same dimensions as the base or they fail grading and are not copied or moved. SSIM is most meaningful for aligned images of the same subject and does not assess color similarity.

BRISQUE is optional. To enable it, supply compatible OpenCV BRISQUE model and range YAML files when prompted; these files are not included. Without them the grade uses sharpness and exposure only. Scores and grades are heuristics, not guarantees of visual or professional quality. OpenCV reads color images with transparency discarded; animated and multi-page files are graded using their first decoded frame.

### Creating a Saved Workflow
1. Click **Workflows**, enter a name, and choose **Add** to configure tasks.
2. Select a task to edit or remove it, or use **Move up** and **Move down** to change the order.
3. Choose **Save** to store the JSON file in your application data folder. Saved workflows appear in the list on the left. Select one and choose **Open Selected** to edit it or **Queue Selected** to add its saved contents to the queue. Use **Refresh** to find files added outside the application.
4. Use **Import...** to open a workflow from another location, **Duplicate** to save a separate copy, or **Delete** to delete the currently open saved file.

5. Choose **Add to Queue** to append the current editor tasks after any already pending tasks. This uses the current settings, including unsaved edits, without changing the saved file. **Queue Selected** instead uses the selected saved file and leaves the editor unchanged.
6. If auto-start is enabled, the queue starts automatically. Otherwise, use **Start Queue** when the queue is idle; a queue already running will continue processing its pending tasks.

The entire workflow is validated before tasks are added. Paths and task settings are stored in the JSON file. Paths do not need to exist when editing or adding to the queue, so a later task can refer to an earlier task's output.

Workflow tasks use the normal sequential queue, progress display, and log. **Cancel Current** requests cancellation of the running task; **Cancel Pending...** removes a selected pending task. Other queued tasks continue afterward. Cancelling does not undo work already performed or modify the saved workflow.

Workflow files contain a format version, a name, and an ordered array of task types and settings. For example:

```json
{
  "version": 1,
  "name": "Count images",
  "tasks": [
    {
      "type": "count_files",
      "settings": {
        "folder": "C:\\Images",
        "include_subfolders": true
      }
    }
  ]
}
```

On Windows, workflows are stored in `%LOCALAPPDATA%\ImageMultitool\workflows`; on other systems, they are stored under `$XDG_DATA_HOME/ImageMultitool/workflows` (defaulting to `~/.local/share/ImageMultitool/workflows`). The folder is created on first save. When the workflow editor opens, existing JSON files in the old `WKF_JSON` folder (in the source project root or beside the executable) are copied once to the new location; the originals are left untouched. Conflicting filenames receive a numbered suffix. You can import workflows from another location; saving creates a copy in the application data folder without changing the original. Workflow files contain paths and other settings in plain text, so share them only when those details are appropriate to share.

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
3. Click **Cancel Pending...** and select a queued task to remove it before it starts
4. Other pending tasks remain in queue

### Threading Safety
- All background work isolated from GUI thread
- Logging synchronized to prevent corruption
- UI remains responsive even during heavy operations
- Thread pool limited to 4 workers (prevents system overload)

## File Structure

```
Image-Multitool/
├── assets/
│   └── codec.wav
├── packaging/
│   └── multitool.spec
├── src/
│   └── image_multitool/
│       ├── core/
│       │   ├── __init__.py
│       │   ├── helpers.py
│       │   ├── settings.py
│       │   └── task_queue.py
│       ├── gui/
│       │   ├── workflows/
│       │   │   ├── __init__.py
│       │   │   ├── editor.py
│       │   │   └── task_dialog.py
│       │   ├── __init__.py
│       │   ├── dialogs.py
│       │   ├── konami.py
│       │   ├── main_window.py
│       │   ├── options_window.py
│       │   └── queue_panel.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── updates.py
│       ├── tools/
│       │   ├── excel/
│       │   │   ├── __init__.py
│       │   │   ├── compare_txt_to_excel.py
│       │   │   ├── rename_wt_excel.py
│       │   │   └── web_downloading.py
│       │   ├── files/
│       │   │   ├── __init__.py
│       │   │   ├── count_files_by_extension.py
│       │   │   ├── creat_backup.py
│       │   │   ├── list_files_by_extension.py
│       │   │   └── search_files.py
│       │   ├── folders/
│       │   │   ├── __init__.py
│       │   │   └── folder_compare.py
│       │   ├── images/
│       │   │   ├── __init__.py
│       │   │   ├── image_optimization.py
│       │   │   ├── image_quality_grader.py
│       │   │   └── image_reformatting.py
│       ├── workflows/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── storage.py
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── cli.py
│       └── version.py
├── .gitignore
├── changelog.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements.txt
```


## Troubleshooting

### Problem: GUI doesn't launch from source
**Solution:**
```bash
# Verify Python installation
python --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Run with verbose output
python -m image_multitool
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

## Advanced Usage

### Command Line Arguments (From Source)
Currently, the GUI requires interactive dialogs. For automation, modify `gui.py` or create custom wrapper scripts using the individual tool modules.

### Custom Integration
Each tool module should be independently importable:
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

| Operation | Time (100 MB data unless told otherwise) |
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
**I take no resposibility on what you decide what to use this program for.**

---

**Made with blood, sweat, and tears using Python, tkinter, and community libraries.**