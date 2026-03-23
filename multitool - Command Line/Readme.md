Written By: Adrian Utz on: 3/19/2026

GUI design (concise)

Approach: Use tkinter (already imported in multitool.py) for a lightweight cross-platform app.

Window: single main window with menu bar (File, Settings, Help).

Navigation: left vertical pane with buttons for each tool:

Count files
List filenames
Search & Copy
Image reformat/convert
Excel Renaming
TXT↔Excel Compare
Excel Image Downloader
Folder Compare
Exit
Main area:

Top: tool-specific options panel (dynamic: changes per tool).
Center: scrollable log/output Text widget for status and results.
Right (optional): small preview or parameters summary.
Bottom:

ttk.Progressbar (indeterminate and determinate modes).
Run / Cancel buttons.
Execution & Responsiveness:

Run tasks in background using concurrent.futures.ThreadPoolExecutor (or threading.Thread) to avoid UI freeze.
Provide callbacks to append progress/log lines to the Text widget via tkinter thread-safe queue + after().
File dialogs & inputs:

Use filedialog.askdirectory, askopenfilename, askopenfilenames for selecting folders/files.
For operations needing extra inputs (columns, extensions, ignore ext), show small popups or expand the options panel.
Integration notes:

Keep current modules (count_files_by_extension, etc.) and call their functions from the GUI.
Prefer small refactors so functions accept optional path argument and an optional logger/progress_callback.
If a function prints to stdout, route prints to the GUI log by temporarily redirecting sys.stdout or by wrapping functions to capture output.
Persistence & Extras:

Save last-used folders and simple settings in config.json in the app folder.
Add Help → Short usage docs and "Open log folder" option.