# Portable packaging update

- Added Windows x64 PyInstaller onedir workflow and frozen EXE media acceptance test.
- Added bundled absolute tool paths, Unicode-safe subprocesses and per-user rotating logs.
- Moved metadata, frame fallback and review operations off the GUI thread.
- Added pinned FFmpeg/x264 source build, corresponding sources, Qt/PySide notices, signature reporting and ZIP checksums.
- Added private tagged draft-release support. AI detection remains unimplemented.
- Windows build and artifact status must be verified from the actual Actions run.

# v0.1.0

- Added PySide6 desktop timeline editor, native playback and FFmpeg frame fallback.
- Added per-source pitch data, review states, atomic JSON save, CSV and source relinking.
- Added normalized H.264/AAC clips, concatenation, output decode validation and relative-path MLT export.
- Added timing, overlap, order, missing-source and expected-count review checks.
- Added Windows setup/run scripts and synthetic media/GUI integration tests.
- Preserved existing probe/clip CLI and cloud environment setup files.
- Pending: Windows real-footage acceptance, Shotcut compatibility, automatic detection,
  VFR frame accuracy, cancellation and finer rendering progress.
