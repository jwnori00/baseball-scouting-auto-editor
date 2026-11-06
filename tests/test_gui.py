import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication
from gui.app import Window
from engine.project import Pitch, Project


def test_window_editing(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = Window()
    source = str(tmp_path / 'local.mp4')
    window.project = Project(source_file=source)
    window.source = source
    window.metadata[source] = {'format': {'duration': '10'}}
    window.start.setValue(1)
    window.end.setValue(2)
    window.status.setCurrentIndex(window.status.findData('MANUALLY_CONFIRMED'))
    window.add_pitch()
    assert window.project.pitches == [Pitch(source, 1, 2, status='MANUALLY_CONFIRMED')]
    window.pitches.setCurrentRow(0)
    window.end.setValue(3)
    window.update_pitch()
    assert window.project.pitches[0].end == 3
    window.delete_pitch()
    assert not window.project.pitches
    window.dirty = False
    window.close()
    app.processEvents()


def test_preview_real_frame(tmp_path):
    import subprocess
    from PySide6.QtCore import QEventLoop, QTimer
    source = tmp_path / 'preview.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=160x120:rate=25',
                    '-t', '2', '-c:v', 'libx264', str(source)], check=True)
    app = QApplication.instance() or QApplication([])
    window = Window()
    window.open_source(str(source))
    window.seek(400)
    window.show_frame()
    wait_for_tasks(app, window)
    assert not window.frame_image.pixmap().isNull()
    window.step(1)
    wait_for_tasks(app, window)
    assert window.position() == .44
    window.start.setValue(.2); window.end.setValue(.6)
    window.preview()
    loop = QEventLoop(); QTimer.singleShot(1200, loop.quit); loop.exec()
    assert window.player.position() >= 200
    window.player.stop(); window.dirty = False; window.close(); app.processEvents()


def wait_for_tasks(app, window):
    import time
    deadline = time.monotonic() + 10
    while window.tasks and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert not window.tasks


def test_changing_source_can_be_cancelled_without_losing_cuts(tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog, QMessageBox
    app = QApplication.instance() or QApplication([])
    window = Window()
    original = str(tmp_path / 'part1.mp4')
    project = Project(source_file=original, pitches=[Pitch(original, 1, 2)])
    window.project = project
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *args: (str(tmp_path / 'part2.mp4'), ''))
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.No)
    window.choose_source()
    assert window.project is project and len(window.project.pitches) == 1
    assert not hasattr(window, 'sources') and not hasattr(window, 'junctions')
    assert not window.keep_clips.isChecked()
    window.dirty = False; window.close(); app.processEvents()
