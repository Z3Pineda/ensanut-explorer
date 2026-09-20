import { loadCatalog, loadDataset } from "./data-loader.js";
import { renderChart, updateMetaPanel } from "./charts.js";
import { qs, setQuery } from "./utils.js";

const state = {
  catalog: null,
  dataset: null,
  module: qs("module") || "salud",
  year: qs("year") || "2018",
  variable: qs("var") || "DM_Diabetes",
  split: qs("split") || "",
};

async function init() {
  state.catalog = await loadCatalog();
  populateModuleSelect();
  bindEvents();
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

function bindEvents() {
  document.getElementById("sel-module").addEventListener("change", async (e) => {
    state.module = e.target.value;
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
    await render();
  });
  document.getElementById("sel-split").addEventListener("change", async (e) => {
    state.split = e.target.value;
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
  await render();
}

async function render() {
  setQuery({
    module: state.module,
    year: state.year,
    var: state.variable,
    split: state.split || undefined,
  });

  const { meta, summary } = state.dataset;
  const metaCol = meta.columns[state.variable];
  const prev = summary.prevalence?.[state.variable];
  const dist = summary.distribution?.[state.variable];
  const block = prev ?? dist ?? {};

  const shortName = state.variable.replace(/_/g, " ");
  document.getElementById("chart-title").textContent =
    metaCol?.label && metaCol.label !== shortName ? metaCol.label : shortName;
  document.getElementById("chart-subtitle").textContent =
    `${state.catalog.modules[state.module].title} · ENSANUT ${state.year} · n=${meta.rows.toLocaleString("es-MX")}`;

  renderChart("chart-main", state.variable, metaCol, block, state.split, meta);
  updateMetaPanel(metaCol, block);
}

init().catch((err) => {
  console.error(err);
  document.getElementById("chart-main").innerHTML =
    `<p style="padding:1rem">Error al iniciar: ${err.message}</p>`;
});
