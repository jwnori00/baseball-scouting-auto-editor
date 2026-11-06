"""Review aids do not prove every real pitch was captured."""
from pathlib import Path
import math
import subprocess
from .video import probe


def review(project):
    issues, durations = [], {}
    for source in project.sources:
        try:
            durations[source] = float(probe(source)['format']['duration'])
        except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError, StopIteration) as exc:
            issues.append(f'MISSING_SOURCE: {source}: {exc}')
    seen = set()
    previous = (0, 0)
    for i, p in enumerate(project.pitches):
        if p.inning < 1 or p.number < 1:
            issues.append(f'잘못된 이닝/투구 번호: 컷 {i+1}')
        key = (p.inning, p.number)
        if key in seen:
            issues.append(f'중복 투구 번호: {key}')
        if key < previous:
            issues.append(f'투구 순서 검토: {key}')
        seen.add(key)
        previous = key
        if not all(math.isfinite(t) for t in (p.start, p.end)) or not 0 <= p.start < p.end:
            issues.append(f'잘못된 시간: 컷 {i+1}')
        if p.source_file not in durations:
            issues.append(f'MISSING_SOURCE: 컷 {i+1}')
        elif p.end > durations[p.source_file] + 0.001:
            issues.append(f'원본 범위 초과: 컷 {i+1}')
        if p.status != 'MANUALLY_CONFIRMED':
            issues.append(f'{p.status}: 컷 {i+1}')
        for q in project.pitches[:i]:
            if p.source_file == q.source_file and max(p.start, q.start) < min(p.end, q.end):
                issues.append(f'중복 구간: 컷 {i+1} / 투구 {q.number}')
    if project.expected_count is not None and len(project.pitches) != project.expected_count:
        issues.append('기대 투구 수와 목록 개수 불일치')
    if len(project.sources) > 1 and not project.junctions_reviewed:
        issues.append('원본 파일 연결부의 중복/누락은 수동 검토 필요')
    return {'issues': issues, 'pitch_count': len(project.pitches),
            'expected_count': project.expected_count,
            'completeness_verified': False}
