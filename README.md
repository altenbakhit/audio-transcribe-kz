# audio-transcribe-kz

Локальная транскрибация аудио и голосовых сообщений в текст. Русский, казахский, английский и другие языки Whisper. Без загрузки записи в облако: после скачивания модели всё считается на вашем компьютере.

В репозитории два движка и готовый skill для ИИ-агентов:

- **faster-whisper** — кроссплатформенный Python-клиент, самая простая установка.
- **whisper.cpp** — лёгкий C++-движок, работает без Python; удобен на Windows.
- **SKILL.md** — инструкция для Claude Code / Codex, чтобы агент сам выбирал движок и формат.

## Быстрый старт

### Windows

```powershell
git clone https://github.com/altenbakhit/audio-transcribe-kz.git
cd audio-transcribe-kz

# один раз: Python-зависимости
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1

# транскрибация
py -3 .\scripts\transcribe.py .\audio.ogg --language ru
py -3 .\scripts\transcribe.py .\interview.m4a --language kk --format srt
```

> Если Python не установлен или Hugging Face не скачивается из-за корпоративного TLS, используйте `scripts/transcribe.ps1` и уже готовый whisper.cpp — см. раздел ниже.

### macOS / Linux

```bash
git clone https://github.com/altenbakhit/audio-transcribe-kz.git
cd audio-transcribe-kz

python3 -m pip install --upgrade faster-whisper
python3 scripts/transcribe.py audio.ogg --language ru
```

Первый запуск скачает модель (от ~75 МБ для `tiny` до ~3 ГБ для `large-v3`). Дальше интернет не нужен.

## Форматы и вывод

Поддерживаются MP3, WAV, M4A, OGG, WEBM, FLAC, MP4 и другие форматы, которые читает ffmpeg/PyAV.

```bash
# текст в stdout
python3 scripts/transcribe.py audio.ogg --language ru

# субтитры SRT рядом с аудио
python3 scripts/transcribe.py audio.ogg --language ru --format srt

# JSON с сегментами и таймкодами
python3 scripts/transcribe.py audio.ogg --language auto --format json -o result.json

# текст с отметками времени
python3 scripts/transcribe.py audio.ogg --language ru --timestamps
```

| Формат | Что получится |
|---|---|
| `txt` | Сплошной текст, по умолчанию в stdout |
| `srt` | Субтитры с таймкодами |
| `vtt` | WebVTT для браузера |
| `json` | Язык, длительность, сегменты |

## Модели

| Модель | Размер | Качество | Скорость |
|---|---:|---|---|
| `tiny` | ~75 МБ | базовое | самая быстрая |
| `base` | ~145 МБ | невысокое | быстрая |
| `small` | ~480 МБ | хорошее | средняя |
| `medium` | ~1,5 ГБ | высокое | медленная |
| `large-v3` | ~3 ГБ | лучшее | самая медленная |
| `large-v3-turbo` | ~1,6 ГБ | близко к large | быстрее large |

Для русского и казахского на чистой записи обычно достаточно `small`. Для интервью, шума и юридически значимых записей берите `large-v3`.

```bash
python3 scripts/transcribe.py interview.m4a --language ru --model large-v3
```

## whisper.cpp на Windows

Если Python не нужен, используйте `scripts/transcribe.ps1`. Скрипт сам ищет `whisper-cli.exe`, модель и `ffmpeg`, конвертирует запись в WAV 16 кГц и запускает распознавание.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\transcribe.ps1 `
  -Path .\audio.ogg -Language ru -Format txt
```

Пути по умолчанию:

- `%USERPROFILE%\Documents\Codex\...\whisper\Release\whisper-cli.exe`
- `%USERPROFILE%\whisper-models\ggml-large-v3-turbo-q5_0.bin`

Их можно переопределить:

```powershell
.\scripts\transcribe.ps1 -Path .\audio.ogg -Language kk -Format srt `
  -Whisper "C:\tools\whisper-cli.exe" `
  -Model "C:\models\ggml-large-v3-turbo.bin"
```

## Skill для ИИ-агента

Репозиторий сам является skill-папкой: `SKILL.md` лежит в корне, скрипты — в `scripts/`. Установите его в каталог навыков:

```powershell
# Claude Code
git clone https://github.com/altenbakhit/audio-transcribe-kz.git "$env:USERPROFILE\.claude\skills\audio-transcribe"

# OpenCode
git clone https://github.com/altenbakhit/audio-transcribe-kz.git "$env:USERPROFILE\.config\opencode\skills\audio-transcribe"
```

После перезапуска агент сможет сам транскрибировать файлы по фразам вроде «расшифруй голосовое», «сделай субтитры», «переведи аудио в текст». Skill лежит в `SKILL.md` и `scripts/`.

## Веб-версия

В сайте alten.kz подготовлена бесплатная страница (публикуется отдельно от этого репозитория):

**https://www.alten.kz/kalkulyator/transkribaciya**

Она принимает файлы до 2,5 МБ, распознаёт русский и казахский через Fish Audio и не сохраняет аудио на сайте. Это отдельный облачный сценарий: локальный CLI из этого репозитория не отправляет запись никуда.

## Если что-то не работает

**`faster-whisper` не установлен** — `py -3 -m pip install --upgrade faster-whisper` (Windows) или `python3 -m pip install --upgrade faster-whisper`.

**`ffmpeg не найден`** — `winget install Gyan.FFmpeg` (Windows) или `brew install ffmpeg` (macOS). Без ffmpeg Python-скрипт попробует PyAV, но на новых версиях PyAV возможна несовместимость.

**Hugging Face не скачивается, `RecursionError` или SSL** — на некоторых корпоративных сетях Python-клиент Hugging Face не проходит TLS. Используйте `scripts/transcribe.ps1` (whisper.cpp) или скачайте модель на другом компьютере и передайте локальную папку через `--model C:\models\faster-whisper-small`.

**Тишина превращается в текст** — Whisper иногда «галлюцинирует» на пустых участках. Проверяйте запись и используйте VAD; для юридических стенограмм вычитывайте текст вручную.

## Приватность

- Локальные скрипты не делают сетевых запросов, кроме первой загрузки модели с Hugging Face.
- Записи и расшифровки остаются на диске.
- Веб-страница alten.kz отправляет аудио во внешний сервис Fish Audio; не загружайте туда конфиденциальные разговоры без согласия участников.
- Для судебных и служебных стенограмм проверяйте текст вручную: Whisper ошибается на именах, числах, терминах и шумных записях.

## Лицензия

MIT. Модели Whisper распространяются по своим лицензиям (OpenAI / Hugging Face).
