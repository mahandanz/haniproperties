/* ============================================================
   Hani Properties — Area page pagination
   area-pager.js  |  used by every /area/local/*.html and
   /ms/area/*.html page (the build script adds the <script> tag).

   Shows 12 cards per page in each listing grid (#grid-unit,
   #grid-subsale) with ‹ 1 2 3 › buttons under the grid.

   How it works: every card stays in the page (so search engines
   still see the full list); cards outside the current page are
   just hidden. Hidden cards' photos are lazy, so they don't load,
   and lightbox.js only looks for their extra photos once they're
   on screen.

   No changes needed in the page's own filter code: this watches
   each grid and re-paginates (back to page 1) whenever the page
   re-renders it after a filter / tab / search change.

   Links to a unit (#slug, e.g. "View in Area Page" from
   search.html) open the page that unit is on.
   ============================================================ */

(function () {
  const PAGE_SIZE = 12;               // four full rows in the 3-column grid
  const GRID_SELECTOR = '.listing-grid';
  const BM = document.documentElement.lang === 'ms';
  const T = BM
    ? { page: 'Halaman', prev: 'Halaman sebelum', next: 'Halaman seterusnya', of: 'daripada', unit: 'iklan', nav: 'Halaman iklan' }
    : { page: 'Page', prev: 'Previous page', next: 'Next page', of: 'of', unit: 'listings', nav: 'Listing pages' };

  // Follow a #unit link until the visitor starts using filters or pages themselves
  let followHash = true;

  function injectCSS() {
    const style = document.createElement('style');
    style.textContent = `
      .hp-pg-hidden{display:none!important}
      .hp-pager{display:flex;justify-content:center;align-items:center;flex-wrap:wrap;gap:6px;margin:22px 0 8px}
      .hp-pager:empty{display:none}
      .hp-pager-btn{min-width:38px;height:38px;padding:0 12px;font-family:'DM Sans',sans-serif;font-size:13px;font-weight:700;color:#1c1c18;background:#fff;border:1px solid #e3ddd0;border-radius:9px;cursor:pointer;transition:all .15s}
      .hp-pager-btn:hover:not(:disabled):not(.active){border-color:#1B4D35;color:#1B4D35}
      .hp-pager-btn.active{background:#1B4D35;border-color:#1B4D35;color:#fff;cursor:default;opacity:1}
      .hp-pager-btn:disabled:not(.active){opacity:.35;cursor:not-allowed}
      .hp-pager-gap{font-size:13px;color:#7a7268;padding:0 2px}
      @media(max-width:600px){
        .hp-pager{gap:4px;margin-top:18px}
        .hp-pager-btn{min-width:34px;height:34px;padding:0 9px;font-size:12px}
      }`;
    document.head.appendChild(style);
  }

  function cardsOf(grid) {
    return Array.from(grid.children).filter(el => el.classList.contains('card'));
  }

  function hashId() {
    try { return decodeURIComponent(window.location.hash.slice(1)); } catch (e) { return ''; }
  }

  // Page numbers shown: first, last, and current ±1, with "…" for gaps (1 … 4 5 6 … 12)
  function pageList(cur, total) {
    const keep = new Set([1, total, cur - 1, cur, cur + 1]);
    const out = [];
    for (let p = 1; p <= total; p++) {
      if (!keep.has(p)) continue;
      if (out.length && p - out[out.length - 1] > 1) out.push('…');
      out.push(p);
    }
    return out;
  }

  function pagerFor(grid) {
    let pager = grid.nextElementSibling;
    if (!pager || !pager.classList.contains('hp-pager')) {
      pager = document.createElement('div');
      pager.className = 'hp-pager';
      pager.setAttribute('role', 'navigation');
      pager.setAttribute('aria-label', T.nav);
      pager.addEventListener('click', e => {
        const btn = e.target.closest('.hp-pager-btn');
        if (!btn || btn.disabled) return;
        followHash = false;
        paginate(grid, parseInt(btn.dataset.page, 10));
        scrollToGrid(grid);
      });
      grid.parentNode.insertBefore(pager, grid.nextSibling);
    }
    return pager;
  }

  function paginate(grid, page) {
    const cards = cardsOf(grid);
    const n = cards.length;
    const total = Math.max(1, Math.ceil(n / PAGE_SIZE));

    // A #unit link wins over the requested page while it's still being followed
    let hashCard = null;
    if (followHash) {
      const id = hashId();
      const idx = id ? cards.findIndex(c => c.id === id) : -1;
      if (idx >= 0) { page = Math.floor(idx / PAGE_SIZE) + 1; hashCard = cards[idx]; }
    }
    page = Math.min(Math.max(1, page || 1), total);
    grid.dataset.page = page;

    const start = (page - 1) * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, n);
    cards.forEach((c, i) => c.classList.toggle('hp-pg-hidden', i < start || i >= end));

    const pager = pagerFor(grid);
    if (n <= PAGE_SIZE) {
      pager.innerHTML = '';
    } else {
      const btn = (label, p, opts = {}) =>
        `<button type="button" class="hp-pager-btn${opts.active ? ' active' : ''}" data-page="${p}"` +
        `${opts.disabled ? ' disabled' : ''}${opts.active ? ' aria-current="page"' : ''}` +
        ` aria-label="${opts.aria || T.page + ' ' + p}">${label}</button>`;
      let html = btn('‹', page - 1, { disabled: page === 1, aria: T.prev });
      pageList(page, total).forEach(p => {
        html += p === '…'
          ? '<span class="hp-pager-gap">…</span>'
          : btn(p, p, { active: p === page, disabled: p === page });
      });
      html += btn('›', page + 1, { disabled: page === total, aria: T.next });
      pager.innerHTML = html;
    }

    // "25–48 of 130 listings" — only for the grid on the visible tab, and only
    // when there's more than one page (otherwise the page's own count stays).
    const count = document.getElementById('filter-count');
    if (count && n > PAGE_SIZE && grid.offsetParent !== null) {
      count.textContent = `${start + 1}–${end} ${T.of} ${n} ${T.unit}`;
    }

    // The page rebuilds the grid once listings.csv loads, which can move the
    // linked unit after the page's own scroll-to-unit already ran — so bring
    // it back into view (and re-highlight it) after each rebuild.
    if (hashCard && grid.offsetParent !== null) {
      requestAnimationFrame(() => {
        if (!hashCard.isConnected) return;
        hashCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        hashCard.classList.add('card-highlight');
        setTimeout(() => hashCard.classList.remove('card-highlight'), 2800);
      });
    }
  }

  function navOffset() {
    const v = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-offset'), 10);
    if (v) return v;
    const nav = document.querySelector('nav');
    return nav ? nav.offsetHeight : 0;
  }

  function scrollToGrid(grid) {
    const top = grid.getBoundingClientRect().top + window.scrollY - navOffset() - 16;
    window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
  }

  function init() {
    const grids = document.querySelectorAll(GRID_SELECTOR);
    if (!grids.length) return;
    injectCSS();

    // The page rebuilds a grid's cards on every filter/tab/search change → back to page 1
    const observer = new MutationObserver(muts => {
      const touched = new Set(muts.map(m => m.target));
      touched.forEach(grid => paginate(grid, 1));
    });
    grids.forEach(grid => {
      paginate(grid, 1);                       // the build-written (SSR) cards
      observer.observe(grid, { childList: true });
    });

    // Visitor touched a filter or the search box → stop jumping to the #unit's page
    ['change', 'input'].forEach(ev => document.addEventListener(ev, e => {
      if (e.isTrusted && e.target.closest && e.target.closest('select, input')) followHash = false;
    }, true));

    // A new #unit link on the same page → open that unit's page
    window.addEventListener('hashchange', () => {
      followHash = true;
      grids.forEach(grid => paginate(grid, parseInt(grid.dataset.page, 10) || 1));
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
