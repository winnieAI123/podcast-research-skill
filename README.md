# Podcast Research Agent Skill

An Agent skill that searches recent podcast episodes, downloads audio from RSS, transcribes it locally, and produces a concise cross-podcast viewpoint report.

中文：这是一个可安装到 Claude Code 或 Codex 的播客研究 Skill。它会搜索节目、下载音频、本地转写，并生成多期播客观点对比报告。

## Requirements

- Python 3.10 or newer
- Git command-line client
- At least **8 GB system memory (RAM)**; **16 GB recommended**
- At least **5 GB free disk space**; **8 GB recommended**
- Internet access for podcast search, audio, Python packages, and the first Whisper model download
- Apple Silicon macOS uses `mlx-whisper`; Windows, Linux, and Intel macOS use `faster-whisper`
- FFmpeg is optional but required for the YouTube fallback and splitting large files for the optional OpenAI API backend

Machines with less than 8 GB RAM fail the setup check because local transcription may be unstable. Machines with 8–16 GB RAM can run the Skill, but should prefer the `small` model and avoid concurrent heavy applications. The first transcription downloads a model of roughly 0.5–1.6 GB. Audio files and transcripts need additional space. CPU transcription on Windows can be substantially slower than Apple Silicon.

## Agent-safe installation

An Agent must assess the machine first, report the result, and ask the user for explicit confirmation before installing dependencies or copying the Skill.

### 1. Clone and assess without making changes

```bash
git clone https://github.com/winnieAI123/podcast-research-skill.git
cd podcast-research-skill
python3 install.py --check-only
```

Windows Codex assessment:

```powershell
git clone https://github.com/winnieAI123/podcast-research-skill.git
Set-Location .\podcast-research-skill
py -3 install.py --check-only --agent codex
```

The assessment does not install packages or copy files. It reports the platform, Python interpreter, Git availability, RAM, free disk space, selected Agent destination, transcription backend, and expected model download size.

### 2. Report and confirm

The Agent must show the assessment to the user, explain that installation will install Python packages and copy the Skill into the selected Agent directory, then request explicit confirmation.

### 3. Install after confirmation

Use the same Python launcher used for assessment:

```bash
python3 install.py --agent claude
python3 install.py --agent codex
python3 install.py --agent both
```

Windows Codex installation: `py -3 install.py --agent codex`.

The installation succeeds only when the required Python packages, local transcription backend, Skill files, minimum RAM, and minimum free disk space pass the built-in check. Agents must also follow [`AGENTS.md`](AGENTS.md).

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
