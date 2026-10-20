"""Portable paths and private settings for local installations."""
import json
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("VIDEOTRANSFORMER_DATA_DIR", PROJECT_DIR / "data")).expanduser().resolve()
LOGS_DIR = Path(os.environ.get("VIDEOTRANSFORMER_LOGS_DIR", PROJECT_DIR / "logs")).expanduser().resolve()


def get_pexels_key():
    """Prefer an environment variable; never publish private settings."""
    if "PEXELS_API_KEY" in os.environ:
        return os.environ["PEXELS_API_KEY"].strip()
    settings = DATA_DIR / "private_settings.json"
    if settings.is_file():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
            value = data.get("pexels_api_key", "")
            return value.strip() if isinstance(value, str) else ""
        except (OSError, ValueError, AttributeError):
            return ""
    return ""
