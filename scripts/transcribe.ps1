param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Path,

    [ValidateSet('ru', 'kk', 'en', 'auto')]
    [string]$Language = 'ru',

    [ValidateSet('txt', 'srt', 'vtt')]
    [string]$Format = 'txt',

    [string]$Model,
    [string]$Whisper,
    [string]$OutPrefix
)

$ErrorActionPreference = 'Stop'

try {
    [Console]::OutputEncoding = [Text.Encoding]::UTF8
    $OutputEncoding = [Text.Encoding]::UTF8
} catch {
    # Старые хосты PowerShell могут не разрешать смену кодировки — не критично.
}

if (-not (Test-Path -LiteralPath $Path)) {
    throw "Файл не найден: $Path"
}

$ffmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $ffmpeg) {
    throw "ffmpeg не найден. Установите: winget install Gyan.FFmpeg"
}

if (-not $Whisper) {
    $candidates = @(
        "$env:USERPROFILE\Documents\Codex\2026-09-09\remotion-plugin-remotion-openai-curated-remote\work\whisper\Release\whisper-cli.exe",
        "$env:USERPROFILE\whisper.cpp\build\bin\whisper-cli.exe",
        "$env:USERPROFILE\whisper.cpp\main.exe"
    )
    $Whisper = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $Whisper) {
        $Whisper = (Get-Command whisper-cli -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    }
}
if (-not $Whisper -or -not (Test-Path -LiteralPath $Whisper)) {
    throw "whisper-cli.exe не найден. Укажите путь через -Whisper или установите whisper.cpp."
}

if (-not $Model) {
    $modelCandidates = @(
        "$env:USERPROFILE\whisper-models\ggml-large-v3-turbo-q5_0.bin",
        "$env:USERPROFILE\whisper.cpp\models\ggml-large-v3-turbo.bin",
        "$env:USERPROFILE\whisper.cpp\models\ggml-small.bin"
    )
    $Model = $modelCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $Model -or -not (Test-Path -LiteralPath $Model)) {
    throw "Модель Whisper не найдена. Укажите путь через -Model."
}

if (-not $OutPrefix) {
    $full = [IO.Path]::GetFullPath($Path)
    $dir = [IO.Path]::GetDirectoryName($full)
    $name = [IO.Path]::GetFileNameWithoutExtension($full)
    $OutPrefix = Join-Path $dir $name
}

$tempWav = Join-Path $env:TEMP ("whisper-" + [guid]::NewGuid().ToString('N') + ".wav")
try {
    Write-Host "Конвертирую в WAV 16 кГц…" -ForegroundColor DarkGray
    & $ffmpeg -y -hide_banner -loglevel error -i $Path -ar 16000 -ac 1 -c:a pcm_s16le $tempWav
    if ($LASTEXITCODE -ne 0) {
        throw "ffmpeg не смог прочитать файл: $Path"
    }

    $formatFlag = "-o$Format"
    Write-Host "Распознаю речь ($Language)…" -ForegroundColor DarkGray
    & $Whisper -m $Model -f $tempWav -l $Language -of $OutPrefix $formatFlag -np
    if ($LASTEXITCODE -ne 0) {
        throw "whisper-cli завершился с ошибкой (код $LASTEXITCODE)."
    }
}
finally {
    if (Test-Path -LiteralPath $tempWav) {
        Remove-Item -LiteralPath $tempWav -Force -ErrorAction SilentlyContinue
    }
}

$output = "$OutPrefix.$Format"
if (-not (Test-Path -LiteralPath $output)) {
    throw "Готовый файл не найден: $output"
}

Write-Host "Готово: $output" -ForegroundColor Green
if ($Format -eq 'txt') {
    Get-Content -LiteralPath $output -Raw -Encoding UTF8
}
