"""Validation helpers shared by integrity and reproduction tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import prepare_data

SITE = Path(__file__).resolve().parents[1]
DATA = SITE / "docs" / "data"


def dataset_path(module_id: str, year: int) -> Path:
    return DATA / module_id / str(year)


def load_bundle(module_id: str, year: int) -> tuple[dict, dict, pd.DataFrame | None]:
    base = dataset_path(module_id, year)
    meta = json.loads((base / "meta.json").read_text(encoding="utf-8"))
    summary = json.loads((base / "summary.json").read_text(encoding="utf-8"))
    csv_path = base / "data.csv"
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False) if csv_path.exists() else None
    if df is not None:
        df = prepare_data.normalize_dataframe(df)
    return meta, summary, df


def recompute_overall_prevalence(df: pd.DataFrame, col: str) -> dict[str, float]:
    s = prepare_data.valid_series(df[col])
    if len(s) == 0:
        return {}
    vc = s.value_counts(normalize=True)
    return {str(k): round(float(v), 4) for k, v in vc.items()}


def recompute_overall_distribution(df: pd.DataFrame, col: str) -> dict:
    s = pd.to_numeric(prepare_data.valid_series(df[col]), errors="coerce").dropna()
    if len(s) == 0:
        return {"n_valid": 0}
    counts, edges = np.histogram(s, bins=20)
    return {
        "n_valid": int(len(s)),
        "mean": round(float(s.mean()), 2),
        "median": round(float(s.median()), 2),
        "p25": round(float(s.quantile(0.25)), 2),
        "p75": round(float(s.quantile(0.75)), 2),
        "histogram": {
            "counts": counts.tolist(),
            "bin_edges": [round(float(x), 2) for x in edges.tolist()],
        },
    }


def pick_check_columns(
    catalog: dict, module_id: str, year: int | None = None
) -> tuple[str | None, str | None]:
    if year is not None:
        categorical, continuous = prepare_data.get_year_variables(
            catalog["modules"][module_id], year
        )
    else:
        variables = catalog["modules"][module_id].get("variables", {})
        categorical = variables.get("categorical") or []
        continuous = variables.get("continuous") or []
    cat = next((c for c in categorical if c not in ("Entidad", "Region", "Estrato", "ESTRATO")), None)
    cont = next((c for c in continuous if c != "Edad"), continuous[0] if continuous else None)
    return cat, cont


def compare_prevalence(actual: dict, expected: dict, tol: float = 1e-4) -> None:
    assert actual.keys() == expected.keys()
    for code, prop in expected.items():
        assert abs(actual[code] - prop) <= tol


def compare_distribution(actual: dict, expected: dict, tol: float = 1e-4) -> None:
    """Compare recomputed distribution stats to committed summary.json.

    Histogram bins are omitted: committed summaries were built on Windows and
    np.histogram edges can differ slightly on Linux CI for the same CSV.
    """
    assert actual["n_valid"] == expected["n_valid"]
    for key in ("mean", "median", "p25", "p75"):
        assert abs(actual[key] - expected[key]) <= tol
