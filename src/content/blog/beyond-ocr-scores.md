---
title: 'Beyond OCR Scores: Where Document Parsers Fail'
pubDate: 2026-09-01
draft: true
description:
  'A 1,250-page OCR benchmark exposes the scrambled reading order, missing tables, and broken formulas that RAG pipelines and AI agents inherit. I
  compare document parsers, OCR specialists, the open-weights Qwen 3.6, the hosted Claude Fable 5.1 and GPT-6 Astra, and Apple Vision to show where
  each fails—and what aggregate scores hide.'
author: 'Ping-Lin Chang'
lang: 'en'
image:
  url: '/blog/beyond-ocr-scores/hero-ocr-watercolor-polished.png'
  alt:
    'Illustrative OCR failures: interleaved columns, lost table headers, flattened math, and omitted notes distort a complex page before it reaches
    RAG or an AI agent.'
tags: ['engineering', 'benchmark', 'ocr']
---

<!-- DRAFT: do not publish with this comment present.
     STATE 2026-09-20: the article was cut to roughly half its previous length at the owner's direction, in this
     order: (1) the ParseBench section ("The same reader on a different benchmark", Table 5) and the speed
     section ("How fast each reader reads", Table 4) removed, with the accuracy-only scope stated in the preface;
     (2) the composite rationale and reader catalogue compressed; the four mid-table readers folded into one
     Results paragraph; Tables 2 and 3 REMOVED in favour of Figures 3 and 6, which label every value; the
     missed-tables section reduced to a paragraph; (3) this pass: the whole body rewritten at about half again,
     and per the owner "remove the implementation details and error experiences" — gone are the precision and
     library-pin paragraph, the three withdrawn rows (harness-vs-model), the dots.mocr merge-step and json.loads
     stories, the Qwen per-host repetition-loop finding, PaddleOCR-VL's stray-delimiter defect, the below-zero
     matcher pairing, API token budgets and billing arithmetic, and the "next composite" discussion.
     FIGURES ARE RENUMBERED: old Fig. 3 (headline bars) is now Fig. 2, old Fig. 5 (layout) is Fig. 3, old Fig. 7
     (missed tables) is Fig. 4. Old Fig. 2 (source thumbnails), Fig. 4 (empty pages), Fig. 6 (per-source bars)
     and Table 1 (page sources) are REMOVED; their generators (gen_ocr_bench_sources.py, gen_ocr_bench_figs.py
     panels, gen_ocr_bench_tables.py) still exist and still work.
     EVERY NUMBER still comes from the evaluator files for the held-out 1,250 and was carried over unchanged from
     the previous revision; nothing was recomputed or re-rounded in this pass. Provenance for every arm is in
     ~/.shubo-bench/RESULTS-heldout-1250.md and the backend report (a40-labs/backend, FINAL_REPORT.md), which
     also keeps the speed table (§5) and the ParseBench results (§6) that this article no longer carries.
     The full previous text is in git history. -->

Every document system has a moment where it must turn a page — a real page, scanned or photographed or exported, with its columns and footnotes and
smudged tables — into text a machine can use. Whatever you build downstream inherits the quality of that step. Retrieval cannot find a paragraph the
parser never produced; an agent cannot reason over a table that arrived as soup. I do that step on
[Apple-silicon Macs](/blog/optimizing-apple-silicon-gpu-for-transformer-inference), where the choice of reader is wide open: two-stage document
parsers, single-model OCR specialists, general-purpose vision-language models — open-weights on the Mac or hosted behind an API — and the text
recognizer built into the operating system. So: **of everything that can read a page today, including the OCR that ships free inside every Mac, what
should?**

This post is that comparison, run the way I would want someone else to run it: one benchmark, one held-out page set nothing was tuned on, every reader
under the protocol its own authors ship, scored by the benchmark's published evaluator, and the failures broken down far enough that you can tell
_which pages_ each reader loses.

It measures accuracy and nothing else. Speed, price and the hardware a reader needs are real constraints, and they are the easy ones: you can see them
from the outside, and they change with the next chip or the next price list. What a reader gets wrong on your pages does not, and it is the only thing
here that survives into the index and the answers built on it.

## Where the reader sits in a RAG or agent system

OCR is, narrowly, the step that turns pixels into characters. This post uses the wider meaning: find the blocks on the page, decide the order they are
read in, and transcribe each one into something a machine can consume — prose as prose, a table as a table, a formula as a formula. Every reader here
is measured on that whole job, which is why the post says "reader" rather than "OCR engine".

[Fig. 1](#figure-1) shows where that step sits. Documents arrive as PDFs, scans and photographs; the reader turns each page into structured text; the
text is chunked, embedded and indexed; a question retrieves from the index and a model reasons over what came back. Nothing on the serving side can
see the page — only what the reader said about it. A paragraph the reader dropped is not hard to retrieve, it does not exist. A table that arrived as
a run of words cannot be filtered or summed. None of this raises an error, because an embedder embeds soup as readily as prose and the vector store
returns it with a confident score. Agents sharpen both edges: they read on demand, with nobody glancing at the output, and they act on what they read,
so a column silently dropped from a scanned invoice becomes a wrong action rather than a wrong sentence.

<figure id="figure-1">
  <img src="/blog/beyond-ocr-scores/pipeline_light.svg" class="dark:hidden" alt="System diagram in two rows. The top row, labelled ingest, runs left to right: Documents, then a Text layer? check that branches to Extract text layer (born-digital, no OCR) and to Read the page (scan or photo, layout plus OCR, highlighted as the twelve readers in this post); both branches feed Structured text, then an Index. The bottom row, labelled serve, runs right to left: the Index feeds Retrieve, then an LLM or agent that takes a Question or task, then Answer or action. A dashed arrow from the LLM or agent back up into Read the page is labelled read a page on demand (tool call)." />
  <img src="/blog/beyond-ocr-scores/pipeline_dark.svg" class="hidden dark:block" alt="System diagram in two rows. The top row, labelled ingest, runs left to right: Documents, then a Text layer? check that branches to Extract text layer (born-digital, no OCR) and to Read the page (scan or photo, layout plus OCR, highlighted as the twelve readers in this post); both branches feed Structured text, then an Index. The bottom row, labelled serve, runs right to left: the Index feeds Retrieve, then an LLM or agent that takes a Question or task, then Answer or action. A dashed arrow from the LLM or agent back up into Read the page is labelled read a page on demand (tool call)." />
  <figcaption>Figure 1. Where the reader sits in a retrieval or agent system. A born-digital page carries its own text layer and skips the
  reader; a scanned or photographed page cannot. Everything downstream inherits the reader's output. The highlighted box is the step this post
  measures; the dashed arrow is an agent reading a page on demand.</figcaption>
</figure>

**Reading is the root of the system, and nothing above it compensates.** A stronger embedding model, a reranker, a longer context window, a better LLM
— all of them operate on the reader's output and none of them ever sees the page. A number that OCR misread is not a hard number to reason about; it
is a different number, and a model that reasons well will reason well toward the wrong answer. Errors at this step are not attenuated downstream, they
are compounded, because every later stage treats the text it was handed as ground truth. The only remedy for a bad read is a better read.

One fork before the measurements. A born-digital PDF carries its own text layer, and extracting it is deterministic, free and exact, so a well-built
pipeline checks for that layer first and sends pixels to a reader only where it must. This post stands on the pixel side of that fork deliberately:
every page in the study arrives as an image, so the numbers describe the branch a pipeline takes when the text layer is absent or untrustworthy.

## The benchmark

Everything here is measured on [OmniDocBench](https://github.com/opendatalab/OmniDocBench)
([Ouyang et al., CVPR 2025](https://arxiv.org/abs/2412.07626)), the most carefully annotated public benchmark for full-page document parsing. Version
1.6 contains 1,651 real PDF pages with block-level ground truth: every text block, table cell, formula and reading-order edge annotated by hand. It is
usefully adversarial, oversampling the page types that break parsers — dense CJK newspapers, exam papers, handwritten notes — rather than the clean
single-column PDFs where every method looks the same. The ten sources run from scanned books (212 pages) and exported slide decks (196) through
journal papers, exam sheets, textbooks, magazines, broadsheet newspapers (115), financial reports and handwritten notes.

The detail that matters most is _which_ pages I quote. I split the 1,651 in two: a seeded 401 pages to tune on, and the remaining **1,250 that nothing
was tuned, debugged or prompt-engineered on**. Every number in this post comes from that held-out 1,250, and the split is stratified so the two halves
resemble each other — which is what makes a difference between two readers attributable to the readers rather than to the pages they happened to get.
Small samples do not have that property, and table scores are where it shows worst: a 64-page selection carries four times the table density of either
half, and a table score computed on one moves by double-digit points in whichever direction a method's weakness happens to lie.

Four metrics, all from the benchmark's own evaluator:

- **Text edit distance** (lower is better) — normalized Levenshtein distance between predicted and ground-truth text blocks, averaged per page. The
  headline reading metric: 0.05 means the transcription is 95% right by characters.
- **Table TEDS** (higher is better) — [Tree-Edit-Distance Similarity](https://arxiv.org/abs/1911.10683) over table structure plus content, as a
  percentage.
- **Reading order** (lower is better) — edit distance over the sequence in which text blocks are emitted. This is where multi-column layouts bite.
- **Formula edit distance** (lower is better) — edit distance on display formulas, LaTeX-normalized.

One derived number appears alongside TEDS: **found-only TEDS**, the score over only the tables a reader actually detected, next to how many gold
tables it missed outright. A reader that misses a third of all tables but transcribes the rest beautifully has a different problem, and a different
fix, than one that finds everything and garbles cells.

The public leaderboard reports a single aggregate instead, [Eq. (1)](#eq-1), an equal-weight mean of three metrics:

$$
\htmlId{eq-1}{\text{Overall} = \frac{(1 - \text{text edit}) \times 100 \;+\; \text{table TEDS} \;+\; \text{formula CDM}}{3}} \tag{1}
$$

Its third term needs a word, because it is the one metric here that is not an edit distance. **CDM**
([Character Detection Matching](https://arxiv.org/abs/2409.03643), higher is better) scores a formula by rendering both the prediction and the gold
LaTeX to images and matching the symbols it sees in them. Mathematics can be written many ways — `\frac{a}{b}` and `\dfrac{a}{b}`, `x^{2}` and `x^2` —
and edit distance charges for every character that differs, while CDM asks only whether the rendered formula looks right. Where the two disagree, the
reader spelled the same mathematics differently; where both fall, it read the mathematics wrong.

I don't use Eq. (1), because one number cannot tell you _what_ broke. A reader that finds every table and garbles the cells, one that transcribes
cells perfectly but never detects a third of them, and one that reads every block correctly in the wrong order can all land on the same Overall, and
each needs a different fix. Eq. (1) also drops reading order entirely, which is the metric that separates these readers most sharply. So the columns
stay separate here, and for the same reason these are not the leaderboard's numbers and should not be read against them.

## The readers

Twelve readers, each run under the protocol its authors ship — their prompts, their stages, their decoding guards — on the same Apple-silicon
hardware, except the two hosted models, which ran on their providers' servers.

The production reader is the one that needs a justification, so here it is first. A two-stage parser sends every block through the same recognizer —
table, formula, paragraph alike — and paragraphs are most of what a retrieval index holds. So rather than serve the best single parser, I keep
MinerU2.5-Pro for layout, reading order, tables and formulas, and hand the prose blocks of formula-free pages to a model trained to do nothing but
transcribe prose. Every table and formula the composite emits is MinerU2.5-Pro's own, untouched.

- **Composite — [MinerU2.5-Pro](https://arxiv.org/abs/2509.22186) + [dots.mocr](https://huggingface.co/rednote-hilab/dots.mocr)**, the production
  reader. MinerU2.5-Pro (OpenDataLab, 1.2B) parses a page in two decoupled stages, layout on a downsampled view then recognition on native-resolution
  crops, which is what lets a small model handle dense pages; dots.mocr (rednote-hilab, ~3B) is the prose specialist it hands paragraphs to.
- **[MinerU2.5-Pro](https://arxiv.org/abs/2509.22186) alone**, the same parser without the prose swap, to show what the composite adds.
- **[dots.mocr](https://huggingface.co/rednote-hilab/dots.mocr) alone**, run its authors' way: the whole page in one pass with its own prompt, no
  layout or table model in front of it.
- **[GLM-OCR](https://huggingface.co/zai-org/GLM-OCR)** (Z.ai, 0.9B), 95.22 on the public OmniDocBench leaderboard, run through its own SDK: a layout
  model finds the regions and their order, and the recogniser is asked for each one.
- **[PaddleOCR-VL-1.6](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6)** (Baidu, 0.9B), 96.34 on the same leaderboard, and the reader whose
  documentation is most explicit that the VLM must not be run alone. It runs as it ships, layout stage in front.
- **[Unlimited-OCR](https://huggingface.co/baidu/Unlimited-OCR)**, Baidu's continuation of [DeepSeek-OCR](https://arxiv.org/abs/2510.18234)'s
  optical-compression architecture, reading the whole page in one pass under the decoding guard its own recipe carries.
- **[RapidOCR](https://github.com/RapidAI/RapidOCR)**: 32 MB of ONNX weights on the CPU, run twice — alone, and behind the RapidAI layout and table
  models. It is the cleanest experiment here: the same recogniser with and without a layout stage.
- **[LiteParse](https://github.com/run-llama/liteparse)** (LlamaIndex), the one reader built from rules instead of models: Tesseract OCR with the
  layout rebuilt from where the text sits.
- **[Apple Vision](https://developer.apple.com/documentation/vision/recognizedocumentsrequest)**, the text recognizer inside macOS, the same engine
  behind Live Text. One setting decides its row: its minimum text height defaults to a thirty-second of the page, which silently discards every
  newspaper body column before recognition begins, so I lowered it.
- **[Qwen 3.6](https://huggingface.co/Qwen)** (Alibaba, 35B open weights), prompted to transcribe the page. It is the control every specialist should
  have to beat: trained for everything, tuned for nothing here.
- **[Claude Fable 5.1](https://platform.claude.com/docs/en/about-claude/pricing)**, the same prompt sent to Anthropic's API, with thinking off.
- **[GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)**, the same prompt again, to OpenAI's API at full page resolution. The
  two hosted models answer the question every team asks first: is the API already better than anything you can run?

## Results

<figure id="figure-2">
  <img src="/blog/beyond-ocr-scores/headline_bars_light.svg" class="dark:hidden" alt="Six small horizontal bar charts, one per metric: text edit distance, table TEDS, reading order, formula edit distance, found-only TEDS and missed tables. Twelve readers in each, document readers first and the four controls set apart at the bottom; every bar is labelled with its value." />
  <img src="/blog/beyond-ocr-scores/headline_bars_dark.svg" class="hidden dark:block" alt="Six small horizontal bar charts, one per metric: text edit distance, table TEDS, reading order, formula edit distance, found-only TEDS and missed tables. Twelve readers in each, document readers first and the four controls set apart at the bottom; every bar is labelled with its value." />
  <figcaption>Figure 2. The six metrics on the held-out 1,250, one panel each, every bar labelled with its value; arrows give the direction of
  better. Document readers first; the four controls, which were never built for this job, are set apart at the bottom.</figcaption>
</figure>

**The composite is the best reader you can run yourself, and it never loses a column to the model inside it.** 0.0356 text, 0.1213 reading order,
91.63 TEDS and 8 of 473 tables missed, against MinerU2.5-Pro alone at 0.0401, 0.1263, 90.59 and 13. On display formulas the two are identical to four
decimal places, which is the design rather than a coincidence: formula pages go to MinerU2.5-Pro verbatim, so parity is the ceiling and it reaches it
on all 231 of them. The table columns are the surprise. A pipeline built on a model cannot find tables that model missed, so parity was the
expectation; instead the composite's missed set is a strict subset of MinerU2.5-Pro's, and it recovers five tables the model alone loses.

**The prose specialist is a capable parser on its own, and a poor one at structure.** dots.mocr reading the whole page in a single pass lands at
0.0537 text and 81.34 TEDS with 47 of 473 tables missed — no layout model, no table model, one forward pass. Its weakness is formulas, at 0.6335, and
that is bad transcription rather than absence: it writes LaTeX on 225 of the 231 pages that carry a display equation and gets it wrong.

**The four mid-table pipelines lose every column to the composite, and each loses it somewhere different.** GLM-OCR reads at 0.0881 text and 68.15
TEDS with 83 of 473 tables missed, and its layout stage is not the problem: the detector finds 462 of the 473 gold tables, and most of the losses are
tables it found and then lost, because a recogniser asked for a table sometimes returns prose. PaddleOCR-VL-1.6 is the opposite shape: 0.0616 text,
77.92 TEDS and only 14 tables missed, third in the study, but its formulas are the worst of any two-stage parser here, 0.3545 by edit distance and
60.34 by CDM against its own published 97.53. RapidOCR shows what a layout stage is worth: the same CPU weights read at 0.4337 text and 0 TEDS with
every table missed, and behind the RapidAI layout stage at 0.1227 and 76.97 TEDS with 15 missed — 13× better on newspapers and no better at all on
handwriting, where there are no columns to recover. And LiteParse, the rules pipeline, finds columns it cannot read: 0.4107 text, 20.91 TEDS, 150
tables missed, yet on English three-column pages it reads at 0.125 against Apple Vision's 0.358. Column order can be recovered from where the text
sits; recognition and tables cannot.

**The open-weights generalist lands between the specialists and the free OCR.** Qwen 3.6 at 0.0646 is 0.025 behind MinerU2.5-Pro alone on text —
respectable for a model tuned for nothing on this task — but the gap widens the moment structure matters: ten TEDS points behind, and clearly worse
reading order at 0.18 against 0.12.

**Claude Fable 5.1 reads level with the composite on the pages it agrees to read, and declines twelve.** As scored it lands at 0.0463 text, 89.86 TEDS
and 0.1337 reading order, with 16 of 473 tables never found. Twelve of its pages are empty because the API refused them on every one of four attempts:
ten were cut off mid-transcription by a content filter, most likely the one against reproducing published text verbatim, and two — a cholera-toxin
assay and a table of convulsant doses in mice — were refused outright, consistent with the model's dual-use safeguards. Set those twelve aside and
score every reader on the 1,238 pages that remain, and it reads at 0.0365 text, 90.43 TEDS and 0.1253 order against the composite's 0.0358, 91.60 and
0.1223. A reader that declines pages is a failure mode no local reader in this study has.

**GPT-6 Astra is the best text reader in the study, and fourth on structure.** It reads at 0.0331 and orders at 0.1189, ahead of the composite on
both, and takes newspapers at 0.0198 against the composite's 0.0481. On structure it is fourth: 88.71 TEDS and 23 of 473 tables never found against
the composite's 8, at an identical 0.933 on the tables both do find, so the whole table gap is detection.

**That text lead is resolution, not reasoning.** It sees the whole page at full resolution, where a two-stage parser reads crops cut from a
downsampled layout pass; reading order is a property of the whole page, and a model holding the page in one context never has to reconstruct it from
boxes, which is why it has the flattest layout curve in the study. Thinking plays no part:
[Roboflow's Vision Evals](https://playground.roboflow.com/models/openai/gpt-6-astra) score it 0.4 points _lower_ on OCR at high reasoning effort than
at low, for 2.9× the cost. Where it loses is where a layout model does the work — handwritten notes at 0.0812 against the composite's 0.0530, slides
at 0.0239 against 0.0125, and tables. The price of the row is the [last section](#who-controls-what-your-system-reads): \$154 for the set, and a
reader you cannot pin, inspect or re-run, since the alias has no dated snapshot, no weights and no stated precision.

**The one-pass specialist reads text worse than the free OCR does.** Unlimited-OCR lands at 0.2083 text, behind Apple Vision's 0.1881, while beating
it comfortably on structure: 68.66 TEDS against 50.68, and 91 tables missed against 166. Its text gap is concentrated rather than spread — 33 of its
1,177 text pages come back a total loss, against 7 for Apple Vision — and setting those aside inverts the ranking. What happens on them is the next
section.

**Apple Vision is more than 5× worse on text than the best reader, and that average hides the real story**, which is also the next section.

## Where each reader actually fails

<figure id="figure-3">
  <img src="/blog/beyond-ocr-scores/layout_collapse_light.svg" class="dark:hidden" alt="Grouped bar chart of text edit distance by page layout for nine of the twelve readers: the composite, MinerU2.5-Pro, dots.mocr, GLM-OCR, Unlimited-OCR, Apple Vision, Qwen 3.6, Claude Fable 5.1, and GPT-6 Astra. Six are flat across single-column, double-column, three-column, mixed-column, and other layouts: the composite and MinerU2.5-Pro between 0.02 and 0.06, dots.mocr between 0.05 and 0.08, Qwen between 0.04 and 0.10, Claude Fable 5.1 between 0.024 and 0.060, and GPT-6 Astra between 0.018 and 0.040. Three fall apart: GLM-OCR holds between 0.04 and 0.07 on column layouts and collapses to 0.20 on other layouts; Apple Vision climbs from 0.12 on single-column to 0.24 on double-column and 0.37 on three-column pages; and Unlimited-OCR follows the same climb, 0.13 to 0.23 to 0.33." />
  <img src="/blog/beyond-ocr-scores/layout_collapse_dark.svg" class="hidden dark:block" alt="Grouped bar chart of text edit distance by page layout for nine of the twelve readers: the composite, MinerU2.5-Pro, dots.mocr, GLM-OCR, Unlimited-OCR, Apple Vision, Qwen 3.6, Claude Fable 5.1, and GPT-6 Astra. Six are flat across single-column, double-column, three-column, mixed-column, and other layouts: the composite and MinerU2.5-Pro between 0.02 and 0.06, dots.mocr between 0.05 and 0.08, Qwen between 0.04 and 0.10, Claude Fable 5.1 between 0.024 and 0.060, and GPT-6 Astra between 0.018 and 0.040. Three fall apart: GLM-OCR holds between 0.04 and 0.07 on column layouts and collapses to 0.20 on other layouts; Apple Vision climbs from 0.12 on single-column to 0.24 on double-column and 0.37 on three-column pages; and Unlimited-OCR follows the same climb, 0.13 to 0.23 to 0.33." />
  <figcaption>Figure 3. Text edit distance by page layout, for the nine readers the colour-blind-safe palette holds; best per layout in bold.
  Seven of the nine stay flat as columns multiply and two fall apart, each on different pages.</figcaption>
</figure>

Every reader with a layout stage in front of it, and every whole-page VLM, stays flat as columns multiply. GPT-6 Astra is the flattest, 0.024–0.040 at
every column count; the composite actually _improves_ on three-column pages; dots.mocr, with no layout stage at all, stays within 0.042–0.048. Two
readers fall apart, and on different pages.

**Apple's deficit is column structure, not character recognition.** On single-column pages Apple Vision reads at 0.122, not far off what specialists
managed two years ago. Add columns and it degrades monotonically: 0.238 at two, 0.369 at three, where MinerU2.5-Pro reads the same pages at 0.024.
Vision recognizes characters well and simply does not do layout analysis. The contrast that pins it is dots.mocr, which has no layout stage either and
reads those same three-column pages at 0.046: a model that sees the whole page keeps the columns apart without being told where they are, while a
line-by-line recognizer emits lines in the order it finds them, and on a three-column page that order runs across the columns. The same signature
explains its table numbers — it transcribes the tables it finds at a respectable 0.781 but never finds 166 of 473, because table _detection_ is a
layout problem too. On research reports and slide decks, though, Apple Vision reads within 0.03–0.05 of the best reader at zero marginal cost. If your
corpus is corporate documents and presentations, the OCR already in the OS is a defensible parser; if it contains anything multi-column, no amount of
tuning changes the answer, because the failure is architectural.

**Unlimited-OCR's curve looks like Apple's and has nothing to do with columns.** It reads handwritten notes and books better than Apple Vision does,
then posts 0.602 on newspapers, its worst source by far. What the outputs show is a decoder that abandons the page: on 71 of the 1,250 — a quarter of
the newspapers among them — the output contains the text of a data-labelling rubric that appears nowhere on the page, repeated ten times or more on 24
of them. Those pages read at 0.518. On newspapers, 49 of 115 outputs run past one and a half times the length of the gold text and 15 stop under half
of it: over-generation and under-reading, both of them the page being lost rather than misread. This is the lineage's documented behaviour on dense
text, and the remedy its own authors recommend is a tiled high-resolution mode for dense pages.

**Formulas split the field into three groups, and the gaps are the widest in the study.** The two-stage parsers built around MinerU sit at 0.0874. The
readers that write LaTeX from a whole-page or per-region read land at 1.2 to 2.6 times that: GPT-6 Astra at 0.1055, GLM-OCR at 0.1228, Qwen 3.6 at
0.1286, Claude Fable 5.1 at 0.1309, Unlimited-OCR at 0.2240. Then there is a cliff, and it is not a difference of degree. PaddleOCR-VL-1.6 (0.3545)
and dots.mocr (0.6335) attempt every equation and get it wrong; Apple Vision, at 0.8097, and LiteParse, at 0.9320, are not reading equations badly,
they are not reading them at all — both transcribe the glyphs in front of them and have no notion of LaTeX, so an equation comes back as a line of
loose symbols that scores as text and means nothing. Edit distance alone cannot tell "wrong" from "absent", and neither can an aggregate. CDM against
edit distance can: 39.95 for dots.mocr and 60.34 for PaddleOCR-VL-1.6, where much of the loss is restyling that renders identically, against 95.93 for
the composite. If your documents contain mathematics, this is the whole decision, and no aggregate text score exposes it.

**The eight tables the best reader misses are all detection failures**, in five shapes ([Fig. 4](#figure-4)): four one-row tables written as text, a
grid of short tokens called a list, an infographic printed over a photograph, the lower of two stacked panels merged into the upper, and a signature
block read as headings. They are this layout head's blind spots rather than the field's — the RapidAI layout stage finds all eight, and every one of
them is read by someone.

<figure id="figure-4">
  <img src="/blog/beyond-ocr-scores/missed_tables_light.jpg" class="dark:hidden" alt="Six panels of cropped document pages, each with a red box around a gold table the composite missed. A: two pink one-row strips on a presentation slide, emitted as list text. B: a six-by-four grid of tokens such as VO Pr NG RelN on a linguistics slide, emitted as six lines. C: a newspaper infographic, How budget will affect labour costs, printed over a photograph, of which only the title was emitted. D: two stacked regression panels, the upper outlined blue as paired, the lower red as missed, emitted as one table. E: the signature block of a Chinese financial statement, four titles over four names, emitted as headings. F: two single schedule lines on a newspaper scoreboard page, 8:30 p.m. USC at Maryland FS1 and Minnesota at LA Rams, emitted as text." />
  <img src="/blog/beyond-ocr-scores/missed_tables_dark.jpg" class="hidden dark:block" alt="Six panels of cropped document pages, each with a red box around a gold table the composite missed. A: two pink one-row strips on a presentation slide, emitted as list text. B: a six-by-four grid of tokens such as VO Pr NG RelN on a linguistics slide, emitted as six lines. C: a newspaper infographic, How budget will affect labour costs, printed over a photograph, of which only the title was emitted. D: two stacked regression panels, the upper outlined blue as paired, the lower red as missed, emitted as one table. E: the signature block of a Chinese financial statement, four titles over four names, emitted as headings. F: two single schedule lines on a newspaper scoreboard page, 8:30 p.m. USC at Maryland FS1 and Minnesota at LA Rams, emitted as text." />
  <figcaption>Figure 4. The eight gold tables the best reader misses, on six pages, one panel each: a crop of the held-out page around the gold
  table (red; blue where a sibling table on the same page did pair), with what the reader emitted for it. A and F are the same failure, a single row
  of cells read as a sentence, on a slide and on a newspaper. Page images are from OmniDocBench v1.6 (OpenDataLab), released for research use,
  reproduced as crops.</figcaption>
</figure>

## Who controls what your system reads?

Notice what every specific finding above required. That Apple Vision's deficit is column structure rather than character recognition, that
Unlimited-OCR's text average is really a count of the pages it abandons, that the best reader's missing tables are all detection failures — none of
that is visible in a score. It came from reading individual pages next to individual outputs. A number tells you a reader is worse; only the output
tells you which pages you lose, and that is what decides whether a reader is usable on your corpus.

Reading is also unusual among the dependencies a system takes on, because its failures are written down. A failed API call retries; a bad read is
persisted. The chunks go into the index, the index serves every query after that, and nothing raises an error, because a garbled table embeds as
readily as a clean one. By the time anyone notices, the damage is a body of quietly wrong answers whose cause is a page nobody looked at, months
earlier. That is why a successful response is not evidence that a document was read correctly, and why the ability to go back and check is worth more
here than in most places you would spend it.

What that argues for is concrete: keep the original documents, keep an evaluation set drawn from your own corpus rather than a public one, and tie
every stored parse to the parser build that produced it, because "which parser" is not a complete description of what produced a chunk. Then keep a
path to a second reader and a way to rebuild what a bad parse produced, because you will eventually need both. I benchmarked one hosted model that
read text better than anything I run, so this is not a claim that local is more accurate. It is an argument for keeping evaluation and recovery in
your own hands — and a model you cannot pin to a build is exactly the case where that matters most.

## Take-home messages

1. **Reading is the root, and nothing above it compensates.** Every stage of a RAG pipeline or an agent operates on the reader's output and never sees
   the page. A misread number is a different number; a table that lost its structure cannot be rebuilt by a larger model. The only remedy for a bad
   read is a better read.
2. **Quote held-out numbers, from a sample large enough to carry them.** A 64-page selection has four times the table density of this benchmark as a
   whole, and a table score computed on one swings by double-digit points in whichever direction a method's weakness lies.
3. **A hosted frontier model reads text better than any specialist here and still misses three times the tables.** GPT-6 Astra beats the composite on
   text and reading order, wins five of nine page sources, and never finds 23 tables to the composite's 8 — at an identical score on the tables both
   find. The lead is resolution and a whole-page read, not reasoning. Claude Fable 5.1 is level with the composite on the pages it accepts and
   declines twelve outright, which is a failure mode no local reader has.
4. **The free OCR in your Mac is a column detector away from being a contender.** Character recognition is solved in the OS; layout is not. Feed it
   single-column corporate paper and it is fine. Feed it a newspaper and two-fifths of the characters come back wrong.
5. **Split detection from transcription before you read a table score.** "Scores 51 TEDS" and "transcribes the tables it finds at 78 while missing a
   third of them" are the same number, and only the second tells you what to fix. The same split decides formulas: a reader that writes wrong LaTeX
   and a reader that writes none score alike on edit distance and need different remedies.
6. **The specialists need their pipeline; the generalists do not.** Every OCR-specialised model that holds structure here holds it with a layout model
   in front of it, and a layout stage in front of a 32 MB recogniser is worth 77 TEDS points. The stages have to be learned, too: the one pipeline
   built from rules finds the columns and still reads like the free OCR. A specialist is a pipeline whether or not its README says so; a generalist is
   a prompt.
7. **Keep control of the reading step.** A bad read does not fail, it gets indexed, and it answers questions for as long as it sits there. Keep the
   originals, keep an evaluation set from your own corpus, tie every stored parse to the parser build that produced it, and choose a reader you can
   inspect, replace and re-run.
