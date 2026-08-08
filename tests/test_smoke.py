import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_DIR / "podcast-research" / "scripts"


def load_script(name):
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class PodcastSkillTests(unittest.TestCase):
    def test_search_writes_source_fields(self):
        search = load_script("search_podcasts")
        payload = {
            "results": [{
                "trackId": 1,
                "trackName": "AI Agents Today",
                "collectionName": "Test Show",
                "description": "Test description",
                "releaseDate": "2099-01-01T00:00:00Z",
                "trackTimeMillis": 60000,
                "trackViewUrl": "https://example.com/episode",
                "feedUrl": "https://example.com/feed.xml",
                "artistName": "Host",
            }]
        }
        with mock.patch.object(search.requests, "get", return_value=FakeResponse(payload)):
            episodes = search.search_episodes("AI agents", days_back=36500, max_results=1)
        self.assertEqual(episodes[0]["name"], "AI Agents Today")
        self.assertEqual(episodes[0]["feed_url"], "https://example.com/feed.xml")

    def test_filename_is_safe_on_windows(self):
        downloader = load_script("audio_downloader")
        result = downloader.sanitize_filename('A/B:C*D?E"F<G>H|I')
        self.assertNotRegex(result, r'[\\/:*?"<>|]')
        self.assertEqual(downloader.sanitize_filename("CON"), "_CON")

    def test_auto_language_becomes_none(self):
        transcriber = load_script("transcriber")
        self.assertIn("turbo", transcriber.FASTER_MODELS)
        self.assertIn("turbo", transcriber.MLX_MODELS)

    def test_windows_selects_faster_whisper(self):
        transcriber = load_script("transcriber")
        with mock.patch.object(transcriber.platform, "system", return_value="Windows"), \
             mock.patch.object(transcriber.platform, "machine", return_value="AMD64"), \
             mock.patch.object(transcriber, "module_exists", side_effect=lambda name: name == "faster_whisper"):
            self.assertEqual(transcriber.choose_backend("turbo"), "faster")

    def test_setup_windows_backend_import(self):
        setup = load_script("check_setup")
        with mock.patch.object(setup.platform, "system", return_value="Windows"), \
             mock.patch.object(setup.platform, "machine", return_value="AMD64"), \
             mock.patch.object(setup, "module_imports", side_effect=lambda name: name == "faster_whisper"):
            self.assertEqual(setup.local_backend(), "faster-whisper")

    def test_all_cli_scripts_compile(self):
        for path in SCRIPTS_DIR.glob("*.py"):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")


if __name__ == "__main__":
    unittest.main()
