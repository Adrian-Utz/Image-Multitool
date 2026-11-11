import os
import shutil
import tempfile
from dataclasses import dataclass, replace
from typing import Optional

import cv2
import numpy as np
"""Grade image sharpness, exposure, and optionally BRISQUE distortion.

Written by: AJ Utz
Written on: 11/10/2026
Lastest Update: 11/10/2026
"""

IMAGE_EXTENSIONS = {
    ".bmp", ".dib", ".jpg", ".jpeg", ".jpe", ".jp2", ".png",
    ".webp", ".tif", ".tiff", ".avif", ".gif",
}

GRADING_MODES = ("both", "sharpness", "brightness")
GRADES = ("A", "B", "C", "D", "E", "F")
GRADE_LABELS = {
    "A": "Excellent",
    "B": "Good",
    "C": "Fair",
    "D": "Poor",
    "E": "Very poor",
    "F": "Severely flawed",
}


@dataclass(frozen=True)
class QualityReport:
    path: str
    sharpness: float
    sharpness_label: str
    brightness: float
    exposure_label: str
    brisque: Optional[float]
    distortion_label: str
    grade: str
    similarity: Optional[float] = None
    similarity_grade: Optional[str] = None
    quality_grade: Optional[str] = None
    grading_mode: str = "both"


def calculate_blur_variance(gray_image):
    """Returns the variance of the laplacian of the grayscale image  
    Laplacian is a mathematical operator that meaures the difference between a pixel and its neighbors  
    used to identify the edges in a image. also uses 64-bit floating point to perform high percision calculations for accurate values"""
    return float(cv2.Laplacian(gray_image, cv2.CV_64F).var())


def calculate_brightness_score(gray_image):
    """Returns the mean brightness or the image.  
    measures the average intensity of all pixels in the image to assess the overall brightness"""
    return float(np.mean(gray_image))


def create_brisque(model_path, range_path):
    """Create one reusable evaluator, or disable BRISQUE if neither path is set."""
    if not model_path and not range_path:
        return None
    if not model_path or not range_path:
        raise ValueError("BRISQUE requires both a model file and a range file.")
    for path in (model_path, range_path):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"BRISQUE file not found: {path}")
    try:
        return cv2.quality.QualityBRISQUE_create(os.fspath(model_path), os.fspath(range_path))
    except (AttributeError, cv2.error) as exc:
        raise RuntimeError(f"Could not initialize BRISQUE: {exc}") from exc


def load_image(image_path):
    image_path = os.fspath(image_path)
    # imdecode with fromfile handles non-ASCII Windows paths unlike cv2.imread.
    encoded = np.fromfile(image_path, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR) if encoded.size else None
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    return image


def sharpness_grade(value):
    if value > 500:
        return "A"
    if value > 250:
        return "B"
    if value > 100:
        return "C"
    if value > 50:
        return "D"
    if value > 20:
        return "E"
    return "F"


def brightness_grade(value):
    if 40 <= value <= 215:
        return "A"
    if 30 <= value <= 225:
        return "B"
    if 20 <= value <= 235:
        return "C"
    if 10 <= value <= 245:
        return "D"
    if 5 <= value <= 250:
        return "E"
    return "F"


def similarity_grade(value):
    if value >= 0.95:
        return "A"
    if value >= 0.85:
        return "B"
    if value >= 0.70:
        return "C"
    if value >= 0.50:
        return "D"
    if value >= 0.25:
        return "E"
    return "F"


def grade_image(image_path, brisque=None, grading_mode="both"):
    """Return a report for one image; raise if the image cannot be decoded."""
    if grading_mode not in GRADING_MODES:
        raise ValueError(f"Invalid grading mode: {grading_mode}")
    image_path = os.fspath(image_path)
    image = load_image(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return _grade_decoded_image(image_path, image, gray, brisque, grading_mode)


def _grade_decoded_image(image_path, image, gray, brisque, grading_mode):
    sharpness = calculate_blur_variance(gray)
    brightness = calculate_brightness_score(gray)
    score = float(brisque.compute(image)[0]) if brisque is not None else None

    if sharpness > 500:
        sharpness_label = "Excellent"
    elif sharpness > 100:
        sharpness_label = "Acceptable"
    else:
        sharpness_label = "Blurry / Poor"

    if 40 <= brightness <= 215:
        exposure_label = "Good Exposure"
    elif brightness < 40:
        exposure_label = "Underexposed (Too Dark)"
    else:
        exposure_label = "Overexposed (Too Bright)"

    if score is None:
        distortion_label = "N/A (BRISQUE not enabled)"
    elif score < 30:
        distortion_label = "High Quality"
    elif score < 60:
        distortion_label = "Moderate Distortions"
    else:
        distortion_label = "Poor Quality / Artifacted"

    selected_grades = []
    if grading_mode in ("both", "sharpness"):
        selected_grades.append(sharpness_grade(sharpness))
    if grading_mode in ("both", "brightness"):
        selected_grades.append(brightness_grade(brightness))
    if score is not None and score >= 30:
        selected_grades.append("B")
    letter = max(selected_grades)
    grade = f"{letter} ({GRADE_LABELS[letter]})"
    return QualityReport(image_path, sharpness, sharpness_label, brightness,
                         exposure_label, score, distortion_label, grade, grading_mode=grading_mode)


def add_similarity_grade(report, reference_gray, evaluator, gray=None):
    if gray is None:
        image = load_image(report.path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if gray.shape != reference_gray.shape:
        raise ValueError(
            f"Image dimensions {gray.shape[1]}x{gray.shape[0]} do not match "
            f"base image {reference_gray.shape[1]}x{reference_gray.shape[0]}"
        )
    score = float(evaluator.compute(gray)[0])
    if not np.isfinite(score):
        raise ValueError("SSIM returned a non-finite score")
    similarity_letter = similarity_grade(score)
    quality_grade = report.grade
    final_grade = quality_grade
    if similarity_letter > quality_grade[0]:
        final_grade = f"{similarity_letter} (Limited similarity to base image)"
    return replace(report, grade=final_grade, similarity=score,
                   similarity_grade=similarity_letter, quality_grade=quality_grade)


def format_report(report, display_path=None, reference=None):
    """Generate a report to be sent to the GUI and CLI"""
    lines = [
        f"--- Quality Report for: {display_path or report.path} ---",
        f"Grading mode: {report.grading_mode}",
        f"Sharpness Score (Variance): {report.sharpness:.2f} -> {report.sharpness_label}"
        + (" (informational only)" if report.grading_mode == "brightness" else ""),
        f"Brightness Score (Mean): {report.brightness:.2f} -> {report.exposure_label}"
        + (" (informational only)" if report.grading_mode == "sharpness" else ""),
    ]
    if report.brisque is None:
        lines.append(f"Spatial Distortion (BRISQUE): {report.distortion_label}")
    else:
        lines.append(f"Spatial Distortion (BRISQUE): {report.brisque:.2f} -> {report.distortion_label}")
    if report.similarity is not None:
        lines.append(f"Quality-only grade: {report.quality_grade}")
        lines.append(f"Base image similarity (SSIM): {report.similarity:.4f} -> {report.similarity_grade}")
    lines.append(f"RECOMMENDED GRADE: {report.grade}")
    if reference is not None:
        lines.extend([
            "Differences from base image (image minus base):",
            f"Sharpness variance: {report.sharpness - reference.sharpness:+.2f}",
            f"Mean brightness: {report.brightness - reference.brightness:+.2f}"
        ])
        #Old Code
       #lines.append("Differences from base image (image minus base):")
       #lines.append(f"  Sharpness variance: {report.sharpness - reference.sharpness:+.2f}")
       #lines.append(f"  Mean brightness: {report.brightness - reference.brightness:+.2f}")
        if report.brisque is not None and reference.brisque is not None:
            lines.append(f"  BRISQUE: {report.brisque - reference.brisque:+.2f}")
    return "\n".join(lines)


def log_grade_summary(reports, logger):
    counts = dict.fromkeys(GRADES, 0)
    #Old code
    #counts = {grade: 0 for grade in GRADES} 
    for report in reports:
        counts[report.grade[0]] += 1
    logger("[INFO] Grade totals: " + ", ".join(f"{grade}: {count}" for grade, count in counts.items()))


def separate_image(source, destination, mode):
    """Copy without overwriting; only remove a source after its copy succeeds."""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    with open(source, "rb") as src:
        dst = open(destination, "xb")
        try:
            with dst:
                shutil.copyfileobj(src, dst)
            shutil.copystat(source, destination)
        except OSError as exc:
            try:
                os.remove(destination)
            except OSError as cleanup_error:
                raise OSError(f"{exc}; could not remove partial copy {destination}: {cleanup_error}") from exc
            raise
    if mode == "move":
        try:
            os.remove(source)
        except OSError as exc:
            raise OSError(f"Copy saved to {destination}, but could not remove original: {exc}") from exc


def grade_folder(input_folder, include_subfolders=False, model_path=None, range_path=None,
                 logger=print, progress_callback=None, cancel_event=None, separation=None,
                 reference_path=None, use_similarity=False, grading_mode="both"):
    """Grade supported images and optionally copy or move them into grade folders."""
    if not os.path.isdir(input_folder):
        raise NotADirectoryError(f"Folder not found: {input_folder}")
    if separation not in (None, "copy", "move"):
        raise ValueError("Separation must be 'copy', 'move', or None.")
    if grading_mode not in GRADING_MODES:
        raise ValueError(f"Invalid grading mode: {grading_mode}")
    if use_similarity and not reference_path:
        raise ValueError("Similarity grading requires a base image.")
    input_folder = os.path.abspath(input_folder)
    parent = os.path.dirname(input_folder)
    if separation and parent == input_folder:
        raise ValueError("Select a folder below the filesystem root to separate images.")
    evaluator = create_brisque(model_path, range_path)
    if evaluator is None:
        logger(f"[INFO] BRISQUE disabled; quality grades use {grading_mode}.")

    reference = None
    reference_gray = None
    similarity_evaluator = None
    reference_key = None
    if reference_path is not None:
        if cancel_event and cancel_event.is_set():
            logger("[INFO] Image quality grading cancelled.")
            log_grade_summary([], logger)
            return []
        try:
            if use_similarity:
                reference_image = load_image(reference_path)
                reference_gray = cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)
                reference = _grade_decoded_image(os.fspath(reference_path), reference_image,
                                                 reference_gray, evaluator, grading_mode)
                del reference_image
                reference_key = os.path.normcase(os.path.abspath(reference_path))
                similarity_evaluator = cv2.quality.QualitySSIM_create(reference_gray)
            else:
                reference = grade_image(reference_path, evaluator, grading_mode=grading_mode)
        except (OSError, ValueError, AttributeError, cv2.error) as exc:
            raise RuntimeError(f"Could not grade base image {reference_path}: {exc}") from exc
        if use_similarity:
            logger("[INFO] Base image metrics (SSIM similarity can lower grades):")
        else:
            logger("[INFO] Base image metrics (comparison only; grades are unchanged):")
        logger(format_report(reference))

    def raise_walk_error(error):
        raise error

    files = []
    for root, dirs, names in os.walk(input_folder, onerror=raise_walk_error):
        if cancel_event and cancel_event.is_set():
            logger("[INFO] Image quality grading cancelled.")
            log_grade_summary([], logger)
            return []
        dirs.sort()
        for name in sorted(names):
            path = os.path.join(root, name)
            if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS and os.path.isfile(path):
                files.append(path)
        if not include_subfolders:
            break
    if not files:
        logger("[INFO] No supported image files found for grading.")
        log_grade_summary([], logger)
        return []

    output_folder = None
    if separation:
        output_folder = tempfile.mkdtemp(prefix=f"{os.path.basename(input_folder)}_grades_", dir=parent)
        logger(f"[INFO] Grade folders: {output_folder}")

    reports = []
    failed = 0
    separated = 0
    separation_failed = 0
    for index, path in enumerate(files, 1):
        if cancel_event and cancel_event.is_set():
            logger(f"[INFO] Image quality grading cancelled after {index - 1} of {len(files)} files.")
            log_grade_summary(reports, logger)
            return reports
        try:
            if similarity_evaluator is not None:
                assert reference_gray is not None and reference is not None
                if os.path.normcase(os.path.abspath(path)) == reference_key:
                    report = replace(reference, path=path)
                    gray = reference_gray
                else:
                    image = load_image(path)
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    report = _grade_decoded_image(path, image, gray, evaluator, grading_mode)
                    del image
                report = add_similarity_grade(report, reference_gray, similarity_evaluator, gray=gray)
            else:
                report = grade_image(path, evaluator, grading_mode=grading_mode)
        except (OSError, ValueError, cv2.error) as exc:
            failed += 1
            logger(f"[ERROR] Could not grade {path}: {exc}")
        else:
            reports.append(report)
            logger(format_report(report, os.path.relpath(path, input_folder), reference))
            if output_folder:
                destination = os.path.join(output_folder, report.grade[0], os.path.relpath(path, input_folder))
                try:
                    separate_image(path, destination, separation)
                except OSError as exc:
                    separation_failed += 1
                    logger(f"[ERROR] Could not {separation} {path}: {exc}")
                else:
                    separated += 1
                    action = "Copied" if separation == "copy" else "Moved"
                    logger(f"[INFO] {action} to: {destination}")
        if progress_callback:
            progress_callback(index * 100 // len(files))
    logger(f"[INFO] Graded {len(reports)} image(s); {failed} failed.")
    if separation:
        logger(f"[INFO] {separated} image(s) separated; {separation_failed} separation(s) failed.")
    log_grade_summary(reports, logger)
    return reports


def run_image_quality_grader():
    """Interactive CLI entry point."""
    folder = input("Enter folder path to grade: ").strip().strip('"')
    if not folder:
        print("No folder selected.")
        return
    include = input("Include subfolders? (y/n) [n]: ").strip().lower() == "y"
    while True:
        grading_mode = input("Grade by sharpness, brightness, or both? [both]: ").strip().lower() or "both"
        if grading_mode in GRADING_MODES:
            break
        print("[ERROR] Choose sharpness, brightness, or both.")
    model_path = range_path = None
    if input("Use BRISQUE model files? (y/n) [n]: ").strip().lower() == "y":
        model_path = input("Path to BRISQUE model file: ").strip().strip('"')
        range_path = input("Path to BRISQUE range file: ").strip().strip('"')
        if not model_path or not range_path:
            print("[ERROR] Both BRISQUE files are required.")
            return
    reference_path = None
    use_similarity = False
    if input("Compare metrics to a base image? (y/n) [n]: ").strip().lower() == "y":
        reference_path = input("Path to base image: ").strip().strip('"')
        if not reference_path:
            print("[ERROR] A base image path is required.")
            return
        use_similarity = input(
            "Use visual similarity to lower grades? Images must match base dimensions. (y/n) [n]: "
        ).strip().lower() == "y"
    while True:
        choice = input("Separate by grade? (none / copy / move) [none]: ").strip().lower()
        if choice in ("", "none", "copy", "move"):
            break
        print("[ERROR] Choose none, copy, or move.")
    try:
        grade_folder(folder, include_subfolders=include, model_path=model_path, range_path=range_path,
                     separation=None if choice in ("", "none") else choice, reference_path=reference_path,
                     use_similarity=use_similarity, grading_mode=grading_mode)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"[ERROR] {exc}")


if __name__ == "__main__":
    run_image_quality_grader()
