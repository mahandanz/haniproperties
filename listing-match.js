/* ============================================================
   Hani Properties — shared listing text matcher
   listing-match.js  |  used by search.html and every area page,
   so a search behaves the same everywhere on the site.

   The whole phrase must appear, as whole words, in the listing's
   area, zone, project name, code or anchors (nearby LRT/MRT,
   malls, etc). "seksyen 7" matches "Seksyen 7" but NOT
   "Seksyen 17", "Seksyen 70" or a price like 1750. Case and
   extra spaces are ignored.

   Transit exception: searching a rail line name on its own
   (lrt, mrt, ktm, brt, erl, monorail) also matches numbered
   lines, so "lrt" finds "LRT3" and "LRT 3", and "mrt" finds
   "MRT2". Other words still need an exact whole-word match.
   ============================================================ */
(function () {
  const TRANSIT_WORDS = ['lrt', 'mrt', 'ktm', 'brt', 'erl', 'monorail'];

  function normalise(str) {
    return (str || '').toString().toLowerCase().replace(/\s+/g, ' ').trim();
  }

  function matchesQuery(r, query) {
    const q = normalise(query);
    if (!q) return true;
    const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const lineNumber = TRANSIT_WORDS.includes(q) ? '(\\s?\\d+)?' : '';
    const re = new RegExp('(^|[^a-z0-9])' + escaped + lineNumber + '($|[^a-z0-9])');
    return [r.area, r.zone, r.project_name, r.code, r.anchors].some(f => re.test(normalise(f)));
  }

  window.HPMatch = { matchesQuery, normalise };
})();
