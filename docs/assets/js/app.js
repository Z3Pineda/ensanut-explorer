import { loadCatalog, loadDataset } from "./data-loader.js";
import { renderChart, updateMetaPanel } from "./charts.js";
import { defaultMapCode, mapValueOptions } from "./maps.js";
import { qs, setQuery } from "./utils.js";

const state = {
  catalog: null,
  dataset: null,
  module: qs("module") || "salud",
  year: qs("year") || "2018",
  variable: qs("var") || "DM_Diabetes",
  split: qs("split") || "",
  mapCode: qs("mapCode") || "",
};

async function init() {
  if (window.location.protocol === "file:") {
    document.getElementById("chart-main").innerHTML =
      "<p style='padding:1rem;color:#b91c1c'>Abre el sitio con un servidor local (<code>python -m http.server 8765</code> en <code>docs</code>), no como archivo en disco.</p>";
    return;
  }
  state.catalog = await loadCatalog();
  populateModuleSelect();
  document.getElementById("sel-split").value = state.split;
  bindEvents();
  updateViewFields();
  await refresh();
}

function populateModuleSelect() {
  const sel = document.getElementById("sel-module");
  sel.innerHTML = "";
  Object.values(state.catalog.modules).forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m.id;
    opt.textContent = m.title;
    opt.disabled = m.status !== "mvp";
    sel.appendChild(opt);
  });
  sel.value = state.module;
  refreshYearSelect();
}

function refreshYearSelect() {
  const cfg = state.catalog.modules[state.module];
  const sel = document.getElementById("sel-year");
  sel.innerHTML = "";
  cfg.years.forEach((y) => {
    const opt = document.createElement("option");
    opt.value = String(y);
    opt.textContent = String(y);
    sel.appendChild(opt);
  });
  if (!cfg.years.map(String).includes(String(state.year))) {
    state.year = String(cfg.years[0]);
  }
  sel.value = String(state.year);
}

function refreshVariableSelect() {
  const cfg = state.catalog.modules[state.module];
  const sel = document.getElementById("sel-variable");
  sel.innerHTML = "";
  const vars = [
    ...(cfg.variables?.categorical ?? []),
    ...(cfg.variables?.continuous ?? []),
  ];
  vars.forEach((v) => {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    sel.appendChild(opt);
  });
  if (!vars.includes(state.variable)) state.variable = vars[0];
  sel.value = state.variable;
}

function updateViewFields() {
  const metaCol = state.dataset?.meta?.columns?.[state.variable];
  const showMapCode =
    state.split === "Entidad" && metaCol?.type === "categorical";
  document.getElementById("field-map-code").hidden = !showMapCode;
}

function refreshMapCodeSelect() {
  const sel = document.getElementById("sel-map-code");
  const metaCol = state.dataset?.meta?.columns?.[state.variable];
  const show = state.split === "Entidad" && metaCol?.type === "categorical";
  if (!show) return;

  const options = mapValueOptions(metaCol);
  sel.innerHTML = "";
  options.forEach(({ code, label }) => {
    const opt = document.createElement("option");
    opt.value = code;
    opt.textContent = `${code} — ${label}`;
    sel.appendChild(opt);
  });

  if (!state.mapCode || !options.some((o) => o.code === state.mapCode)) {
    state.mapCode = defaultMapCode(metaCol);
  }
  sel.value = state.mapCode;
}

function bindEvents() {
  document.getElementById("sel-module").addEventListener("change", async (e) => {
    state.module = e.target.value;
    state.mapCode = "";
    refreshYearSelect();
    refreshVariableSelect();
    await refresh();
  });
  document.getElementById("sel-year").addEventListener("change", async (e) => {
    state.year = e.target.value;
    await refresh();
  });
  document.getElementById("sel-variable").addEventListener("change", async (e) => {
    state.variable = e.target.value;
    state.mapCode = "";
    updateViewFields();
    refreshMapCodeSelect();
    await render();
  });
  document.getElementById("sel-split").addEventListener("change", async (e) => {
    state.split = e.target.value;
    updateViewFields();
    refreshMapCodeSelect();
    await render();
  });
  document.getElementById("sel-map-code").addEventListener("change", async (e) => {
    state.mapCode = e.target.value;
    await render();
  });
}

async function refresh() {
  refreshVariableSelect();
  try {
    state.dataset = await loadDataset(state.module, state.year);
  } catch (err) {
    document.getElementById("chart-main").innerHTML =
      `<p style="padding:1rem;color:#b91c1c">${err.message}</p>`;
    return;
  }
  document.getElementById("btn-download").href = state.dataset.csvUrl;
  updateViewFields();
  refreshMapCodeSelect();
  await render();
}

async function render() {
  setQuery({
    module: state.module,
    year: state.year,
    var: state.variable,
    split: state.split || undefined,
    mapCode: state.split === "Entidad" ? state.mapCode || undefined : undefined,
  });

  const { meta, summary } = state.dataset;
  const metaCol = meta.columns[state.variable] ?? { label: state.variable, type: "unknown" };
  const prev = summary.prevalence?.[state.variable];
  const dist = summary.distribution?.[state.variable];
  const block = prev ?? dist ?? {};

  const shortName = state.variable.replace(/_/g, " ");
  document.getElementById("chart-title").textContent =
    metaCol?.label && metaCol.label !== shortName ? metaCol.label : shortName;

  let hint = "";
  if (state.split === "Entidad" && metaCol?.type === "categorical") {
    hint = ` · Mapa: categoría ${state.mapCode}`;
  } else if (state.split === "Entidad" && metaCol?.type === "continuous") {
    hint = " · Mapa: media por entidad";
  }

  document.getElementById("chart-subtitle").textContent =
    `${state.catalog.modules[state.module].title} · ENSANUT ${state.year} · n=${meta.rows.toLocaleString("es-MX")}${hint}`;

  updateViewFields();
  refreshMapCodeSelect();
  try {
    await renderChart(
      "chart-main",
      state.variable,
      metaCol,
      block,
      state.split,
      meta,
      state.mapCode
    );
    updateMetaPanel(metaCol, block);
  } catch (err) {
    console.error(err);
    document.getElementById("chart-main").innerHTML =
      `<p style="padding:1rem;color:#b91c1c">Error al graficar: ${err.message}</p>`;
  }
}

init().catch((err) => {
  console.error(err);
  document.getElementById("chart-main").innerHTML =
    `<p style="padding:1rem">Error al iniciar: ${err.message}</p>`;
});
