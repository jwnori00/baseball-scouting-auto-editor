import subprocess

import cv2
import numpy as np
import pytest

from engine.video import clip, probe


def test_synthetic_clip(tmp_path):
    source = tmp_path / "synthetic.mp4"
    output = tmp_path / "clip.mp4"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
        "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=30",
        "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source),
    ], check=True)
    clip(source, output, 0.5, 1)
    metadata = probe(output)
    assert float(metadata["format"]["duration"]) == pytest.approx(1, abs=0.1)
    capture = cv2.VideoCapture(str(output))
    try:
        success, frame = capture.read()
        assert success
        assert frame.shape == (240, 320, 3)
        assert np.std(frame) > 0
    finally:
        capture.release()
    with pytest.raises(FileExistsError):
        clip(source, output, 0, 1)


@pytest.mark.parametrize("start,duration", [(-1, 1), (0, 0), (0, -1)])
def test_invalid_interval(start, duration):
    with pytest.raises(ValueError):
        clip("unused.mp4", "output.mp4", start, duration)
