import io
import os
import shutil

from PIL import Image, ImageCms

"""
Optimize an existing image without changing its file type or dimensions.
This module is intentionally scoped to palette reduction, metadata removal, chroma subsampling, dithering, and color optimization.
Written by: AJ Utz
Written on: 8/14/2026
Last Updated: 8/18/2026
"""


def normalize_for_quantization(img, preserve_alpha=True):
    """Prepare an image for palette reduction without resizing or changing the file type."""
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)

    if img.mode == "CMYK":
        if "icc_profile" in img.info:
            try:
                srgb = ImageCms.createProfile("sRGB")
                cmyk = ImageCms.getOpenProfile(io.BytesIO(img.info["icc_profile"]))
                img = ImageCms.profileToProfile(
                    img,
                    cmyk,
                    srgb,
                    outputMode="RGBA" if has_alpha else "RGB",
                    renderingIntent=0,
                )
            except Exception:
                img = img.convert("RGBA" if has_alpha else "RGB")
        else:
            img = img.convert("RGBA" if has_alpha else "RGB")

    if preserve_alpha:
        if has_alpha and img.mode not in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
        elif not has_alpha and img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    else:
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

    return img


def _dither_setting(dither):
    """Map user-facing dithering names to Pillow dither modes."""
    if dither in (None, False, "none", "no"):
        return Image.Dither.NONE
    if dither in ("floyd", "floyd_steinberg", "floyd-steinberg", "floydsteinberg"):
        return Image.Dither.FLOYDSTEINBERG
    if dither in ("ordered", "bayer"):
        try:
            return Image.Dither.ORDERED
        except AttributeError:
            return Image.Dither.NONE
    return Image.Dither.NONE

def strip_metadata(img):
    """Remove all nonessential metadata while preserving transparency."""
    cleaned = img.copy()

    preserved = {}
    if "transparency" in cleaned.info:
        preserved["transparency"] = cleaned.info["transparency"]

    cleaned.info.clear()
    cleaned.info.update(preserved)
    return cleaned


def _save_kwargs_for(ext, chroma_subsampling=None):
    """Format-specific save options that shrink output without changing pixels."""
    if ext in {".png", ".apng"}:
        return {"optimize": True, "compress_level": 9}
    if ext in {".jpg", ".jpeg"}:
        kwargs = {"optimize": True}
        if chroma_subsampling is not None:
            kwargs["subsampling"] = chroma_subsampling
        return kwargs
    return {}

def apply_quantization(img, max_colors=256, method="median_cut", dither=False, preserve_alpha=True):
    """Reduce the color count while keeping the image dimensions and original file type intact."""
    if max_colors is None:
        max_colors = 256
    if method is None or method not in {"median_cut", "octree", "none"}:
        method = "median_cut"

    if method == "none":
        return img

    #Ensure the user inputed a valid range, and check for transparency
    max_colors = max(2, min(256, int(max_colors)))
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)

    #If preserve_alpha is false convert to RGB
    if has_alpha and not preserve_alpha:
        img = img.convert("RGB")
        has_alpha = False

    """
    Median cut is a clustering algorihm that divides an image into regions based on color distribution. 
    It works by iterativly selectin and splitting the pixel clusters with the largest inter-cluster variance.
    this helps reduce the number of colors while maintaining the overall cisual quality of the image.
    """
    if method == "median_cut":
        base = img.convert("RGB") if has_alpha else img
        quantized = base.convert("P", palette=Image.Palette.ADAPTIVE, colors=max_colors, dither=_dither_setting(dither))
        if has_alpha:
            alpha = img.getchannel("A")
            rgba = Image.new("RGBA", img.size)
            rgba.paste(quantized.convert("RGBA"), mask=alpha)
            return rgba
        return quantized

    """
    Octree is another cluseting algorithm that divides an image into a heirarchical tree structure based on pixel intensity.
    It uses binary splitting to divide each node into 8 smaller subnodes until a certian depth or a specified number of leaves is reached.
    """
    if method == "octree":
        base = img.convert("RGB") if has_alpha else img
        quantized = base.quantize(colors=max_colors, method=Image.Quantize.FASTOCTREE, dither=_dither_setting(dither))
        if has_alpha:
            alpha = img.getchannel("A")
            rgba = Image.new("RGBA", img.size)
            rgba.paste(quantized.convert("RGBA"), mask=alpha)
            return rgba
        return quantized
    #return original if no method is chosen
    return img


def optimize_image(input_path, output_path, max_colors=256, method="median_cut", dither=False, preserve_alpha=True, strip_metadata_enabled=True, chroma_subsampling=None, logger=print):
    """
    Optimize an existing image by reducing color count without changing dimensions or file extension.
    Removing the Metadata or, initializing croma subsampleing(if it is a jpg).
    """
    try:
        if max_colors is None:
            max_colors = 256
        if method is None or method not in {"median_cut", "octree", "none"}:
            method = "median_cut"

        output_ext = os.path.splitext(input_path)[1].lower()
        requested_ext = os.path.splitext(output_path)[1].lower() if output_path else output_ext
        if requested_ext and requested_ext != output_ext:
            root, _ = os.path.splitext(output_path)
            output_path = root + output_ext

        with Image.open(input_path) as img:
            original_mode = img.mode
            normalized = normalize_for_quantization(img, preserve_alpha=preserve_alpha)
            optimized = apply_quantization(
                normalized,
                max_colors=max_colors,
                method=method,
                dither=dither,
                preserve_alpha=preserve_alpha,
            )

            if optimize_mode := os.path.splitext(output_path)[1].lower():
                """
                Extract file extension, check if it matches one of the ommon image formats, ensure that the mode of the image is neither RGB or L(grayscale)
                then convert to RGB mode.
                """
                if optimize_mode in {".png", ".webp", ".bmp", ".gif", ".tiff", ".tif", ".jpg", ".jpeg"}:
                    if optimized.mode not in {"RGB", "L"} and optimize_mode in {".jpg", ".jpeg"}:
                        optimized = optimized.convert("RGB")

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            root, ext = os.path.splitext(output_path)
            temp_path = f"{root}.tmp{ext or '.png'}"
            before_bytes = os.path.getsize(input_path)
            if strip_metadata_enabled:
                optimized = strip_metadata(optimized)
            optimized.save(temp_path, **_save_kwargs_for(ext, chroma_subsampling))
            action = "Optimized"

            if os.path.getsize(temp_path) >= before_bytes:
                os.remove(temp_path)

                # Quantization didn't help; try stripping metadata from the
                # original pixel data alone before giving up on any savings.
                fallback = strip_metadata(normalized) if strip_metadata_enabled else normalized
                if optimize_mode in {".jpg", ".jpeg"} and fallback.mode not in {"RGB", "L"}:
                    fallback = fallback.convert("RGB")
                fallback.save(temp_path, **_save_kwargs_for(ext, chroma_subsampling))

                if os.path.getsize(temp_path) < before_bytes:
                    action = "Stripped metadata" if strip_metadata_enabled else "Optimized"
                    os.replace(temp_path, output_path)
                else:
                    os.remove(temp_path)
                    action = "Kept original"
                    same_file = os.path.abspath(os.fspath(input_path)) == os.path.abspath(os.fspath(output_path))
                    if not same_file:
                        shutil.copyfile(input_path, output_path)
            else:
                os.replace(temp_path, output_path)

            before_kb = before_bytes / 1024
            after_kb = os.path.getsize(output_path) / 1024
            logger(
                f"{action}: {os.path.basename(input_path)} -> {os.path.basename(output_path)} "
                f"({before_kb:.1f} KB -> {after_kb:.1f} KB, mode={original_mode})"
            )
            return output_path

    except Exception as exc:
        logger(f"[ERROR] Could not optimize {os.path.basename(input_path)}: {exc}")
        return None


def optimize_folder(input_folder, output_folder=None, max_colors=256, method="median_cut", dither=False, preserve_alpha=True, strip_metadata_enabled=True, chroma_subsampling=None, include_subfolders=False, logger=print, progress_callback=None, cancel_event=None):
    """Optimize all supported images in a folder without changing dimensions or file type."""
    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp", ".avif", ".heic", ".heif"}

    if isinstance(input_folder, (list, tuple)):
        folders = [os.path.abspath(path) for path in input_folder if path]
    else:
        folders = [os.path.abspath(input_folder)]

    if not folders:
        logger("[INFO] No folders selected for image optimization.")
        return []

    if output_folder is None:
        output_folder = os.path.join(os.path.commonpath(folders), "optimized_copy")

    image_files = []
    #Simple walkdown loop if the user selects include_subfolders
    for folder in folders:
        if include_subfolders:
            for root, _, files in os.walk(folder):
                for filename in files:
                    if os.path.splitext(filename)[1].lower() in valid_exts:
                        image_files.append((root, filename))
        else:
            for filename in os.listdir(folder):
                if os.path.splitext(filename)[1].lower() in valid_exts:
                    image_files.append((folder, filename))

    if not image_files:
        logger("[INFO] No supported image files found for optimization.")
        return []

    results = []
    total = len(image_files)

    for index, (root, filename) in enumerate(image_files, start=1):
        #Check for cancelation event
        if cancel_event and cancel_event.is_set():
            logger("[INFO] Image optimization cancelled.")
            return results

        input_path = os.path.join(root, filename)
        #determine the target directory based on folder structure
        if len(folders) == 1 and root == folders[0] and not include_subfolders:
            rel_path = os.path.basename(input_path)
            target_dir = output_folder
        else:
            rel_root = os.path.relpath(root, os.path.commonpath(folders)) if len(folders) > 1 else os.path.relpath(root, folders[0])
            target_dir = os.path.join(output_folder, rel_root) if rel_root != "." else output_folder

        #Create the target dir if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, filename)

        #save the image to the path
        saved = optimize_image(
            input_path,
            target_path,
            max_colors=max_colors,
            method=method,
            dither=dither,
            preserve_alpha=preserve_alpha,
            strip_metadata_enabled=strip_metadata_enabled,
            chroma_subsampling=chroma_subsampling,
            logger=logger,
        )
        #add to the results list
        if saved:
            results.append(saved)

        #Update Progress
        if progress_callback:
            progress_callback(int((index / total) * 100))

    logger(f"\n[INFO] Optimized {len(results)} image(s) to: {output_folder}\n")
    return results


def optimize_in_place(input_path, max_colors=256, method="median_cut", dither=False, preserve_alpha=True, strip_metadata_enabled=True, chroma_subsampling=None, logger=print):
    """Optimize an image in place while preserving its original dimensions and file type."""
    return optimize_image(
        input_path,
        input_path,
        max_colors=max_colors,
        method=method,
        dither=dither,
        preserve_alpha=preserve_alpha,
        strip_metadata_enabled=strip_metadata_enabled,
        chroma_subsampling=chroma_subsampling,
        logger=logger,
    )


def run_image_optimizer():
    """CLI entry point for running image optimization in a folder."""
    folder = input("Enter folder path to optimize: ").strip()
    if not folder:
        return

    method = input("Optimization method (median_cut / octree / none) [median_cut]: ").strip().lower() or "median_cut"
    if method not in {"median_cut", "octree", "none"}:
        print("Invalid method. Defaulting to median_cut.")
        method = "median_cut"

    try:
        max_colors = int(input("Maximum palette colors (2-256) [256]: ") or 256)
    except ValueError:
        max_colors = 256
    max_colors = max(2, min(256, max_colors))

    dither_raw = input("Dithering mode (none / floyd_steinberg / ordered) [none]: ").strip().lower() or "none"
    valid_dither_modes = {"none", "floyd", "floyd_steinberg", "floyd-steinberg", "steinberg", "fs", "ordered", "bayer"}
    if dither_raw not in valid_dither_modes:
        print("Invalid dithering mode. Defaulting to none.")
        dither = "none"
    else:
        dither = dither_raw
    if dither in {"floyd", "floyd_steinberg", "floyd-steinberg", "steinberg", "fs"}:
        dither = "floyd_steinberg"
    elif dither in {"ordered", "bayer"}:
        dither = "ordered"
    else:
        dither = "none"

    preserve_alpha = input("Preserve transparency? (y/n) [y]: ").strip().lower() != "n"
    strip_metadata_enabled = input("Strip metadata (EXIF, ICC, etc.)? (y/n) [y]: ").strip().lower() != "n"

    chroma_subsampling = input("JPEG chroma subsampling (4:4:4 / 4:2:2 / 4:2:0) [default]: ").strip() or None
    if chroma_subsampling not in {None, "4:4:4", "4:2:2", "4:2:0"}:
        print("Invalid subsampling. Using JPEG default.")
        chroma_subsampling = None

    include_subfolders = input("Include subfolders? (y/n) [n]: ").strip().lower() == "y"

    optimize_folder(
        folder,
        output_folder=None,
        max_colors=max_colors,
        method=method,
        dither=dither,
        preserve_alpha=preserve_alpha,
        strip_metadata_enabled=strip_metadata_enabled,
        chroma_subsampling=chroma_subsampling,
        include_subfolders=include_subfolders,
        logger=print,
    )

    print("\nImage optimization complete.\n")


