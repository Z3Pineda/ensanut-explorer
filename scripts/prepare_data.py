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

# Etiquetas estándar ENSANUT (respaldo si el JSON no las trae)
STANDARD_VALUES: dict[str, dict[str, str]] = {
    "Sexo": {"1": "Hombre", "2": "Mujer"},
    "Region": {
        "1": "Norte",
        "2": "Centro",
        "3": "Ciudad de México",
        "4": "Sur",
    },
}

# Clave ENT — 32 entidades federativas (código ENSANUT → nombre)
ENTIDAD_VALUES: dict[str, str] = {
    "1": "Aguascalientes",
    "2": "Baja California",
    "3": "Baja California Sur",
    "4": "Campeche",
    "5": "Chiapas",
    "6": "Chihuahua",
    "7": "Ciudad de México",
    "8": "Coahuila",
    "9": "Colima",
    "10": "Durango",
    "11": "Guanajuato",
    "12": "Guerrero",
    "13": "Hidalgo",
    "14": "Jalisco",
    "15": "Estado de México",
    "16": "Michoacán",
    "17": "Morelos",
    "18": "Nayarit",
    "19": "Nuevo León",
    "20": "Oaxaca",
    "21": "Puebla",
    "22": "Querétaro",
    "23": "Quintana Roo",
    "24": "San Luis Potosí",
    "25": "Sinaloa",
    "26": "Sonora",
    "27": "Tabasco",
    "28": "Tamaulipas",
    "29": "Tlaxcala",
    "30": "Veracruz",
    "31": "Yucatán",
    "32": "Zacatecas",
}

# Etiquetas biomarcadores (description.csv sin texto descriptivo)
BIO_LABELS: dict[str, str] = {
    "Glucosa": "Glucosa en suero",
    "HB1AC": "Hemoglobina glucosilada (HbA1c)",
    "Albumina": "Albumina sérica",
    "C_HDL": "Colesterol HDL",
    "C_LDL": "Colesterol LDL",
    "Colesterol": "Colesterol total",
    "Creatinina": "Creatinina sérica",
    "Insulina": "Insulina",
    "Trigliceridos": "Triglicéridos",
}

# Nutrición — sin catálogo JSON oficial del INSP en ZENODO_JSON
ALIMENTOS_LABELS: dict[str, str] = {
    "bebidas": "Porciones semanales de bebidas",
    "carnes": "Porciones semanales de carnes",
    "cereales": "Porciones semanales de cereales",
    "com_rapida": "Porciones semanales de comida rápida",
    "dulces": "Porciones semanales de dulces y postres",
    "frutas": "Porciones semanales de frutas",
    "lacteos": "Porciones semanales de lácteos",
    "leguminosas": "Porciones semanales de leguminosas",
    "miscelaneos": "Porciones semanales de alimentos misceláneos",
    "pescado": "Porciones semanales de pescado y mariscos",
    "prod_maiz": "Porciones semanales de productos de maíz",
    "sopas": "Porciones semanales de sopas",
    "verduras": "Porciones semanales de verduras",
    "Edad": "Edad en años cumplidos",
}

# Parámetro JSON correcto cuando description.csv / Nombre_corto INSP asigna mal
COLUMN_JSON_PARAM: dict[str, str] = {
    "TR_medicamento": "p6_7_1",
}

# Columnas internas del cuestionario (notas de flujo); no analizar en el sitio
SKIP_COLUMNS = re.compile(r"^nota\d+$", re.I)


def clean_label(raw: str | None, fallback: str) -> str:
    label = str(raw or "").strip()
    if label.lower() in ("", "nan", "<ninguno>", "ninguno", "none"):
        return fallback.replace("_", " ")
    if label in ('"', " ", "''"):
        return fallback.replace("_", " ")
    return label


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    drop = [c for c in df.columns if str(c).startswith("Unnamed")]
    if drop:
        df = df.drop(columns=drop)
    rename: dict[str, str] = {}
    if "estrato" in df.columns and "Estrato" not in df.columns:
        rename["estrato"] = "Estrato"
    if rename:
        df = df.rename(columns=rename)
    return df


def load_catalog() -> dict:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _pick_csv_column(columns: list[str], *needles: str) -> str | None:
    for needle in needles:
        for col in columns:
            if needle.lower() in col.lower():
                return col
    return None


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
    if df.empty:
        return {}

    cols = list(df.columns)
    name_col = _pick_csv_column(cols, "nombre corto   (adulto)", "nombre corto  (adulto)", "nombre corto")
    desc_col = _pick_csv_column(cols, "descripción   (adulto)", "descripción  (adulto)", "descripción")
    param_col = _pick_csv_column(cols, "parámetro ensanut (adulto)", "parámetro ensanut")
    if not name_col:
        return {}

    meta: dict[str, dict] = {}
    for _, row in df.iterrows():
        col = str(row.get(name_col, "")).strip()
        if not col or col == "nan":
            continue
        desc = str(row.get(desc_col, "")).strip() if desc_col else ""
        param = str(row.get(param_col, "")).strip() if param_col else ""
        values = parse_value_map(desc)
        if col == "Entidad" and values:
            values = dict(ENTIDAD_VALUES)
        label = BIO_LABELS.get(col, col.replace("_", " "))
        meta[col] = {
            "label": label,
            "ensanut_param": param if param != "nan" else None,
            "type": "categorical" if values else "unknown",
            "values": values,
        }
    return meta


def normalize_code(val) -> str:
    s = str(val).strip()
    if not s:
        return s
    if re.fullmatch(r"\d+\.0+", s):
        return str(int(float(s)))
    if re.fullmatch(r"\d+", s):
        return str(int(s))
    return s


def parse_value_map(desc: str) -> dict[str, str]:
    """Extrae mapa código→etiqueta de cadenas tipo '1.0: Norte, 2.0: Centro'."""
    values: dict[str, str] = {}
    if not desc or desc in ("", "nan"):
        return values
    for m in re.finditer(r"([\d.]+)\s*:\s*([^,]+?)(?=,\s*[\d.]+\s*:|$)", desc):
        code = normalize_code(m.group(1))
        label = m.group(2).strip()
        if code and label:
            values[code] = label
    return values


def _entry_from_json(param: str, info: dict) -> dict:
    values: dict[str, str] = {}
    for v in info.get("Valores") or []:
        code = normalize_code(v.get("Valor_numerico", ""))
        label = str(v.get("Etiqueta", "")).strip()
        if code and label:
            values[code] = label
    short = info.get("Nombre_corto") or info.get("nombre_corto") or param
    return {
        "label": clean_label(info.get("Etiqueta"), str(short)),
        "ensanut_param": param,
        "values": values,
    }


def parse_description_json(path: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    """Catálogo INSP: por Nombre corto y por parámetro ENSANUT."""
    if not path.exists():
        return {}, {}
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    by_short: dict[str, dict] = {}
    by_param: dict[str, dict] = {}
    for param, info in raw.items():
        if not isinstance(info, dict):
            continue
        entry = _entry_from_json(param, info)
        by_param[str(param).lower()] = entry
        short = info.get("Nombre_corto") or info.get("nombre_corto")
        if short:
            by_short[str(short)] = entry
    return by_short, by_param


def build_column_rename_map(
    desc_csv_path: Path,
    json_path: Path | None,
    columns: list[str],
) -> dict[str, str]:
    """Map raw ENSANUT parameter names to Nombre corto (case-insensitive keys)."""
    mapping: dict[str, str] = {}

    if desc_csv_path.exists():
        for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                df = pd.read_csv(desc_csv_path, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            df = None
        if df is not None and not df.empty:
            cols = list(df.columns)
            name_col = _pick_csv_column(
                cols, "nombre corto   (adulto)", "nombre corto  (adulto)", "nombre corto"
            )
            param_col = _pick_csv_column(
                cols, "parámetro ensanut (adulto)", "parámetro ensanut"
            )
            if name_col and param_col:
                for _, row in df.iterrows():
                    param = str(row.get(param_col, "")).strip()
                    short = str(row.get(name_col, "")).strip()
                    if param and short and param != "nan" and short != "nan":
                        mapping[param.lower()] = short

    if json_path and json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            raw = json.load(f)
        col_lower = {c.lower(): c for c in columns}
        for param, info in raw.items():
            if not isinstance(info, dict):
                continue
            short = info.get("Nombre_corto") or info.get("nombre_corto")
            if not short:
                continue
            key = str(param).lower()
            if key in mapping:
                continue
            if key in col_lower:
                mapping[key] = str(short)

    return mapping


def apply_column_renames(
    df: pd.DataFrame,
    rename_map: dict[str, str],
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Rename columns using official short names; return provenance {new: original}."""
    if not rename_map:
        return df, {}

    used_targets: set[str] = set()
    rename: dict[str, str] = {}
    provenance: dict[str, str] = {}

    for col in df.columns:
        target = rename_map.get(str(col).lower())
        if not target or target == col:
            continue
        if target in used_targets:
            continue
        rename[col] = target
        provenance[target] = col
        used_targets.add(target)

    if rename:
        df = df.rename(columns=rename)
    return df, provenance


def find_description_json(source_dir: str, year: int) -> Path | None:
    bases = (
        ZENODO / source_dir,
        ROOT / source_dir,
        ZENODO_JSON / source_dir,
        ROOT / "ZENODO_RELEASE" / source_dir,
    )
    for base in bases:
        path = base / str(year) / "description.json"
        if path.exists():
            return path
    release = ROOT / "ZENODO_RELEASE" / source_dir
    if release.is_dir():
        for path in sorted(release.glob("*/description.json")):
            return path
    return None


def merge_desc_meta(
    csv_meta: dict[str, dict],
    json_short: dict[str, dict],
    json_param: dict[str, dict],
    df_columns: list[str],
    provenance: dict[str, str] | None = None,
) -> dict[str, dict]:
    """JSON (catálogo INSP) tiene prioridad sobre description.csv."""
    merged: dict[str, dict] = {}
    provenance = provenance or {}
    for col in df_columns:
        entry: dict = dict(csv_meta.get(col, {}))
        js = None
        if col in COLUMN_JSON_PARAM:
            js = json_param.get(COLUMN_JSON_PARAM[col])
        if not js:
            js = json_short.get(col)
        param = entry.get("ensanut_param")
        source_col = provenance.get(col)
        if not js and source_col:
            js = json_param.get(str(source_col).lower())
        if not js and param:
            js = json_param.get(str(param).lower())
        if js:
            entry["label"] = clean_label(
                js.get("label") or entry.get("label"),
                col,
            )
            entry["ensanut_param"] = js.get("ensanut_param") or param
            if js.get("values"):
                entry["values"] = dict(js["values"])

        if col in BIO_LABELS:
            entry["label"] = BIO_LABELS[col]
        elif col in ALIMENTOS_LABELS:
            entry["label"] = ALIMENTOS_LABELS[col]

        if col == "Entidad":
            entry["values"] = dict(ENTIDAD_VALUES)
            entry["label"] = "Entidad federativa"
        elif col == "Region":
            entry["values"] = dict(STANDARD_VALUES["Region"])
            entry["label"] = "Región ENSANUT"
        elif col in STANDARD_VALUES:
            entry["values"] = dict(STANDARD_VALUES[col])
            entry["label"] = "Sexo" if col == "Sexo" else col

        if entry.get("values"):
            entry["type"] = "categorical"
        merged[col] = entry
    return merged


def get_year_variables(module_cfg: dict, year: int) -> tuple[list[str], list[str]]:
    """Variables declared for a module/year (falls back to module union)."""
    by_year = module_cfg.get("variables_by_year", {}).get(str(year))
    if by_year:
        return (
            list(by_year.get("categorical") or []),
            list(by_year.get("continuous") or []),
        )
    variables = module_cfg.get("variables", {})
    return (
        list(variables.get("categorical") or []),
        list(variables.get("continuous") or []),
    )


def infer_column_types(df: pd.DataFrame, module_cfg: dict, year: int | None = None) -> dict[str, str]:
    declared = {}
    categorical, continuous = get_year_variables(module_cfg, year) if year else ([], [])
    if not categorical and not continuous:
        for t in ("continuous", "categorical"):
            for c in module_cfg.get("variables", {}).get(t, []):
                declared[c] = t
    else:
        for c in categorical:
            declared[c] = "categorical"
        for c in continuous:
            declared[c] = "continuous"
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
    provenance: dict[str, str] | None = None,
) -> dict:
    provenance = provenance or {}
    types = infer_column_types(df, module_cfg, year)
    columns: dict[str, dict] = {}
    for col in df.columns:
        if col == "ID" or SKIP_COLUMNS.match(col):
            continue
        info = desc_meta.get(col, {})
        ensanut_param = info.get("ensanut_param") or provenance.get(col)
        entry = {
            "label": clean_label(info.get("label"), col),
            "type": types.get(col, "unknown"),
            "ensanut_param": ensanut_param,
        }
        if col in provenance:
            entry["source_column"] = provenance[col]
        if info.get("values"):
            entry["values"] = info["values"]
        if entry["type"] == "categorical" and "values" not in entry and col in STANDARD_VALUES:
            entry["values"] = STANDARD_VALUES[col]
        if module_cfg["id"] == "alimentos" and col in ALIMENTOS_LABELS and col != "Edad":
            entry["unit"] = "porciones/semana"
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


def build_variables_by_year(catalog: dict) -> dict:
    """Scan generated meta.json files and attach per-year variable lists to catalog."""
    updated = json.loads(json.dumps(catalog))
    for mid in updated.get("mvp_modules", []):
        cfg = updated["modules"][mid]
        by_year: dict[str, dict[str, list[str]]] = {}
        for year in cfg["years"]:
            meta_path = OUT / mid / str(year) / "meta.json"
            if not meta_path.exists():
                continue
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            categorical: list[str] = []
            continuous: list[str] = []
            for col, info in meta.get("columns", {}).items():
                if info.get("type") == "categorical":
                    categorical.append(col)
                elif info.get("type") == "continuous":
                    continuous.append(col)
            by_year[str(year)] = {
                "categorical": sorted(categorical),
                "continuous": sorted(continuous),
            }
        if by_year:
            cfg["variables_by_year"] = by_year
    return updated


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

    df = normalize_dataframe(pd.read_csv(csv_src, encoding="utf-8", low_memory=False))
    json_path = find_description_json(cfg["source_dir"], year)
    rename_map = build_column_rename_map(src_dir / "description.csv", json_path, list(df.columns))
    df, provenance = apply_column_renames(df, rename_map)
    csv_meta = parse_description_csv(src_dir / "description.csv")
    json_short, json_param = parse_description_json(json_path) if json_path else ({}, {})
    desc_meta = merge_desc_meta(
        csv_meta, json_short, json_param, list(df.columns), provenance
    )
    meta = build_meta(df, cfg, year, desc_meta, provenance)
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
        df.to_csv(dest / "data.csv", index=False, encoding="utf-8")

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

    catalog = build_variables_by_year(catalog)
    catalog["version"] = "1.0.1"
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    manifest = build_manifest(catalog)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    shutil.copy2(CATALOG_PATH, SITE / "docs" / "catalog.json")
    print(f"Manifest -> {OUT / 'manifest.json'}")
    print(f"Catalog  -> {CATALOG_PATH} (variables_by_year updated)")


if __name__ == "__main__":
    main()
