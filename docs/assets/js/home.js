const DEFAULT_LINKS = {
  salud: "explore.html?module=salud&year=2018&var=DM_Diabetes",
  antropometria: "explore.html?module=antropometria&year=2018&var=Peso",
  bio: "explore.html?module=bio&year=2018&var=Glucosa",
  lactancia: "explore.html?module=lactancia&year=2018&var=amamantar",
};

const SITE_ROOT = new URL("../../", import.meta.url);

async function init() {
  const res = await fetch(new URL("catalog.json", SITE_ROOT));
  const catalog = await res.json();
  const grid = document.getElementById("module-grid");

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
      ${href
        ? `<a class="btn btn-primary" href="${href}">Explorar</a>`
        : `<span class="btn btn-secondary">En desarrollo</span>`}
    `;
    grid.appendChild(card);
  });
}

init();
