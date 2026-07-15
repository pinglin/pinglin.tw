---
title: '優化 Transformer 模型服務參數 – Apple Silicon GPU 的案例'
pubDate: 2026-07-11
description:
  '一台 MacBook Pro M4 Max、一個開源 MoE 模型，針對推論優化的一次實戰：為什麼讓 LLM 的吞吐量崩跌 100 倍的是 prefill（而不是 decode），以及兩個針對
  prefill 部分的優化。'
author: '張秉霖'
lang: 'zh-tw'
image:
  url: '/blog/optimizing-apple-silicon-gpu-for-transformer-inference/header.png'
  urlLight: '/blog/optimizing-apple-silicon-gpu-for-transformer-inference/header_light.png'
  alt: 'GPU 佔用時間軸：當 benchmark 的 prefill 區塊佔住 GPU 時，LLM 的 decode 速度從每秒 65 個 token 崩跌到每秒 0.67 個。'
tags: ['工程', '推論']
---

我有一台 MacBook Pro M4 Max，它是我的 portable LLM/VLM lab。

一開始我只是在上面跑跑各家的開源模型，純 vibe 感受效果，但隨著時間推移，我開始在本機端 host LLM/VLM 來跑 coding
agent，並同時跑大型 benchmark（幾百道題，每題帶著 10–25k+
token 的 prompt，並且好幾個 workers 同時發問）。某天晚上，我的聊天突然慢到不行，token 像瀝青在滴，慢到我可以跟著唸。實際量出來的數字比體感還糟：**每秒 0.67 個 token**，而這台機器在沒有其他負載時，decode 速度是 65
tok/s。

跌了 100 倍，沒有 crash、沒有錯誤，GPU 也明顯一直在忙。這篇文章記錄的就是這次的診斷與解法。背後的原理其實就是教科書等級的：prefill 受算力限制（compute-bound），decode 受記憶體頻寬限制（memory-bandwidth-bound）。但幾乎所有討論這件事的文章，都假設你人在資料中心，可以往問題丟更多 GPU。這篇要講的是另一個版本的故事：一台 Metal 機器、兩種工作負載，以及一個決心把它物盡其用的我。

## 環境

模型是一個 35B 參數的 mixture-of-experts，活躍參數約 3B，量化成 mxfp4（每個 output token 大約要讀 2
GB 的權重），跑在一個支援 batching 的 MLX 引擎（[mlx-vlm](https://github.com/Blaizzy/mlx-vlm)）上，對外提供 OpenAI 相容的 endpoint。硬體是 M4 Max：128
GB 統一記憶體，頻寬 546 GB/s。

兩種完全不同的工作負載共用這台機器：

- **Agent 聊天。** 多輪、會呼叫工具的 session。每一輪都會重送到目前為止的完整對話，所以一個 session 會累積出一條很長的 warm prefix；我的通常在 23k
  token 左右。這方面的使用情境，通常就是人會坐在螢幕前看著 token 即時輸出，所以如果延遲很長，體驗就會很糟。
- **Benchmark 量測。** 一輪跑分大約 150 道題，每題都是**全新**的 10–25k+ token
  prompt（長文件加檢索上下文），由好幾個 workers 並行送出。以刷榜實驗的情境來說，人是不需要在旁邊等的，跑分出來時再通知我就是了。

這裡的「聊天」只是我手上的具體案例，它代表的是任何互動式串流：agent 迴圈、coding
assistant，任何有人在另一端等著 token 的東西；benchmark 則代表任何批次工作。

以我量測的數據來說，這台機器平均每輸出 1 個 token，就要先讀進
**77 個 token**，也就是 77:1 的輸入輸出比。對這顆 GPU 來說，工作壓倒性地是**讀 prompt**，而不是輸出 token。先記住這個比例，它決定了後面其中一個優化邏輯。

## 兩種工作，兩種瓶頸

Transformer 處理一個請求分成兩個階段，而這兩個階段的瓶頸落在機器完全不同的地方。

**Decode 卡在記憶體頻寬。** 每個 decode
step 都要把模型的活躍權重從記憶體完整讀一遍，然後為每一條進行中的 sequence 各產出一個 token。算術上就是一道除法：

```text
理論上限: 546 GB/s ÷ 每步約 2 GB ≈ 270 tok/s
實際量測: 60–70 tok/s (大約只有理論值的四分之一)
```

這道簡化其實除法沒有算進去很多東西

- **KV cache 的讀取**：每產生一個新 token，attention 都要回頭看整段上下文；為了不每次重算，每個處理過的 token 都會留下一份 KV
  cache（假設模型每個 token 消耗 20 KB），而這份 cache 每一步都得整段重讀。所以一場已經累積到 23k token 的聊天，每一步就要多讀大約 0.5 GB（23k token ×
  20 KB），相當於再讀四分之一份權重。[kipply](https://kipp.ly/p/transformer-inference-arithmetic) 稱它為「sometimes-significant factor」；
  [DeepMind 的 scaling book](https://jax-ml.github.io/scaling-book/inference/) 則直接把它放進下限公式：minimum step time = (batch × KV cache +
  parameters) ÷ bandwidth。
- **Kernel 跑不到頻寬峰值**：kipply 在估算時，只給真實 kernel 理論頻寬的 72–90%；即使是手工調校過的 FasterTransformer，在 A100 上 decode 一個 13B 模型，實測也要每 token
  22 ms（約 45 tok/s），而純算術的預測是 18.5 ms（約 54 tok/s）。
- **矩陣乘法之間的所有細微操作**：softmax、layernorm、residual：這些都是 memory-bound 的小型 pass，只除權重的那道算式完全沒有計入。
- **這套 stack 特有的開銷**：mlx-vlm 每一步的固定 overhead，加上 MoE 的 experts 散落在記憶體各處，沒辦法一次連續讀完。

所以實際值落在理論值的四分之一，一點都不奇怪；更重要的是，上面每一項成本，本質上仍然是記憶體成本。

天花板由頻寬決定，跟容量無關：我用到的整個記憶體（權重 + KV cache + prefix cache）尖峰也只佔 128 GB 裡的 40–50
GB，買更多記憶體並不會讓任何單一串流變快。那要怎麼同時服務好幾個人？靠的不是更多記憶體，而是 batching 共享同一個 step：batch 開到 N 的時候，同一次權重讀取就能讓 N 條 sequence 各輸出一個 token，所以純 decode 的多租戶輸出幾乎是零成本。如果這顆 GPU 只需要做 decode，每個租戶都能體驗 60+
tok/s，但真實的流量成本從來就不會只有 decode，而這正是接下來整篇文章要談的。

**Prefill 卡在算力。**
一個請求要 decode 出第一個 token 之前，整段 prompt 都得先推過模型一次。這是橫跨整條 sequence 的大型矩陣乘法（40 個 GPU 核心全部吃滿），以 2,048
token 為一個 chunk 處理；一般長文件等級的 prompt，每個 chunk 都要跑一到兩秒。對多租戶情境來說，最致命的問題是：**prefill
chunk 在運算的期間，誰都不能 decode。**

## 核心問題：交錯運算

交錯運算這兩個階段的方式，是在 prefill chunk 之間大約放行一個 decode
step。當 GPU 大部分時間都在 decode 時（Agent 聊天情境），你根本不會察覺這件事。但一旦有 benchmark 等級的任務介入，GPU 就再也不是大部分時間在 decode 了：

<figure id="figure-1">
  <img src="/blog/optimizing-apple-silicon-gpu-for-transformer-inference/gpu_timeline_light.svg" class="dark:hidden" alt="一張跨十二秒的雙軌 GPU 佔用時間軸。軌道 A，只有聊天：一條連續的 decode 帶，中間有一小段 prefix cache 還原，速度 60 到 70 tok/s。軌道 B，一個冷的 60k token benchmark prefill：橘色 prefill chunk 一塊接一塊，之間只夾著一條細細的 decode step，並行的聊天實測只拿到 0.67 tok/s。" />
  <img src="/blog/optimizing-apple-silicon-gpu-for-transformer-inference/gpu_timeline_dark.svg" class="hidden dark:block" alt="一張跨十二秒的雙軌 GPU 佔用時間軸。軌道 A，只有聊天：一條連續的 decode 帶，中間有一小段 prefix cache 還原，速度 60 到 70 tok/s。軌道 B，一個冷的 60k token benchmark prefill：橘色 prefill chunk 一塊接一塊，之間只夾著一條細細的 decode step，並行的聊天實測只拿到 0.67 tok/s。" />
  <figcaption>圖一。同一個 12 秒的時間窗，兩種情境。軌道 B 裡那些細細的藍色縫隙（實際上只有約 15 ms，圖上畫得寬很多），就是所有人能分到的全部 decode step。</figcaption>
</figure>

Benchmark 任務本質上就是不斷進行 prefill，每道題都是全新內容，永遠不會命中 prefix cache：保證 cache
miss、保證完整 prefill，一輪跑分重複 N 次，通常還有多個 worker 同時併發，把 queue 填得滿滿的，所以任何時刻幾乎都有某個 2,048
token 的 chunk 佔著 GPU，batch 裡的每個 decoder 只能靠 chunk 之間放行的那一步勉強前進。在這個案例裡面，我實際測量了一次：在單一個 60k
token 的 prefill 進行期間，一條並行的聊天串流只剩 0.67 tok/s。我的體感大概是這樣：

<figure id="figure-2">
  <img src="/blog/optimizing-apple-silicon-gpu-for-transformer-inference/chat_decode_rate_light.svg" class="dark:hidden" alt="一條聊天串流六十秒內的 decode 速率折線圖。原本穩定在每秒 65 個 token 附近，在 60k token 的 benchmark prefill 進行的二十五秒間崩跌到實測的每秒 0.67 個，然後瞬間恢復。" />
  <img src="/blog/optimizing-apple-silicon-gpu-for-transformer-inference/chat_decode_rate_dark.svg" class="hidden dark:block" alt="一條聊天串流六十秒內的 decode 速率折線圖。原本穩定在每秒 65 個 token 附近，在 60k token 的 benchmark prefill 進行的二十五秒間崩跌到實測的每秒 0.67 個，然後瞬間恢復。" />
  <figcaption>圖二。一條已經 warm-up 的聊天串流的 decode 速率：一個 60k token 的 benchmark prefill 抵達、執行、完成。</figcaption>
</figure>

模型服務系統的文獻對這個現象有個專有名詞，叫 generation
stalls（生成停滯），而且文獻裡的數字跟這個案例對得上：prefill 優先的排程器，可以把進行中的 decode 停住好幾秒。[Sarathi-Serve 論文（OSDI '24）](https://arxiv.org/abs/2403.02310)
在 vLLM 裡診斷出的正是這個問題，並提出了 stall-free batching：限制每次迭代的 prefill 預算，讓 prefill
chunk 和進行中的 decode 合併成同一個 batch，而不是把 decode 擠掉。帶著 decode 意識排程的 chunked prefill，後來成了
[vLLM V1 引擎的預設](https://docs.vllm.ai/en/stable/configuration/optimization/)，SGLang也內建同樣的技術。

## 長駐 KV Cache 的代價

這裡面還有一個比較隱微的效應，值得單獨拆出來討論。每個 decode step 重讀的不只是權重，還包括每條進行中 sequence 的 KV cache，按前面說的每 token 約 20
KB 計。聊天等級的上下文還算溫和，但一條停在 130k token 的 benchmark sequence，會讓每一步、每個人都多付 2.6 GB 的讀取（130k token × 20 KB）：

<figure id="figure-3">
  <img src="/blog/optimizing-apple-silicon-gpu-for-transformer-inference/kv_reread_tax_light.svg" class="dark:hidden" alt="每個 decode step 讀取位元組數的堆疊橫條圖。只有聊天時，每步約讀 2 GB 權重，速度約 65 tok/s。加入一條 130k token 的 benchmark sequence 之後，每步多出 2.6 GB 的 KV 讀取，速度大約砍半。" />
  <img src="/blog/optimizing-apple-silicon-gpu-for-transformer-inference/kv_reread_tax_dark.svg" class="hidden dark:block" alt="每個 decode step 讀取位元組數的堆疊橫條圖。只有聊天時，每步約讀 2 GB 權重，速度約 65 tok/s。加入一條 130k token 的 benchmark sequence 之後，每步多出 2.6 GB 的 KV 讀取，速度大約砍半。" />
  <figcaption>圖三。每個 decode step 的讀取量。這條 sequence 的 KV（2.6 GB）比權重本身（2.0 GB）還大，把每一步要讀的量從約 2 GB 推到約 4.6 GB，所以即使沒有任何 prefill 在跑，一條長駐的 sequence 也足以把大家共享的 step rate 砍到大約一半。</figcaption>
</figure>

最直覺的優化是 KV cache 量化：位元組減半，這項 overhead 就減半。但 mlx-vlm 現在不支援量化 KV 和 APC (automatic prefix
cache) 並存，要用前者就得放棄後者。在 77:1 的輸入輸出比之下，這個選擇很明確：每一輪命中 prefix
cache 的對話都能跳過幾萬個 token 的 prefill，價值遠遠超過 decode 時省下來的 KV 讀取，所以我保留了 prefix cache。mlx-vlm 未來馬上會支持兩者並存了，見
[#1559](https://github.com/Blaizzy/mlx-vlm/issues/1559)。如果你的輸入輸出比是反過來，decode 為主要的工作負載，那你應該直接量化 KV cache 來進行優化。

## 主要兩點優化

所以真正有效的優化，都發生在 prefill 這一側。這也是整個案例討論最後的結論：decode 共享從來就不是問題，要保護 decode，靠的是控制 prefill 什麼時候、在哪裡發生。

**1. 把 prefix cache 加大。** 聊天要攤掉自己的 prefill，前提是 cache 裡還留著它的 prefix。我把 prefix
cache 的容量調大，讓大約 6 個並行 session 可以同時保持暖機；現在第 N+1 輪對話能在一秒內還原大約 23k
token 的 prefix，而不是重新 prefill 幾十秒。這同時也壓低了長駐 KV 的 overhead，因為還原回來的 prefix 取代了重新計算的版本。特別大的 unified 記憶體容量在 Apple
Silicon 上真正的優勢是這個：不是更快的 decode（參考前面那道頻寬除法），而是一個更大、能讓你跳過 prefill 的 cache。

**2. 幫長文件等級的 prefill 加一道 admission gate。**
一次只放行一個大型 prefill，而且排程器會守住 chunk 之間的 decode 空隙，不讓排隊中的下一個 prefill 把空隙接走。這樣不管 prefill
queue 排的多深，互動型串流都能持續拿到自己的 decode step，這部分跟 Sarathi stall-free batching 的政策層概念很類似。

兩點優化都到位之後，即使 benchmark 同時在跑，聊天也能穩穩維持 60–70 tok/s。GPU 從頭到尾都沒有變快，它只是不再被要求在錯的時間做錯的事。受
[DistServe](https://arxiv.org/abs/2401.09670) 和 [Splitwise](https://arxiv.org/abs/2311.18677)
把 prefill 和 decode 拆到不同硬體的想法啟發，長遠來看不同性質的工作負載，放到各自專屬的運算單元上，才是正解。（有錢的話 🤑）

## TTFT 與 ITL 的取捨

Prefill 和 decode 這場 latency 拉扯的兩邊，在 serving 領域各有正式名稱。**TTFT**（time to first
token）是一個請求等到第一個 token 出現要多久：排隊時間，加上把整段 prompt 推過模型的 prefill 運算，也就是那些隨 prompt 長度成長的矩陣乘法與 attention。**ITL**（inter-token
latency，也寫作 TPOT，time per output token；Sarathi 論文裡叫 TBT，time between
tokens）則是串流開始 decode 之後，token 與 token 之間的間隔：也就是 decode step 的節奏。

用這兩個概念重新理解一遍這個案例：Benchmark 這個租戶的 TTFT 工作，把聊天互動這個租戶的 ITL 從約 15 ms 延長到約 1.5
s（將近 100 倍的退化），而這個系統退化並沒有反映在任何吞吐量的指標。前面的兩個優化也可以直接對應到這兩個概念：加大 prefix
cache 是 TTFT 修正（命中 cache 的回合，現在一秒內就能開始），admission gate 是 ITL 修正（不管 prefill
queue 多深，聊天互動情境裡面最壞的 token 間隔都被限制在大約一個 chunk 的時間）。

這兩個指標之所以重要，是因為它們在同一顆 GPU 上互相拉扯，而拉扯的比例由一個參數決定：**兩個 decode
step 之間放行多少 prefill**，也就是 chunk 的大小。Chunk 越大，prompt 越快跑完（TTFT 越好），但每一條並行串流的 token 間隔也被拉長（ITL 越差）。反過來把 chunk 切細，並行的互動式串流就能喘口氣（ITL 變好），代價是每多一個 chunk 邊界都要付一次固定開銷（kernel 啟動、重讀前面的 KV），讓那個大 prompt 自己反而跑更久（TTFT 越差）；極端的情況下，decode 優先的排程甚至會讓 prefill 完全動彈不得。

舉個具體的例子：下圖的 TTFT 曲線是一個長文件等級 prompt 自己的 TTFT。它的第一個 token 得等全部 60,000 個 prompt
token 都 prefill 完才會出現，所以不管 chunk 切多小，都低不過約 25 秒的算力下界；chunk
size 只決定它要在下界之上多付多少開銷，以及這段期間其他串流的 token 要等多久。Chunk
size 的兩個極端通常都不是我們要的，如何針對使用情境找到甜蜜點才是重點：

<figure id="figure-4">
  <img src="/blog/optimizing-apple-silicon-gpu-for-transformer-inference/ttft_itl_tradeoff_light.svg" class="dark:hidden" alt="一張 log-log 折線圖，x 軸是 prefill chunk size，y 軸是秒數。橘色曲線是 60k token prompt 自己的 TTFT，從 128 token chunk 時的約 55 秒，隨 chunk 變大下降到它約 25 秒的 prefill 算力下界（以點線標出）。藍色曲線是 prefill 進行期間並行互動式串流感受到的 ITL，從約 0.1 秒近乎線性上升到 6 秒。512 到 1,024 token 之間有一條陰影帶標出甜蜜點，虛線標出這台機器目前的 2,048 token 設定。" />
  <img src="/blog/optimizing-apple-silicon-gpu-for-transformer-inference/ttft_itl_tradeoff_dark.svg" class="hidden dark:block" alt="一張 log-log 折線圖，x 軸是 prefill chunk size，y 軸是秒數。橘色曲線是 60k token prompt 自己的 TTFT，從 128 token chunk 時的約 55 秒，隨 chunk 變大下降到它約 25 秒的 prefill 算力下界（以點線標出）。藍色曲線是 prefill 進行期間並行互動式串流感受到的 ITL，從約 0.1 秒近乎線性上升到 6 秒。512 到 1,024 token 之間有一條陰影帶標出甜蜜點，虛線標出這台機器目前的 2,048 token 設定。" />
  <figcaption>圖四。Chunk size 把 benchmark prompt 自己的 TTFT 和互動式串流的 ITL 放上同一座天平，曲線用這台機器的實測速率建模（假設列在圖內）。橘色曲線永遠低不過約 25 秒的 prefill 算力下界；甜蜜區間的左邊，你付出實實在在的 TTFT，只換到一點點流暢度；甜蜜區間的右邊，互動式串流的 ITL 線性變差，TTFT 卻幾乎不再進步。</figcaption>
</figure>

以這個案例來說，合適的甜蜜區間大約在每 chunk 512–1,024 token：並行聊天的 token 間隔維持在約 0.4–0.8 秒，60k
token 的 prompt 則比約 25 秒的下界多付出 15–30% 的 TTFT。我目前設定的 2,048
token 落在這個區間的右邊：刻意偏向 benchmark 的完成時間，代價就是最壞情況下，互動聊天的 decode 會出現 1.5 秒（0.67
tok/s）的間隔。而這正是引入 admission gate 的重點：它保證每兩個 prefill chunk 之間都留一段 decode window，讓聊天在那段時間以完整的 60–70
tok/s 串流。所以聊天的體感是：正常速度串流，中間夾著週期性的短暫停頓，而不是開頭那種一路 0.67 tok/s 的龜速。

## 延伸討論：市場算力天花板

前面的分析全都受制於同一個數字：546
GB/s。既然整篇文章都在主張「單串流 decode 就是一道頻寬除法」，那把同一道除法套用到真正為推論而生的硬體上，就能看清兩件事：資料中心的錢究竟買到多少頻寬，以及這台筆電在整條光譜上落在哪裡。

| Hardware                                       | Memory                    | Bandwidth      | vs. M4 Max  | Indicative decode, this model\*   |
| ---------------------------------------------- | ------------------------- | -------------- | ----------- | --------------------------------- |
| Apple M4 (MacBook Pro)                         | ≤ 32 GB unified           | 120 GB/s       | 0.2×        | ~14 tok/s                         |
| Apple M5                                       | ≤ 32 GB unified           | 153 GB/s       | 0.3×        | ~18 tok/s                         |
| **Apple M4 Max (this post)**                   | 128 GB unified            | 546 GB/s       | 1×          | **65 tok/s (measured)**           |
| Apple M5 Max, 40-core GPU (Mar 2026)           | 128 GB unified            | 614 GB/s       | 1.1×        | ~73 tok/s                         |
| Apple M3 Ultra (Mac Studio, current top)       | ≤ 512 GB unified          | 819 GB/s       | 1.5×        | ~98 tok/s                         |
| Apple M5 Ultra (Mac Studio, rumored late 2026) | ≤ 768 GB unified, rumored | ~1.2 TB/s†     | ~2.2×       | ~145 tok/s                        |
| NVIDIA GeForce RTX 3090                        | 24 GB GDDR6X              | 936 GB/s       | 1.7×        | ~110 tok/s                        |
| NVIDIA GeForce RTX 4090                        | 24 GB GDDR6X              | 1.0 TB/s       | 1.8×        | ~120 tok/s                        |
| NVIDIA GeForce RTX 5090                        | 32 GB GDDR7               | 1.8 TB/s       | 3.3×        | ~215 tok/s                        |
| NVIDIA A100 (SXM, 80 GB)                       | 80 GB HBM2e               | 2.0 TB/s       | 3.7×        | ~240 tok/s                        |
| NVIDIA H100 (SXM)                              | 80 GB HBM3                | 3.35 TB/s      | 6.1×        | ~400 tok/s                        |
| NVIDIA H200                                    | 141 GB HBM3e              | 4.8 TB/s       | 8.8×        | ~570 tok/s                        |
| NVIDIA B100 / B200 (Blackwell)                 | 192 GB HBM3e              | 8 TB/s         | ~15×        | ~950 tok/s                        |
| NVIDIA B300 (Blackwell Ultra)                  | 288 GB HBM3e              | 8 TB/s         | ~15×        | ~950 tok/s                        |
| NVIDIA Rubin (late 2026, HBM4)                 | 288 GB HBM4               | 13 TB/s        | ~24×        | ~1,500 tok/s                      |
| Groq LPU                                       | 230 MB SRAM per chip      | 80 TB/s on-die | ~146×       | ~9,500 tok/s on paper (see below) |
| SSD offload tier (e.g. Phison aiDAPTIV+)       | TB-scale NAND             | ~7–14 GB/s     | ~0.01–0.03× | ~1–2 tok/s (see below)            |

\* 用我實測的 65 tok/s 按頻寬比例直接外推：同一個每步約 2 GB 的 MoE、batch
1、軟體效率假設不變。真實數字會隨服務框架與 batch 深度移動；這一欄請當成物理上的天花板，而不是 benchmark 成績。

† 尚未發表。Apple 跳過了 M4 Ultra，所以目前 Mac Studio 的頂規停在 M3 Ultra；M5 Ultra 這一列假設 UltraFusion 會把 M5 Max 的 614
GB/s 翻倍，之前每一代 Ultra 都是這個模式。如果真的照這樣出貨，最高階的 Mac 會落在 A100 頻寬的六成左右。

這張表可以讀出四件事。

**Decode 速度與頻寬成正比。**
公開的 SOTA 數字也印證了這件事。[Groq 在 GroqCloud 上以每使用者 460+ tok/s 跑 Llama 4 Scout](https://groq.com/blog/llama-4-now-live-on-groq-build-fast-at-the-lowest-cost-without-compromise)；NVIDIA 則靠 DGX
B200（每顆 GPU 8 TB/s）加上 EAGLE-3 speculative decoding，寫下
[每使用者 1,000 tok/s 的 Llama 4 Maverick 紀錄](https://developer.nvidia.com/blog/blackwell-breaks-the-1000-tps-user-barrier-with-metas-llama-4-maverick/)。引文裡面的 speculative
decoding 看起來是軟體技巧，但它骨子裡解的還是頻寬問題：先便宜地起草一批 token，讓每一次昂貴的全權重讀取一次驗證好幾個，而不是只驗證一個。所以下次看到廠商宣傳驚人的 tokens
per
second，第一個該問的不是「用了什麼排程器」，而是「用了什麼記憶體系統、每個 token 要讀幾個位元組」。而且這招不是資料中心的專利：[mlx-vlm 也支援 speculative decoding](https://github.com/Blaizzy/mlx-vlm/blob/main/docs/usage.md)（EAGLE-3 也在內）。

**Groq 把容量與頻寬的取捨推到了極限。** [80 TB/s 來自直接把權重放在晶片內的 SRAM](https://groq.com/blog/the-groq-lpu-explained)，但每顆晶片只有約 230
MB，所以一個模型得橫跨幾百顆晶片，排成一條 deterministic
pipeline。這等於把這個取捨邏輯整個反過來：每顆晶片幾乎沒有記憶體，但卻有著誇張的頻寬，disaggregation 不是後來的優化，而是這個架構與生俱來的前提。注意上面表格裡的那個 ~9,500
tok/s 純屬理論值：實務上沒有任何模型塞得進單顆晶片，而權重一旦鋪到幾百顆晶片上，單顆 SRAM 的頻寬就不再是你拿來除的那個數字；實際步調由 interconnect
hops 和 pipeline 深度決定，GroqCloud 在這個量級的模型上，實測是每秒幾百個 token，不是幾千。統一記憶體的 Mac 則是同一個設計空間的另一個極端：一整池 128
GB、一顆晶片，每個位元組都同樣都是 546 GB/s。

**SSD offload 是同一道頻寬除法，只是分子小得可憐，而且完全由 decode 承受。**
[Phison 的 aiDAPTIV+](https://www.phison.com/en/aidaptiv-plus-ai-data-storage-solution)
這類方案，用 NAND 把 GPU 記憶體往外擴，容量上看 TB 級，但一顆高速 NVMe 的讀取速度只有約 7–15 GB/s（PCIe
Gen4 到 Gen5），拼個小陣列也不過每秒幾十 GB。一旦把「每一步都要讀」的位元組放上去，那道除法就毫不留情：14 GB/s ÷ 每步約 2 GB，天花板只有約 7
tok/s，這還沒算軟體效率，比最入門的 M4 都慢。Prefill 就寬容得多：一個文件級的 chunk 本來就要算約 1.5 秒，期間把約 2 GB 權重從 SSD 串流進來只需不到 150
ms，只要模型服務框架懂得把傳輸疊在矩陣乘法後面，TTFT 幾乎不受影響。所以規則很簡單：SSD 適合放「每回合只讀一次」的位元組，絕不要放「每步都要讀」的位元組。溢出到 SSD 的 prefix
cache 正是好例子：還原一個 23k token 的 prefix（約 460 MB 的 KV），就算只用一顆 SSD 也遠低於 100
ms，換來的卻是省下幾十秒的 prefill；至於每個 token 都要碰的權重，就得乖乖留在快的記憶體裡。這條分界也解釋了為什麼這類方案主打 fine-tuning 和批次任務，而不是互動式 serving。

**這台 MacBook Pro M4 Max 筆電真正的短板不是頻寬，是 prefill 算力。** 以每瓦頻寬來看，一台整機牆插功耗約一百瓦的筆電有 546
GB/s，而一張光模組本身就要 700 W 的 H100 有 3.35 TB/s，兩者其實在同一個量級。資料中心硬體真正拉開差距的，是矩陣乘法的吞吐量：H100 的 tensor
core 大約是 M4
Max 可用矩陣乘法速率的 15–30 倍，但頻寬優勢只有約 6 倍。這個不對稱，正好解釋了為什麼本案例的問題主要是出在 prefill 而不是 decode；也解釋了為什麼 Apple 在 M5 世代把 Neural
Accelerators 做進每一個 GPU 核心、對準 AI 算力（Apple 宣稱相對 M4 有約 4 倍的 GPU
AI 峰值算力），補的正是這種工作負載最痛的地方。同時，Mac 的老本行沒有變：每塊錢能買到的容量。表裡的 GeForce 列從另一個方向講了同一件事：社群最愛拿來架 LLM 的顯示卡，頻寬是 M4
Max 的兩三倍，但 24 GB 的 RTX 4090 連 128
GB 的五分之一都不到，裝得下的模型根本是另一個量級。而就像前面三個修正展示的，容量買到 cache，cache 讓你跳過 prefill。

## 結論

- **Decode 速度是一道頻寬除法，不是容量的函數。** 546 GB/s ÷ 每步位元組數，天花板就定在那裡。在 Apple
  Silicon 上，能移動天花板的升級是 Ultra 級晶片（頻寬約 819 GB/s，大約提升 50%），不是加 RAM。
- **SOTA 的 tokens per second，大部分是用錢買來的頻寬。** 從 SSD offload 層的約 10 GB/s、MacBook 的 546 GB/s LPDDR、Blackwell 的 8 TB/s
  HBM3e，到 Groq 的 80 TB/s SRAM，單串流 decode 幾乎是線性地跟著記憶體系統走。排程的巧思能讓你逼近天花板；要移動天花板，只能換硬體。
- **多租戶的傷害來自 prefill。** Decode batching 幾乎是免費地共享每一步；但一個文件級的 prefill，就能把所有 decoder 排擠到只剩約 1 tok/s。
- **TTFT 和 ITL 互相拉扯，chunk size 是決定因素。**
  如果 chunk 大，偏向 prompt 的完成時間；反之如果 chunk 小，偏向串流的流暢度。用自己的機器把兩條曲線畫出來，有意識地選甜蜜點，而不是繼承預設值。
- **記憶體容量能買到 cache，cache 能讓你跳過 prefill。** 整條價值鏈就這一句話。先把 prefix cache 的大小對齊你的並行 session 數，再考慮其他優化。
- **優化得針對使用情境。** 要不要量化 KV cache，取決於你的輸入輸出比：像 77:1 這種 prefill 為主的工作負載，prefix
  cache 勝出；但把比例翻過來、變成 decode 為主，量化就正是該做的事。
- **資料中心的解法，可以先用政策算法模擬。** Chunked prefill 加 admission control，近似 stall-free batching；把批次負載導到別的硬體，近似 P/D
  disaggregation。
