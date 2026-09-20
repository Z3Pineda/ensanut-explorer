import { labelForValue, pct } from "./utils.js";

export function renderChart(containerId, variable, metaCol, summaryBlock, splitBy, meta) {
  const el = document.getElementById(containerId);
  if (!el || !window.Plotly) return;

  if (metaCol.type === "continuous") {
    renderHistogram(el, variable, metaCol, summaryBlock);
    return;
  }

  const key = splitBy ? `by_${splitBy}` : null;
  if (key && summaryBlock[key]) {
    renderGroupedBars(el, variable, summaryBlock[key], splitBy, meta);
  } else {
    renderSimpleBars(el, variable, summaryBlock.overall, metaCol);
  }
}

function renderSimpleBars(el, variable, overall, metaCol) {
  const codes = Object.keys(overall);
  const labels = codes.map((c) => labelForValue(metaCol, c));
  const values = codes.map((c) => overall[c] * 100);

  Plotly.newPlot(
    el,
    [{
      type: "bar",
      x: labels,
      y: values,
      text: values.map((v) => `${v.toFixed(1)}%`),
      textposition: "auto",
      marker: { color: "#2563eb" },
    }],
    {
      margin: { t: 24, r: 16, b: 80, l: 48 },
      yaxis: { title: "Prevalencia (%)", rangemode: "tozero" },
      xaxis: { title: variable },
    },
    { responsive: true, displayModeBar: false }
  );
}

function renderGroupedBars(el, variable, byGroup, splitCol, meta) {
  const splitMeta = meta.columns[splitCol];
  const groups = Object.keys(byGroup);
  const allCodes = new Set();
  groups.forEach((g) => Object.keys(byGroup[g]).forEach((c) => allCodes.add(c)));
  const codes = [...allCodes];

  const traces = groups.map((g, i) => ({
    type: "bar",
    name: labelForValue(splitMeta, g),
    x: codes.map((c) => labelForValue(meta.columns[variable], c)),
    y: codes.map((c) => (byGroup[g][c] ?? 0) * 100),
  }));

  Plotly.newPlot(
    el,
    traces,
    {
      barmode: "group",
      margin: { t: 24, r: 16, b: 80, l: 48 },
      yaxis: { title: "Prevalencia (%)", rangemode: "tozero" },
      legend: { title: { text: splitCol } },
    },
    { responsive: true, displayModeBar: false }
  );
}

function renderHistogram(el, variable, metaCol, block) {
  const hist = block.histogram;
  if (!hist) {
    el.innerHTML = "<p>Sin datos de distribución.</p>";
    return;
  }
  const centers = hist.bin_edges.slice(0, -1).map((e, i) => (e + hist.bin_edges[i + 1]) / 2);

  Plotly.newPlot(
    el,
    [{
      type: "bar",
      x: centers,
      y: hist.counts,
      marker: { color: "#2980b9" },
    }],
    {
      margin: { t: 24, r: 16, b: 48, l: 48 },
      xaxis: { title: metaCol.label || variable },
      yaxis: { title: "Frecuencia" },
    },
    { responsive: true, displayModeBar: false }
  );
}

export function updateMetaPanel(metaCol, summaryBlock) {
  document.getElementById("meta-label").textContent = metaCol?.label ?? "—";
  document.getElementById("meta-type").textContent = metaCol?.type ?? "—";
  document.getElementById("meta-param").textContent = metaCol?.ensanut_param ?? "—";

  if (metaCol?.values) {
    const lines = Object.entries(metaCol.values).map(([k, v]) => `${k}: ${v}`);
    document.getElementById("meta-values").textContent = lines.join(" · ") || "—";
  } else {
    document.getElementById("meta-values").textContent = "—";
  }

  const n = summaryBlock?.n_valid ?? summaryBlock?.n ?? "—";
  document.getElementById("meta-n").textContent = n;
}
