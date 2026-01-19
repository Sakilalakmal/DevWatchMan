import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

import logoUrl from "./assets/devwatchman-logo.png";

type StatusEls = {
  card: HTMLElement;
  logo: HTMLImageElement;
  title: HTMLElement;
  subtitle: HTMLElement;
  copyLogs: HTMLButtonElement;
  details: HTMLElement;
  frame: HTMLElement;
  iframe: HTMLIFrameElement;
};

type BackendStarting = { type: "starting" };
type BackendPortDetected = { type: "port_detected"; port: number };
type BackendReady = { type: "ready"; port: number; base_url: string; log_path: string };
type BackendError = {
  type: "error";
  message: string;
  details: string;
  log_path: string;
  last_logs: string;
};

type BackendState = BackendStarting | BackendPortDetected | BackendReady | BackendError;

function getEls(): StatusEls {
  const card = document.getElementById("status-card");
  const logo = document.getElementById("brand-logo");
  const title = document.getElementById("status-title");
  const subtitle = document.getElementById("status-subtitle");
  const copyLogs = document.getElementById("copy-logs");
  const details = document.getElementById("status-details");
  const frame = document.getElementById("frame");
  const iframe = document.getElementById("dashboard");

  if (
    !card ||
    !(logo instanceof HTMLImageElement) ||
    !title ||
    !subtitle ||
    !(copyLogs instanceof HTMLButtonElement) ||
    !details ||
    !frame ||
    !(iframe instanceof HTMLIFrameElement)
  ) {
    throw new Error("UI elements missing (index.html mismatch)");
  }

  return { card, logo, title, subtitle, copyLogs, details, frame, iframe };
}

function setStatus(els: StatusEls, title: string, subtitle: string, details?: string): void {
  els.title.textContent = title;
  els.subtitle.textContent = subtitle;
  if (details) {
    els.details.textContent = details;
    els.details.removeAttribute("hidden");
  } else {
    els.details.textContent = "";
    els.details.setAttribute("hidden", "true");
  }
}

function showDashboard(els: StatusEls, url: string): void {
  els.card.setAttribute("hidden", "true");
  els.frame.removeAttribute("hidden");
  els.iframe.src = url;
}

function showError(els: StatusEls, message: string, details?: string): void {
  els.card.removeAttribute("hidden");
  els.frame.setAttribute("hidden", "true");
  els.copyLogs.removeAttribute("hidden");
  setStatus(els, "Failed to start DevWatchMan", message, details);
}

function hideCopyLogs(els: StatusEls): void {
  els.copyLogs.setAttribute("hidden", "true");
  els.copyLogs.disabled = false;
  els.copyLogs.textContent = "Copy logs";
}

function formatErrorDetails(state: BackendError): string {
  const details = state.details?.trim() ? state.details.trim() : state.message?.trim();
  const parts = [
    details || "No details available.",
    state.log_path ? `\n\nLog file:\n${state.log_path}` : "",
    state.last_logs?.trim()
      ? `\n\nLast ${state.last_logs.split("\n").length} log lines:\n${state.last_logs}`
      : "",
  ].filter(Boolean);

  return parts.join("");
}

function applyBackendState(els: StatusEls, state: BackendState): void {
  if (state.type === "starting") {
    hideCopyLogs(els);
    setStatus(els, "Starting DevWatchMan", "Launching local backend");
    return;
  }

  if (state.type === "port_detected") {
    hideCopyLogs(els);
    setStatus(els, "Starting DevWatchMan", `Backend started (port ${state.port}). Waiting for health check...`);
    return;
  }

  if (state.type === "ready") {
    hideCopyLogs(els);
    const url = `${state.base_url}/`;
    setStatus(els, "Starting DevWatchMan", `Loading ${url}`);
    showDashboard(els, url);
    return;
  }

  showError(els, state.message || "Backend failed to start.", formatErrorDetails(state));
}

window.addEventListener("DOMContentLoaded", async () => {
  const els = getEls();
  let lastLogs = "";

  els.logo.src = logoUrl;
  requestAnimationFrame(() => els.logo.classList.add("is-visible"));
  hideCopyLogs(els);

  els.copyLogs.addEventListener("click", async () => {
    let text = lastLogs || els.details.textContent || "";
    try {
      const latest = await invoke<string>("backend_get_last_logs");
      if (latest?.trim()) text = latest;
    } catch {
      // fallback to existing details text
    }

    try {
      await navigator.clipboard.writeText(text);
      els.copyLogs.textContent = "Copied";
      els.copyLogs.disabled = true;
      setTimeout(() => {
        els.copyLogs.textContent = "Copy logs";
        els.copyLogs.disabled = false;
      }, 1200);
    } catch {
      els.details.removeAttribute("hidden");
    }
  });

  try {
    const initial = await invoke<BackendState>("backend_get_state");
    applyBackendState(els, initial);
    if (initial.type === "error") lastLogs = initial.last_logs || "";

    await listen<BackendState>("backend://state", (event) => {
      const state = event.payload;
      applyBackendState(els, state);
      if (state.type === "error") lastLogs = state.last_logs || "";
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    showError(els, "Failed to initialize app startup.", message);
  }
});
