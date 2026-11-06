"""CI-only: publish actual Windows outcomes using checkout's existing Git auth.

No tokens are read/copied. This runs in a fresh disposable GitHub job after the
Windows build. It never changes main, force-pushes, or publishes source footage.
"""
import json
import os
from pathlib import Path
import subprocess


def git(*args, **kwargs):
    return subprocess.run(['git', *args], check=True, **kwargs)


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('This helper is only for the isolated GitHub Actions evidence job')
    commit = os.environ['GITHUB_SHA']
    run = os.environ['GITHUB_RUN_ID']
    attempt = os.environ['GITHUB_RUN_ATTEMPT']
    evidence = Path(os.environ['EVIDENCE_PATH'])
    branch = 'ci/windows-evidence'
    remote = git('ls-remote', '--heads', 'origin', branch, capture_output=True, text=True)
    if remote.stdout.strip():
        git('fetch', '--depth=1', 'origin', branch)
        git('switch', '--force-create', 'ci-evidence', 'FETCH_HEAD')
    else:
        git('switch', '--orphan', 'ci-evidence')
    folder = Path('reports') / commit / f'{run}-{attempt}'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'status.json').write_text(json.dumps({
        'commit': commit, 'result': os.environ['BUILD_RESULT'],
        'run_url': f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{run}",
        'artifact_url': os.environ.get('BUILD_ARTIFACT_URL', ''),
    }, indent=2), encoding='utf-8')
    allowed = {'portable-test-report.json', 'signature-report.json', 'ffmpeg-build.log',
               'python-tests.log', 'dependencies.log', 'qt-sources.log', 'pyinstaller.log', 'build-version.txt', 'encoders.txt'}
    if evidence.exists():
        for source in evidence.rglob('*'):
            if source.is_file() and source.name in allowed:
                lines = source.read_text(encoding='utf-8', errors='replace').splitlines()
                (folder / source.name).write_text('\n'.join(lines[-250:])[-60000:], encoding='utf-8')
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    git('add', str(folder))
    git('commit', '-m', f'Windows build evidence for {commit[:8]} ({run}-{attempt})')
    git('push', 'origin', f'HEAD:refs/heads/{branch}')


if __name__ == '__main__':
    main()
