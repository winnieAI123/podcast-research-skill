#!/usr/bin/env python3
"""Search recent podcast episodes through the public iTunes Search API."""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests


HEADERS = {"User-Agent": "podcast-research-skill/1.0"}


def search_episodes(topic, days_back=30, max_results=10, country="US", language=None):
    url = "https://itunes.apple.com/search"
    params = {
        "term": topic,
        "media": "podcast",
        "entity": "podcastEpisode",
        "limit": min(max_results * 3, 200),
        "country": country,
    }
    if language:
        params["language"] = language

    print(f"Searching iTunes for: \"{topic}\"")
    print(f"Time range: last {days_back} days | Max results: {max_results}")

    resp = requests.get(url, params=params, timeout=30, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    cutoff = datetime.now() - timedelta(days=days_back)
    episodes = []

    for item in data.get("results", []):
        release_str = item.get("releaseDate", "")
        try:
            rd = datetime.fromisoformat(release_str.replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, AttributeError):
            continue

        if rd < cutoff:
            continue

        duration_ms = item.get("trackTimeMillis", 0) or 0
        duration_min = round(duration_ms / 60000, 1)

        episodes.append({
            "id": str(item.get("trackId", "")),
            "name": item.get("trackName", "Unknown Episode"),
            "show_name": item.get("collectionName", "Unknown Show"),
            "description": (item.get("description") or item.get("shortDescription") or "")[:500],
            "release_date": rd.strftime("%Y-%m-%d"),
            "duration_ms": duration_ms,
            "duration_min": duration_min,
            "external_url": item.get("trackViewUrl", ""),
            "feed_url": item.get("feedUrl", ""),
            "artist_name": item.get("artistName", ""),
        })

        if len(episodes) >= max_results:
            break

    episodes.sort(key=lambda x: x["release_date"], reverse=True)
    return episodes


def print_episodes(episodes):
    if not episodes:
        print("\nNo episodes found matching the criteria.")
        return

    print(f"\n{'='*80}")
    print(f"Found {len(episodes)} episodes:")
    print(f"{'='*80}\n")

    for i, ep in enumerate(episodes, 1):
        print(f"  [{i}] {ep['name']}")
        print(f"      Show: {ep['show_name']}  ({ep['artist_name']})")
        print(f"      Date: {ep['release_date']}  |  Duration: {ep['duration_min']} min")
        if ep.get("feed_url"):
            print(f"      RSS:  {ep['feed_url'][:80]}...")
        if ep["description"]:
            desc = ep["description"][:150]
            if len(ep["description"]) > 150:
                desc += "..."
            print(f"      Desc: {desc}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Search for podcast episodes (via iTunes API)")
    parser.add_argument("--topic", required=True, help="Search topic")
    parser.add_argument("--days-back", type=int, default=30, help="How many days back to search (default: 30)")
    parser.add_argument("--max", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("--country", default="US", help="Country code (default: US)")
    parser.add_argument("--output-dir", required=True, help="Directory to save episodes.json")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    episodes = search_episodes(args.topic, args.days_back, args.max, args.country)
    print_episodes(episodes)

    output_path = output_dir / "episodes.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(episodes)} episodes to: {output_path}")


if __name__ == "__main__":
    main()
