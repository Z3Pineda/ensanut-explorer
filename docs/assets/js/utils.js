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
  if (code == null || code === "") return "Sin dato";
  if (!metaCol?.values) return String(code);
  const raw = String(code);
  const candidates = [
    raw,
    raw.replace(/\.0+$/, ""),
    Number.isFinite(Number(raw)) ? String(parseInt(raw, 10)) : null,
  ].filter(Boolean);
  for (const key of candidates) {
    if (metaCol.values[key] != null) return metaCol.values[key];
  }
  return raw;
}

export function sortCodes(codes) {
  return [...codes].sort((a, b) => {
    const na = Number(a);
    const nb = Number(b);
    if (Number.isFinite(na) && Number.isFinite(nb)) return na - nb;
    return String(a).localeCompare(String(b), "es");
  });
}

export function pct(n) {
  return `${(n * 100).toFixed(1)}%`;
}
