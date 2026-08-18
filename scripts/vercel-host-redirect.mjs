#!/usr/bin/env node
/* global console */
// Vercel deploys this site through the Build Output API, which ignores the
// routing properties of vercel.json — a www→apex redirect declared there
// never reaches production. Astro middleware cannot do it either: the
// adapter only wraps the SSR render paths, and prerendered pages are served
// straight off the filesystem. So the host redirect is spliced into the
// adapter's .vercel/output/config.json after the build; vercel.json's
// buildCommand runs this script right after `astro build`.
import { readFileSync, writeFileSync } from 'node:fs';

const CONFIG = '.vercel/output/config.json';
const redirect = {
  src: '^/(.*)$',
  has: [{ type: 'host', value: 'www.pinglin.tw' }],
  headers: { Location: 'https://pinglin.tw/$1' },
  status: 308,
};

const config = JSON.parse(readFileSync(CONFIG, 'utf-8'));
config.routes ??= [];
const present = config.routes.some((route) => JSON.stringify(route) === JSON.stringify(redirect));
if (!present) config.routes.unshift(redirect);
writeFileSync(CONFIG, JSON.stringify(config, null, 2));
console.log(`www→apex redirect ${present ? 'already present' : 'added'} in ${CONFIG}`);
