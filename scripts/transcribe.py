#!/usr/bin/env python3
"""
Локальная транскрибация аудио в текст через faster-whisper.

Примеры:
    python transcribe.py audio.ogg --language ru
    python transcribe.py interview.m4a --language kk --format srt
    python transcribe.py podcast.mp3 --language auto --format json -o podcast.json
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def format_timestamp(seconds: float, separator: str = ",") -> str:
    """Превращает секунды в HH:MM:SS,mmm (SRT) или HH:MM:SS.mmm (VTT)."""
    total_ms = max(0, int(round(float(seconds) * 1000)))
    hours, rest = divmod(total_ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


def clean_text(value: str) -> str:
    return " ".join(str(value).split())


def decode_with_ffmpeg(audio: Path):
    """Читает любой формат через ffmpeg и отдаёт mono float32 16 кГц.

    Это обходит несовместимость новых версий PyAV с faster-whisper и заодно
    поддерживает видеофайлы. Если ffmpeg нет, возвращаем None — тогда
    faster-whisper попробует декодировать файл сам через PyAV.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None

    command = [
        ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error",
        "-i", str(audio),
        "-f", "s16le", "-ac", "1", "-ar", "16000", "-",
    ]
    try:
        process = subprocess.run(command, capture_output=True, check=True)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", "replace").strip()[:500]
        raise RuntimeError(f"ffmpeg не смог прочитать файл: {detail}") from exc

    if not process.stdout:
        raise RuntimeError("ffmpeg вернул пустой аудиопоток")

    import numpy as np

    return np.frombuffer(process.stdout, np.int16).astype(np.float32) / 32768.0


def make_srt(segments) -> str:
    blocks = []
    for index, segment in enumerate(segments, start=1):
        blocks.append(
            f"{index}\n"
            f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}\n"
            f"{clean_text(segment.text)}"
        )
    return "\n\n".join(blocks).strip() + "\n"


def make_vtt(segments) -> str:
    blocks = ["WEBVTT", ""]
    for index, segment in enumerate(segments, start=1):
        blocks.append(
            f"{index}\n"
            f"{format_timestamp(segment.start, '.')} --> {format_timestamp(segment.end, '.')}\n"
            f"{clean_text(segment.text)}"
        )
    return "\n\n".join(blocks).strip() + "\n"


def make_txt(segments, timestamps: bool) -> str:
    if timestamps:
        lines = [
            f"[{format_timestamp(segment.start, '.')[:-4]}] {clean_text(segment.text)}"
            for segment in segments
        ]
        return "\n".join(lines).strip() + "\n"
    return " ".join(clean_text(segment.text) for segment in segments).strip() + "\n"


def make_json(audio: Path, segments, info) -> str:
    payload = {
        "audio": str(audio),
        "language": info.language,
        "language_probability": round(float(info.language_probability), 4),
        "duration": round(float(info.duration), 3),
        "text": " ".join(clean_text(segment.text) for segment in segments).strip(),
        "segments": [
            {
                "start": round(float(segment.start), 3),
                "end": round(float(segment.end), 3),
                "text": clean_text(segment.text),
            }
            for segment in segments
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Транскрибация аудио в текст локально, без загрузки в облако.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Модели: tiny, base, small, medium, large-v3, large-v3-turbo.\n"
            "Для русского и казахского лучше small или large-v3.\n"
            "По умолчанию текст печатается в stdout; для srt/vtt/json файл\n"
            "создаётся рядом с аудио, если не указан -o."
        ),
    )
    parser.add_argument("audio", type=Path, help="Путь к аудио- или видеофайлу")
    parser.add_argument("--model", default="small", help="Модель Whisper (по умолчанию small)")
    parser.add_argument("--language", default="auto", help="ru, kk, en, ... или auto")
    parser.add_argument("--format", choices=["txt", "srt", "vtt", "json"], default="txt")
    parser.add_argument("-o", "--output", type=Path, help="Куда записать результат")
    parser.add_argument("--timestamps", action="store_true", help="Добавить [ЧЧ:ММ:СС] в txt")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--compute-type", default="default", help="default, int8, float16, float32")
    parser.add_argument("--no-vad", action="store_true", help="Отключить фильтр тишины (VAD)")
    parser.add_argument("--beam-size", type=int, default=5, help="Размер луча (по умолчанию 5)")
    return parser.parse_args()


def main() -> int:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleCP(65001)
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args()
    if not args.audio.exists():
        print(f"Файл не найден: {args.audio}", file=sys.stderr)
        return 2

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print(
            "Не установлен faster-whisper. Выполните:\n"
            "  python -m pip install --upgrade faster-whisper",
            file=sys.stderr,
        )
        return 2

    print(f"Загружаю модель {args.model}…", file=sys.stderr)
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)

    print(f"Распознаю {args.audio.name}…", file=sys.stderr)
    try:
        audio_input = decode_with_ffmpeg(args.audio)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    segments_iter, info = model.transcribe(
        audio_input if audio_input is not None else str(args.audio),
        language=None if args.language == "auto" else args.language,
        beam_size=args.beam_size,
        vad_filter=not args.no_vad,
    )
    # Генератор нужно материализовать: и для текста, и для сегментов в JSON.
    segments = list(segments_iter)

    if args.format == "srt":
        result = make_srt(segments)
    elif args.format == "vtt":
        result = make_vtt(segments)
    elif args.format == "json":
        result = make_json(args.audio, segments, info)
    else:
        result = make_txt(segments, args.timestamps)

    output = args.output
    if output is None and args.format != "txt":
        output = args.audio.with_suffix(f".{args.format}")

    if output is None:
        sys.stdout.write(result)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result, encoding="utf-8")
        print(f"Готово: {output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
