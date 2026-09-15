# Watercolor OCR hero

Created with the built-in image generation tool. The existing OCR comparison is the content reference; the user-supplied watercolor study illustration
is the style reference.

Original watercolor asset: `public/blog/beyond-ocr-scores/hero-ocr-watercolor.png` (1729 × 910). The active article and social asset is
`public/blog/beyond-ocr-scores/hero-ocr-watercolor-polished.png` (1728 × 910). The final cleanup in `ocr_hero_polish_prompt.md` removes the arrow
across the columns and the stray red stroke beside the footnotes. The same warm paper illustration is used in both site themes. The typeset source
remains available in `gen_ocr_hero.mjs`.

## Prompt

Use case: style-transfer. Asset: a wide editorial hero for an OCR/document-parsing article.

INPUTS: Image 1 is the EDIT TARGET and the authority for ALL content and composition: a complex document on the left and four OCR failure examples on
the right. Image 2 is a STYLE REFERENCE ONLY: warm watercolor and fine pen-and-ink illustration with textured paper, restrained ochre and olive
washes, dark blue-black ink, rust-red annotations, and soft natural light.

REQUEST: Restyle Image 1 in the hand-rendered watercolor and ink medium of Image 2. Keep the existing OCR comparison, all four numbered failure
examples, and every piece of meaningful text, table data and math. Keep the same two-panel horizontal composition and roughly the same proportions. Do
not recreate the person or room in Image 2. Make this feel like a beautifully illustrated research notebook: warm ivory paper, subtle pigment blooms
around page edges, delicate irregular ink rules, lightly textured cream/olive backdrop, and restrained red pencil marks. Give it real visible
watercolor character rather than merely applying a beige tint, but keep surfaces flat and text clear. Natural light from upper left. Quiet tactile
editorial craft; no glossy rendering or generic tech effects.

CONTENT INVARIANTS: Top labels: "COMPLEX INPUT" and "ILLUSTRATIVE EXAMPLE". Left source sheet: "LAB NOTES / 07" "Measurements and observations" Two
clearly distinct text columns titled "1. Sampling" and "2. Analysis". Preserve the real readable prose from Image 1, including fine print. Keep the
red reading-order path crossing the two columns through whitespace. Keep the TRUE source equation as a two-dimensional fraction: s² = (sum from i=1 to
n of (x_i − x̄)²) / (n − 1). It must have the squared superscripts, i subscript, bar on x, upper/lower summation limits, and a horizontal fraction bar
with n − 1 beneath it, exactly as Image 1. "Table 1. Paired measurements" Preserve the merged-cell table. "Specimen" spans both header rows. "Mass
(mg)" spans "Before" and "After". Exact rows: A | 12 | 15 ; B | 24 | 28 ; C | 36 | 41. Preserve the readable red handwritten note "recheck B" / "use
original" and its arrow to specimen B. Footnotes: "¹ Values rounded to the nearest mg. Blank cells are not zero." and "† Repeat measurement requested
for specimen B; retain the handwritten note." Preserve red numbered markers 01, 02, 03, 04 next to the corresponding source features.

Right side, exact large readable labels and example text: "OCR ATTEMPT" "01" "Columns interleaved" "Each specimen Compare each" "was measured reading
with…" "02" "Header links lost" "B 24 28" "Which value is “Before”?" "03" "Math flattened" "s2 = Σ(xi − x)2 / n − 1" "04" "Notes disappear" "[not
extracted]" "Used as RAG / agent context"

TYPOGRAPHY: Keep all source text, numbers, equation and right-side labels crisp and accurately readable, like printed black ink on watercolor paper.
Only the existing handwritten note uses handwriting. Do not imitate the reference's unreadable decorative micro-writing. Preserve deliberate garbling
ONLY in the displayed OCR output. Style the paper, lines, marks, surfaces and atmosphere; do not distort letterforms or invent characters.

CONSTRAINTS: No article headline in the image. No added slogan, people, hands, plants, books, room, laptop, detached letters, paper strips, decorative
gibberish, 3D panels, robots, neon, glossy surfaces, or watermarks. The challenge of OCR must remain immediately visible through the complex original
page versus damaged extraction. Keep all content inside frame with comfortable margins. Wide 1200:630 aspect ratio; output at high resolution, ideally
2400 × 1260, so the real text remains legible.
