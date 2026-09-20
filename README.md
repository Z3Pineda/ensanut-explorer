# ENSANUT Explorer

Sitio estático ([GitHub Pages](https://z3pineda.github.io/ensanut-explorer/)) para explorar subconjuntos procesados de ENSANUT (2018–2023).

**Datos (Zenodo):** [doi.org/10.5281/zenodo.14460946](https://doi.org/10.5281/zenodo.14460946) (CC BY 4.0)  
**Código:** MIT License — ver [`LICENSE`](LICENSE)  
**Datos en repo:** CC BY 4.0 — ver [`LICENSE-DATA.md`](LICENSE-DATA.md)

## Módulos

Salud · Antropometría · Biomarcadores · Actividad física · Lactancia materna · Nutrición

## Inicio rápido

```bash
pip install -r scripts/requirements.txt
python scripts/prepare_data.py --mvp
cd docs && python -m http.server 8765
# http://localhost:8765
```

## Regenerar datos

Lee CSV desde `../ZENODO/` y metadatos desde `../ZENODO_JSON/` o `../ZENODO_RELEASE/`:

```bash
python scripts/prepare_data.py --module salud --year 2018
python scripts/prepare_data.py --mvp
```

## Publicar cambios

```powershell
git add -A
git commit -m "Describe tu cambio"
git push
```

GitHub Actions despliega automáticamente desde `/docs`.

## Paquete Zenodo v1

Generar en el proyecto padre:

```powershell
cd D:\DOCUMENTOS\ML_WORKS\PROY_ENSANUT
python scripts/build_zenodo_release.py
```

Ver [`../ZENODO_RELEASE/ZENODO_UPLOAD.md`](../ZENODO_RELEASE/ZENODO_UPLOAD.md) para instrucciones de subida.

## Documentación

- [ARCHITECTURE.md](./ARCHITECTURE.md) — diseño técnico
- [docs/about.html](./docs/about.html) — metodología, licencias, citación
