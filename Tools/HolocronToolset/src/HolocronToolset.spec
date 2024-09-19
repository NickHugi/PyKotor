# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['toolset\\__main__.py'],
    pathex=['C:\\GitHub\\PyKotor\\Tools\\HolocronToolset\\src'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['dl_translate', 'torch'],
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
    name='HolocronToolset',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['_uuid.pyd', 'api-ms-win-crt-environment-l1-1-0.dll', 'api-ms-win-crt-string-l1-1-0.dll', 'api-ms-win-crt-convert-l1-1-0.dll', 'api-ms-win-crt-heap-l1-1-0.dll', 'api-ms-win-crt-conio-l1-1-0.dll', 'api-ms-win-crt-filesystem-l1-1-0.dll', 'api-ms-win-crt-stdio-l1-1-0.dll', 'api-ms-win-crt-process-l1-1-0.dll', 'api-ms-win-crt-locale-l1-1-0.dll', 'api-ms-win-crt-time-l1-1-0.dll', 'api-ms-win-crt-math-l1-1-0.dll', 'api-ms-win-crt-runtime-l1-1-0.dll', 'api-ms-win-crt-utility-l1-1-0.dll', 'python3.dll', 'api-ms-win-crt-private-l1-1-0.dll', 'api-ms-win-core-timezone-l1-1-0.dll', 'api-ms-win-core-file-l1-1-0.dll', 'api-ms-win-core-processthreads-l1-1-1.dll', 'api-ms-win-core-processenvironment-l1-1-0.dll', 'api-ms-win-core-debug-l1-1-0.dll', 'api-ms-win-core-localization-l1-2-0.dll', 'api-ms-win-core-processthreads-l1-1-0.dll', 'api-ms-win-core-errorhandling-l1-1-0.dll', 'api-ms-win-core-handle-l1-1-0.dll', 'api-ms-win-core-util-l1-1-0.dll', 'api-ms-win-core-profile-l1-1-0.dll', 'api-ms-win-core-rtlsupport-l1-1-0.dll', 'api-ms-win-core-namedpipe-l1-1-0.dll', 'api-ms-win-core-libraryloader-l1-1-0.dll', 'api-ms-win-core-file-l1-2-0.dll', 'api-ms-win-core-synch-l1-2-0.dll', 'api-ms-win-core-sysinfo-l1-1-0.dll', 'api-ms-win-core-console-l1-1-0.dll', 'api-ms-win-core-string-l1-1-0.dll', 'api-ms-win-core-memory-l1-1-0.dll', 'api-ms-win-core-synch-l1-1-0.dll', 'api-ms-win-core-interlocked-l1-1-0.dll', 'api-ms-win-core-datetime-l1-1-0.dll', 'api-ms-win-core-file-l2-1-0.dll', 'api-ms-win-core-heap-l1-1-0.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources\\icons\\sith.ico'],
)
