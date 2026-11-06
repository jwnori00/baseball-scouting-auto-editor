"""PySide6 desktop editor with native playback and FFmpeg frame fallback."""
import json
import logging
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

from engine.runtime import media_run, tool
from .diagnostics import configure_logging, error_text
from engine.project import Project, Pitch, STATUSES, RULES
from engine.video import probe
from engine.render import render, output_name
from engine.quality import review


STATUS_LABELS = dict(zip(STATUSES, ('자동 후보 (미검증)', '검수 완료', '검수 필요', '원본 확인 필요')))


class RenderWorker(QThread):
    progress = Signal(int)
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, project, destination, keep_clips=False):
        super().__init__()
        self.project, self.destination = deepcopy(project), destination
        self.keep_clips = keep_clips

    def run(self):
        try:
            self.completed.emit(str(render(self.project, self.destination, self.progress.emit, keep_clips=self.keep_clips)))
        except Exception as exc:
            logging.exception('Rendering failed')
            self.failed.emit(error_text(exc))


class Task(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, operation):
        super().__init__()
        self.operation = operation

    def run(self):
        try:
            self.completed.emit(self.operation())
        except Exception as exc:
            logging.exception('Background media operation failed')
            self.failed.emit(error_text(exc))


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Baseball Scouting Auto Editor v0.2.0 — 단일 영상 편집')
        self.resize(1180, 820)
        self.project = Project()
        self.metadata = {}
        self.source = None
        self.fps = 30
        self.preview_end = None
        self.dirty = False
        self.worker = None
        self.tasks = []
        self.source_request = 0
        self.frame_request = 0
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        body = QWidget()
        self.setCentralWidget(body)
        layout = QVBoxLayout(body)
        header = QHBoxLayout()
        self.player_name = QLineEdit(self.project.player)
        self.date = QLineEdit(self.project.game_date)
        for label, widget in [('대상 투수 이름', self.player_name), ('경기 날짜', self.date)]:
            header.addWidget(QLabel(label)); header.addWidget(widget)
            widget.textEdited.connect(self.mark_dirty)
        layout.addLayout(header)
        splitter = QSplitter()
        layout.addWidget(splitter, 1)
        file_row = QHBoxLayout()
        self.button(file_row, '1. 원본 영상 선택', self.choose_source)
        self.source_info = QLabel('선택한 원본 영상이 없습니다')
        self.source_info.setWordWrap(True)
        file_row.addWidget(self.source_info, 1)
        self.button(file_row, '원본 경로 재연결', self.relink)
        layout.insertLayout(1, file_row)
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
        self.status = QComboBox()
        for value, label in STATUS_LABELS.items(): self.status.addItem(label, value)
        self.status.setCurrentIndex(self.status.findData('REVIEW_REQUIRED'))
        self.rule = QComboBox(); self.rule.addItems(RULES)
        self.notes = QLineEdit()
        self.expected = QSpinBox(); self.expected.setRange(0, 9999); self.expected.setSpecialValueText('미확인')
        for label, widget in [('시작 (초)', self.start), ('종료 (초)', self.end), ('이닝', self.inning),
                              ('투구 번호', self.number), ('검토 상태', self.status), ('종료 규칙', self.rule),
                              ('메모', self.notes), ('확인한 전체 투구 수', self.expected)]:
            form.addRow(label, widget)
        for label, action in [('현재 위치 → 시작', lambda: self.start.setValue(self.position())),
                              ('현재 위치 → 종료', lambda: self.end.setValue(self.position())),
                              ('투구 추가', self.add_pitch), ('선택 투구 수정 적용', self.update_pitch),
                              ('선택 투구 삭제', self.delete_pitch), ('투구 구간 미리보기', self.preview),
                              ('자동 탐색 (준비 중)', self.detection_info)]:
            self.button(form, label, action)
        form.addRow(QLabel('일반: 세트/와인드업 시작 → 포수 반환까지\n인플레이·폭투: 실제 플레이 종료까지\n리플레이를 별도 투구로 추가하지 마세요.'))
        splitter.addWidget(right)
        splitter.setSizes([820, 340])
        self.pitches = QListWidget(); layout.addWidget(self.pitches)
        ordering = QHBoxLayout(); layout.addLayout(ordering)
        self.button(ordering, '선택 컷 위로', lambda: self.move(-1))
        self.button(ordering, '선택 컷 아래로', lambda: self.move(1))
        tools = QHBoxLayout(); layout.addLayout(tools)
        for label, action in [('프로젝트 저장', self.save), ('프로젝트 불러오기', self.load),
                              ('검증 보고서', self.report), ('최종 MP4 저장', self.export)]:
            self.button(tools, label, action)
        self.keep_clips = QCheckBox('투구별 MP4도 저장')
        tools.addWidget(self.keep_clips)
        self.progress = QProgressBar(); tools.addWidget(self.progress)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(lambda ms: self.slider.setMaximum(ms))
        self.player.errorOccurred.connect(self.playback_error)
        self.slider.sliderMoved.connect(self.seek)
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
            logging.exception('User operation failed')
            QMessageBox.critical(self, '오류', error_text(exc))

    def choose_source(self):
        if self.tasks: raise ValueError('영상 분석이 끝난 뒤 원본을 선택하세요')
        path, _ = QFileDialog.getOpenFileName(self, '원본 영상 하나 선택', '', '영상 (*.mp4 *.mkv *.mov *.avi *.ts);;모든 파일 (*)')
        if not path: return
        path = str(Path(path).resolve())
        if path == self.project.source_file:
            self.request_source(path)
            return
        if (self.project.pitches or self.dirty) and QMessageBox.question(
                self, '새 영상 작업', '다른 원본을 선택하면 현재 컷 목록이 초기화됩니다. 저장한 프로젝트 파일은 유지됩니다. 계속하시겠습니까?') != QMessageBox.Yes:
            return
        self.task(lambda: probe(path), lambda metadata: self.begin_source(path, metadata))

    def begin_source(self, path, metadata):
        if not any(stream.get('codec_type') == 'video' for stream in metadata['streams']):
            raise ValueError('선택한 파일에 영상 스트림이 없습니다')
        self.sync()
        self.project = Project(source_file=path, player=self.project.player, game_date=self.project.game_date)
        self.metadata = {path: metadata}
        self.open_source(path)
        self.refresh()
        self.start.setValue(0); self.end.setValue(0); self.number.setValue(1)
        self.status.setCurrentIndex(self.status.findData('REVIEW_REQUIRED'))
        self.expected.setValue(0)
        self.dirty = True

    def relink(self):
        if self.tasks: raise ValueError('영상 분석이 끝난 뒤 재연결하세요')
        if not self.project.source_file: raise ValueError('원본 영상을 먼저 선택하세요')
        path, _ = QFileDialog.getOpenFileName(self, '같은 원본의 새 경로 선택')
        if not path: return
        path = str(Path(path).resolve())
        self.task(lambda: probe(path), lambda metadata: self.finish_relink(path, metadata))

    def finish_relink(self, path, metadata):
        if not any(stream.get('codec_type') == 'video' for stream in metadata['streams']):
            raise ValueError('선택한 파일에 영상 스트림이 없습니다')
        self.project.source_file = path
        self.metadata = {path: metadata}
        for pitch in self.project.pitches:
            pitch.source_file = path
            pitch.status = 'REVIEW_REQUIRED'
        self.open_source(path); self.refresh(); self.dirty = True

    def task(self, operation, completed):
        worker = Task(operation)
        self.tasks.append(worker)
        worker.completed.connect(lambda result: self.guard(lambda: completed(result)))
        worker.failed.connect(lambda message: QMessageBox.critical(self, '영상 처리 오류', message))
        worker.finished.connect(lambda: self.tasks.remove(worker))
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def request_source(self, source):
        self.source_request += 1
        self.source = None
        request = self.source_request
        self.player.pause()
        def ready(metadata):
            if request != self.source_request: return
            self.metadata[source] = metadata
            self.open_source(source)
        self.task(lambda: self.metadata.get(source) or probe(source), ready)

    def open_source(self, source):
        if self.project.pitches and self.project.source_file != source:
            raise ValueError('다른 원본을 사용하려면 새 영상 작업을 시작하세요')
        metadata = self.metadata.get(source) or probe(source)
        self.metadata[source] = metadata
        stream = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
        try:
            self.fps = float(Fraction(stream.get('avg_frame_rate', '30/1')))
        except (ValueError, ZeroDivisionError):
            self.fps = 30
        if self.fps <= 0: self.fps = 30
        self.source = source
        self.project.source_file = source
        self.frame_request += 1
        self.preview_end = None
        self.player.pause()
        self.player.setSource(QUrl.fromLocalFile(source))
        self.video.show(); self.frame_image.hide()
        self.slider.setRange(0, round(float(metadata['format']['duration']) * 1000))
        self.source_info.setText(f'{source}\n{stream["width"]}×{stream["height"]} · {self.fps:.3f} fps · {metadata["format"]["duration"]}초')
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
        self.frame_request += 1
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
        source, position = self.source, self.position()
        self.frame_request += 1
        request = self.frame_request
        def decode():
            return media_run(['ffmpeg', '-v', 'error', '-nostdin', '-ss', str(position),
                '-i', source, '-frames:v', '1', '-vf', 'scale=800:-1', '-f', 'image2pipe', '-vcodec', 'bmp', '-'],
                capture_output=True, timeout=30, check=True).stdout
        def ready(data):
            if request != self.frame_request or source != self.source: return
            image = QImage.fromData(data)
            if image.isNull(): raise ValueError('이 위치에서 프레임을 디코딩할 수 없습니다')
            self.frame_image.setPixmap(QPixmap.fromImage(image)); self.frame_image.show(); self.video.hide()
        self.task(decode, ready)

    def playback_error(self, error, message):
        self.statusBar().showMessage(f'재생 오류: {message}. FFmpeg 프레임 버튼을 사용하세요.')

    def current_pitch(self):
        if not self.source: raise ValueError('원본을 선택하세요')
        if self.start.value() >= self.end.value(): raise ValueError('시작은 종료보다 작아야 합니다')
        duration = float(self.metadata[self.source]['format']['duration'])
        if self.end.value() > duration: raise ValueError('원본 길이를 초과했습니다')
        return Pitch(self.source, self.start.value(), self.end.value(), self.inning.value(), self.number.value(),
                     self.status.currentData(), self.rule.currentText(), self.notes.text())

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
            self.pitches.addItem(f'이닝 {p.inning:02d} / 투구 {p.number:03d} | {p.start:.3f}–{p.end:.3f}s | {STATUS_LABELS[p.status]} | {p.rule}')

    def select_pitch(self, row):
        if row < 0: return
        p = self.project.pitches[row]
        self.start.setValue(p.start); self.end.setValue(p.end)
        self.inning.setValue(p.inning); self.number.setValue(p.number)
        self.status.setCurrentIndex(self.status.findData(p.status)); self.rule.setCurrentText(p.rule); self.notes.setText(p.notes)

    def preview(self):
        self.frame_request += 1
        p = self.current_pitch()
        self.seek(round(p.start * 1000)); self.preview_end = p.end
        self.video.show(); self.frame_image.hide(); self.player.play()

    def sync(self):
        self.project.player = self.player_name.text()
        self.project.game_date = self.date.text(); self.project.expected_count = self.expected.value() or None
        self.project.name = f'{self.project.player} {self.project.game_date}'

    def save(self):
        self.sync()
        path, _ = QFileDialog.getSaveFileName(self, '프로젝트 저장', 'timeline.json', 'JSON (*.json)')
        if path:
            if self.project.source_file and Path(path).resolve() == Path(self.project.source_file).resolve():
                raise ValueError('원본 경로에 저장할 수 없습니다')
            self.project.save(path); self.dirty = False

    def can_discard(self):
        return not self.dirty or QMessageBox.question(self, '변경사항', '저장하지 않은 변경사항을 버리시겠습니까?') == QMessageBox.Yes

    def load(self):
        if self.tasks: raise ValueError('영상 분석이 끝난 뒤 프로젝트를 불러오세요')
        if not self.can_discard(): return
        path, _ = QFileDialog.getOpenFileName(self, '프로젝트 불러오기', '', 'JSON (*.json)')
        if not path: return
        project = Project.load(path)
        self.player.stop(); self.source = None; self.metadata = {}; self.project = project
        self.player_name.setText(project.player); self.date.setText(project.game_date)
        self.expected.setValue(project.expected_count or 0)
        self.refresh(); self.dirty = False
        if project.source_file:
            self.source_info.setText(project.source_file)
            if Path(project.source_file).is_file(): self.request_source(project.source_file)
            else: QMessageBox.warning(self, '원본 경로 확인', '원본을 찾을 수 없습니다. 원본 경로 재연결 버튼으로 같은 영상을 선택하세요.')
        else:
            self.source_info.setText('선택한 원본 영상이 없습니다')

    def report(self):
        self.sync()
        snapshot = deepcopy(self.project)
        self.task(lambda: review(snapshot), lambda report: QMessageBox.information(self, '검증 보고서 — 완전성 보장 아님', json.dumps(report, ensure_ascii=False, indent=2)))

    def export(self):
        if self.worker and self.worker.isRunning(): raise ValueError('이미 렌더링 중입니다')
        self.sync()
        destination, _ = QFileDialog.getSaveFileName(self, '최종 MP4 저장', output_name(self.project), 'MP4 영상 (*.mp4)')
        if not destination: return
        self.progress.setValue(0)
        self.worker = RenderWorker(self.project, destination, self.keep_clips.isChecked())
        self.worker.progress.connect(self.progress.setValue)
        self.worker.completed.connect(lambda path: QMessageBox.information(self, '출력 완료', path))
        self.worker.failed.connect(lambda message: QMessageBox.critical(self, '렌더링 실패', message))
        self.worker.start()

    def detection_info(self):
        QMessageBox.information(self, '자동 탐색 미구현', '현재는 투구 시작·종료를 직접 지정하고 검수하는 버전입니다. 실제 투구 인식 모델과 정확도는 아직 검증되지 않았습니다. 외부로 영상을 전송하지 않습니다.')

    def closeEvent(self, event):
        if self.tasks or (self.worker and self.worker.isRunning()):
            QMessageBox.warning(self, '렌더링 중', '영상 처리가 끝난 뒤 종료하세요.'); event.ignore(); return
        if self.can_discard(): self.player.stop(); event.accept()
        else: event.ignore()


def main():
    log_path = configure_logging()
    app = QApplication(sys.argv)
    try:
        tool('ffmpeg'); tool('ffprobe')
    except FileNotFoundError as exc:
        logging.exception('Bundled tools unavailable')
        QMessageBox.critical(None, '포터블 파일 확인', str(exc))
        return 1
    window = Window()
    window.statusBar().showMessage(f'로그: {log_path}')
    window.show()
    return app.exec()
