#!/usr/bin/env node
// Typeset illustrative input: difficult page structure and the OCR failures it invites.
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { Resvg } from '@resvg/resvg-js';

const output = fileURLToPath(new URL('../../public/blog/beyond-ocr-scores/', import.meta.url));
mkdirSync(output, { recursive: true });

const themes = {
  light: { bg: '#f3f4ef', ink: '#202620', muted: '#667062', rule: '#cdd2c7', accent: '#ad4435', tint: '#f4e3dd' },
  dark: { bg: '#191e1b', ink: '#e9eee6', muted: '#a3ae9c', rule: '#3c473b', accent: '#f3957b', tint: '#392a23' },
};

function render(p) {
  const s = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="hero-title hero-desc">
<title id="hero-title">A complex page and a flawed OCR attempt</title>
<desc id="hero-desc">Illustrative page with two text columns, merged table headers, a fraction with summation limits, handwriting, and fine-print footnotes. Beside it, an OCR attempt interleaves columns, drops header relationships, flattens the equation, and misses the notes.</desc>
<style>
text { font-family: Arial, Helvetica, sans-serif; fill: ${p.ink}; }
.mono { font-family: Menlo, Consolas, monospace; }
.serif { font-family: Georgia, 'Times New Roman', serif; }
.muted { fill: ${p.muted}; }
.accent { fill: ${p.accent}; }
</style>
<rect width="1200" height="630" fill="${p.bg}"/>`,
  ];

  const escape = (value) => String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const text = (x, y, value, size = 18, extra = '') => {
    s.push(`<text x="${x}" y="${y}" font-size="${size}" ${extra}>${escape(value)}</text>`);
  };
  const line = (x1, y1, x2, y2, color = p.rule, width = 1) => {
    s.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}"/>`);
  };
  const rect = (x, y, width, height, fill, extra = '') => {
    s.push(`<rect x="${x}" y="${y}" width="${width}" height="${height}" fill="${fill}" ${extra}/>`);
  };
  const paperInk = '#283029';
  const paperAccent = '#ad4435';
  const paperRule = '#919989';
  const paperText = (x, y, value, size = 15, extra = '') => {
    text(x, y, value, size, `class="serif" style="fill:${paperInk}" ${extra}`);
  };
  const badge = (x, y, number) => {
    rect(x, y - 14, 23, 21, paperAccent);
    text(x + 11.5, y + 1, number, 11, 'class="mono" style="fill:#ffffff" font-weight="700" text-anchor="middle"');
  };

  text(48, 35, 'COMPLEX INPUT', 12, 'font-weight="700" letter-spacing="1.6"');
  text(1148, 35, 'ILLUSTRATIVE EXAMPLE', 10, 'class="muted" letter-spacing="1.3" text-anchor="end"');

  // The whole left side is an actual typeset page, not a generic PDF icon.
  rect(48, 55, 714, 526, '#fffefa', 'stroke="#c9cfc3"');
  paperText(83, 89, 'LAB NOTES / 07', 11, 'letter-spacing="1.4"');
  paperText(83, 126, 'Measurements and observations', 27);
  line(83, 144, 728, 144, paperInk, 1.2);

  // Two full paragraphs have real words. Their side-by-side placement is the challenge.
  badge(57, 174, '01');
  paperText(84, 177, '1. Sampling', 16, 'font-weight="700"');
  paperText(416, 177, '2. Analysis', 16, 'font-weight="700"');
  const left = [
    'Each specimen was measured twice',
    'under the same conditions. Labels',
    'remain fixed across both readings.',
    'The second series follows the first;',
    'values must stay with their rows.',
    'See the note beside specimen B.',
    'Small differences are retained.¹',
  ];
  const right = ['Compare each reading with its', 'paired value, then preserve the', 'fraction and its lower limit:'];
  for (let i = 0; i < left.length; i++) paperText(84, 203 + i * 19, left[i], 14.5);
  for (let i = 0; i < right.length; i++) paperText(416, 203 + i * 19, right[i], 14.5);
  line(397, 175, 397, 325, '#d8dcd2');

  // Thin red reading paths run in the line spacing, making row-wise interleaving visible.
  s.push(
    '<path d="M90 210 H714 M708 206 l6 4 -6 4 M714 213 V229 H90 M96 225 l-6 4 6 4" fill="none" stroke="#ad4435" stroke-width="1" opacity="0.6"/>',
  );

  // A real 2-D expression: superscript, summation limits, an overbar, and a fraction.
  badge(700, 269, '03');
  paperText(421, 303, 's', 30, 'font-style="italic"');
  paperText(436, 283, '2', 14);
  paperText(453, 301, '=', 24);
  paperText(497, 300, '∑', 34);
  paperText(509, 271, 'n', 12, 'font-style="italic"');
  paperText(497, 317, 'i = 1', 11, 'font-style="italic"');
  paperText(538, 299, '(', 23);
  paperText(549, 299, 'x', 23, 'font-style="italic"');
  paperText(562, 305, 'i', 12, 'font-style="italic"');
  paperText(579, 299, '−', 22);
  paperText(610, 299, 'x', 23, 'font-style="italic"');
  line(611, 281, 625, 281, paperInk, 1.2);
  paperText(629, 299, ')', 23);
  paperText(641, 283, '2', 13);
  line(489, 326, 668, 326, paperInk, 1.3);
  paperText(551, 349, 'n − 1', 20, 'font-style="italic"');

  // Rowspan + colspan headers require the recognizer to recover cell relationships.
  badge(57, 375, '02');
  paperText(84, 351, 'Table 1. Paired measurements', 12, 'font-style="italic"');
  const tx = 84,
    ty = 364,
    tw = 480;
  rect(tx, ty, tw, 140, 'none', 'stroke="#687461" stroke-width="1"');
  rect(228, ty, 336, 26, '#edf0e7');
  line(228, ty, 228, 504, paperRule);
  line(396, 390, 396, 504, paperRule);
  line(228, 390, 564, 390, paperRule);
  for (const y of [414, 444, 474]) line(84, y, 564, y, paperRule);
  paperText(156, 395, 'Specimen', 15, 'font-weight="700" text-anchor="middle"');
  paperText(396, 382, 'Mass (mg)', 15, 'font-weight="700" text-anchor="middle"');
  paperText(312, 408, 'Before', 14, 'text-anchor="middle"');
  paperText(480, 408, 'After', 14, 'text-anchor="middle"');
  const rows = [
    ['A', '12', '15'],
    ['B', '24', '28'],
    ['C', '36', '41'],
  ];
  rows.forEach((row, index) => {
    const y = 435 + index * 30;
    [156, 312, 480].forEach((x, column) => paperText(x, y, row[column], 17, 'text-anchor="middle"'));
  });
  // A bracket picks out the merged heading rather than treating it as another cell.
  s.push('<path d="M235 361 v-5 h322 v5" fill="none" stroke="#ad4435" stroke-width="1.5"/>');

  // Outline the handwriting once so it stays identical across clients without a custom font.
  const note =
    '<svg xmlns="http://www.w3.org/2000/svg" width="169" height="83">' +
    '<text x="4" y="30" font-family="Bradley Hand" font-weight="700" font-size="24" fill="#ad4435">recheck B</text>' +
    '<text x="8" y="57" font-family="Bradley Hand" font-weight="700" font-size="19" fill="#ad4435">use original</text></svg>';
  const outlinedNote = new Resvg(note)
    .toString()
    .replace(/^<svg[^>]*>/, '')
    .replace(/<\/svg>\s*$/, '');
  badge(698, 407, '04');
  s.push(`<g transform="translate(574 409) rotate(-7 80 35)" aria-label="Handwritten note: recheck B, use original">${outlinedNote}</g>`);
  s.push('<path d="M604 482 Q570 490 504 464 M510 462 l-6 2 5 4" fill="none" stroke="#ad4435" stroke-width="1.3" stroke-linecap="round"/>');

  // Fine print is genuine text, deliberately smaller than the main columns.
  line(84, 527, 305, 527, paperRule);
  paperText(84, 543, '¹ Values rounded to the nearest mg. Blank cells are not zero.', 10.5);
  paperText(84, 560, '† Repeat measurement requested for specimen B; retain the handwritten note.', 10.5);
  line(726, 531, 726, 561, paperAccent, 1.2);

  // An open, typeset failure report. No 3-D effects or repeated article headline.
  text(824, 85, 'OCR ATTEMPT', 18, 'font-weight="700" letter-spacing="1.4"');
  line(824, 103, 1150, 103, p.ink, 1.3);
  const resultLabel = (y, number, label) => {
    text(824, y, number, 12, 'class="mono accent"');
    text(855, y, label, 19, 'font-weight="600"');
  };
  resultLabel(140, '01', 'Columns interleaved');
  text(855, 171, 'Each specimen Compare each', 14, 'class="mono"');
  text(855, 194, 'was measured reading with…', 14, 'class="mono"');
  line(824, 218, 1150, 218);

  resultLabel(251, '02', 'Header links lost');
  text(855, 284, 'B   24   28', 21, 'class="mono"');
  text(855, 309, 'Which value is “Before”?', 16, 'class="muted"');
  line(824, 332, 1150, 332);

  resultLabel(365, '03', 'Math flattened');
  text(855, 400, 's2 = Σ(xi − x)2 / n − 1', 16, 'class="mono accent"');
  line(824, 424, 1150, 424);

  resultLabel(457, '04', 'Notes disappear');
  text(855, 490, '[not extracted]', 19, 'class="mono accent"');
  line(824, 526, 1150, 526, p.ink, 1.3);
  text(824, 552, 'Used as RAG / agent context', 14, 'class="muted"');

  // The small connector indicates extraction; source complexity remains the focal point.
  s.push(`<path d="M776 299 h34 m-7 -6 7 6 -7 6" fill="none" stroke="${p.muted}" stroke-width="1.3"/>`);
  s.push('</svg>');
  return `${s.join('\n')}\n`;
}

for (const [theme, palette] of Object.entries(themes)) {
  const svg = render(palette);
  const stem = `${output}/hero-ocr-difficulty${theme === 'light' ? '-light' : ''}`;
  writeFileSync(`${stem}.svg`, svg);
  writeFileSync(`${stem}.png`, new Resvg(svg).render().asPng());
}
console.log('Wrote complex-input OCR heroes in light and dark themes.');
