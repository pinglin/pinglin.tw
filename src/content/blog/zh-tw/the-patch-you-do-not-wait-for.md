---
title: '跟漏洞攻擊程式（exploit）賽跑的 patch'
pubDate: 2026-10-22
description:
  '十月中短短九天，PHP、GitLab、Node.js、LiteLLM、Railway、Zeabur 接連出事。仔細看，攻擊手法只有兩種：拿官方釋出的 patch 回推出漏洞攻擊程式（exploit），或是偷走一把永遠不會過期的金鑰。A40 Labs 的對策是：只要漏洞已遭利用或屬於 Critical 等級，agent-ops 在 4 小時內開出 pull request，24 小時內上 production。'
author: '張秉霖'
lang: 'zh-tw'
image:
  url: '/blog/the-patch-you-do-not-wait-for/header.svg'
  urlLight: '/blog/the-patch-you-do-not-wait-for/header_light.svg'
  alt:
    '廠商一發布漏洞的安全 patch，比賽就開始了。攻擊者可能幾小時內就寫好攻擊程式；Critical 的修正要跑完 Scan、Patch、Gate、Release 四站，目標是 24 小時內上線。'
tags: ['工程', '資安', 'agent']
---

我在〈[The Cluster You Do Not Watch](/blog/the-cluster-you-do-not-watch)〉裡介紹過我們的 SRE/Infra agent-ops，整套基礎設施基本上都歸它管。之前它只盯兩件事：cluster 健不健康、資源有沒有浪費。10 月 14 日到 22 日這九天之後，它得多盯一件事：我們跑的東西有沒有**已知漏洞**，有的話，修正多久能上到 production。

## 九天六起事件

<figure id="table-1" class="table-figure">

| 誰                                                                                                                    | 日期           | 經過                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Zeabur](https://zeabur.com/zh-TW/blogs/october-2026-security-incident)                                               | 10 月 14–15 日 | 管理員憑證長期有效，還直接用明文存著。攻擊者讀了 3,218,965 個環境變數和 321,810 個帳號，在 865 個資料庫裡下過指令，主要目標是 AI API key。          |
| [PHP](https://thephp.foundation/blog/2026/10/21/todays-php-security-release-and-how-were-strengthening-php-security/) | 10 月 21 日    | 兩個免驗證的遠端程式碼執行（RCE）漏洞，CVSS 9.2。8.2 到 8.5 已經修補，8.1 以前的版本不會再修。PoC 已經在網路上流傳。                                 |
| [GitLab](https://docs.gitlab.com/releases/patches/patch-release-gitlab-19-5-1-released/)                              | 10 月 21 日    | CVSS 10.0。regex 引擎的整數溢位，在特定條件下不必登入就能執行程式碼，2014 年的 7.0 以來每一版都受影響。                                             |
| [Node.js](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases)                                    | 10 月 21 日    | 一次修了十個漏洞，其中四個是 High，包括一個可能導致程式碼執行的 Brotli 漏洞。                                                                       |
| [LiteLLM](https://docs.litellm.ai/blog/security-incident-oct-21-2026)                                                 | 10 月 21 日    | 有人在 PyPI 和 Docker 上發布了藏有惡意程式的 1.107.0 版，約 1¾ 小時後下架。惡意程式會偷雲端憑證、AI 金鑰、SSH 和 Git token，連瀏覽器存的密碼也不放過。在這之前，GitHub token 已經從內部 log 外洩。 |
| [Railway](https://blog.railway.com/p/security-disclosure-wednesday-october-21st)                                      | 10 月 21–22 日 | 攻擊者可能讀到客戶的環境變數，部分還是解密後的明文，包括 API key、資料庫與 registry 密碼。Railway 已撤銷全部 API token。                             |

<figcaption>表 1。每一筆都對照過廠商本身的公告或 postmortem，點名稱就能看原文。</figcaption>
</figure>

## 有了 AI，攻擊的效率高出許多

六起事件看下來，攻擊者用的其實只有兩招。

**看 patch 寫攻擊程式**。PHP、GitLab 和 Node.js 都發布了 patch。patch 本身就標出了哪幾行有問題。以前高手也得花上好幾天，才能照著 diff 寫出漏洞攻擊程式（exploit）；現在丟給語言模型，沒多久就能生出初稿。「patch 出來」到「攻擊程式出來」的時間差這幾年本來就在縮短，漏洞的平均被利用時間（time-to-exploit）從 2018–19 年的 63 天降到 2023 年的 5 天（[Mandiant, 2024](https://cloud.google.com/blog/topics/threat-intelligence/time-to-exploit-trends-2023)），語言模型只會讓它縮得更快。但「patch 出來」到「patch 真正上線」的時間差完全沒縮。還是要等有人看到公告、開 ticket、排進下一次 release，企業完整修補一個列在 CISA 已知遭利用清單上的漏洞，中位數是 43 天（[Verizon DBIR, 2026](https://www.verizon.com/business/resources/reports/dbir/)）。這兩個時間點之間，系統就一直暴露在風險裡（[圖一](#figure-1)）。

<figure id="figure-1">
  <img src="/blog/the-patch-you-do-not-wait-for/race_light.svg" class="dark:hidden" alt="一條對數刻度的時間軸，從 patch 發布的那一刻延伸到 43 天後。有模型幫忙的攻擊者，幾小時內就讀完 diff、寫好攻擊程式，開始掃描目標。根據 Verizon DBIR 2026，人工修補完成的中位數是 43 天：有人看到新聞、開 ticket、等 release。兩者之間的區段塗成紅色，標註為曝險期：攻擊程式已經有了，patch 卻還沒上線。A40 Labs 處理 Critical 漏洞的那一列在一天處結束：4 小時開 PR、12 小時上 staging、24 小時上 production。" />
  <img src="/blog/the-patch-you-do-not-wait-for/race_dark.svg" class="hidden dark:block" alt="一條對數刻度的時間軸，從 patch 發布的那一刻延伸到 43 天後。有模型幫忙的攻擊者，幾小時內就讀完 diff、寫好攻擊程式，開始掃描目標。根據 Verizon DBIR 2026，人工修補完成的中位數是 43 天：有人看到新聞、開 ticket、等 release。兩者之間的區段塗成紅色，標註為曝險期：攻擊程式已經有了，patch 卻還沒上線。A40 Labs 處理 Critical 漏洞的那一列在一天處結束：4 小時開 PR、12 小時上 staging、24 小時上 production。" />
  <figcaption>圖一。patch 發布的那一刻，攻擊者就開始計時；我們的時鐘則從公告比對到我們在跑的東西那一刻起算，最晚不超過一小時。</figcaption>
</figure>

**偷金鑰，不打伺服器**。Zeabur、Railway、LiteLLM 這三起事件，都不需要什麼高明的漏洞。問題都出在金鑰、密碼這類 secret 存放太久，又放在太多程式讀得到的地方：明文的管理員憑證、環境變數、寫進 log 的 token。而且攻擊者想要的東西也變了。Zeabur 的攻擊者主要在找 AI API key，因為那能直接變現。LiteLLM 是 AI gateway，整個 stack 裡只有它握有所有模型供應商的金鑰，在它身上下毒，就能一次拿到全部。

第一招要靠速度擋。第二招要擋，就得讓手上沒有任何值得偷、又能長期使用的東西。

## 我們的對策

CVE 迴圈沿用 agent-ops 一貫的做法：agent 負責讀，唯一會寫出來的是 pull request，最後由 CI 把關（[圖二](#figure-2)）。

<figure id="figure-2">
  <img src="/blog/the-patch-you-do-not-wait-for/loop_light.svg" class="dark:hidden" alt="四張卡片排成一列。Scan：每小時看一次安全公告，每天再用 trivy、govulncheck、gitleaks 完整掃一輪；已遭利用的漏洞，一小時內就會發現。Patch：比對到之後，在每個 repo 裡用它原生的工具升級相依套件、跑 repo 的檢查，每個 finding 開一個 PR。Gate：同一個 major 版本內的升級，CI 綠燈就自動 merge；跨 major 的升級要等人確認。每次 merge 都要先過 CI。Release：staging 自動部署，production 要有人 merge；Critical 會 page 負責人，24 小時內上線。一條虛線箭頭繞回 Scan：修正進 main 了沒？上 staging 了沒？上 production 了沒？卡片上方寫著：每一步都會留下一個 pull request 或每日摘要裡的一行，沒有任何東西直接動到 production。兩條註腳：沒辦法用 PR 修的，列進每日摘要，由負責人跑一支 script 處理；要壓下某個 finding，只能記在同一本帳上，附上理由，期限最長 90 天。" />
  <img src="/blog/the-patch-you-do-not-wait-for/loop_dark.svg" class="hidden dark:block" alt="四張卡片排成一列。Scan：每小時看一次安全公告，每天再用 trivy、govulncheck、gitleaks 完整掃一輪；已遭利用的漏洞，一小時內就會發現。Patch：比對到之後，在每個 repo 裡用它原生的工具升級相依套件、跑 repo 的檢查，每個 finding 開一個 PR。Gate：同一個 major 版本內的升級，CI 綠燈就自動 merge；跨 major 的升級要等人確認。每次 merge 都要先過 CI。Release：staging 自動部署，production 要有人 merge；Critical 會 page 負責人，24 小時內上線。一條虛線箭頭繞回 Scan：修正進 main 了沒？上 staging 了沒？上 production 了沒？卡片上方寫著：每一步都會留下一個 pull request 或每日摘要裡的一行，沒有任何東西直接動到 production。兩條註腳：沒辦法用 PR 修的，列進每日摘要，由負責人跑一支 script 處理；要壓下某個 finding，只能記在同一本帳上，附上理由，期限最長 90 天。" />
  <figcaption>圖二。CVE 迴圈。只有 patch 這一步交給 agent，其餘都是一般工具，上 production 的則由人來 merge。</figcaption>
</figure>

- **Scan**。一支每小時執行的程式會讀取 CISA 的 Known Exploited Vulnerabilities 清單，以及 GitHub、OSV 的安全公告 feed，再把每則新公告拿來比對我們最近一次記錄的部署清單。只要比對到 Critical 或已遭利用的漏洞，一小時內就會觸發 patch 步驟。每天還會再完整掃過一次所有 lockfile、image digest 和鎖定版本的 chart。`govulncheck` 會分析 Go 的 call graph，如果漏洞落在我們從沒呼叫過的函式，嚴重度就降一級，不會直接發出告警。
- **Patch**。每個 repo 都在自己的 CI runner 上跑一個 agent。agent 用該生態系原生的工具升級套件、執行 repo 既有的檢查，每個 finding 各開一個經過簽章的 pull request。它可以改 manifest、lockfile 和 Dockerfile，但不能動應用程式碼或 workflow；需要改程式碼才能修的，就停下來交給人處理。
- **Gate**。只部署到 staging 的 repo，同一 major 版本內的升級只要 CI 綠燈就會自動 merge。跨 major 的升級、chart，以及任何 Terraform 的變更，一律等人審核。
- **Release**。production 的把關方式不變：production pin 仍然由人 merge。不同的是，現在每個嚴重度都有期限：Critical 會 page 負責人，並單獨發一次 release；如果還沒有 patch，4 小時內要先上緩解措施，例如加一條封鎖規則，或先關掉某個功能。

<figure id="table-2" class="table-figure">

| 嚴重度                           | 開 PR    | merge               | 上 production  |
| -------------------------------- | -------- | ------------------- | -------------- |
| Critical（CVSS ≥ 9，或已遭利用） | 4 小時   | 12 小時，上 staging | 24 小時        |
| High（7.0–8.9）                  | 48 小時  | 7 天                | 14 天          |
| Medium                           | 7 天     | 30 天               | 下一次 release |
| Low                              | 每月一批 | 當月                | 下一次 release |

<figcaption>表 2。從安全公告第一次比對到我們在用的東西就開始計時，而不是等有人注意到。「已遭利用」指列在 CISA 清單上，或已有公開的 PoC。Critical 訂 24 小時，是因為攻擊程式現在幾天內就會跟上 patch：Mandiant 統計 2023 年的平均被利用時間是 5 天。</figcaption>
</figure>

至於第二招，重點是別讓金鑰外洩。push protection 會在 GitHub 端攔下含有憑證的 commit，就算有人從筆電跳過 hook 直接 push，也進不了 repo；gitleaks 也會再檢查每一個 pull request。掃描器本身也不在硬碟上放長效金鑰：它以兩個 GitHub App 的身分登入，一個只能讀程式碼，另一個只能回寫掃描結果，兩者的私鑰都放在 secret 管理系統裡；讀 registry 時則透過 workload identity federation 取得短效 token，根本沒有雲端金鑰可以偷。掃到的 secret 不會出現在報告、pull request 或 Slack 裡；執行 log 只記它在哪個檔案、哪一行，不記內容，再由負責人輪替。

## 同一個模型，也能站在我們這邊

攻擊者既然會用模型讀我們的程式碼，我們就要比他們先讀（[圖三](#figure-3)）。所以我們採用了 [Strix](https://github.com/usestrix/strix)，一套開源的 AI 滲透測試工具，由我們自己 host。它除了讀程式碼，也能對執行中的服務實際發動攻擊。一個跟我們 backend 差不多大的 repo，Strix 大約 25 分鐘就能讀完。找到的問題有兩種：一種是已知的 CVE，一般的掃描器也抓得到；另一種是我們自己寫出來的存取控制 bug，任何 CVE 掃描器都看不到。我們用 Strix，就是為了後面這一種。

<figure id="figure-3">
  <img src="/blog/the-patch-you-do-not-wait-for/mirror.webp" width="1672" height="917" class="rounded-lg border border-[#d8d7cd] dark:border-[#3a3a4e]" alt="兩隻卡通機器人分站兩邊，中間一隻小機器人標著「同一個模型」。左邊紅色的是攻擊者的模型，三個步驟是：讀已發布的 patch，修正本身就透露該往哪裡找；寫出攻擊程式，模型幾小時就好，人工要好幾天；找出還在跑舊版的系統。右邊綠色的是站在我們這邊的同一個模型：在變更上線前讀 pull request；找出掃描器漏掉的問題，包括我們自己寫錯的存取控制；在 release 前修好，早於進 main，也早於 patch note。底部橫幅寫著：先讀，先修。" />
  <figcaption>圖三。同一個模型，兩個方向。誰先讀到 diff，誰就佔上風。</figcaption>
</figure>

## 能改變的是什麼

GitLab 那個不用登入就能執行程式碼的漏洞，從 2014 年的 7.0 版就在了，直到這個月才修補。漏洞會不會出現在程式碼裡，CVE 迴圈管不了；它管的是 patch 發布之後，我們還要帶著有漏洞的版本跑多久。對 Critical 漏洞，我們的目標是 24 小時；業界的中位數是 43 天。
