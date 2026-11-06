"""Portable, versioned scouting timelines. Times are seconds in each source."""
from dataclasses import dataclass, field, asdict
from pathlib import Path
import csv
import json
import math
import os
import tempfile

STATUSES = ('AUTO_CANDIDATE', 'MANUALLY_CONFIRMED', 'REVIEW_REQUIRED', 'MISSING_SOURCE')
RULES = ('일반 투구', '인플레이', '홈런', '파울플라이', '포일', '폭투/주루', '중계 시작 누락')

@dataclass
class Pitch:
    source_file: str
    start: float
    end: float
    inning: int = 1
    number: int = 1
    status: str = 'REVIEW_REQUIRED'
    rule: str = '일반 투구'
    notes: str = ''

@dataclass
class Project:
    name: str = 'Daniel Martinez 20260818'
    player: str = 'Daniel Martínez'
    game_date: str = '2026-08-18'
    source_file: str = ''
    pitches: list[Pitch] = field(default_factory=list)
    expected_count: int | None = None
    version: str = '0.2.0'

    def save(self, path):
        self.validate_source()
        if self.source_file and Path(path).resolve() == Path(self.source_file).resolve():
            raise ValueError('원본 영상 경로에는 프로젝트를 저장할 수 없습니다')
        atomic_json(path, asdict(self))

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if data.get('version') == '0.1.0':
            sources = data.pop('sources', [])
            if len(sources) > 1:
                raise ValueError('이전 다중 영상 프로젝트입니다. 원본 파일은 변경하지 않았습니다. 기존 버전에서 영상별 프로젝트로 나눠 저장하세요.')
            data['source_file'] = sources[0] if sources else ''
            data.pop('junctions_reviewed', None)
            data['version'] = '0.2.0'
        if data.get('version') != '0.2.0':
            raise ValueError('지원하지 않는 프로젝트 버전')
        data['pitches'] = [Pitch(**p) for p in data['pitches']]
        project = cls(**data)
        project.validate_source()
        for p in project.pitches:
            if p.status not in STATUSES or not all(math.isfinite(t) for t in (p.start, p.end)):
                raise ValueError('잘못된 컷 데이터')
        return project

    def validate_source(self):
        if self.pitches and not self.source_file:
            raise ValueError('원본 영상 하나를 선택하세요')
        if any(Path(p.source_file).resolve() != Path(self.source_file).resolve() for p in self.pitches):
            raise ValueError('모든 투구는 선택한 원본 영상 하나에 속해야 합니다')

    def csv(self, path):
        with open(path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(Pitch.__dataclass_fields__))
            writer.writeheader()
            writer.writerows(asdict(p) for p in self.pitches)


def atomic_json(path, data):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
