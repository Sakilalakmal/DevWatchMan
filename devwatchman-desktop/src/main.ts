import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
import { Command, type Child } from "@tauri-apps/plugin-shell";

type StatusEls = {
  card: HTMLElement;
  title: HTMLElement;
  subtitle: HTMLElement;
  details: HTMLElement;
  frame: HTMLElement;
  iframe: HTMLIFrameElement;
};

function getEls(): StatusEls {
  const card = document.getElementById("status-card");
  const title = document.getElementById("status-title");
  const subtitle = document.getElementById("status-subtitle");
  const details = document.getElementById("status-details");
  const frame = document.getElementById("frame");
  const iframe = document.getElementById("dashboard");

  if (!card || !title || !subtitle || !details || !frame || !(iframe instanceof HTMLIFrameElement)) {
    throw new Error("UI elements missing (index.html mismatch)");
  }

  return { card, title, subtitle, details, frame, iframe };
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
  setStatus(els, "Failed to start DevWatchMan", message, details);
}

async function startBackend(els: StatusEls): Promise<{ child: Child; port: number }>
{
  setStatus(els, "Starting DevWatchMan…", "Launching local backend");

  const command = Command.sidecar("devwatchman-backend");

  let resolvePort: ((port: number) => void) | undefined;
  let rejectPort: ((err: Error) => void) | undefined;
  const portPromise = new Promise<number>((resolve, reject) => {
    resolvePort = resolve;
    rejectPort = reject;
  });

  const stdoutHandler = (line: string) => {
    const trimmed = line.trim();
    // Expected first line: DEVWATCHMAN_PORT=8000
    const match = /^DEVWATCHMAN_PORT=(\d{2,5})$/.exec(trimmed);
    if (match) {
      resolvePort?.(Number(match[1]));
      resolvePort = undefined;
      rejectPort = undefined;
    }
  };

  const stderrLines: string[] = [];
  const stderrHandler = (line: string) => {
    const trimmed = line.trimEnd();
    stderrLines.push(trimmed);
    if (stderrLines.length > 200) stderrLines.shift();
  };

  command.stdout.on("data", stdoutHandler);
  command.stderr.on("data", stderrHandler);

  command.on("close", (data) => {
    const details = [
      `exit code: ${data.code}`,
      data.signal ? `signal: ${data.signal}` : undefined,
      stderrLines.length ? `--- stderr ---\n${stderrLines.join("\n")}` : undefined,
    ]
      .filter(Boolean)
      .join("\n");

    rejectPort?.(new Error(details || "Backend process exited"));
    resolvePort = undefined;
    rejectPort = undefined;
  });

  command.on("error", (error) => {
    rejectPort?.(new Error(error));
    resolvePort = undefined;
    rejectPort = undefined;
  });

  const child = await command.spawn();

  const timeoutMs = 20_000;
  const timeout = new Promise<number>((_, reject) =>
    setTimeout(() => reject(new Error(`Timed out waiting for backend port (${timeoutMs}ms)`)), timeoutMs)
  );

  const port = await Promise.race([portPromise, timeout]);
  return { child, port };
}

window.addEventListener("DOMContentLoaded", async () => {
  const els = getEls();
  let child: Child | null = null;

  try {
    const started = await startBackend(els);
    child = started.child;

    const url = `http://127.0.0.1:${started.port}/`;
    setStatus(els, "Starting DevWatchMan…", `Loading ${url}`);
    showDashboard(els, url);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    showError(els, "Backend failed to start. See details.", message);
    return;
  }

  const appWindow = getCurrentWebviewWindow();
  await appWindow.onCloseRequested(async (event) => {
    event.preventDefault();
    try {
      if (child) {
        await child.kill();
      }
    } catch {
      // best-effort
    } finally {
      await appWindow.close();
    }
  });
});
