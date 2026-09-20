"""Re-run prepare_data and compare against committed artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import prepare_data
from tests.helpers import (
    DATA,
    compare_distribution,
    compare_prevalence,
    load_bundle,
    pick_check_columns,
)

SITE = Path(__file__).resolve().parents[1]


def pytest_generate_tests(metafunc):
    if {"module_id", "year"} <= set(metafunc.fixturenames):
        catalog = json.loads((SITE / "catalog.json").read_text(encoding="utf-8"))
        pairs = [
            (mid, year)
            for mid in catalog["mvp_modules"]
            for year in catalog["modules"][mid]["years"]
            if (DATA / mid / str(year) / "meta.json").exists()
        ]
        metafunc.parametrize("module_id,year", pairs, ids=[f"{m}-{y}" for m, y in pairs])


def test_pipeline_reproduces_summary(module_id, year, catalog, dataset_dir):
    prepare_data.process_module_year(module_id, year, copy_csv=False)

    generated_dir = dataset_dir / module_id / str(year)
    assert (generated_dir / "meta.json").exists()
    assert (generated_dir / "summary.json").exists()

    new_meta = json.loads((generated_dir / "meta.json").read_text(encoding="utf-8"))
    new_summary = json.loads((generated_dir / "summary.json").read_text(encoding="utf-8"))
    old_meta, old_summary, _ = load_bundle(module_id, year)

    assert new_meta["rows"] == old_meta["rows"]
    assert new_summary["n_rows"] == old_summary["n_rows"]
    assert set(new_meta["columns"]) == set(old_meta["columns"])

    cat_col, cont_col = pick_check_columns(catalog, module_id, year)

    if cat_col and cat_col in old_summary["prevalence"]:
        compare_prevalence(
            new_summary["prevalence"][cat_col]["overall"],
            old_summary["prevalence"][cat_col]["overall"],
        )

    if cont_col and cont_col in old_summary["distribution"]:
        compare_distribution(
            new_summary["distribution"][cont_col],
            old_summary["distribution"][cont_col],
        )
