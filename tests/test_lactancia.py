"""Lactancia column normalization (2021–2023)."""

from __future__ import annotations

import pytest

from tests.helpers import load_bundle

NORMALIZED_CORE = (
    "amamantar",
    "aun_amamanta",
    "ayer_amamanto",
    "amamanta_libre",
    "alimento_formula",
    "Sexo",
    "Entidad",
    "Region",
    "Edad",
    "Edad_meses",
)

RENAMED_FROM_OFFICIAL = {
    2021: {"amamantar": "lac02", "no_Formula": "LAC03A", "Edad": "h0303"},
    2022: {"amamantar": "lac02", "no_Formula": "lac03A", "Edad": "h0303"},
    2023: {"amamantar": "lac02", "no_Formula": "lac03A", "Edad": "h0303"},
}


@pytest.mark.parametrize("year", [2021, 2022, 2023])
def test_lactancia_core_variables_normalized(year):
    meta, summary, _ = load_bundle("lactancia", year)
    for var in NORMALIZED_CORE:
        assert var in meta["columns"], f"{var} missing in lactancia/{year} meta"
        assert var in summary["prevalence"] or var in summary["distribution"], (
            f"{var} has no aggregates in lactancia/{year}"
        )


@pytest.mark.parametrize("year", [2021, 2022, 2023])
def test_lactancia_source_column_traceability(year):
    meta, _, _ = load_bundle("lactancia", year)
    expected = RENAMED_FROM_OFFICIAL[year]
    for short, original in expected.items():
        col = meta["columns"][short]
        assert col.get("source_column", short).lower() == original.lower()


def test_lactancia_2018_unchanged_short_names():
    meta, _, _ = load_bundle("lactancia", 2018)
    assert "amamantar" in meta["columns"]
    assert meta["columns"]["amamantar"].get("source_column") is None
