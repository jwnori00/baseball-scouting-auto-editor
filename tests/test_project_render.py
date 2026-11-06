import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

import pytest

from engine.project import Project, Pitch
from engine.quality import review
from engine.render import render, output_name
from engine.video import probe


@pytest.fixture
def footage(tmp_path):
    path = tmp_path / 'source & one.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=25',
                    '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '3',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(path)], check=True)
    return str(path)


def project_for(source):
    return Project(source_file=source, pitches=[
        Pitch(source, 0.2, 1.2, 1, 1, 'MANUALLY_CONFIRMED'),
        Pitch(source, 1.5, 2.5, 1, 2, 'MANUALLY_CONFIRMED')], expected_count=2)


def test_default_produces_only_final_mp4(footage, tmp_path):
    project = project_for(footage)
    before = hashlib.sha256(open(footage, 'rb').read()).hexdigest()
    progress = []
    output = tmp_path / '한글 출력' / output_name(project)
    assert render(project, output, progress.append) == output
    assert list(output.parent.iterdir()) == [output]
    assert progress[-1] == 100
    metadata = probe(output)
    assert float(metadata['format']['duration']) == pytest.approx(2, abs=.15)
    assert {s['codec_name'] for s in metadata['streams']} >= {'h264', 'aac'}
    assert hashlib.sha256(open(footage, 'rb').read()).hexdigest() == before
    with pytest.raises(FileExistsError): render(project, output)
    with pytest.raises(FileExistsError): render(project, footage)


def test_optional_clips_and_preserved_exporters(footage, tmp_path):
    project = project_for(footage)
    final = render(project, tmp_path / output_name(project), export_metadata=True)
    clips = final.with_name(final.stem + '_클립')
    assert len(list(clips.glob('*.mp4'))) == 2
    assert Project.load(clips / 'timeline.json') == project
    assert len((clips / 'timeline.csv').read_text(encoding='utf-8-sig').splitlines()) == 3
    report = json.loads((clips / 'review_report.json').read_text())
    assert report['output_count'] == 2 and report['outputs_verified']
    assert not report['completeness_verified']
    tree = ET.parse(clips / 'timeline.mlt')
    assert len(tree.findall('.//entry')) == 2
    for resource in tree.findall(".//property[@name='resource']"):
        assert (clips / resource.text).is_file()


def test_review_rejects_invalid_and_unconfirmed(footage, tmp_path):
    project = project_for(footage)
    project.pitches[1] = Pitch(footage, .5, 4, 1, 1)
    issues = '\n'.join(review(project)['issues'])
    assert '중복' in issues and '범위 초과' in issues and 'REVIEW_REQUIRED' in issues
    with pytest.raises(ValueError): render(project, tmp_path / 'bad.mp4')
    assert not (tmp_path / 'bad.mp4').exists()


def test_missing_and_corrupt_sources(tmp_path):
    project = Project(source_file=str(tmp_path / 'missing.mp4'))
    assert 'MISSING_SOURCE' in review(project)['issues'][0]
    corrupt = tmp_path / 'corrupt.mp4'; corrupt.write_bytes(b'broken')
    project.source_file = str(corrupt)
    assert 'MISSING_SOURCE' in review(project)['issues'][0]


def test_silent_source_render(tmp_path):
    source = tmp_path / 'silent.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=size=160x120:rate=30',
                    '-t', '1', '-c:v', 'libx264', str(source)], check=True)
    project = Project(source_file=str(source), pitches=[Pitch(str(source), 0, .5, status='MANUALLY_CONFIRMED')])
    final = render(project, tmp_path / 'out.mp4')
    assert any(s['codec_type'] == 'audio' for s in probe(final)['streams'])


def test_foreign_source_pitch_is_rejected(footage, tmp_path):
    project = project_for(footage)
    project.pitches[1].source_file = str(tmp_path / 'other.mp4')
    with pytest.raises(ValueError, match='원본 영상 하나'): render(project, tmp_path / 'out.mp4')
    with pytest.raises(ValueError): project.save(tmp_path / 'invalid.json')


def test_failed_encoder_leaves_no_partial_output(footage, tmp_path, monkeypatch):
    import importlib
    renderer = importlib.import_module('engine.render')
    def fail(args):
        raise RuntimeError('test encoder error')
    monkeypatch.setattr(renderer, 'run', fail)
    with pytest.raises(RuntimeError, match='encoder error'):
        render(project_for(footage), tmp_path / 'failed' / 'out.mp4')
    assert list((tmp_path / 'failed').iterdir()) == []


def test_project_migration_preserves_legacy_file(footage, tmp_path):
    original = {'name': 'legacy', 'player': 'Daniel Martínez', 'game_date': '2026-08-18',
                'sources': [footage], 'pitches': [], 'version': '0.1.0', 'junctions_reviewed': True}
    path = tmp_path / 'old.json'
    path.write_text(json.dumps(original), encoding='utf-8')
    before = path.read_bytes()
    project = Project.load(path)
    assert project.source_file == footage and project.version == '0.2.0'
    assert path.read_bytes() == before
    original['sources'].append('part2.mp4')
    path.write_text(json.dumps(original), encoding='utf-8')
    before = path.read_bytes()
    with pytest.raises(ValueError, match='다중 영상'): Project.load(path)
    assert path.read_bytes() == before


def test_output_name_supports_korean_and_windows_safety():
    assert output_name(Project(player='김 투수')) == '김_투수_20260818_Scouting.mp4'
    assert '/' not in output_name(Project(player='A/B:C'))
    with pytest.raises(ValueError): output_name(Project(player='  '))
