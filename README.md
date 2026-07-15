# Python Multitool

An all-in-one tool for bulk image re-formatting, file renaming, and file management.

## Features
- **Count Files by Extension** — Analyze file distribution in a folder with optional subfolder traversal.
- **List Filenames** — List and export files by extension with optional txt output.
- **Search & Copy** — Find files by name and optionally copy matches to a timestamped folder.
- **Image Reformat/Convert** — Batch convert images between formats (jpg, png, webp, tiff, bmp, avif, heic, heif) with optional resizing, compression, and PPI settings.
- **Excel Rename Tool** — Rename files based on Excel data mapping (e.g., match image file numbers to SKU names).
- **TXT ↔ Excel Compare** — Compare a text file against an Excel column to find matches and missing items.
- **Excel Image Downloader** — Download images from URLs listed in an Excel file with multi-threaded support.
- **Folder Comparison** — Compare two folders and find files that differ, with optional extension-ignore mode.

#### To run in commandline: run multitool.py
#### To run as a GUI: run gui.py

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
