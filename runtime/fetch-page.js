#!/usr/bin/env node
/**
 * fetch-page.js — Playwright-based page fetcher for Brand New Day
 *
 * Usage: node fetch-page.js <url> [--timeout=15000] [--selector=".content"]
 *
 * Outputs JSON to stdout:
 * {
 *   "success": true,
 *   "url": "https://...",
 *   "title": "Page Title",
 *   "content": "Extracted text content...",
 *   "html": "<raw HTML of target element>",
 *   "elapsed_ms": 1234
 * }
 *
 * On failure:
 * { "success": false, "url": "...", "error": "reason" }
 */

const { chromium } = require("playwright");

const args = process.argv.slice(2);
const url = args.find((a) => !a.startsWith("--"));
if (!url) {
  console.log(JSON.stringify({ success: false, url: null, error: "No URL provided" }));
  process.exit(1);
}

const timeoutFlag = args.find((a) => a.startsWith("--timeout="));
const timeout = timeoutFlag ? parseInt(timeoutFlag.split("=")[1], 10) : 15000;

const selectorFlag = args.find((a) => a.startsWith("--selector="));
const selector = selectorFlag ? selectorFlag.split("=")[1] : null;

// Source-specific selectors for known ATS platforms
function getWaitSelector(pageUrl) {
  if (selector) return selector;
  if (pageUrl.includes("jobs.lever.co")) return ".content";
  if (pageUrl.includes("jobs.ashbyhq.com")) return '[data-testid="job-details"], .ashby-job-posting-brief-description, main';
  if (pageUrl.includes("builtin.com")) return '[class*="job-description"], main';
  return "main, article, body";
}

(async () => {
  const start = Date.now();
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      userAgent:
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    });
    const page = await context.newPage();

    // Block images, fonts, and media to speed up load
    await page.route("**/*", (route) => {
      const type = route.request().resourceType();
      if (["image", "media", "font", "stylesheet"].includes(type)) {
        route.abort();
      } else {
        route.continue();
      }
    });

    await page.goto(url, { waitUntil: "domcontentloaded", timeout });

    // Wait for the content selector to appear
    const waitSel = getWaitSelector(url);
    const selectors = waitSel.split(", ");
    try {
      await Promise.race(
        selectors.map((s) => page.waitForSelector(s, { timeout: timeout / 2 }))
      );
    } catch {
      // Selector didn't appear — still try to extract what's there
    }

    // Small extra wait for any late JS rendering
    await page.waitForTimeout(1500);

    const title = await page.title();

    // Extract text from the most relevant container
    let content = "";
    let html = "";
    for (const s of selectors) {
      try {
        const el = await page.$(s);
        if (el) {
          content = await el.innerText();
          html = await el.innerHTML();
          if (content.trim().length > 100) break; // Good enough
        }
      } catch {
        continue;
      }
    }

    // Fallback to body if nothing found
    if (content.trim().length < 100) {
      content = await page.innerText("body");
      html = await page.innerHTML("body");
    }

    // Trim excessive whitespace
    content = content.replace(/\n{3,}/g, "\n\n").trim();

    // Cap content at 50k chars to avoid blowing up JSON output
    if (content.length > 50000) {
      content = content.substring(0, 50000) + "\n[...truncated]";
    }

    const elapsed = Date.now() - start;
    console.log(
      JSON.stringify({ success: true, url, title, content, elapsed_ms: elapsed })
    );
  } catch (err) {
    const elapsed = Date.now() - start;
    console.log(
      JSON.stringify({ success: false, url, error: err.message, elapsed_ms: elapsed })
    );
  } finally {
    if (browser) await browser.close();
  }
})();
