import hashlib
import json
import platform
from pathlib import Path
import sys
import traceback


def main(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    report = {'passed': False, 'frozen': bool(getattr(sys, 'frozen', False)),
              'platform': platform.platform(), 'python': sys.version}
    try:
        import cv2
        import numpy as np
        from PySide6.QtCore import QEventLoop, QTimer
        from PySide6.QtWidgets import QApplication
        from engine.runtime import tool, media_run, resource_root
        from engine.project import Project, Pitch
        from engine.render import render, output_name
        from gui.app import Window
        from gui.diagnostics import configure_logging
        configure_logging()
        report['tools'] = {name: tool(name) for name in ('ffmpeg', 'ffprobe')}
        if report['frozen']:
            assert all(Path(p).is_relative_to(resource_root()) for p in report['tools'].values())
        source = destination / '한글 원본 sample.mp4'
        media_run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=25',
                   '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '3',
                   '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', source], check=True, capture_output=True)
        original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        app = QApplication.instance() or QApplication([])
        window = Window(); window.show(); app.processEvents()
        window.open_source(str(source))
        window.start.setValue(.2); window.end.setValue(1.2)
        window.status.setCurrentIndex(window.status.findData('MANUALLY_CONFIRMED')); window.add_pitch()
        window.start.setValue(1.5); window.end.setValue(2.5); window.add_pitch()
        saved = destination / '프로젝트 test.json'
        window.project.save(saved)
        project = Project.load(saved)
        assert len(project.pitches) == 2
        window.show_frame()
        loop = QEventLoop(); QTimer.singleShot(1500, loop.quit); loop.exec()
        assert not window.frame_image.pixmap().isNull()
        window.preview()
        loop = QEventLoop(); QTimer.singleShot(1000, loop.quit); loop.exec()
        assert window.player.position() >= 200
        target = render(project, destination / '출력 폴더' / output_name(project))
        assert list(target.parent.iterdir()) == [target]
        image = media_run(['ffmpeg', '-v', 'error', '-i', target,
                           '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'bmp', '-'],
                          capture_output=True, check=True).stdout
        frame = cv2.imdecode(np.frombuffer(image, dtype=np.uint8), cv2.IMREAD_COLOR)
        assert frame is not None and np.std(frame) > 0
        assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
        window.player.stop(); window.dirty = False; window.close(); app.processEvents()
        optional = render(project, destination / '개별 클립 포함' / output_name(project), keep_clips=True)
        assert len(list(optional.with_name(optional.stem + '_클립').glob('*.mp4'))) == 2
        report.update(passed=True, single_source=True, final_mp4_only=True, optional_clips=True, output=str(target), gui_opened=True,
                      gui_playback=True, project_roundtrip=True, source_unchanged=True,
                      opencv=cv2.__version__, numpy=np.__version__)
    except Exception:
        report['error'] = traceback.format_exc()
    (destination / 'portable-test-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['passed'] else 1
