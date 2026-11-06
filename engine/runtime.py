"""Resolve bundled tools without relying on the user's PATH."""
import os
from pathlib import Path
import shutil
import subprocess
import sys


def resource_root():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))


def tool(name):
    if name not in ('ffmpeg', 'ffprobe'):
        raise ValueError('Unsupported media tool')
    filename = name + ('.exe' if os.name == 'nt' else '')
    bundled = resource_root() / 'tools' / filename
    if bundled.is_file():
        return str(bundled)
    if getattr(sys, 'frozen', False):
        raise FileNotFoundError(f'내장 {filename} 파일이 없습니다. ZIP 전체를 새 폴더에 다시 압축 해제하세요.')
    found = shutil.which(name)
    if found:
        return found
    raise FileNotFoundError(f'개발 환경에 {name}가 없습니다. 포터블 ZIP 사용자는 전체 압축을 다시 해제하세요.')


def media_run(args, **kwargs):
    args = [tool(args[0]), *map(str, args[1:])]
    if os.name == 'nt':
        kwargs.setdefault('creationflags', subprocess.CREATE_NO_WINDOW)
    # Unicode paths go through CreateProcessW; never invoke a shell.
    if kwargs.get('text'):
        kwargs.setdefault('encoding', 'utf-8')
        kwargs.setdefault('errors', 'replace')
    return subprocess.run(args, **kwargs)
