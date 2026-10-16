# Usage (from site root): python patch_demand_sort.py
# Optional: pass specific files, e.g. python patch_demand_sort.py area/local/shah-alam.html
import sys, pathlib, glob
OLD_FN = """function sortByNewest(rows) {
  return rows.slice().sort((a, b) => parseDateAdded(b.date_added) - parseDateAdded(a.date_added));
}"""
NEW_FN = """function demandScore(r) {
  const n = parseFloat(String(r['Demand %'] || '').replace('%', ''));
  return isNaN(n) ? -1 : n; // blank demand sorts to the end
}

// Highest demand first; ties fall back to newest date_added
function sortByDemand(rows) {
  return rows.slice().sort((a, b) =>
    (demandScore(b) - demandScore(a)) ||
    (parseDateAdded(b.date_added) - parseDateAdded(a.date_added)));
}"""
files = [f for a in sys.argv[1:] for f in (glob.glob(a) or [a])] or sorted(glob.glob('area/local/*.html'))
if not files: print('No files found - run this from your site root (the folder containing area/local).')
for p in files:
    f = pathlib.Path(p)
    raw = f.read_bytes()
    crlf = b'\r\n' in raw
    s = raw.decode('utf-8').replace('\r\n', '\n')
    if 'sortByDemand' in s:
        print('skip (already patched):', p); continue
    if OLD_FN not in s:
        print('SKIP (pattern not found):', p); continue
    s = s.replace(OLD_FN, NEW_FN).replace('sortByNewest(filtered', 'sortByDemand(filtered')
    if crlf: s = s.replace('\n', '\r\n')
    f.write_bytes(s.encode('utf-8'))
    print('patched:', p)
