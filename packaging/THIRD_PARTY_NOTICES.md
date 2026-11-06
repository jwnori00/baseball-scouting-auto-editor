# Third-party redistribution notices

This portable build includes Python (PSF), PySide6/Qt/shiboken6 (LGPLv3-compatible
open-source distribution; see each actual module's notices), NumPy (BSD), OpenCV
(Apache 2.0 plus bundled components), and the PyInstaller bootloader (GPL with
its distribution exception). The installed distributions' license/notice files
are copied verbatim under `licenses/`; `manifest.json` records exact versions.
This notice does not replace those licenses.

Qt DLLs remain separate, dynamically loaded files. You may replace compatible
Qt/PySide library files and reverse-engineer the application for debugging such
modifications as allowed by the applicable LGPL. No code signing or signature
enforcement prevents library replacement. Source and build instructions:

- Qt 6.8.3: https://download.qt.io/archive/qt/6.8/6.8.3/single/
  (`qt-everywhere-src-6.8.3.tar.xz`, including its license and build instructions).
- PySide6/shiboken 6.8.3: https://code.qt.io/pyside/pyside-setup.git/ (tag v6.8.3).
- Qt's bundled FFmpeg: consult the actual Qt Multimedia FFmpeg license notices
  and Qt Multimedia 6.8.3 sources for its build configuration. The workflow queries
  the actual avutil DLL's version and archives that exact FFmpeg release source.
- OpenCV 4.12.0: https://github.com/opencv/opencv/tree/4.12.0
- NumPy 2.2.6: https://github.com/numpy/numpy/tree/v2.2.6
- Python: https://www.python.org/downloads/source/ (exact version in build report).
- PyInstaller: https://github.com/pyinstaller/pyinstaller/tree/v6.16.0

## Standalone FFmpeg and FFprobe

The build compiles the official FFmpeg n7.1.3 source mirror at
f46e514491172d15bd74b4abb1814cd2f05a763e with libx264 from the VideoLAN mirror at
c24e06c2e184345ceb33eb20a15d1024d9fd3497. No `--enable-nonfree` components
are used. `--enable-gpl` makes these standalone executables GPLv2-or-later.
They are separate processes; the application does not link to their libraries.

Unmodified complete FFmpeg and x264 source archives, the build script, configure
log, compiler version and actual build configuration accompany the binaries in
`corresponding-source/`. The full GPL texts are in `licenses/FFmpeg/`.
Keep these notices and source materials with redistributions. Rebuilding needs
Windows x64, MSYS2 MINGW64 GCC/make/nasm/pkgconf/git and the included script.
The script's pinned network fetches can be replaced by unpacking the included
source archives into its `build/media` directories and skipping git fetch/archive.

FFmpeg supports AAC and libx264/H.264 in this build; the workflow performs actual
encode/decode tests. Patent licensing is distinct from the open-source licenses.
The source-based build is used instead of a third-party opaque prebuilt binary
so its exact corresponding source can be distributed alongside it.

The Windows build publishes `ThirdPartyCorrespondingSources` beside the portable
artifact, containing full Qt/PySide source and any separately bundled Qt FFmpeg
source. Distribute that source artifact from the same download location alongside
the portable ZIP; tagged private draft releases attach both. Source is not needed
to run the EXE. The Qt archive is checked against the upstream SHA-256 file.

The optional OpenCV videoio FFmpeg DLL is excluded from the portable bundle.
Frames are decoded by the standalone FFmpeg and processed with cv2.imdecode.
