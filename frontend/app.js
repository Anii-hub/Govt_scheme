/* ===================================================
   DOM Helpers
=================================================== */
const $ = (id) => document.getElementById(id);

function show(id) {
  $(id).classList.add("visible");
}
function hide(id) {
  $(id).classList.remove("visible");
}
function clear(id) {
  $(id).innerHTML = "";
}

function setQuery(btn) {
  $("queryInput").value = btn.textContent.trim();
  $("queryInput").focus();
}

function esc(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ===================================================
   Reset UI
=================================================== */
function resetUI() {
  hide("statusBar");
  hide("errorBox");
  hide("parsedInfo");
  hide("summaryCard");
  hide("emptyState");
  hide("importantNote");
  clear("results");
  clear("parsedInfo");
  clear("errorBox");
  $("summaryText").textContent = "";
  $("noteText").textContent = "";
}

/* ===================================================
   Search Action
=================================================== */
async function runSearch() {
  const query = $("queryInput").value.trim();
  if (!query) {
    $("queryInput").focus();
    return;
  }

  resetUI();

  const btn = $("searchBtn");
  btn.disabled = true;
  $("statusText").textContent = "Searching government schemes & generating AI response...";
  show("statusBar");

  try {
    const res = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || `HTTP ${res.status}`);
    }

    hide("statusBar");
    renderResults(data);
  } catch (err) {
    hide("statusBar");
    $("errorBox").textContent = "⚠️ " + (err.message || "An unexpected error occurred while connecting to the API.");
    show("errorBox");
  } finally {
    btn.disabled = false;
  }
}

/* ===================================================
   Render Results
=================================================== */
function renderResults(data) {
  // Parsed metadata pills
  const { state, category } = data.parsed_query || {};
  if (state || category) {
    let html = "";
    if (state) {
      html += `<span class="pill">📍 State: <strong>${esc(state)}</strong></span>`;
    }
    if (category) {
      html += `<span class="pill">🏷️ Category: <strong>${esc(category)}</strong></span>`;
    }
    $("parsedInfo").innerHTML = html;
    show("parsedInfo");
  }

  const answer = data.results || {};

  // Summary
  if (answer.summary) {
    $("summaryText").textContent = answer.summary;
    show("summaryCard");
  }

  // Schemes list
  const schemes = answer.schemes || [];
  if (schemes.length === 0) {
    show("emptyState");
  } else {
    const container = $("results");
    schemes.forEach((scheme, i) => {
      container.appendChild(buildSchemeCard(scheme, i));
    });
  }

  // Important disclaimer note
  if (answer.important_note) {
    $("noteText").textContent = answer.important_note;
    show("importantNote");
  }
}

function buildSchemeCard(scheme, index) {
  const card = document.createElement("div");
  card.className = "scheme-card";
  card.style.animationDelay = `${index * 80}ms`;

  const isCentral = !scheme.state || scheme.state.toLowerCase() === "central" || scheme.state.toLowerCase() === "all india";
  const stateBadgeClass = isCentral ? "badge-state badge-central" : "badge-state";
  const stateLabel = isCentral ? "🇮🇳 Central Scheme" : `📍 ${scheme.state}`;

  let linksHtml = "";
  if (scheme.official_url) {
    linksHtml += `<a class="btn-link official" href="${esc(scheme.official_url)}" target="_blank" rel="noopener noreferrer">
      🔗 Official Portal
    </a>`;
  }
  if (scheme.apply_url) {
    linksHtml += `<a class="btn-link apply" href="${esc(scheme.apply_url)}" target="_blank" rel="noopener noreferrer">
      ✅ Apply Online
    </a>`;
  }

  card.innerHTML = `
    <div class="card-header">
      <h2>${esc(scheme.scheme_name || "Scheme")}</h2>
      <span class="${stateBadgeClass}">${stateLabel}</span>
    </div>
    <div class="card-body">
      ${scheme.category ? `<div class="card-category">${esc(scheme.category)}</div>` : ""}
      ${scheme.relevance ? `<div class="relevance">${esc(scheme.relevance)}</div>` : ""}

      ${listSection("Benefits", scheme.benefits)}
      ${listSection("Eligibility Criteria", scheme.eligibility)}
      ${listSection("Application Process", scheme.application_process)}
      ${listSection("Documents Required", scheme.documents_required)}

      ${linksHtml ? `<div class="card-links">${linksHtml}</div>` : ""}
    </div>
  `;
  return card;
}

function listSection(title, items) {
  if (!items || items.length === 0) return "";
  const lis = items.map((item) => `<li>${esc(item)}</li>`).join("");
  return `
    <div class="section-title">${title}</div>
    <ul class="detail-list">${lis}</ul>
  `;
}

/* ===================================================
   Keyboard Listeners
=================================================== */
$("queryInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSearch();
});
