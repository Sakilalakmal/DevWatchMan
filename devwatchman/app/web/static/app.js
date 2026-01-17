/* global Chart */

const NA = "\u2014";

const state = {
  chart: null,
  chartTsMs: [],
  alerts: [],
  timeline: [],
  processes: [],
  listeningPorts: {
    items: [],
    query: "",
    wsSeen: false,
    tsUtc: null,
  },
  ws: {
    connected: false,
    disconnectedSinceMs: null,
    reconnectDelayMs: 1000,
    socket: null,
  },
  fallback: {
    enabled: false,
  },
};

function $(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  const el = $(id);
  if (!el) return;
  el.textContent = value;
}

function escapeHtml(value) {
  const s = String(value ?? "");
  return s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return NA;
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

function formatBytes(bytes) {
  if (bytes === null || bytes === undefined || Number.isNaN(bytes)) return NA;
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
  if (bytesPerSec === null || bytesPerSec === undefined || Number.isNaN(bytesPerSec)) return NA;
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

function updateWsBadge() {
  const dot = $("dot-status");
  const text = $("text-status");
  const backend = $("backend-status");
  const procStatus = $("processes-status");

  if (state.ws.connected) {
    if (dot) dot.className = "h-2 w-2 rounded-full bg-emerald-400";
    if (text) text.textContent = "live";
    if (backend) backend.textContent = "live";
    if (procStatus && state.processes.length > 0) procStatus.textContent = "Live";
  } else {
    if (dot) dot.className = "h-2 w-2 rounded-full bg-amber-400";
    if (text) text.textContent = "degraded";
    if (backend) backend.textContent = "degraded";
    if (procStatus && state.processes.length > 0) procStatus.textContent = "Fallback";
  }
}

function updateLastUpdated() {
  setText("last-updated", new Date().toLocaleTimeString());
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

function makePoller(url, intervalMs, handler) {
  let controller = null;
  let requestSeq = 0;
  let intervalId = null;

  const tick = async () => {
    requestSeq += 1;
    const seq = requestSeq;
    if (controller) controller.abort();
    controller = new AbortController();

    try {
      const json = await fetchJson(url, controller);
      if (seq !== requestSeq) return;
      handler(json);
    } catch (_) {
      if (seq !== requestSeq) return;
      handler(null);
    }
  };

  return {
    start() {
      if (intervalId) return;
      tick();
      intervalId = window.setInterval(tick, intervalMs);
    },
    stop() {
      if (intervalId) {
        window.clearInterval(intervalId);
        intervalId = null;
      }
      if (controller) controller.abort();
      controller = null;
    },
  };
}

function renderKpis(kpi) {
  if (!kpi) {
    setText("kpi-cpu", NA);
    setText("kpi-ram", NA);
    setText("kpi-disk", NA);
    setText("kpi-net-up", NA);
    setText("kpi-net-down", NA);
    setText("kpi-ram-bytes", NA);
    setText("kpi-disk-bytes", NA);
    return;
  }

  setText("kpi-cpu", formatNumber(kpi.cpu_percent ?? null, 1));
  setText("kpi-ram", formatNumber(kpi.mem_percent ?? null, 1));
  setText("kpi-disk", formatNumber(kpi.disk_percent ?? null, 1));
  setText("kpi-net-up", formatRate(kpi.net_sent_bps ?? null));
  setText("kpi-net-down", formatRate(kpi.net_recv_bps ?? null));

  setText(
    "kpi-ram-bytes",
    kpi.mem_used_bytes != null && kpi.mem_total_bytes != null
      ? `${formatBytes(kpi.mem_used_bytes)} / ${formatBytes(kpi.mem_total_bytes)}`
      : NA,
  );
  setText(
    "kpi-disk-bytes",
    kpi.disk_used_bytes != null && kpi.disk_total_bytes != null
      ? `${formatBytes(kpi.disk_used_bytes)} / ${formatBytes(kpi.disk_total_bytes)}`
      : NA,
  );
}

function renderNetworkQuality({ status, latency_ms }) {
  setText("kpi-net-quality", status ?? NA);
  setText("kpi-net-latency", latency_ms == null ? "offline" : `${formatNumber(latency_ms, 0)} ms`);
}

function handlePorts(json) {
  const tbody = $("ports-body");
  if (!tbody) return;

  if (!json || !json.ok || !Array.isArray(json.data)) {
    tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-400">${NA}</td></tr>`;
    return;
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
          <td class="py-3 pr-3 text-slate-200">${p.pid ?? NA}</td>
          <td class="py-3 text-slate-200">${p.process_name ?? NA}</td>
        </tr>
      `;
    })
    .join("");

  tbody.innerHTML = rows || `<tr><td colspan="4" class="py-4 text-slate-400">${NA}</td></tr>`;
}

function filterListeningPorts(items, query) {
  if (!query) return items;
  const q = query.trim().toLowerCase();
  if (!q) return items;
  return items.filter((p) => {
    const port = p?.port != null ? String(p.port) : "";
    const pid = p?.pid != null ? String(p.pid) : "";
    const ip = (p?.local_ip ?? "").toLowerCase();
    const name = (p?.process_name ?? "").toLowerCase();
    return port.includes(q) || pid.includes(q) || ip.includes(q) || name.includes(q);
  });
}

function renderListeningPorts(items) {
  const tbody = $("listening-ports-body");
  const meta = $("listening-ports-meta");
  if (!tbody) return;

  if (!Array.isArray(items)) {
    if (meta) meta.textContent = NA;
    tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-400">Unable to load</td></tr>`;
    return;
  }

  const query = state.listeningPorts.query;
  const filtered = filterListeningPorts(items, query);
  const maxRows = 500;
  const show = filtered.slice(0, maxRows);
  const truncated = filtered.length > maxRows;
  const mode = state.ws.connected && state.listeningPorts.wsSeen ? "Live" : "Fallback";

  if (meta) {
    const bits = [`${mode} · ${filtered.length} shown`];
    if (query.trim()) bits.push(`filter: "${query.trim()}"`);
    if (truncated) bits.push("Showing first 500");
    meta.textContent = bits.join(" · ");
  }

  if (show.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-400">No matches</td></tr>`;
    return;
  }

  tbody.innerHTML = show
    .map((p) => {
      const port = p?.port ?? NA;
      const localIp = escapeHtml(p?.local_ip ?? NA);
      const pid = p?.pid ?? NA;
      const name = escapeHtml(p?.process_name ?? NA);
      return `
        <tr class="hover:bg-slate-900/20">
          <td class="py-3 pr-3 text-slate-100">${port}</td>
          <td class="py-3 pr-3 text-slate-200">${localIp}</td>
          <td class="py-3 pr-3 text-slate-200">${pid}</td>
          <td class="py-3 text-slate-200 truncate max-w-[18rem]" title="${name}">${name}</td>
        </tr>
      `;
    })
    .join("");
}

function handleListeningPorts(json) {
  const items = json?.ok ? json?.data?.items : null;
  if (!Array.isArray(items)) {
    renderListeningPorts(null);
    return;
  }
  state.listeningPorts.items = items;
  state.listeningPorts.tsUtc = json?.meta?.ts_utc ?? null;
  renderListeningPorts(state.listeningPorts.items);
}

function renderAlerts(alerts) {
  const list = $("alerts-list");
  const count = $("alerts-count");
  if (!list) return;

  if (!Array.isArray(alerts)) {
    if (count) count.textContent = NA;
    list.innerHTML = `<div class="text-sm text-slate-400">${NA}</div>`;
    return;
  }

  if (count) count.textContent = `${alerts.length}`;
  if (alerts.length === 0) {
    list.innerHTML = `<div class="text-sm text-slate-400">No alerts</div>`;
    return;
  }

  list.innerHTML = alerts
    .map((a) => {
      const sev = a.severity ?? "info";
      const ts = a.ts_utc ? new Date(a.ts_utc).toLocaleTimeString() : NA;
      return `
        <div class="rounded-2xl border border-slate-800/60 bg-slate-950/20 p-3">
          <div class="flex items-center justify-between gap-2">
            <div class="text-xs text-slate-400">${ts}</div>
            <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs border ${badgeClass(sev)}">
              ${sev}
            </span>
          </div>
          <div class="mt-2 text-sm text-slate-100">${a.message ?? NA}</div>
          <div class="mt-1 text-xs text-slate-400">${a.type ?? ""}</div>
        </div>
      `;
    })
    .join("");
}

function renderTimeline(items) {
  const list = $("timeline-list");
  const count = $("timeline-count");
  if (!list) return;

  if (!Array.isArray(items)) {
    if (count) count.textContent = NA;
    list.innerHTML = `<div class="text-sm text-slate-400">${NA}</div>`;
    return;
  }

  if (count) count.textContent = `${items.length}`;
  if (items.length === 0) {
    list.innerHTML = `<div class="text-sm text-slate-400">No events</div>`;
    return;
  }

  list.innerHTML = items
    .map((e) => {
      const sev = e.severity ?? "info";
      const ts = e.ts_utc ? new Date(e.ts_utc).toLocaleTimeString() : NA;
      return `
        <div class="rounded-2xl border border-slate-800/60 bg-slate-950/20 p-3">
          <div class="flex items-center justify-between gap-2">
            <div class="text-xs text-slate-400">${ts}</div>
            <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs border ${badgeClass(sev)}">
              ${sev}
            </span>
          </div>
          <div class="mt-2 text-sm text-slate-100">${e.message ?? NA}</div>
        </div>
      `;
    })
    .join("");
}

function renderProcesses(items) {
  const tbody = $("processes-body");
  const status = $("processes-status");
  if (!tbody) return;

  if (!Array.isArray(items)) {
    if (status) status.textContent = "Unable to load processes";
    if (state.processes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-400">Unable to load processes</td></tr>`;
    }
    return;
  }

  if (status) status.textContent = state.ws.connected ? "Live" : "Fallback";

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-400">No processes</td></tr>`;
    return;
  }

  tbody.innerHTML = items
    .slice()
    .map((p) => {
      const name = p.name ?? NA;
      const pid = p.pid ?? NA;
      const cpu = typeof p.cpu_percent === "number" ? formatNumber(p.cpu_percent, 1) : NA;
      const mem = typeof p.memory_bytes === "number" ? formatBytes(p.memory_bytes) : NA;
      return `
        <tr class="hover:bg-slate-900/20">
          <td class="py-3 pr-3 text-slate-100 truncate max-w-[12rem]" title="${name}">${name}</td>
          <td class="py-3 pr-3 text-slate-200">${pid}</td>
          <td class="py-3 pr-3 text-slate-200">${cpu}</td>
          <td class="py-3 text-slate-200">${mem}</td>
        </tr>
      `;
    })
    .join("");
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

function seedHistory(json) {
  const chart = ensureChart();
  if (!chart) return;

  if (!json || !json.ok || !Array.isArray(json.data)) {
    chart.data.labels = [];
    chart.data.datasets[0].data = [];
    chart.data.datasets[1].data = [];
    state.chartTsMs = [];
    chart.update("none");
    return;
  }

  const rows = json.data;
  const tsMs = rows.map((r) => (r.ts_utc ? Date.parse(r.ts_utc) : NaN));
  chart.data.labels = rows.map((r, i) =>
    Number.isFinite(tsMs[i]) ? new Date(tsMs[i]).toLocaleTimeString() : NA,
  );
  chart.data.datasets[0].data = rows.map((r) => (typeof r.cpu_percent === "number" ? r.cpu_percent : null));
  chart.data.datasets[1].data = rows.map((r) => (typeof r.mem_percent === "number" ? r.mem_percent : null));
  state.chartTsMs = tsMs.map((t) => (Number.isFinite(t) ? t : Date.now()));
  chart.update("none");
}

function appendChartPoint(tsUtc, cpuPercent, memPercent) {
  const chart = ensureChart();
  if (!chart) return;

  const t = Date.parse(tsUtc);
  const tsMs = Number.isFinite(t) ? t : Date.now();
  chart.data.labels.push(new Date(tsMs).toLocaleTimeString());
  chart.data.datasets[0].data.push(typeof cpuPercent === "number" ? cpuPercent : null);
  chart.data.datasets[1].data.push(typeof memPercent === "number" ? memPercent : null);
  state.chartTsMs.push(tsMs);

  const cutoff = Date.now() - 60 * 60 * 1000;
  while (state.chartTsMs.length > 0 && state.chartTsMs[0] < cutoff) {
    state.chartTsMs.shift();
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
    chart.data.datasets[1].data.shift();
  }

  const maxPoints = 1400;
  while (state.chartTsMs.length > maxPoints) {
    state.chartTsMs.shift();
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
    chart.data.datasets[1].data.shift();
  }

  chart.update("none");
}

function startFallback(summaryPoller, alertsPoller, networkPoller, processesPoller) {
  if (state.fallback.enabled) return;
  state.fallback.enabled = true;
  summaryPoller.start();
  alertsPoller.start();
  networkPoller.start();
  processesPoller.start();
}

function stopFallback(summaryPoller, alertsPoller, networkPoller, processesPoller) {
  if (!state.fallback.enabled) return;
  state.fallback.enabled = false;
  summaryPoller.stop();
  alertsPoller.stop();
  networkPoller.stop();
  processesPoller.stop();
}

function connectWebSocket({ onKpi, onChartPoint, onAlert, onTimelineEvent, onProcesses, onListeningPorts }) {
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  const url = `${scheme}://${window.location.host}/ws/live`;

  if (state.ws.socket) {
    try {
      state.ws.socket.close();
    } catch (_) {
      // ignore
    }
  }

  const ws = new WebSocket(url);
  state.ws.socket = ws;

  ws.addEventListener("open", () => {
    state.ws.connected = true;
    state.ws.disconnectedSinceMs = null;
    state.ws.reconnectDelayMs = 1000;
    updateWsBadge();
  });

  ws.addEventListener("message", (evt) => {
    let msg = null;
    try {
      msg = JSON.parse(evt.data);
    } catch (_) {
      return;
    }

    if (!msg || msg.v !== 1 || typeof msg.type !== "string") return;
    if (msg.type === "hello") return;
    if (msg.type === "kpi") onKpi(msg);
    if (msg.type === "chart_point") onChartPoint(msg);
    if (msg.type === "alert") onAlert(msg);
    if (msg.type === "timeline_event") onTimelineEvent(msg);
    if (msg.type === "processes") onProcesses(msg);
    if (msg.type === "listening_ports" && onListeningPorts) onListeningPorts(msg);
  });

  const onDisconnect = () => {
    if (state.ws.connected) {
      state.ws.connected = false;
      state.ws.disconnectedSinceMs = Date.now();
      updateWsBadge();
    }

    const delay = state.ws.reconnectDelayMs;
    state.ws.reconnectDelayMs = Math.min(state.ws.reconnectDelayMs * 2, 10000);
    window.setTimeout(
      () => connectWebSocket({ onKpi, onChartPoint, onAlert, onTimelineEvent, onProcesses, onListeningPorts }),
      delay,
    );
  };

  ws.addEventListener("close", onDisconnect);
  ws.addEventListener("error", onDisconnect);
}

document.addEventListener("DOMContentLoaded", async () => {
  updateWsBadge();

  const portsPoller = makePoller("/api/ports", 3000, handlePorts);
  portsPoller.start();

  const listeningPortsPoller = makePoller("/api/ports/listening?limit=2000", 5000, handleListeningPorts);
  listeningPortsPoller.start();

  const summaryPoller = makePoller("/api/summary", 2000, (json) => {
    if (!json || !json.ok || !json.data) {
      renderKpis(null);
      return;
    }
    renderKpis(json.data);
    updateLastUpdated();
  });

  const alertsPoller = makePoller("/api/alerts?limit=10", 5000, (json) => {
    if (!json || !json.ok || !Array.isArray(json.data)) {
      renderAlerts(null);
      return;
    }
    state.alerts = json.data.slice(0, 10);
    renderAlerts(state.alerts);
    updateLastUpdated();
  });

  const networkPoller = makePoller("/api/network", 5000, (json) => {
    if (!json || !json.ok || !json.data) {
      renderNetworkQuality({ status: NA, latency_ms: null });
      return;
    }
    renderNetworkQuality(json.data);
  });

  const processesPoller = makePoller("/api/processes?limit=10", 5000, (json) => {
    const items = json?.ok ? json?.data?.items : null;
    if (!Array.isArray(items)) {
      renderProcesses(null);
      return;
    }
    state.processes = items.slice(0, 10);
    renderProcesses(state.processes);
    updateLastUpdated();
  });

  try {
    const controller = new AbortController();
    const history = await fetchJson("/api/history?hours=1", controller);
    seedHistory(history);
  } catch (_) {
    seedHistory(null);
  }

  try {
    const controller = new AbortController();
    const summary = await fetchJson("/api/summary", controller);
    if (summary && summary.ok && summary.data) {
      renderKpis(summary.data);
    }
  } catch (_) {
    // ignore
  }

  try {
    const controller = new AbortController();
    const alerts = await fetchJson("/api/alerts?limit=10", controller);
    if (alerts && alerts.ok && Array.isArray(alerts.data)) {
      state.alerts = alerts.data.slice(0, 10);
      renderAlerts(state.alerts);
    }
  } catch (_) {
    // ignore
  }

  try {
    const controller = new AbortController();
    const timeline = await fetchJson("/api/timeline/latest?limit=20", controller);
    const items = timeline?.ok ? timeline?.data?.items : null;
    if (Array.isArray(items)) {
      state.timeline = items.slice(0, 20);
      renderTimeline(state.timeline);
    }
  } catch (_) {
    // ignore
  }

  try {
    const controller = new AbortController();
    const network = await fetchJson("/api/network", controller);
    if (network && network.ok && network.data) {
      renderNetworkQuality(network.data);
    }
  } catch (_) {
    // ignore
  }

  try {
    const controller = new AbortController();
    const processes = await fetchJson("/api/processes?limit=10", controller);
    const items = processes?.ok ? processes?.data?.items : null;
    if (Array.isArray(items)) {
      state.processes = items.slice(0, 10);
      renderProcesses(state.processes);
    }
  } catch (_) {
    // ignore
  }

  connectWebSocket({
    onKpi: (msg) => {
      const d = msg.data || null;
      renderKpis(d);
      if (d && (d.network_quality || d.ping_latency_ms !== undefined)) {
        renderNetworkQuality({ status: d.network_quality, latency_ms: d.ping_latency_ms });
      }
      updateLastUpdated();
    },
    onChartPoint: (msg) => {
      const d = msg.data || {};
      appendChartPoint(msg.ts_utc, d.cpu_percent, d.mem_percent);
    },
    onAlert: (msg) => {
      const a = msg.data || null;
      if (!a) return;
      const alert = {
        id: a.id,
        ts_utc: a.ts_utc || msg.ts_utc,
        type: a.type,
        severity: a.severity,
        message: a.message,
      };
      state.alerts = [alert, ...state.alerts.filter((x) => x.id !== alert.id)].slice(0, 10);
      renderAlerts(state.alerts);
      updateLastUpdated();
    },
    onTimelineEvent: (msg) => {
      const e = msg.data || null;
      if (!e) return;
      const item = {
        id: e.id,
        ts_utc: msg.ts_utc,
        kind: e.kind,
        severity: e.severity,
        message: e.message,
      };
      state.timeline = [item, ...state.timeline.filter((x) => x.id !== item.id)].slice(0, 20);
      renderTimeline(state.timeline);
      updateLastUpdated();
    },
    onProcesses: (msg) => {
      const items = msg?.data?.items;
      if (!Array.isArray(items)) {
        renderProcesses(null);
        return;
      }
      state.processes = items.slice(0, 10);
      renderProcesses(state.processes);
      updateLastUpdated();
    },
    onListeningPorts: (msg) => {
      const items = msg?.data?.items;
      if (!Array.isArray(items)) {
        renderListeningPorts(null);
        return;
      }
      state.listeningPorts.wsSeen = true;
      state.listeningPorts.items = items;
      state.listeningPorts.tsUtc = msg?.ts_utc ?? null;
      renderListeningPorts(state.listeningPorts.items);
      updateLastUpdated();
    },
  });

  const search = $("listening-ports-search");
  if (search) {
    search.addEventListener("input", () => {
      state.listeningPorts.query = search.value ?? "";
      renderListeningPorts(state.listeningPorts.items);
    });
  }

  window.setInterval(() => {
    if (state.ws.connected) {
      stopFallback(summaryPoller, alertsPoller, networkPoller, processesPoller);
      if (state.listeningPorts.wsSeen) listeningPortsPoller.stop();
      return;
    }

    listeningPortsPoller.start();
    const since = state.ws.disconnectedSinceMs;
    if (since != null && Date.now() - since > 10000) {
      startFallback(summaryPoller, alertsPoller, networkPoller, processesPoller);
    }
  }, 1000);
});
