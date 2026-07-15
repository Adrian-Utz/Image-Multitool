import os
import io
from PIL import Image, ImageCms
try:
    import pillow_avif# noqa: F401
except ImportError:
    pass  # AVIF  support requires pillow-avif-plugin 

HEIF_SUPPORT_AVAILABLE = False
HEIF_SUPPORT_ERROR = None
try:
    import pillow_heif# noqa: F401
    try:
        from pillow_heif import HeifImagePlugin  # noqa: F401
    except Exception:
        pass
    try:
        pillow_heif.register_heif_opener()
        HEIF_SUPPORT_AVAILABLE = True
    except Exception as exc:
        HEIF_SUPPORT_ERROR = exc
        try:
            if hasattr(pillow_heif, 'HeifImagePlugin'):
                HEIF_SUPPORT_AVAILABLE = True
        except Exception:
            pass
except ImportError as exc:
    HEIF_SUPPORT_ERROR = exc
except Exception as exc:
    HEIF_SUPPORT_ERROR = exc

# Map common extensions to Pillow format names (for Image.save)
EXT_TO_FORMAT = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".bmp": "BMP",
    ".gif": "GIF",
    ".tiff": "TIFF",
    ".tif": "TIFF",
    ".webp": "WEBP",
    ".avif": "AVIF",
    ".heic": "HEIF",
    ".heif": "HEIF",
}

#Hello! The main purpose of this program is to convert images to your desired format. Make sure you have Pillow installed on your machine before you run.

#To check if you have installed Pillow go to Command Prompt and put this command in: python -c "from PIL import Image; print(Image.__version__)"
#If it returns a version number you have Pillow installed.

#If you haven't installed Pillow run this in Command Prompt.
#Type this: python -m pip install Pillow

#Change Log: Split the file into 2 defs for optimization. Added file compression to the conversion script.
#Added a if statement to check if the user wants compression.
#Fixed a bug where the compression function wasn't activating because compress wasn't being passed to convert_image
#Added Image resising feature, changed it so it pads the image instead of warping it
#Converted .tif files were getting a green tint when they were converted. Added the if statement to check for CMYK format to fix this.
#Added the ability to change the ppi of a picture.
#Avif Support added.
#Added cancellation support.
#Added Crop mode for resizing.
#Added DPI support for screen resolution.

#Last updated: 7/13/2026
#Written by: AJ Utz on 12/18/2025

def convert_image(input_path, output_path, target_ext, compress=False, max_size_kb=100, resize=None, resize_mode="pad", ppi=None, dpi=None, logger=print, progress_callback=None, cancel_event=None):
    try:
        input_ext = os.path.splitext(input_path)[1].lower()
        if input_ext in (".heic", ".heif") and not HEIF_SUPPORT_AVAILABLE:
            logger(
                f"[ERROR] HEIF support unavailable: {HEIF_SUPPORT_ERROR or 'pillow-heif is not available or not bundled into the EXE'}"
            )
            return

        with Image.open(input_path) as img:
            if cancel_event and cancel_event.is_set():
                logger(f"[INFO] Conversion cancelled: {os.path.basename(input_path)}")
                return

            input_ext = os.path.splitext(input_path)[1].lower()
            if input_ext in (".heic", ".heif") and not HEIF_SUPPORT_AVAILABLE:
                logger(
                    f"[ERROR] HEIF support unavailable: {HEIF_SUPPORT_ERROR or 'pillow-heif not installed or not bundled in the EXE'}"
                )
                return

            #1. Detect transparency early
            has_alpha = (
                img.mode in ("RGBA", "LA") or
                (img.mode == "P" and "transparency" in img.info)
            )

            #2. Color management (CMYK → sRGB)
            if img.mode == "CMYK":
                if "icc_profile" in img.info:
                    try:
                        srgb = ImageCms.createProfile("sRGB")
                        cmyk = ImageCms.getOpenProfile(
                            io.BytesIO(img.info["icc_profile"])
                        )
                        img = ImageCms.profileToProfile(
                            img,
                            cmyk,
                            srgb,
                            outputMode="RGBA" if has_alpha else "RGB",
                            renderingIntent=0
                        )
                    except Exception as e:
                        logger(f"ICC conversion failed, falling back: {e}")
                        img = img.convert("RGBA" if has_alpha else "RGB")
                else:
                    img = img.convert("RGBA" if has_alpha else "RGB")

            #3. Normalize modes safely
            if has_alpha and img.mode not in ("RGBA", "LA"):
                img = img.convert("RGBA")
            elif not has_alpha and img.mode != "RGB":
                img = img.convert("RGB")

            #4. Resize / pad / crop (alpha-safe)
            if resize:
                target_w, target_h = resize
                orig_w, orig_h = img.size

                if resize_mode == "crop":
                    img = resize_to_fill_with_crop(img, resize)
                else:
                    #Explanation of the if statement:
                    #If the original width to height ratio is different than the target width to height ratio,
                    #pad the image to fit the target dimensions instead of warping the image. Prevents distortion.
                    if orig_w * target_h != orig_h * target_w:
                        img = resize_to_square_with_padding(img, resize)
                    else:
                        img = img.resize(resize, Image.LANCZOS)

            #5. Flatten ONLY if needed (to preserve quality when possible)
            if has_alpha and target_ext in (".jpg", ".jpeg"):
                img = flatten_transparency(img)
                has_alpha = False  #Alpha is now gone

            #6. Save (with compression loop)
            if not compress:
                if cancel_event and cancel_event.is_set():
                    logger(f"[INFO] Conversion cancelled: {os.path.basename(input_path)}")
                    return
                save_kwargs = {}
                dpi_value = dpi if dpi is not None else ppi
                if dpi_value:
                    save_kwargs["dpi"] = (dpi_value, dpi_value)

                format_name = EXT_TO_FORMAT.get(target_ext.lower())
                if format_name:
                    save_kwargs["format"] = format_name

                img.save(output_path, **save_kwargs)

                size_kb = os.path.getsize(output_path) / 1024
                logger(f"Converted: {os.path.basename(input_path)} -> {os.path.basename(output_path)} ({size_kb:.1f} KB)")
                return

            quality = 95
            temp_path = output_path

            #While Loop Explanation:
            #When compress is enabled, the program will save the image with the current quality setting, check the file size, and if it's still above the max_size_kb,
            #it will reduce the quality by 5 and try again. This loop continues until the file size is below the target or the quality drops to 10,
            #which is a reasonable lower limit for quality.
            while True:
                if cancel_event and cancel_event.is_set():
                    logger(f"[INFO] Conversion cancelled: {os.path.basename(input_path)}")
                    return
                save_kwargs = {}
                dpi_value = dpi if dpi is not None else ppi
                if dpi_value:
                    save_kwargs["dpi"] = (dpi_value, dpi_value)

                format_name = EXT_TO_FORMAT.get(target_ext.lower())

                # Use quality parameter for formats that accept lossy quality settings
                if target_ext in (".jpg", ".jpeg", ".webp", ".heic", ".heif", ".avif"):
                    if format_name:
                        img.save(temp_path, quality=quality, format=format_name, **save_kwargs)
                    else:
                        img.save(temp_path, quality=quality, **save_kwargs)
                else:
                    if format_name:
                        img.save(temp_path, format=format_name, **save_kwargs)
                    else:
                        img.save(temp_path, **save_kwargs)


                size_kb = os.path.getsize(temp_path) / 1024
                if size_kb <= max_size_kb or quality <= 10:
                    break

                quality -= 5

            logger(
                f"Converted: {os.path.basename(input_path)} -> {os.path.basename(output_path)} "
                f"({size_kb:.1f} KB, quality={quality})"
            )

    except Exception as e:
        print(f"\033[91m[ERROR] Could not convert {os.path.basename(input_path)}: {e}\033[0m")


def resize_to_square_with_padding(img, target_size, bg_color=(255, 255, 255)):
    target_w, target_h = target_size
    original_w, original_h = img.size

    scale = min(target_w / original_w, target_h / original_h)
    new_w = int(original_w * scale)
    new_h = int(original_h * scale)
    
    img = img.resize((new_w, new_h), Image.LANCZOS)

    #Create background
    if img.mode == "RGBA":
        square_image = Image.new("RGBA", (target_w, target_h), bg_color + (255,))
        square_image.paste(img, ((target_w - new_w) // 2, (target_h - new_h) // 2), mask=img)
    else:
        square_image = Image.new("RGB", (target_w, target_h), bg_color)
        square_image.paste(img, ((target_w - new_w) // 2, (target_h - new_h) // 2))

    return square_image


def resize_to_fill_with_crop(img, target_size):
    target_w, target_h = target_size
    original_w, original_h = img.size

    scale = max(target_w / original_w, target_h / original_h)
    new_w = int(original_w * scale)
    new_h = int(original_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    return img.crop((left, top, right, bottom))


def flatten_transparency(img, bg_color=(255, 255, 255)):
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        background = Image.new("RGB", img.size, bg_color)
        alpha = img.convert("RGBA").split()[-1]  #Extract alpha
        background.paste(img, mask=alpha)
        return background
    return img


#Wrapper function to allow calling from external programs
def run_image_reformatter():
    main()


def main():

    print("What file type do you want to convert your images to? (jpg, png, webp, tiff, bmp, avif, heic, heif)")
    target_ext = input("Enter file type (without dot): ").lower().strip()
    if not target_ext.startswith("."):
        target_ext = "." + target_ext

    print("Would you like to compress images to a target size? (y/n)")
    kb_ask = input("Enter y or n: ").lower().strip()
    compress = (kb_ask == "y")
    kb_limit = 100
    if compress:
        kb_limit_input = input("Enter maximum file size (e.g., 100KB or 1MB): ").strip().upper()
        try:
            if kb_limit_input.endswith("MB"):
                mb_value = float(kb_limit_input[:-2].strip())
                kb_limit = int(mb_value * 1024)
            elif kb_limit_input.endswith("KB"):
                kb_limit = int(kb_limit_input[:-2].strip())
            else:
                kb_limit = int(kb_limit_input)
        except ValueError:
            print("Invalid input, using default 100 KB.")
            kb_limit = 100

    print("Do you want to resize the images to specific dimensions? (y/n)")
    resize_ask = input().lower().strip()
    resize_dims = None
    resize_mode = "pad"
    if resize_ask == "y":
        width = int(input("Enter new Width (px): "))
        height = int(input("Enter new Height (px): "))
        resize_dims = (width, height)
        resize_mode = input("How should the image fit the new size? Pad or crop (pad/crop): ").lower().strip()
        if resize_mode not in ("pad", "crop"):
            print("Invalid mode selected, defaulting to pad.")
            resize_mode = "pad"

    print("Do you want to set a custom PPI (print resolution)? (y/n)")
    ppi_ask = input().lower().strip()

    ppi_value = None
    if ppi_ask == "y":
        ppi_value = int(input("Enter PPI value (e.g. 72, 150, 300): "))

    print("Do you want to set a custom DPI (screen resolution)? (y/n)")
    dpi_ask = input().lower().strip()

    dpi_value = None
    if dpi_ask == "y":
        dpi_value = int(input("Enter DPI value (e.g. 72, 150, 300): "))

    print("Include subfolders? (y/n)")
    include_subfolders = input().lower().strip() == "y"

    if not target_ext.startswith("."):
        target_ext = "." + target_ext

    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp", ".avif", ".heic", ".heif"}
    current_folder = os.getcwd()
    output_folder = os.path.join(current_folder, f"converted_to_{target_ext[1:]}")
    os.makedirs(output_folder, exist_ok=True)

    print("\nConverting images...\n")

    if include_subfolders:
        # Prevent walking into the output folder
        for root, dirs, files in os.walk(current_folder):
            # Remove output_folder from dirs so os.walk does not descend into it
            abs_output_folder = os.path.abspath(output_folder)
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != abs_output_folder]
            rel_root = os.path.relpath(root, current_folder)
            for filename in files:
                name, ext = os.path.splitext(filename)
                ext = ext.lower()
                if ext in image_exts:
                    input_path = os.path.join(root, filename)
                    # Preserve subfolder structure in output
                    rel_folder = os.path.join(output_folder, rel_root) if rel_root != "." else output_folder
                    os.makedirs(rel_folder, exist_ok=True)
                    output_path = os.path.join(rel_folder, name + target_ext)
                    convert_image(
                        input_path,
                        output_path,
                        target_ext,
                        compress,
                        kb_limit,
                        resize=resize_dims,
                        resize_mode=resize_mode,
                        ppi=ppi_value,
                        dpi=dpi_value
                    )
    else:
        for filename in os.listdir(current_folder):
            name, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext in image_exts:
                input_path = os.path.join(current_folder, filename)
                output_path = os.path.join(output_folder, name + target_ext)
                convert_image(
                    input_path,
                    output_path,
                    target_ext,
                    compress,
                    kb_limit,
                    resize=resize_dims,
                    resize_mode=resize_mode,
                    ppi=ppi_value,
                    dpi=dpi_value
                )

    print(f"\nDone! Converted images are saved in: {output_folder}")

if __name__ == "__main__":
    main()


def batch_convert_in_folder(input_folder, target_ext, compress=False, max_size_kb=100, resize=None, resize_mode="pad", ppi=None, dpi=None, output_folder=None, include=False, logger=print, progress_callback=None, cancel_event=None):
    """Convert images in one or more folders to `target_ext`. Suitable for GUI use.

    - input_folder: directory or list/tuple of directories containing images
    - target_ext: extension including leading dot (e.g. '.jpg')
    - compress: boolean
    - max_size_kb: target max size when compressing
    - resize: tuple (width, height) or None
    - resize_mode: 'pad' or 'crop'
    - ppi: integer or None
    - dpi: integer or None
    - output_folder: optional specific folder to write outputs; if None a folder named converted_to_<ext> is used
    - progress_callback: function to call with progress percentage
    """
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp", ".avif", ".heic", ".heif"}

    if isinstance(input_folder, (list, tuple)):
        folders = [os.path.abspath(path) for path in input_folder if path]
    else:
        folders = [os.path.abspath(input_folder)]

    if not folders:
        logger("[INFO] No folders selected for image reformatting.")
        return

    if output_folder is None:
        output_folder = os.path.join(os.path.commonpath(folders), f"converted_to_{target_ext.lstrip('.')}")
    os.makedirs(output_folder, exist_ok=True)

    logger("\nConverting images...\n")

    # First, collect all image files to process
    image_files = []
    for current_folder in folders:
        if include:
            abs_output_folder = os.path.abspath(output_folder)
            for root, dirs, files in os.walk(current_folder):
                dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != abs_output_folder]
                for filename in files:
                    if os.path.splitext(filename)[1].lower() in image_exts:
                        image_files.append((root, filename, current_folder))
        else:
            for filename in os.listdir(current_folder):
                if os.path.splitext(filename)[1].lower() in image_exts:
                    image_files.append((current_folder, filename, current_folder))

    # Now process with progress tracking in groups of up to 100 files.
    total_files = len(image_files)
    processed_files = 0
    group_size = 100

    #Here is an explanation of the for loop:
    #The for loop it iterates over the image files in groupes of 100
    #Then it processes each image file in the group, converting it to the target format and saving it to the output folder.
    for group_start in range(0, total_files, group_size):
        group = image_files[group_start:group_start + group_size]
        #The for loop iterates over each image file in the current group, checking for cancellation, determining the output path based on whether subfolders are included, 
        #and calling the convert_image function to perform the conversion. It also updates the progress and logs the completion of the conversion process.
        for root, filename, source_folder in group:
            if cancel_event and cancel_event.is_set():
                logger("[INFO] Image reformat cancelled.")
                return
            name, ext = os.path.splitext(filename)
            input_path = os.path.join(root, filename)

            #If include is True, the output path is constructed to preserve the subfolder structure relative to the source folder.
            #If include is False, the output path is constructed directly in the output folder without preserving subfolder structure.
            if include:
                rel_root = os.path.relpath(root, source_folder)
                rel_folder = os.path.join(output_folder, rel_root) if rel_root != "." else output_folder
                os.makedirs(rel_folder, exist_ok=True)
                output_path = os.path.join(rel_folder, name + target_ext)
            else:
                output_path = os.path.join(output_folder, name + target_ext)

            convert_image(
                input_path,
                output_path,
                target_ext,
                compress,
                max_size_kb,
                resize,
                resize_mode=resize_mode,
                ppi=ppi,
                dpi=dpi,
                logger=logger,
                progress_callback=None,
                cancel_event=cancel_event
            )
            processed_files += 1
            if progress_callback and total_files > 0:
                progress_callback(int((processed_files / total_files) * 100))

    logger(f"\nDone! Converted images are saved in: {output_folder}")
    


