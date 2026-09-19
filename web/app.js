document.addEventListener("DOMContentLoaded", () => {
  initCopyButtons();
  initConsole();
  initExplorerFilter();
  initModal();
});

function initCopyButtons() {
  const installCopyBtn = document.getElementById("btn-copy-install");
  if (installCopyBtn) {
    installCopyBtn.addEventListener("click", () => {
      const code = document.getElementById("install-cmd")?.textContent?.trim() || "pip install animesaturn";
      copyToClipboard(code, installCopyBtn);
    });
  }

  const copyOutputBtn = document.getElementById("btn-copy-output");
  if (copyOutputBtn) {
    copyOutputBtn.addEventListener("click", () => {
      const isJsonActive = document.getElementById("json-view")?.classList.contains("active");
      const targetElem = isJsonActive ? document.getElementById("json-code-content") : document.getElementById("python-code-content");
      if (targetElem) {
        copyToClipboard(targetElem.textContent || "", copyOutputBtn);
      }
    });
  }
}

function copyToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    const tooltip = btnElement.querySelector(".copy-tooltip");
    if (tooltip) {
      tooltip.classList.add("show");
      setTimeout(() => tooltip.classList.remove("show"), 1500);
    } else {
      const span = btnElement.querySelector("span");
      if (span) {
        const prev = span.textContent;
        span.textContent = "Copied!";
        setTimeout(() => span.textContent = prev, 1500);
      }
    }
  }).catch(() => {});
}

function getSelectedBaseServer() {
  const select = document.getElementById("api-server-select");
  if (!select) return "https://api.lawliet.lol";
  if (select.value === "custom") {
    const currentVal = document.getElementById("api-url-input")?.value || "";
    try {
      const parsed = new URL(currentVal);
      return parsed.origin;
    } catch {
      return "https://api.lawliet.lol";
    }
  }
  return select.value;
}

function initConsole() {
  const urlInput = document.getElementById("api-url-input");
  const runBtn = document.getElementById("btn-run-query");
  const spinner = document.getElementById("query-spinner");
  const btnText = runBtn?.querySelector(".btn-run-text");
  const statusBadge = document.getElementById("status-badge");
  const responseTimeBadge = document.getElementById("response-time-badge");
  const jsonCodeContent = document.getElementById("json-code-content");
  const pythonCodeContent = document.getElementById("python-code-content");
  const serverSelect = document.getElementById("api-server-select");

  const tabBtnJson = document.getElementById("tab-btn-json");
  const tabBtnCode = document.getElementById("tab-btn-code");
  const jsonView = document.getElementById("json-view");
  const codeView = document.getElementById("code-view");

  if (tabBtnJson && tabBtnCode && jsonView && codeView) {
    tabBtnJson.addEventListener("click", () => {
      tabBtnJson.classList.add("active");
      tabBtnCode.classList.remove("active");
      jsonView.classList.add("active");
      codeView.classList.remove("active");
    });

    tabBtnCode.addEventListener("click", () => {
      tabBtnCode.classList.add("active");
      tabBtnJson.classList.remove("active");
      codeView.classList.add("active");
      jsonView.classList.remove("active");
    });
  }

  if (serverSelect && urlInput) {
    serverSelect.addEventListener("change", () => {
      if (serverSelect.value === "custom") {
        urlInput.focus();
        return;
      }
      try {
        const currentUrl = new URL(urlInput.value, window.location.origin);
        urlInput.value = `${serverSelect.value}${currentUrl.pathname}${currentUrl.search}`;
      } catch {
        urlInput.value = `${serverSelect.value}/api/search?q=Solo+Leveling`;
      }
      runQuery();
    });
  }

  const presetBtns = document.querySelectorAll(".preset-btn");
  presetBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      presetBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const base = getSelectedBaseServer();
      const type = btn.dataset.type;
      const query = btn.dataset.query;

      if (type === "search") {
        urlInput.value = `${base}/api/search?q=${encodeURIComponent(query)}`;
      } else if (type === "latest") {
        urlInput.value = `${base}/api/latest`;
      } else if (type === "mirrors") {
        urlInput.value = `${base}/api/domains`;
      }
      runQuery();
    });
  });

  async function runQuery() {
    if (!urlInput) return;
    const rawUrl = urlInput.value.trim();
    if (!rawUrl) return;

    if (spinner) spinner.classList.add("show");
    if (btnText) btnText.textContent = "Executing...";
    if (runBtn) runBtn.disabled = true;

    const startTime = performance.now();
    let resolvedData = null;
    let statusCode = 200;
    let statusText = "OK";
    let isError = false;

    try {
      const res = await fetch(rawUrl, {
        headers: { "Accept": "application/json" }
      });
      statusCode = res.status;
      statusText = res.statusText || (res.ok ? "OK" : "Error");
      
      const contentType = res.headers.get("content-type") || "";
      if (contentType.includes("json")) {
        resolvedData = await res.json();
      } else {
        const text = await res.text();
        resolvedData = {
          status: res.status,
          response: text.slice(0, 500)
        };
      }
      if (!res.ok) {
        isError = true;
      }
    } catch (err) {
      isError = true;
      statusCode = 503;
      statusText = "Machine Unavailable";
      resolvedData = {
        error: true,
        endpoint: rawUrl,
        message: err.message || "Failed to establish connection to the machine API.",
        notice: "If your Render service is on the free tier, it spins down after inactivity. Sending this request initiates wakeup; retry in 30-45 seconds."
      };
    }

    const elapsed = Math.max(10, Math.round(performance.now() - startTime));
    if (responseTimeBadge) responseTimeBadge.textContent = `${elapsed}ms`;

    if (statusBadge) {
      statusBadge.textContent = `${statusCode} ${statusText}`;
      statusBadge.className = `status-indicator ${isError ? "status-err" : "status-ok"}`;
    }

    if (jsonCodeContent) {
      jsonCodeContent.innerHTML = syntaxHighlightJson(resolvedData);
    }

    if (pythonCodeContent) {
      pythonCodeContent.textContent = generatePythonSnippet(rawUrl);
    }

    if (spinner) spinner.classList.remove("show");
    if (btnText) btnText.textContent = "Run Query";
    if (runBtn) runBtn.disabled = false;
  }

  if (runBtn) {
    runBtn.addEventListener("click", runQuery);
  }

  if (urlInput) {
    urlInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") runQuery();
    });
  }

  runQuery();
}

function syntaxHighlightJson(jsonObj) {
  const jsonStr = JSON.stringify(jsonObj, null, 2);
  return jsonStr
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
      let cls = "json-number";
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = "json-key";
        } else {
          cls = "json-string";
        }
      } else if (/true|false/.test(match)) {
        cls = "json-boolean";
      } else if (/null/.test(match)) {
        cls = "json-null";
      }
      return `<span class="${cls}">${match}</span>`;
    });
}

function generatePythonSnippet(url) {
  if (url.includes("/api/search")) {
    const qMatch = url.match(/[?&]q=([^&]+)/);
    const query = qMatch ? decodeURIComponent(qMatch[1]) : "Solo Leveling";
    return `import animesaturn\n\nresults = animesaturn.find("${query}")\nfor anime in results:\n    print(anime["name"], anime["episodes"], anime["url"])`;
  }
  if (url.includes("/api/latest")) {
    return `import animesaturn\n\nlatest = animesaturn.latest_episodes(page=1)\nfor ep in latest.get("items", []):\n    print(ep["title"], ep["episodeLabel"])`;
  }
  if (url.includes("/api/domains")) {
    return `import animesaturn\n\nmirrors = animesaturn.fetch_official_domains()\nactive = animesaturn.discover_active_domain()\nprint("Active mirror:", active)`;
  }
  if (url.includes("/api/anime/")) {
    const slug = url.split("/api/anime/")[1]?.split("?")[0] || "solo-leveling-6iHEN";
    return `import animesaturn\n\nanime = animesaturn.Anime("${slug}")\nprint(anime.title, f"{len(anime)} episodes")\nfor ep in anime:\n    print(ep.number, ep.url)`;
  }
  if (url.includes("/api/stream/")) {
    const parts = url.split("/api/stream/")[1]?.split("/") || ["solo-leveling-6iHEN", "1"];
    const slug = parts[0];
    const epNum = parts[1] || "1";
    return `import animesaturn\n\nanime = animesaturn.Anime("${slug}")\nep = anime[${epNum}]\nfor server in ep.getServer():\n    stream_url = server.fileLink()\n    print(f"[{server.name}] -> {stream_url}")`;
  }
  return `import animesaturn\n\nresults = animesaturn.find("Solo Leveling")\nprint(results)`;
}

function initExplorerFilter() {
  const searchInput = document.getElementById("explorer-search-input");
  const cards = document.querySelectorAll(".anime-card");

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      cards.forEach(card => {
        const title = card.dataset.title.toLowerCase();
        if (title.includes(q)) {
          card.style.display = "flex";
        } else {
          card.style.display = "none";
        }
      });
    });
  }

  cards.forEach(card => {
    card.addEventListener("click", () => {
      openAnimeModal(card.dataset.slug, card.dataset.title, card.querySelector(".card-poster")?.src);
    });
  });
}

function initModal() {
  const backdrop = document.getElementById("modal-backdrop");
  const closeBtn = document.getElementById("btn-modal-close");

  if (backdrop) {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) closeModal();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", closeModal);
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && backdrop && backdrop.classList.contains("open")) {
      closeModal();
    }
  });
}

function closeModal() {
  const backdrop = document.getElementById("modal-backdrop");
  if (backdrop) backdrop.classList.remove("open");
}

async function openAnimeModal(slug, fallbackTitle, posterSrc) {
  const backdrop = document.getElementById("modal-backdrop");
  const container = document.getElementById("modal-content-container");
  if (!backdrop || !container) return;

  const base = getSelectedBaseServer();
  backdrop.classList.add("open");

  container.innerHTML = `
    <div>
      <img class="modal-poster" src="${posterSrc || "static/img/logo.png"}" alt="${escapeHtml(fallbackTitle)}">
    </div>
    <div>
      <h2 class="modal-title">${escapeHtml(fallbackTitle)}</h2>
      <div class="modal-pills">
        <span class="modal-pill">Loading Live Data from ${escapeHtml(base)}...</span>
      </div>
      <div id="modal-body-area">
        <div class="spinner show" style="margin: 20px 0;"></div>
      </div>
    </div>
  `;

  try {
    const res = await fetch(`${base}/api/anime/${encodeURIComponent(slug)}`, {
      headers: { "Accept": "application/json" }
    });
    
    if (res.ok) {
      const data = await res.json();
      renderModalContent(container, data, slug, base);
      return;
    }
  } catch {}

  renderModalFallback(container, slug, fallbackTitle, posterSrc, base);
}

function renderModalContent(container, data, slug, base) {
  const episodes = data.episodes || [];
  const epsCount = episodes.length || data.episodes_count || 12;
  const epButtons = [];

  for (let i = 0; i < Math.min(episodes.length, 36); i++) {
    const ep = episodes[i];
    const num = ep.number || (i + 1);
    epButtons.push(`<button class="ep-btn" data-ep="${num}">Ep. ${num}</button>`);
  }

  container.innerHTML = `
    <div>
      <img class="modal-poster" src="${data.poster || "static/img/logo.png"}" alt="${escapeHtml(data.title)}">
    </div>
    <div>
      <h2 class="modal-title">${escapeHtml(data.title)}</h2>
      ${data.jtitle ? `<div class="modal-jtitle">${escapeHtml(data.jtitle)}</div>` : ""}
      
      <div class="modal-pills">
        <span class="modal-pill">${epsCount} Episodes</span>
        ${data.category ? `<span class="modal-pill">${escapeHtml(data.category)}</span>` : ""}
        ${data.status ? `<span class="modal-pill">${escapeHtml(data.status)}</span>` : ""}
        ${data.studio ? `<span class="modal-pill">${escapeHtml(data.studio)}</span>` : ""}
        ${data.year ? `<span class="modal-pill">${escapeHtml(data.year)}</span>` : ""}
      </div>

      <p class="modal-synopsis">${escapeHtml(data.story || "No synopsis available.")}</p>

      <div class="modal-section-title">
        <span>Select Episode to Inspect Stream:</span>
      </div>

      <div class="episode-picker-grid">
        ${epButtons.length > 0 ? epButtons.join("") : "<span style='color:#9ba3af;'>No episode list returned.</span>"}
      </div>

      <div id="modal-stream-info" style="margin-top: 14px; padding: 12px 14px; background: #16181d; border: 1px solid #303642; border-radius: 4px;">
        <div style="font-size: 0.84rem; color: #9ba3af;">
          Click an episode above to decrypt direct stream URLs via <code>${escapeHtml(base)}</code>.
        </div>
        <div style="margin-top: 10px; display: flex; gap: 8px;">
          <a href="${data.url || `https://www.animesaturn.net/anime/${slug}`}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="padding: 5px 12px; font-size: 0.8rem;">
            Open on AnimeSaturn
          </a>
        </div>
      </div>
    </div>
  `;

  attachEpisodeClickHandlers(container, slug, base);
}

function renderModalFallback(container, slug, fallbackTitle, posterSrc, base) {
  const epButtons = [];
  for (let i = 1; i <= 24; i++) {
    epButtons.push(`<button class="ep-btn" data-ep="${i}">Ep. ${i}</button>`);
  }

  container.innerHTML = `
    <div>
      <img class="modal-poster" src="${posterSrc || "static/img/logo.png"}" alt="${escapeHtml(fallbackTitle)}">
    </div>
    <div>
      <h2 class="modal-title">${escapeHtml(fallbackTitle)}</h2>
      
      <div class="modal-pills">
        <span class="modal-pill">Offline Preview</span>
        <span class="modal-pill">TV Series</span>
      </div>

      <p class="modal-synopsis">Select an episode below to request live stream decryption from the Render machine API.</p>

      <div class="modal-section-title">
        <span>Select Episode:</span>
      </div>

      <div class="episode-picker-grid">
        ${epButtons.join("")}
      </div>

      <div id="modal-stream-info" style="margin-top: 14px; padding: 12px 14px; background: #16181d; border: 1px solid #303642; border-radius: 4px;">
        <div style="font-size: 0.84rem; color: #9ba3af;">
          Click an episode above to decrypt stream URLs.
        </div>
        <div style="margin-top: 10px; display: flex; gap: 8px;">
          <a href="https://www.animesaturn.net/anime/${slug}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="padding: 5px 12px; font-size: 0.8rem;">
            Open on AnimeSaturn
          </a>
        </div>
      </div>
    </div>
  `;

  attachEpisodeClickHandlers(container, slug, base);
}

function attachEpisodeClickHandlers(container, slug, base) {
  container.querySelectorAll(".ep-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      container.querySelectorAll(".ep-btn").forEach(b => b.style.backgroundColor = "#252a35");
      btn.style.backgroundColor = "var(--primary)";
      const epNum = btn.dataset.ep;
      const infoBox = document.getElementById("modal-stream-info");
      if (!infoBox) return;

      infoBox.innerHTML = `
        <div style="font-size: 0.82rem; color: #9ba3af; display: flex; align-items: center; gap: 8px;">
          <div class="spinner show" style="width: 10px; height: 10px;"></div>
          <span>Decrypting direct stream for Episode ${epNum} from <code>${escapeHtml(base)}</code>...</span>
        </div>
      `;

      try {
        const streamRes = await fetch(`${base}/api/stream/${encodeURIComponent(slug)}/${epNum}`, {
          headers: { "Accept": "application/json" }
        });

        if (streamRes.ok) {
          const streamData = await streamRes.json();
          const streams = streamData.streams || [];
          const best = streams.find(s => s.stream_url) || streams[0];

          if (best && best.stream_url) {
            infoBox.innerHTML = `
              <div style="font-size: 0.82rem; color: #9ba3af; margin-bottom: 6px;">
                Episodio <strong>${epNum}</strong> | Server: <strong style="color: #fff;">${escapeHtml(best.server_name || "SaturnStream")}</strong>
              </div>
              <div style="font-family: var(--font-mono); font-size: 0.76rem; color: #64b5f6; word-break: break-all; margin-bottom: 8px; background: #0f1115; padding: 6px 8px; border-radius: 3px;">
                ${escapeHtml(best.stream_url)}
              </div>
              <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <a href="${best.stream_url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="padding: 5px 12px; font-size: 0.8rem;">
                  Play Direct Video (.mp4/.m3u8)
                </a>
                <a href="https://www.animesaturn.net/anime/${slug}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary" style="padding: 5px 12px; font-size: 0.8rem;">
                  Watch on Web
                </a>
              </div>
            `;
            return;
          }
        }
      } catch {}

      infoBox.innerHTML = `
        <div style="font-size: 0.82rem; color: #9ba3af; margin-bottom: 6px;">
          Episodio <strong>${epNum}</strong> | AnimeSaturn Web Fallback
        </div>
        <div style="font-size: 0.78rem; color: #e57373; margin-bottom: 8px;">
          Could not decrypt live stream directly (machine offline or waking up).
        </div>
        <div style="display: flex; gap: 8px;">
          <a href="https://www.animesaturn.net/anime/${slug}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="padding: 5px 12px; font-size: 0.8rem;">
            Watch Episode ${epNum} on AnimeSaturn
          </a>
        </div>
      `;
    });
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
