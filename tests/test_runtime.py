from pathlib import Path
import sys
import pytest
from engine import runtime


def test_frozen_tool_never_falls_back_to_path(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, '_MEIPASS', str(tmp_path), raising=False)
    monkeypatch.setattr(runtime.shutil, 'which', lambda _: '/external/ffmpeg')
    with pytest.raises(FileNotFoundError): runtime.tool('ffmpeg')
    folder = tmp_path / 'tools'; folder.mkdir()
    tool = folder / ('ffmpeg.exe' if runtime.os.name == 'nt' else 'ffmpeg')
    tool.write_bytes(b'placeholder')
    assert runtime.tool('ffmpeg') == str(tool)


def test_media_run_preserves_unicode_arguments(monkeypatch):
    monkeypatch.setattr(runtime, 'tool', lambda _: '/bundle/tools/ffmpeg')
    captured = {}
    def run(args, **kwargs):
        captured.update(args=args, kwargs=kwargs)
    monkeypatch.setattr(runtime.subprocess, 'run', run)
    runtime.media_run(['ffmpeg', '-i', Path('한글 폴더/원본 경기.mp4')], text=True)
    assert captured['args'] == ['/bundle/tools/ffmpeg', '-i', '한글 폴더/원본 경기.mp4']
    assert not captured['kwargs'].get('shell')
    assert captured['kwargs']['encoding'] == 'utf-8'
