#!/usr/bin/env node
/**
 * domo-capture.js — Puppeteer script to capture Domo dashboard screenshots.
 *
 * Usage:
 *   node scripts/domo-capture.js [pageId]
 *
 * If pageId is omitted, captures all pages listed in config/domo.yml under kpi_pages.
 * Saves screenshots to .claude/tmp-screenshots/funnel-weekly/<pageId>-<YYYY-MM-DD>.png
 *
 * Required env vars (inherited from shell or .env):
 *   DOMO_HOST        — e.g. your-instance.domo.com
 *   DOMO_USERNAME    — Domo login email
 *   DOMO_PASSWORD    — Domo login password
 *
 * Optional env vars:
 *   SCREENSHOT_DIR   — override output directory (default: .claude/tmp-screenshots/funnel-weekly)
 *   HEADLESS         — set to "false" to watch the browser (default: true)
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// ── Config ─────────────────────────────────────────────────────────────────

const REPO_ROOT = path.resolve(__dirname, '..');
const CONFIG_PATH = path.join(REPO_ROOT, 'config', 'domo.yml');
const DEFAULT_OUT_DIR = path.join(REPO_ROOT, '.claude', 'tmp-screenshots', 'funnel-weekly');

const host = process.env.DOMO_HOST;
const username = process.env.DOMO_USERNAME;
const password = process.env.DOMO_PASSWORD;
const outDir = process.env.SCREENSHOT_DIR || DEFAULT_OUT_DIR;
const headless = process.env.HEADLESS !== 'false';

if (!host || !username || !password) {
  console.error('ERROR: DOMO_HOST, DOMO_USERNAME, and DOMO_PASSWORD env vars are required.');
  process.exit(1);
}

// ── Resolve page IDs to capture ────────────────────────────────────────────

function loadRegisteredPages() {
  if (!fs.existsSync(CONFIG_PATH)) {
    console.error(`ERROR: config not found at ${CONFIG_PATH}`);
    process.exit(1);
  }
  const config = yaml.load(fs.readFileSync(CONFIG_PATH, 'utf8'));
  const pages = config.kpi_pages || [];
  return pages
    .filter(p => p.approved === true)
    .map(p => ({ id: String(p.id), name: p.name || p.id }));
}

const argPageId = process.argv[2];
const pagesToCapture = argPageId
  ? [{ id: argPageId, name: argPageId }]
  : loadRegisteredPages();

if (pagesToCapture.length === 0) {
  console.error('ERROR: No approved pages found in config/domo.yml and no pageId argument provided.');
  process.exit(1);
}

// ── Helpers ────────────────────────────────────────────────────────────────

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function outPath(pageId) {
  return path.join(outDir, `${pageId}-${todayStr()}.png`);
}

// ── Main ───────────────────────────────────────────────────────────────────

(async () => {
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await puppeteer.launch({
    headless,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // ── Log in ─────────────────────────────────────────────────────────────
  console.log(`Logging in to https://${host} …`);
  await page.goto(`https://${host}/auth/index?domoLoginPage=true`, {
    waitUntil: 'networkidle2',
    timeout: 30000,
  });

  await page.type('input[name="username"], input[type="email"], #username', username);
  await page.type('input[name="password"], input[type="password"], #password', password);
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }),
    page.click('button[type="submit"], input[type="submit"], .login-btn'),
  ]);

  const currentUrl = page.url();
  if (currentUrl.includes('login') || currentUrl.includes('auth')) {
    console.error('ERROR: Login may have failed. Current URL:', currentUrl);
    await browser.close();
    process.exit(1);
  }
  console.log('Login successful.');

  // ── Capture each page ──────────────────────────────────────────────────
  const results = [];

  for (const { id, name } of pagesToCapture) {
    const url = `https://${host}/page/${id}`;
    console.log(`Capturing "${name}" (${id}) …`);

    try {
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 45000 });

      // Wait for card content to render
      await page.waitForSelector('.domo-card, .card-frame, [data-testid="card"]', {
        timeout: 15000,
      }).catch(() => {
        console.warn(`  Warning: card selector not found for page ${id} — capturing anyway`);
      });

      // Extra settle time for lazy-loaded charts
      await new Promise(r => setTimeout(r, 3000));

      const dest = outPath(id);
      await page.screenshot({ path: dest, fullPage: false });
      console.log(`  Saved → ${dest}`);
      results.push({ id, name, dest, status: 'ok' });
    } catch (err) {
      console.error(`  ERROR capturing page ${id}: ${err.message}`);
      results.push({ id, name, dest: null, status: 'error', error: err.message });
    }
  }

  await browser.close();

  // ── Summary ────────────────────────────────────────────────────────────
  const ok = results.filter(r => r.status === 'ok');
  const failed = results.filter(r => r.status === 'error');
  console.log(`\nDone. ${ok.length} captured, ${failed.length} failed.`);
  if (failed.length > 0) {
    console.error('Failed pages:', failed.map(r => r.id).join(', '));
    process.exit(1);
  }
})();
