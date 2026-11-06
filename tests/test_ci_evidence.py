"""Exercise the evidence publisher against a local bare Git remote."""
import json
import os
from pathlib import Path
import subprocess
import sys


def test_evidence_preserves_main_and_appends_history(tmp_path):
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'publish_build_evidence.py'
    remote = tmp_path / 'remote.git'
    repo = tmp_path / 'runner'
    def git(*args, cwd=None):
        return subprocess.check_output(['git', *map(str, args)], cwd=cwd, stderr=subprocess.PIPE, text=True).strip()
    git('init', '--bare', remote)
    git('clone', remote, repo)
    git('config', 'user.name', 'Test', cwd=repo)
    git('config', 'user.email', 'test@example.invalid', cwd=repo)
    git('switch', '-c', 'main', cwd=repo)
    (repo / 'source.txt').write_text('preserve main')
    git('add', 'source.txt', cwd=repo); git('commit', '-m', 'Original', cwd=repo)
    git('push', 'origin', 'main', cwd=repo)
    commit = git('rev-parse', 'HEAD', cwd=repo)
    evidence = tmp_path / 'evidence'; evidence.mkdir()
    (evidence / 'portable-test-report.json').write_text('{"passed":true}')
    (evidence / 'unwanted.txt').write_text('do not publish')
    env = {**os.environ, 'GITHUB_ACTIONS': 'true', 'GITHUB_SHA': commit, 'GITHUB_RUN_ID': '123',
           'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_SERVER_URL': 'https://github.com',
           'GITHUB_REPOSITORY': 'example/test', 'BUILD_RESULT': 'success',
           'BUILD_ARTIFACT_URL': 'https://github.com/example/test/actions/runs/123/artifacts/456',
           'EVIDENCE_PATH': str(evidence)}
    for attempt in ('1', '2'):
        env['GITHUB_RUN_ATTEMPT'] = attempt
        subprocess.run([sys.executable, str(script)], cwd=repo, env=env, check=True, capture_output=True)
    assert git('rev-parse', 'refs/heads/main', cwd=remote) == commit
    folder = f'reports/{commit}/123-2'
    status = json.loads(git('show', f'ci/windows-evidence:{folder}/status.json', cwd=remote))
    assert status['result'] == 'success' and status['artifact_url'].endswith('/456')
    entries = git('ls-tree', '-r', '--name-only', 'ci/windows-evidence', cwd=remote)
    assert '123-1/status.json' in entries and '123-2/status.json' in entries
    assert 'unwanted' not in entries and 'source.txt' not in entries
