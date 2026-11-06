"""Archive upstream corresponding source and license texts for Qt/PySide wheels."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import tarfile
import urllib.request
import PySide6

root = Path(__file__).resolve().parent.parent
sources = root / 'vendor' / 'qt-sources'
licenses = root / 'vendor' / 'qt-licenses'
sources.mkdir(parents=True, exist_ok=True)
licenses.mkdir(parents=True, exist_ok=True)
manifest = []
license_index = []


def fetch(url, filename):
    path = sources / filename
    request = urllib.request.Request(url, headers={'User-Agent': 'BaseballScoutingEditor-build'})
    with urllib.request.urlopen(request, timeout=180) as response, path.open('wb') as output:
        while block := response.read(1024 * 1024): output.write(block)
    digest = hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()
    manifest.append({'url': url, 'file': filename, 'sha256': digest})
    return path

qt_url = 'https://download.qt.io/archive/qt/6.8/6.8.3/single/qt-everywhere-src-6.8.3.tar.xz'
qt = fetch(qt_url, 'qt-everywhere-src-6.8.3.tar.xz')
with urllib.request.urlopen(qt_url + '.sha256', timeout=60) as response:
    expected = response.read().decode().split()[0].lower()
if manifest[-1]['sha256'] != expected: raise RuntimeError('Qt source checksum mismatch')
pyside = fetch('https://github.com/pyside/pyside-setup/archive/3ae6c97953d563c33ff630f259716b01b81aa531.tar.gz',
               'pyside-setup-6.8.3.tar.gz')
# Only extract license text, using safe basenames rather than archive paths.
for archive in (qt, pyside):
    with tarfile.open(archive) as tar:
        for member in tar:
            if member.isfile() and ('/LICENSES/' in member.name or Path(member.name).name.startswith(('LICENSE', 'COPYING'))):
                identifier = hashlib.sha256(member.name.encode()).hexdigest()[:16]
                filename = re.sub(r'[^A-Za-z0-9._-]', '_', Path(member.name).name)[:80]
                destination = licenses / (identifier + '-' + filename)
                license_index.append({'file': destination.name, 'archive': archive.name, 'source_path': member.name})
                destination.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as stream: destination.write_bytes(stream.read())
# Qt Multimedia's FFmpeg binaries, if present, have their own LGPL source.
# Query the actual DLL rather than guessing a patch version from the ABI number.
qt_root = Path(PySide6.__file__).parent
handles = []
for directory in {p.parent for p in qt_root.rglob('avutil-*.dll')}:
    handles.append(os.add_dll_directory(str(directory)))
    for dll in directory.glob('avutil-*.dll'):
        library = ctypes.CDLL(str(dll))
        function = library.av_version_info; function.restype = ctypes.c_char_p
        version = function().decode()
        match = re.fullmatch(r'(?:n)?(\d+\.\d+(?:\.\d+)?)', version)
        if not match: raise RuntimeError(f'Qt FFmpeg exact source cannot be identified: {version}')
        release = match.group(1)
        fetch(f'https://github.com/FFmpeg/FFmpeg/archive/refs/tags/n{release}.tar.gz', f'qt-ffmpeg-{release}.tar.gz')
(licenses / 'license-index.json').write_text(json.dumps(license_index, indent=2), encoding='utf-8')
(sources / 'source-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
