/* ============================================================
   Hani Properties — Universal Search
   search.js  |  v3.0 — free-text box removed. The nav now shows a
   "Search listings" button that opens /search.html, where
   visitors use the filters.
   ============================================================ */

(function () {
  const RESULTS_PAGE = '/search.html';

  /* ── Inject CSS ─────────────────────────────────────────── */
  function injectCSS() {
    const style = document.createElement('style');
    style.textContent = `
      .hp-search-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 16px 7px 12px;
        border: 1.5px solid #d4cfc6;
        border-radius: 20px;
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        color: #1c1c18;
        background: #f9f6f0;
        text-decoration: none;
        white-space: nowrap;
        transition: border-color .18s, background-color .18s;
      }
      .hp-search-btn:hover,
      .hp-search-btn:focus-visible {
        border-color: #2a5c3a;
        background-color: #fff;
        outline: none;
      }
      .hp-search-btn svg { flex-shrink: 0; }

      /* Mobile search row — full width below nav.
         Hidden by default; only shown at mobile widths, so it
         doesn't render alongside the desktop nav-links button. */
      .nav-search-mobile { display: none; }
      @media (max-width: 600px) {
        .nav-search-mobile {
          display: block;
          padding: 8px 16px;
          background: rgba(253,250,245,.97);
          border-bottom: 1px solid #e3ddd0;
        }
        .nav-search-mobile .hp-search-btn {
          display: flex;
          width: 100%;
          box-sizing: border-box;
          justify-content: center;
          border-radius: 10px;
        }
      }
    `;
    document.head.appendChild(style);
  }

  /* ── Build one search button (links to the filters page) ── */
  function buildSearchButton() {
    const link = document.createElement('a');
    link.className = 'hp-search-btn';
    link.href = RESULTS_PAGE;
    link.setAttribute('aria-label', 'Search listings');
    link.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7a7268" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' +
      '<span>Search listings</span>';
    return link;
  }

  /* ── Inject search button into nav ──────────────────────── */
  function injectSearch() {
    // Skip on the search page itself — visitors are already on
    // the filters, so a button pointing back to it is redundant.
    const path = window.location.pathname.replace(/\/+$/, '');
    if (path === '/search.html' || path === '/search') return;

    // Desktop — append into nav-links (falls back gracefully if
    // a .cta-nav element isn't present, since WhatsApp is now a
    // separate floating button rather than a nav link)
    const navLinks = document.querySelector('.nav-links');
    if (navLinks) {
      const cta = navLinks.querySelector('.cta-nav');
      navLinks.insertBefore(buildSearchButton(), cta);
    }

    // Mobile — inject a search row below nav-mobile
    const navMobile = document.querySelector('.nav-mobile');
    if (navMobile) {
      const mobileRow = document.createElement('div');
      mobileRow.className = 'nav-search-mobile';
      mobileRow.appendChild(buildSearchButton());
      navMobile.parentNode.insertBefore(mobileRow, navMobile.nextSibling);
    }
  }

  /* ── Keep --nav-offset in sync with the *actual* nav height ──
     nav is position:fixed, so it doesn't push content down by
     itself. Anything meant to sit just below it (e.g. .hero)
     should use margin-top:var(--nav-offset) rather than a
     hardcoded px value, so it stays correct even after this
     script adds the extra mobile search row. */
  function updateNavOffset() {
    const nav = document.querySelector('nav');
    if (!nav) return;
    document.documentElement.style.setProperty('--nav-offset', nav.offsetHeight + 'px');
  }

  /* ── Init ───────────────────────────────────────────────── */
  function init() {
    injectCSS();
    injectSearch();
    updateNavOffset();
    window.addEventListener('resize', updateNavOffset);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
