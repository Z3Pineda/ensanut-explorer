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

El repo ya incluye los datos en `docs/data/` (~12 MB) y el workflow `.github/workflows/pages.yml`.

### Pasos (primera vez)

1. Crear repo vacío en GitHub: **https://github.com/new**
   - Nombre sugerido: `ensanut-explorer`
   - Público
   - **Sin** README ni .gitignore (ya existen aquí)

2. En PowerShell, desde esta carpeta:

```powershell
cd D:\DOCUMENTOS\ML_WORKS\PROY_ENSANUT\ensanut-site
git remote add origin https://github.com/TU_USUARIO/ensanut-explorer.git
git push -u origin main
```

3. En GitHub → **Settings → Pages**
   - Source: **GitHub Actions** (recomendado, usa el workflow incluido)
   - O alternativa: Deploy from branch **`main`**, folder **`/docs`**

4. Esperar 1–2 min. URL:

`https://TU_USUARIO.github.io/ensanut-explorer/`

### Actualizar después de cambios

```powershell
git add -A
git commit -m "Describe tu cambio"
git push
```

## Documentación

Ver [ARCHITECTURE.md](./ARCHITECTURE.md) para diseño completo, flujo de datos y roadmap.

## Fuentes de datos

El script `prepare_data.py` lee desde el proyecto padre:

- `../ZENODO/` — CSV procesados
- `../ZENODO_JSON/` — metadatos JSON (futuro enriquecimiento)
