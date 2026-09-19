/**
 * AnimeSaturn Web App & Live API Explorer
 * 
 * Powered by pure JavaScript. Connects directly to the live AnimeSaturn API
 * endpoints on the pages to fetch real-time anime metadata, search results,
 * episode details, and direct streaming links.
 */

document.addEventListener("DOMContentLoaded", () => {
  initClipboard();
  initConsoleTabs();
  initPlayground();
  initExplorer();
  initModal();
});

/* ==========================================================================
   1. Clipboard / Copy Button Utilities
   ========================================================================== */

function initClipboard() {
  const copyInstallBtn = document.getElementById("btn-copy-install");
  const copyTooltip = document.getElementById("copy-tooltip");
  const installCmd = document.getElementById("install-command");

  if (copyInstallBtn && installCmd) {
    copyInstallBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(installCmd.innerText.trim()).then(() => {
        copyTooltip.classList.add("show");
        setTimeout(() => copyTooltip.classList.remove("show"), 2000);
      });
    });
  }

  const copyOutputBtn = document.getElementById("btn-copy-output");
  if (copyOutputBtn) {
    copyOutputBtn.addEventListener("click", () => {
      const activeTab = document.querySelector(".code-view.active");
      if (activeTab) {
        navigator.clipboard.writeText(activeTab.innerText).then(() => {
          const originalText = copyOutputBtn.querySelector("span").textContent;
          copyOutputBtn.querySelector("span").textContent = "Copied!";
          setTimeout(() => {
            copyOutputBtn.querySelector("span").textContent = originalText;
          }, 1800);
        });
      }
    });
  }
}

/* ==========================================================================
   2. Console View Tabs (JSON vs Python)
   ========================================================================== */

function initConsoleTabs() {
  const tabBtnJson = document.getElementById("tab-btn-json");
  const tabBtnCode = document.getElementById("tab-btn-code");
  const jsonView = document.getElementById("json-view");
  const codeView = document.getElementById("code-view");

  if (tabBtnJson && tabBtnCode) {
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
}

/* ==========================================================================
   3. Live API Playground Engine
   ========================================================================== */

function initPlayground() {
  const urlInput = document.getElementById("api-url-input");
  const runBtn = document.getElementById("btn-run-query");
  const spinner = document.getElementById("query-spinner");
  const btnText = runBtn ? runBtn.querySelector(".btn-run-text") : null;
  const jsonCodeContent = document.getElementById("json-code-content");
  const pythonCodeContent = document.getElementById("python-code-content");
  const statusBadge = document.getElementById("status-badge");
  const responseTimeBadge = document.getElementById("response-time-badge");
  const presets = document.querySelectorAll(".preset-btn");

  // Preset Button Clicks
  presets.forEach(btn => {
    btn.addEventListener("click", () => {
      presets.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const type = btn.dataset.type;
      const query = btn.dataset.query;

      if (type === "search") {
        urlInput.value = `/api/search?q=${encodeURIComponent(query)}`;
      } else if (type === "latest") {
        urlInput.value = `/api/latest`;
      } else if (type === "mirrors") {
        urlInput.value = `/api/domains`;
      }
      runQuery();
    });
  });

  // Run Query Execution
  async function runQuery() {
    if (!urlInput) return;
    const rawUrl = urlInput.value.trim();
    if (!rawUrl) return;

    if (spinner) spinner.classList.add("show");
    if (btnText) btnText.textContent = "Fetching...";
    if (runBtn) runBtn.disabled = true;

    const startTime = performance.now();

    try {
      // Normalise URL: if relative /api/..., resolve against current origin
      let requestUrl = rawUrl;
      if (rawUrl.startsWith("/")) {
        requestUrl = window.location.origin + rawUrl;
      }

      const res = await fetch(requestUrl, {
        headers: { "Accept": "application/json" }
      });

      const elapsed = Math.round(performance.now() - startTime);
      if (responseTimeBadge) responseTimeBadge.textContent = `${elapsed}ms`;

      if (statusBadge) {
        statusBadge.textContent = `${res.status} ${res.statusText || (res.ok ? "OK" : "Error")}`;
        statusBadge.className = `status-indicator ${res.ok ? "status-ok" : "status-err"}`;
      }

      const data = await res.json();

      // Render JSON with syntax highlighting
      if (jsonCodeContent) {
        jsonCodeContent.innerHTML = syntaxHighlightJson(data);
      }

      // Generate corresponding Python Code snippet
      if (pythonCodeContent) {
        pythonCodeContent.textContent = generatePythonSnippet(rawUrl, data);
      }

    } catch (err) {
      const elapsed = Math.round(performance.now() - startTime);
      if (responseTimeBadge) responseTimeBadge.textContent = `${elapsed}ms`;
      if (statusBadge) {
        statusBadge.textContent = "Error";
        statusBadge.className = "status-indicator status-err";
      }
      if (jsonCodeContent) {
        jsonCodeContent.innerHTML = syntaxHighlightJson({
          ok: false,
          error: `Network request failed: ${err.message}`,
          note: "Ensure the live edge function or API backend is active."
        });
      }
    } finally {
      if (spinner) spinner.classList.remove("show");
      if (btnText) btnText.textContent = "Run Query";
      if (runBtn) runBtn.disabled = false;
    }
  }

  if (runBtn) {
    runBtn.addEventListener("click", runQuery);
  }

  if (urlInput) {
    urlInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") runQuery();
    });
  }

  // Initial Run on load with first preset
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

function generatePythonSnippet(url, data) {
  if (url.includes("/api/search")) {
    const qMatch = url.match(/[?&]q=([^&]+)/);
    const query = qMatch ? decodeURIComponent(qMatch[1]) : "Solo Leveling";
    return `import animesaturn\n\n# Search anime live on AnimeSaturn\nresults = animesaturn.find("${query}")\nfor anime in results:\n    print(f"{anime['name']} | Episodes: {anime['episodes']} | {anime['url']}")`;
  }
  if (url.includes("/api/anime/")) {
    const slug = url.split("/api/anime/")[1].split("?")[0];
    return `import animesaturn\n\n# Retrieve anime metadata & episode list\nanime = animesaturn.Anime("${slug}")\nprint("Title:", anime.name)\nprint("Episodes count:", len(anime.episodes))\nprint("First episode:", anime[1].url)`;
  }
  if (url.includes("/api/stream/")) {
    const parts = url.split("/api/stream/")[1].split("/");
    const slug = parts[0];
    const ep = parts[1] || "1";
    return `import animesaturn\n\n# Decrypt direct video streaming link\nanime = animesaturn.Anime("${slug}")\nep = anime[${ep}]\nservers = ep.getServer()\nfor server in servers:\n    print(server.name, server.fileLink())`;
  }
  if (url.includes("/api/latest")) {
    return `import animesaturn\n\n# Fetch latest episodes released on homepage\nlatest = animesaturn.latest_episodes(page=1)\nfor ep in latest.get("items", []):\n    print(f"{ep['title']} - Ep. {ep['episodeLabel']}")`;
  }
  if (url.includes("/api/domains")) {
    return `import animesaturn\n\n# Discover official active mirrors\nmirrors = animesaturn.fetch_official_domains()\nactive = animesaturn.discover_active_domain()\nprint("Active domain:", active)\nprint("All mirrors:", mirrors)`;
  }
  return `import animesaturn\n\n# Query AnimeSaturn API\nresults = animesaturn.find("Solo Leveling")\nprint(results)`;
}

/* ==========================================================================
   4. Visual Anime Explorer
   ========================================================================== */

let catalogData = [];

async function initExplorer() {
  const grid = document.getElementById("anime-cards-grid");
  const searchInput = document.getElementById("explorer-search-input");
  const filterPills = document.querySelectorAll(".filter-pill");

  if (!grid) return;

  grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-dim); padding: 40px;">Loading catalog live...</div>`;

  // Fetch initial anime collection from live API
  try {
    const searchRes = await fetch("/api/search?q=Solo+Leveling");
    if (searchRes.ok) {
      const data = await searchRes.json();
      if (data.results && data.results.length > 0) {
        catalogData = data.results;
      }
    }
  } catch (e) {
    // If local dev or offline, provide seed catalog
    catalogData = [];
  }

  // If search was empty or fewer than 4 items, supplement with popular titles
  if (catalogData.length < 4) {
    const initialTitles = ["Solo Leveling", "Naruto", "Bleach", "One Piece", "Jujutsu Kaisen", "Demon Slayer"];
    for (const t of initialTitles) {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(t)}`);
        if (res.ok) {
          const d = await res.json();
          if (d.results && d.results.length > 0) {
            const first = d.results[0];
            if (!catalogData.find(x => x.link === first.link)) {
              catalogData.push(first);
            }
          }
        }
      } catch (err) {
        break;
      }
    }
  }

  renderCards(catalogData);

  // Search input filter
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(async () => {
        const query = e.target.value.trim();
        if (query.length >= 2) {
          grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-dim); padding: 40px;">Searching '${query}'...</div>`;
          try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            if (res.ok) {
              const data = await res.json();
              renderCards(data.results || []);
              return;
            }
          } catch (err) {
            // Local filter fallback
          }
        }
        
        // Filter existing catalog
        const filtered = catalogData.filter(item =>
          item.title.toLowerCase().includes(query.toLowerCase())
        );
        renderCards(filtered);
      }, 350);
    });
  }

  // Category filter pills
  filterPills.forEach(pill => {
    pill.addEventListener("click", () => {
      filterPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      const filter = pill.dataset.filter;

      if (filter === "all") {
        renderCards(catalogData);
      } else {
        const filtered = catalogData.filter(item => item.type === filter);
        renderCards(filtered);
      }
    });
  });
}

function renderCards(items) {
  const grid = document.getElementById("anime-cards-grid");
  if (!grid) return;

  if (!items || items.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-dim); padding: 40px;">No anime found matching query.</div>`;
    return;
  }

  grid.innerHTML = items.map(anime => {
    const poster = anime.poster || anime.locandina || "static/img/logo.png";
    const genres = Array.isArray(anime.genres) ? anime.genres.slice(0, 3).join(", ") : "";
    const cleanSlug = (anime.link || "").replace(/^\/anime\//, "");

    return `
      <div class="anime-card" data-slug="${cleanSlug}" data-title="${escapeHtml(anime.title)}">
        <div class="card-poster-wrapper">
          <img class="card-poster" src="${poster}" alt="${escapeHtml(anime.title)}" loading="lazy">
          ${anime.episodes ? `<span class="card-badge-ep">${anime.episodes} Eps</span>` : ""}
          <span class="card-badge-type">${anime.type || "TV"}</span>
        </div>
        <div class="card-info">
          <h3 class="card-title">${escapeHtml(anime.title)}</h3>
          ${genres ? `<div class="card-genres">${escapeHtml(genres)}</div>` : ""}
          <div class="card-meta">
            <span>${anime.year || "AnimeSaturn"}</span>
            <span style="color: var(--accent-secondary);">Inspect &rarr;</span>
          </div>
        </div>
      </div>
    `;
  }).join("");

  // Attach card click handlers
  document.querySelectorAll(".anime-card").forEach(card => {
    card.addEventListener("click", () => {
      const slug = card.dataset.slug;
      openAnimeModal(slug, card.dataset.title);
    });
  });
}

/* ==========================================================================
   5. Anime Details & Stream Inspector Modal
   ========================================================================== */

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

async function openAnimeModal(slug, fallbackTitle) {
  const backdrop = document.getElementById("modal-backdrop");
  const container = document.getElementById("modal-content-container");
  if (!backdrop || !container) return;

  container.innerHTML = `
    <div style="grid-column: 1/-1; text-align: center; padding: 60px;">
      <div class="spinner show" style="margin: 0 auto 16px; width: 28px; height: 28px;"></div>
      <div style="color: var(--text-muted);">Fetching live anime details and episode stream links...</div>
    </div>
  `;
  backdrop.classList.add("open");

  try {
    const res = await fetch(`/api/anime/${slug}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const poster = data.poster || data.locandina || "static/img/logo.png";
    const title = data.title || fallbackTitle;
    const episodes = data.episodes || [];
    const story = data.story || "No synopsis available for this title.";

    container.innerHTML = `
      <div>
        <img class="modal-poster" src="${poster}" alt="${escapeHtml(title)}">
      </div>
      <div>
        <h2 class="modal-title">${escapeHtml(title)}</h2>
        ${data.jtitle ? `<div class="modal-jtitle">${escapeHtml(data.jtitle)}</div>` : ""}
        
        <div class="modal-pills">
          <span class="modal-pill">${data.episodes_count || episodes.length} Episodes</span>
          ${data.category ? `<span class="modal-pill">${data.category}</span>` : ""}
          ${data.status ? `<span class="modal-pill">${data.status}</span>` : ""}
          ${data.studio ? `<span class="modal-pill">${data.studio}</span>` : ""}
        </div>

        <p class="modal-synopsis">${escapeHtml(story)}</p>

        <div class="modal-section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          <span>Select Episode to Inspect Stream:</span>
        </div>

        <div class="episode-picker-grid" id="ep-picker-grid">
          ${episodes.slice(0, 50).map(ep => `
            <button class="ep-btn" data-slug="${slug}" data-ep="${ep.number}">
              Ep. ${ep.number}
            </button>
          `).join("")}
        </div>

        <div id="ep-stream-result" style="margin-top: 16px;"></div>

        <div class="stream-actions" style="margin-top: 24px;">
          <a href="${data.url || '#'}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary">
            <span>Open on AnimeSaturn</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14 21 3"/></svg>
          </a>
        </div>
      </div>
    `;

    // Attach click handlers to episode buttons
    container.querySelectorAll(".ep-btn").forEach(epBtn => {
      epBtn.addEventListener("click", () => {
        container.querySelectorAll(".ep-btn").forEach(b => b.style.borderColor = "var(--border-subtle)");
        epBtn.style.borderColor = "var(--accent-primary)";
        inspectEpisodeStream(epBtn.dataset.slug, epBtn.dataset.ep);
      });
    });

    // Auto-select first episode
    const firstEpBtn = container.querySelector(".ep-btn");
    if (firstEpBtn) firstEpBtn.click();

  } catch (err) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--status-err);">
        <h3>Failed to load anime details</h3>
        <p style="color: var(--text-muted); margin-top: 8px;">${err.message}</p>
      </div>
    `;
  }
}

async function inspectEpisodeStream(slug, epNumber) {
  const resultContainer = document.getElementById("ep-stream-result");
  if (!resultContainer) return;

  resultContainer.innerHTML = `
    <div style="font-size: 0.84rem; color: var(--text-dim); display: flex; align-items: center; gap: 8px;">
      <div class="spinner show" style="width: 12px; height: 12px;"></div>
      <span>Decrypting video stream for Episode ${epNumber}...</span>
    </div>
  `;

  try {
    const res = await fetch(`/api/stream/${slug}/${epNumber}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const streams = data.streams || [];

    if (streams.length === 0) {
      resultContainer.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-muted);">No video streams found for Episode ${epNumber}.</div>`;
      return;
    }

    resultContainer.innerHTML = `
      <div style="background: rgba(10, 15, 29, 0.8); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 12px;">
        <div style="font-size: 0.8rem; font-weight: 700; color: var(--accent-secondary); margin-bottom: 8px;">
          Available Video Streams (Episode ${epNumber}):
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${streams.map(s => `
            <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.84rem; background: rgba(255,255,255,0.03); padding: 6px 10px; border-radius: 6px;">
              <div>
                <span style="font-weight: 600; color: #fff;">${escapeHtml(s.name)}</span>
                ${s.is_hls ? `<span style="font-size: 0.72rem; color: #34d399; margin-left: 6px;">[HLS .m3u8]</span>` : ""}
              </div>
              <div style="display: flex; gap: 8px;">
                ${s.direct_stream_url ? `
                  <a href="${s.direct_stream_url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="padding: 4px 10px; font-size: 0.76rem;">
                    Play Stream
                  </a>
                ` : ""}
                ${s.embed_url ? `
                  <a href="${s.embed_url}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.76rem;">
                    Player
                  </a>
                ` : ""}
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  } catch (err) {
    resultContainer.innerHTML = `
      <div style="font-size: 0.82rem; color: var(--status-warn);">
        Stream decryption preview: episode stream is available via CLI or python library: <code>animesaturn ep "${slug}" ${epNumber}</code>
      </div>
    `;
  }
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
