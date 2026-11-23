import copy
import importlib
from dataclasses import dataclass
from typing import Any, Callable, Dict

"""
Workflow data model: task types, validation and tool resolution (no GUI).

Written by: AJ Utz
Written on: 11/18/2026
Latest Update: 11/18/2026
"""

@dataclass(frozen=True)
class Field:
    key: str
    label: str
    kind: str = "text"
    default: object = ""
    required: bool = False
    choices: tuple = ()

#Here are all task types with their associated variables
F = Field
TASK_TYPES = {
    "count_files": ("Count files by extension", (
        F("folder", "Folder", "folder", required=True),
        F("include_subfolders", "Include subfolders", "bool", False),
    )),
    "list_files": ("List filenames", (
        F("folder", "Folder", "folder", required=True),
        F("extensions", "Extensions (one per line)", "list", ("jpg",), True),
        F("include_subfolders", "Include subfolders", "bool", False),
        F("save_txt", "Save results to text file", "bool", False),
        F("txt_file", "Output filename", "text"),
    )),
    "search_files": ("Search & Copy", (
        F("folder", "Folder to search", "folder", required=True),
        F("search_terms", "Search terms (one per line)", "list", ()),
        F("txt_file", "Search terms file (optional)", "file"),
        F("include_subfolders", "Include subfolders", "bool", False),
        F("copy", "Copy matched files", "bool", False),
        F("parent_dest", "Copy destination", "folder"),
    )),
    "image_reformat": ("Image reformat", (
        F("input_folder", "Image folder", "folder", required=True),
        F("target_ext", "Target extension (e.g. .jpg)", default=".jpg", required=True),
        F("compress", "Compress to target size", "bool", False),
        F("max_size_kb", "Maximum size (KB)", "int", 100),
        F("resize", "Resize dimensions (WIDTHxHEIGHT, optional)", "dimensions", None),
        F("resize_mode", "Resize mode", "choice", "pad", choices=("pad", "crop")),
        F("ppi", "PPI (optional)", "optional_int", None),
        F("dpi", "DPI (optional)", "optional_int", None),
        F("preserve_transparency", "Preserve transparency", "bool", True),
        F("include", "Include subfolders", "bool", False),
    )),
    "image_optimize": ("Image optimize", (
        F("input_folder", "Image folder", "folder", required=True),
        F("max_colors", "Maximum colors (2-256)", "int", 256),
        F("method", "Color reduction method", "choice", "median_cut", choices=("median_cut", "octree", "none")),
        F("dither", "Dithering", "choice", "none", choices=("none", "floyd_steinberg", "ordered")),
        F("preserve_alpha", "Preserve transparency", "bool", True),
        F("strip_metadata_enabled", "Strip metadata", "bool", True),
        F("chroma_subsampling", "JPEG chroma subsampling", "optional_choice", None, choices=("4:4:4", "4:2:2", "4:2:0")),
        F("include_subfolders", "Include subfolders", "bool", True),
    )),
    "image_quality_grader": ("Image quality grader", (
        F("input_folder", "Image folder", "folder", required=True),
        F("include_subfolders", "Include subfolders", "bool", False),
        F("grading_mode", "Grading criteria", "choice", "both", choices=("both", "sharpness", "brightness")),
        F("model_path", "BRISQUE model file (optional)", "optional_file", None),
        F("range_path", "BRISQUE range file (optional)", "optional_file", None),
        F("reference_path", "Base image (optional)", "optional_file", None),
        F("use_similarity", "Use similarity grading", "bool", False),
        F("separation", "Separate images", "optional_choice", None, choices=("copy", "move")),
    )),
    "rename_excel": ("Excel rename", (
        F("excel_file", "Excel file", "file", required=True),
        F("image_col", "Image column name or zero-based index", "column", required=True),
        F("sku_col", "SKU column name or zero-based index", "column", required=True),
        F("folder_path", "Folder containing files", "folder", required=True),
        F("include", "Include subfolders", "bool", False),
        F("preserve_variants", "Preserve variants", "bool", False),
        F("ignore_file_extension", "Ignore file extensions", "bool", False),
        F("output_folder", "Output folder name", default="renamed_by_sku", required=True),
    )),
    "compare_txt_excel": ("TXT <-> Excel Compare", (
        F("txt_file", "Text file", "file", required=True),
        F("excel_file", "Excel file", "file", required=True),
        F("column", "Excel column name", required=True),
        F("save", "Save results", "bool", False),
    )),
    "download_excel": ("Excel image downloader", (
        F("file_name", "Excel file", "file", required=True),
        F("image_columns", "Image column names (one per line)", "list", (), True),
        F("rename_column", "Rename column name (optional)", "optional_text", None),
        F("output_folder", "Output folder", "folder", required=True),
        F("max_workers", "Download workers", "int", 20),
    )),
    "folder_compare": ("Folder compare", (
        F("folder1", "First folder", "folder", required=True),
        F("folder2", "Second folder", "folder", required=True),
        F("ignore_extensions", "Ignore extensions", "bool", False),
        F("save", "Save results", "bool", False),
        F("output_file", "Output filename", "optional_text", None),
    )),
    "backup_files": ("Backup files", (
        F("sources", "Source paths (one per line)", "paths", (), True),
        F("destination_root", "Destination folder", "folder", required=True),
        F("include_subfolders", "Include subfolders", "bool", False),
        F("fast_mode", "Fast mode (skip disk checks and metadata)", "bool", False),
    )),
}
#Used to associate a task type with a common name
TASK_HANDLERS = {
    "count_files": ("image_multitool.tools.files.count_files_by_extension", "count_files_by_extension"),
    "list_files": ("image_multitool.tools.files.list_files_by_extension", "list_files_by_extension_gui"),
    "search_files": ("image_multitool.tools.files.search_files", "search_files_gui"),
    "image_reformat": ("image_multitool.tools.images.image_reformatting", "batch_convert_in_folder"),
    "image_optimize": ("image_multitool.tools.images.image_optimization", "optimize_folder"),
    "image_quality_grader": ("image_multitool.tools.images.image_quality_grader", "grade_folder"),
    "rename_excel": ("image_multitool.tools.excel.rename_wt_excel", "rename_from_excel_gui"),
    "compare_txt_excel": ("image_multitool.tools.excel.compare_txt_to_excel", "run_txt_excel_compare_gui"),
    "download_excel": ("image_multitool.tools.excel.web_downloading", "download_from_excel"),
    "folder_compare": ("image_multitool.tools.folders.folder_compare", "run_folder_compare_gui"),
    "backup_files": ("image_multitool.tools.files.create_backup", "create_backup"),
}


@dataclass
class PreparedTask:
    #Class to hold the fuction, taskname, and keyword args
    func: Callable[..., Any]
    task_name: str
    kwargs: Dict[str, Any]


def new_workflow():
    #Function to create a new workflow dictionary
    return {"version": 1, "name": "", "tasks": []}


def validate_task(task):
    """Function to validate a single task dictionary"""
    #Check if the task if a dictionary with the correct keys
    if not isinstance(task, dict) or set(task) != {"type", "settings"}:
        raise ValueError("A task must contain a type and settings.")
    #Get the task type and validate ir
    task_type = task["type"]
    if not isinstance(task_type, str) or task_type not in TASK_TYPES:
        raise ValueError(f"Unknown task type: {task_type!r}")
    #Get the settings and validate their keys
    settings = task["settings"]
    fields = TASK_TYPES[task_type][1]
    if not isinstance(settings, dict) or set(settings) != {f.key for f in fields}:
        raise ValueError(f"Invalid settings for {TASK_TYPES[task_type][0]}.")
    #Validate each setting
    for field in fields:
        value = settings[field.key]
        kind = field.kind
        if kind == "bool":
            valid = isinstance(value, bool)
        elif kind in ("int", "optional_int"):
            valid = (value is None and kind == "optional_int") or (type(value) is int and value > 0)
        elif kind in ("list", "paths"):
            valid = isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)
        elif kind == "dimensions":
            valid = value is None or (isinstance(value, list) and len(value) == 2 and
                                      all(type(item) is int and item > 0 for item in value))
        elif kind in ("choice", "optional_choice"):
            valid = value in field.choices or (value is None and kind == "optional_choice")
        elif kind == "column":
            valid = (isinstance(value, str) and bool(value.strip())) or (type(value) is int and value >= 0)
        elif kind in ("optional_text", "optional_file"):
            valid = value is None or (isinstance(value, str) and bool(value.strip()))
        else:
            valid = isinstance(value, str)
        #check if the value is missing or invalid
        missing = not value or (isinstance(value, str) and not value.strip())
        if not valid or (field.required and missing and not (kind == "column" and value == 0)):
            raise ValueError(f"{field.label}: enter a valid value.")
    #Additional validation for specific task types
    if task_type == "image_optimize" and not 2 <= settings["max_colors"] <= 256:
        raise ValueError("Maximum colors must be between 2 and 256.")
    if task_type == "image_reformat" and not settings["target_ext"].startswith("."):
        raise ValueError("Target extension must start with a dot, for example .jpg.")
    if task_type == "list_files" and settings["save_txt"] and not settings["txt_file"].strip():
        raise ValueError("Enter an output filename when saving the file list.")
    if task_type == "search_files":
        if not settings["search_terms"] and not settings["txt_file"].strip():
            raise ValueError("Enter search terms or select a search terms file.")
        if settings["copy"] and not settings["parent_dest"].strip():
            raise ValueError("Select a copy destination.")
    if task_type == "image_quality_grader":
        if bool(settings["model_path"]) != bool(settings["range_path"]):
            raise ValueError("BRISQUE requires both model and range files.")
        if settings["use_similarity"] and not settings["reference_path"]:
            raise ValueError("Similarity grading requires a base image.")
    if task_type == "folder_compare" and settings["save"] and not settings["output_file"]:
        raise ValueError("Enter an output filename when saving the comparison.")


def validate_workflow(workflow):
    """Validate the entire workflow dictionary"""
    #Check if the workflow is a dictionary with the correct keys
    if not isinstance(workflow, dict) or set(workflow) != {"version", "name", "tasks"}:
        raise ValueError("Invalid workflow format.")
    #Validate the version number
    if type(workflow["version"]) is not int or workflow["version"] != 1:
        raise ValueError("Unsupported workflow version.")
    #Validate the workflow name
    if not isinstance(workflow["name"], str) or not workflow["name"].strip():
        raise ValueError("Enter a workflow name.")
    #Validate the task list
    if not isinstance(workflow["tasks"], list):
        raise ValueError("Workflow tasks must be a list.")
    #validate each task in the list
    for index, task in enumerate(workflow["tasks"], 1):
        try:
            validate_task(task)
        except ValueError as exc:
            raise ValueError(f"Task {index}: {exc}") from exc


def prepare_workflow_tasks(workflow):
    """Resolve tasks without running them; the caller supplies runtime callbacks."""
    #Validate the workflow before preparing tasks
    validate_workflow(workflow)
    #Init a list to hold prepared tasks
    prepared = []
    #Iterate over each task in the workflow
    for index, task in enumerate(workflow["tasks"], 1):
        task_type = task["type"]
        #Get the module and function anems for the task type
        try:
            module_name, function_name = TASK_HANDLERS[task_type]
        except KeyError as exc:
            raise RuntimeError(f"Task {index} ({TASK_TYPES[task_type][0]}): no tool mapping.") from exc
        #Try to import and get the task function
        try:
            func = getattr(importlib.import_module(module_name), function_name)
        except (ImportError, AttributeError, OSError) as exc:
            raise RuntimeError(f"Task {index} ({TASK_TYPES[task_type][0]}): cannot load tool: {exc}") from exc
        #check if the function is callable
        if not callable(func):
            raise RuntimeError(f"Task {index} ({TASK_TYPES[task_type][0]}): tool is not callable.")
        #Deep copy the task settings to avoid modifying the og
        kwargs = copy.deepcopy(task["settings"])
        #Handle specific task types
        if task_type == "image_reformat" and kwargs["resize"] is not None:
            kwargs["resize"] = tuple(kwargs["resize"])
        if task_type == "download_excel":
            kwargs["use_tqdm"] = False
        #Prepare the task by creating a Prepared Task object
        prepared.append(PreparedTask(func, TASK_TYPES[task_type][0], kwargs))
    #return a list of prepaired tasks
    return prepared
