function $(id) {
  return document.getElementById(id)
}

async function apiFetch(url, options) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options && options.headers ? options.headers : {}) },
    credentials: 'same-origin',
    ...options
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const msg = data && data.error && data.error.message ? data.error.message : 'La requête a échoué'
    throw new Error(msg)
  }
  return data
}

function toast(title, message, variant) {
  const root = $('toastRoot')
  if (!root) return

  const t = document.createElement('div')
  t.className = 'toast'

  const dot = document.createElement('div')
  dot.className = 'toast-dot' + (variant ? ' ' + variant : '')

  const body = document.createElement('div')
  const h = document.createElement('div')
  h.className = 'toast-title'
  h.textContent = title
  const p = document.createElement('div')
  p.className = 'toast-msg'
  p.textContent = message

  body.appendChild(h)
  body.appendChild(p)
  t.appendChild(dot)
  t.appendChild(body)
  root.appendChild(t)

  setTimeout(() => {
    t.style.opacity = '0'
    t.style.transform = 'translateY(6px)'
    t.style.transition = 'opacity 220ms ease, transform 220ms ease'
  }, 3200)
  setTimeout(() => t.remove(), 3600)
}

function flashToToasts() {
  const flashes = window.__FLASHES__ || []
  flashes.forEach(([cat, msg]) => {
    const variant = cat === 'success' ? 'success' : cat === 'warning' ? 'warning' : cat === 'danger' ? 'danger' : ''
    toast('Notification', msg, variant)
  })
}

function initTheme() {
  const stored = localStorage.getItem('devscope-theme')
  const theme = stored || document.documentElement.getAttribute('data-theme') || 'dark'
  document.documentElement.setAttribute('data-theme', theme)
  // Theme toggle control moved into profile menu (id: profileThemeToggle)
}

function initProfileMenu() {
  const btn = $('profileMenuBtn')
  const menu = $('profileMenu')
  const themeBtn = $('profileThemeToggle')
  if (!btn || !menu) return

  function closeMenu() { menu.classList.remove('show'); menu.setAttribute('aria-hidden', 'true'); btn.setAttribute('aria-expanded', 'false') }
  function openMenu() { menu.classList.add('show'); menu.setAttribute('aria-hidden', 'false'); btn.setAttribute('aria-expanded', 'true') }

  btn.addEventListener('click', (e) => {
    e.stopPropagation()
    if (menu.classList.contains('show')) closeMenu(); else openMenu()
  })

  document.addEventListener('click', (e) => {
    if (!menu.contains(e.target) && e.target !== btn) closeMenu()
  })

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark'
      const next = current === 'dark' ? 'light' : 'dark'
      document.documentElement.setAttribute('data-theme', next)
      localStorage.setItem('devscope-theme', next)
    })
  }
}

function initEtlControls() {
  const toggle = $('toggleEtlAdvanced')
  const advanced = $('etlAdvanced')
  const summary = $('etlQuerySummary')
  const q = $('etlQuery')
  const limit = $('etlLimit')
  if (!toggle || !advanced || !summary || !q || !limit) return

  function updateSummary() {
    const query = (q.value || '').trim()
    const l = String(limit.value || '25')
    summary.textContent = (query ? query : 'Aucune requête') + ' · limite ' + l
  }

  toggle.addEventListener('click', () => {
    const isHidden = advanced.hasAttribute('hidden')
    if (isHidden) {
      advanced.removeAttribute('hidden')
      toggle.setAttribute('aria-expanded', 'true')
      toggle.textContent = 'Avancé ▴'
    } else {
      advanced.setAttribute('hidden', '')
      toggle.setAttribute('aria-expanded', 'false')
      toggle.textContent = 'Avancé ▾'
    }
  })

  q.addEventListener('input', updateSummary)
  limit.addEventListener('input', updateSummary)
  updateSummary()
}

function initSidebar() {
  const btn = $('sidebarToggle')
  if (!btn) return
  btn.addEventListener('click', () => {
    document.body.classList.toggle('sidebar-open')
  })
}

function initGlobalSearch() {
  const form = $('globalSearchForm')
  const input = $('globalSearchInput')
  if (!form || !input) return
  form.addEventListener('submit', (e) => {
    e.preventDefault()
    const q = (input.value || '').trim()
    const params = new URLSearchParams()
    if (q) params.set('q', q)
    window.location.href = '/search' + (params.toString() ? '?' + params.toString() : '')
  })
}

function activityBadge(level) {
  if (level === 'high') return 'badge good'
  if (level === 'medium') return 'badge warn'
  return 'badge bad'
}

function activityLabel(level) {
  if (level === 'high') return 'élevée'
  if (level === 'medium') return 'moyenne'
  if (level === 'low') return 'faible'
  return safeText(level)
}

function safeText(x) {
  return x === null || x === undefined || x === '' ? '—' : String(x)
}

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString()
}

function plotChart(id, figure) {
  if (!figure || !window.Plotly) return
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  const theme = getComputedStyle(document.documentElement)
  const cssColor = (name, fallback) => (theme.getPropertyValue(name) || fallback).trim()
  const textColor = cssColor('--text', isDark ? '#e7ebef' : '#242832')
  const mutedColor = cssColor('--muted', isDark ? '#a7b0ba' : '#68707d')
  const gridColor = cssColor('--border', isDark ? '#303841' : '#dde2e8')
  const primary = cssColor('--primary', isDark ? '#8fb4da' : '#476a8f')
  const secondary = cssColor('--secondary', isDark ? '#9aa98f' : '#5f6f64')
  const accent = cssColor('--accent', isDark ? '#d1b06a' : '#9a6a20')
  const danger = cssColor('--danger', isDark ? '#e18484' : '#a14141')
  const success = cssColor('--success', isDark ? '#8fbd9c' : '#4b765e')
  const warning = cssColor('--warning', isDark ? '#d5a956' : '#9a6a20')
  const layout = {
    ...(figure.layout || {}),
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, Arial, sans-serif', color: textColor, size: 12 },
    margin: { l: 42, r: 20, t: 34, b: 42, ...((figure.layout || {}).margin || {}) },
    colorway: [primary, secondary, accent, success, warning, danger, '#64748b'],
    xaxis: { gridcolor: gridColor, zerolinecolor: gridColor, tickfont: { color: mutedColor }, ...((figure.layout || {}).xaxis || {}) },
    yaxis: { gridcolor: gridColor, zerolinecolor: gridColor, tickfont: { color: mutedColor }, ...((figure.layout || {}).yaxis || {}) },
    legend: { orientation: 'h', y: -0.18, x: 0, font: { color: mutedColor }, ...((figure.layout || {}).legend || {}) }
  }
  Plotly.newPlot(id, figure.data, layout, { displayModeBar: false, responsive: true })
}

function animateNumber(el, value) {
  if (!el) return
  const target = Number(value || 0)
  const start = Number(el.getAttribute('data-num') || 0)
  const diff = target - start
  const startTime = performance.now()
  const duration = 600

  function tick(now) {
    const t = Math.min(1, (now - startTime) / duration)
    const current = Math.round(start + diff * (1 - Math.pow(1 - t, 3)))
    el.textContent = String(current)
    if (t < 1) requestAnimationFrame(tick)
    else el.setAttribute('data-num', String(target))
  }

  requestAnimationFrame(tick)
}

function setProgress(el, pct) {
  if (!el) return
  const p = Math.max(0, Math.min(100, Number(pct || 0)))
  el.style.width = p + '%'
}

function avatarHtml(url, name) {
  const safe = (name || 'U').trim()
  const letter = safe ? safe[0].toUpperCase() : 'U'
  if (!url) return `<div class="avatar-fallback">${letter}</div>`
  return `<img class="avatar" src="${url}" alt="${safe}" loading="lazy" />`
}

function skillNames(skills) {
  return (skills || []).map((s) => typeof s === 'string' ? s : s.name).filter(Boolean)
}

function renderSkillPills(skills, maxItems) {
  const names = skillNames(skills).slice(0, maxItems || 6)
  if (!names.length) return '<span class="muted small">Aucune competence.</span>'
  return names.map((name) => `<span class="skill-pill">${safeText(name)}</span>`).join('')
}

function openProfileModal(title, body, actions) {
  const old = $('profileModalOverlay')
  if (old) old.remove()
  const overlay = document.createElement('div')
  overlay.className = 'modal-overlay'
  overlay.id = 'profileModalOverlay'
  const modal = document.createElement('div')
  modal.className = 'modal-panel'
  const head = document.createElement('div')
  head.className = 'modal-head'
  const h = document.createElement('div')
  h.className = 'card-title'
  h.textContent = title
  const close = document.createElement('button')
  close.type = 'button'
  close.className = 'btn btn-ghost'
  close.textContent = 'Fermer'
  close.addEventListener('click', () => overlay.remove())
  head.appendChild(h)
  head.appendChild(close)
  const content = document.createElement('div')
  content.className = 'modal-body'
  if (typeof body === 'string') content.innerHTML = body
  else content.appendChild(body)
  const footer = document.createElement('div')
  footer.className = 'modal-actions'
  ;(actions || []).forEach((action) => footer.appendChild(action))
  modal.appendChild(head)
  modal.appendChild(content)
  modal.appendChild(footer)
  overlay.appendChild(modal)
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.remove()
  })
  document.body.appendChild(overlay)
  return overlay
}

function initGithubLiveSearch() {
  const input = $('githubSearchInput')
  const limit = $('githubLimit')
  const btn = $('githubSearchBtn')
  const grid = $('githubResultsGrid')
  const meta = $('githubSearchMeta')
  if (!input || !limit || !btn || !grid || !meta) return

  function renderEmpty(message) {
    grid.innerHTML = ''
    const empty = document.createElement('div')
    empty.className = 'empty'
    empty.textContent = message
    grid.appendChild(empty)
  }

  function setLoading(isLoading) {
    btn.disabled = isLoading
    btn.textContent = isLoading ? 'Recherche...' : 'Rechercher sur GitHub'
  }

  function renderProfiles(items) {
    grid.innerHTML = ''
    if (!items.length) {
      renderEmpty('Aucun utilisateur GitHub trouvé.')
      return
    }

    items.forEach((profile) => {
      const card = document.createElement('div')
      card.className = 'github-card'

      const head = document.createElement('div')
      head.className = 'github-card-head'

      const avatar = document.createElement('div')
      avatar.className = 'github-avatar'
      avatar.innerHTML = avatarHtml(profile.avatar_url, profile.username)

      const identity = document.createElement('div')
      const name = document.createElement('a')
      name.className = 'list-title'
      name.href = profile.profile_url || '#'
      name.target = '_blank'
      name.rel = 'noreferrer'
      name.textContent = profile.username
      const sub = document.createElement('div')
      sub.className = 'list-sub'
      sub.textContent = profile.name || 'Utilisateur GitHub'
      identity.appendChild(name)
      identity.appendChild(sub)

      head.appendChild(avatar)
      head.appendChild(identity)

      const bio = document.createElement('div')
      bio.className = 'github-bio'
      bio.textContent = profile.bio || 'Aucune bio disponible.'

      const stats = document.createElement('div')
      stats.className = 'github-stats'
      const followers = document.createElement('span')
      followers.textContent = `${profile.followers} followers`
      const repos = document.createElement('span')
      repos.textContent = `${profile.repositories_count} dépôts`
      stats.appendChild(followers)
      stats.appendChild(repos)
      const status = document.createElement('span')
      status.className = profile.exists_in_database ? 'status success' : 'status running'
      status.textContent = profile.status || (profile.exists_in_database ? 'Déjà enregistré' : 'Nouveau profil GitHub')
      stats.appendChild(status)

      const actions = document.createElement('div')
      actions.className = 'row gap-8'

      const save = document.createElement('button')
      save.className = profile.exists_in_database ? 'btn btn-primary' : 'btn btn-ghost'
      save.type = 'button'
      save.textContent = profile.exists_in_database ? 'Déjà enregistré' : 'Ajouter à la base'
      save.disabled = profile.status === 'Déjà enregistré'
      save.addEventListener('click', async () => {
        save.disabled = true
        try {
          const res = await apiFetch('/api/github/users/save', {
            method: 'POST',
            body: JSON.stringify({ username: profile.username })
          })
          save.className = 'btn btn-primary'
          save.textContent = res.data.duplicate ? 'Déjà enregistré' : (res.data.created ? 'Ajouté' : 'Associé')
          status.className = 'status success'
          status.textContent = 'Déjà enregistré'
          toast('GitHub', res.data.duplicate ? 'Profil déjà présent dans votre base.' : `${profile.username} a été ajouté localement.`, 'success')
          window.dispatchEvent(new CustomEvent('devscope:profiles-changed'))
        } catch (e) {
          save.disabled = false
          toast('GitHub', e.message, 'danger')
        }
      })

      actions.appendChild(save)
      const ignore = document.createElement('button')
      ignore.className = 'btn btn-ghost'
      ignore.type = 'button'
      ignore.textContent = 'Ignorer'
      ignore.addEventListener('click', async () => {
        try {
          await apiFetch('/api/github/users/ignore', {
            method: 'POST',
            body: JSON.stringify({ username: profile.username })
          })
          card.remove()
          toast('GitHub', `${profile.username} ignoré.`, 'success')
          window.dispatchEvent(new CustomEvent('devscope:profiles-changed'))
        } catch (e) {
          toast('GitHub', e.message, 'danger')
        }
      })
      actions.appendChild(ignore)

      card.appendChild(head)
      card.appendChild(bio)
      card.appendChild(stats)
      card.appendChild(actions)
      grid.appendChild(card)
    })
  }

  btn.addEventListener('click', async () => {
    const q = (input.value || '').trim()
    if (!q) {
      meta.textContent = "Saisissez un nom d'utilisateur GitHub."
      renderEmpty("Saisissez un nom d'utilisateur puis cliquez sur Rechercher sur GitHub.")
      return
    }

    setLoading(true)
    meta.textContent = 'Recherche sur GitHub...'
    grid.innerHTML = '<div class="empty"><div class="spinner"></div><div>Chargement...</div></div>'

    const params = new URLSearchParams()
    params.set('q', q)
    params.set('limit', limit.value || '5')

    try {
      const res = await apiFetch('/api/github/users?' + params.toString())
      const items = res.data.items || []
      meta.textContent = `${items.length} résultat(s) GitHub`
      renderProfiles(items)
    } catch (e) {
      meta.textContent = 'La recherche GitHub a échoué.'
      renderEmpty(e.message)
      toast('GitHub', e.message, 'danger')
    } finally {
      setLoading(false)
    }
  })
}

async function loadDashboard() {
  const statusPill = $('etlStatusPill')
  const lastRun = $('etlLastRun')
  const monitor = $('etlMonitor')

  const loadingHtml = '<div class="empty"><div class="spinner"></div><div>Chargement...</div></div>'
  if ($('mostActiveList')) $('mostActiveList').innerHTML = loadingHtml
  if ($('topDevsList')) $('topDevsList').innerHTML = loadingHtml
  if ($('recentProfilesList')) $('recentProfilesList').innerHTML = loadingHtml
  if (monitor) monitor.innerHTML = loadingHtml

  try {
    const summary = await apiFetch('/api/dashboard/summary')
    const k = summary.data.kpis
    const last = summary.data.etl_last_run
    animateNumber($('kpiProfiles'), k.total_profiles)
    animateNumber($('kpiActive'), k.active_profiles_estimate)
    animateNumber($('kpiFavorites'), k.favorites_count)
    const profilesTrend = $('kpiProfilesTrend')
    if (profilesTrend) {
      if (last) {
        const created = Number(last.created_count || 0)
        const linked = Number(last.linked_count || 0)
        const updated = Number(last.updated_count || 0)
        profilesTrend.textContent = created || linked ? `+${Math.max(created, linked)} dernier ETL` : `${updated} mis à jour`
      } else {
        profilesTrend.textContent = 'Aucun ETL'
      }
    }

    const quality = Math.round(((Number(k.with_location_pct || 0) + Number(k.with_bio_pct || 0)) / 2) || 0)
    const kpiQuality = $('kpiQuality')
    if (kpiQuality) kpiQuality.textContent = quality + '%'
    setProgress($('qualityBar'), quality)

    const active = summary.data.most_active_profiles || []
    const list = $('mostActiveList')
    if (list) list.innerHTML = ''
    active.forEach((d) => {
      if (!list) return
      const item = document.createElement('div')
      item.className = 'list-item'
      const left = document.createElement('div')
      const head = document.createElement('div')
      head.className = 'list-head'
      head.innerHTML = avatarHtml(d.avatar_url, d.display_name || d.username)
      const t = document.createElement('div')
      t.className = 'list-title'
      t.textContent = d.display_name || d.username
      const s = document.createElement('div')
      s.className = 'list-sub'
      s.textContent = `${d.platform} · dépôts ${d.repos_count} · followers ${d.followers_count}`
      head.appendChild(t)
      left.appendChild(head)
      left.appendChild(s)
      const right = document.createElement('a')
      right.className = 'btn btn-ghost'
      right.href = `/developers/${d.id}`
      right.textContent = 'Voir'
      item.appendChild(left)
      item.appendChild(right)
      list.appendChild(item)
    })

    const top = summary.data.top_developers || []
    const topList = $('topDevsList')
    if (topList) {
      topList.innerHTML = ''
      top.forEach((d) => {
        const item = document.createElement('div')
        item.className = 'list-item'
        const left = document.createElement('div')
        const head = document.createElement('div')
        head.className = 'list-head'
        head.innerHTML = avatarHtml(d.avatar_url, d.display_name || d.username)
        const t = document.createElement('div')
        t.className = 'list-title'
        t.textContent = d.display_name || d.username
        const s = document.createElement('div')
        s.className = 'list-sub'
        s.textContent = `${safeText(d.location)} · followers ${d.followers_count} · dépôts ${d.repos_count}`
        head.appendChild(t)
        left.appendChild(head)
        left.appendChild(s)
        const right = document.createElement('a')
        right.className = 'btn btn-ghost'
        right.href = `/developers/${d.id}`
        right.textContent = 'Voir'
        item.appendChild(left)
        item.appendChild(right)
        topList.appendChild(item)
      })
    }

    const recent = summary.data.recent_collected_profiles || []
    const recentList = $('recentProfilesList')
    if (recentList) {
      recentList.innerHTML = ''
      recent.forEach((d) => {
        const item = document.createElement('div')
        item.className = 'list-item'
        const left = document.createElement('div')
        const head = document.createElement('div')
        head.className = 'list-head'
        head.innerHTML = avatarHtml(d.avatar_url, d.display_name || d.username)
        const t = document.createElement('div')
        t.className = 'list-title'
        t.textContent = d.display_name || d.username
        const s = document.createElement('div')
        s.className = 'list-sub'
        s.textContent = `${d.platform} · ${safeText(d.location)} · mis à jour ${formatDate(d.updated_at)}`
        head.appendChild(t)
        left.appendChild(head)
        left.appendChild(s)
        const right = document.createElement('a')
        right.className = 'btn btn-ghost'
        right.href = `/developers/${d.id}`
        right.textContent = 'Ouvrir'
        item.appendChild(left)
        item.appendChild(right)
        recentList.appendChild(item)
      })
    }

    if (monitor) {
      if (!last) {
        monitor.innerHTML = "<div class=\"empty\">Aucune exécution ETL pour le moment.</div>"
      } else {
        const total = Math.max(1, Number(last.extracted_count || 0))
        const cleanPct = Math.round((Number(last.transformed_count || 0) / total) * 100)
        const loadPct = Math.round((Number(last.loaded_count || 0) / Math.max(1, Number(last.transformed_count || 0))) * 100)
        monitor.innerHTML = `
          <div class="monitor-grid">
            <div class="monitor-item">
              <div class="monitor-label">Dernier ETL</div>
              <div class="monitor-value">#${last.id} · ${safeText(last.status)}</div>
              <div class="monitor-sub">${formatDate(last.started_at)}</div>
            </div>
            <div class="monitor-item">
              <div class="monitor-label">Extraction</div>
              <div class="monitor-value">${safeText(last.extracted_count)}</div>
              <div class="progress"><div class="progress-bar" style="width:100%"></div></div>
            </div>
            <div class="monitor-item">
              <div class="monitor-label">Transformation</div>
              <div class="monitor-value">${safeText(last.transformed_count)}</div>
              <div class="progress"><div class="progress-bar" style="width:${cleanPct}%"></div></div>
              <div class="monitor-sub">doublons supprimés ${safeText(last.duplicates_removed)} · valeurs manquantes corrigées ${safeText(last.missing_values_filled)}</div>
            </div>
            <div class="monitor-item">
              <div class="monitor-label">Chargement</div>
              <div class="monitor-value">${safeText(last.loaded_count)}</div>
              <div class="progress"><div class="progress-bar" style="width:${loadPct}%"></div></div>
              <div class="monitor-sub">nouveaux ${safeText(last.created_count)} · mis à jour ${safeText(last.updated_count)} · associés ${safeText(last.linked_count)} · erreurs ${safeText(last.error_count)}</div>
            </div>
          </div>
        `
      }
    }
  } catch (e) {
    toast('Tableau de bord', e.message, 'danger')
  }

  try {
    const charts = await apiFetch('/api/dashboard/charts')
    plotChart('chartTopTech', charts.data.top_technologies)
    plotChart('chartActivity', charts.data.activity_over_time)
    plotChart('chartPlatform', charts.data.platform_distribution)
    if ($('chartGrowth') && charts.data.profile_growth) {
      plotChart('chartGrowth', charts.data.profile_growth)
    }
    if ($('chartLocation') && charts.data.location_distribution) {
      plotChart('chartLocation', charts.data.location_distribution)
    }
    if ($('chartFollowersRepos') && charts.data.followers_repositories) {
      plotChart('chartFollowersRepos', charts.data.followers_repositories)
    }
    if ($('chartActivityFreshness') && charts.data.activity_freshness) {
      plotChart('chartActivityFreshness', charts.data.activity_freshness)
    }
    if ($('chartDataCompleteness') && charts.data.data_completeness) {
      plotChart('chartDataCompleteness', charts.data.data_completeness)
    }
    if ($('chartEtlThroughput') && charts.data.etl_throughput) {
      plotChart('chartEtlThroughput', charts.data.etl_throughput)
    }
  } catch (e) {
    toast('Graphiques', e.message, 'danger')
  }

  const btn = $('runEtlBtn')
  if (!btn) return
  btn.addEventListener('click', async () => {
    const query = $('etlQuery').value || ''
    const limit = parseInt($('etlLimit').value || '25', 10)
    btn.disabled = true
    btn.textContent = 'Exécution...'
    if (statusPill) statusPill.textContent = 'En cours'
    if (statusPill) statusPill.className = 'pill status running'
    try {
      const res = await apiFetch('/api/etl/run', { method: 'POST', body: JSON.stringify({ query, limit }) })
      toast('ETL', `Terminé. ${res.data.created_count || 0} nouveaux, ${res.data.updated_count || 0} mis à jour.`, 'success')
      if (statusPill) statusPill.textContent = 'Succès'
      if (statusPill) statusPill.className = 'pill status success'
      if (lastRun) lastRun.textContent = `Dernière exécution : #${res.data.etl_run_id}`
      await loadDashboard()
    } catch (e) {
      toast('ETL', e.message, 'danger')
      if (statusPill) statusPill.textContent = 'Échec'
      if (statusPill) statusPill.className = 'pill status failed'
    } finally {
      btn.disabled = false
      btn.textContent = 'Lancer ETL'
    }
  })
}

async function loadSearch() {
  initGithubLiveSearch()

  const resultsMeta = $('resultsMeta')
  const grid = $('resultsGrid')
  const chips = $('recentSearches')
  const tagsRoot = $('activeTags')
  const paginationRoot = $('pagination')
  const operationsRoot = $('profileOperations')
  const searchBtn = $('searchBtn')
  const resetBtn = $('resetBtn')
  const searchInput = $('searchInput')

  if (!resultsMeta || !grid || !searchBtn || !resetBtn || !searchInput) return

  let favorites = new Set()
  try {
    const favRes = await apiFetch('/api/favorites')
    favorites = new Set(favRes.data.developer_ids || [])
  } catch (_) {}

  const state = {
    page: 1,
    per_page: 18,
  }

  function getInputs() {
    return {
      q: $('searchInput').value || '',
      technologies: $('filterTechs').value || '',
      platform: $('filterPlatform').value || '',
      activity: $('filterActivity').value || '',
      recent_days: $('filterRecent').value || '',
      location: $('filterLocation').value || '',
      min_repos: $('filterReposMin').value || '',
      max_repos: $('filterReposMax').value || '',
      min_followers: $('filterFollowersMin').value || '',
      max_followers: $('filterFollowersMax').value || '',
      sort: $('filterSort').value || 'activity',
      order: $('filterOrder').value || 'desc'
    }
  }

  function setInput(id, value) {
    const el = $(id)
    if (!el) return
    el.value = value === null || value === undefined ? '' : String(value)
  }

  function applyUrlPreset() {
    const params = new URLSearchParams(window.location.search || '')
    const q = params.get('q')
    if (q) $('searchInput').value = q
  }

  function buildTags(values) {
    if (!tagsRoot) return
    tagsRoot.innerHTML = ''
    const items = []
    if (values.q) items.push(['searchInput', 'q', values.q])
    if (values.technologies) items.push(['filterTechs', 'technologies', values.technologies])
    if (values.location) items.push(['filterLocation', 'location', 'localisation : ' + values.location])
    if (values.platform) items.push(['filterPlatform', 'platform', 'plateforme : ' + values.platform])
    if (values.activity) items.push(['filterActivity', 'activity', 'activité : ' + values.activity])
    if (values.recent_days) items.push(['filterRecent', 'recent_days', values.recent_days + 'd'])
    if (values.min_repos) items.push(['filterReposMin', 'min_repos', 'dépôts >= ' + values.min_repos])
    if (values.max_repos) items.push(['filterReposMax', 'max_repos', 'dépôts <= ' + values.max_repos])
    if (values.min_followers) items.push(['filterFollowersMin', 'min_followers', 'followers >= ' + values.min_followers])
    if (values.max_followers) items.push(['filterFollowersMax', 'max_followers', 'followers <= ' + values.max_followers])
    items.push(['filterSort', 'sort', 'tri : ' + values.sort])
    items.push(['filterOrder', 'order', 'ordre : ' + values.order])

    if (items.length === 0) {
      tagsRoot.innerHTML = '<span class="muted small">Aucun filtre actif.</span>'
      return
    }

    items.forEach(([fieldId, key, label]) => {
      const tag = document.createElement('span')
      tag.className = 'tag'
      const text = document.createElement('span')
      text.textContent = label
      const x = document.createElement('button')
      x.type = 'button'
      x.setAttribute('aria-label', 'Retirer le filtre')
      x.textContent = 'x'
      x.addEventListener('click', () => {
        setInput(fieldId, '')
        state.page = 1
        run()
      })
      tag.appendChild(text)
      tag.appendChild(x)
      tagsRoot.appendChild(tag)
    })
  }

  async function refreshHistory() {
    if (!chips) return
    chips.innerHTML = ''
    try {
      const h = await apiFetch('/api/search/history')
      const items = h.data.items || []
      items.slice(0, 10).forEach((it) => {
        const btn = document.createElement('button')
        btn.type = 'button'
        btn.className = 'chip'
        const parts = []
        if (it.q) parts.push(it.q)
        if (it.technologies) parts.push(it.technologies)
        if (it.location) parts.push(it.location)
        btn.textContent = parts.join(' / ') || 'Recherche'
        btn.addEventListener('click', () => {
          $('searchInput').value = it.q || ''
          $('filterTechs').value = it.technologies || ''
          $('filterPlatform').value = it.platform || ''
          $('filterActivity').value = it.activity || ''
          $('filterRecent').value = it.recent_days ? String(it.recent_days) : ''
          $('filterLocation').value = it.location || ''
          $('filterReposMin').value = it.min_repos === null || it.min_repos === undefined ? '' : String(it.min_repos)
          $('filterReposMax').value = it.max_repos === null || it.max_repos === undefined ? '' : String(it.max_repos)
          $('filterFollowersMin').value = it.min_followers === null || it.min_followers === undefined ? '' : String(it.min_followers)
          $('filterFollowersMax').value = it.max_followers === null || it.max_followers === undefined ? '' : String(it.max_followers)
          $('filterSort').value = it.sort || 'activity'
          $('filterOrder').value = it.order || 'desc'
          state.page = 1
          run()
        })
        chips.appendChild(btn)
      })

    } catch (_) {}
  }

  async function refreshOperations() {
    if (!operationsRoot) return
    operationsRoot.innerHTML = '<div class="empty"><div class="spinner"></div><div>Chargement...</div></div>'
    try {
      const res = await apiFetch('/api/profile-operations?limit=12')
      const items = res.data.items || []
      operationsRoot.innerHTML = ''
      if (!items.length) {
        operationsRoot.innerHTML = '<div class="empty">Aucune operation pour le moment.</div>'
        return
      }
      items.forEach((op) => {
        const item = document.createElement('div')
        item.className = 'list-item'
        const left = document.createElement('div')
        const title = document.createElement('div')
        title.className = 'list-title'
        title.textContent = `${op.operation} - ${op.username || 'profil'}`
        const sub = document.createElement('div')
        sub.className = 'list-sub'
        sub.textContent = `${safeText(op.message)} - ${formatDate(op.created_at)}`
        left.appendChild(title)
        left.appendChild(sub)
        const badge = document.createElement('span')
        badge.className = op.operation === 'delete' ? 'status failed' : op.operation === 'duplicate' ? 'status running' : 'status success'
        badge.textContent = op.platform || 'github'
        item.appendChild(left)
        item.appendChild(badge)
        operationsRoot.appendChild(item)
      })
    } catch (e) {
      operationsRoot.innerHTML = '<div class="empty">Historique indisponible.</div>'
    }
  }

  function openDetails(d) {
    const body = `
      <div class="profile-head">
        <div class="profile-avatar">${avatarHtml(d.avatar_url, d.display_name || d.username)}</div>
        <div>
          <div class="list-title">${safeText(d.display_name || d.username)}</div>
          <div class="list-sub">${safeText(d.username)} · ${safeText(d.platform)} · ${safeText(d.location || 'Localisation non renseignée')}</div>
          <div class="profile-bio">${safeText(d.bio || 'Aucune bio disponible.')}</div>
        </div>
      </div>
      <div class="stats-row compact-stats">
        <div class="stat"><div class="stat-label">Followers</div><div class="stat-value">${safeText(d.followers_count)}</div></div>
        <div class="stat"><div class="stat-label">Repositories</div><div class="stat-value">${safeText(d.repos_count)}</div></div>
        <div class="stat"><div class="stat-label">Activite</div><div class="stat-value">${formatDate(d.last_activity_at)}</div></div>
        <div class="stat"><div class="stat-label">Score</div><div class="stat-value">${safeText(d.global_score)}</div></div>
      </div>
      <div class="skills modal-skills">${renderSkillPills(d.skills, 20)}</div>
    `
    const open = document.createElement('a')
    open.className = 'btn btn-primary'
    open.href = `/developers/${d.id}`
    open.textContent = 'Ouvrir la fiche'
    openProfileModal('Detail du profil', body, [open])
  }

  function openEdit(d) {
    const form = document.createElement('form')
    form.className = 'modal-form'
    form.innerHTML = `
      <label class="field"><span class="label">Nom</span><input class="input" name="display_name" value="${safeText(d.display_name || '')}" /></label>
      <label class="field"><span class="label">Localisation</span><input class="input" name="location" value="${safeText(d.location || '')}" /></label>
      <label class="field"><span class="label">Avatar URL</span><input class="input" name="avatar_url" value="${safeText(d.avatar_url || '')}" /></label>
      <label class="field"><span class="label">Profil URL</span><input class="input" name="profile_url" value="${safeText(d.profile_url || '')}" /></label>
      <div class="field-split">
        <label class="field"><span class="label">Followers</span><input class="input" name="followers_count" type="number" min="0" value="${safeText(d.followers_count || 0)}" /></label>
        <label class="field"><span class="label">Repositories</span><input class="input" name="repos_count" type="number" min="0" value="${safeText(d.repos_count || 0)}" /></label>
      </div>
      <label class="field"><span class="label">Bio</span><textarea class="input textarea" name="bio">${safeText(d.bio || '')}</textarea></label>
      <label class="field"><span class="label">Competences / technologies</span><textarea class="input textarea" name="skills">${skillNames(d.skills).join(', ')}</textarea></label>
    `
    const save = document.createElement('button')
    save.className = 'btn btn-primary'
    save.type = 'submit'
    save.textContent = 'Enregistrer'
    form.addEventListener('submit', async (e) => {
      e.preventDefault()
      save.disabled = true
      const data = Object.fromEntries(new FormData(form).entries())
      data.skills = (data.skills || '').split(',').map((name) => ({ name: name.trim(), score: 1 })).filter((s) => s.name)
      try {
        await apiFetch(`/api/developers/${d.id}`, { method: 'PUT', body: JSON.stringify(data) })
        toast('Search', 'Profil modifie.', 'success')
        const overlay = $('profileModalOverlay')
        if (overlay) overlay.remove()
        await run()
        await refreshOperations()
      } catch (err) {
        toast('Modification', err.message, 'danger')
      } finally {
        save.disabled = false
      }
    })
    openProfileModal('Modifier le profil', form, [save])
  }

  function confirmDelete(d) {
    const body = document.createElement('div')
    body.innerHTML = `
      <div class="empty danger-empty">
        <div>Suppression définitive de ${safeText(d.display_name || d.username)}.</div>
        <div class="muted small">Cette action supprime le profil et ses relations associées.</div>
      </div>
    `
    const del = document.createElement('button')
    del.className = 'btn btn-danger'
    del.type = 'button'
    del.textContent = 'Supprimer'
    del.addEventListener('click', async () => {
      del.disabled = true
      try {
        await apiFetch(`/api/developers/${d.id}`, { method: 'DELETE', body: JSON.stringify({ confirm: 'delete' }) })
        toast('Search', 'Profil supprimé.', 'success')
        const overlay = $('profileModalOverlay')
        if (overlay) overlay.remove()
        await run()
        await refreshOperations()
        window.dispatchEvent(new CustomEvent('devscope:profiles-changed'))
      } catch (err) {
        toast('Suppression', err.message, 'danger')
      } finally {
        del.disabled = false
      }
    })
    openProfileModal('Confirmer la suppression', body, [del])
  }

  function renderLocalProfileCard(d) {
    const card = document.createElement('div')
    card.className = 'result-card profile-result-card'

    const head = document.createElement('div')
    head.className = 'result-head'
    const left = document.createElement('div')
    left.className = 'profile-identity'
    const avatar = document.createElement('div')
    avatar.className = 'result-avatar'
    avatar.innerHTML = avatarHtml(d.avatar_url, d.display_name || d.username)
    const copy = document.createElement('div')
    copy.className = 'profile-copy'
    const title = document.createElement('div')
    title.className = 'list-title'
    title.textContent = d.display_name || d.username
    const sub = document.createElement('div')
    sub.className = 'list-sub'
    sub.textContent = `${d.username} · ${d.platform} · ${safeText(d.location || 'Localisation non renseignée')}`
    left.appendChild(avatar)
    copy.appendChild(title)
    copy.appendChild(sub)
    left.appendChild(copy)

    const badge = document.createElement('div')
    badge.className = activityBadge(d.activity_level)
    badge.textContent = activityLabel(d.activity_level)
    head.appendChild(left)
    head.appendChild(badge)

    const status = document.createElement('div')
    status.className = 'profile-status-row'
    status.innerHTML = `
      <span class="status success">${safeText(d.status || 'Déjà enregistré')}</span>
      <span class="metric"><strong>${safeText(d.followers_count)}</strong> Followers</span>
      <span class="metric"><strong>${safeText(d.repos_count)}</strong> Dépôts</span>
      <span class="metric">Score ${safeText(d.global_score)}</span>
    `

    const skills = document.createElement('div')
    skills.className = 'profile-skill-row'
    skills.innerHTML = renderSkillPills(d.skills, 6)

    const meta = document.createElement('div')
    meta.className = 'profile-meta-row'
    meta.innerHTML = `
      <span>Dernière activité : ${formatDate(d.last_activity_at)}</span>
      <span>Mise à jour : ${formatDate(d.updated_at)}</span>
    `

    const actions = document.createElement('div')
    actions.className = 'row gap-8 profile-actions'

    const details = document.createElement('button')
    details.className = 'btn btn-ghost'
    details.type = 'button'
    details.textContent = 'Détails'
    details.addEventListener('click', () => openDetails(d))

    const open = document.createElement('a')
    open.className = 'btn btn-ghost'
    open.href = `/developers/${d.id}`
    open.textContent = 'Fiche'

    const edit = document.createElement('button')
    edit.className = 'btn btn-ghost'
    edit.type = 'button'
    edit.textContent = 'Modifier'
    edit.addEventListener('click', () => openEdit(d))

    const remove = document.createElement('button')
    remove.className = 'btn btn-danger'
    remove.type = 'button'
    remove.textContent = 'Supprimer'
    remove.addEventListener('click', () => confirmDelete(d))

    const fav = document.createElement('button')
    fav.className = 'btn ' + (favorites.has(d.id) ? 'btn-primary' : 'btn-ghost')
    fav.type = 'button'
    fav.textContent = favorites.has(d.id) ? 'Favori' : 'Favori +'
    fav.addEventListener('click', async () => {
      try {
        if (favorites.has(d.id)) {
          await apiFetch(`/api/favorites/${d.id}`, { method: 'DELETE' })
          favorites.delete(d.id)
          fav.className = 'btn btn-ghost'
          fav.textContent = 'Favori +'
          toast('Favoris', 'Retiré des favoris.', 'success')
        } else {
          await apiFetch(`/api/favorites/${d.id}`, { method: 'POST' })
          favorites.add(d.id)
          fav.className = 'btn btn-primary'
          fav.textContent = 'Favori'
          toast('Favoris', 'Ajouté aux favoris.', 'success')
        }
      } catch (e) {
        toast('Favoris', e.message, 'danger')
      }
    })

    actions.appendChild(details)
    actions.appendChild(open)
    actions.appendChild(edit)
    actions.appendChild(remove)
    actions.appendChild(fav)
    card.appendChild(head)
    card.appendChild(status)
    card.appendChild(skills)
    card.appendChild(meta)
    card.appendChild(actions)
    return card
  }

  function renderPagination(total) {
    if (!paginationRoot) return
    const totalPages = Math.max(1, Math.ceil(Number(total || 0) / state.per_page))
    paginationRoot.innerHTML = ''

    const left = document.createElement('div')
    left.className = 'muted small'
    left.textContent = `Page ${state.page} / ${totalPages}`

    const pager = document.createElement('div')
    pager.className = 'pager'

    const prev = document.createElement('button')
    prev.type = 'button'
    prev.className = 'pager-btn'
    prev.textContent = 'Précédent'
    prev.disabled = state.page <= 1
    prev.addEventListener('click', () => {
      state.page = Math.max(1, state.page - 1)
      run()
    })

    const next = document.createElement('button')
    next.type = 'button'
    next.className = 'pager-btn'
    next.textContent = 'Suivant'
    next.disabled = state.page >= totalPages
    next.addEventListener('click', () => {
      state.page = Math.min(totalPages, state.page + 1)
      run()
    })

    pager.appendChild(prev)

    const start = Math.max(1, state.page - 2)
    const end = Math.min(totalPages, state.page + 2)
    for (let p = start; p <= end; p++) {
      const b = document.createElement('button')
      b.type = 'button'
      b.className = 'pager-btn' + (p === state.page ? ' active' : '')
      b.textContent = String(p)
      b.addEventListener('click', () => {
        state.page = p
        run()
      })
      pager.appendChild(b)
    }

    pager.appendChild(next)

    paginationRoot.appendChild(left)
    paginationRoot.appendChild(pager)
  }

  async function run() {
    grid.innerHTML = ''
    resultsMeta.textContent = 'Chargement...'
    grid.innerHTML = '<div class="empty"><div class="spinner"></div><div>Chargement...</div></div>'
    const values = getInputs()
    buildTags(values)

    const params = new URLSearchParams()
    if (values.q) params.set('q', values.q)
    if (values.technologies) params.set('technologies', values.technologies)
    if (values.platform) params.set('platform', values.platform)
    if (values.activity) params.set('activity', values.activity)
    if (values.recent_days) params.set('recent_days', values.recent_days)
    if (values.location) params.set('location', values.location)
    if (values.min_repos) params.set('min_repos', values.min_repos)
    if (values.max_repos) params.set('max_repos', values.max_repos)
    if (values.min_followers) params.set('min_followers', values.min_followers)
    if (values.max_followers) params.set('max_followers', values.max_followers)
    if (values.sort) params.set('sort', values.sort)
    if (values.order) params.set('order', values.order)
    params.set('page', String(state.page))
    params.set('per_page', String(state.per_page))

    try {
      const res = await apiFetch('/api/search?' + params.toString())
      const items = res.data.items || []
      const total = Number(res.data.total || items.length || 0)
      const start = total === 0 ? 0 : (state.page - 1) * state.per_page + 1
      const end = Math.min(total, (state.page - 1) * state.per_page + items.length)
      resultsMeta.textContent = total === 0 ? '0 résultat(s)' : `Affichage ${start}-${end} sur ${total}`
      refreshHistory()
      renderPagination(total)
      if (items.length === 0) {
        const empty = document.createElement('div')
        empty.className = 'empty'
        empty.textContent = "Aucun résultat. Lancez l'ETL depuis le tableau de bord pour collecter des données."
        grid.appendChild(empty)
        return
      }

      grid.innerHTML = ''
      items.forEach((d) => {
        grid.appendChild(renderLocalProfileCard(d))
      })
    } catch (e) {
      resultsMeta.textContent = 'Erreur'
      toast('Recherche', e.message, 'danger')
    }
  }

  searchBtn.addEventListener('click', () => {
    state.page = 1
    run()
  })
  resetBtn.addEventListener('click', () => {
    searchInput.value = ''
    $('filterTechs').value = ''
    $('filterPlatform').value = ''
    $('filterActivity').value = ''
    $('filterRecent').value = ''
    $('filterLocation').value = ''
    $('filterReposMin').value = ''
    $('filterReposMax').value = ''
    $('filterFollowersMin').value = ''
    $('filterFollowersMax').value = ''
    $('filterSort').value = 'activity'
    $('filterOrder').value = 'desc'
    state.page = 1
    run()
  })
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      state.page = 1
      run()
    }
  })

  applyUrlPreset()
  run()
  refreshHistory()
}

async function loadDeveloper() {
  const id = window.__DEVELOPER_ID__
  let favorites = new Set()
  try {
    const favRes = await apiFetch('/api/favorites')
    favorites = new Set(favRes.data.developer_ids || [])
  } catch (_) {}

  const favBtn = $('favToggle')
  function refreshFavBtn() {
    const saved = favorites.has(id)
    favBtn.textContent = saved ? 'Enregistré' : 'Enregistrer'
    favBtn.className = 'btn ' + (saved ? 'btn-primary' : 'btn-ghost')
  }

  refreshFavBtn()
  favBtn.addEventListener('click', async () => {
    try {
      if (favorites.has(id)) {
        await apiFetch(`/api/favorites/${id}`, { method: 'DELETE' })
        favorites.delete(id)
        toast('Favoris', 'Retiré des favoris.', 'success')
      } else {
        await apiFetch(`/api/favorites/${id}`, { method: 'POST' })
        favorites.add(id)
        toast('Favoris', 'Enregistré dans les favoris.', 'success')
      }
      refreshFavBtn()
    } catch (e) {
      toast('Favoris', e.message, 'danger')
    }
  })

  try {
    const res = await apiFetch(`/api/developers/${id}`)
    const d = res.data
    $('devName').textContent = d.display_name || d.username
    $('devMeta').textContent = `${d.platform} · ${d.username} · ${safeText(d.location)}`
    const avatar = $('devAvatar')
    if (avatar) avatar.innerHTML = avatarHtml(d.avatar_url, d.display_name || d.username)
    const bio = $('devBio')
    if (bio) bio.textContent = d.bio ? String(d.bio) : ''
    const link = $('devProfileLink')
    link.href = d.profile_url

    const stats = $('devStats')
    stats.innerHTML = ''
    const items = [
      ['Followers', d.followers_count],
      ['Dépôts', d.repos_count],
      ['Contributions (1 an)', d.contributions_last_year],
      ['Dernière activité', formatDate(d.last_activity_at)],
      ['Créé le', formatDate(d.created_at)],
      ['Mis à jour le', formatDate(d.updated_at)]
    ]
    items.forEach(([label, value]) => {
      const box = document.createElement('div')
      box.className = 'stat'
      const l = document.createElement('div')
      l.className = 'stat-label'
      l.textContent = label
      const v = document.createElement('div')
      v.className = 'stat-value'
      v.textContent = safeText(value)
      box.appendChild(l)
      box.appendChild(v)
      stats.appendChild(box)
    })

    const skills = $('devSkills')
    skills.innerHTML = ''
    ;(d.skills || []).forEach((s) => {
      const pill = document.createElement('div')
      pill.className = 'skill-pill'
      pill.innerHTML = `<span>${s.name}</span><span class="skill-score">${s.score}</span>`
      skills.appendChild(pill)
    })
  } catch (e) {
    toast('Développeur', e.message, 'danger')
  }

  try {
    const rr = await apiFetch(`/api/developers/${id}/repos`)
    const items = rr.data.items || []
    const root = $('devRepos')
    if (root) {
      root.innerHTML = ''
      if (items.length === 0) {
        root.innerHTML = "<div class=\"empty\">Aucun aperçu de dépôt pour le moment. Relancez l'ETL pour actualiser les données du profil.</div>"
      } else {
        items.forEach((r) => {
          const row = document.createElement('a')
          row.className = 'repo-row'
          row.href = r.html_url || '#'
          row.target = '_blank'
          row.rel = 'noreferrer'
          row.innerHTML = `
            <div>
              <div class="repo-name">${safeText(r.name)}</div>
              <div class="repo-sub">${safeText(r.language)} · push ${formatDate(r.pushed_at)}</div>
            </div>
            <div class="repo-metrics">
              <span class="metric">★ ${safeText(r.stargazers_count)}</span>
              <span class="metric">⑂ ${safeText(r.forks_count)}</span>
            </div>
          `
          root.appendChild(row)
        })
      }
    }
  } catch (_) {}

  try {
    const charts = await apiFetch(`/api/developers/${id}/charts`)
    plotChart('devChartBar', charts.data.skills_bar)
    plotChart('devChartPie', charts.data.skills_pie)
  } catch (e) {
    toast('Graphiques', e.message, 'danger')
  }
}

async function loadFavorites() {
  const grid = $('favoritesGrid')
  grid.innerHTML = ''
  let ids = []
  try {
    const fav = await apiFetch('/api/favorites')
    ids = fav.data.developer_ids || []
  } catch (e) {
    toast('Favoris', e.message, 'danger')
    return
  }

  if (ids.length === 0) {
    const empty = document.createElement('div')
    empty.className = 'muted'
    empty.style.padding = '16px'
    empty.textContent = "Aucun profil enregistré pour le moment. Enregistrez un développeur depuis la page de recherche."
    grid.appendChild(empty)
    return
  }

  // Fill KPIs
  try {
    const statsRes = await apiFetch('/api/favorites/stats')
    const s = statsRes.data || {}
    const favTotal = $('favTotal')
    if (favTotal) favTotal.textContent = String(s.total || ids.length)
    const favAvgFollowers = $('favAvgFollowers')
    if (favAvgFollowers) favAvgFollowers.textContent = String(Math.round(s.avg_followers || 0))
    const favAvgRepos = $('favAvgRepos')
    if (favAvgRepos) favAvgRepos.textContent = String(Math.round(s.avg_repos || 0))
  } catch (_) {}

  const compareBtn = $('compareFavoritesBtn')
  if (compareBtn) {
    // disable when less than 2 favorites
    if ((ids || []).length < 2) {
      compareBtn.disabled = true
      compareBtn.classList.add('compare-disabled')
    } else {
      compareBtn.disabled = false
      compareBtn.classList.remove('compare-disabled')
    }
    compareBtn.addEventListener('click', () => {
      const idsArr = Array.from(ids)
      if (idsArr.length < 2) return toast('Comparaison', 'Sélectionnez au moins deux favoris à comparer.', 'warning')
      window.open('/ml/compare?ids=' + idsArr.join(','), '_blank')
    })
  }

  for (const id of ids) {
    try {
      const res = await apiFetch(`/api/developers/${id}`)
      const d = res.data

      const card = document.createElement('div')
      card.className = 'result-card'
      const head = document.createElement('div')
      head.className = 'result-head'
      const left = document.createElement('div')
      const title = document.createElement('div')
      title.className = 'list-title'
      title.textContent = d.display_name || d.username
      const sub = document.createElement('div')
      sub.className = 'list-sub'
      sub.textContent = `${d.platform} · dépôts ${d.repos_count} · followers ${d.followers_count}`
      left.appendChild(title)
      left.appendChild(sub)
      head.appendChild(left)
      const badge = document.createElement('div')
      badge.className = 'badge'
      badge.textContent = 'enregistré'
      head.appendChild(badge)

      const meta = document.createElement('div')
      meta.className = 'muted small'
      meta.textContent = `Dernière activité : ${formatDate(d.last_activity_at)}`

      const actions = document.createElement('div')
      actions.className = 'row gap-8'
      const view = document.createElement('a')
      view.className = 'btn btn-ghost'
      view.href = `/developers/${d.id}`
      view.textContent = 'Voir'

      const remove = document.createElement('button')
      remove.className = 'btn btn-ghost'
      remove.type = 'button'
      remove.textContent = 'Retirer'
      remove.addEventListener('click', async () => {
        try {
          await apiFetch(`/api/favorites/${d.id}`, { method: 'DELETE' })
          card.remove()
          toast('Favoris', 'Retiré des favoris.', 'success')
        } catch (e) {
          toast('Favoris', e.message, 'danger')
        }
      })

      actions.appendChild(view)
      actions.appendChild(remove)

      card.appendChild(head)
      card.appendChild(meta)
      card.appendChild(actions)
      grid.appendChild(card)
    } catch (_) {}
  }
}

async function loadEtlHistory() {
  const table = $('etlTable').querySelector('tbody')

  table.innerHTML = ''

  try {
    const res = await apiFetch('/api/etl/history')
    const items = res.data.items || []
    if (items.length === 0) {
      const tr = document.createElement('tr')
      tr.innerHTML = "<td colspan=\"10\" class=\"muted\">Aucune exécution ETL pour le moment. Lancez l'ETL depuis le tableau de bord.</td>"
      table.appendChild(tr)
      return
    }

    items.forEach((r) => {
      const tr = document.createElement('tr')
      const statusClass = r.status === 'success' ? 'success' : r.status === 'failed' ? 'failed' : 'running'
      tr.innerHTML = `
        <td>${r.id}</td>
        <td>${safeText(r.source)}</td>
        <td><span class="status ${statusClass}">${safeText(r.status)}</span></td>
        <td>${safeText(r.extracted_count)}</td>
        <td>${safeText(r.transformed_count)}</td>
        <td>${safeText(r.loaded_count)}</td>
        <td>${safeText(r.duration_seconds ? r.duration_seconds + 's' : (r.duration_ms ? (Number(r.duration_ms)/1000).toFixed(1) + 's' : '—'))}</td>
        <td>${safeText(r.duplicates_removed)}</td>
        <td>${safeText(r.error_count)}</td>
        <td>${formatDate(r.started_at)}</td>
      `
      table.appendChild(tr)
    })

  } catch (e) {
    toast('Historique ETL', e.message, 'danger')
  }
}


document.addEventListener('DOMContentLoaded', () => {
  initTheme()
  initSidebar()
  initGlobalSearch()
  flashToToasts()

  const page = window.__PAGE__
  if (page === 'dashboard') loadDashboard()
  if (page === 'search') loadSearch()
  if (page === 'developer') loadDeveloper()
  if (page === 'favorites') loadFavorites()
  if (page === 'etl_history') loadEtlHistory()
  initProfileMenu()
  initEtlControls()
})

