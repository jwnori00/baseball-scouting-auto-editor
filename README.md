# Baseball Scouting Auto Editor v0.2.0

**원본 영상 하나 → 투구 구간 지정·검수 → 최종 MP4 하나**로 작업하는 야구 스카우팅 편집기입니다.
기존 PySide6·FFmpeg 편집 엔진과 포터블 패키징을 유지하고 단일 영상 중심으로 개편했습니다.
자동 투구 시작·종료 탐색은 최종 목표이며 **현재 미구현**입니다. 직접 지정한 구간만 편집합니다.

첫 작업 대상은 2026-08-18 LMB 경기의 Daniel Martínez입니다. 원본은 Windows PC에서
보관하며 클라우드나 GitHub에 업로드하지 않습니다. 다른 영상은 현재 작업을 저장한 뒤 별도 프로젝트로 작업합니다.

## 일반 사용자: 설치 없이 실행

1. [Windows portable](https://github.com/jwnori00/baseball-scouting-auto-editor/actions/workflows/windows-portable.yml)에서
   **성공한 실행**의 `BaseballScoutingEditor-Windows-x64` Artifact를 다운로드합니다.
2. Artifact ZIP 안의 `BaseballScoutingEditor-Windows-x64.zip`을 꺼내 전체 압축을 해제합니다.
3. `BaseballScoutingEditor/BaseballScoutingEditor.exe`를 더블클릭합니다.

Python·FFmpeg·FFprobe·pip·가상환경 설치가 필요 없습니다. `setup_windows.bat`이나
`run.bat`은 일반 사용자용 실행 절차가 아닙니다. EXE만 복사하지 말고 `_internal`, `licenses`,
`corresponding-source`를 포함한 폴더 전체를 유지하세요. 지원 대상은 Windows 10 22H2 / Windows 11 x64입니다.
Private 저장소의 다운로드에는 저장소 접근 권한이 필요합니다.

워크플로우가 존재하는 것과 Windows 빌드 성공은 다릅니다. 해당 실행의 성공 상태와
`Windows-build-evidence` 보고서를 확인하세요. 아직 확인하지 못한 EXE·실제 사용자 PC의 실행을
성공했다고 간주하지 않습니다. 서명 상태는 배포본의 `signature-report.json`에 기록됩니다.
현재 코드 서명 인증서는 설정하지 않았으며 SmartScreen 경고가 표시될 수 있습니다.

## 투구 3~5개 시험 편집

1. **원본 영상 선택**으로 파일 하나를 선택하고 **대상 투수 이름·경기 날짜**를 입력합니다.
2. 재생/일시정지·슬라이더·앞뒤 1프레임 버튼으로 투구를 찾습니다.
   재생 코덱 문제가 있으면 **FFmpeg 프레임**으로 정지 화면을 확인합니다.
3. 시작 장면에서 **현재 위치 → 시작**, 종료 장면에서 **현재 위치 → 종료**를 누릅니다.
   시작·종료 초 값도 직접 수정할 수 있습니다.
4. 이닝·투구 번호·종료 규칙을 입력하고 **투구 추가**를 누릅니다.
5. 목록에서 선택해 **투구 구간 미리보기**로 확인합니다. 수정 후 **선택 투구 수정 적용**을 누릅니다.
   확인한 투구의 검토 상태를 **검수 완료**로 바꾸고 수정 적용합니다.
6. 3~5개를 반복하고 **프로젝트 저장**으로 JSON을 저장합니다. 불러오기로 이어서 작업할 수 있습니다.
7. **검증 보고서**에서 미검수·시간 범위·같은 영상 안의 중복 컷·투구 번호 및 순서를 확인합니다.
8. **최종 MP4 저장**에서 위치와 이름을 지정합니다. 기본 이름은
   `선수이름_YYYYMMDD_Scouting.mp4`입니다(예: `Daniel_Martínez_20260818_Scouting.mp4`).

기본 출력은 최종 MP4 **하나**입니다. 병합용 중간 클립은 임시로 만들고 작업 후 정리합니다.
**투구별 MP4도 저장**을 선택하면 `최종파일명_클립/` 폴더에 개별 투구도 보관합니다.
기존 파일·클립 폴더는 덮어쓰지 않습니다. 실패한 기본 출력은 불완전한 최종 MP4를 남기지 않습니다.
클립 선택 출력 중 저장 오류가 나면 일부 클립 폴더가 남을 수 있으나 최종 MP4는 게시하지 않습니다.

다른 원본을 선택하면 컷 목록 초기화 전에 확인합니다. 취소하면 현재 작업을 유지합니다.
같은 영상의 위치만 바뀌었다면 **원본 경로 재연결**을 사용하세요. 재연결한 컷은 다시 검수해야 합니다.
여러 원본 등록·파일 연결부 검사·서로 다른 영상 사이의 중복 검사는 제공하지 않습니다.
이전 0.1.0의 단일 영상 JSON은 메모리에서 변환해 불러오며 원래 파일을 수정하지 않습니다.
이전 다중 영상 JSON은 안내와 함께 거부하고 원래 파일을 보존합니다. 영상별 프로젝트로 분리해 사용해야 합니다.

## 한도 없이 Windows PC에서 직접 빌드

GitHub Actions의 **Run workflow도 Actions 한도를 사용**합니다. 한도가 소진됐다면 Windows PC에서
로컬 빌드를 할 수 있습니다. 이 경우 Codex나 GitHub Actions 실행 한도를 사용하지 않습니다.

이 준비는 **프로그램 제작 PC에만** 필요합니다. 완성된 ZIP을 받는 사용자는 설치하지 않습니다.

1. 64비트 Python 3.12(Python Launcher 포함), Git for Windows, [MSYS2](https://www.msys2.org/)를 설치합니다.
2. MSYS2 MINGW64 터미널에서 `pacman -Syu`로 업데이트합니다. 재시작 안내가 나오면 창을 닫고 다시 열어 완료합니다.
3. 저장소 최신 소스를 받습니다. 기존 작업 폴더가 있다면 변경사항을 보존하고 최신 main을 반영하세요.
4. 저장소 폴더에서 PowerShell을 열고 실행합니다:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_windows.ps1
# MSYS2를 다른 경로에 설치한 경우
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_windows.ps1 -MsysRoot 'D:\msys64'
```

ExecutionPolicy 옵션은 해당 PowerShell 프로세스에만 적용됩니다. 조직 정책이 이를 금지하면
정책을 변경하지 말고 관리자에게 승인된 실행 방법을 문의하세요.

스크립트는 빌드 가상환경·의존성·FFmpeg/FFprobe를 준비하고 편집 테스트, PyInstaller 빌드,
실제 EXE 자체검증을 순서대로 수행합니다. 실패 시 ZIP 생성을 중단합니다.
처음에는 컴파일러·Qt 대응 소스 등 큰 다운로드와 컴파일이 있으므로 인터넷과 충분한 디스크 여유가 필요합니다.
기존 ZIP이 있으면 다른 위치에 보관한 후 실행하세요. 덮어쓰지 않습니다.

성공하면 저장소 폴더에 `BaseballScoutingEditor-Windows-x64.zip`과 `.sha256`이 생깁니다.
`build-evidence/portable-test-report.json`에서 실제 EXE 검사 결과를 확인하세요.
직접 실행 파일은 `dist/BaseballScoutingEditor/BaseballScoutingEditor.exe`입니다.
GitHub에 배포할 때는 ZIP 및 체크섬과 `vendor/qt-sources`의 대응 소스를 같은 다운로드 위치에 제공합니다.
로컬 빌드 스크립트를 제공하는 것과 Windows에서 실제 빌드 성공을 확인한 것은 다릅니다.

## 편집 규칙과 검증 한계

일반 투구는 세트에서 손을 모으는 순간 또는 와인드업 시작부터 포수의 반환 송구까지 포함합니다.
인플레이·폭투·주루는 실제 플레이 종료까지, 홈런은 1루/2루 주루까지, 파울플라이는 포구/낙구까지,
포일은 회수까지 포함합니다. 중계에 시작 장면이 없으면 확인 가능한 가장 가까운 장면을 쓰고 메모합니다.
리플레이·카메라 전환을 별도 투구로 계산하지 않습니다.

H.264/AAC로 재인코딩하며 화면 비율·원본 음성을 보존합니다. 음성이 없으면 무음 AAC를 추가합니다.
개별 클립과 최종 MP4의 스트림·길이·전체 디코딩을 검사하고 원본은 수정·삭제하지 않습니다.
기대 투구 수는 **현재 원본 하나**에 대해 사용자가 확인한 개수이며 미확인은 0으로 둡니다.
개수가 일치해도 실제 투구가 모두 포함됐다고 보장하지 않습니다.

프레임 이동은 평균 FPS 기준입니다. VFR·특수 방송 코덱의 프레임 경계, 실제 LMB 경기,
Windows 사용자 PC와 Shotcut 호환성은 별도 검증 대상입니다. 렌더 취소·세밀한 프레임 진행률·자동 저장·
공식 기록 자동 조회·AI 자동 탐색은 미구현입니다. 영상은 외부 AI 서비스로 전송하지 않습니다.
향후 로컬 중계 앵글 후보·투수 구간·OCR·시작/종료 제안을 연결하고 정답 투구 라벨로 누락률과 정밀도를 검증해야 합니다.

## 개발 및 테스트

Python 3.12와 FFmpeg/FFprobe가 있는 개발 환경에서:

```bash
cd /workspace/baseball-scouting-auto-editor
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
# 데스크톱 환경
.venv/bin/python -m gui
# 기존 단일 클립 CLI 유지
.venv/bin/python -m engine --help
```

고정 의존성의 Python 지원 범위는 3.11–3.13입니다. Windows 소스 개발자는 `setup_windows.bat`,
`run.bat`을 사용할 수 있습니다. 포터블 사용자는 이 단계를 생략합니다.
Linux 제한 샌드박스에서는 Qt 오디오 초기화가 차단될 수 있으므로 GUI 테스트는 OS 오디오 접근이
허용된 실행 환경에서 수행합니다. 테스트 영상은 FFmpeg로 생성한 합성 자료만 사용합니다.

- `engine/project.py`: 단일 원본 프로젝트·검수 상태·이전 단일 프로젝트 변환
- `engine/quality.py`: 현재 영상의 시간·중복 컷·투구 순서·검수 확인
- `engine/render.py`: 최종 MP4, 선택 클립, 원본 보호, 중간 파일 정리
- `engine/runtime.py`: 포터블 내장 FFmpeg/FFprobe 절대경로
- `gui/app.py`: 한국어 단일 영상 UI, 백그라운드 영상 처리
- `engine/detection.py`: 향후 후보 탐색 API 계약(검출 구현 없음)

기존 JSON/CSV/MLT 엔진 내보내기도 보존했습니다. 개발자는
`render(project, final_mp4, export_metadata=True)`를 호출하면 선택 클립 폴더에 JSON/CSV/MLT와
검증 보고서를 함께 저장할 수 있습니다. GUI 기본 출력에서는 생성하지 않습니다.
MLT는 개별 클립 상대경로를 참조하므로 폴더 전체를 함께 이동해야 하며 실제 Shotcut 검증은 미완료입니다.

## 포터블 빌드와 배포

`.github/workflows/windows-portable.yml`이 main 푸시·PR·수동 실행에서 `windows-latest`로 빌드합니다.
FFmpeg n7.1.3와 x264를 고정 커밋의 공식 소스에서 빌드하고 libx264/AAC를 검사합니다.
PyInstaller 6.16.0 **onedir**가 Python·PySide6/Qt 플러그인·OpenCV·NumPy·FFmpeg·FFprobe와 런타임을 수집합니다.
빌드 의존성은 `requirements-build.txt`, 설정은 `BaseballScoutingEditor.spec`입니다.

실제 frozen EXE 검증은 Python/FFmpeg를 PATH에서 제거하고 한글·공백 설치/작업 경로에서 실행합니다.
설치 폴더 쓰기를 ACL로 차단한 상태에서 GUI·재생·프레임·JSON 저장/복원·기본 MP4 하나·선택 클립·
디코딩·원본 해시 보존을 검사합니다. GitHub runner 테스트는 깨끗한 사용자 PC 테스트를 대체하지 않습니다.

성공한 실행의 Artifact:

- `BaseballScoutingEditor-Windows-x64`: 최종 ZIP과 SHA256
- `Windows-build-evidence`: 실제 EXE·서명 보고서·Windows 테스트 및 빌드 로그
- `ThirdPartyCorrespondingSources`: Qt/PySide 및 별도 Qt FFmpeg DLL 대응 소스

일반 푸시의 결과 요약과 제한된 로그 사본은 **`ci/windows-evidence` 브랜치**에도 기록합니다.
GitHub API 접근이 없는 개발 환경에서도 Git으로 실제 성공/실패와 Artifact 링크를 확인하기 위한 용도입니다.
main 소스와 별도로 기록하며 PR에서는 결과 브랜치에 쓰지 않습니다.

FFmpeg/x264 소스·빌드 스크립트·GPL 라이선스는 배포 ZIP에 포함합니다. Qt/PySide의 라이선스 본문도 수집하며
LGPL 라이브러리는 교체 가능한 DLL로 배포합니다. 재배포할 때는 대응 소스 Artifact를 같은 다운로드 위치에 제공하고
고지·소스 자료를 보존하세요. 자세한 내용은 `packaging/THIRD_PARTY_NOTICES.md`를 참고하세요.
Private 저장소의 `v*` 태그에서는 ZIP과 대응 소스가 첨부된 초안 릴리스를 생성합니다. 공개 설정은 변경하지 않습니다.

수동 빌드 담당자는 Windows/MSYS2에서 워크플로우와 같은 순서로
`packaging/build_ffmpeg.sh`, `packaging/fetch_qt_sources.py`, PyInstaller spec,
`packaging/collect_notices.py`, `packaging/test_portable.ps1`을 실행합니다.
onefile은 Qt/DLL 임시 추출·백신 오탐·임시 폴더 권한·시작 비용 때문에 이번 버전에서는 제공하거나 검증하지 않습니다.

포터블 설치 폴더에 쓰지 않으며 로그는 `%LOCALAPPDATA%\BaseballScoutingEditor\logs\application.log`에 남습니다.
로그에는 로컬 원본 경로가 포함될 수 있습니다. 코드 서명 상태는 보고서에 기록하며 서명했다고 가정하지 않습니다.
