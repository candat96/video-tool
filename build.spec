# -*- mode: python ; coding: utf-8 -*-

import os
import customtkinter

block_cipher = None

# Tìm đường dẫn customtkinter để include assets
ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (ctk_path, 'customtkinter/'),
    ],
    hiddenimports=[
        'google.genai',
        'google.genai.types',
        'google.genai.models',
        'google.genai.operations',
        'google.genai.files',
        'google.auth',
        'google.auth.transport',
        'google.auth.transport.requests',
        'openai',
        'PIL',
        'PIL.Image',
        'requests',
        'customtkinter',
        'providers',
        'providers.base',
        'providers.veo3',
        'providers.runway',
        'providers.kling',
        'providers.minimax',
        'core',
        'core.config',
        'core.prompt_engine',
        'core.task_manager',
        'core.frame_utils',
        'gui',
        'gui.app',
        'gui.settings_dialog',
        'gui.prompt_editor',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI Video Generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Không hiện cửa sổ console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI Video Generator',
)
