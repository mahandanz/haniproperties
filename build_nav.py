"""
build_nav.py -- Python version of build-nav.js (no Node needed).

Copies partials/nav.html into every .html page that has the markers
    <!-- NAV:START ... -->
    <!-- NAV:END -->
Run:  python build_nav.py
"""
from pathlib import Path

ROOT = Path(__file__).parent
PARTIAL = ROOT / "partials" / "nav.html"
START = "<!-- NAV:START"
END = "<!-- NAV:END -->"
SKIP_DIRS = {"node_modules", ".git", "partials"}


def html_files(d: Path):
    for p in d.iterdir():
        if p.name.startswith("."):
            continue
        if p.is_dir():
            if p.name not in SKIP_DIRS:
                yield from html_files(p)
        elif p.suffix == ".html":
            yield p


def main():
    nav = PARTIAL.read_text(encoding="utf-8").strip()
    block = ("<!-- NAV:START (auto-generated from partials/nav.html — run build_nav.py "
             "after editing, do not hand-edit) -->\n" + nav + "\n" + END)
    updated = skipped = 0
    for f in html_files(ROOT):
        with open(f, encoding="utf-8", newline="") as fh:  # keep original line endings
            text = fh.read()
        s, e = text.find(START), text.find(END)
        if s == -1 or e == -1:
            skipped += 1
            continue
        new = text[:s] + block + text[e + len(END):]
        if new != text:
            f.write_text(new, encoding="utf-8", newline="")
            updated += 1
            print(f"updated: {f.relative_to(ROOT)}")
    print(f"\nDone. {updated} file(s) updated, {skipped} file(s) had no NAV markers (left untouched).")


if __name__ == "__main__":
    main()
