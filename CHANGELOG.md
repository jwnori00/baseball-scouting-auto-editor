# v0.2.0 — single-video workflow

- Replaced multiple-source registration with one source per project and Korean review labels.
- Removed source-junction review and cross-source editing; retained same-video cut validation.
- Default output is player_date_Scouting.mp4 only; individual clips are optional.
- Kept project roundtrip and engine CSV/MLT export; legacy single-source JSON migrates without changing the original file.
- Retained portable build and updated frozen EXE acceptance for default/optional outputs.
- Added a separate CI evidence branch for observing Windows build results over existing Git access.
- AI detection remains unimplemented; actual Windows build evidence must be checked.

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
