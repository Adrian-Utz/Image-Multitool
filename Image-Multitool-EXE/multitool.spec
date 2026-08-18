# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import tempfile
import zipfile
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

tcl_tk_datas = []
if sys.version_info >= (3, 14):
    tcl_root = os.path.join(sys.base_prefix, 'tcl')
    tcl_archive = os.path.join(tcl_root, 'libtcl9.0.4.zip')
    tk_archive = os.path.join(tcl_root, 'libtk9.0.4.zip')
    if os.path.isfile(tcl_archive) and os.path.isfile(tk_archive):
        tcl_tk_build_root = tempfile.mkdtemp(prefix='multitool-tcl-tk-')
        tcl_data_root = os.path.join(tcl_tk_build_root, '_tcl_data')
        tk_data_root = os.path.join(tcl_tk_build_root, '_tk_data')
        with zipfile.ZipFile(tcl_archive) as archive:
            for member in archive.infolist():
                relative_name = member.filename.removeprefix('tcl_library/')
                if relative_name:
                    archive.extract(member, tcl_data_root)
                    extracted_path = os.path.join(tcl_data_root, member.filename)
                    target_path = os.path.join(tcl_data_root, relative_name)
                    if extracted_path != target_path and os.path.exists(extracted_path):
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        os.replace(extracted_path, target_path)
        with zipfile.ZipFile(tk_archive) as archive:
            for member in archive.infolist():
                relative_name = member.filename.removeprefix('tk_library/')
                if relative_name:
                    archive.extract(member, tk_data_root)
                    extracted_path = os.path.join(tk_data_root, member.filename)
                    target_path = os.path.join(tk_data_root, relative_name)
                    if extracted_path != target_path and os.path.exists(extracted_path):
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        os.replace(extracted_path, target_path)
        tcl_tk_datas.extend([
            (tcl_data_root, '_tcl_data'),
            (tk_data_root, '_tk_data'),
        ])

a = Analysis(
    ['gui.py'],
    pathex=[base_path],
    binaries=pillow_heif_binaries,
    datas=[
        ('assets/codec.wav', 'assets'),
        *tcl_tk_datas,
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
        'create_backup',
        'check_for_update',
        'image_optimization',
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
