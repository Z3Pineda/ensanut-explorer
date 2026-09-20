# ENSANUT Explorer

Sitio estático (GitHub Pages) para explorar subconjuntos procesados de ENSANUT.

## Inicio rápido

```bash
# 1. Instalar dependencias del preprocesador
pip install -r scripts/requirements.txt

# 2. Generar datos del MVP (Salud + Antropometría, todos los años)
python scripts/prepare_data.py --mvp

# 3. Servir localmente
cd docs && python -m http.server 8080
# Abrir http://localhost:8080
```

## Publicar en GitHub Pages

1. Crear repo `ensanut-explorer` y subir esta carpeta
2. Settings → Pages → **Deploy from branch `main`, folder `/docs`**
3. URL: `https://{usuario}.github.io/ensanut-explorer/`

## Documentación

Ver [ARCHITECTURE.md](./ARCHITECTURE.md) para diseño completo, flujo de datos y roadmap.

## Fuentes de datos

El script `prepare_data.py` lee desde el proyecto padre:

- `../ZENODO/` — CSV procesados
- `../ZENODO_JSON/` — metadatos JSON (futuro enriquecimiento)
