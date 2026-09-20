# ENSANUT Explorer v1.0.1

Research software release focused on **reproducibility**, **automated testing**, and **lactancia data normalization**.

## Highlights

- **Lactancia 2021–2023:** column renaming from official INSP `description.csv` / `description.json` with `source_column` traceability in `meta.json`
- **`variables_by_year`** in `catalog.json` — UI only offers variables available for the selected year
- **GitHub Actions:** pytest workflow on push/PR (`121` CI tests; `24` reproduction tests run locally with `ZENODO/`)
- **`ARCHITECTURE.md`** updated for static-first v1.0.1 design
- **Downloadable CSVs** in `docs/data/` aligned with processed column names

## Validation

| Check | Result |
|-------|--------|
| Local pytest (full) | 145 passed, 0 skipped |
| CI pytest | 121 passed (reproduction excluded) |
| Benchmark | pipeline ~46.9 s · integrity ~0.7 s |
| Datasets | 24 module×year |

## Software citation

Pineda Rico, Z. (2026). ENSANUT Explorer (v1.0.1) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.14460946

## Data citation

```
Pineda Rico, Z. (2026). Processed health, anthropometry, biomarkers, physical activity,
breastfeeding and nutrition datasets from ENSANUT (Mexico, 2018–2023) (Version 1) [Data set].
Zenodo. https://doi.org/10.5281/zenodo.14460946
```

## Links

- Explorer: https://z3pineda.github.io/ensanut-explorer/
- Repository: https://github.com/Z3Pineda/ensanut-explorer
- INSP source: https://ensanut.insp.mx/

## Known limitations

- Variable schemas differ by year (notably actividad física 2018 vs 2022–2023)
- Lactancia 2018 includes many variables absent in 2021–2023 waves
- Processed subsets; not a substitute for official INSP microdata
