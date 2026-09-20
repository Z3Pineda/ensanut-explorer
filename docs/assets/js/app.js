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
  seriesGroup: qs("seriesGroup") || "",
};

function syncControlsFromState() {
  document.getElementById("sel-split").value = state.split;
  document.getElementById("sel-series-group").value = state.seriesGroup;
}

async function init() {
  state.catalog = await loadCatalog();
  populateModuleSelect();
  syncControlsFromState();
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

function moduleYears() {
  return state.catalog.modules[state.module].years;
}

function updateViewFields() {
  const isTimeseries = state.split === "timeseries";
  const isMap = state.split === "Entidad";
  const metaCol = state.dataset?.meta?.columns?.[state.variable];
  const isCategorical = metaCol?.type === "categorical";

  document.getElementById("field-year").hidden = isTimeseries;
  document.getElementById("field-series-group").hidden = !isTimeseries;
  document.getElementById("field-map-code").hidden = !(isMap || isTimeseries) || !isCategorical;
}

function refreshMapCodeSelect() {
  const sel = document.getElementById("sel-map-code");
  const metaCol = state.dataset?.meta?.columns?.[state.variable];
  const show =
    (state.split === "Entidad" || state.split === "timeseries") &&
    metaCol?.type === "categorical";

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
    if (state.split === "timeseries" && !state.mapCode) {
      const metaCol = state.dataset?.meta?.columns?.[state.variable];
      if (metaCol?.type === "categorical") {
        state.mapCode = defaultMapCode(metaCol);
      }
    }
    updateViewFields();
    refreshMapCodeSelect();
    await render();
  });
  document.getElementById("sel-map-code").addEventListener("change", async (e) => {
    state.mapCode = e.target.value;
    await render();
  });
  document.getElementById("sel-series-group").addEventListener("change", async (e) => {
    state.seriesGroup = e.target.value;
    await render();
  });
  document.getElementById("sel-series-group").value = state.seriesGroup;
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
    mapCode:
      state.split === "Entidad" || state.split === "timeseries"
        ? state.mapCode || undefined
        : undefined,
    seriesGroup: state.split === "timeseries" ? state.seriesGroup || undefined : undefined,
  });

  const { meta, summary } = state.dataset;
  const metaCol = meta.columns[state.variable];
  const prev = summary.prevalence?.[state.variable];
  const dist = summary.distribution?.[state.variable];
  const block = prev ?? dist ?? {};

  const shortName = state.variable.replace(/_/g, " ");
  document.getElementById("chart-title").textContent =
    metaCol?.label && metaCol.label !== shortName ? metaCol.label : shortName;

  const years = moduleYears();
  const yearLabel = state.split === "timeseries"
    ? `${Math.min(...years)}–${Math.max(...years)}`
    : state.year;

  let hint = "";
  if (state.split === "Entidad" && metaCol?.type === "categorical") {
    hint = ` · Mapa: categoría ${state.mapCode}`;
  } else if (state.split === "Entidad" && metaCol?.type === "continuous") {
    hint = " · Mapa: media por entidad";
  } else if (state.split === "timeseries") {
    hint = metaCol?.type === "continuous"
      ? " · Evolución de la media nacional"
      : ` · Evolución % categoría ${state.mapCode}`;
    if (state.seriesGroup) hint += ` · por ${state.seriesGroup}`;
  }

  const nLabel =
    state.split === "timeseries"
      ? "oleadas comparables"
      : `n=${meta.rows.toLocaleString("es-MX")}`;
  document.getElementById("chart-subtitle").textContent =
    `${state.catalog.modules[state.module].title} · ENSANUT ${yearLabel} · ${nLabel}${hint}`;

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
      state.mapCode,
      {
        module: state.module,
        years,
        seriesGroup: state.seriesGroup,
      }
    );
  } catch (err) {
    document.getElementById("chart-main").innerHTML =
      `<p style="padding:1rem;color:#b91c1c">${err.message}</p>`;
  }
  updateMetaPanel(metaCol, block);
}

init().catch((err) => {
  console.error(err);
  document.getElementById("chart-main").innerHTML =
    `<p style="padding:1rem">Error al iniciar: ${err.message}</p>`;
});
