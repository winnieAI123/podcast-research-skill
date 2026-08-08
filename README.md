# Podcast Research Agent Skill

An Agent skill that searches recent podcast episodes, downloads audio from RSS, transcribes it locally, and produces a concise cross-podcast viewpoint report.

中文：这是一个可安装到 Claude Code 或 Codex 的播客研究 Skill。它会搜索节目、下载音频、本地转写，并生成多期播客观点对比报告。

## Requirements

- Python 3.10 or newer
- Git command-line client
- At least **5 GB free disk space**; **8 GB recommended**
- Internet access for podcast search, audio, Python packages, and the first Whisper model download
- Apple Silicon macOS uses `mlx-whisper`; Windows, Linux, and Intel macOS use `faster-whisper`
- FFmpeg is optional but required for the YouTube fallback and splitting large files for the optional OpenAI API backend

The first transcription downloads a model of roughly 0.5–1.6 GB. Audio files and transcripts need additional space. CPU transcription on Windows can be substantially slower than Apple Silicon.

## One-command installer

```bash
git clone https://github.com/winnieAI123/podcast-research-skill.git
cd podcast-research-skill
python3 install.py
```

On Windows, run `py -3 install.py`. Use the same Python launcher for later checks and Skill commands. The installer detects Claude Code and Codex directories. Override detection with:

```bash
python3 install.py --agent claude
python3 install.py --agent codex
python3 install.py --agent both
```

The installation succeeds only when the required Python packages, local transcription backend, Skill files, and minimum free disk space pass the built-in check.

## Verify or diagnose

Run the checker against the installed Skill, not only the cloned source tree.

```bash
python3 ~/.codex/skills/podcast-research/scripts/check_setup.py --skill-dir ~/.codex/skills/podcast-research
```

For Claude Code, replace `.codex` with `.claude`. Windows Codex equivalent:

```powershell
py -3 "$env:USERPROFILE\.codex\skills\podcast-research\scripts\check_setup.py" --skill-dir "$env:USERPROFILE\.codex\skills\podcast-research"
```

All required rows must show `PASS`. `WARN` means an optional fallback, normally FFmpeg or an OpenAI API key, is unavailable.

## Use with an Agent

Restart the Agent after installation, then say:

> Use podcast-research to find and compare recent podcast viewpoints about AI agents.

The Agent should search first, show the candidate episodes, wait for your selection, then download, transcribe, and report. Full operational instructions and completion criteria are in [`podcast-research/SKILL.md`](podcast-research/SKILL.md).

## Optional FFmpeg

- macOS: `brew install ffmpeg`
- Windows: `winget install Gyan.FFmpeg`
- Ubuntu/Debian: `sudo apt install ffmpeg`

RSS downloading and local transcription work without FFmpeg. The YouTube fallback does not.

## Privacy and copyright

Audio and transcripts stay in the working directory unless the user explicitly moves or shares them. Use podcast material for personal research and follow the publisher's copyright terms and the relevant platform rules.

MIT licensed.
