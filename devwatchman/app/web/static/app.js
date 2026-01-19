/* global Chart */

const NA = "\u2014";

const state = {
  chart: null,
  chartTsMs: [],
  alerts: [],
  timeline: [],
  processes: [],
  history: {
    hours: 1,
    liveEnabled: true,
    resolution: null,
    points: 0,
    sinceTsUtc: null,
    tsMs: [],
    charts: {
      cpu: null,
      ram: null,
      net: null,
    },
    fetch: {
      controller: null,
      seq: 0,
    },
  },
  profiles: {
    active: "default",
    items: [],
  },
  docker: {
    items: [],
    query: "",
    wsSeen: false,
    available: false,
    reason: "unknown",
    tsUtc: null,
  },
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

function applyTheme(theme) {
  const root = document.documentElement;
  const next = theme === "dark" ? "dark" : "light";
  root.classList.toggle("dark", next === "dark");
  return next;
}

function getInitialTheme() {
  try {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  } catch (_) {
    return "dark";
  }
}

function debounce(fn, waitMs) {
  let t = null;
  return (...args) => {
    if (t) window.clearTimeout(t);
    t = window.setTimeout(() => fn(...args), waitMs);
  };
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

function chartTheme() {
  const isDark = document.documentElement.classList.contains("dark");
  return {
    isDark,
    text: isDark ? "rgba(226, 232, 240, 0.9)" : "rgba(15, 23, 42, 0.85)",
    muted: isDark ? "rgba(148, 163, 184, 0.9)" : "rgba(71, 85, 105, 0.85)",
    grid: isDark ? "rgba(51, 65, 85, 0.35)" : "rgba(148, 163, 184, 0.35)",
  };
}

function badgeClass(severity) {
  switch (severity) {
    case "critical":
      return "bg-rose-500/15 border-rose-400/30 text-rose-700 dark:text-rose-200";
    case "warning":
      return "bg-amber-500/15 border-amber-400/30 text-amber-700 dark:text-amber-200";
    default:
      return "bg-sky-500/15 border-sky-400/30 text-sky-700 dark:text-sky-200";
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

async function postJson(url) {
  const res = await fetch(url, {
    method: "POST",
    headers: { Accept: "application/json" },
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

function setActiveProfileUi(name) {
  const n = String(name ?? "default");
  state.profiles.active = n;
  setText("profile-active", n);

  const title = $("watched-ports-title");
  if (title) title.textContent = `Ports (${n})`;

  const subtitle = $("watched-ports-subtitle");
  if (subtitle) subtitle.textContent = "Watched services";

  const select = $("profile-select");
  if (select && select.value !== n) select.value = n;
}

function populateProfileSelect(items, active) {
  const select = $("profile-select");
  if (!select) return;
  const current = active ?? select.value ?? "default";
  select.innerHTML = items
    .slice()
    .map((p) => `<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}</option>`)
    .join("");
  select.value = current;
}

function handlePorts(json) {
  const tbody = $("ports-body");
  if (!tbody) return;

  if (!json || !json.ok || !Array.isArray(json.data)) {
    tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-600 dark:text-slate-400">${NA}</td></tr>`;
    return;
  }

  const metaProfile = json?.meta?.profile;
  if (metaProfile) setActiveProfileUi(metaProfile);

  const rows = json.data
    .slice()
    .sort((a, b) => a.port - b.port)
    .map((p) => {
      const status = p.listening ? "LISTEN" : "DOWN";
      const statusCls = p.listening
        ? "bg-emerald-500/15 border-emerald-400/30 text-emerald-700 dark:text-emerald-200"
        : "bg-rose-500/15 border-rose-400/30 text-rose-700 dark:text-rose-200";

      return `
        <tr class="hover:bg-slate-900/5 dark:hover:bg-slate-900/20">
          <td class="py-3 pr-3 text-slate-900 dark:text-slate-100">${p.port}</td>
          <td class="py-3 pr-3">
            <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs border ${statusCls}">
              ${status}
            </span>
          </td>
          <td class="py-3 pr-3 text-slate-700 dark:text-slate-200">${p.pid ?? NA}</td>
          <td class="py-3 text-slate-700 dark:text-slate-200">${p.process_name ?? NA}</td>
        </tr>
      `;
    })
    .join("");

  tbody.innerHTML = rows || `<tr><td colspan="4" class="py-4 text-slate-600 dark:text-slate-400">${NA}</td></tr>`;
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
    tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-600 dark:text-slate-400">Unable to load</td></tr>`;
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
    tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-600 dark:text-slate-400">No matches</td></tr>`;
    return;
  }

  tbody.innerHTML = show
    .map((p) => {
      const port = p?.port ?? NA;
      const localIp = escapeHtml(p?.local_ip ?? NA);
      const pid = p?.pid ?? NA;
      const name = escapeHtml(p?.process_name ?? NA);
      return `
        <tr class="hover:bg-slate-900/5 dark:hover:bg-slate-900/20">
          <td class="py-3 pr-3 text-slate-900 dark:text-slate-100">${port}</td>
          <td class="py-3 pr-3 text-slate-700 dark:text-slate-200">${localIp}</td>
          <td class="py-3 pr-3 text-slate-700 dark:text-slate-200">${pid}</td>
          <td class="py-3 text-slate-700 dark:text-slate-200 truncate max-w-[18rem]" title="${name}">${name}</td>
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
    list.innerHTML = `<div class="text-sm text-slate-600 dark:text-slate-400">${NA}</div>`;
    return;
  }

  if (count) count.textContent = `${alerts.length}`;
  if (alerts.length === 0) {
    list.innerHTML = `<div class="text-sm text-slate-600 dark:text-slate-400">No alerts</div>`;
    return;
  }

  list.innerHTML = alerts
    .map((a) => {
      const sev = a.severity ?? "info";
      const ts = a.ts_utc ? new Date(a.ts_utc).toLocaleTimeString() : NA;
      return `
        <div class="rounded-2xl border border-slate-200/70 bg-white/70 p-3 dark:border-slate-800/60 dark:bg-slate-950/20">
          <div class="flex items-center justify-between gap-2">
            <div class="text-xs text-slate-600 dark:text-slate-400">${ts}</div>
            <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs border ${badgeClass(sev)}">
              ${sev}
            </span>
          </div>
          <div class="mt-2 text-sm text-slate-900 dark:text-slate-100">${a.message ?? NA}</div>
          <div class="mt-1 text-xs text-slate-600 dark:text-slate-400">${a.type ?? ""}</div>
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
    list.innerHTML = `<div class="text-sm text-slate-600 dark:text-slate-400">${NA}</div>`;
    return;
  }

  if (count) count.textContent = `${items.length}`;
  if (items.length === 0) {
    list.innerHTML = `<div class="text-sm text-slate-600 dark:text-slate-400">No events</div>`;
    return;
  }

  list.innerHTML = items
    .map((e) => {
      const sev = e.severity ?? "info";
      const ts = e.ts_utc ? new Date(e.ts_utc).toLocaleTimeString() : NA;
      return `
        <div class="rounded-2xl border border-slate-200/70 bg-white/70 p-3 dark:border-slate-800/60 dark:bg-slate-950/20">
          <div class="flex items-center justify-between gap-2">
            <div class="text-xs text-slate-600 dark:text-slate-400">${ts}</div>
            <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs border ${badgeClass(sev)}">
              ${sev}
            </span>
          </div>
          <div class="mt-2 text-sm text-slate-900 dark:text-slate-100">${e.message ?? NA}</div>
        </div>
      `;
    })
    .join("");
}

function filterDockerItems(items, query) {
  if (!query) return items;
  const q = query.trim().toLowerCase();
  if (!q) return items;
  return items.filter((c) => {
    const name = (c?.name ?? "").toLowerCase();
    const image = (c?.image ?? "").toLowerCase();
    const status = (c?.status ?? "").toLowerCase();
    return name.includes(q) || image.includes(q) || status.includes(q);
  });
}

function renderDocker(items) {
  const tbody = $("docker-body");
  const meta = $("docker-meta");
  if (!tbody) return;

  if (!Array.isArray(items)) {
    if (meta) meta.textContent = NA;
    tbody.innerHTML = `<tr><td colspan="7" class="py-4 text-slate-600 dark:text-slate-400">Unable to load</td></tr>`;
    return;
  }

  const query = state.docker.query;
  const filtered = filterDockerItems(items, query);
  const maxRows = 50;
  const show = filtered.slice(0, maxRows);
  const truncated = filtered.length > maxRows;

  const connected = state.docker.available;
  const mode = state.ws.connected && state.docker.wsSeen ? "Live" : "Polling";
  const status = connected ? "Docker connected" : `Docker unavailable: ${state.docker.reason ?? "unknown"}`;
  if (meta) {
    const bits = [`${status} · ${mode} · ${filtered.length} shown`];
    if (query.trim()) bits.push(`filter: "${query.trim()}"`);
    if (truncated) bits.push("Showing first 50");
    meta.textContent = bits.join(" · ");
  }

  if (show.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="py-4 text-slate-600 dark:text-slate-400">No containers</td></tr>`;
    return;
  }

  tbody.innerHTML = show
    .map((c) => {
      const name = escapeHtml(c?.name ?? NA);
      const stateText = String(c?.state ?? c?.status ?? NA);
      const running = String(stateText).toLowerCase() === "running";
      const statusCls = running
        ? "bg-emerald-500/15 border-emerald-400/30 text-emerald-700 dark:text-emerald-200"
        : "bg-slate-500/10 border-slate-300/40 text-slate-700 dark:border-slate-400/20 dark:text-slate-300";

      const stats = c?.stats ?? {};
      const cpu = typeof stats.cpu_percent === "number" ? formatNumber(stats.cpu_percent, 1) : NA;
      const memPct = typeof stats.mem_percent === "number" ? formatNumber(stats.mem_percent, 1) : NA;
      const memUsed = typeof stats.mem_usage_bytes === "number" ? formatBytes(stats.mem_usage_bytes) : NA;
      const ports = Array.isArray(c?.ports) ? c.ports.slice(0, 2).join(", ") : "";
      const portsMore = Array.isArray(c?.ports) && c.ports.length > 2 ? ` +${c.ports.length - 2}` : "";
      const restarts = c?.restart_count ?? 0;

      return `
        <tr class="hover:bg-slate-900/5 dark:hover:bg-slate-900/20">
          <td class="py-3 pr-3 text-slate-900 dark:text-slate-100 truncate max-w-[10rem]" title="${name}">${name}</td>
          <td class="py-3 pr-3">
            <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs border ${statusCls}">
              ${escapeHtml(stateText)}
            </span>
          </td>
          <td class="py-3 pr-3 text-slate-700 dark:text-slate-200">${cpu}</td>
          <td class="py-3 pr-3 text-slate-700 dark:text-slate-200">${memPct}</td>
          <td class="py-3 pr-3 text-slate-700 dark:text-slate-200">${memUsed}</td>
          <td class="py-3 pr-3 text-slate-700 dark:text-slate-200 truncate max-w-[14rem]" title="${escapeHtml((Array.isArray(c?.ports) ? c.ports.join(', ') : '') || '')}">
            ${escapeHtml(ports)}${escapeHtml(portsMore)}
          </td>
          <td class="py-3 text-slate-700 dark:text-slate-200">${restarts}</td>
        </tr>
      `;
    })
    .join("");
}

function handleDocker(json) {
  const items = json?.ok ? json?.data?.items : null;
  if (!Array.isArray(items)) {
    renderDocker(null);
    return;
  }
  state.docker.items = items;
  state.docker.available = Boolean(json?.meta?.available);
  state.docker.reason = String(json?.meta?.reason ?? "unknown");
  state.docker.tsUtc = json?.meta?.ts_utc ?? null;
  renderDocker(state.docker.items);
}

function renderProcesses(items) {
  const tbody = $("processes-body");
  const status = $("processes-status");
  if (!tbody) return;

  if (!Array.isArray(items)) {
    if (status) status.textContent = "Unable to load processes";
    if (state.processes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-600 dark:text-slate-400">Unable to load processes</td></tr>`;
    }
    return;
  }

  if (status) status.textContent = state.ws.connected ? "Live" : "Fallback";

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-slate-600 dark:text-slate-400">No processes</td></tr>`;
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
        <tr class="hover:bg-slate-900/5 dark:hover:bg-slate-900/20">
          <td class="py-3 pr-3 text-slate-900 dark:text-slate-100 truncate max-w-[12rem]" title="${name}">${name}</td>
          <td class="py-3 pr-3 text-slate-700 dark:text-slate-200">${pid}</td>
          <td class="py-3 pr-3 text-slate-700 dark:text-slate-200">${cpu}</td>
          <td class="py-3 text-slate-700 dark:text-slate-200">${mem}</td>
        </tr>
      `;
    })
    .join("");
}

function historyMaxPoints(hours) {
  const estimate = Math.max(1, Number(hours) || 1) * 60 * 20; // ~20 points/min @ 3s interval
  return Math.min(2000, Math.max(600, estimate));
}

function formatHistoryLabel(tsMs, hours) {
  const d = new Date(tsMs);
  if (hours <= 24) {
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleString([], { month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function setHistoryError(message) {
  const el = $("history-error");
  if (!el) return;
  if (!message) {
    el.classList.add("hidden");
    return;
  }
  el.textContent = message;
  el.classList.remove("hidden");
}

function setHistoryUi({ hours, resolution, points, sinceTsUtc }) {
  const resolutionEl = $("history-resolution");
  const modeEl = $("history-mode");
  const metaEl = $("history-meta");
  const refreshBtn = $("history-refresh");

  if (resolutionEl) resolutionEl.textContent = `resolution: ${resolution ?? NA}`;
  const aggregated = Number(hours) > 6;
  if (modeEl) {
    modeEl.textContent = aggregated ? "Aggregated mode" : "Live mode";
    modeEl.className = aggregated
      ? "inline-flex items-center rounded-full px-2.5 py-1 border border-amber-400/30 bg-amber-500/15 text-amber-700 dark:text-amber-200"
      : "inline-flex items-center rounded-full px-2.5 py-1 border border-emerald-400/30 bg-emerald-500/15 text-emerald-700 dark:text-emerald-200";
  }
  if (refreshBtn) refreshBtn.classList.toggle("hidden", !aggregated);

  const pointsStr = typeof points === "number" ? `${points}` : NA;
  const sinceStr = sinceTsUtc ? new Date(sinceTsUtc).toLocaleString() : NA;
  if (metaEl) metaEl.textContent = `${hours}h · ${pointsStr} points · since ${sinceStr}`;
}

function setActiveHistoryRange(hours) {
  state.history.hours = hours;
  state.history.liveEnabled = Number(hours) <= 6;
  try {
    window.localStorage.setItem("dwm_history_hours", String(hours));
  } catch (_) {
    // ignore
  }

  const btns = document.querySelectorAll(".history-range-btn");
  btns.forEach((btn) => {
    const btnHours = Number(btn.getAttribute("data-range-hours"));
    const active = btnHours === Number(hours);
    btn.className = active
      ? "history-range-btn px-3 py-1.5 text-xs rounded-xl border border-sky-400/30 bg-sky-500/15 text-sky-700 dark:text-sky-200"
      : "history-range-btn px-3 py-1.5 text-xs rounded-xl border border-transparent text-slate-600 hover:bg-slate-900/5 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-900/30 dark:hover:text-slate-100";
  });
}

function createPercentChart(canvasId, color) {
  const el = $(canvasId);
  if (!el) return null;
  const ctx = el.getContext("2d");
  const t = chartTheme();
  return new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "%",
          data: [],
          borderColor: color.border,
          backgroundColor: color.bg,
          tension: 0.35,
          pointRadius: 0,
          borderWidth: 2,
          fill: true,
        },
      ],
    },
    options: {
      animation: false,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: true,
          callbacks: {
            label: (ctx2) => `${formatNumber(ctx2.parsed.y, 1)}%`,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: t.muted, maxTicksLimit: 10 },
          grid: { color: t.grid },
        },
        y: {
          min: 0,
          max: 100,
          ticks: { color: t.muted, callback: (v) => `${v}%` },
          grid: { color: t.grid },
        },
      },
    },
  });
}

function createNetworkChart(canvasId) {
  const el = $(canvasId);
  if (!el) return null;
  const ctx = el.getContext("2d");
  const t = chartTheme();
  return new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Sent",
          data: [],
          borderColor: "rgba(56, 189, 248, 0.95)",
          backgroundColor: "rgba(56, 189, 248, 0.10)",
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2,
          fill: true,
        },
        {
          label: "Recv",
          data: [],
          borderColor: "rgba(167, 139, 250, 0.95)",
          backgroundColor: "rgba(167, 139, 250, 0.08)",
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2,
          fill: true,
        },
      ],
    },
    options: {
      animation: false,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: { labels: { color: t.text } },
        tooltip: {
          enabled: true,
          callbacks: {
            label: (ctx2) => `${ctx2.dataset.label}: ${formatRate(ctx2.parsed.y)}`,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: t.muted, maxTicksLimit: 10 },
          grid: { color: t.grid },
        },
        y: {
          ticks: {
            color: t.muted,
            callback: (v) => `${formatBytes(v)}/s`,
          },
          grid: { color: t.grid },
        },
      },
    },
  });
}

function ensureHistoryCharts() {
  if (state.history.charts.cpu && state.history.charts.ram && state.history.charts.net) return;
  state.history.charts.cpu = createPercentChart("chart-cpu", {
    border: "rgba(56, 189, 248, 0.95)",
    bg: "rgba(56, 189, 248, 0.15)",
  });
  state.history.charts.ram = createPercentChart("chart-ram", {
    border: "rgba(52, 211, 153, 0.95)",
    bg: "rgba(52, 211, 153, 0.12)",
  });
  state.history.charts.net = createNetworkChart("chart-net");
}

function applyHistoryData({ hours, labels, tsMs, cpu, ram, netSent, netRecv }) {
  ensureHistoryCharts();
  const cpuChart = state.history.charts.cpu;
  const ramChart = state.history.charts.ram;
  const netChart = state.history.charts.net;
  if (!cpuChart || !ramChart || !netChart) return;

  const maxTicks = Number(hours) <= 24 ? 10 : 8;
  cpuChart.options.scales.x.ticks.maxTicksLimit = maxTicks;
  ramChart.options.scales.x.ticks.maxTicksLimit = maxTicks;
  netChart.options.scales.x.ticks.maxTicksLimit = maxTicks;

  cpuChart.data.labels = labels;
  cpuChart.data.datasets[0].data = cpu;
  ramChart.data.labels = labels;
  ramChart.data.datasets[0].data = ram;
  netChart.data.labels = labels;
  netChart.data.datasets[0].data = netSent;
  netChart.data.datasets[1].data = netRecv;

  state.history.tsMs = tsMs;
  cpuChart.update("none");
  ramChart.update("none");
  netChart.update("none");
}

async function fetchAndRenderHistory(hours) {
  const h = Number(hours) || 1;
  setActiveHistoryRange(h);
  setHistoryError(null);
  setText("history-meta", "Loading history…");

  state.history.fetch.seq += 1;
  const seq = state.history.fetch.seq;
  if (state.history.fetch.controller) state.history.fetch.controller.abort();
  state.history.fetch.controller = new AbortController();

  try {
    const json = await fetchJson(`/api/history?hours=${encodeURIComponent(h)}`, state.history.fetch.controller);
    if (seq !== state.history.fetch.seq) return;

    if (!json || !json.ok || !Array.isArray(json.data)) {
      setHistoryError("Unable to load history");
      return;
    }

    const resolution = json?.meta?.resolution ?? NA;
    const sinceTsUtc = json?.meta?.since_ts_utc ?? null;
    const points = typeof json?.meta?.points === "number" ? json.meta.points : json.data.length;
    setHistoryUi({ hours: h, resolution, points, sinceTsUtc });

    const rows = json.data;
    const tsMs = [];
    const labels = [];
    const cpu = [];
    const ram = [];
    const netSent = [];
    const netRecv = [];

    for (const r of rows) {
      const t = r?.ts_utc ? Date.parse(r.ts_utc) : NaN;
      if (!Number.isFinite(t)) continue;
      tsMs.push(t);
      labels.push(formatHistoryLabel(t, h));
      cpu.push(typeof r.cpu_percent === "number" ? r.cpu_percent : null);
      ram.push(typeof r.mem_percent === "number" ? r.mem_percent : null);
      netSent.push(typeof r.net_sent_bps === "number" ? r.net_sent_bps : null);
      netRecv.push(typeof r.net_recv_bps === "number" ? r.net_recv_bps : null);
    }

    const hardCap = 2000;
    if (tsMs.length > hardCap) {
      const stride = Math.ceil(tsMs.length / hardCap);
      const dTs = [];
      const dLabels = [];
      const dCpu = [];
      const dRam = [];
      const dSent = [];
      const dRecv = [];
      for (let i = 0; i < tsMs.length; i += 1) {
        if (i % stride !== 0 && i !== tsMs.length - 1) continue;
        dTs.push(tsMs[i]);
        dLabels.push(labels[i]);
        dCpu.push(cpu[i]);
        dRam.push(ram[i]);
        dSent.push(netSent[i]);
        dRecv.push(netRecv[i]);
      }
      applyHistoryData({ hours: h, labels: dLabels, tsMs: dTs, cpu: dCpu, ram: dRam, netSent: dSent, netRecv: dRecv });
      return;
    }

    applyHistoryData({ hours: h, labels, tsMs, cpu, ram, netSent, netRecv });
  } catch (_) {
    if (seq !== state.history.fetch.seq) return;
    setHistoryError("Unable to load history");
  }
}

function appendLiveHistoryPoint(tsUtc, cpuPercent, memPercent, netSentBps, netRecvBps) {
  if (!state.history.liveEnabled) return;
  ensureHistoryCharts();
  const cpuChart = state.history.charts.cpu;
  const ramChart = state.history.charts.ram;
  const netChart = state.history.charts.net;
  if (!cpuChart || !ramChart || !netChart) return;

  const t = Date.parse(tsUtc);
  const tsMs = Number.isFinite(t) ? t : Date.now();

  state.history.tsMs.push(tsMs);
  const label = formatHistoryLabel(tsMs, state.history.hours);

  cpuChart.data.labels.push(label);
  cpuChart.data.datasets[0].data.push(typeof cpuPercent === "number" ? cpuPercent : null);
  ramChart.data.labels.push(label);
  ramChart.data.datasets[0].data.push(typeof memPercent === "number" ? memPercent : null);
  netChart.data.labels.push(label);
  netChart.data.datasets[0].data.push(typeof netSentBps === "number" ? netSentBps : null);
  netChart.data.datasets[1].data.push(typeof netRecvBps === "number" ? netRecvBps : null);

  const cutoff = Date.now() - Number(state.history.hours) * 60 * 60 * 1000;
  while (state.history.tsMs.length > 0 && state.history.tsMs[0] < cutoff) {
    state.history.tsMs.shift();
    cpuChart.data.labels.shift();
    cpuChart.data.datasets[0].data.shift();
    ramChart.data.labels.shift();
    ramChart.data.datasets[0].data.shift();
    netChart.data.labels.shift();
    netChart.data.datasets[0].data.shift();
    netChart.data.datasets[1].data.shift();
  }

  const maxPoints = historyMaxPoints(state.history.hours);
  while (state.history.tsMs.length > maxPoints) {
    state.history.tsMs.shift();
    cpuChart.data.labels.shift();
    cpuChart.data.datasets[0].data.shift();
    ramChart.data.labels.shift();
    ramChart.data.datasets[0].data.shift();
    netChart.data.labels.shift();
    netChart.data.datasets[0].data.shift();
    netChart.data.datasets[1].data.shift();
  }

  cpuChart.update("none");
  ramChart.update("none");
  netChart.update("none");
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

function connectWebSocket({ onKpi, onChartPoint, onAlert, onTimelineEvent, onProcesses, onListeningPorts, onDocker }) {
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
    if (msg.type === "docker" && onDocker) onDocker(msg);
    if (msg.type === "profile" && msg.data) {
      setActiveProfileUi(msg.data.active);
      if (Array.isArray(state.profiles.items) && state.profiles.items.length > 0) {
        populateProfileSelect(state.profiles.items, msg.data.active);
      }
    }
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
      () => connectWebSocket({ onKpi, onChartPoint, onAlert, onTimelineEvent, onProcesses, onListeningPorts, onDocker }),
      delay,
    );
  };

  ws.addEventListener("close", onDisconnect);
  ws.addEventListener("error", onDisconnect);
}

document.addEventListener("DOMContentLoaded", async () => {
  const processesCard = $("processes-card");
  const processesExpand = $("processes-expand");
  if (processesCard && processesExpand) {
    processesExpand.addEventListener("click", () => {
      const expanded = processesCard.classList.toggle("dwm-card-expanded");
      processesExpand.setAttribute("aria-expanded", expanded ? "true" : "false");
      processesExpand.textContent = expanded ? "Collapse" : "Expand";
    });
  }

  applyTheme(getInitialTheme());

  updateWsBadge();

  document.querySelectorAll(".history-range-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const hours = Number(btn.getAttribute("data-range-hours")) || 1;
      fetchAndRenderHistory(hours);
    });
  });
  const refreshBtn = $("history-refresh");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      fetchAndRenderHistory(state.history.hours);
    });
  }
  let initialHours = 1;
  try {
    const stored = Number(window.localStorage.getItem("dwm_history_hours"));
    if (Number.isFinite(stored) && stored > 0) initialHours = stored;
  } catch (_) {
    // ignore
  }
  setActiveHistoryRange(initialHours);
  ensureHistoryCharts();
  fetchAndRenderHistory(initialHours);

  const portsPoller = makePoller("/api/ports", 3000, handlePorts);
  portsPoller.start();

  const listeningPortsPoller = makePoller("/api/ports/listening?limit=2000", 5000, handleListeningPorts);
  listeningPortsPoller.start();

  const dockerPoller = makePoller("/api/docker/containers?include_stopped=true&limit=50", 5000, handleDocker);
  dockerPoller.start();

  try {
    const controller = new AbortController();
    const profiles = await fetchJson("/api/profiles", controller);
    if (profiles?.ok && profiles?.data) {
      const active = profiles.data.active ?? "default";
      const items = Array.isArray(profiles.data.profiles) ? profiles.data.profiles : [];
      state.profiles.items = items;
      populateProfileSelect(items, active);
      setActiveProfileUi(active);
    }
  } catch (_) {
    // ignore
  }

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
      appendLiveHistoryPoint(msg.ts_utc, d.cpu_percent, d.mem_percent, d.net_sent_bps, d.net_recv_bps);
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
    onDocker: (msg) => {
      const items = msg?.data?.items;
      if (!Array.isArray(items)) {
        renderDocker(null);
        return;
      }
      state.docker.wsSeen = true;
      state.docker.available = Boolean(msg?.data?.available);
      state.docker.reason = String(msg?.data?.reason ?? "unknown");
      state.docker.items = items;
      state.docker.tsUtc = msg?.ts_utc ?? null;
      renderDocker(state.docker.items);
      updateLastUpdated();
    },
  });

  const profileSelect = $("profile-select");
  if (profileSelect) {
    profileSelect.addEventListener("change", async () => {
      const next = profileSelect.value ?? "default";
      try {
        profileSelect.disabled = true;
        const json = await postJson(`/api/profiles/select?name=${encodeURIComponent(next)}`);
        if (json?.ok && json?.data?.active) {
          setActiveProfileUi(json.data.active);
        }
      } catch (_) {
        // ignore
      } finally {
        profileSelect.disabled = false;
      }
    });
  }

  const search = $("listening-ports-search");
  if (search) {
    search.addEventListener(
      "input",
      debounce(() => {
        state.listeningPorts.query = search.value ?? "";
        renderListeningPorts(state.listeningPorts.items);
      }, 60),
    );
  }

  const dockerSearch = $("docker-search");
  if (dockerSearch) {
    dockerSearch.addEventListener(
      "input",
      debounce(() => {
        state.docker.query = dockerSearch.value ?? "";
        renderDocker(state.docker.items);
      }, 60),
    );
  }

  window.setInterval(() => {
    if (state.ws.connected) {
      stopFallback(summaryPoller, alertsPoller, networkPoller, processesPoller);
      if (state.listeningPorts.wsSeen) listeningPortsPoller.stop();
      if (state.docker.wsSeen) dockerPoller.stop();
      return;
    }

    listeningPortsPoller.start();
    dockerPoller.start();
    const since = state.ws.disconnectedSinceMs;
    if (since != null && Date.now() - since > 10000) {
      startFallback(summaryPoller, alertsPoller, networkPoller, processesPoller);
    }
  }, 1000);
});
