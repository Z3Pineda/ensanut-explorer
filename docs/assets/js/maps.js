import { labelForValue, sortCodes } from "./utils.js";
import { resolveFromSite } from "./site-base.js";

let geoCache = null;

export async function loadMexicoGeoJSON() {
  if (geoCache) return geoCache;
  const res = await fetch(resolveFromSite("assets/data/mexico-entidades.geojson"));
  if (!res.ok) throw new Error("No se pudo cargar el mapa de México");
  geoCache = await res.json();
  return geoCache;
}

/** Elige código "1" si existe; si no, el primer código con etiqueta. */
export function defaultMapCode(metaCol) {
  const values = metaCol?.values ?? {};
  const codes = sortCodes(Object.keys(values));
  if (codes.includes("1")) return "1";
  return codes[0] ?? "1";
}

export function mapValueOptions(metaCol) {
  const values = metaCol?.values ?? {};
  return sortCodes(Object.keys(values)).map((code) => ({
    code,
    label: labelForValue(metaCol, code),
  }));
}

export function extractByEntidad(block, metaCol, mapCode, isContinuous) {
  const byEnt = block.by_Entidad ?? {};
  const out = {};
  for (const [ent, data] of Object.entries(byEnt)) {
    if (isContinuous) {
      out[ent] = data.mean ?? null;
    } else {
      out[ent] = (data[mapCode] ?? 0) * 100;
    }
  }
  return out;
}

export async function renderEntidadMap(containerId, metaCol, block, mapCode, isContinuous) {
  const el = document.getElementById(containerId);
  if (!el || !window.Plotly) return;

  const geojson = await loadMexicoGeoJSON();
  const byEnt = extractByEntidad(block, metaCol, mapCode, isContinuous);

  const locations = [];
  const z = [];
  const text = [];

  for (const feat of geojson.features) {
    const code = feat.properties.ensanut;
    if (!code || byEnt[code] == null) continue;
    locations.push(code);
    const val = byEnt[code];
    z.push(val);
    const name = feat.properties.name;
    if (isContinuous) {
      text.push(`${name}<br>${val?.toFixed?.(1) ?? val}`);
    } else {
      const catLabel = labelForValue(metaCol, mapCode);
      text.push(`${name}<br>${catLabel}: ${val.toFixed(1)}%`);
    }
  }

  const zTitle = isContinuous
    ? metaCol?.label || "Media"
    : `% ${labelForValue(metaCol, mapCode)}`;

  Plotly.newPlot(
    el,
    [{
      type: "choropleth",
      geojson,
      locations,
      z,
      text,
      hoverinfo: "text",
      featureidkey: "properties.ensanut",
      colorscale: [
        [0, "#f7fbff"],
        [0.2, "#deebf7"],
        [0.4, "#c6dbef"],
        [0.6, "#6baed6"],
        [0.8, "#2171b5"],
        [1, "#08306b"],
      ],
      colorbar: { title: zTitle, ticksuffix: isContinuous ? "" : "%" },
      marker: { line: { color: "#ffffff", width: 0.5 } },
      zmin: isContinuous ? undefined : 0,
      zmax: isContinuous ? undefined : 100,
    }],
    {
      margin: { t: 8, r: 8, b: 8, l: 8 },
      geo: {
        fitbounds: "locations",
        visible: false,
      },
    },
    { responsive: true, displayModeBar: false }
  );
}
