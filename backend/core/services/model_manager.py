"""Stubbed model_manager after DeepSeek 1.5B removal."""
from pathlib import Path


def status() -> dict:
    return {
        "status": "removed",
        "progress": 0,
        "detail": "Local DeepSeek 1.5B model has been removed. Use Gemini API.",
        "repo": "",
        "revision": "",
        "path": "",
        "installed": False,
        "auto_download": False,
        "loaded": False,
        "problems": [],
    }


def ensure_ready():
    pass


def download():
    pass


def load():
    pass


def config_problems():
    return []


def model_label():
    return "removed"
