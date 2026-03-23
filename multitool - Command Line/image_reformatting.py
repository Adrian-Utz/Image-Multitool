import os
import io
from PIL import Image, ImageCms


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

#Last updated:1/28/2026
#Written by: AJ Utz on 12/18/2025

def convert_image(input_path, output_path, target_ext, compress=False, max_size_kb=100, resize=None, ppi=None):
    try:
        with Image.open(input_path) as img:

           
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
                        print("ICC conversion failed, falling back:", e)
                        img = img.convert("RGBA" if has_alpha else "RGB")
                else:
                    img = img.convert("RGBA" if has_alpha else "RGB")

            #3. Normalize modes safely
            if has_alpha and img.mode not in ("RGBA", "LA"):
                img = img.convert("RGBA")
            elif not has_alpha and img.mode != "RGB":
                img = img.convert("RGB")

            #4. Resize / pad (alpha-safe)
            if resize:
                target_w, target_h = resize
                orig_w, orig_h = img.size

                if orig_w * target_h != orig_h * target_w:
                    img = resize_to_square_with_padding(img, resize)
                else:
                    img = img.resize(resize, Image.LANCZOS)

            #5. Flatten ONLY if needed

            if has_alpha and target_ext in (".jpg", ".jpeg"):
                img = flatten_transparency(img)
                has_alpha = False  #alpha is now gone

            #6. Save (with compression loop)
            if not compress:
                save_kwargs = {}
                if ppi:
                    save_kwargs["dpi"] = (ppi, ppi)

                img.save(output_path, **save_kwargs)

                size_kb = os.path.getsize(output_path) / 1024
                print(f"Converted: {os.path.basename(input_path)} -> {os.path.basename(output_path)} ({size_kb:.1f} KB)")
                return

            quality = 95
            temp_path = output_path

            while True:
                save_kwargs = {}
                if ppi:
                    save_kwargs["dpi"] = (ppi, ppi)

                if target_ext in (".jpg", ".jpeg", ".webp"):
                    img.save(temp_path, quality=quality, **save_kwargs)
                else:
                    img.save(temp_path, **save_kwargs)


                size_kb = os.path.getsize(temp_path) / 1024
                if size_kb <= max_size_kb or quality <= 10:
                    break

                quality -= 5

            print(
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
    print("What file type do you want to convert your images to? (jpg, png, webp, tiff, bmp)")
    target_ext = input("Enter file type (without dot): ").lower().strip()
    if not target_ext.startswith("."):
        target_ext = "." + target_ext
    
    print("Would you like to resize each image to 100KB?")
    kb_ask = input("Enter y or n: ").lower().strip()
    compress = (kb_ask == "y")

    print("Do you want tot resize the images to specific dimentions? (y/n)")
    resize_ask = input().lower().strip()
    resize_dims = None
    if resize_ask == "y":
        width = int(input("Enter new Width (px): "))
        height = int(input("Enter new Height (px): "))
        resize_dims = (width, height)

    print("Do you want to set a custom PPI (print resolution)? (y/n)")
    ppi_ask = input().lower().strip()

    ppi_value = None
    if ppi_ask == "y":
        ppi_value = int(input("Enter PPI value (e.g. 72, 150, 300): "))


    if not target_ext.startswith("."):
        target_ext = "." + target_ext

    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}
    current_folder = os.getcwd()
    output_folder = os.path.join(current_folder, f"converted_to_{target_ext[1:]}")
    os.makedirs(output_folder, exist_ok=True)

    #Loop through files only once
    print("\nConverting images...\n")

    for filename in os.listdir(current_folder):
        name, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext in image_exts:
            input_path = os.path.join(current_folder, filename)
            output_path = os.path.join(output_folder, name + target_ext)
            convert_image(input_path, output_path, target_ext, compress, resize=resize_dims)

    print(f"\nDone! Converted images are saved in: {output_folder}")

if __name__ == "__main__":
    main()
    


