#!/usr/bin/env python3
"""
Genera docs/data/{modulo}/{año}/ para GitHub Pages.

Fuentes (relativas a PROY_ENSANUT):
  - ZENODO/{source_dir}/{year}/{data_file}     → data.csv
  - ZENODO/{source_dir}/{year}/description.csv → meta.json (columnas)
  - ZENODO/{source_dir}/{year}/texto.txt
  - ZENODO_JSON/.../description.json (opcional, enriquece etiquetas)

Uso:
  python prepare_data.py --module salud --year 2018
  python prepare_data.py --mvp
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]  # PROY_ENSANUT
SITE = Path(__file__).resolve().parents[1]
CATALOG_PATH = SITE / "catalog.json"
ZENODO = ROOT / "ZENODO"
ZENODO_JSON = ROOT / "ZENODO_JSON"
OUT = SITE / "docs" / "data"

MISSING_CODES = {888, 888.0, 999, 999.0, 8888, 8888.0, 222.2, 222.222}
MIN_CELL_N = 30


def load_catalog() -> dict:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def parse_description_csv(path: Path) -> dict[str, dict]:
    """Convierte description.csv a meta parcial keyed by Nombre corto."""
    if not path.exists():
        return {}
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return {}
    if df.empty or "Nombre corto" not in df.columns:
        return {}
    meta: dict[str, dict] = {}
    for _, row in df.iterrows():
        col = str(row.get("Nombre corto", "")).strip()
        if not col or col == "nan":
            continue
        desc = str(row.get("Descripción", "")).strip()
        param = str(row.get("Parámetro ENSANUT", "")).strip()
        values = {}
        if desc and desc not in ("", "nan"):
            for part in re.split(r",\s*", desc):
                m = re.match(r"([\d.]+)\s*:\s*(.+)", part.strip())
                if m:
                    values[m.group(1).rstrip(".0")] = m.group(2).strip()
        meta[col] = {
            "label": col.replace("_", " "),
            "ensanut_param": param if param != "nan" else None,
            "type": "categorical" if values else "unknown",
            "values": values,
        }
    return meta


def infer_column_types(df: pd.DataFrame, module_cfg: dict) -> dict[str, str]:
    declared = {}
    for t in ("continuous", "categorical"):
        for c in module_cfg.get("variables", {}).get(t, []):
            declared[c] = t
    for col in df.columns:
        if col in declared:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            nunique = df[col].nunique(dropna=True)
            declared[col] = "categorical" if nunique <= 15 else "continuous"
        else:
            declared[col] = "categorical"
    return declared


def build_meta(
    df: pd.DataFrame,
    module_cfg: dict,
    year: int,
    desc_meta: dict[str, dict],
) -> dict:
    types = infer_column_types(df, module_cfg)
    columns: dict[str, dict] = {}
    for col in df.columns:
        if col == "ID":
            continue
        entry = {
            "label": desc_meta.get(col, {}).get("label", col.replace("_", " ")),
            "type": types.get(col, "unknown"),
            "ensanut_param": desc_meta.get(col, {}).get("ensanut_param"),
        }
        if entry["type"] == "categorical" and col in desc_meta and desc_meta[col].get("values"):
            entry["values"] = desc_meta[col]["values"]
        columns[col] = entry
    return {
        "module": module_cfg["id"],
        "year": year,
        "source": f"ENSANUT {year} — {module_cfg['data_file']}",
        "population": module_cfg.get("population"),
        "rows": int(len(df)),
        "columns": columns,
    }


def valid_series(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="ignore")
    if pd.api.types.is_numeric_dtype(s):
        return s[~s.isna() & ~s.isin(MISSING_CODES)]
    return s.dropna()


def prevalence_block(df: pd.DataFrame, col: str, group_cols: list[str]) -> dict:
    s = valid_series(df[col])
    idx = s.index
    out: dict = {
        "n_valid": int(len(s)),
        "overall": {},
    }
    if len(s) == 0:
        return out
    vc = s.value_counts(normalize=True)
    out["overall"] = {str(k): round(float(v), 4) for k, v in vc.items()}
    for gcol in group_cols:
        if gcol not in df.columns or gcol == col:
            continue
        by_group = {}
        for gval, sub in df.loc[idx].groupby(gcol, dropna=True):
            sub_s = valid_series(sub[col])
            if len(sub_s) < MIN_CELL_N:
                continue
            by_group[str(gval)] = {
                str(k): round(float(v), 4)
                for k, v in sub_s.value_counts(normalize=True).items()
            }
        if by_group:
            out[f"by_{gcol}"] = by_group
    return out


def distribution_block(df: pd.DataFrame, col: str, group_cols: list[str]) -> dict:
    s = pd.to_numeric(valid_series(df[col]), errors="coerce").dropna()
    out: dict = {"n_valid": int(len(s))}
    if len(s) == 0:
        return out
    out["mean"] = round(float(s.mean()), 2)
    out["median"] = round(float(s.median()), 2)
    out["p25"] = round(float(s.quantile(0.25)), 2)
    out["p75"] = round(float(s.quantile(0.75)), 2)
    counts, edges = np.histogram(s, bins=20)
    out["histogram"] = {
        "counts": counts.tolist(),
        "bin_edges": [round(float(x), 2) for x in edges.tolist()],
    }
    for gcol in group_cols:
        if gcol not in df.columns or gcol == col:
            continue
        by_group = {}
        for gval, sub in df.groupby(gcol, dropna=True):
            sub_s = pd.to_numeric(valid_series(sub[col]), errors="coerce").dropna()
            if len(sub_s) < MIN_CELL_N:
                continue
            by_group[str(gval)] = {
                "mean": round(float(sub_s.mean()), 2),
                "median": round(float(sub_s.median()), 2),
                "n": int(len(sub_s)),
            }
        if by_group:
            out[f"by_{gcol}"] = by_group
    return out


def build_summary(df: pd.DataFrame, meta: dict, group_cols: list[str]) -> dict:
    summary = {
        "generated_at": date.today().isoformat(),
        "n_rows": int(len(df)),
        "prevalence": {},
        "distribution": {},
    }
    for col, info in meta["columns"].items():
        if col not in df.columns:
            continue
        if info["type"] == "categorical":
            summary["prevalence"][col] = prevalence_block(df, col, group_cols)
        elif info["type"] == "continuous":
            summary["distribution"][col] = distribution_block(df, col, group_cols)
    return summary


def build_manifest(catalog: dict) -> dict:
    modules = {}
    for mid, cfg in catalog["modules"].items():
        years = {}
        for year in cfg["years"]:
            d = OUT / mid / str(year)
            if (d / "meta.json").exists():
                years[str(year)] = {
                    "meta": f"data/{mid}/{year}/meta.json",
                    "summary": f"data/{mid}/{year}/summary.json",
                    "texto": f"data/{mid}/{year}/texto.txt",
                    "data": f"data/{mid}/{year}/data.csv",
                }
        if years:
            modules[mid] = {
                "title": cfg["title"],
                "status": cfg["status"],
                "years": years,
            }
    return {
        "version": catalog["version"],
        "title": catalog["title"],
        "modules": modules,
    }


def process_module_year(module_id: str, year: int, copy_csv: bool = True) -> None:
    catalog = load_catalog()
    cfg = catalog["modules"][module_id]
    src_dir = ZENODO / cfg["source_dir"] / str(year)
    csv_src = src_dir / cfg["data_file"]
    if not csv_src.exists():
        raise FileNotFoundError(f"No existe: {csv_src}")

    dest = OUT / module_id / str(year)
    dest.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_src, encoding="utf-8", low_memory=False)
    desc_meta = parse_description_csv(src_dir / "description.csv")
    meta = build_meta(df, cfg, year, desc_meta)
    group_cols = [c for c in catalog["demographic_columns"] if c in df.columns]

    with open(dest / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    summary = build_summary(df, meta, group_cols)
    with open(dest / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    texto_src = src_dir / "texto.txt"
    if texto_src.exists():
        shutil.copy2(texto_src, dest / "texto.txt")

    if copy_csv:
        shutil.copy2(csv_src, dest / "data.csv")

    print(f"OK  {module_id}/{year}  rows={len(df)}  -> {dest}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", help="id del módulo (ej. salud)")
    parser.add_argument("--year", type=int, help="año ENSANUT")
    parser.add_argument("--mvp", action="store_true", help="procesar módulos MVP")
    parser.add_argument("--no-csv", action="store_true", help="no copiar CSV (solo meta+summary)")
    args = parser.parse_args()

    catalog = load_catalog()

    if args.mvp:
        for mid in catalog["mvp_modules"]:
            for year in catalog["modules"][mid]["years"]:
                process_module_year(mid, year, copy_csv=not args.no_csv)
    elif args.module and args.year:
        process_module_year(args.module, args.year, copy_csv=not args.no_csv)
    else:
        parser.error("Usa --mvp o --module X --year Y")

    manifest = build_manifest(catalog)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    # Copiar catálogo al folder servido por GitHub Pages
    shutil.copy2(CATALOG_PATH, SITE / "docs" / "catalog.json")
    print(f"Manifest -> {OUT / 'manifest.json'}")


if __name__ == "__main__":
    main()
