"""Offline release checks with synthetic data and isolated local state."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

ROOT = Path(__file__).resolve().parents[1]


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.environment = patch.dict(os.environ, {
            "VIDEOTRANSFORMER_DATA_DIR": str(cls.root / "data"),
            "VIDEOTRANSFORMER_LOGS_DIR": str(cls.root / "logs"),
            "PEXELS_API_KEY": "synthetic-test-key",
        })
        cls.environment.start()
        spec = importlib.util.spec_from_file_location("release_app", ROOT / "web/app.py")
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)
        cls.module.app.config["TESTING"] = True
        cls.client = cls.module.app.test_client()

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("release_app", None)
        cls.environment.stop()
        cls.temp.cleanup()

    def setUp(self):
        self.module.config["pexels_api_key"] = "synthetic-test-key"
        self.module.config["max_file_size_mb"] = 30

    def test_templates_are_english_and_never_embed_the_key(self):
        for url in ("/", "/videos"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn('lang="en"', response.text)
            self.assertNotIn("synthetic-test-key", response.text)
            self.assertNotIn("Télécharger", response.text)

    def test_config_get_only_reports_key_presence(self):
        response = self.client.get("/api/config")
        self.assertTrue(response.json["pexels_configured"])
        self.assertNotIn("pexels_api_key", response.json)
        self.assertNotIn("synthetic-test-key", response.text)

    def test_config_update_does_not_echo_secret_or_change_private_paths(self):
        original = self.module.config["download_dir"]
        response = self.client.post("/api/config", json={
            "pexels_api_key": "synthetic-replacement-key",
            "download_dir": "untrusted-path",
            "max_file_size_mb": 45,
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("synthetic-replacement-key", response.text)
        self.assertEqual(self.module.config["download_dir"], original)
        self.assertEqual(self.module.config["max_file_size_mb"], 45)
        self.client.post("/api/config", json={"pexels_api_key": ""})
        self.assertEqual(self.module.config["pexels_api_key"], "synthetic-replacement-key")

    def test_invalid_config_does_not_mutate_current_key(self):
        for payload in ([], {"max_file_size_mb": 0}, {"max_file_size_mb": "invalid"},
                        {"pexels_api_key": ["invalid"]}):
            response = self.client.post("/api/config", json=payload)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(self.module.config["pexels_api_key"], "synthetic-test-key")

    def test_import_does_not_start_background_download_worker(self):
        self.assertFalse(hasattr(self.module, "worker_thread"))
        self.assertFalse(self.module.is_processing)

    def test_task_is_queued_without_downloading(self):
        response = self.client.post("/api/task", json={
            "type": "download_direct", "name": "Synthetic task",
            "params": {"url": "https://example.com/video.mp4"},
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["task"]["status"], "queued")
        task = self.module.task_queue.get_nowait()
        self.assertEqual(task["name"], "Synthetic task")
        self.module.task_queue.task_done()

    def test_markdown_url_and_windows_filename_normalization(self):
        self.assertEqual(self.module.normalize_pasted_url(
            "[Example](https://example.com/video.mp4)"), "https://example.com/video.mp4")
        self.assertEqual(self.module._sanitize_filename("Example： test?"), "Example- test")

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is not installed")
    def test_real_ffmpeg_conversion_uses_only_synthetic_audio(self):
        source = self.root / "synthetic.wav"
        with wave.open(str(source), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(b"\0\0" * 1600)
        before = source.read_bytes()
        result = self.module.run_convert_file({
            "mode": "file", "source": str(source), "format": "flac", "overwrite": False,
        })
        self.assertEqual(result["converted"], 1)
        self.assertEqual(source.read_bytes(), before)
        output = source.with_suffix(".flac")
        self.assertTrue(output.is_file())
        original_output = output.read_bytes()
        again = self.module.run_convert_file({
            "mode": "file", "source": str(source), "format": "flac", "overwrite": False,
        })
        self.assertEqual(again["skipped"], 1)
        self.assertEqual(output.read_bytes(), original_output)


class CleanupTests(unittest.TestCase):
    def test_preview_and_apply_preserve_media_and_documentation(self):
        from src.cleanup import clean
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "cache").mkdir()
            (root / "cache/transient.txt").write_text("temporary", encoding="utf-8")
            (root / "data").mkdir()
            (root / "data/example.mp4").write_bytes(b"synthetic")
            (root / "README.md").write_text("Keep documentation", encoding="utf-8")
            clean(root=root)
            self.assertTrue((root / "cache/transient.txt").exists())
            clean(apply=True, root=root)
            self.assertFalse((root / "cache").exists())
            self.assertTrue((root / "data/example.mp4").exists())
            self.assertTrue((root / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
