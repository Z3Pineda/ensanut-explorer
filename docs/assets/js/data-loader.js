import { resolveFromSite } from "./site-base.js";

const DATA_ROOT = resolveFromSite("data/");

export async function loadCatalog() {
  const res = await fetch(resolveFromSite("catalog.json"));
  if (!res.ok) throw new Error("No se pudo cargar catalog.json");
  return res.json();
}

export async function loadManifest() {
  const res = await fetch(new URL("manifest.json", DATA_ROOT));
  if (!res.ok) throw new Error("Ejecuta scripts/prepare_data.py para generar docs/data/");
  return res.json();
}

export async function loadDataset(module, year) {
  const base = new URL(`${module}/${year}/`, DATA_ROOT);
  const [metaRes, summaryRes, textoRes] = await Promise.all([
    fetch(new URL("meta.json", base)),
    fetch(new URL("summary.json", base)),
    fetch(new URL("texto.txt", base)),
  ]);
  if (!metaRes.ok) throw new Error(`No se encontró meta.json (${module}/${year})`);
  if (!summaryRes.ok) throw new Error(`No se encontró summary.json (${module}/${year})`);
  const [meta, summary] = await Promise.all([metaRes.json(), summaryRes.json()]);
  return {
    meta,
    summary,
    texto: textoRes.ok ? await textoRes.text() : "",
    csvUrl: new URL("data.csv", base).href,
  };
}
