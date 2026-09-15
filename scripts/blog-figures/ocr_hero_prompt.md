# Archived raster hero prompt

This image-generation experiment has been replaced by the watercolor hero described in `ocr_hero_watercolor_prompt.md`, with cleanup in
`ocr_hero_polish_prompt.md`. The active article and social image is `public/blog/beyond-ocr-scores/hero-ocr-watercolor-polished.png`. Its content
reference is the typeset SVG in `gen_ocr_hero.mjs`. Regenerate those reference SVG/PNG assets with `node scripts/blog-figures/gen_ocr_hero.mjs`. The
previous raster asset was `public/blog/beyond-ocr-scores/hero-ocr-rag.png`.

The current visual pairs a complex typeset document with a flawed OCR attempt. Two columns, merged table headers, mathematical notation, handwriting,
and footnotes make the difficulty visible. The output interleaves columns, loses header relationships, flattens math, and omits notes before reaching
RAG or agent context. All data and failures in this image are illustrative, not measured benchmark outputs. Keep text readable and omit the article
title. Do not return to abstract paper strips or detached characters. The prompt below is retained for reference. Use `ocr_hero_watercolor_prompt.md`
to revise the current artwork.

## Generation prompt

Use case: stylized-concept. Asset: a polished editorial technology hero illustration for an article about OCR and document parsing quality upstream of
RAG and AI agents. Create a NEW composition.

Core concept, immediately understandable: information lost during OCR/document parsing remains absent from retrieved context, so an AI agent cannot
answer a question the original PDF could answer.

Visual direction: refined technical editorial illustration with tactile white document surfaces, restrained translucent blue processing elements,
crisp dark typography, and one coral-red omission carried along a continuous flow. Pale cool-white background, soft directional shadows, a strong
coherent composition. Light three-quarter perspective, but all important text faces the viewer and is easily readable. Modern and precise, no warm
parchment or antique paper. The result should feel designed for a serious AI engineering publication.

Arrange four connected stages across a wide 1.905:1 canvas, with clear visual hierarchy and generous spacing:

1. A large, recognisable upright PDF page with a clearly printed small table.
2. A slim optical scanning frame passing over a document, turning it into structured text. A small blue scan line makes OCR visually explicit. Show an
   empty red-outlined field where one cell value was lost.
3. Three neatly layered retrieved-context sheets beside a small magnifying-glass symbol. This represents RAG retrieval. The foremost context sheet
   visibly retains the missing field.
4. One compact, readable AI conversation panel, showing that the missing value cannot be answered from context.

Use one understated horizontal connecting path between the four stages. A tiny coral-red empty-square symbol follows the missing value from the parser
to the retrieved context. The source value is intact on the original document; the omission begins at the OCR/parser stage. Keep the relationship
visually clear without a thicket of arrows or an infographic full of callouts.

Exactly four small but prominent stage labels, set in crisp modern sans-serif, around 26 px at a final 1200-pixel image width: "DOCUMENT" "OCR /
PARSE" "RAG" "AI AGENT"

Exact source table, large enough to read: "Group" | "Count" "A" | "12" "B" | "24" "C" | "36" Give the original value "24" a subtle blue highlight to
make the comparison easy. This is illustrative source data, not benchmark scores.

At the OCR stage, the small structured text output reads exactly: "A: 12" "B: —" "C: 36" Mark the missing B value with a small coral-red outlined
empty slot. Do not show a false replacement number.

The front RAG context sheet reads exactly: "Retrieved context" "Group B: —"

The final AI conversation panel reads exactly: "Count for B?" "Not in context."

Keep these few words genuinely readable, correctly spelled, with clear black letterforms. Do not add microtext, pseudo-characters, decorative code, or
gibberish. Favor larger type and fewer details over density.

No article headline or repeated article title. No large decorative slogan, fake benchmark metrics, leaderboard scores, robot, brain, humanoid, curling
paper ribbon, floating debris, orange callout boxes, or sci-fi neon. No logo or watermark. The technical workflow itself is the visual concept.

Output: one finished wide hero illustration, preferably exactly 1200 × 630 pixels. Keep the entire composition in frame and make the document,
scanning, retrieval, and answer silhouettes easy to recognise at thumbnail size.
