const MODULES = {
  salud: { status: "mvp", href: "explore.html?module=salud&year=2018&var=DM_Diabetes" },
  antropometria: { status: "mvp", href: "explore.html?module=antropometria&year=2018&var=Peso" },
  bio: { status: "planned", href: null },
  actfis: { status: "planned", href: null },
  lactancia: { status: "planned", href: null },
  alimentos: { status: "planned", href: null },
};

const SITE_ROOT = new URL("../../", import.meta.url);

async function init() {
  const res = await fetch(new URL("catalog.json", SITE_ROOT));
  const catalog = await res.json();
  const grid = document.getElementById("module-grid");

  Object.values(catalog.modules).forEach((m) => {
    const info = MODULES[m.id] ?? { status: "planned", href: null };
    const card = document.createElement("article");
    card.className = `module-card${info.status === "planned" ? " disabled" : ""}`;
    card.style.borderTop = `4px solid ${m.color}`;

    const badge = info.status === "mvp" ? "badge-mvp" : "badge-planned";
    const badgeText = info.status === "mvp" ? "Disponible" : "Próximamente";

    card.innerHTML = `
      <span class="badge ${badge}">${badgeText}</span>
      <h3>${m.title}</h3>
      <p>${m.subtitle}</p>
      ${info.href
        ? `<a class="btn btn-primary" href="${info.href}">Explorar</a>`
        : `<span class="btn btn-secondary">En desarrollo</span>`}
    `;
    grid.appendChild(card);
  });
}

init();
