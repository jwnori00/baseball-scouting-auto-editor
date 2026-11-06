import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

import pytest

from engine.project import Project, Pitch
from engine.quality import review
from engine.render import render
from engine.video import probe


@pytest.fixture
def footage(tmp_path):
    path = tmp_path / "source & one.mp4"
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=25',
                    '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '3',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(path)], check=True)
    return str(path)


def project_for(source):
    return Project(sources=[source], pitches=[
        Pitch(source, 0.2, 1.2, 1, 1, 'MANUALLY_CONFIRMED'),
        Pitch(source, 1.5, 2.5, 1, 2, 'MANUALLY_CONFIRMED')], expected_count=2)


def test_complete_render_and_persistence(footage, tmp_path):
    project = project_for(footage)
    before = hashlib.sha256(open(footage, 'rb').read()).hexdigest()
    progress = []
    target = render(project, tmp_path / 'output', progress.append)
    assert progress[-1] == 100
    assert Project.load(target / 'timeline.json') == project
    assert len((target / 'timeline.csv').read_text(encoding='utf-8-sig').splitlines()) == 3
    report = json.loads((target / 'review_report.json').read_text())
    assert report['output_count'] == 2 and report['outputs_verified']
    assert not report['completeness_verified']
    full = probe(target / 'Daniel_Martinez_20260818_FULL.mp4')
    assert float(full['format']['duration']) == pytest.approx(2, abs=.15)
    assert {s['codec_name'] for s in full['streams']} >= {'h264', 'aac'}
    tree = ET.parse(target / 'Daniel_Martinez_20260818.mlt')
    assert len(tree.findall('.//entry')) == 2
    for resource in tree.findall(".//property[@name='resource']"):
        assert (target / resource.text).is_file()
    assert hashlib.sha256(open(footage, 'rb').read()).hexdigest() == before


def test_review_rejects_invalid_and_unconfirmed(footage, tmp_path):
    project = project_for(footage)
    project.pitches[1] = Pitch(footage, .5, 4, 1, 1)
    issues = '\n'.join(review(project)['issues'])
    assert '중복' in issues and '범위 초과' in issues and 'REVIEW_REQUIRED' in issues
    with pytest.raises(ValueError): render(project, tmp_path / 'bad')
    assert not (tmp_path / 'bad').exists()


def test_missing_and_corrupt_sources(tmp_path):
    project = Project(sources=[str(tmp_path / 'missing.mp4')])
    assert 'MISSING_SOURCE' in review(project)['issues'][0]
    corrupt = tmp_path / 'corrupt.mp4'; corrupt.write_bytes(b'broken')
    project.sources = [str(corrupt)]
    assert 'MISSING_SOURCE' in review(project)['issues'][0]


def test_silent_source_render(tmp_path):
    source = tmp_path / 'silent.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=size=160x120:rate=30',
                    '-t', '1', '-c:v', 'libx264', str(source)], check=True)
    project = Project(sources=[str(source)], pitches=[Pitch(str(source), 0, .5, status='MANUALLY_CONFIRMED')])
    target = render(project, tmp_path / 'out')
    assert any(s['codec_type'] == 'audio' for s in probe(target / 'Inning_01_Pitch_001.mp4')['streams'])


def test_mixed_sources_require_junction_review_and_normalize(footage, tmp_path):
    other = tmp_path / 'part2.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=256x144:rate=30',
                    '-t', '1', '-c:v', 'libx264', str(other)], check=True)
    project = Project(sources=[footage, str(other)], pitches=[
        Pitch(footage, 0, .6, 1, 1, 'MANUALLY_CONFIRMED'),
        Pitch(str(other), 0, .6, 1, 2, 'MANUALLY_CONFIRMED')])
    with pytest.raises(ValueError, match='연결부'): render(project, tmp_path / 'out')
    project.junctions_reviewed = True
    target = render(project, tmp_path / 'out')
    for name in ('Inning_01_Pitch_001.mp4', 'Inning_01_Pitch_002.mp4'):
        streams = probe(target / name)['streams']
        video = next(s for s in streams if s['codec_type'] == 'video')
        assert (video['width'], video['height'], video['avg_frame_rate']) == (320, 240, '25/1')


def test_failed_encoder_leaves_diagnostic(footage, tmp_path, monkeypatch):
    import importlib
    renderer = importlib.import_module('engine.render')
    def fail(args):
        raise RuntimeError('test encoder error')
    monkeypatch.setattr(renderer, 'run', fail)
    with pytest.raises(RuntimeError, match='encoder error'):
        render(project_for(footage), tmp_path / 'failed')
    error_file = next((tmp_path / 'failed').glob('render_*/render_error.json'))
    assert json.loads(error_file.read_text())['complete'] is False
    assert not list((tmp_path / 'failed').glob('render_*/*FULL.mp4'))
