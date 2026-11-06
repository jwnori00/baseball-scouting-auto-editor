"""FFmpeg adapters; no GUI or platform-specific dependencies."""
import json
import math
from pathlib import Path
import subprocess


def probe(source):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(source)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def clip(source, destination, start, duration):
    """Re-encode a precise clip; refuse to overwrite existing output."""
    if not all(math.isfinite(t) for t in (start, duration)) or start < 0 or duration <= 0:
        raise ValueError("start must be nonnegative and duration positive")
    if Path(source).resolve() == Path(destination).resolve():
        raise ValueError("source and destination must differ")
    if Path(destination).exists():
        raise FileExistsError(destination)
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
         "-ss", str(start), "-i", str(source), "-t", str(duration),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(destination)],
        check=True,
    )
