# Baseball Scouting Auto Editor v0.1.0

야구 스카우팅용 **반자동 투구 편집기**입니다. Python 3.11+, FFmpeg/FFprobe,
OpenCV, NumPy, PySide6를 사용합니다. 첫 작업 대상은 LMB **2026-08-18 Daniel Martínez**
경기의 Part 1입니다. 소속팀·등판 이닝·투구 수는 확인되지 않았으며 추정하지 않습니다.
실제 경기영상은 Windows PC에 보관하고 클라우드나 GitHub에 업로드하지 않습니다.

## 일반 사용자: Windows 포터블 실행

성공한 [Windows portable 빌드](https://github.com/jwnori00/baseball-scouting-auto-editor/actions/workflows/windows-portable.yml)의
Artifacts에서 `BaseballScoutingEditor-Windows-x64`를 다운로드합니다.
Artifact 포장 ZIP 안의 **`BaseballScoutingEditor-Windows-x64.zip`**을 꺼내 전체 압축을 해제하고,
`BaseballScoutingEditor/BaseballScoutingEditor.exe`를 더블클릭합니다.

**Python·FFmpeg·FFprobe·pip·가상환경을 설치할 필요가 없습니다.**
일반 사용자는 `setup_windows.bat`이나 `run.bat`을 실행하지 않습니다.
EXE만 복사하지 말고 `_internal`, `licenses`, `corresponding-source` 등 폴더 전체를 함께 보관하세요.
지원 대상은 Windows 10 22H2 / Windows 11 x64입니다. GitHub Private 저장소의
Artifact는 해당 저장소 접근 권한이 있는 사용자만 다운로드할 수 있습니다.

포터블 빌드는 Python 런타임·PySide6/Qt 플러그인·OpenCV·NumPy·FFmpeg·FFprobe를 포함합니다.
내장 도구를 절대경로로 찾아 실행하므로 Windows PATH에 의존하지 않습니다.
출력과 프로젝트는 사용자가 선택한 폴더에 저장하고 로그는
`%LOCALAPPDATA%\BaseballScoutingEditor\logs\application.log`에 저장합니다.
한글·공백 경로를 지원하며 설치 폴더에 쓰지 않습니다. 로그에는 원본 파일 경로가 포함될 수 있습니다.

배포본은 현재 코드 서명을 설정하지 않았습니다. 실제 서명 상태는 ZIP의
`signature-report.json`에 기록합니다. SmartScreen 경고가 나올 수 있으므로
출처·ZIP SHA256과 조직 정책을 확인하세요. 서명 인증서가 있다고 가정하지 않습니다.

Windows Actions는 합성 영상과 실제 frozen EXE로 검증하도록 구성되어 있습니다.
**워크플로우 파일이 존재하는 것과 빌드 성공은 다릅니다.** 다운로드 전 해당 실행의 성공 상태와
`Windows-build-evidence/portable-test-report.json`을 확인하세요. 실제 사용자 Windows PC,
실제 LMB 영상 및 Shotcut에서 검증했다는 의미는 아닙니다.

## Part 1에서 투구 3~5개 시험 편집

1. **로컬 영상 추가**로 Windows에 보관한 Part 1을 선택합니다. 영상 전체를 메모리에
   적재하지 않으며 원본을 수정하지 않습니다. 왼쪽 목록과 메타데이터를 확인합니다.
2. 재생/일시정지와 탐색 슬라이더로 등판 구간을 찾습니다. 앞뒤 1프레임 버튼으로
   위치를 미세 조정합니다. 재생 코덱 문제가 있으면 **FFmpeg 프레임**으로 정지 화면을 확인합니다.
3. 세트 포지션에서 손을 모으는 순간 또는 와인드업 시작에 **현재 위치 → 시작**을 누릅니다.
4. 포수의 반환 송구까지 본 뒤 **현재 위치 → 종료**를 누릅니다. 인플레이·폭투·주루는 실제
   플레이 종료까지, 홈런은 1루/2루 주루까지, 파울플라이는 포구/낙구까지, 포일은 회수까지 포함합니다.
   중계에 시작 동작이 없으면 가장 가까운 확인 장면을 사용하고 메모합니다.
5. 이닝·투구 번호·규칙·메모를 입력합니다. **컷 추가** 후 목록에서 선택하여
   **선택 컷 미리보기**로 확인합니다. 수정 후에는 **선택 컷 수정 적용**을 누릅니다.
6. 확인한 컷의 상태를 `MANUALLY_CONFIRMED`로 바꾸고 수정 적용합니다. 3~5개를 반복합니다.
   리플레이·카메라 전환을 별도 투구로 계산하지 마세요. 누락·불확실한 컷은
   `REVIEW_REQUIRED` 또는 `MISSING_SOURCE`로 남기며 확인 전에는 출력하지 않습니다.
7. **프로젝트 저장**으로 JSON을 저장합니다. **프로젝트 불러오기**로 이어서 작업할 수 있습니다.
   영상 이동 후에는 왼쪽 원본 목록을 선택하고 **선택 원본 경로 재연결**을 사용합니다.
   재연결한 컷은 다시 검토해야 합니다.
8. **검증 보고서**에서 중복 시간·번호·순서·원본 범위·미확정 상태를 확인합니다.
   투구 수 입력은 현재 목록이 아닌 해당 작업의 기대 전체 개수입니다. 미확인이면 0으로 둡니다.
9. **영상 출력**에서 출력 폴더를 지정합니다. 기존 파일을 덮어쓰지 않는 고유 `render_...`
   하위 폴더를 생성합니다. 진행률은 클립 완료 기준이며 백그라운드에서 렌더링합니다.

Part 2·3도 목록에 추가할 수 있습니다. 컷 시간은 각 원본 기준입니다. 파일 사이의
같은 투구·누락은 자동 판별하지 않습니다. 각 파일의 끝/시작을 목록에서 전환해 검토하고
**파일 연결부 중복·누락 수동 확인**을 체크해야 다중 원본 출력이 가능합니다.
새 원본을 추가하면 이 확인은 해제됩니다.

## 출력물

- `Inning_01_Pitch_001.mp4` 등 개별 투구 MP4
- `Daniel_Martinez_20260818_FULL.mp4` 전체 병합본
- `Daniel_Martinez_20260818.mlt` Shotcut용 프로젝트 초안
- `timeline.json`, `timeline.csv`, `review_report.json`

선수·날짜를 변경하면 전체 MP4/MLT 파일명도 변경됩니다. 원본은 읽기 전용으로 사용합니다.
H.264/AAC로 재인코딩하며 첫 원본의 프레임레이트와 화면 규격으로 통일하고,
다른 화면 비율은 여백으로 보존합니다. 음성이 있으면 유지하고, 없는 원본에는 무음 AAC를 추가합니다.
출력 영상의 길이·영상/음성 스트림 및 전체 디코딩을 검사합니다. 실패 시
`render_error.json`과 부분 출력이 남으며 완료로 취급하지 않습니다.

MLT는 **같은 폴더의 개별 MP4를 상대경로로 참조**합니다. 이동 시 출력 폴더 전체를
복사하고, 경로가 끊기면 Shotcut에서 재연결하세요. 실제 Shotcut에서 열기·재생은
검증하지 않았습니다. XML/OTIO와 iMovie 전용 프로젝트 출력은 지원하지 않습니다.

## 개발자용 소스 실행

포터블 사용자는 이 단계를 건너뜁니다. 소스 개발자는 Python 3.12와 FFmpeg/FFprobe가 필요합니다.
Windows에서는 FFmpeg bin을 PATH에 추가한 뒤 `setup_windows.bat`, `run.bat`을 사용할 수 있습니다.
고정 의존성은 Python 3.11–3.13 대상입니다.

## 개발 및 테스트

```bash
cd /workspace/baseball-scouting-auto-editor
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
# 데스크톱이 있는 Linux에서 실행
.venv/bin/python -m gui
# 기존 엔진 CLI도 유지
.venv/bin/python -m engine --help
```

Windows 테스트: `.venv\Scripts\python.exe -m pytest -q`.
클라우드 기본 버전은 Python 3.12.14, FFmpeg/FFprobe 7.1.5입니다.
Qt 멀티미디어 초기화에는 OS 오디오 접근이 필요할 수 있습니다. 제한된 샌드박스에서는
오디오 초기화가 정지할 수 있어 Linux GUI 테스트는 허용된 실행 환경에서 수행합니다.
테스트는 FFmpeg로 생성한 영상만 사용하며 원본 자료나 외부 AI 서비스가 필요하지 않습니다.

## 코드 구조와 현재 한계

- `engine/video.py`: 기존 FFprobe 조회·단일 클립 CLI 어댑터
- `engine/project.py`: 버전 있는 프로젝트, 컷 상태, JSON/CSV 저장
- `engine/quality.py`: 시간·원본·중복·순서·투구 수 검토
- `engine/render.py`: 규격 통일, 개별 인코딩, 병합, 디코딩 검증, MLT
- `engine/detection.py`: 향후 로컬 OCR/영상 모델 후보 API 계약
- `gui/app.py`: Qt 재생, FFmpeg 정지 프레임, 컷 목록, 작업 스레드 렌더링
- `tests/`: 합성 영상 통합 검사와 PySide6 비화면 편집·미리보기 검사

PHASE 1의 반자동 편집을 구현하고 PHASE 2의 기본 검증·내보내기를 포함했습니다.
자동 투구 탐색은 **미구현**이며 버튼에서도 이를 명시합니다. 모델 없이 장면 전환을
투구로 판정하지 않습니다. 향후 로컬 프레임 샘플링·중계 앵글 분류·OCR·등판 구간 후보
제안·수동 승인·실제 라벨 데이터의 누락률/정밀도 평가를 추가해야 합니다.
외부로 영상을 보내는 기능은 없습니다.

시간은 초 단위로 저장합니다. 기본 프레임 이동은 평균 FPS 기준이며 VFR·방송 코덱의
정확한 프레임 경계는 실제 Windows 원본으로 추가 검증해야 합니다. 메타데이터·FFmpeg 정지 프레임·검증 보고서·렌더링은 백그라운드 스레드에서 처리합니다. 렌더 취소,
상세 프레임 진행률, 프로젝트 자동 저장, 자동 누락/파일 간 동일 투구 인식은 미구현입니다.
공식 투구 기록 자동 조회도 없습니다. 개수가 일치해도 모든 투구 수집을 보장하지 않으며
보고서의 `completeness_verified`는 항상 false입니다.


## Windows 빌드·검증·재배포

`.github/workflows/windows-portable.yml`은 main 푸시·Pull Request·수동 실행 시
`windows-latest`에서 Python 3.12 x64, MSYS2 도구를 준비합니다. FFmpeg n7.1.3 및 x264의
고정 커밋에서 GPL Windows 실행 파일을 빌드하고 실제 libx264/AAC 인코딩을 검사합니다.
대응 소스가 누락된 사전 빌드 대신 공식 소스 기반 빌드를 선택했습니다.
PyInstaller 6.16.0 onedir로 `BaseballScoutingEditor.exe`를 생성합니다.

검증은 DLL·Qt Windows 플러그인·서명 상태 확인, 기존 편집 테스트, frozen EXE 자체검증을 포함합니다.
EXE 자체검증은 Python/FFmpeg를 PATH에서 제거하고 한글·공백이 있는 설치/작업 경로에서 실행합니다.
설치 폴더의 쓰기를 ACL로 차단한 상태에서 GUI 표시·재생·정지 프레임·프로젝트 저장/복원·개별 추출·병합·
OpenCV 디코딩과 원본 해시 보존을 확인합니다. 설치 폴더 파일이 변경되지 않았는지도 검사합니다.
이는 개발 도구가 사전 설치된 GitHub 호스팅 Windows runner의 테스트이며 완전히 깨끗한 사용자 PC 검증은 아닙니다.

성공한 실행은 다음 Artifact를 제공합니다.

- `BaseballScoutingEditor-Windows-x64`: 최종 ZIP 및 SHA256 파일
- `Windows-build-evidence`: EXE 테스트·서명 보고서·로그·FFmpeg 빌드 정보
- `ThirdPartyCorrespondingSources`: Qt/PySide와 Qt의 별도 FFmpeg DLL이 있다면 그 대응 소스

FFmpeg/x264 소스·빌드 스크립트와 라이선스는 포터블 ZIP에도 동봉합니다.
Qt/PySide 라이선스 본문은 공식 대응 소스에서 수집합니다. LGPL 라이브러리는 DLL 교체가 가능하도록
동적 배포하며 수정 디버깅을 위한 역공학을 해당 라이선스가 허용하는 범위에서 제한하지 않습니다.
재배포할 때에는 포터블 ZIP과 `ThirdPartyCorrespondingSources`를 같은 다운로드 위치에 제공하고
고지·소스·라이선스 자료를 유지하세요. 자세한 내용은 `packaging/THIRD_PARTY_NOTICES.md`를 확인하세요.

Private 저장소에서 `v*` 태그를 푸시하면 빌드 성공 후 ZIP과 대응 소스가 첨부된 **초안 릴리스**를 생성합니다.
저장소 공개 설정은 변경하지 않으며, 공개 저장소에서는 이 릴리스 작업을 실행하지 않습니다.
태그·릴리스는 자동으로 지금 생성하지 않습니다.

수동 빌드 담당자는 워크플로우와 동일한 Windows/MSYS2 환경에서
`bash packaging/build_ffmpeg.sh`, `python packaging/fetch_qt_sources.py`,
`python -m PyInstaller --noconfirm --clean BaseballScoutingEditor.spec`,
`python packaging/collect_notices.py`, `./packaging/test_portable.ps1` 순서로 실행합니다.
빌드 의존성은 `requirements-build.txt`입니다.

초기 배포는 onedir입니다. onefile은 Qt/DLL 임시 추출 시간, 백신 오탐, 임시 폴더 권한과
대용량 번들 비용이 있어 이번 버전에서 제공하거나 검증하지 않았습니다.
자동 투구 인식은 여전히 미구현이며 향후 실제 정답 투구 구간으로 정확도를 검증해야 합니다.
