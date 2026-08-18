#!/usr/bin/env node
/* global fetch, process, console */
// Submit URLs to IndexNow (feeds Bing — and through it ChatGPT search and
// Copilot — plus other participating engines) so new or updated pages get
// crawled within minutes instead of waiting for the next scheduled crawl.
//
// Usage, after the deploy is live:
//   pnpm indexnow                     submit every URL in the sitemap
//   pnpm indexnow <url> [url ...]     submit just the given URLs
//
// Re-submitting unchanged URLs is harmless; IndexNow deduplicates. The key
// file in public/ proves site ownership — keep its name in sync with KEY.
const HOST = 'pinglin.tw';
const KEY = 'cd82fb343c8460add94fb5210ed0f5f2';

let urls = process.argv.slice(2);
if (!urls.length) {
  const xml = await (await fetch(`https://${HOST}/sitemap.xml`)).text();
  urls = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]);
}
if (!urls.length) {
  console.error('No URLs to submit.');
  process.exit(1);
}

const response = await fetch('https://api.indexnow.org/indexnow', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8' },
  body: JSON.stringify({
    host: HOST,
    key: KEY,
    keyLocation: `https://${HOST}/${KEY}.txt`,
    urlList: urls,
  }),
});

console.log(`IndexNow: ${response.status} ${response.statusText} — submitted ${urls.length} URL(s)`);
if (!response.ok) process.exit(1);
