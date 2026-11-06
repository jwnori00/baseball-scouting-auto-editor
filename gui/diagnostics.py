"""User-writable diagnostics; never write into the portable installation."""
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys


def configure_logging():
    base = Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.local' / 'state')
    folder = base / 'BaseballScoutingEditor' / 'logs'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'application.log'
    handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=3, encoding='utf-8')
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
    def unhandled(kind, value, traceback):
        logging.critical('Unhandled exception', exc_info=(kind, value, traceback))
        from PySide6.QtWidgets import QApplication, QMessageBox
        if QApplication.instance():
            QMessageBox.critical(None, '프로그램 오류', f'작업 중 오류가 발생했습니다. 프로그램을 다시 실행하세요.\n로그: {path}')
    sys.excepthook = unhandled
    return path


def error_text(exc):
    if isinstance(exc, PermissionError):
        return '파일을 읽거나 저장할 권한이 없습니다. 다른 출력 폴더를 선택하고 파일 사용 여부를 확인하세요.'
    if isinstance(exc, FileNotFoundError):
        return '필요한 파일을 찾을 수 없습니다. 원본 경로를 재연결하거나 포터블 ZIP 전체를 다시 압축 해제하세요.'
    if isinstance(exc, ValueError):
        return str(exc)
    return '영상 처리에 실패했습니다. 원본 재생 여부와 저장 공간을 확인하세요. 자세한 내용은 로그에 기록했습니다.'
