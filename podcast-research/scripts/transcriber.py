#!/usr/bin/env python3
"""Transcribe podcast audio using a platform-appropriate Whisper backend."""

import argparse
import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path


MLX_MODELS = {
    "turbo": "mlx-community/whisper-large-v3-turbo",
    "large": "mlx-community/whisper-large-v3",
    "small": "mlx-community/whisper-small",
}

FASTER_MODELS = {
    "turbo": "turbo",
    "large": "large-v3",
    "small": "small",
}


def module_exists(name):
    return importlib.util.find_spec(name) is not None


def choose_backend(model):
    if model == "api":
        if module_exists("openai") and os.environ.get("OPENAI_API_KEY"):
            return "openai"
        return None

    machine = platform.machine().lower()
    apple_silicon = platform.system() == "Darwin" and machine in {"arm64", "aarch64"}
    if apple_silicon and module_exists("mlx_whisper"):
        return "mlx"
    if module_exists("faster_whisper"):
        return "faster"
    if module_exists("mlx_whisper"):
        return "mlx"
    return None


def transcribe_mlx(audio_path, model, language=None):
    import mlx_whisper

    kwargs = {"path_or_hf_repo": MLX_MODELS[model]}
    if language:
        kwargs["language"] = language
    print(f"  [mlx-whisper] Model: {MLX_MODELS[model].split('/')[-1]}")
    result = mlx_whisper.transcribe(str(audio_path), **kwargs)
    return result.get("text", "")


def transcribe_faster(audio_path, model, language=None):
    from faster_whisper import WhisperModel

    model_name = FASTER_MODELS[model]
    print(f"  [faster-whisper] Model: {model_name}")
    whisper = WhisperModel(model_name, device="auto", compute_type="int8")
    segments, _info = whisper.transcribe(str(audio_path), language=language)
    return " ".join(segment.text.strip() for segment in segments).strip()


def transcribe_openai_chunked(audio_path, language=None):
    from openai import OpenAI

    if not shutil_which("ffmpeg"):
        raise RuntimeError("FFmpeg is required to split files larger than 25 MB")

    client = OpenAI()
    chunk_dir = Path(audio_path).parent / ".chunks"
    chunk_dir.mkdir(exist_ok=True)
    stem = Path(audio_path).stem
    chunk_pattern = str(chunk_dir / f"{stem}_chunk_%03d.mp3")

    subprocess.run(
        ["ffmpeg", "-i", str(audio_path), "-f", "segment", "-segment_time", "600", "-c:a", "libmp3lame", "-q:a", "5", chunk_pattern, "-y", "-loglevel", "quiet"],
        check=True,
        timeout=300,
    )

    texts = []
    for index, chunk in enumerate(sorted(chunk_dir.glob(f"{stem}_chunk_*.mp3")), 1):
        print(f"  [OpenAI API] Chunk {index}")
        with chunk.open("rb") as handle:
            kwargs = {"model": "whisper-1", "file": handle, "response_format": "text"}
            if language:
                kwargs["language"] = language
            texts.append(client.audio.transcriptions.create(**kwargs))
        chunk.unlink()
    try:
        chunk_dir.rmdir()
    except OSError:
        pass
    return "\n".join(texts)


def shutil_which(command):
    import shutil

    return shutil.which(command)


def transcribe_openai(audio_path, language=None):
    from openai import OpenAI

    if Path(audio_path).stat().st_size > 25 * 1024 * 1024:
        return transcribe_openai_chunked(audio_path, language)

    print("  [OpenAI API] Transcribing")
    with Path(audio_path).open("rb") as handle:
        kwargs = {"model": "whisper-1", "file": handle, "response_format": "text"}
        if language:
            kwargs["language"] = language
        return OpenAI().audio.transcriptions.create(**kwargs)


def audio_files_from(directory):
    metadata = directory / "episodes_with_audio.json"
    if metadata.exists():
        import json

        episodes = json.loads(metadata.read_text(encoding="utf-8"))
        return [Path(item["audio_path"]) for item in episodes if item.get("audio_path") and Path(item["audio_path"]).exists()]
    return sorted(path for path in directory.iterdir() if path.suffix.lower() in {".mp3", ".m4a", ".wav", ".opus", ".webm", ".ogg"})


def update_metadata(directory, transcripts):
    import json

    metadata = directory / "episodes_with_audio.json"
    if not metadata.exists():
        return
    episodes = json.loads(metadata.read_text(encoding="utf-8"))
    for episode in episodes:
        audio_path = episode.get("audio_path")
        if audio_path in transcripts:
            episode["transcript_path"] = transcripts[audio_path]
    metadata.write_text(json.dumps(episodes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated metadata: {metadata}")


def transcribe_episodes(audio_dir, model="turbo", language=None, force=False):
    directory = Path(audio_dir)
    files = audio_files_from(directory)
    if not files:
        print("No audio files found to transcribe.")
        return 0

    backend = choose_backend(model)
    if not backend:
        if model == "api":
            print("ERROR: install openai and set OPENAI_API_KEY before using --model api", file=sys.stderr)
        else:
            print("ERROR: no local transcription backend is installed; run install.py", file=sys.stderr)
        return 1

    print(f"Backend: {backend}")
    transcripts = {}
    for index, audio_path in enumerate(files, 1):
        print(f"\n[{index}/{len(files)}] {audio_path.name}")
        text_path = audio_path.with_suffix(".txt")
        if text_path.exists() and not force:
            print("  Transcript exists; skipping. Use --force to replace it.")
            transcripts[str(audio_path)] = str(text_path)
            continue
        try:
            if backend == "mlx":
                text = transcribe_mlx(audio_path, model, language)
            elif backend == "faster":
                text = transcribe_faster(audio_path, model, language)
            else:
                text = transcribe_openai(audio_path, language)
            text_path.write_text(text, encoding="utf-8")
            transcripts[str(audio_path)] = str(text_path)
            print(f"  Saved: {text_path.name} ({len(text)} chars)")
        except Exception as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            transcripts[str(audio_path)] = None

    update_metadata(directory, transcripts)
    success = sum(bool(path) for path in transcripts.values())
    print(f"\nTranscribed: {success}/{len(files)}")
    return 0 if success == len(files) else 1


def main():
    parser = argparse.ArgumentParser(description="Transcribe podcast audio")
    parser.add_argument("--audio-dir", required=True, help="Directory containing audio files")
    parser.add_argument("--model", default="turbo", choices=("turbo", "large", "small", "api"))
    parser.add_argument("--language", default=None, help="Language hint such as en or zh; default: auto-detect")
    parser.add_argument("--force", action="store_true", help="Replace existing transcripts")
    args = parser.parse_args()
    language = None if args.language in {None, "", "auto"} else args.language
    return transcribe_episodes(args.audio_dir, args.model, language, args.force)


if __name__ == "__main__":
    raise SystemExit(main())
