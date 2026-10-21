$ErrorActionPreference = 'Stop'

Write-Host "Проверяю Python…" -ForegroundColor DarkGray
$python = (Get-Command py -ErrorAction SilentlyContinue | Select-Object -First 1).Source
$pythonArgs = @('-3')
if (-not $python) {
    $python = (Get-Command python3 -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    $pythonArgs = @()
}
if (-not $python) {
    $python = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    $pythonArgs = @()
}
if (-not $python) {
    throw "Python не найден. Установите Python 3.10+ с python.org или через winget install Python.Python.3.12"
}
& $python @pythonArgs --version

Write-Host "Ставлю faster-whisper…" -ForegroundColor DarkGray
& $python @pythonArgs -m pip install --upgrade pip
& $python @pythonArgs -m pip install --upgrade faster-whisper numpy

Write-Host "Проверяю ffmpeg…" -ForegroundColor DarkGray
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $ffmpeg) {
    Write-Warning "ffmpeg не найден. Установите: winget install Gyan.FFmpeg"
} else {
    & $ffmpeg.Source -version | Select-Object -First 1
}

Write-Host ""
Write-Host "Готово. Пример:" -ForegroundColor Green
Write-Host "  py -3 .\scripts\transcribe.py .\audio.ogg --language ru"
Write-Host "  py -3 .\scripts\transcribe.py .\audio.ogg --language kk --format srt"
