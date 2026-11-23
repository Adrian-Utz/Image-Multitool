import argparse

"""
Single public entry point shared by the GUI and the command-line menu.

Run GUI: python -m image_multitool
run CLI: python -m image_multitool --cli

Written by: AJ Utz
Written on: 11/17/2026
Latest Update: 11/18/2026
"""

def run_gui():
    import tkinter as tk

    from image_multitool.gui.main_window import GUI

    root = tk.Tk()
    GUI(root)
    root.mainloop()


def run_cli():
    from image_multitool.cli import main_menu

    main_menu()


def main(argv=None):
    #Parse the command to check if the user wants the CLI or the GUI
    parser = argparse.ArgumentParser(prog="image-multitool", description="Image Multitool")
    parser.add_argument("--cli", action="store_true", help="use the text menu instead of the GUI")
    args = parser.parse_args(argv)
    if args.cli:
        run_cli()
    else:
        run_gui()


if __name__ == "__main__":
    main()
