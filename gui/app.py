"""PySide6 desktop editor with native playback and FFmpeg frame fallback."""
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from fractions import Fraction

from PySide6.QtCore import Qt, QUrl, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QSlider, QDoubleSpinBox, QSpinBox, QComboBox,
    QLineEdit, QFileDialog, QMessageBox, QFormLayout, QSplitter, QProgressBar, QCheckBox)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from engine.project import Project, Pitch, STATUSES, RULES
from engine.video import probe
from engine.render import render
from engine.quality import review


class RenderWorker(QThread):
    progress = Signal(int)
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, project, destination):
        super().__init__()
        self.project, self.destination = deepcopy(project), destination

    def run(self):
        try:
            self.completed.emit(str(render(self.project, self.destination, self.progress.emit)))
        except Exception as exc:
            self.failed.emit(str(exc))


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Baseball Scouting Auto Editor v0.1.0')
        self.resize(1280, 820)
        self.project = Project()
        self.metadata = {}
        self.source = None
        self.fps = 30
        self.preview_end = None
        self.dirty = False
        self.worker = None
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        body = QWidget()
        self.setCentralWidget(body)
        layout = QVBoxLayout(body)
        header = QHBoxLayout()
        self.title = QLineEdit(self.project.name)
        self.player_name = QLineEdit(self.project.player)
        self.date = QLineEdit(self.project.game_date)
        for label, widget in [('프로젝트', self.title), ('선수', self.player_name), ('날짜', self.date)]:
            header.addWidget(QLabel(label)); header.addWidget(widget)
            widget.textEdited.connect(self.mark_dirty)
        layout.addLayout(header)
        splitter = QSplitter()
        layout.addWidget(splitter, 1)
        left = QWidget(); ll = QVBoxLayout(left)
        ll.addWidget(QLabel('원본 목록 — 각 파일 시간은 독립적'))
        self.sources = QListWidget(); ll.addWidget(self.sources)
        self.button(ll, '로컬 영상 추가', self.add_source)
        self.button(ll, '선택 원본 경로 재연결', self.relink)
        self.junctions = QCheckBox('파일 연결부 중복·누락 수동 확인')
        self.junctions.toggled.connect(self.mark_dirty)
        ll.addWidget(self.junctions)
        self.source_info = QLabel('Part 1을 먼저 선택하세요'); self.source_info.setWordWrap(True)
        ll.addWidget(self.source_info)
        splitter.addWidget(left)
        center = QWidget(); cl = QVBoxLayout(center)
        self.video = QVideoWidget(); cl.addWidget(self.video, 1)
        self.player.setVideoOutput(self.video)
        self.frame_image = QLabel('FFmpeg 대체 프레임 미리보기'); self.frame_image.setAlignment(Qt.AlignCenter)
        self.frame_image.hide(); cl.addWidget(self.frame_image, 1)
        self.slider = QSlider(Qt.Horizontal); self.slider.setRange(0, 0); cl.addWidget(self.slider)
        self.clock = QLabel('0.000 s'); cl.addWidget(self.clock)
        controls = QHBoxLayout(); cl.addLayout(controls)
        self.button(controls, '재생/일시정지', self.play)
        self.button(controls, '◀ 1프레임', lambda: self.step(-1))
        self.button(controls, '1프레임 ▶', lambda: self.step(1))
        self.button(controls, 'FFmpeg 프레임', self.show_frame)
        splitter.addWidget(center)
        right = QWidget(); form = QFormLayout(right)
        self.start = self.time_spin(); self.end = self.time_spin()
        self.inning = QSpinBox(); self.inning.setRange(1, 99)
        self.number = QSpinBox(); self.number.setRange(1, 9999)
        self.status = QComboBox(); self.status.addItems(STATUSES); self.status.setCurrentText('REVIEW_REQUIRED')
        self.rule = QComboBox(); self.rule.addItems(RULES)
        self.notes = QLineEdit()
        self.expected = QSpinBox(); self.expected.setRange(0, 9999); self.expected.setSpecialValueText('미확인')
        for label, widget in [('시작 (초)', self.start), ('종료 (초)', self.end), ('이닝', self.inning),
                              ('투구 번호', self.number), ('검토 상태', self.status), ('종료 규칙', self.rule),
                              ('메모', self.notes), ('확인한 전체 투구 수', self.expected)]:
            form.addRow(label, widget)
        for label, action in [('현재 위치 → 시작', lambda: self.start.setValue(self.position())),
                              ('현재 위치 → 종료', lambda: self.end.setValue(self.position())),
                              ('컷 추가', self.add_pitch), ('선택 컷 수정 적용', self.update_pitch),
                              ('선택 컷 삭제', self.delete_pitch), ('선택 컷 미리보기', self.preview),
                              ('자동 탐색 안내', self.detection_info)]:
            self.button(form, label, action)
        form.addRow(QLabel('일반: 세트/와인드업 시작 → 포수 반환까지\n인플레이·폭투: 실제 플레이 종료까지\n리플레이를 별도 투구로 추가하지 마세요.'))
        splitter.addWidget(right)
        splitter.setSizes([230, 650, 330])
        self.pitches = QListWidget(); layout.addWidget(self.pitches)
        ordering = QHBoxLayout(); layout.addLayout(ordering)
        self.button(ordering, '선택 컷 위로', lambda: self.move(-1))
        self.button(ordering, '선택 컷 아래로', lambda: self.move(1))
        tools = QHBoxLayout(); layout.addLayout(tools)
        for label, action in [('프로젝트 저장', self.save), ('프로젝트 불러오기', self.load),
                              ('검증 보고서', self.report), ('영상 출력', self.export)]:
            self.button(tools, label, action)
        self.progress = QProgressBar(); tools.addWidget(self.progress)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(lambda ms: self.slider.setMaximum(ms))
        self.player.errorOccurred.connect(self.playback_error)
        self.slider.sliderMoved.connect(self.seek)
        self.sources.currentRowChanged.connect(self.select_source)
        self.pitches.currentRowChanged.connect(self.select_pitch)
        self.expected.valueChanged.connect(self.mark_dirty)

    def mark_dirty(self, *args):
        self.dirty = True

    @staticmethod
    def time_spin():
        widget = QDoubleSpinBox(); widget.setRange(0, 1e8); widget.setDecimals(6)
        return widget

    def button(self, layout, label, action):
        button = QPushButton(label)
        button.clicked.connect(lambda checked=False: self.guard(action))
        if isinstance(layout, QFormLayout): layout.addRow(button)
        else: layout.addWidget(button)
        return button

    def guard(self, action):
        try:
            action()
        except Exception as exc:
            QMessageBox.critical(self, '오류', str(exc))

    def add_source(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Part 1 또는 추가 원본 선택', '', 'Video (*.mp4 *.mkv *.mov *.avi *.ts);;All files (*)')
        if path:
            path = str(Path(path).resolve())
            if path not in self.project.sources:
                self.metadata[path] = probe(path)
                self.project.sources.append(path); self.sources.addItem(path); self.dirty = True
                self.junctions.setChecked(False)
            self.sources.setCurrentRow(self.project.sources.index(path))

    def relink(self):
        row = self.sources.currentRow()
        if row < 0: raise ValueError('재연결할 원본을 목록에서 선택하세요')
        path, _ = QFileDialog.getOpenFileName(self, '대체 원본 경로 선택')
        if not path: return
        path = str(Path(path).resolve())
        metadata = probe(path)
        old = self.project.sources[row]
        if path in self.project.sources and path != old: raise ValueError('이미 등록된 원본입니다')
        self.project.sources[row] = path
        self.metadata[path] = metadata
        for p in self.project.pitches:
            if p.source_file == old:
                p.source_file = path
                p.status = 'REVIEW_REQUIRED'
        self.sources.item(row).setText(path)
        self.open_source(path); self.refresh(); self.dirty = True

    def select_source(self, row):
        if row < 0: return
        self.guard(lambda: self.open_source(self.project.sources[row]))

    def open_source(self, source):
        metadata = self.metadata.get(source) or probe(source)
        self.metadata[source] = metadata
        stream = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
        try:
            self.fps = float(Fraction(stream.get('avg_frame_rate', '30/1')))
        except (ValueError, ZeroDivisionError):
            self.fps = 30
        if self.fps <= 0: self.fps = 30
        self.source = source
        self.preview_end = None
        self.player.pause()
        self.player.setSource(QUrl.fromLocalFile(source))
        self.video.show(); self.frame_image.hide()
        self.slider.setRange(0, round(float(metadata['format']['duration']) * 1000))
        self.source_info.setText(f'{Path(source).name}\n{stream["width"]}×{stream["height"]}\n{self.fps:.3f} fps\n{metadata["format"]["duration"]} s')
        self.start.setSingleStep(1/self.fps); self.end.setSingleStep(1/self.fps)

    def position(self):
        return self.slider.value() / 1000

    def position_changed(self, ms):
        if not self.slider.isSliderDown(): self.slider.setValue(ms)
        self.clock.setText(f'{ms/1000:.3f} s')
        if self.preview_end is not None and ms >= self.preview_end * 1000:
            self.player.pause(); self.preview_end = None

    def seek(self, ms):
        self.player.setPosition(ms); self.slider.setValue(ms)
        self.clock.setText(f'{ms/1000:.3f} s')

    def play(self):
        if not self.source: raise ValueError('원본 영상을 먼저 선택하세요')
        self.video.show(); self.frame_image.hide()
        if self.player.playbackState() == QMediaPlayer.PlayingState: self.player.pause()
        else: self.player.play()

    def step(self, delta):
        self.player.pause()
        frame = round(self.position() * self.fps) + delta
        self.seek(max(0, min(self.slider.maximum(), round(frame / self.fps * 1000))))
        self.show_frame()

    def show_frame(self):
        if not self.source: raise ValueError('원본 영상을 먼저 선택하세요')
        self.player.pause()
        result = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-ss', str(self.position()),
            '-i', self.source, '-frames:v', '1', '-vf', 'scale=800:-1', '-f', 'image2pipe', '-vcodec', 'png', '-'],
            capture_output=True, timeout=30, check=True)
        image = QImage.fromData(result.stdout)
        if image.isNull(): raise ValueError('이 위치에서 프레임을 디코딩할 수 없습니다')
        self.frame_image.setPixmap(QPixmap.fromImage(image)); self.frame_image.show(); self.video.hide()

    def playback_error(self, error, message):
        self.statusBar().showMessage(f'재생 오류: {message}. FFmpeg 프레임 버튼을 사용하세요.')

    def current_pitch(self):
        if not self.source: raise ValueError('원본을 선택하세요')
        if self.start.value() >= self.end.value(): raise ValueError('시작은 종료보다 작아야 합니다')
        duration = float(self.metadata[self.source]['format']['duration'])
        if self.end.value() > duration: raise ValueError('원본 길이를 초과했습니다')
        return Pitch(self.source, self.start.value(), self.end.value(), self.inning.value(), self.number.value(),
                     self.status.currentText(), self.rule.currentText(), self.notes.text())

    def add_pitch(self):
        self.project.pitches.append(self.current_pitch()); self.refresh(); self.dirty = True
        self.number.setValue(self.number.value()+1)

    def update_pitch(self):
        row = self.pitches.currentRow()
        if row < 0: raise ValueError('수정할 컷을 선택하세요')
        self.project.pitches[row] = self.current_pitch(); self.refresh(); self.pitches.setCurrentRow(row); self.dirty = True

    def delete_pitch(self):
        row = self.pitches.currentRow()
        if row >= 0: del self.project.pitches[row]; self.refresh(); self.dirty = True

    def move(self, delta):
        row = self.pitches.currentRow(); other = row + delta
        if row >= 0 and 0 <= other < len(self.project.pitches):
            self.project.pitches[row], self.project.pitches[other] = self.project.pitches[other], self.project.pitches[row]
            self.refresh(); self.pitches.setCurrentRow(other); self.dirty = True

    def refresh(self):
        self.pitches.clear()
        for p in self.project.pitches:
            self.pitches.addItem(f'이닝 {p.inning:02d} / 투구 {p.number:03d} | {Path(p.source_file).name} | {p.start:.3f}–{p.end:.3f}s | {p.status} | {p.rule}')

    def select_pitch(self, row):
        if row < 0: return
        p = self.project.pitches[row]
        if p.source_file in self.project.sources:
            self.sources.setCurrentRow(self.project.sources.index(p.source_file))
        self.start.setValue(p.start); self.end.setValue(p.end)
        self.inning.setValue(p.inning); self.number.setValue(p.number)
        self.status.setCurrentText(p.status); self.rule.setCurrentText(p.rule); self.notes.setText(p.notes)

    def preview(self):
        p = self.current_pitch()
        self.seek(round(p.start * 1000)); self.preview_end = p.end
        self.video.show(); self.frame_image.hide(); self.player.play()

    def sync(self):
        self.project.name = self.title.text(); self.project.player = self.player_name.text()
        self.project.game_date = self.date.text(); self.project.expected_count = self.expected.value() or None
        self.project.junctions_reviewed = self.junctions.isChecked()

    def save(self):
        self.sync()
        path, _ = QFileDialog.getSaveFileName(self, '프로젝트 저장', 'timeline.json', 'JSON (*.json)')
        if path:
            if Path(path).resolve() in [Path(p).resolve() for p in self.project.sources]:
                raise ValueError('원본 경로에 저장할 수 없습니다')
            self.project.save(path); self.dirty = False

    def can_discard(self):
        return not self.dirty or QMessageBox.question(self, '변경사항', '저장하지 않은 변경사항을 버리시겠습니까?') == QMessageBox.Yes

    def load(self):
        if not self.can_discard(): return
        path, _ = QFileDialog.getOpenFileName(self, '프로젝트 불러오기', '', 'JSON (*.json)')
        if not path: return
        project = Project.load(path)
        self.player.stop(); self.source = None; self.metadata = {}; self.project = project
        self.title.setText(project.name); self.player_name.setText(project.player); self.date.setText(project.game_date)
        self.sources.clear(); self.sources.addItems(project.sources)
        self.expected.setValue(project.expected_count or 0); self.junctions.setChecked(project.junctions_reviewed)
        self.refresh(); self.dirty = False
        missing = [p for p in project.sources if not Path(p).is_file()]
        if missing:
            QMessageBox.warning(self, '원본 경로 확인', '원본 경로가 없습니다. 목록 선택 후 원본 경로 재연결 버튼을 사용하세요:\n'+'\n'.join(missing))

    def report(self):
        self.sync()
        QMessageBox.information(self, '검증 보고서 — 완전성 보장 아님', json.dumps(review(self.project), ensure_ascii=False, indent=2))

    def export(self):
        if self.worker and self.worker.isRunning(): raise ValueError('이미 렌더링 중입니다')
        self.sync()
        destination = QFileDialog.getExistingDirectory(self, '출력 폴더 선택 — 고유 render_ 폴더 생성')
        if not destination: return
        self.progress.setValue(0)
        self.worker = RenderWorker(self.project, destination)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.completed.connect(lambda path: QMessageBox.information(self, '출력 완료', path))
        self.worker.failed.connect(lambda message: QMessageBox.critical(self, '렌더링 실패', message))
        self.worker.start()

    def detection_info(self):
        QMessageBox.information(self, '자동 탐색 미구현', 'v0.1.0은 수동 편집 버전입니다. 실제 투구 인식 모델과 정확도는 아직 검증되지 않았습니다. 외부로 영상을 전송하지 않습니다.')

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, '렌더링 중', '원본 보호를 위해 렌더링이 끝난 뒤 종료하세요.'); event.ignore(); return
        if self.can_discard(): self.player.stop(); event.accept()
        else: event.ignore()


def main():
    import shutil
    app = QApplication(sys.argv)
    if any(shutil.which(name) is None for name in ('ffmpeg', 'ffprobe')):
        QMessageBox.critical(None, 'FFmpeg 필요', 'FFmpeg와 FFprobe를 설치하고 bin 폴더를 PATH에 추가하세요.'); return 1
    window = Window(); window.show()
    return app.exec()
