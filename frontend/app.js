// ─────────────────────────────────────────────
//  YojnaSearch — app.js
//  Plain JS, no framework, no build step.
// ─────────────────────────────────────────────

const API_URL = window.location.protocol === 'file:' 
  ? 'http://localhost:8000/api/search' 
  : '/api/search'

const form       = document.getElementById('searchForm')
const input      = document.getElementById('queryInput')
const languageSelect = document.getElementById('languageSelect')
const btn        = document.getElementById('searchBtn')
const btnText    = document.getElementById('btnText')
const spinner    = document.getElementById('spinner')
const resultsDiv = document.getElementById('results')

// ── Form submit ──────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault()
  const query = input.value.trim()
  if (!query) return
  await doSearch(query, languageSelect.value)
})

// Explicitly submit on Enter as well.  This keeps the search working in
// embedded browsers that do not promote an Enter keypress to a form submit.
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.isComposing) {
    e.preventDefault()
    form.requestSubmit()
  }
})

// ── Search ───────────────────────────────────
async function doSearch(query, language) {
  setLoading(true)
  resultsDiv.innerHTML = renderSkeletons()

  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, language }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Server error ${res.status}`)
    }

    const data = await res.json()
    renderResults(data)

  } catch (err) {
    resultsDiv.innerHTML = renderError(err.message)
  } finally {
    setLoading(false)
  }
}

// ── Loading state ────────────────────────────
function setLoading(on) {
  btn.disabled  = on
  spinner.classList.toggle('hidden', !on)
  btnText.textContent = on ? 'Searching…' : 'Search'
}

// ── Render results ───────────────────────────
function renderResults(data) {
  const schemes        = data?.results?.schemes ?? []
  const summary        = data?.results?.summary ?? ''
  const important_note = data?.results?.important_note ?? ''
  const parsed         = data?.parsed_query ?? {}
  const noMatch        = data?.no_match_reason

  let html = ''

  // Parsed query badges
  const badges = renderBadges(parsed)
  if (badges) html += `<div class="flex flex-wrap gap-2 items-center mb-4 animate-in">${badges}</div>`

  // Summary
  if (summary) {
    html += `
      <div class="bg-orange-50 border border-orange-200 rounded-2xl px-5 py-4 mb-5 animate-in">
        <p class="text-sm text-orange-900 font-medium leading-relaxed">${escHtml(summary)}</p>
      </div>`
  }

  // Scheme cards or empty state
  if (schemes.length > 0) {
    const accentColors = [
      'border-l-orange-400', 'border-l-blue-400',
      'border-l-emerald-400', 'border-l-purple-400', 'border-l-rose-400'
    ]
    const label = schemes.length === 1 ? '1 scheme found' : `${schemes.length} schemes found`
    html += `<p class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 animate-in">${label}</p>`
    schemes.forEach((scheme, i) => {
      html += renderCard(scheme, accentColors[i % accentColors.length])
    })
  } else {
    html += renderEmpty(noMatch, parsed)
  }

  // Important note
  if (important_note && schemes.length > 0) {
    html += `
      <div class="mt-6 text-xs text-slate-400 text-center animate-in">
        ℹ️ ${escHtml(important_note)}
      </div>`
  }

  resultsDiv.innerHTML = html
}

// ── Parsed query badges ──────────────────────
function renderBadges(parsed) {
  const defs = [
    parsed.state    && ['📍', parsed.state,                                     'bg-blue-100 text-blue-800'],
    parsed.category && ['🏷️', parsed.category,                                  'bg-purple-100 text-purple-800'],
    parsed.age      && ['🎂', `${parsed.age} yrs`,                              'bg-amber-100 text-amber-800'],
    parsed.gender   && ['👤', parsed.gender,                                     'bg-pink-100 text-pink-800'],
    parsed.income   && ['💰', `₹${(parsed.income / 100000).toFixed(1)} lakh`,   'bg-emerald-100 text-emerald-800'],
  ].filter(Boolean)

  if (!defs.length) return ''

  const chips = defs.map(([icon, label, cls]) =>
    `<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${cls}">
      ${icon} ${escHtml(label)}
    </span>`
  ).join('')

  return `<span class="text-xs text-slate-400 font-medium mr-1">Understood:</span>${chips}`
}

// ── Scheme card ──────────────────────────────
function renderCard(scheme, accent) {
  const listItems = (arr) =>
    (arr || []).map(item =>
      `<li class="flex gap-2 text-sm text-slate-600">
        <span class="text-orange-400 mt-0.5 flex-shrink-0">•</span>
        <span>${escHtml(item)}</span>
      </li>`
    ).join('')

  const section = (title, icon, items, open = false) => {
    if (!items || !items.length) return ''
    return `
      <details class="border-t border-slate-100 pt-3" ${open ? 'open' : ''}>
        <summary class="flex items-center justify-between text-sm font-semibold text-slate-700
                        hover:text-orange-500 transition-colors select-none py-0.5">
          <span>${icon} ${title}</span>
          <svg class="chevron w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
          </svg>
        </summary>
        <ul class="mt-2 space-y-1 pl-2">${listItems(items)}</ul>
      </details>`
  }

  const applyBtn = scheme.apply_url
    ? `<a href="${escHtml(scheme.apply_url)}" target="_blank" rel="noopener"
          class="px-4 py-2 rounded-full bg-saffron-500 text-white text-xs font-semibold
                 hover:bg-saffron-600 transition-colors">
         Apply Now ↗
       </a>`
    : ''

  const officialBtn = scheme.official_url
    ? `<a href="${escHtml(scheme.official_url)}" target="_blank" rel="noopener"
          class="px-4 py-2 rounded-full border border-slate-300 text-slate-700 text-xs font-medium
                 hover:border-orange-400 hover:text-orange-600 transition-colors">
         Official Page ↗
       </a>`
    : ''

  const links = (applyBtn || officialBtn)
    ? `<div class="flex flex-wrap gap-2 border-t border-slate-100 pt-4 mt-2">${applyBtn}${officialBtn}</div>`
    : ''

  return `
    <article class="bg-white rounded-2xl border border-slate-200 border-l-4 ${accent}
                    shadow-sm hover:shadow-md transition-shadow mb-4 overflow-hidden animate-in">
      <!-- Header -->
      <div class="px-5 pt-5 pb-4">
        <h3 class="text-base font-bold text-slate-900 leading-snug">${escHtml(scheme.scheme_name || 'Unnamed Scheme')}</h3>
        <div class="flex flex-wrap gap-1.5 mt-2">
          ${scheme.state    ? `<span class="badge bg-blue-100 text-blue-800">📍 ${escHtml(scheme.state)}</span>` : ''}
          ${scheme.category ? `<span class="badge bg-purple-100 text-purple-800">🏷️ ${escHtml(scheme.category)}</span>` : ''}
        </div>
        ${scheme.relevance ? `<p class="mt-3 text-sm text-slate-500 italic leading-relaxed">${escHtml(scheme.relevance)}</p>` : ''}
      </div>

      <!-- Collapsible sections -->
      <div class="px-5 pb-4 space-y-0">
        ${section('Benefits',            '🎁', scheme.benefits,            true)}
        ${section('Eligibility',         '✅', scheme.eligibility,         false)}
        ${section('How to Apply',        '📋', scheme.application_process, false)}
        ${section('Documents Required',  '📄', scheme.documents_required,  false)}
      </div>

      <!-- Links -->
      ${links ? `<div class="px-5 pb-5">${links}</div>` : ''}
    </article>`
}

// ── Empty state ──────────────────────────────
function renderEmpty(reason, parsed) {
  const headlines = {
    parser_miss: 'Category not matched in our database',
    no_results:  'No schemes found for this query',
  }
  const headline = headlines[reason] || 'No matching schemes found'

  const tips = [
    !parsed?.state    && '📍 Add your state — e.g. "from Maharashtra"',
    !parsed?.category && '🏥 Describe your need — e.g. "health", "scholarship", "housing"',
    !parsed?.age      && '🎂 Mention your age — e.g. "I am 30 years old"',
    !parsed?.income   && '💰 State your income — e.g. "earning under ₹3 lakh"',
    !parsed?.gender   && '👤 Add gender if relevant — e.g. "female", "male"',
  ].filter(Boolean)

  const tipItems = tips.map(t => `<li class="text-sm text-slate-600">${t}</li>`).join('')

  return `
    <div class="text-center py-12 animate-in">
      <div class="text-5xl mb-4">🔍</div>
      <h3 class="text-lg font-bold text-slate-800 mb-1">${escHtml(headline)}</h3>
      <p class="text-slate-500 text-sm mb-8">Try adding more details about yourself.</p>
      ${tipItems ? `
        <div class="bg-white border border-slate-200 rounded-2xl p-5 max-w-sm mx-auto text-left">
          <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">💡 Tips</p>
          <ul class="space-y-2">${tipItems}</ul>
        </div>` : ''}
    </div>`
}

// ── Skeletons ────────────────────────────────
function renderSkeletons() {
  const card = `
    <div class="bg-white rounded-2xl border border-slate-200 border-l-4 border-l-slate-200 p-5 mb-4 skeleton">
      <div class="h-4 bg-slate-200 rounded w-3/4 mb-3"></div>
      <div class="flex gap-2 mb-4">
        <div class="h-3 bg-slate-200 rounded-full w-20"></div>
        <div class="h-3 bg-slate-200 rounded-full w-28"></div>
      </div>
      <div class="h-3 bg-slate-200 rounded w-full mb-2"></div>
      <div class="h-3 bg-slate-200 rounded w-5/6 mb-2"></div>
      <div class="h-3 bg-slate-200 rounded w-4/6"></div>
    </div>`
  return card + card + card
}

// ── Error ────────────────────────────────────
function renderError(msg) {
  return `
    <div class="bg-red-50 border border-red-200 rounded-2xl p-8 text-center animate-in">
      <div class="text-4xl mb-3">⚠️</div>
      <p class="text-red-700 font-semibold">${escHtml(msg)}</p>
      <p class="text-red-400 text-sm mt-1">Check your connection or try again.</p>
    </div>`
}

// ── Utility: escape HTML ─────────────────────
function escHtml(str) {
  if (!str) return ''
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

// ── Inline badge style (Tailwind purge workaround) ──
document.head.insertAdjacentHTML('beforeend', `
  <style>
    .badge {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 2px 10px; border-radius: 9999px;
      font-size: .75rem; font-weight: 500; white-space: nowrap;
    }
  </style>
`)
