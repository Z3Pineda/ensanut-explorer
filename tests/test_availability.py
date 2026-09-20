"""Catalog variables_by_year and UI filtering logic."""

from __future__ import annotations

import json
from pathlib import Path

import prepare_data

SITE = Path(__file__).resolve().parents[1]


def test_catalog_has_variables_by_year_for_mvp_modules(catalog):
    for module_id in catalog["mvp_modules"]:
        by_year = catalog["modules"][module_id].get("variables_by_year")
        assert by_year, f"{module_id} missing variables_by_year"
        for year in catalog["modules"][module_id]["years"]:
            assert str(year) in by_year, f"{module_id}/{year} missing in variables_by_year"


def test_year_variables_match_meta_types(catalog):
    data = SITE / "docs" / "data"
    for module_id in catalog["mvp_modules"]:
        by_year = catalog["modules"][module_id]["variables_by_year"]
        for year_str, vars_ in by_year.items():
            meta_path = data / module_id / year_str / "meta.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            for col in vars_.get("categorical", []):
                assert meta["columns"][col]["type"] == "categorical"
            for col in vars_.get("continuous", []):
                assert meta["columns"][col]["type"] == "continuous"


def test_salud_missing_vars_not_listed_for_year(catalog):
    """Variables absent from a year must not appear in variables_by_year."""
    by_2021 = catalog["modules"]["salud"]["variables_by_year"]["2021"]
    all_vars = set(by_2021.get("categorical", []) + by_2021.get("continuous", []))
    assert "De_Fatiga" not in all_vars
    assert "Infeccion_viasurinarias" not in all_vars


def test_get_year_variables_helper(catalog):
    cats, conts = prepare_data.get_year_variables(catalog["modules"]["lactancia"], 2021)
    assert "amamantar" in cats
    assert "Edad" in conts
