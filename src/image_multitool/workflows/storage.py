import filecmp
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

from image_multitool.workflows.models import validate_workflow

"""
Workflow persistence: locate, load and atomically save workflow JSON files.

Written by: AJ Utz
Written on: 11/18/2026
Latest Update: 11/18/2026
"""

def load_workflow(path):
    """Load the workflow file in reading mode with UTF-8 encoding,
    Validate the workflow and return it"""
    with open(path, "r", encoding="utf-8") as file:
        workflow = json.load(file)
    validate_workflow(workflow)
    return workflow


def workflow_directory():
    #Determine the base dir for storing workflows
    if os.name == "nt":
        # Use the LOCALAPPDATA environment variable or the AppData/Local dirs on windows
        base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    else:
        # Use the XDG_DATA_HOME environment variable or the .local/share dirs on Unix
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "ImageMultitool", "workflows") #Return the dir


def _legacy_workflow_directory():
    #Determine the base dir for storing legacy workflows
    if getattr(sys, "frozen", False):
        # use the dir of the executable if it's frozen
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        #use the parent dir of the current script if it is not frozen
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    #Return the dir
    return os.path.join(base, "WKF_JSON")


def migrate_legacy_workflows():
    """Copy the old library once per location, leaving its files untouched."""
    legacy = _legacy_workflow_directory() #Get Dir of legacy workflow
    directory = workflow_directory() #Get the dir where current workflows are stored
    identity = os.path.normcase(os.path.realpath(legacy)).encode("utf-8") #Normalize the case and resolve the real path of the legacy dir
    marker = os.path.join(directory, ".migrated-" + hashlib.sha256(identity).hexdigest()) # Create a marker file to track migration
    #Check if migration is complete
    if os.path.exists(marker):
        return
    try:
        #Scan the legacy dir for JSON files
        with os.scandir(legacy) as entries:
            paths = [entry.path for entry in entries
                     if entry.is_file() and entry.name.lower().endswith(".json")]
    except FileNotFoundError:
        #No JSON files found
        return
    #Create the current dir if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    #copy each legacy workflow to the current dir
    for source in sorted(paths):
        name, extension = os.path.splitext(os.path.basename(source))
        for number in range(1, 10001):
            suffix = "" if number == 1 else f" ({number})"
            destination = os.path.join(directory, f"{name}{suffix}{extension}")
            try:
                #Create a temp file to avoid file access conflicts
                target = open(destination, "xb")
            except FileExistsError:
                #Check if the destination file already exists and is a copy of the source
                if filecmp.cmp(source, destination, shallow=False):
                    break
                continue
            try:
                #Copy the content formt he source to the destination
                with target, open(source, "rb") as original:
                    shutil.copyfileobj(original, target)
            except (OSError, ValueError):
                # IF an error occures, remov the temporary file and raise an erroe
                os.remove(destination)
                raise
            break
        else:
            #If no valid desitnation is found raise an error
            raise OSError(f"Could not find an available filename for {source}")
    #Write a marker file to indicate successful migration
    with open(marker, "a", encoding="utf-8"):
        pass


def _is_managed_workflow(path):
    """Compare the parent dir with the given workflow dir"""
    directory = os.path.normcase(os.path.realpath(workflow_directory()))
    parent = os.path.normcase(os.path.dirname(os.path.realpath(path)))
    return parent == directory


def _reserve_workflow_path(name):
    # Reserve a workflow path for a given name
    directory = workflow_directory()
    os.makedirs(directory, exist_ok=True)
    #Generate a safe name for the workflow
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")[:100].rstrip(" .")
    #If the stem is empty, use "workflow"
    if not stem:
        stem = "workflow"
    # Reserved names for common devices
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update(f"COM{number}" for number in range(1, 10))
    reserved.update(f"LPT{number}" for number in range(1, 10))
    #Ensure the stem does not conflict with reserved names
    if stem.split(".", 1)[0].upper() in reserved:
        stem = "_" + stem
    #Find a unique filename
    for number in range(1, 10001):
        suffix = "" if number == 1 else f" ({number})"
        path = os.path.join(directory, f"{stem}{suffix}.json")
        try:
            #Create the file if it doesn't exist
            with open(path, "x", encoding="utf-8"):
                pass
        except FileExistsError:
            continue
        return path
    #Raise an error if no unique filename is found
    raise OSError("Could not find an available workflow filename.")


def save_workflow(path, workflow):
    #Validate the workflow to ensuer it is in the correct format
    validate_workflow(workflow)
    #Get the dir of the specified path
    directory = os.path.dirname(os.path.abspath(path))
    #init a var to store the temp file path
    temporary_path = None
    try:
        #Create a temp file in the speciied dir with given prefix, suffix, and mode
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                         prefix=".multitool-workflow-", suffix=".tmp",
                                         delete=False) as file:
            #Store the temp file's path
            temporary_path = file.name
            #Dump the workflow JSON to the temp file with pretty formatting and ensure ASCII encoding 
            json.dump(workflow, file, indent=2, ensure_ascii=False)
            #newline char
            file.write("\n")
        #Replace the original file with the contents of the temporary file
        os.replace(temporary_path, path)
    finally:
        # If a temp file path is set and it exists, remove it
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
