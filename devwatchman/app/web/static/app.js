/* global Chart */

const state = {
  endpointOk: {
    summary: false,
    ports: false,
    network: false,
    alerts: false,
    history: false,
  },
  lastUpdatedIso: null,
  chart: null,
};

function $(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  const el = $(id);
  if (!el) return;
  el.textContent = value;
}

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

function formatBytes(bytes) {
  if (bytes === null || bytes === undefined || Number.isNaN(bytes)) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let val = Math.max(0, bytes);
  let i = 0;
  while (val >= 1024 && i < units.length - 1) {
    val /= 1024;
    i += 1;
  }
  const digits = i === 0 ? 0 : i === 1 ? 0 : 1;
  return `${formatNumber(val, digits)} ${units[i]}`;
}

function formatRate(bytesPerSec) {
  if (bytesPerSec === null || bytesPerSec === undefined || Number.isNaN(bytesPerSec)) return "—";
  return `${formatBytes(bytesPerSec)}/s`;
}

function badgeClass(severity) {
  switch (severity) {
    case "critical":
      return "bg-rose-500/15 border-rose-400/30 text-rose-200";
    case "warning":
      return "bg-amber-500/15 border-amber-400/30 text-amber-200";
    default:
      return "bg-sky-500/15 border-sky-400/30 text-sky-200";
  }
}

function updateGlobalStatus() {
  const ok = Object.values(state.endpointOk).every(Boolean);
  const dot = $("dot-status");
  const text = $("text-status");
  const backend = $("backend-status");

  if (dot) dot.className = `h-2 w-2 rounded-full ${ok ? "bg-emerald-400" : "bg-amber-400"}`;
  if (text) text.textContent = ok ? "ok" : "degraded";
  if (backend) backend.textContent = ok ? "ok" : "degraded";
}

async function fetchJson(url, controller) {
  const res = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    signal: controller.signal,
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

function poll(name, url, intervalMs, handler) {
  let controller = null;
  let requestSeq = 0;

  const tick = async () => {
    requestSeq += 1;
    const seq = requestSeq;
    if (controller) controller.abort();
    controller = new AbortController();

    try {
      const json = await fetchJson(url, controller);
      if (seq !== requestSeq) return;
      const ok = handler(json);
      state.endpointOk[name] = ok !== false;
    } catch (err) {
      if (seq !== requestSeq) return;
      state.endpointOk[name] = false;
      handler(null);
    } finally {
      if (seq !== requestSeq) return;
      updateGlobalStatus();
    }
  };

  tick();
  window.setInterval(tick, intervalMs);
}

function handleSummary(json) {
  if (!json || !json.ok || !json.data) {
    setText("kpi-cpu", "—");
    setText("kpi-ram", "—");
    setText("kpi-disk", "—");
    setText("kpi-net-up", "—");
    setText("kpi-net-down", "—");
    setText("kpi-ram-bytes", "—");
    setText("kpi-disk-bytes", "—");
    return false;
  }

  const d = json.data;
  setText("kpi-cpu", formatNumber(d.cpu_percent ?? null, 1));
  setText("kpi-ram", formatNumber(d.mem_percent ?? null, 1));
  setText("kpi-disk", formatNumber(d.disk_percent ?? null, 1));
  setText("kpi-net-up", formatRate(d.net_sent_bps ?? null));
  setText("kpi-net-down", formatRate(d.net_recv_bps ?? null));
  setText(
    "kpi-ram-bytes",
    d.mem_used_bytes != null && d.mem_total_bytes != null
      ? `${formatBytes(d.mem_used_bytes)} / ${formatBytes(d.mem_total_bytes)}`
      : "—",
  );
  setText(
    "kpi-disk-bytes",
    d.disk_used_bytes != null && d.disk_total_bytes != null
      ? `${formatBytes(d.disk_used_bytes)} / ${formatBytes(d.disk_total_bytes)}`
      : "—",
  );

  state.lastUpdatedIso = new Date().toISOString();
  setText("last-updated", new Date().toLocaleTimeString());
  return true;
}

function handlePorts(json) {
  const tbody = $("ports-body");
  if (!tbody) return;

  if (!json || !json.ok || !Array.isArray(json.data)) {
    tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-400">—</td></tr>`;
    return false;
  }

  const rows = json.data
    .slice()
    .sort((a, b) => a.port - b.port)
    .map((p) => {
      const status = p.listening ? "LISTEN" : "DOWN";
      const statusCls = p.listening
        ? "bg-emerald-500/15 border-emerald-400/30 text-emerald-200"
        : "bg-rose-500/15 border-rose-400/30 text-rose-200";

      return `
        <tr class="hover:bg-slate-900/20">
          <td class="py-3 pr-3 text-slate-100">${p.port}</td>
          <td class="py-3 pr-3">
            <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs border ${statusCls}">
              ${status}
            </span>
          </td>
          <td class="py-3 pr-3 text-slate-200">${p.pid ?? "—"}</td>
          <td class="py-3 text-slate-200">${p.process_name ?? "—"}</td>
        </tr>
      `;
    })
    .join("");

  tbody.innerHTML = rows || `<tr><td colspan="4" class="py-4 text-slate-400">—</td></tr>`;
  return true;
}

function handleNetwork(json) {
  if (!json || !json.ok || !json.data) {
    setText("kpi-net-quality", "—");
    setText("kpi-net-latency", "—");
    return false;
  }

  const d = json.data;
  setText("kpi-net-quality", d.status ?? "—");
  setText("kpi-net-latency", d.latency_ms == null ? "offline" : `${formatNumber(d.latency_ms, 0)} ms`);
  return true;
}

function handleAlerts(json) {
  const list = $("alerts-list");
  const count = $("alerts-count");
  if (!list) return;

  if (!json || !json.ok || !Array.isArray(json.data)) {
    if (count) count.textContent = "—";
    list.innerHTML = `<div class="text-sm text-slate-400">—</div>`;
    return false;
  }

  if (count) count.textContent = `${json.data.length}`;

  if (json.data.length === 0) {
    list.innerHTML = `<div class="text-sm text-slate-400">No alerts</div>`;
    return;
  }

  list.innerHTML = json.data
    .map((a) => {
      const sev = a.severity ?? "info";
      const ts = a.ts_utc ? new Date(a.ts_utc).toLocaleTimeString() : "—";
      return `
        <div class="rounded-2xl border border-slate-800/60 bg-slate-950/20 p-3">
          <div class="flex items-center justify-between gap-2">
            <div class="text-xs text-slate-400">${ts}</div>
            <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs border ${badgeClass(sev)}">
              ${sev}
            </span>
          </div>
          <div class="mt-2 text-sm text-slate-100">${a.message ?? "—"}</div>
          <div class="mt-1 text-xs text-slate-400">${a.type ?? ""}</div>
        </div>
      `;
    })
    .join("");
  return true;
}

function ensureChart() {
  if (state.chart) return state.chart;
  const el = $("chart-history");
  if (!el) return null;

  const ctx = el.getContext("2d");
  state.chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "CPU %",
          data: [],
          borderColor: "rgba(56, 189, 248, 0.95)",
          backgroundColor: "rgba(56, 189, 248, 0.15)",
          tension: 0.35,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: "RAM %",
          data: [],
          borderColor: "rgba(52, 211, 153, 0.95)",
          backgroundColor: "rgba(52, 211, 153, 0.12)",
          tension: 0.35,
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: { labels: { color: "rgba(226, 232, 240, 0.9)" } },
        tooltip: { enabled: true },
      },
      scales: {
        x: {
          ticks: { color: "rgba(148, 163, 184, 0.9)", maxTicksLimit: 10 },
          grid: { color: "rgba(51, 65, 85, 0.35)" },
        },
        y: {
          min: 0,
          max: 100,
          ticks: { color: "rgba(148, 163, 184, 0.9)" },
          grid: { color: "rgba(51, 65, 85, 0.35)" },
        },
      },
    },
  });

  return state.chart;
}

function handleHistory(json) {
  const chart = ensureChart();
  if (!chart) return;

  if (!json || !json.ok || !Array.isArray(json.data)) {
    chart.data.labels = [];
    chart.data.datasets[0].data = [];
    chart.data.datasets[1].data = [];
    chart.update();
    return false;
  }

  const rows = json.data;
  const labels = rows.map((r) => (r.ts_utc ? new Date(r.ts_utc).toLocaleTimeString() : "—"));
  const cpu = rows.map((r) => (typeof r.cpu_percent === "number" ? r.cpu_percent : null));
  const ram = rows.map((r) => (typeof r.mem_percent === "number" ? r.mem_percent : null));

  chart.data.labels = labels;
  chart.data.datasets[0].data = cpu;
  chart.data.datasets[1].data = ram;
  chart.update();
  return true;
}

document.addEventListener("DOMContentLoaded", () => {
  poll("summary", "/api/summary", 2000, handleSummary);
  poll("ports", "/api/ports", 3000, handlePorts);
  poll("network", "/api/network", 5000, handleNetwork);
  poll("alerts", "/api/alerts?limit=10", 5000, handleAlerts);
  poll("history", "/api/history?hours=1", 10000, handleHistory);

  updateGlobalStatus();
});
