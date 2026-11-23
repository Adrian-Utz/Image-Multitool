import json
import os

"""
Persisted user preferences (theme, auto-start) stored in the user's home folder.

Written by: AJ Utz
Written on: 11/18/2026
Latest Update: 11/18/2026
"""

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".multitool_settings.json")


def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f)
    except Exception:
        pass


def update_setting(key, value):
    settings = load_settings()
    settings[key] = value
    save_settings(settings)


def load_saved_auto_start(default=True):
    """Return the last-used auto-start flag, falling back to `default`."""
    return bool(load_settings().get("auto_start", default))
