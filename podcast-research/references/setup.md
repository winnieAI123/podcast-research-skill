# Setup and platform notes

Read this file only when installing the Skill or diagnosing a failed preflight check.

## Required environment

- Python 3.10+
- 5 GB free disk space minimum; 8 GB recommended
- Network access for iTunes Search, RSS audio, Python packages, and the initial model download

`requirements.txt` in the repository root selects the local transcription backend:

- Apple Silicon macOS: `mlx-whisper`
- Windows, Linux, or Intel macOS: `faster-whisper`

The OpenAI Whisper API is optional. Use it only when the user explicitly selects `--model api`; install `openai` and set `OPENAI_API_KEY` first.

## Disk and performance

Whisper models normally consume about 0.5–1.6 GB. A set of downloaded podcast episodes can add several GB. Keep 5 GB free at minimum and 8 GB for comfortable repeated use. Windows CPU transcription works but is usually slower than Apple Silicon; select `--model small` when speed matters more than maximum accuracy.

## Optional FFmpeg

FFmpeg and ffprobe are not required for RSS downloading or local transcription. They are required for YouTube audio extraction and splitting files larger than the OpenAI API limit.

- macOS: `brew install ffmpeg`
- Windows: `winget install Gyan.FFmpeg`
- Ubuntu/Debian: `sudo apt install ffmpeg`

## Success criteria

Run:

```bash
python3 scripts/check_setup.py --skill-dir .
```

On Windows, replace `python3` with `py -3` and `/` with `\` when needed. Use the same Python launcher that ran `install.py`; mixing Python installations can make installed packages appear missing.

Installation is ready when Python, free disk, required packages, a local transcription backend, and Skill files all show `PASS`. Optional FFmpeg and OpenAI API rows may show `WARN` without blocking the RSS plus local-transcription workflow.
