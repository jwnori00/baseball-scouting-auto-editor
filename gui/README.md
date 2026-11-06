# Desktop GUI

Run `python -m gui` from the repository root, or `run.bat` on Windows.
PySide6 handles playback and UI; the independent `engine` modules own project data,
validation, and rendering. Rendering runs on a QThread with a snapshot of project data.
The FFmpeg frame fallback decodes a single image without loading the full source.
See the root README for the editing workflow and known limitations.
