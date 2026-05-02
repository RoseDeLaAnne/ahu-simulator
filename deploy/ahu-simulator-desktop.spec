# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path


project_root = Path(SPECPATH).resolve().parent
source_root = project_root / "src"

added_data = [
    (str(project_root / "config"), "config"),
    (str(project_root / "data"), "data"),
    (str(project_root / "models"), "models"),
    (str(project_root / "images-of-models"), "images-of-models"),
    (str(source_root / "app" / "ui" / "assets"), "app/ui/assets"),
]

hidden_imports = [
    "a2wsgi",
    "dash",
    "dash.dcc",
    "dash.html",
    "dash.dash_table",
    "plotly",
    "plotly.graph_objects",
    "plotly.io",
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
]

windows_version_file = os.environ.get("AHU_WINDOWS_VERSION_FILE")
if windows_version_file and not Path(windows_version_file).exists():
    windows_version_file = None


a = Analysis(
    [str(source_root / "app" / "desktop_launcher.py")],
    pathex=[str(source_root)],
    binaries=[],
    datas=added_data,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AhuSimulator",
    version=windows_version_file,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AhuSimulator",
)
