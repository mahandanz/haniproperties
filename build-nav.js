#!/usr/bin/env node
/**
 * build-nav.js
 *
 * Keeps the nav bar in sync across every page of the site — while keeping
 * the nav as plain, crawlable HTML (no JS injection, good for SEO).
 *
 * How it works:
 *   1. Edit partials/nav.html — the single source of truth for the nav.
 *   2. Run:  node build-nav.js
 *   3. It finds every .html file in the project, and replaces whatever sits
 *      between the markers:
 *          <!-- NAV:START ... -->
 *          <!-- NAV:END -->
 *      with the current contents of partials/nav.html.
 *
 * A page only gets updated if it already contains both markers. To add the
 * shared nav to a NEW page, paste this into the page once, in place of
 * wherever <nav>...</nav> should go:
 *
 *   <!-- NAV:START -->
 *   <!-- NAV:END -->
 *
 * Then run this script — it fills in the nav content automatically.
 * Links in partials/nav.html use root-absolute paths (e.g. "/projects/projects.html"),
 * so the same partial works correctly no matter how deep the page is nested.
 */

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const PARTIAL_PATH = path.join(ROOT, 'partials', 'nav.html');
const START_MARKER = '<!-- NAV:START';
const END_MARKER = '<!-- NAV:END -->';

// Directories to skip while scanning for .html files.
const SKIP_DIRS = new Set(['node_modules', '.git', 'partials']);

function findHtmlFiles(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!SKIP_DIRS.has(entry.name)) findHtmlFiles(full, out);
    } else if (entry.isFile() && entry.name.endsWith('.html')) {
      out.push(full);
    }
  }
  return out;
}

function main() {
  if (!fs.existsSync(PARTIAL_PATH)) {
    console.error(`Missing partial: ${PARTIAL_PATH}`);
    process.exit(1);
  }
  const navHtml = fs.readFileSync(PARTIAL_PATH, 'utf8').trim();
  const replacement =
    `<!-- NAV:START (auto-generated from partials/nav.html — run build-nav.js after editing, do not hand-edit) -->\n` +
    navHtml + '\n' +
    `<!-- NAV:END -->`;

  const files = findHtmlFiles(ROOT);
  let updated = 0;
  let skipped = 0;

  for (const file of files) {
    const original = fs.readFileSync(file, 'utf8');
    const startIdx = original.indexOf(START_MARKER);
    const endIdx = original.indexOf(END_MARKER);

    if (startIdx === -1 || endIdx === -1) {
      skipped++;
      continue;
    }

    const before = original.slice(0, startIdx);
    const after = original.slice(endIdx + END_MARKER.length);
    const next = before + replacement + after;

    if (next !== original) {
      fs.writeFileSync(file, next, 'utf8');
      console.log(`updated: ${path.relative(ROOT, file)}`);
      updated++;
    }
  }

  console.log(`\nDone. ${updated} file(s) updated, ${skipped} file(s) had no NAV markers (left untouched).`);
}

main();
