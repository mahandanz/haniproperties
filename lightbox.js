/* ── Shared lightbox / card image carousel ─────────────────────────
   Used by search.html and every /area/local/*.html page.
   Include with: <script src="/lightbox.js"></script>
   No other setup needed — the overlay markup is injected automatically.

   Clicking a card's photo opens a popup with the enlarged photo carousel
   PLUS the rest of that listing's details (name, price, pills, anchors,
   WhatsApp button) — i.e. the whole card, not just the picture. */

// Inject the lightbox overlay markup once, so no page needs to hand-code it in HTML.
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('lightboxOverlay')) return; // already present, don't duplicate
  const overlay = document.createElement('div');
  overlay.className = 'lightbox-overlay';
  overlay.id = 'lightboxOverlay';
  overlay.setAttribute('onclick', 'closeLightbox()');
  overlay.innerHTML = `
  <div class="lightbox-card" onclick="event.stopPropagation()">
    <button type="button" class="lightbox-close" onclick="closeLightbox()" aria-label="Close">&times;</button>
    <div class="lightbox-img-wrap">
      <img id="lightboxImg" src="" alt="Property photo">
      <div id="lightboxNavWrap"></div>
    </div>
    <div class="lightbox-details" id="lightboxDetails"></div>
  </div>`;
  document.body.appendChild(overlay);
});

function cardImage(r) {
  const raw = (r.image || '').trim();
  let imgs = [];
  if (raw && raw !== '-') {
    let base = '';
    imgs = raw.split('|').map(s => s.trim()).filter(Boolean).map(p => {
      if (/^https?:\/\//i.test(p)) {
        base = p.substring(0, p.lastIndexOf('/') + 1);
        return p;
      }
      return base ? base + p : p;
    });
  }
  const canScan = imgs.length > 0; // '-'/empty stays on the placeholder, nothing to scan
  if (imgs.length === 0) imgs = ['/images/update.png'];
  const nav = imgs.length > 1 ? cardNavHTML(imgs, 0) : '';
  return `<div class="card-image-wrap" data-images="${imgs.join('|')}" data-index="0"${canScan ? ' data-auto-scan="1"' : ''}>
    <img src="${imgs[0]}" alt="${r.project_name}" class="card-image" loading="lazy" onerror="this.onerror=null;this.src='/images/update.png';" onclick="openLightbox(event,this)">
    <div class="card-tap-hint">🔍 Full details</div>${nav}
  </div>`;
}

function cardNavHTML(imgs, activeIdx) {
  return `
    <button type="button" class="card-img-nav prev" onclick="cardImgNav(event,this,-1)" aria-label="Previous photo">‹</button>
    <button type="button" class="card-img-nav next" onclick="cardImgNav(event,this,1)" aria-label="Next photo">›</button>
    <div class="card-img-dots">${imgs.map((_, i) => `<span class="card-img-dot${i === activeIdx ? ' active' : ''}"></span>`).join('')}</div>`;
}

// ── Auto-discover extra photos already sitting in the listing's folder ──
// The sheet only lists one filename per listing (e.g. ".../pic1.jpg"), but
// the actual folder may hold pic2.jpg, pic3.jpg, etc. that were never typed
// in. Rather than requiring manual pipe-separated entry, probe the folder
// for the next few numbered files (via Image() so it isn't blocked by
// cross-origin fetch/CORS restrictions) and fold in whatever exists.
const PHOTO_SCAN_MAX = 20; // stop scanning after this many extra photos

function parsePhotoPattern(url) {
  const m = url.match(/^(.*?)(\d+)(\.[a-z0-9]+)$/i);
  if (!m) return null;
  return { prefix: m[1], num: m[2], ext: m[3] };
}

function photoUrlForNum(pattern, n) {
  let numStr = String(n);
  if (pattern.num.length > 1 && pattern.num[0] === '0') numStr = numStr.padStart(pattern.num.length, '0');
  return pattern.prefix + numStr + pattern.ext;
}

function probeImageExists(url) {
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => resolve(true);
    img.onerror = () => resolve(false);
    img.src = url;
  });
}

async function autoDiscoverPhotos(wrap) {
  const current = (wrap.getAttribute('data-images') || '').split('|').filter(Boolean);
  const last = current[current.length - 1];
  const pattern = last ? parsePhotoPattern(last) : null;
  if (!pattern) return;
  const startN = parseInt(pattern.num, 10) + 1;
  const found = current.slice();
  for (let n = startN; n < startN + PHOTO_SCAN_MAX; n++) {
    const ok = await probeImageExists(photoUrlForNum(pattern, n));
    if (!ok) break;
    found.push(photoUrlForNum(pattern, n));
  }
  if (found.length > current.length) {
    wrap.setAttribute('data-images', found.join('|'));
    let dots = wrap.querySelector('.card-img-dots');
    if (!dots) {
      wrap.insertAdjacentHTML('beforeend', cardNavHTML(found, parseInt(wrap.getAttribute('data-index'), 10) || 0));
    } else {
      dots.innerHTML = found.map((_, i) => `<span class="card-img-dot${i === 0 ? ' active' : ''}"></span>`).join('');
    }
  }
}

function scanForAutoDiscovery(root) {
  (root || document).querySelectorAll('.card-image-wrap[data-auto-scan="1"]').forEach(wrap => {
    wrap.removeAttribute('data-auto-scan');
    autoDiscoverPhotos(wrap);
  });
}

(function () {
  const observer = new MutationObserver(mutations => {
    for (const m of mutations) {
      m.addedNodes.forEach(node => {
        if (node.nodeType !== 1) return;
        if (node.matches && node.matches('.card-image-wrap[data-auto-scan="1"]')) {
          node.removeAttribute('data-auto-scan');
          autoDiscoverPhotos(node);
        } else if (node.querySelectorAll) {
          scanForAutoDiscovery(node);
        }
      });
    }
  });
  document.addEventListener('DOMContentLoaded', () => {
    observer.observe(document.body, { childList: true, subtree: true });
    scanForAutoDiscovery(document);
  });
})();

function cardImgNav(e, btn, dir) {
  e.preventDefault();
  e.stopPropagation();
  navCardImages(btn.closest('.card-image-wrap'), dir);
}

function navCardImages(wrap, dir) {
  if (!wrap) return;
  const imgs = wrap.getAttribute('data-images').split('|');
  if (imgs.length < 2) return;
  let idx = parseInt(wrap.getAttribute('data-index'), 10) || 0;
  idx = (idx + dir + imgs.length) % imgs.length;
  wrap.setAttribute('data-index', idx);
  const cardImgEl = wrap.querySelector('.card-image');
  cardImgEl.onerror = function() { this.onerror = null; this.src = '/images/update.png'; };
  cardImgEl.src = imgs[idx];
  wrap.querySelectorAll('.card-img-dot').forEach((d, i) => d.classList.toggle('active', i === idx));
}

let lbImgs = [];
let lbIdx = 0;

function openLightbox(e, img) {
  e.preventDefault();
  e.stopPropagation();
  const wrap = img.closest('.card-image-wrap');
  lbImgs = wrap.getAttribute('data-images').split('|');
  lbIdx = parseInt(wrap.getAttribute('data-index'), 10) || 0;
  renderLightbox();

  // Clone the rest of this listing's card (badges, name, price, pills, anchors, CTA)
  // into the popup so it shows the whole card, not just the photo.
  const card = img.closest('.card');
  const body = card ? card.querySelector('.card-body') : null;
  const detailsEl = document.getElementById('lightboxDetails');
  if (detailsEl) detailsEl.innerHTML = body ? body.innerHTML : '';

  document.getElementById('lightboxOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  document.getElementById('lightboxOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function lbNav(dir) {
  lbIdx = (lbIdx + dir + lbImgs.length) % lbImgs.length;
  renderLightbox();
}

function renderLightbox() {
  const lbImgEl = document.getElementById('lightboxImg');
  lbImgEl.onerror = function() { this.onerror = null; this.src = '/images/update.png'; };
  lbImgEl.src = lbImgs[lbIdx];
  const nav = lbImgs.length > 1 ? `
    <button type="button" class="lightbox-nav prev" onclick="event.stopPropagation();lbNav(-1)" aria-label="Previous photo">‹</button>
    <button type="button" class="lightbox-nav next" onclick="event.stopPropagation();lbNav(1)" aria-label="Next photo">›</button>
    <div class="lightbox-dots">${lbImgs.map((_, i) => `<span class="lightbox-dot${i === lbIdx ? ' active' : ''}" onclick="event.stopPropagation();lbIdx=${i};renderLightbox()"></span>`).join('')}</div>` : '';
  document.getElementById('lightboxNavWrap').innerHTML = nav;
}

document.addEventListener('keydown', (e) => {
  const overlay = document.getElementById('lightboxOverlay');
  if (!overlay || !overlay.classList.contains('open')) return;
  if (e.key === 'Escape') closeLightbox();
  if (e.key === 'ArrowLeft') lbNav(-1);
  if (e.key === 'ArrowRight') lbNav(1);
});

// ── Swipe (touch) support ───────────────────────────────────────────
// Lets a finger-drag left/right move between photos, both on the small
// card thumbnail and on the enlarged popup photo. Vertical drags (e.g.
// scrolling the popup's details) are ignored so they don't get mistaken
// for a photo swipe.
(function () {
  const SWIPE_MIN = 40;   // px of horizontal movement to count as a swipe
  const SWIPE_SLOP = 60;  // max px of vertical drift still allowed

  let startX = 0, startY = 0, swipeWrap = null;

  document.addEventListener('touchstart', (e) => {
    const wrap = e.target.closest('.card-image-wrap, .lightbox-img-wrap');
    if (!wrap || !e.changedTouches || !e.changedTouches.length) { swipeWrap = null; return; }
    swipeWrap = wrap;
    startX = e.changedTouches[0].clientX;
    startY = e.changedTouches[0].clientY;
  }, { passive: true });

  document.addEventListener('touchend', (e) => {
    if (!swipeWrap || !e.changedTouches || !e.changedTouches.length) return;
    const wrap = swipeWrap;
    swipeWrap = null;
    const dx = e.changedTouches[0].clientX - startX;
    const dy = e.changedTouches[0].clientY - startY;
    if (Math.abs(dx) < SWIPE_MIN || Math.abs(dy) > SWIPE_SLOP) return;
    const dir = dx < 0 ? 1 : -1;
    if (wrap.classList.contains('lightbox-img-wrap')) {
      if (lbImgs.length > 1) lbNav(dir);
    } else {
      navCardImages(wrap, dir);
    }
  }, { passive: true });
})();
