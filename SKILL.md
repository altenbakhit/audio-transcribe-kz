---
name: audio-transcribe
description: Transcribe audio and voice messages to text locally — Russian, Kazakh, English and other Whisper languages — using faster-whisper or whisper.cpp. Use whenever the user asks to transcribe, decode, recognize, or «расшифровать» speech from an audio file, voice message, podcast, interview, lecture, or video; wants SRT/VTT subtitles; needs a text transcript without uploading the recording to a third-party service; or asks to turn WhatsApp/Telegram voice notes into text.
---

# Audio transcription

Локальная транскрибация без облака. Запись остаётся на диске; сеть нужна только для первой загрузки модели.

## Quick start

> На этом ноутбуке уже настроен whisper.cpp с моделью `large-v3-turbo`. Он работает без Python и без скачивания модели с Hugging Face — начинайте с него:
>
> ```powershell
> powershell -ExecutionPolicy Bypass -File .\scripts\transcribe.ps1 -Path .\audio.ogg -Language ru
> ```

```powershell
# Windows, если Python и Hugging Face доступны
py -3 .\scripts\transcribe.py .\audio.ogg --language ru
py -3 .\scripts\transcribe.py .\interview.m4a --language kk --format srt
```

```bash
# macOS / Linux
python3 scripts/transcribe.py audio.ogg --language ru --format vtt
```

Если `faster-whisper` не установлен:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

Или вручную:

```powershell
# Windows
py -3 -m pip install --upgrade faster-whisper

# macOS / Linux
python3 -m pip install --upgrade faster-whisper
```

## Choose the engine

**whisper.cpp — основной путь на этом ноутбуке.** Модель `large-v3-turbo` и `whisper-cli.exe` уже на месте; ничего скачивать не нужно, качество выше, чем у `small`. Скрипт `scripts/transcribe.ps1` сам знает пути:

- `%USERPROFILE%\Documents\Codex\2026-09-09\remotion-plugin-remotion-openai-curated-remote\work\whisper\Release\whisper-cli.exe`
- `%USERPROFILE%\whisper-models\ggml-large-v3-turbo-q5_0.bin`

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\transcribe.ps1 `
  -Path .\audio.ogg -Language ru -Format txt
```

**faster-whisper — для других машин и для скриптовой обработки.** Кроссплатформенный, не требует отдельной сборки. Скрипт декодирует MP3/M4A/OGG/WEBM через ffmpeg, а если ffmpeg нет — через PyAV. Модель скачивается с Hugging Face при первом запуске. На этом ноутбуке загрузка с Hugging Face может падать из-за корпоративного TLS — тогда используйте whisper.cpp или укажите локальную папку модели через `--model`.

## Workflow

1. **Уточните файл и язык.** Если язык неизвестен, начните с `--language auto`; для русского/казахского лучше указать `ru`/`kk` явно — меньше ошибок на коротких записях.
2. **Выберите модель.** `small` — баланс скорости и качества; `large-v3` — для шума, интервью и юридически значимых записей. `tiny`/`base` — только для черновика.
3. **Запустите скрипт.** Для длинных файлов используйте `--format srt` или `--format json`, чтобы сохранить таймкоды.
4. **Проверьте текст.** Whisper путает имена, числа, суммы, названия компаний и термины. Для документов и суда обязательно вычитывайте вручную.
5. **Сохраните результат.** По умолчанию `txt` печатается в stdout; `srt`/`vtt`/`json` создаются рядом с аудио, если не указан `-o`.

## Output formats

| Формат | Команда | Результат |
|---|---|---|
| `txt` | `--format txt` | Сплошной текст |
| `srt` | `--format srt` | Субтитры с таймкодами |
| `vtt` | `--format vtt` | WebVTT для браузера |
| `json` | `--format json` | Язык, длительность, сегменты |

Полезные флаги:

```bash
--model small|medium|large-v3|large-v3-turbo
--language ru|kk|en|auto
--timestamps          # [ЧЧ:ММ:СС] в txt
--device cpu|cuda|auto
--compute-type int8   # меньше памяти на CPU
--no-vad              # отключить фильтр тишины
```

## Web page on alten.kz

Публичная страница `https://www.alten.kz/kalkulyator/transkribaciya` — другой сценарий: файл до 2,5 МБ уходит в Fish Audio, без регистрации, 3 файла в час. Используйте её, когда пользователю нужен быстрый онлайн-результат и запись не конфиденциальна. Для приватных записей — только локальные скрипты.

## Privacy and accuracy

- Локальные скрипты не отправляют аудио в сеть. Первый запуск скачивает модель с Hugging Face.
- Не отправляйте в облачные сервисы записи с персональными данными, коммерческой тайной и разговорами без согласия участников.
- Для судебных стенограмм храните исходный файл, укажите модель и язык, проверьте текст и при необходимости оформите расшифровку как документ.
- `large-v3` заметно лучше на казахском и на записях с шумом, но работает медленнее.

## Troubleshooting

**`faster-whisper` не установлен** — выполните `py -3 -m pip install --upgrade faster-whisper` (Windows) или `python3 -m pip install --upgrade faster-whisper`.

**`ffmpeg не найден`** — `winget install Gyan.FFmpeg` (Windows) или `brew install ffmpeg` (macOS).

**Модель долго скачивается** — первый запуск `large-v3` может занять несколько минут и несколько ГБ. Для пробы используйте `--model small`.

**Неверный язык** — укажите `--language ru` или `--language kk`; `auto` на коротких фразах ошибается чаще.

**Пустой текст** — проверьте, что в записи есть речь, а не тишина; попробуйте `--no-vad` и модель `large-v3`.

**Кракозябры в Windows-консоли** — скрипт выставляет UTF-8; если вывод искажается, перенаправьте в файл `-o result.txt` и откройте его в редакторе.
