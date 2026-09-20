"""Integrity checks on committed docs/data artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers import (
    DATA,
    compare_distribution,
    compare_prevalence,
    load_bundle,
    pick_check_columns,
    recompute_overall_distribution,
    recompute_overall_prevalence,
)

SITE = Path(__file__).resolve().parents[1]


def test_manifest_matches_filesystem(catalog):
    manifest_path = DATA / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for module_id in catalog["mvp_modules"]:
        assert module_id in manifest["modules"]
        for year in catalog["modules"][module_id]["years"]:
            year_key = str(year)
            assert year_key in manifest["modules"][module_id]["years"]
            rel = manifest["modules"][module_id]["years"][year_key]["meta"]
            assert (SITE / "docs" / rel).exists()


def pytest_generate_tests(metafunc):
    if {"module_id", "year"} <= set(metafunc.fixturenames):
        catalog_path = SITE / "catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        pairs = [
            (mid, year)
            for mid in catalog["mvp_modules"]
            for year in catalog["modules"][mid]["years"]
            if (DATA / mid / str(year) / "meta.json").exists()
        ]
        metafunc.parametrize("module_id,year", pairs, ids=[f"{m}-{y}" for m, y in pairs])


def test_meta_summary_row_counts(module_id, year):
    meta, summary, _ = load_bundle(module_id, year)
    assert meta["rows"] == summary["n_rows"]


def test_catalog_variables_present(module_id, year, catalog):
    """Declared variables that exist in the CSV must appear in meta.json."""
    meta, _, df = load_bundle(module_id, year)
    if df is None:
        pytest.skip("data.csv not present")
    declared = set(catalog["modules"][module_id]["variables"].get("categorical", []))
    declared.update(catalog["modules"][module_id]["variables"].get("continuous", []))
    available = set(df.columns)
    expected = declared & available
    missing = sorted(expected - set(meta["columns"].keys()))
    assert not missing, f"{module_id}/{year} missing catalog vars: {missing}"


def test_prevalence_proportions_sum_to_one(module_id, year, catalog):
    _, summary, df = load_bundle(module_id, year)
    if df is None:
        pytest.skip("data.csv not present")
    cat_col, _ = pick_check_columns(catalog, module_id)
    if not cat_col or cat_col not in summary["prevalence"]:
        pytest.skip("no categorical check column")
    overall = summary["prevalence"][cat_col]["overall"]
    assert overall
    assert abs(sum(overall.values()) - 1.0) < 1e-3


def test_aggregates_match_csv(module_id, year, catalog):
    meta, summary, df = load_bundle(module_id, year)
    if df is None:
        pytest.skip("data.csv not present")

    cat_col, cont_col = pick_check_columns(catalog, module_id)

    if cat_col and cat_col in summary["prevalence"]:
        expected = summary["prevalence"][cat_col]["overall"]
        actual = recompute_overall_prevalence(df, cat_col)
        compare_prevalence(actual, expected)

    if cont_col and cont_col in summary["distribution"]:
        expected = summary["distribution"][cont_col]
        actual = recompute_overall_distribution(df, cont_col)
        compare_distribution(actual, expected)

    assert meta["module"] == module_id
    assert meta["year"] == year
