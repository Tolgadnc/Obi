import copy
import shutil
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def video(youtube="AAAAAAAAAAA", approved=True, **extra):
    base = {"youtube": youtube, "title": "A video", "channel": "A channel", "approved": approved}
    return base | extra


TECHNIQUES = [
    {
        "id": "ushiro-ukemi",
        "name": "Ushiro-ukemi",
        "category": "ukemi",
        "translation": {"nl": "Achterwaartse valbreking", "en": "Backward breakfall"},
        "videos": [video("AAAAAAAAAAA")],
    },
    {
        "id": "o-soto-gari",
        "name": "O-soto-gari",
        "category": "nage-waza",
        "group": "ashi-waza",
        "translation": {"nl": "Grote buitenwaartse maaiworp", "en": "Major outer reap"},
        "videos": [video("BBBBBBBBBBB", start=12, end=40), video("CCCCCCCCCCC", approved=False)],
    },
    {
        "id": "tokui-waza",
        "name": "Tokui-waza",
        "category": "oefenvormen",
        "translation": {"nl": "Voorkeurstechniek", "en": "Favourite technique"},
        "description": {"nl": "Kies je eigen worp.", "en": "Choose your own throw."},
    },
]

BELTS = [
    {
        "id": "wit",
        "kyu": 6,
        "colour": "#ffffff",
        "name": {"nl": "Witte gordel", "en": "White belt"},
        "slug": {"nl": "wit", "en": "white"},
        "intro": {"nl": "Start.", "en": "Start."},
    },
    {
        "id": "geel",
        "kyu": 5,
        "colour": "#f6c90e",
        "name": {"nl": "Gele gordel", "en": "Yellow belt"},
        "slug": {"nl": "geel", "en": "yellow"},
        "syllabus": {"basis": ["ushiro-ukemi", "o-soto-gari"]},
    },
    {
        "id": "oranje",
        "kyu": 4,
        "colour": "#f28c00",
        "name": {"nl": "Oranje gordel", "en": "Orange belt"},
        "slug": {"nl": "oranje", "en": "orange"},
        "syllabus": {"verdieping": ["o-soto-gari"], "verpersoonlijking": ["tokui-waza"]},
    },
]


@pytest.fixture
def data():
    """Editable copies of a small, valid data set: data["belts"], data["techniques"]."""
    return {"belts": copy.deepcopy(BELTS), "techniques": copy.deepcopy(TECHNIQUES)}


@pytest.fixture
def write_data(tmp_path):
    """Write a data set to a folder (with the real ui.yaml) and return the folder."""

    def write(data) -> Path:
        folder = tmp_path / "data"
        folder.mkdir(exist_ok=True)
        for name in ("belts", "techniques"):
            text = yaml.safe_dump(data[name], allow_unicode=True, sort_keys=False)
            (folder / f"{name}.yaml").write_text(text, encoding="utf-8")
        shutil.copy(ROOT / "data" / "ui.yaml", folder / "ui.yaml")
        return folder

    return write
