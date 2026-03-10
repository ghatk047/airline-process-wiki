/* Airlines Process Wiki JS v2 — lightbox + search + collapsible sidebar */
document.addEventListener('DOMContentLoaded', () => {

  /* 1. SIDEBAR ACCORDION */
  document.querySelectorAll('.sidebar-domain').forEach(el => {
    el.addEventListener('click', () => {
      el.classList.toggle('open');
      const l2 = el.nextElementSibling;
      if (l2) l2.classList.toggle('open');
    });
  });
  const active = document.querySelector('.sidebar-l3-link.active');
  if (active) {
    let p = active.closest('.sidebar-l2');
    if (p) { p.classList.add('open'); const d = p.previousElementSibling; if (d) d.classList.add('open'); }
  }

  /* 2. COLLAPSIBLE SIDEBAR */
  const sidebar   = document.getElementById('sidebar');
  const mainEl    = document.querySelector('.main');
  const toggleBtn = document.getElementById('sidebar-toggle');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      const collapsed = sidebar.classList.toggle('sidebar-collapsed');
      if (mainEl) mainEl.classList.toggle('main-expanded', collapsed);
      toggleBtn.title   = collapsed ? 'Show sidebar' : 'Hide sidebar';
      toggleBtn.innerHTML = collapsed ? '&#9654;' : '&#9664;';
    });
  }

  /* 3. SMOOTH SCROLL */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const t = document.querySelector(a.getAttribute('href'));
      if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    });
  });

  /* 4. BPMN LIGHTBOX WITH ZOOM + PAN */
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
    let scale = 1, ox = 0, oy = 0, dragging = false, lx = 0, ly = 0;
    const applyT   = () => { img.style.transform = `translate(${ox}px,${oy}px) scale(${scale})`; };
    const resetView = () => { scale=1; ox=0; oy=0; applyT(); };
    const closeLB   = () => { ov.classList.remove('lb-open'); resetView(); };
    document.getElementById('lb-zoom-in').onclick  = () => { scale = Math.min(scale*1.3, 8); applyT(); };
    document.getElementById('lb-zoom-out').onclick = () => { scale = Math.max(scale/1.3, 0.15); applyT(); };
    document.getElementById('lb-reset').onclick    = resetView;
    document.getElementById('lb-close').onclick    = closeLB;
    ov.addEventListener('click', e => { if (e.target === ov) closeLB(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLB(); });
    canvas.addEventListener('wheel', e => {
      e.preventDefault();
      scale = Math.max(0.15, Math.min(8, scale * (e.deltaY > 0 ? 0.85 : 1.18)));
      applyT();
    }, { passive: false });
    canvas.addEventListener('mousedown', e => { dragging=true; lx=e.clientX; ly=e.clientY; canvas.style.cursor='grabbing'; });
    document.addEventListener('mousemove', e => {
      if (!dragging) return;
      ox += e.clientX-lx; oy += e.clientY-ly; lx=e.clientX; ly=e.clientY; applyT();
    });
    document.addEventListener('mouseup', () => { dragging=false; canvas.style.cursor='grab'; });
    return ov;
  }

  document.querySelectorAll('.diagram-wrap img').forEach(img => {
    img.style.cursor = 'zoom-in';
    img.title = 'Click to expand and zoom';
    img.addEventListener('click', () => {
      const lb = buildLightbox();
      document.getElementById('lb-img').src = img.src;
      lb.classList.add('lb-open');
    });
  });

  /* 5. SEARCH */
  const idx = [];
  document.querySelectorAll('.sidebar-l3-link').forEach(link => {
    const pid  = link.querySelector('.pid')?.textContent?.trim() || '';
    const name = link.textContent.replace(pid, '').trim();
    idx.push({ pid, name, url: link.href, type: 'process', text: (pid+' '+name).toLowerCase() });
  });
  document.querySelectorAll('tbody tr').forEach(row => {
    const c = row.querySelectorAll('td');
    if (c.length < 3) return;
    const step=c[0]?.textContent?.trim(), name=c[1]?.textContent?.trim(), role=c[2]?.textContent?.trim();
    if (!name) return;
    idx.push({ pid:step, name, role, url:window.location.href.split('#')[0], type:'step', text:(step+' '+name+' '+role).toLowerCase() });
  });

  const topR = document.querySelector('.topbar-right');
  if (topR) {
    const wrap = document.createElement('div');
    wrap.id = 'search-wrap';
    wrap.innerHTML = `
      <div id="search-box">
        <span id="search-icon">&#128269;</span>
        <input id="search-input" type="text" placeholder="Search processes, steps... (or press /)" autocomplete="off">
        <button id="search-clear">&#10005;</button>
      </div>
      <div id="search-results"></div>`;
    topR.insertBefore(wrap, topR.firstChild);

    const inp = document.getElementById('search-input');
    const res = document.getElementById('search-results');

    const doSearch = q => {
      q = q.trim().toLowerCase(); res.innerHTML = '';
      if (q.length < 2) { res.classList.remove('open'); return; }
      const tokens = q.split(/\s+/);
      const hits = idx.filter(i => tokens.every(t => i.text.includes(t))).slice(0, 12);
      if (!hits.length) { res.innerHTML = '<div class="sr-empty">No results found</div>'; res.classList.add('open'); return; }
      hits.forEach(m => {
        const d = document.createElement('div'); d.className = 'sr-item';
        d.innerHTML = `<span class="sr-type ${m.type==='process'?'sr-proc':'sr-step'}">${m.type==='process'?'Process':'Step'}</span><span class="sr-pid">${m.pid}</span><span class="sr-name">${m.name}</span>${m.role?`<span class="sr-role">${m.role}</span>`:''}`;
        d.onclick = () => { window.location.href = m.url; res.classList.remove('open'); };
        res.appendChild(d);
      });
      res.classList.add('open');
    };

    inp.addEventListener('input', e => doSearch(e.target.value));
    inp.addEventListener('keydown', e => { if (e.key==='Escape') { res.classList.remove('open'); inp.value=''; } });
    document.getElementById('search-clear').onclick = () => { inp.value=''; res.classList.remove('open'); inp.focus(); };
    document.addEventListener('click', e => { if (!wrap.contains(e.target)) res.classList.remove('open'); });
    document.addEventListener('keydown', e => {
      if ((e.metaKey||e.ctrlKey) && e.key==='k') { e.preventDefault(); inp.focus(); inp.select(); }
      if (e.key==='/' && document.activeElement.tagName !== 'INPUT') { e.preventDefault(); inp.focus(); }
    });
  }

});
