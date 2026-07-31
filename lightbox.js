/* ── Shared lightbox / card image carousel ─────────────────────────
   Used by search.html and every /area/local/*.html page.
   Include with: <script src="/lightbox.js"></script>
   No other setup needed — the overlay markup is injected automatically. */

// Inject the lightbox overlay markup once, so no page needs to hand-code it in HTML.
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('lightboxOverlay')) return; // already present, don't duplicate
  const overlay = document.createElement('div');
  overlay.className = 'lightbox-overlay';
  overlay.id = 'lightboxOverlay';
  overlay.setAttribute('onclick', 'closeLightbox()');
  overlay.innerHTML = `
  <div class="lightbox-img-wrap" onclick="event.stopPropagation()">
    <button type="button" class="lightbox-close" onclick="closeLightbox()" aria-label="Close">&times;</button>
    <img id="lightboxImg" src="" alt="Property photo">
    <div id="lightboxNavWrap"></div>
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
  if (imgs.length === 0) imgs = ['/images/update.png'];
  const nav = imgs.length > 1 ? `
    <button type="button" class="card-img-nav prev" onclick="cardImgNav(event,this,-1)" aria-label="Previous photo">‹</button>
    <button type="button" class="card-img-nav next" onclick="cardImgNav(event,this,1)" aria-label="Next photo">›</button>
    <div class="card-img-dots">${imgs.map((_, i) => `<span class="card-img-dot${i === 0 ? ' active' : ''}"></span>`).join('')}</div>` : '';
  return `<div class="card-image-wrap" data-images="${imgs.join('|')}" data-index="0">
    <img src="${imgs[0]}" alt="${r.project_name}" class="card-image" loading="lazy" onerror="this.onerror=null;this.src='/images/update.png';" onclick="openLightbox(event,this)">${nav}
  </div>`;
}

function cardImgNav(e, btn, dir) {
  e.preventDefault();
  e.stopPropagation();
  const wrap = btn.closest('.card-image-wrap');
  const imgs = wrap.getAttribute('data-images').split('|');
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

/* ── Auto-detect extra photos (pic2, pic3…) for single-image cards ──
   No CSV/pipe-list needed: if a listing's folder has more numbered
   photos sitting next to pic1, they're picked up automatically.
   Naming rule this depends on: same prefix + extension as the first
   photo, sequential numbers, no gaps (pic1, pic2, pic3...). */

const MAX_AUTO_DETECT = 8; // hard cap on how many extra photos to probe for

function checkImageExists(url) {
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => resolve(true);
    img.onerror = () => resolve(false);
    img.src = url;
  });
}

async function autoDetectCardImages(wrap) {
  if (wrap.dataset.detected) return; // never re-probe the same card
  wrap.dataset.detected = '1';

  const imgs = wrap.getAttribute('data-images').split('|');
  if (imgs.length > 1) return; // already has an explicit multi-image list, leave it alone

  const match = imgs[0].match(/^(.*\/)([a-zA-Z]+)(\d+)(\.[a-zA-Z0-9]+)$/);
  if (!match) return; // filename doesn't follow the picN.ext pattern, skip

  const [, folder, prefix, numStr, ext] = match;
  const startNum = parseInt(numStr, 10);
  const found = [imgs[0]];

  for (let i = 1; i < MAX_AUTO_DETECT; i++) {
    const candidate = `${folder}${prefix}${startNum + i}${ext}`;
    const exists = await checkImageExists(candidate);
    if (!exists) break; // stop at first gap
    found.push(candidate);
  }

  if (found.length === 1) return; // nothing extra found

  // Upgrade the card in place: update data-images and add nav/dots
  wrap.setAttribute('data-images', found.join('|'));
  const nav = `
    <button type="button" class="card-img-nav prev" onclick="cardImgNav(event,this,-1)" aria-label="Previous photo">‹</button>
    <button type="button" class="card-img-nav next" onclick="cardImgNav(event,this,1)" aria-label="Next photo">›</button>
    <div class="card-img-dots">${found.map((_, i) => `<span class="card-img-dot${i === 0 ? ' active' : ''}"></span>`).join('')}</div>`;
  wrap.insertAdjacentHTML('beforeend', nav);
}

function scanForNewCards(root) {
  root.querySelectorAll('.card-image-wrap[data-images]:not([data-detected])').forEach(autoDetectCardImages);
}

document.addEventListener('DOMContentLoaded', () => scanForNewCards(document));

// Listing cards get inserted dynamically (CSV/JSON fetch + innerHTML), so watch for that.
new MutationObserver(mutations => {
  for (const m of mutations) {
    m.addedNodes.forEach(node => {
      if (node.nodeType !== 1) return;
      if (node.matches && node.matches('.card-image-wrap[data-images]')) {
        autoDetectCardImages(node);
      } else if (node.querySelectorAll) {
        scanForNewCards(node);
      }
    });
  }
}).observe(document.body, { childList: true, subtree: true });