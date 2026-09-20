#!/usr/bin/env python3
"""Benchmark data pipeline and integrity validation."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
SCRIPTS = SITE / "scripts"
for path in (SITE, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import prepare_data  # noqa: E402
from tests.helpers import (  # noqa: E402
    DATA,
    load_bundle,
    pick_check_columns,
    recompute_overall_distribution,
    recompute_overall_prevalence,
)


def fmt_ms(seconds: float) -> str:
    return f"{seconds * 1000:.1f}"


def benchmark_pipeline(catalog: dict) -> list[dict]:
    rows: list[dict] = []
    for module_id in catalog["mvp_modules"]:
        for year in catalog["modules"][module_id]["years"]:
            src = prepare_data.ZENODO / catalog["modules"][module_id]["source_dir"] / str(year)
            if not (src / catalog["modules"][module_id]["data_file"]).exists():
                continue
            t0 = time.perf_counter()
            df = prepare_data.normalize_dataframe(
                __import__("pandas").read_csv(
                    src / catalog["modules"][module_id]["data_file"],
                    encoding="utf-8",
                    low_memory=False,
                )
            )
            csv_meta = prepare_data.parse_description_csv(src / "description.csv")
            json_path = prepare_data.find_description_json(
                catalog["modules"][module_id]["source_dir"], year
            )
            json_short, json_param = (
                prepare_data.parse_description_json(json_path) if json_path else ({}, {})
            )
            desc_meta = prepare_data.merge_desc_meta(
                csv_meta, json_short, json_param, list(df.columns)
            )
            meta = prepare_data.build_meta(df, catalog["modules"][module_id], year, desc_meta)
            group_cols = [
                c for c in catalog["demographic_columns"] if c in df.columns
            ]
            summary = prepare_data.build_summary(df, meta, group_cols)
            elapsed = time.perf_counter() - t0
            rows.append(
                {
                    "task": "pipeline",
                    "module": module_id,
                    "year": year,
                    "rows": len(df),
                    "prevalence_cols": len(summary["prevalence"]),
                    "distribution_cols": len(summary["distribution"]),
                    "seconds": elapsed,
                }
            )
    return rows


def benchmark_integrity(catalog: dict) -> list[dict]:
    rows: list[dict] = []
    for module_id in catalog["mvp_modules"]:
        for year in catalog["modules"][module_id]["years"]:
            if not (DATA / module_id / str(year) / "data.csv").exists():
                continue
            t0 = time.perf_counter()
            meta, summary, df = load_bundle(module_id, year)
            cat_col, cont_col = pick_check_columns(catalog, module_id)
            if cat_col and cat_col in summary["prevalence"]:
                recompute_overall_prevalence(df, cat_col)
            if cont_col and cont_col in summary["distribution"]:
                recompute_overall_distribution(df, cont_col)
            elapsed = time.perf_counter() - t0
            rows.append(
                {
                    "task": "integrity",
                    "module": module_id,
                    "year": year,
                    "rows": meta["rows"],
                    "seconds": elapsed,
                }
            )
    return rows


def print_table(title: str, rows: list[dict]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    if not rows:
        print("(no rows)")
        return
    header = f"{'module':<14} {'year':<6} {'rows':>8} {'ms':>10}"
    if rows[0]["task"] == "pipeline":
        header += f" {'prev':>5} {'dist':>5}"
    print(header)
    total_s = 0.0
    for row in rows:
        total_s += row["seconds"]
        line = f"{row['module']:<14} {row['year']:<6} {row['rows']:>8} {fmt_ms(row['seconds']):>10}"
        if row["task"] == "pipeline":
            line += f" {row['prevalence_cols']:>5} {row['distribution_cols']:>5}"
        print(line)
    print(f"{'TOTAL':<14} {'':<6} {'':>8} {fmt_ms(total_s):>10}")


def main() -> None:
    catalog = prepare_data.load_catalog()
    print("ENSANUT Explorer — data benchmark")
    print(f"Site: {SITE}")

    pipeline_rows = benchmark_pipeline(catalog)
    integrity_rows = benchmark_integrity(catalog)

    print_table("Pipeline (read CSV + meta + summary, no write)", pipeline_rows)
    print_table("Integrity (reload CSV + recompute spot checks)", integrity_rows)

    total_pipeline = sum(r["seconds"] for r in pipeline_rows)
    total_integrity = sum(r["seconds"] for r in integrity_rows)
    print(
        f"\nSummary: {len(pipeline_rows)} datasets | "
        f"pipeline {fmt_ms(total_pipeline)} ms | "
        f"integrity {fmt_ms(total_integrity)} ms | "
        f"combined {fmt_ms(total_pipeline + total_integrity)} ms"
    )


if __name__ == "__main__":
    main()
