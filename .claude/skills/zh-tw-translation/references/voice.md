# Voice exemplars — how 張秉霖 sounds in Traditional Chinese

Exemplars 1 and 3 are from articles the author proofread personally (`collection-autofill-at-scale`); exemplar 2 is from the unproofread
`optimizing-apple-silicon-gpu` translation but earns its place — the register is exactly right even where that article's terminology is not. These are
the **register and rhythm reference** — how colloquial, how dense, how much English to keep.

**They are NOT the terminology authority.** The proofread articles still contain items the linter flags (a 爆款 survived proofreading). When an
exemplar conflicts with `zhtw-mcp` or `conventions.md`, those win — except where `conventions.md` records a deliberate overrule.

## Exemplar 1 — explaining a concept, then landing it in one line

> 每個輸入都會變成一列，而 AI-generated
> columns 則負責萃取、摘要、分類，或把每列資料轉成可以查詢的欄位。……換句話說，Collection 做的事，是把「一堆檔案和連結」變成「一個我真的可以發問的資料庫」。

What to copy: technical English kept inline where an engineer would speak it; the paragraph ends on a plain-words summary sentence framed with 「」;
concrete lists over abstract description.

## Exemplar 2 — first-person narrative with a vivid, physical image

> 某天晚上，我的聊天突然慢到不行，token 像瀝青在滴，慢到我可以跟著唸。實際量出來的數字比體感還糟：**每秒 0.67 個 token**。

What to copy: sensory metaphor doing real explanatory work; the measured number bolded and delivered after the felt experience; short clauses, spoken
rhythm.

## Exemplar 3 — opinionated architectural claim, no hedging

> 如果某個欄位不能允許有 AI 幻覺，這件事不能只寫在 prompt 裡。欄位定義、欄位狀態和 UI 都要能表達「這裡沒有足夠證據」，而不是讓模型硬生出一個答案。

What to copy: states a position and the reason, no 各有優缺點 hedging; 「」 marks the load-bearing phrase; 硬生出 — colloquial verbs are welcome.

## Register summary

- 口語但精準：可以說「跑跑模型」「純 vibe 感受」，但數字與因果必須嚴格。
- 第一人稱誠實：我、我們直接用，不繞成被動或無主語句。
- 每段落有一句「落地句」：講完機制後用一句大白話收束。
- 幽默是乾的，不加 emoji，不加驚嘆號堆疊。
