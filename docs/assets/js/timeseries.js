import { labelForValue, sortCodes } from "./utils.js";

const summaryCache = new Map();

export async function loadSummary(module, year) {
  const key = `${module}/${year}`;
  if (summaryCache.has(key)) return summaryCache.get(key);
  const base = new URL(`../../data/${module}/${year}/`, import.meta.url);
  const res = await fetch(new URL("summary.json", base));
  if (!res.ok) throw new Error(`Sin datos para ${module}/${year}`);
  const data = await res.json();
  summaryCache.set(key, data);
  return data;
}

function getBlock(summary, variable) {
  return summary.prevalence?.[variable] ?? summary.distribution?.[variable] ?? null;
}

function metricFromBlock(block, metaCol, mapCode, groupKey, groupCode) {
  if (!block) return null;
  const isContinuous = metaCol?.type === "continuous";

  if (groupKey && groupCode != null) {
    const grp = block[`by_${groupKey}`]?.[String(groupCode)];
    if (!grp) return null;
    if (isContinuous) return grp.mean ?? null;
    return (grp[mapCode] ?? null) != null ? grp[mapCode] * 100 : null;
  }

  if (isContinuous) return block.mean ?? null;
  const v = block.overall?.[mapCode];
  return v != null ? v * 100 : null;
}

export async function buildTimeSeries(module, years, variable, metaCol, mapCode, groupBy, meta) {
  const sortedYears = [...years].map(Number).sort((a, b) => a - b);
  const isContinuous = metaCol?.type === "continuous";

  if (!groupBy) {
    const yVals = [];
    const xYears = [];
    const nVals = [];
    for (const year of sortedYears) {
      const summary = await loadSummary(module, year);
      const block = getBlock(summary, variable);
      const val = metricFromBlock(block, metaCol, mapCode, null, null);
      if (val == null) continue;
      xYears.push(year);
      yVals.push(isContinuous ? val : val);
      nVals.push(block?.n_valid ?? summary.n_rows);
    }
    return {
      traces: [{
        name: isContinuous ? "Media nacional" : labelForValue(metaCol, mapCode),
        x: xYears,
        y: yVals,
        customdata: nVals,
      }],
      isContinuous,
    };
  }

  const groupMeta = meta?.columns?.[groupBy];
  const groupCodes = sortCodes(
    Object.keys(groupMeta?.values ?? {}).filter((c) => c !== "")
  );

  const traces = [];
  for (const gCode of groupCodes) {
    const xYears = [];
    const yVals = [];
    const nVals = [];
    for (const year of sortedYears) {
      const summary = await loadSummary(module, year);
      const block = getBlock(summary, variable);
      const val = metricFromBlock(block, metaCol, mapCode, groupBy, gCode);
      if (val == null) continue;
      xYears.push(year);
      yVals.push(val);
      const grp = block?.[`by_${groupBy}`]?.[String(gCode)];
      nVals.push(grp ? block.n_valid : null);
    }
    if (xYears.length === 0) continue;
    traces.push({
      name: labelForValue(groupMeta, gCode),
      x: xYears,
      y: yVals,
      customdata: nVals,
    });
  }
  return { traces, isContinuous };
}

export function renderTimeSeriesChart(containerId, seriesData, metaCol, mapCode) {
  const el = document.getElementById(containerId);
  if (!el || !window.Plotly) return;

  const { traces, isContinuous } = seriesData;
  if (!traces.length) {
    el.innerHTML = "<p style='padding:1rem'>No hay datos temporales para esta variable.</p>";
    return;
  }

  const yTitle = isContinuous
    ? metaCol?.label || "Media"
    : `% ${labelForValue(metaCol, mapCode)}`;

  Plotly.newPlot(
    el,
    traces.map((t) => ({
      type: "scatter",
      mode: "lines+markers",
      name: t.name,
      x: t.x,
      y: t.y,
      customdata: t.customdata,
      hovertemplate: isContinuous
        ? "Año %{x}<br>%{y:.1f}<extra>%{fullData.name}</extra>"
        : "Año %{x}<br>%{y:.1f}%<extra>%{fullData.name}</extra>",
      marker: { size: 8 },
      line: { width: 2 },
    })),
    {
      margin: { t: 24, r: 16, b: 48, l: 56 },
      xaxis: {
        title: "Año ENSANUT",
        dtick: 1,
        tickmode: "linear",
      },
      yaxis: {
        title: yTitle,
        rangemode: isContinuous ? "tozero" : "tozero",
      },
      legend: { orientation: "h", y: -0.15 },
    },
    { responsive: true, displayModeBar: false }
  );
}
