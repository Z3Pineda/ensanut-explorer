"""Unit tests for parsing, typing and aggregation helpers."""

from __future__ import annotations

import pandas as pd
import pytest

import prepare_data


def test_valid_series_excludes_missing_codes():
    s = pd.Series([1, 2, 888, 999, 222.2, None, 3])
    out = prepare_data.valid_series(s)
    assert set(out.tolist()) == {1.0, 2.0, 3.0}


def test_parse_value_map_extracts_codes():
    desc = "1.0: Norte, 2.0: Centro, 3.0: Ciudad de México, 4.0: Sur"
    assert prepare_data.parse_value_map(desc) == {
        "1": "Norte",
        "2": "Centro",
        "3": "Ciudad de México",
        "4": "Sur",
    }


def test_normalize_code_strips_float_suffix():
    assert prepare_data.normalize_code("1.0") == "1"
    assert prepare_data.normalize_code("12") == "12"


def test_prevalence_block_respects_min_cell_n():
    df = pd.DataFrame(
        {
            "Sexo": [1, 1, 1, 2, 2] * 10,
            "Region": [1] * 25 + [2] * 25,
            "flag": [1, 2] * 25,
        }
    )
    block = prepare_data.prevalence_block(df, "flag", ["Region"])
    assert block["n_valid"] == 50
    assert abs(sum(block["overall"].values()) - 1.0) < 1e-6
    assert "by_Region" not in block


def test_prevalence_block_includes_large_groups():
    df = pd.DataFrame(
        {
            "Sexo": [1] * 35 + [2] * 35,
            "flag": [1] * 70,
        }
    )
    block = prepare_data.prevalence_block(df, "flag", ["Sexo"])
    assert "by_Sexo" in block
    assert block["by_Sexo"]["1"]["1"] == 1.0


def test_distribution_block_histogram_has_twenty_bins():
    df = pd.DataFrame({"Edad": list(range(100)) * 2, "Sexo": [1, 2] * 100})
    block = prepare_data.distribution_block(df, "Edad", ["Sexo"])
    assert len(block["histogram"]["counts"]) == 20
    assert len(block["histogram"]["bin_edges"]) == 21


def test_merge_desc_meta_prefers_json_for_tr_medicamento():
    csv_meta = {"TR_medicamento": {"label": "csv label", "ensanut_param": "P7_1"}}
    json_param = {
        "p6_7_1": {
            "label": "Medicamento para triglicéridos",
            "ensanut_param": "P6_7_1",
            "values": {"1": "Sí", "2": "No"},
        }
    }
    merged = prepare_data.merge_desc_meta(csv_meta, {}, json_param, ["TR_medicamento"])
    entry = merged["TR_medicamento"]
    assert entry["ensanut_param"] == "P6_7_1"
    assert entry["values"]["1"] == "Sí"


def test_build_meta_skips_nota_columns():
    df = pd.DataFrame({"Sexo": [1, 2], "nota1": ["a", "b"], "ID": [1, 2]})
    cfg = {
        "id": "salud",
        "data_file": "CS_ADULTOS.csv",
        "population": "Adultos",
        "variables": {"categorical": ["Sexo"], "continuous": []},
    }
    meta = prepare_data.build_meta(df, cfg, 2018, {"Sexo": {"label": "Sexo", "values": {"1": "Hombre", "2": "Mujer"}}})
    assert "nota1" not in meta["columns"]
    assert "ID" not in meta["columns"]
    assert meta["columns"]["Sexo"]["type"] == "categorical"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("", "col name"),
        ("<ninguno>", "col name"),
        ("Etiqueta real", "Etiqueta real"),
    ],
)
def test_clean_label(raw, expected):
    assert prepare_data.clean_label(raw, "col_name") == expected
