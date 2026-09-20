/** Base URL del sitio (GitHub Pages /ensanut-explorer/ o servidor local). */
export function siteBaseUrl() {
  const { origin, pathname } = window.location;
  const marker = "/ensanut-explorer/";
  const idx = pathname.indexOf(marker);
  if (idx !== -1) {
    return origin + pathname.slice(0, idx + marker.length);
  }
  const basePath = pathname.replace(/[^/]*$/, "") || "/";
  return origin + basePath;
}

export function resolveFromSite(relativePath) {
  return new URL(relativePath.replace(/^\//, ""), siteBaseUrl());
}
