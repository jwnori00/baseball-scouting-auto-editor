# Build on Windows x64. No onefile extraction or external PATH requirements.
from pathlib import Path
root = Path(SPECPATH)
ffmpeg = root / 'vendor' / 'ffmpeg'
for name in ('ffmpeg.exe', 'ffprobe.exe'):
    if not (ffmpeg / 'bin' / name).is_file():
        raise SystemExit('Build bundled FFmpeg first: packaging/build_ffmpeg.sh')
a = Analysis(
    [str(root / 'packaging' / 'portable_entry.py')],
    pathex=[str(root)],
    binaries=[(str(ffmpeg / 'bin' / 'ffmpeg.exe'), 'tools'),
              (str(ffmpeg / 'bin' / 'ffprobe.exe'), 'tools')],
    datas=[], hiddenimports=['cv2', 'numpy'], hookspath=[],
    excludes=['pytest', 'tkinter', 'PyQt5', 'PyQt6'], noarchive=False,
)
# OpenCV uses subprocess-decoded frames, not its optional FFmpeg videoio DLL.
# Avoid redistributing a second opaque FFmpeg build from the OpenCV wheel.
a.binaries = [entry for entry in a.binaries
              if not Path(entry[0]).name.lower().startswith('opencv_videoio_ffmpeg')]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
          name='BaseballScoutingEditor', debug=False, bootloader_ignore_signals=False,
          strip=False, upx=False, console=False, contents_directory='_internal')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False,
               name='BaseballScoutingEditor')
