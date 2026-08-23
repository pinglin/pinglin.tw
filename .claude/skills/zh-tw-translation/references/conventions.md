# pinglin.tw site conventions for zh-TW posts

General zh-TW terminology is `zhtw-mcp`'s job (and, upstream, python-docs-zh-tw and the Microsoft zh-TW style guide). This file holds only what is
specific to **this blog**: what it keeps in English, what it has already decided, and the mechanics of its markdown.

## The English-retention rule

**If a Taiwanese engineer would say the term in English out loud, keep it in English.** Translating it makes the prose read like a textbook, which is
the opposite of this blog's voice. Use exact English casing (GitOps, not gitops) and put a space on both sides.

**One concept, one form, per article.** The published posts' worst habit is drifting between table／資料表 or feed／饋送 inside one page. Decide at
the start, record the choice in an HTML comment at the top of the draft, delete the comment before finishing.

Keep in English: agent, pipeline, prompt, token, benchmark, workers, prefill, decode, batch, pull request／PR, commit, merge, CI, GitOps, DevOps,
reconciler, Kubernetes, Terraform, plan／apply, LLM, VLM, MoE, GPU, KV cache, context window, embedding, RAG, MCP, stack, host（動詞）, vibe, session.

Product names never translate: Grafana, Loki, VictoriaMetrics, Alertmanager, Argo CD, Slack, GitHub, Claude Code, Codex, mlx-vlm.

## Fixed choices (this blog has already decided)

| English                       | zh-TW            | Not                                                                     |
| ----------------------------- | ---------------- | ----------------------------------------------------------------------- |
| optimize / optimization       | 優化             | 最佳化 — author's published usage wins; zhtw-mcp will flag it, overrule |
| deploy / deployment           | 部署             | 發布（保留給 publish/release）                                          |
| observability                 | 可觀測性         | 可觀察性                                                                |
| alert                         | 告警             | 報警、警報                                                              |
| threshold                     | 閾值             | 閥值（錯字）                                                            |
| self-healing                  | 自我修復         | 自愈                                                                    |
| drift                         | 飄移             | 漂移                                                                    |
| retention                     | 保留（期／量）   | 留存                                                                    |
| replica                       | 副本             | 複本                                                                    |
| snapshot                      | 快照             | 鏡像（那是 image）                                                      |
| throughput                    | 吞吐量           | 通量                                                                    |
| latency                       | 延遲             | 時延                                                                    |
| inference                     | 推論             | 推理（保留給 reasoning）                                                |
| concurrent / concurrently     | 並行             | 併發                                                                    |
| spill to disk                 | 下放到／落到     | 溢出、溢位                                                              |
| scale (capacity, 獨立擴展)    | 擴展             | 擴充 — zhtw-mcp prefers it; overruled, see SKILL.md                     |
| scales with (proportionality) | 跟著⋯走、隨⋯而變 | 擴展、擴充 — neither fits this sense                                    |
| leader / follower             | leader／follower | 領導者／追隨者                                                          |
| runbook                       | runbook          | 操作手冊                                                                |

## Frontmatter

- `title`：翻譯後保留必要英文術語；中英並排時前後加空格。
- `description`：用中文重寫，不逐句翻譯英文版；長度以中文閱讀節奏為準。
- `author: '張秉霖'`、`lang: 'zh-tw'`。
- `tags`：用既有中文標籤（工程、推論⋯⋯），與英文版一一對應。
- `image.alt`：翻譯，與正文同等用心。
- 檔名與英文版相同，放在 `src/content/blog/zh-tw/`。

## Figures, tables, code

Keep structure byte-identical to the English post: same `<figure id="figure-N">` anchors, same numbering, same order. Translate `<figcaption>` and
every `alt` attribute with the same care as prose — the alt text is the figure for anyone who cannot see it.

Figure references in prose use the Chinese form: 圖一、圖二（English posts use Fig. N）. Table captions use 表 1. Code blocks, identifiers, and CLI
output are never translated; comments inside a code block may be.

## Line wrapping — the mechanical trap

**Prefer not to hard-wrap zh-TW paragraphs: one line per paragraph.** The site's remark plugin joins Han characters across a line break, so a wrap
_between two Han characters_ is safe — but a wrap after full-width punctuation, or inside an English phrase, leaves a **stray space in the rendered
page**. The pre-2026-08 translations are full of these. If you must wrap, break only between two Han characters.

Prettier reflows markdown at commit time via lint-staged; one-line paragraphs survive it.
