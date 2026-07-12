/* ============================================================
   Hani Properties — Universal Search
   search.js  |  v2.0 — redirects to /search.html instead of
   showing an inline dropdown (avoids mobile clipping issues)
   ============================================================ */

(function () {
  const RESULTS_PAGE = '/search.html';

  function goToResults(query) {
    const q = (query || '').trim();
    if (!q) return;
    window.location.href = `${RESULTS_PAGE}?q=${encodeURIComponent(q)}`;
  }

  /* ── Inject CSS ─────────────────────────────────────────── */
  function injectCSS() {
    const style = document.createElement('style');
    style.textContent = `
      .hp-search-wrap {
        position: relative;
        display: flex;
        align-items: center;
      }
      .hp-search-input {
        width: 220px;
        padding: 7px 14px 7px 34px;
        border: 1.5px solid #d4cfc6;
        border-radius: 20px;
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        color: #1c1c18;
        background: #f9f6f0 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%237a7268' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E") no-repeat 10px center;
        outline: none;
        transition: border-color .18s, width .2s;
      }
      .hp-search-input:focus {
        border-color: #2a5c3a;
        width: 260px;
        background-color: #fff;
      }
      .hp-search-input::placeholder { color: #a89f94; }

      .hp-search-go {
        position: absolute;
        left: 8px;
        top: 50%;
        transform: translateY(-50%);
        width: 20px;
        height: 20px;
        border: none;
        background: transparent;
        cursor: pointer;
        padding: 0;
      }

      /* Mobile search — full width below nav.
         Hidden by default; only shown at mobile widths, so it
         doesn't render alongside the desktop nav-links search box. */
      .nav-search-mobile { display: none; }
      @media (max-width: 600px) {
        .hp-search-wrap { width: 100%; }
        .hp-search-input { width: 100% !important; border-radius: 10px; }
        .nav-search-mobile {
          display: block;
          padding: 8px 16px;
          background: rgba(253,250,245,.97);
          border-bottom: 1px solid #e3ddd0;
        }
      }
    `;
    document.head.appendChild(style);
  }

  /* ── Build one search box (icon button + input) ─────────── */
  function buildSearchBox() {
    const wrap = document.createElement('div');
    wrap.className = 'hp-search-wrap';

    const searchBox = document.createElement('input');
    searchBox.type = 'search';
    searchBox.className = 'hp-search-input';
    searchBox.placeholder = 'Search listings…';
    searchBox.autocomplete = 'off';

    // Clickable search icon button (sits on top of the input's bg icon)
    const goBtn = document.createElement('button');
    goBtn.type = 'button';
    goBtn.className = 'hp-search-go';
    goBtn.setAttribute('aria-label', 'Search');

    wrap.appendChild(searchBox);
    wrap.appendChild(goBtn);

    searchBox.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') goToResults(searchBox.value);
    });
    goBtn.addEventListener('click', () => goToResults(searchBox.value));

    return wrap;
  }

  /* ── Inject search bar into nav ─────────────────────────── */
  function injectSearch() {
    // Skip entirely on pages that already have their own dedicated
    // search UI (e.g. search.html's hero search box) — avoids a
    // duplicate search bar on that page.
    if (document.querySelector('.hero-search-input')) return;

    // Desktop — append into nav-links (falls back gracefully if
    // a .cta-nav element isn't present, since WhatsApp is now a
    // separate floating button rather than a nav link)
    const navLinks = document.querySelector('.nav-links');
    if (navLinks) {
      const cta = navLinks.querySelector('.cta-nav');
      const wrap = buildSearchBox();
      navLinks.insertBefore(wrap, cta);
    }

    // Mobile — inject a search row below nav-mobile
    const navMobile = document.querySelector('.nav-mobile');
    if (navMobile) {
      const mobileRow = document.createElement('div');
      mobileRow.className = 'nav-search-mobile';
      const mobileWrap = buildSearchBox();
      mobileRow.appendChild(mobileWrap);
      navMobile.parentNode.insertBefore(mobileRow, navMobile.nextSibling);
    }
  }

  /* ── Init ───────────────────────────────────────────────── */
  function init() {
    injectCSS();
    injectSearch();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();