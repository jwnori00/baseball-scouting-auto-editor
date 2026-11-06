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
    sources: list[str] = field(default_factory=list)
    pitches: list[Pitch] = field(default_factory=list)
    expected_count: int | None = None
    version: str = '0.1.0'
    junctions_reviewed: bool = False

    def save(self, path):
        atomic_json(path, asdict(self))

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if data.get('version') != '0.1.0':
            raise ValueError('지원하지 않는 프로젝트 버전')
        data['pitches'] = [Pitch(**p) for p in data['pitches']]
        project = cls(**data)
        for p in project.pitches:
            if p.status not in STATUSES or not all(math.isfinite(t) for t in (p.start, p.end)):
                raise ValueError('잘못된 컷 데이터')
        return project

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
