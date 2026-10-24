---
title: 'The Patch You Do Not Wait For'
pubDate: 2026-10-22
description:
  'Six security incidents in nine October days: PHP, GitLab, Node.js, LiteLLM, Railway and Zeabur. They share two moves: turn a published fix into an
  exploit, and steal a key that never expires. Here is how the agent-ops at A40 Labs answers: an exploited or Critical vulnerability gets a pull request within 4 hours and
  reaches production within 24.'
author: 'Ping-Lin Chang'
lang: 'en'
image:
  url: '/blog/the-patch-you-do-not-wait-for/header.svg'
  urlLight: '/blog/the-patch-you-do-not-wait-for/header_light.svg'
  alt:
    'The race starts when a vendor publishes a security patch. An attacker can have an exploit within hours; a Critical fix runs Scan, Patch, Gate and Release, with 24 hours as its target.'
tags: ['engineering', 'security', 'agents']
---

In [The Cluster You Do Not Watch](/blog/the-cluster-you-do-not-watch) I described our SRE/Infra agent-ops, which runs most of our infrastructure.
Before, it only watched two things: whether the cluster was healthy and whether it was wasteful. The incidents of 14 to 22 October added a third question: whether what we
run is **known to be vulnerable**, and how fast the fix reaches production.

## Nine days, six incidents

<figure id="table-1" class="table-figure">

| Who                                                                                                                   | When      | What happened                                                                                                                                                                                                |
| --------------------------------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Zeabur](https://zeabur.com/zh-TW/blogs/october-2026-security-incident)                                               | 14–15 Oct | Long-lived admin credentials stored in plain text. The attacker read 3,218,965 environment variables and 321,810 accounts, ran commands in 865 databases, and was mostly after AI API keys.                  |
| [PHP](https://thephp.foundation/blog/2026/10/21/todays-php-security-release-and-how-were-strengthening-php-security/) | 21 Oct    | Two unauthenticated remote code execution bugs, CVSS 9.2. Fixed in 8.2–8.5; 8.1 and older get no fix. Proof-of-concept code is circulating.                                                                  |
| [GitLab](https://docs.gitlab.com/releases/patches/patch-release-gitlab-19-5-1-released/)                              | 21 Oct    | CVSS 10.0: an integer overflow in the regex engine allows code execution without logging in, under certain conditions. Every version from 7.0 (2014) is affected.                                            |
| [Node.js](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases)                                    | 21 Oct    | Ten fixes, four rated High, including a Brotli bug that could allow code execution.                                                                                                                          |
| [LiteLLM](https://docs.litellm.ai/blog/security-incident-oct-21-2026)                                                 | 21 Oct    | Release 1.107.0 was poisoned for about 1¾ hours on PyPI and Docker. The malware steals cloud credentials, AI keys, SSH and Git tokens, and browser passwords. GitHub tokens had leaked from an internal log. |
| [Railway](https://blog.railway.com/p/security-disclosure-wednesday-october-21st)                                      | 21–22 Oct | An attacker may have read customers' environment variables, decrypted for some: API keys, database and registry passwords. Every API token was revoked.                                                      |

<figcaption>Table 1. Each line checked against the vendor's own advisory or postmortem, linked.</figcaption>
</figure>

## Two moves, both far more efficient with AI

Strip the product names away and the week has two attacks in it.

**Read the fix, write the exploit.** PHP, GitLab and Node.js all published patches. A patch tells you exactly which lines were wrong, and turning that
diff into a working exploit used to take a skilled person days. A language model reads a diff and drafts the exploit in a fraction of that. The gap
between "the fix exists" and "the exploit exists" has been closing for years, from an average time-to-exploit of 63 days in 2018–19 to five
days in 2023 ([Mandiant, 2024](https://cloud.google.com/blog/topics/threat-intelligence/time-to-exploit-trends-2023)), and models push it further. The gap between "the fix exists" and "the fix is running" has not
closed at all. A person still has to notice the advisory, file a ticket and wait for a release, and organisations take a median of 43 days to fully
remediate a vulnerability on CISA's Known Exploited list ([Verizon DBIR, 2026](https://www.verizon.com/business/resources/reports/dbir/)). Everything between those two moments
is exposure ([Fig. 1](#figure-1)).

<figure id="figure-1">
  <img src="/blog/the-patch-you-do-not-wait-for/race_light.svg" class="dark:hidden" alt="A timeline on a log scale from the moment a fix is published to 43 days later. An attacker with a model finishes reading the diff, writing the exploit and scanning within hours. Patching by hand takes a median of 43 days, per the Verizon DBIR 2026: someone reads the news, files a ticket, and waits for a release. The span between the two is shaded red and labelled exposed: the exploit exists, the fix is not running. A40 Labs' row for a Critical ends at one day: a PR in 4 hours, staging in 12, production in 24." />
  <img src="/blog/the-patch-you-do-not-wait-for/race_dark.svg" class="hidden dark:block" alt="A timeline on a log scale from the moment a fix is published to 43 days later. An attacker with a model finishes reading the diff, writing the exploit and scanning within hours. Patching by hand takes a median of 43 days, per the Verizon DBIR 2026: someone reads the news, files a ticket, and waits for a release. The span between the two is shaded red and labelled exposed: the exploit exists, the fix is not running. A40 Labs' row for a Critical ends at one day: a PR in 4 hours, staging in 12, production in 24." />
  <figcaption>Figure 1. The attacker's clock starts when the patch is published. Ours starts the moment the advisory matches something we run, within the hour.</figcaption>
</figure>

**Take the key, not the server.** Zeabur, Railway and LiteLLM were not about a clever bug. They were about a secret that lived too long in a place too
many things could read: a plain-text admin credential, environment variables, a token in a log. And the prize has changed. Zeabur's attacker was
mostly after AI API keys, which turn straight into money. LiteLLM is an AI gateway, the one service in a stack that holds every model provider's key,
so poisoning it reaches all of them at once.

The defence against the first move is speed. The defence against the second is having nothing worth stealing that lasts.

## Our countermeasures

The CVE loop has the same shape as everything else in our agent-ops: the agent reads, a pull request is the only thing it
writes, and CI is the gate ([Fig. 2](#figure-2)).

<figure id="figure-2">
  <img src="/blog/the-patch-you-do-not-wait-for/loop_light.svg" class="dark:hidden" alt="Four cards in a row. Scan: an hourly advisory watch, plus a daily full sweep with trivy, govulncheck and gitleaks; an exploited finding is seen within an hour. Patch: in each repo, on a match, bump the dependency with its own tool and run the repo's checks, one PR per finding. Gate: a same-major bump merges itself on green, a major bump waits for a person; CI gates every merge. Release: staging is automatic, production takes a person, who is paged for a Critical, within 24 hours. A dashed arrow returns to Scan: is the fix on main, in staging, in production? Above the cards: every step leaves a pull request or a line in the daily digest, and nothing touches production directly. Two footnotes: a fix that cannot be a pull request goes in the daily digest for the owner to run as one script; a finding is silenced only in one ledger, with a reason and an expiry of at most 90 days." />
  <img src="/blog/the-patch-you-do-not-wait-for/loop_dark.svg" class="hidden dark:block" alt="Four cards in a row. Scan: an hourly advisory watch, plus a daily full sweep with trivy, govulncheck and gitleaks; an exploited finding is seen within an hour. Patch: in each repo, on a match, bump the dependency with its own tool and run the repo's checks, one PR per finding. Gate: a same-major bump merges itself on green, a major bump waits for a person; CI gates every merge. Release: staging is automatic, production takes a person, who is paged for a Critical, within 24 hours. A dashed arrow returns to Scan: is the fix on main, in staging, in production? Above the cards: every step leaves a pull request or a line in the daily digest, and nothing touches production directly. Two footnotes: a fix that cannot be a pull request goes in the daily digest for the owner to run as one script; a finding is silenced only in one ledger, with a reason and an expiry of at most 90 days." />
  <figcaption>Figure 2. The CVE loop. Only the patch step is an agent; the rest is ordinary tooling, and a person merges what reaches production.</figcaption>
</figure>

- **Scan.** An hourly watch reads CISA's Known Exploited Vulnerabilities list and the GitHub and OSV advisory feeds, and matches each new advisory
  against what we last recorded we run. A match that is Critical or exploited fires the patch step within the hour. Behind it, a daily sweep scans
  every lockfile, image digest and pinned chart; `govulncheck` reads the Go call graph, so a finding in a function we never call drops one step in
  severity instead of raising an alarm.
- **Patch.** An agent runs in each repository on its own CI runner, bumps the package with the ecosystem's own tool, runs the repository's checks and
  opens one signed pull request per finding. It may touch manifests, lockfiles and Dockerfiles. It may not touch application code or workflows; a fix
  that needs code stops and asks for a person.
- **Gate.** A same-major bump on a repository that only reaches staging merges itself when CI is green. A major bump, a chart, or anything in
  Terraform waits for a person.
- **Release.** Production's gate does not move: a person merges the production pin. What changed is that severity now sets a deadline: a Critical
  pages the owner and forces a release of its own, and when no patch exists yet, a mitigation (a block rule, a feature switched off) goes in within 4
  hours.

<figure id="table-2" class="table-figure">

| Severity                          | PR opened     | Merged               | In production |
| --------------------------------- | ------------- | -------------------- | ------------- |
| Critical (CVSS ≥ 9, or exploited) | 4 hours       | 12 hours, in staging | 24 hours      |
| High (7.0–8.9)                    | 48 hours      | 7 days               | 14 days       |
| Medium                            | 7 days        | 30 days              | next release  |
| Low                               | monthly batch | the month            | next release  |

<figcaption>Table 2. The clock starts when an advisory first matches something we run, not when someone notices it. Exploited means on CISA's list or with a public proof-of-concept. A Critical gets 24 hours because an exploit now follows a patch within days: Mandiant's average time-to-exploit was five days in 2023.</figcaption>
</figure>

For the second move, the keys: push protection refuses a committed credential at GitHub before it lands, even from a laptop that skipped its hooks,
and gitleaks reads every pull request behind it. The scanner itself keeps no long-lived key on disk: it signs in as two GitHub Apps, one that can
only read code and one that can only post the scan results, whose private keys stay in a secrets store, and it reads the registry with short-lived tokens through workload identity
federation, so no cloud key exists to steal. A secret finding never goes into a report, a pull request or Slack. The run log records only its file and line, never
the value, and the owner rotates it.

## The same model, on our side

If attackers point models at our code, we want to read it first ([Fig. 3](#figure-3)). So we adopted [Strix](https://github.com/usestrix/strix), an open-source AI
penetration tester that we host ourselves. Besides reading code, it can attack running services.
Strix reads a repository the size of our backend in about 25 minutes, and it finds two kinds of problem. Some are known CVEs, which an ordinary scanner
would catch too. The rest are access-control bugs we wrote ourselves, which no CVE scanner can ever see. Those are the reason we run it.

<figure id="figure-3">
  <img src="/blog/the-patch-you-do-not-wait-for/mirror.webp" width="1672" height="917" class="rounded-lg border border-[#d8d7cd] dark:border-[#3a3a4e]" alt="Two cartoon robots face each other across a small central robot labelled same model. Left, in red, the attacker's model: reads the published patch, the fix reveals where to look; builds the exploit, hours of model time, days of human work; finds the unpatched, looking for systems still running the old version. Right, in green, the same model on our side: reads the pull request before the change ships; finds flaws scanners miss, including our own access-control mistakes; fixes it before release, before main and before a patch note exists. A banner reads: read it first, fix it first." />
  <figcaption>Figure 3. The same model, both directions. The advantage belongs to whoever reads the diff first.</figcaption>
</figure>

## What it changes

GitLab's bug, code execution without a login, had been there since version 7.0 in 2014 and was only patched this month.
Whether a bug like that gets written is beyond our CVE loop. What the loop controls is how long we keep running the
vulnerable version once the patch is out. For a Critical, our target is 24 hours; the industry median is 43 days.
