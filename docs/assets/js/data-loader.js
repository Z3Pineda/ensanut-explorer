// Rutas relativas al módulo JS → siempre apuntan a docs/ sin depender de la página HTML
const SITE_ROOT = new URL("../../", import.meta.url);
const DATA_ROOT = new URL("../../data/", import.meta.url);

export async function loadCatalog() {
  const res = await fetch(new URL("catalog.json", SITE_ROOT));
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
  const [meta, summary, textoRes] = await Promise.all([
    fetch(new URL("meta.json", base)).then((r) => r.json()),
    fetch(new URL("summary.json", base)).then((r) => r.json()),
    fetch(new URL("texto.txt", base)).then((r) => (r.ok ? r.text() : "")),
  ]);
  return {
    meta,
    summary,
    texto: textoRes,
    csvUrl: new URL("data.csv", base).href,
  };
}
