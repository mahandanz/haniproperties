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
