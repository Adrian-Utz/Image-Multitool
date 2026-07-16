# Currently known issues:
- Program tends to crash if you try to quit a task while it is running.(Should be fixed now ✓ )
- Program crashes when you select more than one task.(Should be fixed now ✓ )
- Progress bar bugs out when trying to complete more than one task.(Should be fixed now ✓ )
- Dark mode inconsistancies.
- Search and Copy: If using a TXT file the task queue will show "Searching for None in "(Should be fixed now ✓ )

# Changelog:

## v1.0.0 
- Initial release with all core functionalities integrated into the GUI.

## v1.0.1 
- Added better error handling and logging for the Excel image downloader,
and improved the task queue display to show active and pending tasks more clearly. 
Also added a cancel button to allow users to cancel the currently running task.(Fixed in v1.1.3)

## v1.0.2 
- Updated the Excel image downloader to show available columns in the selected Excel file 
before prompting for column selection, and added support for selecting columns by index or name with more 
flexible input parsing. Also improved logging and error handling in the downloader tool.
Added the ignore_file_extension option to the Excel renaming tool to allow matching based on base name regardless of file extension,
providing more flexibility in handling different image formats.

## v1.0.3 
- Added a _safe_after() helper method to safely schedule Tkinter operations from any thread, 
preventing potential crashes or runtime errors if the main loop is not running.
Updated log(), stop(), start(), and _update_queue_display() to use _safe_after() for thread-safe UI updates, 
ensuring that log messages and queue display updates do not cause issues when called from background threads.

## v1.0.4 
- Added a "?" help button next to each tool in the left pane that shows a message box with the specific requirements 
for that tool when clicked.

## v1.0.5 
- Fixed a bug where the user couldn't select a .txt file for search terms in the Search & Copy tool when using the GUI, and added support for that in the search_files_gui function.
Added an easter egg triggered by the Konami code that shows a special CODEC transmission message.

## v1.0.6 
- Improved Codec quality.

## v1.0.7 
- Added the search function to the excel renaming tool. This makes it easier for the user to select the column they want. Method name: choose_column.

## v1.0.8 
- Added the ability to add subfolders in the image reformatting tool. Changes it so the program does not look into the output folder when reformatting.
This would cause the program to repeatedly reformat the same images over and over again, creating a huge mess of files. 
Now it ignores the output folder when looking for files to reformat, 
so it only reformats the original files once and saves them to the output folder without touching them again.
Added the same functionality to the excel renaming tool.

## v1.1.0
-Added functionality to the image reformatter. Allowing it to handle and edit .avif files.
Added the pillow_avif import to the hiddenimports in multitool.spec for the EXE.

## v1.1.1
- Changed the progress bar to show a percentage, and fill from left to right during job completion.
Fixed the renaming with excel to handle "0" at the begining of the file name. 

## v1.1.2
- Fixed the progress bar to run while the logger prints output in the list_files_by_extension.py program.

## v1.1.3
- Fixed the cancel task button so it no longer crashes, and cancels the current task properly.
Added a Light mode / Dark mode to make it easier on the eyes. Fixed some theme related issues.
Moved the Konami code easter egg to its own file.(The gui was 1000 lines long. I'm trying to cut it down a bit.)

## v1.1.4
- Fixed a potential bug. This line: print(f"Copied: {source_filename} -> {output_path}\{new_filename}") was using a single backslash which could cause issues on some systems. 
I changed it to this: print(f"Copied: {source_filename} -> {output_path}\\{new_filename}") could be seen as a invalid escape sequence. 
By using a double backslash, we ensure that it is treated as a literal backslash in the output string, which is important for correctly displaying file paths on Windows systems.
Added jinja2 to the requirements. 

## v1.2.0
- Changes the behavior of the image reformatter. Allowed the user to specify the allowed file size. Added the crop function. 
Added the ability to use MB during the compression stage for the image reformatter.

## v1.2.1
- Changed some of the Popups in the web_downloading section. Making it more user friendly.
Added the gui_helpers file to cut down on the main gui file size.

## v1.2.2
- Optimized the search_files_gui function to support searching multiple root folders in parallel using a thread pool, which can speed up searches across multiple directories.
Added the following to search_files: Pre-compiled patterns(Regex patterns are compiled once before the search, not once every filename check.). Batched into groups of 100. Early termination. _matches_any_pattern() function.
The biggest improvement is the perfromance.

## v1.2.3
- Added .heif and .heic support to the image reformatter. Added a total to the bottom of the count_files_by_extension program. Updated readme, fixed build commands. 
Fixed the task_name error in the gui. When searching for a file with a .txt file it now shows the file path.

## v1.2.4
- Fixed the queue system, it now functions as intended. You can now queue multiple actions at once and It will work through them one at a time.
This also fixed the progress bar problem. Fixed a crash that happened in the completion branch after the last queued task was finished. 
The old flow could still be updating queue/UI state in a way that re-entered the same task-lock/GUI update sequence while the final task was finishing, 
which can lead to a crash or inconsistent Tkinter state. 

## v1.2.5
- Moved the Options tab from the right side to a button just above the Exit button. Moved the color switcher to the options panel, and added a auto-start switch.
Added the start button to the top, next to the cancel button. (You can only see it if auto-start is switched to off.) Fixed a crash that happened to the folder_compare tool.
It assumed both selections were valid folders and called os.listdir() directly. 
Moved the color management to the options file. 
Updated the Cropping mechanic in the image reformatter so you can dynamically crop. You are no longer restricted to a square. 

## v1.2.6
- Added dpi changing to the image reformatter. Added a iteration function in the image reformatter. First release on GitHub.
