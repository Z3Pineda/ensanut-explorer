export function qs(name) {
  return new URLSearchParams(window.location.search).get(name);
}

export function setQuery(params) {
  const url = new URL(window.location.href);
  Object.entries(params).forEach(([k, v]) => {
    if (v == null || v === "") url.searchParams.delete(k);
    else url.searchParams.set(k, v);
  });
  window.history.replaceState({}, "", url);
}

export function labelForValue(metaCol, code) {
  if (!metaCol?.values) return String(code);
  const key = String(code).replace(/\.0$/, "");
  return metaCol.values[key] ?? metaCol.values[String(code)] ?? String(code);
}

export function pct(n) {
  return `${(n * 100).toFixed(1)}%`;
}
