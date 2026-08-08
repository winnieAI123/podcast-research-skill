#!/usr/bin/env python3
"""Download podcast audio through RSS, with an optional YouTube fallback."""

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

HEADERS = {"User-Agent": "PodcastResearchSkill/1.0"}
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name, max_len=80):
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = re.sub(r"\s+", "_", name.strip()).strip(". ")
    name = name[:max_len].rstrip(". ") or "episode"
    if name.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
        name = f"_{name}"
    return name


def get_audio_duration_seconds(filepath):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(filepath)],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def download_via_rss(episode, output_dir):
    feed_url = episode.get("feed_url", "")
    title = episode.get("name", "")
    show = episode.get("show_name", "")

    if not feed_url:
        print("  [RSS] No feed URL available")
        return None

    print(f"  [RSS] Fetching feed: {feed_url[:60]}...")

    try:
        resp = requests.get(feed_url, timeout=30, headers=HEADERS)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        print(f"  [RSS] Failed to fetch/parse feed: {e}")
        return None

    title_lower = title.lower().strip()
    best_match = None
    best_score = 0

    for item in root.iter("item"):
        item_title_el = item.find("title")
        if item_title_el is None or item_title_el.text is None:
            continue

        item_title = item_title_el.text.strip().lower()

        if item_title == title_lower:
            score = 100
        elif title_lower in item_title or item_title in title_lower:
            score = 80
        else:
            title_words = set(title_lower.split())
            item_words = set(item_title.split())
            overlap = len(title_words & item_words)
            score = (overlap / max(len(title_words), 1)) * 60

        if score > best_score:
            enclosure = item.find("enclosure")
            if enclosure is not None and enclosure.get("url"):
                best_match = enclosure.get("url")
                best_score = score

    if not best_match or best_score < 40:
        print(f"  [RSS] No matching episode found in feed (best score: {best_score:.0f})")
        return None

    filename = sanitize_filename(f"{show}_{title}") + ".mp3"
    filepath = output_dir / filename
    print(f"  [RSS] Downloading audio (match score: {best_score:.0f})...")

    try:
        audio_resp = requests.get(best_match, timeout=600, stream=True, headers=HEADERS)
        audio_resp.raise_for_status()
        total = int(audio_resp.headers.get("content-length", 0))
        downloaded = 0
        with open(filepath, "wb") as f:
            for chunk in audio_resp.iter_content(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded * 100 // total
                    if pct % 25 == 0:
                        print(f"  [RSS] {pct}% ({downloaded // 1024 // 1024}MB)", end="\r")
        print(f"  [RSS] Downloaded: {filename} ({downloaded // 1024 // 1024}MB)")
        return str(filepath)
    except Exception as e:
        print(f"  [RSS] Download failed: {e}")
        if filepath.exists():
            filepath.unlink()
        return None


def download_via_youtube(episode, output_dir):
    show = episode.get("show_name", "")
    title = episode.get("name", "")
    query = f"{show} {title}"

    filename = sanitize_filename(f"{show}_{title}")
    output_template = str(output_dir / filename)

    print(f"  [YouTube] Searching: {query[:60]}...")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "yt_dlp",
                f"ytsearch1:{query}",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "5",
                "--no-playlist",
                "--output", f"{output_template}.%(ext)s",
                "--quiet",
                "--no-warnings",
                "--socket-timeout", "30",
            ],
            capture_output=True, text=True, timeout=180
        )

        if result.returncode != 0:
            print(f"  [YouTube] Failed: {result.stderr[:100]}")
            return None

        for ext in [".mp3", ".m4a", ".opus", ".webm"]:
            candidate = Path(f"{output_template}{ext}")
            if candidate.exists():
                duration = get_audio_duration_seconds(candidate)
                expected = episode.get("duration_ms", 0) / 1000
                if expected > 0 and duration:
                    ratio = duration / expected
                    if ratio < 0.5 or ratio > 1.5:
                        print(f"  [YouTube] Duration mismatch: {duration:.0f}s vs expected {expected:.0f}s, skipping")
                        candidate.unlink()
                        return None
                dur_str = f" ({duration:.0f}s)" if duration else ""
                print(f"  [YouTube] Downloaded: {candidate.name}{dur_str}")
                return str(candidate)

        print("  [YouTube] No output file found")
        return None

    except subprocess.TimeoutExpired:
        print("  [YouTube] Timeout")
        return None
    except Exception as e:
        print(f"  [YouTube] Error: {e}")
        return None


def download_episodes(episodes_json_path, selected_indices, output_dir):
    with open(episodes_json_path, "r", encoding="utf-8") as f:
        episodes = json.load(f)

    if not selected_indices:
        selected_indices = list(range(len(episodes)))

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for idx in selected_indices:
        if idx < 0 or idx >= len(episodes):
            print(f"\nSkipping invalid index: {idx + 1}")
            continue

        ep = episodes[idx]
        print(f"\n{'─'*60}")
        print(f"Episode {idx + 1}: {ep['name']}")
        print(f"Show: {ep['show_name']}  |  Duration: {ep.get('duration_min', '?')} min")

        # Priority: RSS feed (more reliable when feed_url is available) > YouTube
        audio_path = download_via_rss(ep, output_dir)

        if not audio_path:
            audio_path = download_via_youtube(ep, output_dir)

        if audio_path:
            ep["audio_path"] = audio_path
            ep["audio_status"] = "downloaded"
        else:
            ep["audio_path"] = None
            ep["audio_status"] = "unavailable"
            print("  [FALLBACK] Audio unavailable; description text may be used as secondary evidence")

        results.append(ep)

    updated_path = output_dir / "episodes_with_audio.json"
    with open(updated_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    downloaded = sum(1 for r in results if r["audio_status"] == "downloaded")
    print(f"\n{'='*60}")
    print(f"Results: {downloaded}/{len(results)} episodes downloaded successfully")
    print(f"Updated metadata: {updated_path}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Download podcast audio")
    parser.add_argument("--episodes-json", required=True, help="Path to episodes.json from search")
    parser.add_argument("--select", default="", help="Comma-separated episode numbers (1-indexed), or empty for all")
    parser.add_argument("--output-dir", required=True, help="Directory to save audio files")
    args = parser.parse_args()

    if args.select.strip():
        selected = [int(x.strip()) - 1 for x in args.select.split(",")]
    else:
        selected = []

    download_episodes(args.episodes_json, selected, args.output_dir)


if __name__ == "__main__":
    main()
