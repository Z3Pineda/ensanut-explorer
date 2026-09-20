import { resolveFromSite } from "./site-base.js";

const DEFAULT_LINKS = {
  salud: "explore.html?module=salud&year=2018&var=DM_Diabetes",
  antropometria: "explore.html?module=antropometria&year=2018&var=Peso",
  bio: "explore.html?module=bio&year=2018&var=Glucosa",
  lactancia: "explore.html?module=lactancia&year=2018&var=amamantar",
};

function showError(grid, message) {
  grid.innerHTML = `<p class="load-error">${message}</p>`;
}

async function init() {
  const grid = document.getElementById("module-grid");
  if (!grid) return;

  if (window.location.protocol === "file:") {
    showError(
      grid,
      "Abre el sitio con un servidor local (<code>python -m http.server 8765</code> en la carpeta <code>docs</code>), no como archivo en disco."
    );
    return;
  }

  try {
    const res = await fetch(resolveFromSite("catalog.json"));
    if (!res.ok) throw new Error(`catalog.json respondió ${res.status}`);
    const catalog = await res.json();

    Object.values(catalog.modules).forEach((m) => {
      const available = m.status === "mvp";
      const card = document.createElement("article");
      card.className = `module-card${available ? "" : " disabled"}`;
      card.style.borderTop = `4px solid ${m.color}`;

      const badge = available ? "badge-mvp" : "badge-planned";
      const badgeText = available ? "Disponible" : "Próximamente";
      const href = DEFAULT_LINKS[m.id];

      card.innerHTML = `
        <span class="badge ${badge}">${badgeText}</span>
        <h3>${m.title}</h3>
        <p>${m.subtitle}</p>
        ${
          href
            ? `<a class="btn btn-primary" href="${href}">Explorar</a>`
            : `<span class="btn btn-secondary">En desarrollo</span>`
        }
      `;
      grid.appendChild(card);
    });
  } catch (err) {
    console.error(err);
    showError(
      grid,
      `No se pudieron cargar los módulos. ${err.message}. Si estás en GitHub Pages, prueba recargar o revisa la consola del navegador (F12).`
    );
  }
}

init();
