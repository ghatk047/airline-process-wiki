/* Airlines Process Wiki JS v3 — icon-rail sidebar + drag resize + lightbox + search */

/* L1 domain icons */
const DOMAIN_ICONS = {
  'network and pricing':              '🗺️',
  'network planning':                 '🗺️',
  'customer experience':              '⭐',
  'commercial':                       '📣',
  'flight operations':                '✈️',
  'crew management':                  '👨‍✈️',
  'ground operations':                '🛄',
  'maintenance':                      '🔧',
  'mro':                              '🔧',
  'corporate support':                '🏢',
  'safety':                           '🛡️',
  'cargo':                            '📦',
  'finance':                          '💰',
  'human resources':                  '👥',
  'information technology':           '💻',
  'procurement':                      '🛒',
  'sustainability':                   '🌱',
  'marketing':                        '📣',
  'regulatory':                       '⚖️',
  'fleet':                            '🛫',
};

function getDomainIcon(name) {
  const lower = (name || '').toLowerCase();
  for (const [key, icon] of Object.entries(DOMAIN_ICONS)) {
    if (lower.includes(key)) return icon;
  }
  return '📋';
}

document.addEventListener('DOMContentLoaded', () => {

  /* ── 1. INJECT ICONS into sidebar domain headers ── */
  document.querySelectorAll('.sidebar-domain').forEach(el => {
    const label = el.querySelector('span:first-child');
    const labelText = label ? label.textContent.trim() : el.textContent.trim();
    
    // Add data-label for tooltip in rail mode
    el.setAttribute('data-label', labelText);

    // Inject icon span if not already present
    if (!el.querySelector('.domain-icon')) {
      const iconEl = document.createElement('span');
      iconEl.className = 'domain-icon';
      iconEl.textContent = getDomainIcon(labelText);
      el.insertBefore(iconEl, el.firstChild);
    }
    // Wrap label text
    if (label && !label.classList.contains('domain-label')) {
      label.classList.add('domain-label');
    }
  });

  /* ── 2. SIDEBAR ACCORDION ── */
  document.querySelectorAll('.sidebar-domain').forEach(el => {
    el.addEventListener('click', () => {
      if (sidebar.classList.contains('rail')) {
        // In rail mode — expand sidebar first then open section
        setSidebarExpanded();
        setTimeout(() => {
          el.classList.add('open');
          const l2 = el.nextElementSibling;
          if (l2) l2.classList.add('open');
        }, 230);
        return;
      }
      el.classList.toggle('open');
      const l2 = el.nextElementSibling;
      if (l2) l2.classList.toggle('open');
    });
  });

  // Auto-open active section
  const active = document.querySelector('.sidebar-l3-link.active');
  if (active) {
    let p = active.closest('.sidebar-l2');
    if (p) {
      p.classList.add('open');
      const d = p.previousElementSibling;
      if (d) d.classList.add('open');
    }
  }

  /* ── 3. SIDEBAR ELEMENTS ── */
  const sidebar   = document.getElementById('sidebar');
  const mainEl    = document.querySelector('.main');
  const toggleBtn = document.getElementById('sidebarToggle') || document.getElementById('sidebar-toggle');

  // Inject drag resizer
  let resizer = document.getElementById('sidebar-resizer');
  if (!resizer) {
    resizer = document.createElement('div');
    resizer.id = 'sidebar-resizer';
    document.body.appendChild(resizer);
  }

  // Inject overlay
  let overlay = document.getElementById('sidebar-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'sidebar-overlay';
    document.body.appendChild(overlay);
  }

  const isMobile = () => window.innerWidth <= 900;
  const RAIL_W   = 52;
  let currentW   = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--sidebar-w')) || 260;

  /* ── 4. COLLAPSE TO RAIL / EXPAND ── */
  function setSidebarRail() {
    sidebar.classList.add('rail');
    sidebar.classList.remove('mobile-open');
    if (toggleBtn) { toggleBtn.innerHTML = '&#9654;'; toggleBtn.title = 'Expand sidebar'; }
    resizer.style.left = RAIL_W + 'px';
    localStorage.setItem('sidebarState', 'rail');
  }

  function setSidebarExpanded() {
    sidebar.classList.remove('rail');
    sidebar.style.width = currentW + 'px';
    if (mainEl) mainEl.style.marginLeft = currentW + 'px';
    resizer.style.left = currentW + 'px';
    if (toggleBtn) { toggleBtn.innerHTML = '&#9664;'; toggleBtn.title = 'Collapse sidebar'; }
    localStorage.setItem('sidebarState', 'expanded');
  }

  function toggleDesktop() {
    if (sidebar.classList.contains('rail')) {
      setSidebarExpanded();
    } else {
      setSidebarRail();
    }
  }

  /* ── 5. MOBILE OPEN/CLOSE ── */
  function openMobile() {
    sidebar.classList.add('mobile-open');
    overlay.classList.add('active');
    if (toggleBtn) { toggleBtn.innerHTML = '&#9664;'; toggleBtn.title = 'Close menu'; }
  }
  function closeMobile() {
    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('active');
    if (toggleBtn) { toggleBtn.innerHTML = '&#9654;'; toggleBtn.title = 'Open menu'; }
  }

  /* ── 6. TOGGLE BUTTON ── */
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      if (isMobile()) {
        sidebar.classList.contains('mobile-open') ? closeMobile() : openMobile();
      } else {
        toggleDesktop();
      }
    });
  }

  overlay.addEventListener('click', closeMobile);

  // Close sidebar on mobile when link clicked
  sidebar.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => { if (isMobile()) closeMobile(); });
  });

  /* ── 7. AUTO-COLLAPSE ON MOUSE LEAVE (desktop) ── */
  let hoverTimer;
  sidebar.addEventListener('mouseleave', () => {
    if (!isMobile() && !sidebar.classList.contains('rail')) {
      hoverTimer = setTimeout(() => setSidebarRail(), 1200);
    }
  });
  sidebar.addEventListener('mouseenter', () => {
    clearTimeout(hoverTimer);
    if (!isMobile() && sidebar.classList.contains('rail')) {
      setSidebarExpanded();
    }
  });

  /* ── 8. DRAG TO RESIZE ── */
  let dragging = false;
  let startX, startW;

  resizer.addEventListener('mousedown', e => {
    if (isMobile()) return;
    dragging = true;
    startX = e.clientX;
    startW = sidebar.offsetWidth;
    resizer.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });

  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const delta = e.clientX - startX;
    let newW = Math.max(180, Math.min(480, startW + delta));
    // Snap to rail if dragged very small
    if (newW < 120) {
      setSidebarRail();
      dragging = false;
      return;
    }
    currentW = newW;
    sidebar.style.width = newW + 'px';
    if (mainEl) mainEl.style.marginLeft = newW + 'px';
    resizer.style.left = newW + 'px';
    if (toggleBtn) toggleBtn.style.left = (newW - 13) + 'px';
    document.documentElement.style.setProperty('--sidebar-w', newW + 'px');
    sidebar.classList.remove('rail');
  });

  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    resizer.classList.remove('dragging');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    localStorage.setItem('sidebarW', currentW);
  });

  /* ── 9. RESTORE STATE ── */
  const savedState = localStorage.getItem('sidebarState');
  const savedW     = localStorage.getItem('sidebarW');
  if (!isMobile()) {
    if (savedW) {
      currentW = parseInt(savedW);
      document.documentElement.style.setProperty('--sidebar-w', currentW + 'px');
    }
    if (savedState === 'rail') {
      setSidebarRail();
    } else {
      setSidebarExpanded();
    }
  }

  window.addEventListener('resize', () => {
    if (!isMobile()) {
      overlay.classList.remove('active');
      sidebar.classList.remove('mobile-open');
    }
  });

  /* ── 10. SMOOTH SCROLL ── */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const t = document.querySelector(a.getAttribute('href'));
      if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    });
  });

  /* ── 11. BPMN LIGHTBOX WITH ZOOM + PAN ── */
  function buildLightbox() {
    if (document.getElementById('bpmn-lightbox')) return document.getElementById('bpmn-lightbox');
    const ov = document.createElement('div');
    ov.id = 'bpmn-lightbox';
    ov.innerHTML = `
      <div id="lb-toolbar">
        <span id="lb-title">Process Flow Diagram</span>
        <div id="lb-controls">
          <button id="lb-zoom-in">+</button>
          <button id="lb-zoom-out">&#8722;</button>
          <button id="lb-reset">Reset</button>
          <button id="lb-close">&#10005;</button>
        </div>
      </div>
      <div id="lb-canvas"><img id="lb-img" src="" alt="BPMN" draggable="false"></div>
      <div id="lb-hint">Drag to pan &nbsp;|&nbsp; Scroll to zoom &nbsp;|&nbsp; Esc to close</div>`;
    document.body.appendChild(ov);
    const canvas = document.getElementById('lb-canvas');
    const img    = document.getElementById('lb-img');
    let scale = 1, ox = 0, oy = 0, draggingLB = false, lx = 0, ly = 0;
    const applyT    = () => { img.style.transform = `translate(${ox}px,${oy}px) scale(${scale})`; };
    const resetView = () => { scale=1; ox=0; oy=0; applyT(); };
    const closeLB   = () => { ov.classList.remove('lb-open'); resetView(); };
    document.getElementById('lb-zoom-in').onclick  = () => { scale = Math.min(scale*1.3, 8); applyT(); };
    document.getElementById('lb-zoom-out').onclick = () => { scale = Math.max(scale/1.3, 0.15); applyT(); };
    document.getElementById('lb-reset').onclick    = resetView;
    document.getElementById('lb-close').onclick    = closeLB;
    canvas.addEventListener('wheel', e => { e.preventDefault(); scale = e.deltaY < 0 ? Math.min(scale*1.1,8) : Math.max(scale/1.1,0.15); applyT(); }, {passive:false});
    canvas.addEventListener('mousedown', e => { draggingLB=true; lx=e.clientX; ly=e.clientY; img.style.cursor='grabbing'; });
    document.addEventListener('mousemove', e => { if (!draggingLB) return; ox+=e.clientX-lx; oy+=e.clientY-ly; lx=e.clientX; ly=e.clientY; applyT(); });
    document.addEventListener('mouseup', () => { draggingLB=false; img.style.cursor='grab'; });
    document.addEventListener('keydown', e => { if (e.key==='Escape') closeLB(); });
    ov.addEventListener('click', e => { if (e.target===ov) closeLB(); });
    return ov;
  }

  document.querySelectorAll('.diagram-wrap img').forEach(img => {
    img.style.cursor = 'zoom-in';
    img.addEventListener('click', () => {
      const lb = buildLightbox();
      document.getElementById('lb-img').src = img.src;
      lb.classList.add('lb-open');
    });
  });

  /* ── 12. SEARCH ── */
  const searchBox = document.getElementById('searchBox');
  const resultsEl = document.getElementById('searchResults') || (() => {
    const el = document.createElement('div');
    el.id = 'searchResults';
    el.className = 'search-results';
    el.style.display = 'none';
    document.body.appendChild(el);
    return el;
  })();

  if (searchBox) {
    const links = [...document.querySelectorAll('.sidebar-l3-link')].map(a => ({
      text: a.textContent.trim(), href: a.href
    }));

    searchBox.addEventListener('input', () => {
      const q = searchBox.value.trim().toLowerCase();
      if (!q) { resultsEl.style.display = 'none'; return; }
      const hits = links.filter(l => l.text.toLowerCase().includes(q)).slice(0, 8);
      if (!hits.length) { resultsEl.style.display = 'none'; return; }
      resultsEl.innerHTML = hits.map(h =>
        `<a class="sr-item" href="${h.href}">${h.text}</a>`
      ).join('');
      resultsEl.style.display = 'block';
    });

    document.addEventListener('click', e => {
      if (!searchBox.contains(e.target) && !resultsEl.contains(e.target)) {
        resultsEl.style.display = 'none';
      }
    });

    document.addEventListener('keydown', e => {
      if (e.key === '/' && document.activeElement !== searchBox) {
        e.preventDefault(); searchBox.focus();
      }
      if (e.key === 'Escape') { searchBox.value=''; resultsEl.style.display='none'; searchBox.blur(); }
    });
  }

  /* ── 13. STATUS DOTS ── */
  document.querySelectorAll('.sidebar-l3-link').forEach(link => {
    const dot = link.querySelector('.status-dot');
    if (dot) {
      if (dot.classList.contains('status-done')) dot.title = 'Complete';
      else if (dot.classList.contains('status-wip')) dot.title = 'In Progress';
      else dot.title = 'Queued';
    }
  });

});
