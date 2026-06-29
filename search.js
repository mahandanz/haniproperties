/* ============================================================
   Hani Properties — Universal Search
   search.js  |  v1.0
   ============================================================ */

(function () {
  const CSV_URL = '/listings.csv';
  const BASE = '/area/local/';
  const AREA_MAP = {
    'ampang': BASE + 'ampang.html',
    'bandar saujana putra': BASE + 'bandar-saujana-putra.html',
    'bangi': BASE + 'bangi.html',
    'bukit jalil': BASE + 'bukit-jalil.html',
    'cheras': BASE + 'cheras.html',
    'cyberjaya / putrajaya': BASE + 'cyberjaya.html',
    'kajang': BASE + 'kajang.html',
    'kepong': BASE + 'kepong.html',
    'klang': BASE + 'klang.html',
    'kuala lumpur': BASE + 'kuala-lumpur.html',
    'kuala selangor': BASE + 'kuala-selangor.html',
    'langkawi': BASE + 'langkawi.html',
    'nilai': BASE + 'nilai.html',
    'petaling jaya / damansara': BASE + 'petaling-jaya.html',
    'puchong': BASE + 'puchong.html',
    'puncak alam': BASE + 'puncak-alam.html',
    'rawang': BASE + 'rawang.html',
    'selayang': BASE + 'selayang.html',
    'semenyih': BASE + 'semenyih.html',
    'sentul': BASE + 'sentul.html',
    'sepang': BASE + 'sepang.html',
    'seri kembangan': BASE + 'seri-kembangan.html',
    'setapak': BASE + 'setapak.html',
    'shah alam': BASE + 'shah-alam.html',
    'subang jaya': BASE + 'subang-jaya.html',
    'sungai buloh': BASE + 'sungai-buloh.html',
    'selangor': '/kawasan.html',
  };

  let allListings = [];
  let searchBox, dropdown;

  /* ── Parse CSV (latin-1 safe via fetch) ─────────────────── */
  async function loadCSV() {
    try {
      const res = await fetch(CSV_URL);
      const buf = await res.arrayBuffer();
      const text = new TextDecoder('windows-1252').decode(buf);
      const lines = text.split(/\r?\n/).filter(Boolean);
      const headers = lines[0].split(',').map(h => h.trim().toLowerCase());

      allListings = lines.slice(1).map(line => {
        // Handle quoted fields
        const cols = [];
        let cur = '', inQ = false;
        for (let i = 0; i < line.length; i++) {
          const ch = line[i];
          if (ch === '"') { inQ = !inQ; continue; }
          if (ch === ',' && !inQ) { cols.push(cur); cur = ''; continue; }
          cur += ch;
        }
        cols.push(cur);
        const obj = {};
        headers.forEach((h, i) => obj[h] = (cols[i] || '').trim());
        return obj;
      }).filter(r => r.listing_type && r.area);
    } catch (e) {
      console.warn('Hani Search: could not load listings.csv', e);
    }
  }

  /* ── Slug generator (must match area page logic) ─────────── */
  function toSlug(...parts) {
    return parts.filter(Boolean).join('-')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }

  /* ── Search logic ───────────────────────────────────────── */
  function search(query) {
    if (!query || query.length < 2) return [];
    const q = query.toLowerCase();
    const tokens = q.split(/\s+/);

    return allListings
      .filter(r => {
        // skip rented/sold
        if (r.status && r.status !== '-' && r.status !== '') return false;
        const haystack = [
          r.listing_type, r.area, r.zone, r.project_name,
          r.type, r.furnishing, r.price, r.bed, r.size, r.anchors
        ].join(' ').toLowerCase();
        return tokens.every(t => haystack.includes(t));
      })
      .slice(0, 8);
  }

  /* ── Format price ───────────────────────────────────────── */
  function formatPrice(listing) {
    const p = listing.price;
    if (!p || p === '-') return '';
    const num = parseFloat(p.toString().replace(/[^0-9.]/g, ''));
    if (isNaN(num)) return '';
    if (listing.listing_type === 'rental' || listing.listing_type === 'room') {
      return `RM ${num.toLocaleString()}/mo`;
    }
    if (num >= 1000000) return `RM ${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `RM ${(num / 1000).toFixed(0)}K`;
    return `RM ${num.toLocaleString()}`;
  }

  /* ── Badge label ────────────────────────────────────────── */
  function badge(listing) {
    const t = listing.listing_type;
    if (t === 'rental') return { label: 'Rent', color: '#1a4c8f' };
    if (t === 'room') return { label: 'Room', color: '#7b3fa0' };
    return { label: 'Sale', color: '#2a5c3a' };
  }

  /* ── Render dropdown ────────────────────────────────────── */
  function renderDropdown(results, query) {
    dropdown.innerHTML = '';
    if (!results.length) {
      dropdown.innerHTML = `<div class="hp-sd-empty">No listings found for "<strong>${query}</strong>"</div>`;
      dropdown.style.display = 'block';
      return;
    }

    results.forEach(r => {
      const b = badge(r);
      const price = formatPrice(r);
      const areaKey = (r.area || '').toLowerCase();
      const href = AREA_MAP[areaKey] || 'kawasan.html';
      const slugPart2 = r.listing_type === 'room' ? r.room_type : r.bed;
      const slug = toSlug(r.project_name, slugPart2, r.price);
      const bed = r.bed ? `${r.bed}BR` : '';
      const size = r.size ? `${r.size} sqft` : '';
      const meta = [bed, size, r.furnishing].filter(Boolean).join(' · ');

      const item = document.createElement('a');
      item.className = 'hp-sd-item';
      const tabParam = r.listing_type === 'subsale' ? 'jual' : r.listing_type === 'room' ? 'room' : 'sewa';
      item.href = `${href}?tab=${tabParam}#${slug}`;
      item.innerHTML = `
        <span class="hp-sd-badge" style="background:${b.color}">${b.label}</span>
        <span class="hp-sd-info">
          <span class="hp-sd-name">${r.project_name || r.area}</span>
          <span class="hp-sd-meta">${r.area}${meta ? ' · ' + meta : ''}</span>
        </span>
        <span class="hp-sd-price">${price}</span>
      `;
      dropdown.appendChild(item);
    });

    // Footer
    const footer = document.createElement('div');
    footer.className = 'hp-sd-footer';
    footer.innerHTML = `${results.length} result${results.length > 1 ? 's' : ''} · <a href="/search.html?q=${encodeURIComponent(query)}" style="color:#2a5c3a;font-weight:700;text-decoration:none;">View all results →</a>`;
    dropdown.appendChild(footer);

    dropdown.style.display = 'block';
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

      .hp-search-dropdown {
        display: none;
        position: absolute;
        top: calc(100% + 6px);
        right: 0;
        width: 340px;
        background: #fff;
        border: 1px solid #e3ddd0;
        border-radius: 14px;
        box-shadow: 0 8px 32px rgba(0,0,0,.13);
        overflow: hidden;
        z-index: 999;
      }
      .hp-sd-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        text-decoration: none;
        border-bottom: 1px solid #f0ece4;
        transition: background .13s;
      }
      .hp-sd-item:last-of-type { border-bottom: none; }
      .hp-sd-item:hover { background: #f6f1e7; }
      .hp-sd-badge {
        flex-shrink: 0;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .06em;
        color: #fff;
        padding: 3px 7px;
        border-radius: 10px;
        text-transform: uppercase;
      }
      .hp-sd-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
      }
      .hp-sd-name {
        font-size: 13px;
        font-weight: 600;
        color: #1c1c18;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .hp-sd-meta {
        font-size: 11px;
        color: #7a7268;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .hp-sd-price {
        flex-shrink: 0;
        font-size: 12px;
        font-weight: 700;
        color: #2a5c3a;
      }
      .hp-sd-empty {
        padding: 16px 14px;
        font-size: 13px;
        color: #7a7268;
      }
      .hp-sd-footer {
        padding: 8px 14px;
        font-size: 11px;
        color: #a89f94;
        background: #faf9f6;
        border-top: 1px solid #e3ddd0;
        text-align: center;
      }

      /* Mobile search — full width below nav */
      @media (max-width: 600px) {
        .hp-search-wrap { width: 100%; }
        .hp-search-input { width: 100% !important; border-radius: 10px; }
        .hp-search-dropdown { width: 100%; right: 0; left: 0; border-radius: 10px; }
        .nav-search-mobile {
          padding: 8px 16px;
          background: rgba(253,250,245,.97);
          border-bottom: 1px solid #e3ddd0;
        }
      }
    `;
    document.head.appendChild(style);
  }

  /* ── Inject search bar into nav ─────────────────────────── */
  function injectSearch() {
    const wrap = document.createElement('div');
    wrap.className = 'hp-search-wrap';

    searchBox = document.createElement('input');
    searchBox.type = 'search';
    searchBox.className = 'hp-search-input';
    searchBox.placeholder = 'Search listings…';
    searchBox.autocomplete = 'off';

    dropdown = document.createElement('div');
    dropdown.className = 'hp-search-dropdown';

    wrap.appendChild(searchBox);
    wrap.appendChild(dropdown);

    // Desktop — insert before WhatsApp CTA in nav-links
    const navLinks = document.querySelector('.nav-links');
    if (navLinks) {
      const cta = navLinks.querySelector('.cta-nav');
      navLinks.insertBefore(wrap, cta);
    }

    // Mobile — inject a search row below nav-mobile
    const navMobile = document.querySelector('.nav-mobile');
    if (navMobile) {
      const mobileRow = document.createElement('div');
      mobileRow.className = 'nav-search-mobile';
      const mobileWrap = wrap.cloneNode(true); // clone for mobile
      // Re-query elements in clone
      const mSearchBox = mobileWrap.querySelector('.hp-search-input');
      const mDropdown = mobileWrap.querySelector('.hp-search-dropdown');

      mSearchBox.addEventListener('input', () => {
        const q = mSearchBox.value.trim();
        const results = search(q);
        if (q.length < 2) { mDropdown.style.display = 'none'; return; }
        renderDropdownEl(mDropdown, results, q);
      });

      mobileRow.appendChild(mobileWrap);
      navMobile.parentNode.insertBefore(mobileRow, navMobile.nextSibling);
    }

    // Events for desktop
    searchBox.addEventListener('input', () => {
      const q = searchBox.value.trim();
      const results = search(q);
      if (q.length < 2) { dropdown.style.display = 'none'; return; }
      renderDropdown(results, q);
    });

    searchBox.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = searchBox.value.trim();
        if (q) window.location.href = `/search.html?q=${encodeURIComponent(q)}`;
      }
    });

    document.addEventListener('click', (e) => {
      if (!wrap.contains(e.target)) dropdown.style.display = 'none';
    });
  }

  /* ── Generic renderDropdown for a specific element ──────── */
  function renderDropdownEl(el, results, query) {
    el.innerHTML = '';
    if (!results.length) {
      el.innerHTML = `<div class="hp-sd-empty">No listings found for "<strong>${query}</strong>"</div>`;
      el.style.display = 'block';
      return;
    }
    results.forEach(r => {
      const b = badge(r);
      const price = formatPrice(r);
      const areaKey = (r.area || '').toLowerCase();
      const href = AREA_MAP[areaKey] || 'kawasan.html';
      const slugPart2 = r.listing_type === 'room' ? r.room_type : r.bed;
      const slug = toSlug(r.project_name, slugPart2, r.price);
      const bed = r.bed ? `${r.bed}BR` : '';
      const size = r.size ? `${r.size} sqft` : '';
      const meta = [bed, size, r.furnishing].filter(Boolean).join(' · ');

      const item = document.createElement('a');
      item.className = 'hp-sd-item';
      const tabParam = r.listing_type === 'subsale' ? 'jual' : r.listing_type === 'room' ? 'room' : 'sewa';
      item.href = `${href}?tab=${tabParam}#${slug}`;
      item.innerHTML = `
        <span class="hp-sd-badge" style="background:${b.color}">${b.label}</span>
        <span class="hp-sd-info">
          <span class="hp-sd-name">${r.project_name || r.area}</span>
          <span class="hp-sd-meta">${r.area}${meta ? ' · ' + meta : ''}</span>
        </span>
        <span class="hp-sd-price">${price}</span>
      `;
      el.appendChild(item);
    });
    const footer = document.createElement('div');
    footer.className = 'hp-sd-footer';
    footer.textContent = `${results.length} result${results.length > 1 ? 's' : ''} — click to view area listings`;
    el.appendChild(footer);
    el.style.display = 'block';
  }

  /* ── Init ───────────────────────────────────────────────── */
  async function init() {
    injectCSS();
    injectSearch();
    await loadCSV();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
