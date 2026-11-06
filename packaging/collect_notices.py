"""Copy actual installed license files and source/build provenance into onedir."""
from importlib import metadata
import json
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parent.parent
package = root / 'dist' / 'BaseballScoutingEditor'
licenses = package / 'licenses'
licenses.mkdir(parents=True, exist_ok=True)
manifest = []
for name in ('PySide6', 'PySide6_Essentials', 'PySide6_Addons', 'shiboken6',
             'numpy', 'opencv-python-headless', 'pyinstaller'):
    dist = metadata.distribution(name)
    copied = []
    for entry in dist.files or []:
        if any(word in str(entry).lower() for word in ('license', 'copying', 'notice')):
            source = Path(dist.locate_file(entry))
            if source.is_file():
                # Preserve paths because wheels may have several files named LICENSE.
                relative = Path(*[p for p in entry.parts if p not in ('..', '.')])
                destination = licenses / name / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied.append(str(destination.relative_to(package)))
    if not copied:
        if name.lower().startswith(('pyside6', 'shiboken6')):
            copied = ['licenses/Qt-source-licenses (official corresponding source)']
        else:
            raise RuntimeError(f'No license files found for {name}')
    manifest.append({'package': name, 'version': dist.version, 'license_files': copied})
python_license = Path(sys.base_prefix) / 'LICENSE.txt'
if not python_license.is_file(): raise RuntimeError('Python license missing')
shutil.copy2(python_license, licenses / 'Python-LICENSE.txt')
shutil.copytree(root / 'vendor' / 'qt-licenses', licenses / 'Qt-source-licenses', dirs_exist_ok=True)
shutil.copytree(root / 'vendor' / 'ffmpeg' / 'licenses', licenses / 'FFmpeg', dirs_exist_ok=True)
shutil.copytree(root / 'vendor' / 'ffmpeg' / 'sources', package / 'corresponding-source', dirs_exist_ok=True)
for name in ('PORTABLE_README.txt', 'THIRD_PARTY_NOTICES.md'):
    shutil.copy2(root / 'packaging' / name, package / name)
(licenses / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
