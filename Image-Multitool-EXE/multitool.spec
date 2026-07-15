# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

block_cipher = None

try:
    base_path = os.path.abspath(os.path.dirname(__file__))
except NameError:
    base_path = os.path.abspath(os.getcwd())

pillow_heif_binaries = []
pillow_heif_hiddenimports = []
try:
    import pillow_heif
    pillow_heif_root = os.path.abspath(os.path.join(os.path.dirname(pillow_heif.__file__), os.pardir))
    pillow_heif_binaries = collect_dynamic_libs('pillow_heif')
    pillow_heif_hiddenimports = collect_submodules('pillow_heif')
    for name in os.listdir(pillow_heif_root):
        if name.lower().startswith('libheif') and name.lower().endswith('.dll'):
            pillow_heif_binaries.append((os.path.join(pillow_heif_root, name), '.'))
except ModuleNotFoundError:
    pass

a = Analysis(
    ['gui.py'],
    pathex=[base_path],
    binaries=pillow_heif_binaries,
    datas=[
        ('assets/codec.wav', 'assets')
    ],
    hiddenimports=[
        'count_files_by_extension',
        'list_files_by_extension',
        'search_files',
        'image_reformatting',
        'rename_wt_excel',
        'compare_txt_to_excel',
        'web_downloading',
        'folder_compare',
        'gui_helpers',
        'konami',
        'options',
        'PIL',
        'pandas',
        'numpy',
        'requests',
        'tqdm',
        'openpyxl',
        'pillow_avif',
        'pillow_heif',
        'pillow_heif.HeifImagePlugin',
        'pillow_heif.as_plugin',
        'jinja2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Multitool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
