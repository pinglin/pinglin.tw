---
name: zh-tw-translation
description: |
  Translate a pinglin.tw English blog post into Traditional Chinese (Taiwan) so it reads
  as if 張秉霖 wrote it in Chinese first, and hold the site's own conventions. Trigger when
  asked to translate a post to Chinese/zh-TW/繁體中文, to retranslate or fix an existing
  zh-tw article, or to judge whether one reads Taiwan-native. Not for: other languages,
  zh-CN output, or product/UI strings — those are the a40 workspace's `a40-l10n` and
  `a40-zh-tw`.
---

# zh-TW for pinglin.tw — the voice layer

This skill is **only voice and site conventions**, on purpose. The mechanical pipeline — meaning-first drafting, de-translationese, deterministic
linting, glossary authority — already exists as `a40-zh-tw` in the a40-labs workspace (`buckle/agents/skills/a40-zh-tw`), which states outright that
the voice pass belongs here and deliberately adds no style of its own. **If that skill is reachable, invoke it for stages 1–3 and use this file for
stage 4 and the conventions.** When this repo is opened alone, run the compact equivalent below.

## Stages 1–3, compact

### 1. Outline first, then write from the outline

Read the ENTIRE English post. Write an 8–15 bullet outline of the argument in zh-TW. Write each Chinese paragraph **from that outline**, rereading the
English only for facts (numbers, names, causal claims). The test: a reader must not be able to reconstruct the English clause order from your Chinese.

This is the rule the published translations broke, and every calque traced back to it — `作為 CTO，我貢獻了…` (an "As CTO," opener transliterated),
the imported 旅程 metaphor, and `一堂耗資 920 萬美元的課程` (課程 is a curriculum; a $9.2M lesson is 一課／教訓).

Hard bans, each a documented defect in this repo's history: 作為 X，我⋯ openers; agentless 被-passives; 旅程／篇章 metaphors imported from
English; 「不是 A，而是 B」more than once per article; 首先／其次／最後; 的-chains longer than two; 進行／透過⋯的方式 padding.

### 2. De-translationese

Reread the draft with the English closed. Delete boilerplate (generic conclusions, formula openings, 罐頭轉場); concretize vagueness (if a sentence
says nothing specific once the padding is gone, cut it);
reduce 破折號/粗體 density. 保事實：數字、專有名詞、因果判斷一項不失。人味是作者的：不得替作者發明故事或立場。

The full 38-trace catalogue is `speak-human-tw` (MIT), vendored in the a40 workspace at `buckle/agents/skills/speak-human-tw` — read
`references/patterns.md` there when available.

### 3. zhtw-mcp — `convert` first, then `lint`

```sh
zhtw-mcp convert <file>       # simplified leakage: 软件→軟體, 默认→預設
zhtw-mcp lint <file>          # cross-strait terms, punctuation, MoE character standards
```

**Order is load-bearing.** `lint` assumes traditional input and will NOT flag raw simplified characters — verified here on a seeded fixture:
`這個軟件的默认設定` produced one finding (`軟件`) and passed `默认` silently. Model-drafted text always goes through `convert` first.

**Never `convert --fix` or `lint --fix` on this blog.** `convert` rewrites 優化→最佳化, against the author's published usage (it is in article
titles). Read its stdout, apply findings by hand. See the overrules below.

If the binary is missing, say so in your output — do not silently skip the stage and report the text as checked.

### 4. Voice check — this skill's actual job

Read `references/voice.md`, then the draft against it. Every section should land on a落地句. Register: 口語但精準, first person direct, dry humour, no
emoji.

## What this blog overrules in zhtw-mcp

Findings this site rejects, with the reason. Everything else the linter says, fix.

| Finding                                     | Verdict                | Why                                                                                                                                                                                                                           |
| ------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `優化` → `最佳化`                           | **Keep 優化**          | The author's published usage, including in titles. ~13 hits per article; all noise.                                                                                                                                           |
| `溢出` → `溢位`                             | **Keep/rephrase**      | 溢位 is _numeric_ overflow. For a cache spilling to disk, use 下放到／落到.                                                                                                                                                   |
| `服務框架` → `服務架構`                     | **Rephrase**           | Neither fits "serving stack" — keep `stack` in English, per the retention rule.                                                                                                                                               |
| `擴展` → `擴充`                             | **Keep 擴展**          | Capacity sense ("scale independently", 擴展軸) — the author's consistent usage across proofread articles, 38 hits. Only rephrase when the English is "scales _with_" (proportionality), where neither word fits: say 跟著⋯走. |
| `[translationese]` with an empty suggestion | **Judge individually** | Pattern flags, not fixes. Many are fine Chinese.                                                                                                                                                                              |

## Site conventions

`references/conventions.md` — English-retention policy, fixed term choices, frontmatter, figure/caption handling, and the line-wrapping rule (a bad
wrap leaves a stray space in the rendered page).

## Review

The author proofreads every translation before publication. Never overwrite an existing proofread zh-tw article unasked. Present the draft with the
judgment calls made: term-sheet decisions, sentences deliberately restructured, and any linter finding kept rather than fixed.
