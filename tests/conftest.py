"""Shared fixtures for ENSANUT Explorer data pipeline tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
SCRIPTS = SITE / "scripts"
DATA = SITE / "docs" / "data"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import prepare_data  # noqa: E402


@pytest.fixture
def catalog() -> dict:
    return prepare_data.load_catalog()


@pytest.fixture
def mvp_datasets(catalog: dict) -> list[tuple[str, int]]:
    pairs: list[tuple[str, int]] = []
    for module_id in catalog["mvp_modules"]:
        for year in catalog["modules"][module_id]["years"]:
            pairs.append((module_id, year))
    return pairs


@pytest.fixture
def dataset_dir(tmp_path, monkeypatch):
    """Redirect pipeline output to a temporary directory."""

    out = tmp_path / "data"
    monkeypatch.setattr(prepare_data, "OUT", out)
    return out


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
