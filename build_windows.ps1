#requires -Version 5.1
<# Developer-only local Windows build. Recipients only unzip and open the EXE. #>
param([string]$MsysRoot = 'C:\msys64')
$ErrorActionPreference = 'Stop'
$originalPath = $env:PATH
$originalMsystem = $env:MSYSTEM
$originalRoot = $env:SCOUTING_BUILD_ROOT
$originalQtPlatform = $env:QT_QPA_PLATFORM
Push-Location $PSScriptRoot
try {
    if ([Environment]::OSVersion.Platform -ne 'Win32NT' -or ![Environment]::Is64BitOperatingSystem) {
        throw 'Windows x64 PC에서 실행하세요.'
    }
    $archive = Join-Path $PSScriptRoot 'BaseballScoutingEditor-Windows-x64.zip'
    if (Test-Path $archive) { throw '기존 ZIP을 다른 폴더에 보관한 뒤 다시 빌드하세요. 기존 파일을 덮어쓰지 않습니다.' }
    if (!(Get-Command py -ErrorAction SilentlyContinue)) { throw '빌드 PC에 Python 3.12 (Python Launcher 포함)를 설치하세요.' }
    if (!(Get-Command git -ErrorAction SilentlyContinue)) { throw '빌드 PC에 Git for Windows를 설치하세요.' }
    $bash = Join-Path $MsysRoot 'usr\bin\bash.exe'
    if (!(Test-Path $bash)) { throw "빌드 PC에 MSYS2를 설치하세요. 현재 경로: $MsysRoot. 다른 위치면 -MsysRoot로 지정하세요." }
    & py -3.12 -c 'import sys; assert sys.maxsize > 2**32'
    if ($LASTEXITCODE -ne 0) { throw '64비트 Python 3.12가 필요합니다.' }
    New-Item -ItemType Directory -Force build-evidence | Out-Null
    & py -3.12 -m venv .venv-build
    if ($LASTEXITCODE -ne 0) { throw '빌드 가상환경 생성 실패' }
    $python = Join-Path $PSScriptRoot '.venv-build\Scripts\python.exe'
    & $python -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw '빌드 의존성 설치 실패' }
    & $python -m pip check
    if ($LASTEXITCODE -ne 0) { throw '의존성 검사 실패' }
    $env:MSYSTEM = 'MINGW64'
    $env:SCOUTING_BUILD_ROOT = $PSScriptRoot
    Write-Host 'MSYS2 빌드 패키지를 준비합니다. 처음 실행할 때 시간이 걸립니다.'
    & $bash -lc 'pacman -S --needed --noconfirm git make nasm diffutils mingw-w64-x86_64-gcc mingw-w64-x86_64-pkgconf'
    if ($LASTEXITCODE -ne 0) { throw 'MSYS2 업데이트를 완료한 뒤 다시 실행하세요. MSYS2 MINGW64에서 pacman -Syu를 실행하고 재시작이 필요할 수 있습니다.' }
    $buildCommand = @'
set -euo pipefail
cd -- "$(cygpath -u "$SCOUTING_BUILD_ROOT")"
bash packaging/build_ffmpeg.sh 2>&1 | tee build-evidence/ffmpeg-build.log
'@
    $mediaScript = Join-Path $PSScriptRoot 'build-evidence/local-media-build.sh'
    [IO.File]::WriteAllText($mediaScript, $buildCommand.Replace("`r`n", "`n"), [Text.UTF8Encoding]::new($false))
    & $bash --login $mediaScript
    if ($LASTEXITCODE -ne 0) { throw 'FFmpeg 빌드 실패. build-evidence/ffmpeg-build.log를 확인하세요.' }
    & $python packaging/fetch_qt_sources.py
    if ($LASTEXITCODE -ne 0) { throw '라이선스·대응 소스 준비 실패' }
    $env:PATH = "$PSScriptRoot\vendor\ffmpeg\bin;$originalPath"
    $env:QT_QPA_PLATFORM = 'offscreen'
    & $python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw '편집 기능 테스트 실패' }
    Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    & $python -m PyInstaller --noconfirm --clean BaseballScoutingEditor.spec
    if ($LASTEXITCODE -ne 0) { throw 'EXE 생성 실패' }
    & $python packaging/collect_notices.py
    if ($LASTEXITCODE -ne 0) { throw '라이선스 자료 수집 실패' }
    & "$PSScriptRoot\packaging\test_portable.ps1"
    Compress-Archive -Path dist/BaseballScoutingEditor -DestinationPath $archive
    $hash = (Get-FileHash $archive -Algorithm SHA256).Hash.ToLower()
    "$hash  BaseballScoutingEditor-Windows-x64.zip" | Out-File -Encoding ascii ($archive + '.sha256')
    Write-Host "완료: $archive"
    Write-Host '배포 ZIP을 전체 압축 해제한 뒤 BaseballScoutingEditor.exe를 실행하세요.'
    Write-Host '재배포 시 vendor/qt-sources의 대응 소스도 같은 다운로드 위치에 제공하세요.'
} finally {
    $env:PATH = $originalPath
    $env:MSYSTEM = $originalMsystem
    $env:SCOUTING_BUILD_ROOT = $originalRoot
    $env:QT_QPA_PLATFORM = $originalQtPlatform
    Pop-Location
}
