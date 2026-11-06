$ErrorActionPreference = 'Stop'
$original = Join-Path $pwd 'dist/BaseballScoutingEditor'
$unicodeRoot = Join-Path $env:RUNNER_TEMP '한글 배포 프로그램'
New-Item -ItemType Directory -Force $unicodeRoot | Out-Null
Copy-Item $original $unicodeRoot -Recurse -Force
$package = Join-Path $unicodeRoot 'BaseballScoutingEditor'
$exe = Join-Path $package 'BaseballScoutingEditor.exe'
$evidence = Join-Path $pwd 'build-evidence'
New-Item -ItemType Directory -Force $evidence | Out-Null
if (!(Test-Path $exe)) { throw 'EXE missing' }
foreach ($file in @('_internal/tools/ffmpeg.exe', '_internal/tools/ffprobe.exe',
                     '_internal/PySide6/plugins/platforms/qwindows.dll', '_internal/python312.dll')) {
    if (!(Test-Path (Join-Path $package $file))) { throw "Required runtime missing: $file" }
}
$signatures = @($exe, (Join-Path $package '_internal/tools/ffmpeg.exe'), (Join-Path $package '_internal/tools/ffprobe.exe')) | ForEach-Object {
    $signature = Get-AuthenticodeSignature $_
    [PSCustomObject]@{ file = (Split-Path $_ -Leaf); status = [string]$signature.Status }
}
if ($signatures | Where-Object { $_.status -notin @('Valid', 'NotSigned') }) { throw 'Invalid Authenticode signature state' }
$signatures | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $package 'signature-report.json')
Copy-Item (Join-Path $package 'signature-report.json') $evidence
Copy-Item (Join-Path $package 'signature-report.json') $original
# Remove Python/FFmpeg from PATH and execute from an unrelated Unicode working directory.
$work = Join-Path $env:RUNNER_TEMP '포터블 테스트 공백'
New-Item -ItemType Directory -Force $work | Out-Null
$oldPath = $env:PATH
$env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
Remove-Item Env:PYTHONHOME, Env:PYTHONPATH -ErrorAction SilentlyContinue
Remove-Item Env:QT_PLUGIN_PATH, Env:QT_QPA_PLATFORM_PLUGIN_PATH -ErrorAction SilentlyContinue
$before = Get-ChildItem $package -Recurse -File | ForEach-Object {
    "$($_.FullName):$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)"
}
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls $package /deny ($identity + ':(OI)(CI)(W)') /T | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not enforce read-only installation test' }
try {
    $process = Start-Process -FilePath $exe -ArgumentList @('--portable-self-test', "`"$work`"") -WorkingDirectory $work -PassThru
    if (!$process.WaitForExit(180000)) { $process.Kill(); throw 'Frozen EXE test timed out' }
    $reportPath = Join-Path $work 'portable-test-report.json'
    if (!(Test-Path $reportPath)) { throw 'No EXE self-test report was produced' }
    Copy-Item $reportPath $evidence
    $report = Get-Content $reportPath -Raw | ConvertFrom-Json
    if ($process.ExitCode -ne 0 -or !$report.passed -or !$report.frozen) {
        Get-Content $reportPath
        throw 'Frozen EXE test failed'
    }
    $after = Get-ChildItem $package -Recurse -File | ForEach-Object {
        "$($_.FullName):$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)"
    }
    if (Compare-Object $before $after) { throw 'Application wrote into installation folder' }
    # Also record the actual PE signature state and versions; unsigned is not signed.
    Copy-Item $reportPath (Join-Path $original 'portable-test-report.json')
} finally {
    & icacls $package /remove:d $identity /T | Out-Null
    $env:PATH = $oldPath
    $logs = Join-Path $env:LOCALAPPDATA 'BaseballScoutingEditor/logs'
    if (Test-Path $logs) { Copy-Item $logs (Join-Path $evidence 'logs') -Recurse -Force }
}
