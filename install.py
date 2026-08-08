#!/usr/bin/env python3
"""Install the podcast-research skill for Claude Code and/or Codex."""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent
SOURCE_DIR = REPO_DIR / "podcast-research"
OBSOLETE_FILES = (".env", "scripts/spotify_search.py")


def detected_agents():
    home = Path.home()
    agents = []
    if (home / ".claude").exists():
        agents.append("claude")
    if (home / ".codex").exists():
        agents.append("codex")
    return agents or ["claude", "codex"]


def destinations(agent):
    selected = detected_agents() if agent == "auto" else (["claude", "codex"] if agent == "both" else [agent])
    home = Path.home()
    mapping = {
        "claude": home / ".claude" / "skills" / "podcast-research",
        "codex": home / ".codex" / "skills" / "podcast-research",
    }
    return [mapping[name] for name in selected]


def install_dependencies():
    print(f"Installing dependencies with {sys.executable}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REPO_DIR / "requirements.txt")],
        check=True,
    )


def copy_skill(destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE_DIR, destination, dirs_exist_ok=True)
    for relative_path in OBSOLETE_FILES:
        obsolete = destination / relative_path
        if obsolete.is_file():
            obsolete.unlink()
    print(f"Installed skill: {destination}")


def run_check(destination):
    command = [
        sys.executable,
        str(destination / "scripts" / "check_setup.py"),
        "--skill-dir",
        str(destination),
    ]
    return subprocess.run(command).returncode


def main():
    parser = argparse.ArgumentParser(description="Install the podcast-research Agent skill")
    parser.add_argument(
        "--agent",
        choices=("auto", "claude", "codex", "both"),
        default="auto",
        help="Agent target. Default: detect installed Claude Code/Codex directories.",
    )
    parser.add_argument("--skip-deps", action="store_true", help="Copy the skill without installing Python packages")
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        parser.error("Python 3.10 or newer is required")
    if not SOURCE_DIR.is_dir():
        parser.error(f"Skill source not found: {SOURCE_DIR}")

    print(f"Platform: {platform.system()} {platform.machine()}")
    print("Disk guidance: keep at least 5 GB free; 8 GB is recommended for models and audio.")

    if not args.skip_deps:
        install_dependencies()

    targets = destinations(args.agent)
    for target in targets:
        copy_skill(target)

    failures = sum(run_check(target) != 0 for target in targets)
    if failures:
        print("\nInstallation finished, but setup checks failed. Follow the printed fixes above.", file=sys.stderr)
        return 1

    print("\nSUCCESS: podcast-research is installed and its required runtime is ready.")
    print("Restart the Agent if it was already running, then ask: 'Use podcast-research to research podcasts about AI agents.'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
