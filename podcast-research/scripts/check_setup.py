#!/usr/bin/env python3
"""Check whether podcast-research can run on the current machine."""

import argparse
import importlib
import importlib.util
import os
import platform
import shutil
import sys
from pathlib import Path


MIN_FREE_GB = 5


def module_exists(name):
    return importlib.util.find_spec(name) is not None


def module_imports(name):
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def local_backend():
    machine = platform.machine().lower()
    if platform.system() == "Darwin" and machine in {"arm64", "aarch64"} and module_imports("mlx_whisper"):
        return "mlx-whisper"
    if module_imports("faster_whisper"):
        return "faster-whisper"
    if module_imports("mlx_whisper"):
        return "mlx-whisper"
    return None


def add(results, name, status, detail, required=True):
    results.append((name, status, detail, required))


def run_checks(skill_dir):
    results = []
    version_ok = sys.version_info >= (3, 10)
    add(results, "Python", "PASS" if version_ok else "FAIL", platform.python_version())

    try:
        free_gb = shutil.disk_usage(skill_dir).free / (1024 ** 3)
        disk_ok = free_gb >= MIN_FREE_GB
        add(results, "Free disk", "PASS" if disk_ok else "FAIL", f"{free_gb:.1f} GB; {MIN_FREE_GB} GB required")
    except OSError as exc:
        add(results, "Free disk", "FAIL", str(exc))

    for module, label in (
        ("requests", "requests"),
        ("markdown2", "markdown2"),
        ("docx", "python-docx"),
        ("yt_dlp", "yt-dlp"),
    ):
        installed = module_exists(module)
        add(results, label, "PASS" if installed else "FAIL", "installed" if installed else "missing")

    backend = local_backend()
    add(results, "Local transcription", "PASS" if backend else "FAIL", backend or "install the platform backend")

    required_files = (
        skill_dir / "SKILL.md",
        skill_dir / "scripts" / "search_podcasts.py",
        skill_dir / "scripts" / "audio_downloader.py",
        skill_dir / "scripts" / "transcriber.py",
        skill_dir / "scripts" / "md_to_docx.py",
    )
    missing = [path.name for path in required_files if not path.is_file()]
    add(results, "Skill files", "PASS" if not missing else "FAIL", "complete" if not missing else f"missing: {', '.join(missing)}")

    ffmpeg = shutil.which("ffmpeg")
    add(results, "FFmpeg fallback", "PASS" if ffmpeg else "WARN", ffmpeg or "optional; needed for YouTube and API splitting", required=False)

    api_ready = module_exists("openai") and bool(os.environ.get("OPENAI_API_KEY"))
    add(results, "OpenAI API fallback", "PASS" if api_ready else "WARN", "configured" if api_ready else "optional; package and key not configured", required=False)
    return results


def main():
    parser = argparse.ArgumentParser(description="Check podcast-research requirements")
    parser.add_argument("--skill-dir", default=str(Path(__file__).resolve().parents[1]), help="Path to the podcast-research Skill")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve()
    results = run_checks(skill_dir)
    print(f"Platform: {platform.system()} {platform.machine()} | Python: {sys.executable}")
    for name, status, detail, _required in results:
        print(f"{status:4}  {name:22} {detail}")

    failures = [name for name, status, _detail, required in results if required and status != "PASS"]
    if failures:
        print(f"\nNOT READY: fix required checks: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("\nREADY: required setup checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
