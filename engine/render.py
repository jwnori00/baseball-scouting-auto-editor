"""Single-source rendering with temporary intermediates and optional clips."""
from pathlib import Path
from .runtime import media_run
from fractions import Fraction
from datetime import date
import re
import os
import shutil
import logging
import tempfile
import xml.etree.ElementTree as ET
from .video import probe
from .project import atomic_json
from .quality import review


def run(args):
    result = media_run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:])


def output_name(project):
    """Preserve Korean/Unicode player names while removing Windows filename hazards."""
    player = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', project.player).strip(' .')
    player = re.sub(r'\s+', '_', player)
    if not player:
        raise ValueError('대상 투수 이름을 입력하세요')
    try:
        stamp = date.fromisoformat(project.game_date).strftime('%Y%m%d')
    except ValueError as exc:
        raise ValueError('경기 날짜를 YYYY-MM-DD 형식으로 입력하세요') from exc
    return player + '_' + stamp + '_Scouting.mp4'


def publish(source, destination):
    """Publish without overwriting any existing file, including a concurrent writer."""
    try:
        os.link(source, destination)
    except FileExistsError:
        raise
    except OSError:
        with open(source, 'rb') as reader, open(destination, 'xb') as writer:
            try:
                shutil.copyfileobj(reader, writer)
            except BaseException:
                writer.close()
                Path(destination).unlink(missing_ok=True)
                raise


def render(project, destination, progress=lambda value: None, *, keep_clips=False, export_metadata=False):
    """Default output is one MP4. Intermediate clips are always temporary."""
    report = review(project)
    if report['issues']:
        raise ValueError('검증 문제를 먼저 해결하세요:\n' + '\n'.join(report['issues']))
    if not project.pitches:
        raise ValueError('확정한 투구가 없습니다')
    output_name(project)  # Validate player/date before starting expensive encoding.
    destination = Path(destination).resolve()
    if destination.suffix.lower() != '.mp4':
        raise ValueError('출력 파일은 .mp4 확장자를 사용하세요')
    if destination.exists():
        raise FileExistsError('출력 파일이 이미 있습니다. 다른 이름을 선택하세요.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    clips_folder = destination.with_name(destination.stem + '_클립')
    keep_clips = keep_clips or export_metadata
    if keep_clips and clips_folder.exists():
        raise FileExistsError('개별 클립 폴더가 이미 있습니다. 다른 출력 이름을 선택하세요.')
    with tempfile.TemporaryDirectory(prefix='.scouting-', dir=destination.parent) as temporary:
        target = Path(temporary)
        _encode(project, target, progress)
        full = target / 'merged.mp4'
        if keep_clips:
            # Reserve a new folder exclusively; never merge into user files.
            clips_folder.mkdir()
            try:
                for pitch in project.pitches:
                    filename = f'Inning_{pitch.inning:02d}_Pitch_{pitch.number:03d}.mp4'
                    publish(target / filename, clips_folder / filename)
                if export_metadata:
                    project.save(clips_folder / 'timeline.json')
                    project.csv(clips_folder / 'timeline.csv')
                    metadata = probe(full)
                    video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
                    write_mlt([clips_folder / f'Inning_{p.inning:02d}_Pitch_{p.number:03d}.mp4' for p in project.pitches],
                              clips_folder / 'timeline.mlt', int(video['width']), int(video['height']), video['avg_frame_rate'])
                    report.update(output_count=len(project.pitches), outputs_verified=True)
                    atomic_json(clips_folder / 'review_report.json', report)
            except Exception:
                logging.exception('Optional clip export failed; final MP4 has not been published')
                raise
        publish(full, destination)
    progress(100)
    return destination


def _encode(project, target, progress):
    first = probe(project.source_file)
    stream = next(s for s in first['streams'] if s['codec_type'] == 'video')
    height = int(stream['height']) // 2 * 2
    sar = stream.get('sample_aspect_ratio', '1:1').replace(':', '/')
    aspect = float(Fraction(sar)) if sar not in ('N/A', '0/1') else 1
    width = max(2, round(int(stream['width']) * aspect / 2) * 2)
    rate = stream.get('avg_frame_rate', '30/1')
    if rate == '0/0': rate = '30/1'
    files = []
    for i, pitch in enumerate(project.pitches):
        output = target / f'Inning_{pitch.inning:02d}_Pitch_{pitch.number:03d}.mp4'
        source_meta = first
        has_audio = any(s['codec_type'] == 'audio' for s in source_meta['streams'])
        args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n',
                '-ss', str(pitch.start), '-i', pitch.source_file]
        if not has_audio:
            args += ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
        args += ['-t', str(pitch.end-pitch.start), '-map', '0:v:0', '-map', '0:a:0' if has_audio else '1:a:0',
                 '-vf', f'scale=trunc(iw*sar/2)*2:ih,setsar=1,scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
                 '-r', rate, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '48000', '-ac', '2',
                 '-movflags', '+faststart', str(output)]
        run(args)
        check_output(output, pitch.end-pitch.start)
        files.append(output)
        progress(int(90 * (i+1) / len(project.pitches)))
    listing = target / 'concat.txt'
    listing.write_text(''.join(f"file '{p.name}'\n" for p in files), encoding='utf-8')
    full = target / 'merged.mp4'
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n', '-f', 'concat', '-safe', '1',
         '-i', str(listing), '-c', 'copy', '-movflags', '+faststart', str(full)])
    check_output(full, sum(p.end-p.start for p in project.pitches))


def check_output(path, duration):
    metadata = probe(path)
    kinds = {s['codec_type'] for s in metadata['streams']}
    if not {'video', 'audio'} <= kinds or abs(float(metadata['format']['duration']) - duration) > 0.25:
        raise ValueError(f'출력 스트림/길이 검증 실패: {path}')
    run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'])


def write_mlt(files, path, width, height, rate):
    numerator, denominator = rate.split('/') if '/' in rate else (rate, '1')
    fps = float(numerator) / float(denominator)
    root = ET.Element('mlt', producer='tractor', version='7.24.0')
    ET.SubElement(root, 'profile', frame_rate_num=numerator, frame_rate_den=denominator,
                  width=str(width), height=str(height), progressive='1', sample_aspect_num='1', sample_aspect_den='1',
                  display_aspect_num=str(width), display_aspect_den=str(height), colorspace='709', description='Scouting')
    for i, file in enumerate(files):
        producer = ET.SubElement(root, 'chain', id=f'clip{i}')
        ET.SubElement(producer, 'property', name='resource').text = file.name
        ET.SubElement(producer, 'property', name='mlt_service').text = 'avformat'
    playlist = ET.SubElement(root, 'playlist', id='main')
    ET.SubElement(playlist, 'property', name='shotcut:name').text = 'V1'
    for i, file in enumerate(files):
        frames = round(float(probe(file)['format']['duration']) * fps)
        ET.SubElement(playlist, 'entry', producer=f'clip{i}', **{'in': '0', 'out': str(max(0, frames-1))})
    tractor = ET.SubElement(root, 'tractor', id='tractor', shotcut='1')
    ET.SubElement(tractor, 'property', name='shotcut').text = '1'
    ET.SubElement(tractor, 'track', producer='main')
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)
