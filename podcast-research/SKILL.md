---
name: podcast-research
description: Search recent podcast episodes about a user-provided topic, let the user select episodes, download audio from RSS with an optional YouTube fallback, transcribe locally, and create a source-faithful cross-podcast viewpoint report. Use for podcast research, podcast viewpoint analysis, cross-podcast comparisons, 播客研究, 播客观点分析, or requests to understand what podcast hosts and guests are saying about a topic.
---

# Podcast Research

Use the bundled scripts with the same Python interpreter used during installation. On macOS/Linux, prefer `python3`; on Windows, prefer `py -3`. If the user used another launcher during installation, keep using that launcher. Do not require an API key for the primary workflow.

## Preflight

Resolve this file's directory as `SKILL_DIR`. Before the first task on a machine, run:

```bash
python3 "$SKILL_DIR/scripts/check_setup.py" --skill-dir "$SKILL_DIR"
```

Continue when all required checks show `PASS`. `WARN` rows are optional fallbacks. If a required check fails, read `references/setup.md`, fix the reported item, and rerun the check.

Keep at least 5 GB free disk space; recommend 8 GB. The initial local Whisper model download is approximately 0.5–1.6 GB, and downloaded audio requires additional space.

## Workflow

### 1. Search

Choose an English query when it improves coverage, while preserving the user's intended topic.

```bash
python3 "$SKILL_DIR/scripts/search_podcasts.py" \
  --topic "TOPIC" \
  --days-back 30 \
  --max 10 \
  --output-dir "WORK_DIR"
```

Use a user-approved working directory. The script creates `episodes.json`.

### 2. Let the user select episodes

Show the numbered results with title, show, date, duration, and description. Ask which episodes to analyze. Do not download every result without the user's selection unless the user already requested all results.

### 3. Download

```bash
python3 "$SKILL_DIR/scripts/audio_downloader.py" \
  --episodes-json "WORK_DIR/episodes.json" \
  --select "1,3,5" \
  --output-dir "WORK_DIR"
```

The script tries RSS first and YouTube second. YouTube extraction requires FFmpeg. It writes `episodes_with_audio.json` and marks failures as `unavailable`.

### 4. Transcribe

```bash
python3 "$SKILL_DIR/scripts/transcriber.py" \
  --audio-dir "WORK_DIR" \
  --model turbo \
  --language auto
```

The backend is selected automatically: MLX on Apple Silicon and faster-whisper elsewhere. Use `--model small` on slower CPU-only machines. Use `--model api` only when the user explicitly accepts the OpenAI API requirement and cost.

### 5. Analyze source-faithfully

Read every selected episode's transcript and `episodes_with_audio.json`. Treat descriptions and web summaries as secondary evidence, never as transcripts. If audio is unavailable, use the episode description and web search only when available, label the evidence as secondary, and do not present reconstructed text as a direct quote.

Write a concise Markdown report to `WORK_DIR/[topic]_podcast_report.md`:

```markdown
# [Topic] podcast viewpoint brief

**Research date**: YYYY-MM-DD | **Source**: Apple Podcasts/RSS | **Scope**: N episodes

## One-sentence conclusion

State the dominant view and the most important disagreement in 2–3 sentences.

## Viewpoint overview

| Speaker or organization | Stance | Core view | Verbatim quote | Episode |
|---|---|---|---|---|

## Main disagreements

List only 2–3 genuine disagreements. Attribute every position to a named episode and speaker when the transcript makes the speaker clear.

## Episode summaries

### [Show]: [Episode]
**Guest**: ... | **Date**: ... | **Duration**: ...

1. Three to five source-grounded points.
```

Do not invent speaker identities, quotes, dates, or positions. When the transcript does not establish who said a line, attribute it to the episode rather than guessing.

### 6. Deliver

Show the Markdown report and link the working files. Create Word only when requested:

```bash
python3 "$SKILL_DIR/scripts/md_to_docx.py" \
  "WORK_DIR/[topic]_podcast_report.md" \
  "WORK_DIR/[topic]_podcast_report.docx"
```

On Windows, replace `python3` with `py -3` and use Windows paths. Do not translate the Python script itself.

## Completion criteria

The task is complete only when:

1. Search scope and selected episodes are stated.
2. Every downloaded episode has a transcript or is explicitly marked unavailable.
3. Direct quotes come from transcripts; secondary summaries are labeled.
4. The report distinguishes consensus from disagreement and attributes claims to episodes.
5. The report and supporting metadata are saved in the working directory.

## Fallbacks

- No search results: retry once with a clearer English query or a wider date range.
- RSS fails: allow the bundled YouTube fallback when FFmpeg is installed.
- Both audio paths fail: use the description and available web evidence, label the limitation, and omit direct quotes.
- Transcript is too long for context: summarize it in sequential chunks, retain episode attribution, then compare the chunk summaries.
- Local transcription is unavailable: read `references/setup.md`; use OpenAI only with explicit user approval and a configured key.
