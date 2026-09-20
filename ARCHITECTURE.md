# Arquitectura ENSANUT Explorer (GitHub Pages)

Sitio estático tipo **Our World in Data** para explorar los datos procesados de ENSANUT.
Sin backend en producción: HTML + JavaScript en GitHub Pages, datos en el mismo repo.

---

## 1. Objetivo del MVP

| Fase | Alcance | Entregable |
|------|---------|------------|
| **MVP** | Salud + Antropometría, años 2018–2023 | Explorador con filtros, 3 tipos de gráfica, ficha de variable |
| **v1.1** | Bio + Actividad física | Mismos componentes, nuevo catálogo |
| **v1.2** | Lactancia + Alimentos | Variables específicas (porciones, grupos alimenticios) |
| **v2** | Asistente FAQ (opcional) | Búsqueda sobre metadatos, sin LLM |

---

## 2. Principios de diseño

1. **Estático primero** — GitHub Pages no ejecuta Python; todo análisis pesado se precomputa.
2. **Metadatos delgados** — No servir el JSON crudo del INSP (~10k líneas); generar `meta.json` por dataset (~50–200 variables).
3. **CSV en repo, agregados para gráficas** — Descarga completa disponible; visualización usa `summary.json` precomputado.
4. **Un solo manifiesto** — `catalog.json` describe módulos, años, rutas y columnas analizables.
5. **Reutilizar fuentes existentes** — Datos de `ZENODO/`, metadatos de `ZENODO_JSON/` o `description.csv`.

---

## 3. Estructura del repositorio

```
ensanut-site/
├── ARCHITECTURE.md          ← este documento
├── README.md
├── catalog.json             ← registro central de datasets (fuente de verdad)
├── scripts/
│   ├── prepare_data.py      ← copia CSV + genera meta.json + summary.json
│   └── requirements.txt
├── docs/                    ← raíz de GitHub Pages (/docs en Settings)
│   ├── index.html           ← landing + tarjetas por módulo
│   ├── explore.html         ← explorador principal (SPA ligera)
│   ├── about.html           ← metodología, fuente INSP, licencia
│   ├── assets/
│   │   ├── css/
│   │   │   └── main.css
│   │   └── js/
│   │       ├── app.js           ← orquestador
│   │       ├── catalog.js       ← carga catalog.json
│   │       ├── data-loader.js   ← fetch meta + summary + csv bajo demanda
│   │       ├── metadata-panel.js← ficha lateral de variable
│   │       ├── filters.js       ← año, sexo, región, entidad
│   │       ├── charts.js        ← Plotly: barras, líneas, histograma
│   │       └── utils.js         ← mapas de códigos, formateo
│   └── data/                ← generado por prepare_data.py (no editar a mano)
│       ├── manifest.json        ← índice liviano para el frontend
│       └── {modulo}/{año}/
│           ├── meta.json        ← definición de columnas + etiquetas de valores
│           ├── summary.json     ← agregados precomputados
│           ├── texto.txt
│           └── data.csv         ← opcional en MVP; link de descarga siempre
└── .github/
    └── workflows/
        └── deploy.yml       ← opcional: validar + publicar Pages
```

### Fuentes upstream (fuera del repo del sitio)

```
PROY_ENSANUT/
├── ZENODO/                  → CSV procesados (columnas renombradas)
├── ZENODO_JSON/             → description.json (catálogo completo INSP)
└── ensanut-site/            → este proyecto
```

---

## 4. Flujo de datos

```
┌─────────────────┐     prepare_data.py      ┌──────────────────────┐
│ ZENODO/*.csv    │ ────────────────────────►│ docs/data/.../       │
│ description.csv │                            │   data.csv           │
│ description.json│ ──► meta.json (slim) ────►│   meta.json          │
│ texto.txt       │                            │   texto.txt          │
└─────────────────┘     agregaciones pandas  │   summary.json       │
                                             └──────────┬───────────┘
                                                        │
                                                        ▼
                                             ┌──────────────────────┐
                                             │  GitHub Pages (CDN)  │
                                             │  explore.html + JS   │
                                             └──────────────────────┘
```

### Contenido de cada artefacto

**`catalog.json`** (raíz, versionado)
- Lista de módulos con id, título, descripción, icono, color
- Por módulo: años disponibles, archivo CSV, columnas demográficas fijas
- Columnas “analizables” agrupadas: `continuous`, `categorical`, `binary`

**`meta.json`** (por módulo/año, ~5–50 KB)
```json
{
  "module": "salud",
  "year": 2018,
  "source": "ENSANUT 2018 - CS_ADULTOS",
  "rows": 43070,
  "columns": {
    "Sexo": {
      "label": "Sexo",
      "type": "categorical",
      "values": {"1": "Hombre", "2": "Mujer"}
    },
    "DM_Diabetes": {
      "label": "Diabetes diagnosticada",
      "type": "categorical",
      "values": {"1": "Sí", "2": "No", "3": "No sabe"}
    },
    "Peso": {
      "label": "Peso habitual (kg)",
      "type": "continuous",
      "unit": "kg"
    }
  }
}
```

**`summary.json`** (por módulo/año, precomputado)
```json
{
  "generated_at": "2026-09-20",
  "by_year": { "2018": { "n": 43070 } },
  "prevalence": {
    "DM_Diabetes": {
      "overall": {"1": 0.12, "2": 0.85, "3": 0.03},
      "by_Sexo": {"1": {"1": 0.13}, "2": {"1": 0.11}},
      "by_Region": { ... }
    }
  },
  "distribution": {
    "Peso": {"mean": 72.4, "median": 71.0, "p25": 62, "p75": 82, "bins": [...]}
  }
}
```

**`manifest.json`** (en `docs/data/`, generado)
- Copia reducida de `catalog.json` + checksums + tamaños de archivo para el loader.

---

## 5. Pantallas (UX)

### 5.1 Landing (`index.html`)

```
┌────────────────────────────────────────────────────────────┐
│  ENSANUT Explorer                    [Acerca de] [GitHub]  │
├────────────────────────────────────────────────────────────┤
│  Subconjuntos procesados de la Encuesta Nacional de        │
│  Salud y Nutrición (México), 2018–2023                     │
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Salud   │ │ Antropo- │ │   Bio    │ │  Act.Fís │      │
│  │  ● MVP   │ │  metría  │ │  v1.1    │ │  v1.1    │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐                                 │
│  │Lactancia │ │ Alimentos│                                 │
│  │  v1.2    │ │  v1.2    │                                 │
│  └──────────┘ └──────────┘                                 │
└────────────────────────────────────────────────────────────┘
```

### 5.2 Explorador (`explore.html?module=salud&year=2018&var=DM_Diabetes`)

```
┌──────────────┬─────────────────────────────────────────────┐
│ FILTROS      │  Diabetes diagnosticada · ENSANUT 2018      │
│              │  ─────────────────────────────────────────  │
│ Módulo       │  [Gráfica principal: barras por región]     │
│ Año          │                                             │
│ Variable ▼   │  Desagregar por: [Sexo ▼] [Región ▼]       │
│              │                                             │
│ Sexo         │  ┌─────────────────────────────────────┐   │
│ Región       │  │  Serie temporal 2018–2023 (si aplica)│   │
│ Entidad      │  └─────────────────────────────────────┘   │
├──────────────┤                                             │
│ FICHA VAR    │  [Descargar CSV] [Ver metadatos INSP]     │
│ Pregunta     │                                             │
│ Valores      │                                             │
│ Fuente       │                                             │
└──────────────┴─────────────────────────────────────────────┘
```

### Tipos de gráfica (por tipo de variable)

| Tipo columna | Gráfica default | Desagregación |
|--------------|-----------------|---------------|
| `binary` / `categorical` | Barras (% prevalencia) | Sexo, Región, Entidad |
| `continuous` | Histograma + media | Por grupo categórico |
| Serie multi-año | Línea temporal | Nacional / por región |

---

## 6. Stack técnico

| Capa | Tecnología | Motivo |
|------|------------|--------|
| Hosting | GitHub Pages (`/docs`) | Gratis, HTTPS, CDN |
| UI | HTML semántico + CSS custom | Sin build obligatorio en MVP |
| Gráficas | [Plotly.js](https://plotly.com/javascript/) CDN | Interactivo, mapas, barras, líneas |
| CSV parse (descarga) | [PapaParse](https://www.papaparse.com/) CDN | Solo si el usuario descarga/analiza local |
| Preproceso | Python 3 + pandas | Script local / CI, no en producción |
| CI (opcional) | GitHub Actions | Regenerar `data/` al cambiar fuentes |

**No usar en MVP:** React build, FastAPI, LLM, base de datos.

---

## 7. Mapeo módulos → archivos fuente

| module id | Carpeta ZENODO | CSV | Años | description |
|-----------|----------------|-----|------|-------------|
| `salud` | `ENSANUT_SALUD` | `CS_ADULTOS.csv` | 2018,2021,2022,2023 | csv + json |
| `antropometria` | `ENSANUT_ANTROPOMETRIA` | `CN_ANTROPOMETRIA.csv` | 2018–2023 | csv + json |
| `bio` | `ENSANUT_BIO` | `CS_ADULTOS.csv` | 2018,2020,2023 | csv + json |
| `actfis` | `ENSANUT_ACTFIS` | `CS_ADULTOS.csv` (+ otros) | 2018,2022,2023 | csv parcial |
| `lactancia` | `ENSANUT_LACTANCIA` | `Lactancia.csv` | 2018–2023 | csv |
| `alimentos` | `ENSANUT_ALIMENTOS` | `Nutricion.csv` | 2018–2023 | csv ("No aplica") |

Columnas demográficas comunes (filtros globales):
`Sexo`, `Edad`, `Entidad`, `Region`, `Estrato` (cuando existan).

---

## 8. Reglas de agregación (prepare_data.py)

Para variables categóricas/binarias:
- Excluir missing, `888`, `999`, `222.2` según meta
- Prevalencia = count / total válido
- Mínimo celda: n ≥ 30 para mostrar (ocultar o agrupar si no)

Para continuas:
- Percentiles, media, mediana, n
- Histograma con 20 bins robustos

Para series temporales:
- Misma variable across años → un bloque en `summary.json` multi-año

---

## 9. GitHub Pages — configuración

1. Repo: `github.com/{usuario}/ensanut-explorer`
2. Settings → Pages → Source: **Deploy from branch `main`, folder `/docs`**
3. URL: `https://{usuario}.github.io/ensanut-explorer/`
4. Rutas relativas en JS: `const BASE = import.meta.url` o `const DATA_BASE = './data/'`

### Límite de tamaño repo

- GitHub recomienda < 1 GB; archivos > 100 MB bloquean push
- CSV más grande ~43k filas × ~30 cols ≈ 5–15 MB → OK
- Total estimado data/: ~150–300 MB (7 módulos × 6 años) → considerar **Git LFS** o publicar solo agregados + enlace a Zenodo para CSV completos

**Estrategia recomendada:**
- En GitHub: `meta.json` + `summary.json` + `texto.txt` (liviano)
- CSV completos: release de GitHub o enlace a Zenodo
- MVP: incluir CSV solo de Salud + Antropometría

---

## 10. Roadmap de implementación

### Semana 1 — Fundamentos
- [x] Arquitectura + `catalog.json`
- [ ] `prepare_data.py` para salud 2018
- [ ] `explore.html` con una gráfica de prevalencia
- [ ] Publicar en GitHub Pages

### Semana 2 — MVP Salud + Antropometría
- [ ] Todos los años 2018–2023 de ambos módulos
- [ ] Filtros Sexo / Región
- [ ] Panel de metadatos
- [ ] Descarga CSV

### Semana 3 — Pulido
- [ ] Serie temporal multi-año
- [ ] `about.html` con citación INSP
- [ ] GitHub Action que corre `prepare_data.py`

### v1.1+
- [ ] Bio, Actividad física
- [ ] Mapa coroplético por entidad (Plotly geoJSON México)
- [ ] Buscador de variables (FAQ estático, sin LLM)

---

## 11. Fase 2 opcional — “Asistente” sin LLM

No ChatGPT; un **buscador de variables** indexado en build time:

```
scripts/build_search_index.py → docs/data/search-index.json
```

Frontend: input que filtra `{ module, column, label, question }`.
Respuestas template: definición + años disponibles + link al explorador.

Costo: cero. Riesgo de alucinación: cero.

---

## 12. Citación y licencia (about.html)

- Fuente primaria: [ensanut.insp.mx](https://ensanut.insp.mx/)
- Este sitio: subconjunto procesado con columnas renombradas
- Incluir DOI de Zenodo cuando publiques el dataset
- Aviso: no reemplaza microdatos oficiales del INSP

---

## 13. Decisiones cerradas

| Decisión | Elección |
|----------|----------|
| Hosting | GitHub Pages `/docs` |
| Backend prod | Ninguno |
| Formato metadatos runtime | `meta.json` delgado |
| Gráficas runtime | `summary.json` precomputado |
| Catálogo completo INSP | Solo en descarga / referencia, no en browser |
| MVP módulos | Salud + Antropometría |
