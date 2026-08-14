---
title: 'The Shapes of Agent Memory – Files, Stores, and Experience'
pubDate: 2026-08-12
description:
  'An agent that remembers across sessions can keep its memory as curated markdown files, as an auto-mined structured store, or as trained experience.
  I measured all of them: files against a structured store under one fixed model, a store-only head-to-head across the structured lineages, and an
  experience bank on the agentic benchmarks where the state of the art trains memory into the weights.'
author: 'Ping-Lin Chang'
lang: 'en'
hidden: true
draft: true
image:
  url: '/blog/the-shapes-of-agent-memory/header.svg'
  urlLight: '/blog/the-shapes-of-agent-memory/header_light.svg'
  alt:
    'Three side-by-side memory shapes: a file-based index of markdown lines, a structured store of embedded units linked by a graph, and trajectories
    of agent experience with one successful episode ringed.'
tags: ['engineering', 'agents']
---

An agent that only remembers within one conversation is a stranger with excellent manners: it greets you warmly every single day, and it has no idea
who you are. The moment you want it to know your projects, your preferences, and the thing you told it last Tuesday, you need memory that outlives the
context window. There are three common shapes a modern agent memory system takes ([Fig. 1](#figure-1)). Two are stores that sit beside a frozen model,
and they anchor opposite ends of a design axis; the third moves the memory behavior into the model itself.

The first keeps memory as **files the model curates**: a short index plus topic files, written in plain markdown, read back by searching and reading
them like any other file. It is what a coding agent reaches for when it has a filesystem and no database, and it is what
[Claude Code](https://code.claude.com/docs/en/memory), [Cline](https://docs.cline.bot/best-practices/memory-bank),
[Cursor](https://docs.cursor.com/context/memories), and [Windsurf](https://docs.windsurf.com/windsurf/cascade/memories) ship today.
[OpenClaw](https://docs.openclaw.ai/concepts/memory) is the most thoroughly worked-out version of it: its default `memory-core` plugin keeps a curated
`MEMORY.md` beside dated session logs, and it adds a background consolidation pass that the other file-based products do not have. The second keeps
memory as a **structured store**: every turn is mined into small atomic facts, embedded into a vector index, threaded into a temporal graph, and read
back by ranked retrieval. It is what you build when memory is the product, and it is what the dedicated memory startups
[mem0](https://mem0.ai/research), [Letta](https://www.letta.com/blog/agent-memory/), and [Zep](https://arxiv.org/abs/2501.13956) sell. The third keeps
memory as **experience the model is trained to use**: episodes still land in a bank, but everything that makes them memory, what to retrieve, whether
to trust it, how to turn it into action, is trained into the acting policy by reinforcement learning. It is the agentic state of the art
([MemHarness](https://github.com/KnowledgeXLab/MemHarness)), the shape the field reaches for when retrieval stops paying, and it is where this post
ends.

In this post, I measure which shape is better rather than argue it, which meant building the first two. The structured arm is a [hybrid](#hybrid) of
the [two structured lineages](#two-lineages-place-and-entity-and-time), plus a layer neither has: an associative graph learned from which places
actually get retrieved together, so recall can reach an item the query never ranked. The [file-based arm](#file-based) is a reconstruction of a
shipping coding agent's auto-memory, traced claim by claim to public documentation and
[published with its spec](https://github.com/a40-labs/memory/tree/main/systems/file-based), not a strawman written to lose. Both run behind the _same_
agent loop, on the _same_ local open-weight model, scored by the _same_ judge on the same public benchmark, so only the memory layer can move the
number, and every per-question row with the scripts that recompute each figure is in [a40-labs/memory](https://github.com/a40-labs/memory). Hosted
models come in where fairness demands: the [head-to-head](#the-lineages-head-to-head) reads every store through one shared reader and judge,
`gpt-4o-mini`, the same model the graph vendor's own numbers were scored with; the agentic experiment fields a frontier actor, `claude-sonnet-5`. The
[trained shape](#experience-architecture) cannot join the controlled comparison at all, because the training _is_ the method: unplug its bank and you
have a different policy, not a baseline. The [last section](#remembering-what-worked-the-agentic-benchmarks) meets it on its home ground instead.

**TL;DR** The structured store beats files on accuracy and on token cost at once; files win where memory stays small, or where the right answer is "I
don't know". Against my own interest, the hybrid's place-plus-time structure buys nothing over a plain vector index on LoCoMo; paired on long-haystack
LongMemEval-M the same two stores separate by 15 significant points in the hybrid's favour, so structure pays exactly where histories grow long, and
no single benchmark ranks memory systems. Swapping the model that reads the memory moves the score further than swapping between any two of the stores
that work, which is why numbers do not travel between protocols. On the agentic benchmarks, retrieved experience pays only where the actor is weak and
has headroom left; where the task yields to reasoning, a frontier actor reaches the trained system's bar with no memory at all, and where the reward
has a shape only practice teaches, the trained policy stands alone.

<figure id="figure-1">
  <img src="/blog/the-shapes-of-agent-memory/overview_light.svg" class="dark:hidden" alt="Two panels. Left, store-based memory: a frozen model writes to and reads from a store beside it, the store holding both kinds, file lines and structured dots; writes come from the model's curation or an embedder, reads from grep or ranked recall; it bolts onto any model and is paid at write and read time. Right, experience-based memory: an actor enclosed in a dashed trained-by-reinforcement-learning boundary exchanges episodes with an episode bank, writing finished episodes back and retrieving them; one model, inseparable, paid in training compute." />
  <img src="/blog/the-shapes-of-agent-memory/overview_dark.svg" class="hidden dark:block" alt="Two panels. Left, store-based memory: a frozen model writes to and reads from a store beside it, the store holding both kinds, file lines and structured dots; writes come from the model's curation or an embedder, reads from grep or ranked recall; it bolts onto any model and is paid at write and read time. Right, experience-based memory: an actor enclosed in a dashed trained-by-reinforcement-learning boundary exchanges episodes with an episode bank, writing finished episodes back and retrieving them; one model, inseparable, paid in training compute." />
  <figcaption>Figure 1. Where memory lives. Store-based memory bolts a writable, searchable store onto any frozen model and pays at write and read
  time; experience-based memory keeps a bank too, but trains the model's use of it, paying in training compute.</figcaption>
</figure>

## Store architectures

<figure id="figure-2">
  <img src="/blog/the-shapes-of-agent-memory/architecture_light.svg" class="dark:hidden" alt="Two panels. Left, file-based memory: a new turn leads the model to write or edit a file, a one-line entry into a roughly 200-line MEMORY.md index, which points to separate topic files; reading means putting the index in context then grepping and reading files, with no embeddings and literal search. Right, structured memory: a new turn is auto-extracted into atomic units that are embedded with no LLM write, split into a dense-plus-sparse vector store and a temporal fact graph that supersedes old facts, consolidated in the background, and read back by ranked retrieval plus a preload of salient units." />
  <img src="/blog/the-shapes-of-agent-memory/architecture_dark.svg" class="hidden dark:block" alt="Two panels. Left, file-based memory: a new turn leads the model to write or edit a file, a one-line entry into a roughly 200-line MEMORY.md index, which points to separate topic files; reading means putting the index in context then grepping and reading files, with no embeddings and literal search. Right, structured memory: a new turn is auto-extracted into atomic units that are embedded with no LLM write, split into a dense-plus-sparse vector store and a temporal fact graph that supersedes old facts, consolidated in the background, and read back by ranked retrieval plus a preload of salient units." />
  <figcaption>Figure 2. The same job, two architectures. File-based memory puts the model on the write path and a text search on the read path. Structured
  memory puts an embedder on the write path and a ranker on the read path.</figcaption>
</figure>

Both sit beside a frozen model and persist facts across sessions. The difference that matters is _who does the work, and when_.

### File-based

File-based memory spends its budget at write time, through the model. After a turn, the model decides whether anything is worth keeping, and if so it
edits a file: a new line in the index, or a paragraph in a topic file. The index is small on purpose, because it is loaded into context every session;
a common budget is the first 200 lines or so. Everything else lives in topic files that are _not_ loaded until the model goes and reads them. Recall
is therefore whatever the model can find by keeping the index in view and grepping the rest. There is no embedder and no ranker. The whole system is
the model's own judgment plus a text search, which is exactly why it is so easy to ship: if you have file tools, you have this.

This approach is everywhere in shipping coding agents: Claude Code's auto-memory (a per-project `MEMORY.md` index over model-curated topic files), the
[memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) primitive in Anthropic's API, the community's
[Cline "Memory Bank"](https://docs.cline.bot/best-practices/memory-bank) and its descendants, and the automatic memories in Cursor and Windsurf. Keep
it distinct from the _instruction_-file family (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`), which is human-authored static context; the accumulated,
model-written kind is what this post evaluates.

### Structured

Structured memory spends its budget at write time too, but not through the model. Every turn is mined into atomic units, each embedded and stored with
dense and sparse vectors, and salient facts are threaded into a graph whose edges carry validity windows so a later fact can supersede an earlier one.
A background pass consolidates duplicates and merges the graph. Nothing on the write path asks the model to reason; it is extraction and embedding.
Recall is a ranked hybrid query, and the most salient units are preloaded before the first user word, so the agent often answers without searching at
all.

This is what the dedicated memory startups sell: [mem0](https://mem0.ai/research) extracts facts into a vector-first store with an optional graph
layer, [Letta](https://www.letta.com/blog/agent-memory/) (formerly MemGPT) pages tiered memory in and out of context, and
[Zep](https://arxiv.org/abs/2501.13956) builds a bi-temporal knowledge graph, the strongest form of the idea. All of them put an extractor and a
ranker where the file-based approach puts the model's judgment and a grep.

Two design decisions fall straight out of this split, and they are the whole game:

- **What gets saved.** File-based memory saves what the model _chooses_ to save. Structured memory saves _everything_, then ranks.
- **What gets found.** File-based memory finds what a literal search surfaces from an index that must stay small. Structured memory finds what a
  similarity ranker surfaces from a store that can grow without bound.

#### Two lineages: place, and entity-and-time

Calling all of that one "shape" hides a real split, because the structured pole has two lineages that organize memory around opposite primitives: **by
place, or by entity and time.**

The place-organized lineage files memory by _where it belongs_ rather than by who it is about. [MemPalace](https://github.com/mempalace/mempalace) is
the cleanest public example: people and projects become wings, topics become rooms, and the original conversation text lives in drawers inside them,
retrieved by semantic search scoped to a region rather than swept across a flat corpus. The defining choice is what it declines to do at write time.
It stores the text verbatim, and does not summarize, extract, or paraphrase, so ingest is an embedding and a filing decision with no model reasoning
in it at all. Its structural weakness is aggregation: an answer scattered across many rooms depends on one ranked query surfacing all of it at once,
and no artifact in the store has gathered it in advance.

The entity-and-time lineage (Zep's [Graphiti](https://github.com/getzep/graphiti)) stores a knowledge graph instead: raw messages kept as ground
truth, LLM-extracted entity nodes that are resolved and deduplicated across sessions and carry maintained summaries, and one-line distilled fact edges
between entities. Every edge holds validity timestamps, relative dates are resolved to absolute ones at ingest, and a contradicting new fact _closes
the old edge's validity window_ rather than deleting it. The reader receives distilled facts with date ranges plus entity summaries, never raw
messages. The cost inverts: an LLM reasons at ingest, on every message, for extraction, resolution, and invalidation.

<figure id="figure-3">
  <img src="/blog/the-shapes-of-agent-memory/two_lineages_light.svg" class="dark:hidden" alt="Two panels. Left, place-organized: an always-loaded tray of identity and salient facts above three rooms holding fact chips, with a solid scoped-recall arrow into one room and a dashed broad-search arrow across all rooms; tagline cheap writes, no entity merge, freshness by ranking. Right, entity-and-time: one resolved entity node with edges to fact chips, each carrying a date range, one edge dashed with its validity window closed as superseded, and a timeline strip showing a new fact closing the old fact's window; tagline entity aggregation, validity windows, LLM at ingest." />
  <img src="/blog/the-shapes-of-agent-memory/two_lineages_dark.svg" class="hidden dark:block" alt="Two panels. Left, place-organized: an always-loaded tray of identity and salient facts above three rooms holding fact chips, with a solid scoped-recall arrow into one room and a dashed broad-search arrow across all rooms; tagline cheap writes, no entity merge, freshness by ranking. Right, entity-and-time: one resolved entity node with edges to fact chips, each carrying a date range, one edge dashed with its validity window closed as superseded, and a timeline strip showing a new fact closing the old fact's window; tagline entity aggregation, validity windows, LLM at ingest." />
  <figcaption>Figure 3. The two lineages. Place-organized memory files facts by location and loads in layers; entity-and-time memory keys every fact to
  a resolved entity and stamps it with a validity window a new fact can close.</figcaption>
</figure>

Three consequences follow ([Fig. 3](#figure-3)):

- **Aggregation.** An entity node accumulates every fact about a person _by construction_, so an enumeration question ("what are all of X's hobbies?")
  arrives with a pre-built aggregate. A place-organized store has no such artifact: it must hope one ranked query surfaces every scattered item, and
  the members of an enumerable answer are usually semantically far apart (running, pottery, and movie nights share little beyond the person), so no
  single query ranks them all into the top-k even when every item is in the store. Keep this weakness in mind for the results: the hardest questions
  for this study's structured arm, on both benchmarks, are exactly the ones that assemble an answer from facts scattered across many sessions.
- **Time.** Supersession lives in the store for one lineage (validity windows the reader can trust) and in ranking heuristics for the other.
- **Cost.** Place-organized is cheap at write time and leans on retrieval; entity-and-time pays heavy LLM cost at ingest to make reading cheap and
  precise.

Neither dominates. If your workload is scoped recall over evolving topics, the place lineage's load layers are the better fit; if it is cross-session
aggregation and "what is true now", the graph lineage earns its ingest bill. Which raises the obvious question: why not take the cheap half of each?

### Hybrid

The hybrid takes exactly that bargain, and it is the design this study measures ([Fig. 2](#figure-2)'s right panel is its architecture). Take the
place-organized store's write path wholesale: atomic dated facts filed by location, embedded with no LLM reasoning, recalled by layered loads and
ranked hybrid search. Then borrow one thing from the entity-and-time lineage: validity windows, so a contradicting new fact can close an old one's
window instead of competing with it at recall time. That combination is not unique to this study, and it would be misleading to imply otherwise:
MemPalace ships a temporal entity graph with validity windows of its own, alongside its rooms. What differs here is smaller and more specific, and it
is the third layer below.

What the hybrid buys is the cost profile of place with the time semantics of the graph: writes stay embedder-cheap, and "what is true now" questions
get dated, supersedable facts rather than ranking heuristics alone. One temporal nuance the graph lineage does not spell out: supersession must
distinguish conflicting _states_ from additive _events_. "Works at Acme" should close "works at Beta"; "scored 2 goals this week" must never close
"scored 3 goals last week", or counting questions become unanswerable. What the hybrid deliberately leaves out is the graph lineage's expensive half:
no LLM at ingest, so no entity resolution and no maintained summaries, and cross-session aggregation stays its structural weak point.

The design's answer to that weak point is a third layer the two lineages do not have: an **associative graph learned from usage statistics**.
Locations that co-occur in retrievals more often than chance predicts get linked (a statistical test, not embedding similarity: "these go together" is
a stronger claim than "these look alike"), and recall runs as _anchor, expand, fuse_: ranked search anchors on what it can find, the association graph
expands to linked locations the query never ranked, and the fused result caps the graph's contribution ([Fig. 4](#figure-4)). The principle underneath
answers both lineages' disclosed failure modes at once: **the graph can only add recall, never subtract it.** Where the entity-and-time store is
hard-bounded by its extractor, the hybrid keeps raw dated facts as the anchor, so a graph failure degrades to plain ranked retrieval; and where pure
place organization can never _reach_ an item its one query failed to rank, expansion gives it a query-independent path there.

<figure id="figure-4">
  <img src="/blog/the-shapes-of-agent-memory/hybrid_light.svg" class="dark:hidden" alt="One panel. Three rooms of dated fact chips form the place core. In the middle room a current fact with an open validity window sits above a superseded fact whose window is closed, labeled a new fact closes the old fact's window. A dashed orange association arc links the first and third rooms, labeled as learned from places that co-occur in retrievals beyond chance. Recall flows in three numbered steps: a query anchors on one room by ranked hybrid search, expands along the learned association to a room the query never ranked, and fuses both into a capped context where the graph augments recall but never swamps it." />
  <img src="/blog/the-shapes-of-agent-memory/hybrid_dark.svg" class="hidden dark:block" alt="One panel. Three rooms of dated fact chips form the place core. In the middle room a current fact with an open validity window sits above a superseded fact whose window is closed, labeled a new fact closes the old fact's window. A dashed orange association arc links the first and third rooms, labeled as learned from places that co-occur in retrievals beyond chance. Recall flows in three numbered steps: a query anchors on one room by ranked hybrid search, expands along the learned association to a room the query never ranked, and fuses both into a capped context where the graph augments recall but never swamps it." />
  <figcaption>Figure 4. The hybrid. The place core keeps raw dated facts cheap to write; a validity window lets a new fact close an old one; recall
  anchors on ranked search, expands along usage-learned associations to places the query never ranked, and fuses with a cap, so the graph can add
  recall but never subtract it.</figcaption>
</figure>

One scope note for honesty, and it is a large one: the benchmark protocol below writes facts directly into the store, which never triggers the
background consolidation where supersession lives (the next subsection is about that pass), and the association graph starts empty. So the
configuration actually measured is the hybrid's place-organized core: dated facts plus hybrid ranked search. Read its scores as a floor, with one
update from later work that cuts against my own design: when the association graph was subsequently seeded from real co-retrieval statistics and given
one controlled, paired shot at exactly the aggregation failures it exists to fix, it changed nothing. No harm (the capped fusion held), but no
recovery either. The associative layer stays a design capability, not a measured contributor.

### Consolidation

Every architecture so far has been described by two paths, write and read, and every description is incomplete. There is a third path, and it is not a
fourth architecture: a pass that runs between sessions and reorganizes what is already stored. The field calls it **dreaming**, after the
consolidation that happens in sleep, and it is the only path that can repair a store that is already wrong.

It cuts across the taxonomy rather than extending it. Files can be consolidated, place-organized stores can be consolidated, and the entity-and-time
lineage consolidates so eagerly it is easy to miss: resolving a mention against existing entities and closing a superseded fact's window is exactly
this work, moved to ingest and paid per message. That relocation is the real choice on offer. Consolidate at ingest and every write pays for order the
store may never need; consolidate in the background and writes stay cheap while the store carries its own mess until the pass comes around.

The two implementations below sit at opposite ends of that trade ([Fig. 5](#figure-5)).

<figure id="figure-5">
  <img src="/blog/the-shapes-of-agent-memory/dreaming_light.svg" class="dark:hidden" alt="Two panels. Left, file-based memory promotes upward: a short-term buffer of items labelled by how often each was recalled, with the frequently recalled ones promoted by arrows into a MEMORY.md box loaded every session, gated on score, recall count, and distinct queries. Right, the structured store merges sideways: three differently worded restatements of one fact collapse into a single canonical unit carrying the provenance of all three, annotated with the merge rule, a cosine bar of 0.92 on vectors the store already has, no model calls, and its tiers of exact dedup on write, per chat when idle, and whole store daily; a dashed note adds that a version phrased in entirely different words is missed and catching it would need a model to judge each pair." />
  <img src="/blog/the-shapes-of-agent-memory/dreaming_dark.svg" class="hidden dark:block" alt="Two panels. Left, file-based memory promotes upward: a short-term buffer of items labelled by how often each was recalled, with the frequently recalled ones promoted by arrows into a MEMORY.md box loaded every session, gated on score, recall count, and distinct queries. Right, the structured store merges sideways: three differently worded restatements of one fact collapse into a single canonical unit carrying the provenance of all three, annotated with the merge rule, a cosine bar of 0.92 on vectors the store already has, no model calls, and its tiers of exact dedup on write, per chat when idle, and whole store daily; a dashed note adds that a version phrased in entirely different words is missed and catching it would need a model to judge each pair." />
  <figcaption>Figure 5. Consolidation in both store architectures. The file-based version runs a model nightly to promote what usage proves valuable
  into the always-loaded index; the place-organized store collapses restatements into one canonical unit on similarity alone, spending no model calls
  at all.
  That thrift is also the bound: similarity catches restatements and misses paraphrase, which is where the cost of judgment comes back.</figcaption>
</figure>

[OpenClaw](https://docs.openclaw.ai/concepts/dreaming) runs the file-based version nightly, in three phases borrowed from a night's sleep: a light
phase deduplicates the recent buffer, a phase named after REM (the rapid-eye-movement stage where human brains replay the day and connect it to older
memories) looks across conversations for recurring themes, and a deep phase promotes survivors into `MEMORY.md`, the index every session loads. What
makes it more than cleanup is the gate: an item earns its place by being _used_, clearing a score threshold and several recalls across distinct
queries. The store learns what matters from what the agent kept reaching for, a signal neither the write nor the read path can see.

This study's hybrid does the same job on different material, in three tiers. Identical writes never duplicate, because a unit's content hash is its
primary key. A minute after a conversation goes idle, a pass rebuilds that conversation's index cards. Then once a day the whole store is swept: units
are clustered by similarity, using the vectors they already carry, and each cluster collapses to its longest phrasing with the others' provenance
folded in. The bar is set high so merely _related_ facts stay apart, and because the pass reuses stored vectors instead of re-embedding, it spends no
model calls at all. So OpenClaw promotes upward into a file the model reads; the hybrid collapses sideways into a store the ranker searches.

Two limits come with that design, and both are visible before any measurement. Cheap similarity catches restatements but misses the same event told in
other words, and closing that gap means a model judging each pair, which puts per-item reasoning cost back into the one path that had none. And the
value of tidying at all depends on the reader: a model answers correctly about a handful of restatements sitting in front of it, merged or not, so
storage-level cleanup earns its keep only once duplicates outnumber what the reader can hold. Consolidation pays most on long histories read by weak
models, least on short ones read by strong ones, which is what the measurements later show: run at roughly fifty sessions per history it merged real
duplicates and bought no accuracy, and the main experiment never triggers it at all, so every number reported for the structured arm is a floor.

## Experience architecture

Every store architecture above shares one assumption so basic it is easy to miss: **the model that uses the memory is frozen.** The store gets
smarter, better ranking, better structure, better time semantics; the reader of it does not. The agentic memory line of work drops exactly that
assumption, and [MemHarness](https://github.com/KnowledgeXLab/MemHarness) ([paper](https://arxiv.org/abs/2607.28272)) is its cleanest current example:
hold the store simple, and train the model's _use_ of it instead.

The bank half looks deliberately familiar ([Fig. 6](#figure-6)). After every episode the trajectory is summarized and written into a vector store with
semantic embeddings, deduplicated semantically, and periodically pruned by empirical utility, so entries that keep paying rent stay. By this post's
taxonomy that is a structured store: inspectable, swappable, nothing a reader of the sections above has not seen.

The difference is everything downstream of retrieval. Where a store architecture hands retrieved items to a frozen model and hopes its judgment
suffices, the experience architecture makes that judgment the trained object. Acting is a five-stage policy: **observe** the current state;
**retrieve** the top-k experiences, each paired with the source observation it was learned from; **critique** the retrieved experience against the
current state (does this actually apply here?); **reconstruct** it into state-specific guidance when it does, or reject it and fall back to
self-reasoning when it does not; then **act**. The whole pipeline is trained end-to-end with reinforcement learning (GRPO, group-relative policy
optimization over grouped rollouts, with format rewards that keep the retrieval and reconstruction stages from collapsing), cold-started from a couple
hundred teacher-written memory records.

<figure id="figure-6">
  <img src="/blog/the-shapes-of-agent-memory/experience_light.svg" class="dark:hidden" alt="A pipeline of five stages: observe the current state, retrieve top-k experiences with source context, critique whether they apply here, reconstruct them into state-specific guidance, and act in the environment. A dashed reject path skips from critique to act, labeled fall back to self-reasoning. A dashed green training bracket spans retrieve through act, labeled trained end-to-end with reinforcement learning, reward flowing back through every stage. Below, an episode bank labeled summarize, deduplicate, prune by utility supplies experiences to the retrieve stage and receives finished episodes written back from act." />
  <img src="/blog/the-shapes-of-agent-memory/experience_dark.svg" class="hidden dark:block" alt="A pipeline of five stages: observe the current state, retrieve top-k experiences with source context, critique whether they apply here, reconstruct them into state-specific guidance, and act in the environment. A dashed reject path skips from critique to act, labeled fall back to self-reasoning. A dashed green training bracket spans retrieve through act, labeled trained end-to-end with reinforcement learning, reward flowing back through every stage. Below, an episode bank labeled summarize, deduplicate, prune by utility supplies experiences to the retrieve stage and receives finished episodes written back from act." />
  <figcaption>Figure 6. The experience architecture (<a href="https://github.com/KnowledgeXLab/MemHarness">MemHarness</a>). The episode bank is a structured store, summarized, deduplicated, and pruned by
  utility; the difference is that retrieval, critique, and reconstruction into state-specific guidance are stages of one policy trained end-to-end by
  reinforcement learning.</figcaption>
</figure>

Why go to that expense? Because the untrained alternative is not merely weaker, it is negative: in their own ablation, handing the trained policy raw
replayed episodes instead of reconstructions makes it _worse_ (76.4 with no memory to 70.1 with raw replay). Retrieval gets the experience into view;
nothing about a frozen model guarantees the experience gets _used_, and a policy that has learned when to trust a memory and how to rewrite it for the
situation at hand is solving a problem that no amount of store engineering touches. The cost profile inverts accordingly: the store architectures pay
at write or read time and bolt onto any model; the trained one pays in training compute and is inseparable from the one model it trained.

That is also why it cannot join the controlled comparison that follows: unplug its bank and you have a different trained policy, not a baseline. The
honest meeting point is its home ground, the agentic benchmarks, where the final section takes the structured store to meet it.

## Evaluation

Two public benchmarks carry the comparison: LongMemEval as the primary, LoCoMo as the second opinion. Each gets a subsection below, because what a
benchmark measures, and what its numbers have been made to say in the wild, decides how much a score is worth.

Every result table below compares the same three arms, named the same way throughout. Each table and figure states the sample it was scored over,
written out in the tables and abbreviated as **n** in the figures, meaning the number of questions, games, or sessions behind that number:

- **No-memory**: the same agent loop with the memory layer removed. The floor that sizes what memory contributes at all, and proof that the judge
  cannot be gamed by refusing everything.
- **File-based**: the markdown reconstruction described above. An LLM-curated index plus topic files, recalled by grep and read.
- **Structured**: the hybrid described above. Dated atomic facts, embedded on write with no LLM, recalled by ranked hybrid search.

The two pure structured lineages, place-organized and entity-and-time, do not run in the main experiment; they get their own store-only head-to-head
at the end of this section, where the graph vendor's production system competes through its own published retrieval.

The controls are the point. Both arms ran the same agent loop, the same locally served open-weight model as the answerer
([`Qwen3.6-35B-A3B-mxfp4`](https://huggingface.co/mlx-community/Qwen3.6-35B-A3B-mxfp4)), the same embedder where one was needed, and the same judging
pipeline: a model judge scores each answer against the gold one, and a deterministic pass then re-classifies refusals (saying "I don't know" counts as
correct only when the answer genuinely was not in the history). The judge is identical for both arms, so it cannot favor one over the other, but it is
one model family scoring its own outputs, which I flag rather than hide. The file-based arm is a faithful implementation of the documented approach
(Claude Code's auto-memory, described above), with a couple of deviations that make it slightly _more_ robust than the standard, not less. Anywhere
the two arms could differ for a reason other than the memory architecture, I held them equal.

One thing this is _not_: a measurement of any shipping product. I reimplemented the file-based _architecture_ and drove it with a local open-weight
model, so these numbers say nothing about how Claude Code, Cline, or anyone else performs in their own product, on their own model. Naming products is
about where the architecture comes from, not a leaderboard of them. What is being compared is the memory architecture, with everything else held
fixed.

That fixity is the whole reason to bother. Published memory numbers are notoriously hard to compare across vendors, and the LoCoMo subsection below
tells the canonical story. A number is only worth anything when you know what was held constant. Here, everything but the memory architecture was.

### LongMemEval

[LongMemEval](https://arxiv.org/abs/2410.10813) is a public suite for long-term conversational memory: 500 questions spanning categories that separate
the easy from the hard: single-session recall, multi-session joins, knowledge updates ("what is the _current_ value"), temporal reasoning, and
abstention (knowing when the answer was never stated). Retrieval and answering both count: the system has to surface the right memory _and_ answer
from it, and an LLM judge scores the answer against the gold one. It comes in two sizes: **LongMemEval-S**, where each question sits over a history of
roughly 47 prior sessions, and **LongMemEval-M**, the same questions over roughly 500-session haystacks. The main experiment runs -S; the -M numbers
close this subsection, because scale is exactly what they measure. It is the primary benchmark here because its haystacks are long enough to punish
weak recall and its categories name the exact failure modes the architectures should differ on.

Every headline number below is measured on the **held-out** questions, never the tuning split; both arms scored fractionally _higher_ on questions
they had never seen, which is the opposite of what overfitting looks like. How the 500 questions were split, what "tuning" concretely means, and every
limitation a skeptic should weigh (prompt heritage, reconstruction fidelity, self-judging, and an oracle control that splits the gap into read-path
and write-path halves) are collected in the [appendix](#appendix-methods-and-caveats). The one that matters most mid-read: the file-based arm got an
equal tuning budget, and two of its frozen fixes came from watching its own failures.

#### Accuracy

<figure id="table-1" class="table-figure">

| Category (held-out questions)     | Structured | File-based |
| --------------------------------- | ---------: | ---------: |
| Temporal-reasoning (91)           |      0.802 |      0.407 |
| Multi-session (97)                |      0.608 |      0.330 |
| Knowledge-update (36)             |      0.833 |      0.528 |
| Single-session-user (52)          |      0.923 |      0.673 |
| Single-session-assistant (44)     |      0.568 |      0.273 |
| Preference (18)                   |      0.611 |      0.333 |
| Abstention (18)                   |      0.778 |  **0.889** |
| **Overall (category-reweighted)** |  **0.736** |  **0.449** |

<figcaption>Table 1. Held-out accuracy by question type on LongMemEval-S, over the 356 non-tuning questions. The count beside each category is
how many questions it holds. Structured memory leads every category except abstention.</figcaption>
</figure>

<figure id="figure-7">
  <img src="/blog/the-shapes-of-agent-memory/accuracy_by_category_light.svg" class="dark:hidden" alt="A grouped bar chart of held-out LongMemEval-S accuracy by question type, structured memory in blue against file-based memory in orange. Structured leads in every category except abstention: temporal 80 versus 41 percent, multi-session 61 versus 33, knowledge-update 83 versus 53, single-session-user 92 versus 67, single-session-assistant 57 versus 27, preference 61 versus 33, and abstention 78 versus 89 where the file-based arm wins. Overall 73.6 versus 44.9 percent, against a no-memory floor of 9.8 percent." />
  <img src="/blog/the-shapes-of-agent-memory/accuracy_by_category_dark.svg" class="hidden dark:block" alt="A grouped bar chart of held-out LongMemEval-S accuracy by question type, structured memory in blue against file-based memory in orange. Structured leads in every category except abstention: temporal 80 versus 41 percent, multi-session 61 versus 33, knowledge-update 83 versus 53, single-session-user 92 versus 67, single-session-assistant 57 versus 27, preference 61 versus 33, and abstention 78 versus 89 where the file-based arm wins. Overall 73.6 versus 44.9 percent, against a no-memory floor of 9.8 percent." />
  <figcaption>Figure 7. Held-out accuracy on LongMemEval-S. Structured memory leads everywhere except abstention, and the gap is widest where memory has to do the most
  work: joining facts across sessions and reasoning about time.</figcaption>
</figure>

On the held-out questions ([Tab. 1](#table-1), [Fig. 7](#figure-7)), the structured arm (the hybrid) scored **73.6%** and file-based scored **44.9%**
(category-reweighted; raw 73.1% and 44.1%). The paired difference is **28.7 points**, 95% confidence interval **[22.1, 35.1]**, comfortably clear of
zero. Three checks say the result is solid rather than lucky: the number barely moved from the tuning set to the held-out set for either arm (both
actually ticked _up_, so neither is overfit); widening the held-out set from 256 to all 356 non-tuning questions changed the gap by 0.0002; and
throwing out every question where either arm's answer was truncated by the serving layer still leaves 74.1% against 50.2%. For scale, a no-memory
baseline answering the same questions with no memory at all scores **9.8%**, so both architectures are doing real work; the question is how much.

The category breakdown says _why_, and it is not subtle. The widest gap is **temporal reasoning** (80% against 41%), and **multi-session** (61%
against 33%) is close behind and clearest about the mechanism: its answers are assembled from facts mentioned in several different conversations. A
literal search over a deliberately small index is the wrong tool for that. If the joining fact sits in a topic file the model never thought to grep,
it is simply gone, and the model, to its credit, usually says it does not know rather than inventing an answer. Ranked retrieval over an unbounded
store does not have this failure mode: the fact was saved whether or not anyone predicted it would matter, and similarity, not a filename, brings it
back. **Knowledge updates** (83% against 53%) tell the same story from another angle.

There is exactly one category the file-based arm **wins**: **abstention** (88.9% against 77.8%), knowing that something was never said. That is not a
rounding artifact, and it replicates: on the second benchmark's adversarial questions, in the LoCoMo section below, the file-based arm beats the
structured one by an even wider margin, and a no-memory baseline that refuses everything beats them both. The mechanism is the same in both places and
it is worth stating plainly, because it cuts against the headline: **a store that remembers less over-answers less.** Ranked retrieval almost always
surfaces something plausible enough to tempt an answer, while a curation-limited store often has nothing to offer and the model correctly says so.
Eager retrieval needs an abstention discipline bolted on; sparse memory gets one for free.

#### Cost

Accuracy is half the story. The other half is what each answer costs, and here file-based memory pays twice: more tokens, for a worse answer.

<figure id="figure-8">
  <img src="/blog/the-shapes-of-agent-memory/token_cost_light.svg" class="dark:hidden" alt="A grouped bar chart of model-reasoning tokens. Per question: file-based 287k in orange versus structured 19k in blue. Per correct answer: file-based 665k versus structured 27k. The structured arm additionally spends about 108k embedder tokens per question, a different and far cheaper currency, shown in the legend rather than summed." />
  <img src="/blog/the-shapes-of-agent-memory/token_cost_dark.svg" class="hidden dark:block" alt="A grouped bar chart of model-reasoning tokens. Per question: file-based 287k in orange versus structured 19k in blue. Per correct answer: file-based 665k versus structured 27k. The structured arm additionally spends about 108k embedder tokens per question, a different and far cheaper currency, shown in the legend rather than summed." />
  <figcaption>Figure 8. Model-reasoning tokens per question, and per correct answer, on LongMemEval-S. The two architectures pay in different currencies, so they are
  never summed: the structured arm's write path spends embedder tokens, not reasoning tokens.</figcaption>
</figure>

Comparing cost honestly requires separating two currencies. Both arms spend **model-reasoning tokens** (a 35-billion-parameter model thinking), and
those are directly comparable. The structured arm _additionally_ spends **embedder tokens** (a 2-billion-parameter model producing vectors), which
cost orders of magnitude less per token and have no counterpart on the other side. Summing them into one number would be meaningless, so I never do.

<figure id="table-2" class="table-figure">

| Chat tokens per question                                    | File-based |   Structured |
| ----------------------------------------------------------- | ---------: | -----------: |
| Writing memory (LLM curation, amortized per question)       |     246.1k | 0 (verified) |
| Answering (recall plus reasoning)                           |      40.4k |        19.3k |
| **Total**                                                   | **286.5k** |    **19.3k** |
| Total per _correct_ answer                                  |       665k |          27k |
| Embedder tokens per question (estimated; separate currency) |          0 |       107.8k |
| Wall-clock per ~50-session ingest                           |    ~35 min |       ~5 min |

<figcaption>Table 2. The token ledger on LongMemEval-S, per question. Chat tokens and embedder tokens are different currencies and are never summed.</figcaption>
</figure>

In reasoning tokens ([Tab. 2](#table-2), [Fig. 8](#figure-8)), per question: file-based **287k** against structured **19k**. Divide by accuracy to get
the cost of a _correct_ answer, which is what you actually pay for, and it is **665k against 27k**. On top of its 19k, the structured arm spends about
**108k embedder tokens** per question on the write path. Even charging those at par with reasoning tokens, which wildly overstates them, it remains
the cheaper architecture. The reason is the write path ([Fig. 9](#figure-9)).

<figure id="figure-9">
  <img src="/blog/the-shapes-of-agent-memory/write_path_light.svg" class="dark:hidden" alt="Two horizontal timeline bars for ingesting one roughly 50-session history. File-based in orange is long, marked about 35 minutes and about 246k reasoning tokens, subdivided into one LLM curation call per session. Structured in blue is short, marked about 5 minutes, embeddings only. A note says the structured write path asks no model to reason and is roughly seven times faster." />
  <img src="/blog/the-shapes-of-agent-memory/write_path_dark.svg" class="hidden dark:block" alt="Two horizontal timeline bars for ingesting one roughly 50-session history. File-based in orange is long, marked about 35 minutes and about 246k reasoning tokens, subdivided into one LLM curation call per session. Structured in blue is short, marked about 5 minutes, embeddings only. A note says the structured write path asks no model to reason and is roughly seven times faster." />
  <figcaption>Figure 9. Ingesting one history. File-based memory reasons once per session to decide what to keep; structured memory just embeds. That is
  where the token bill and the wall-clock gap come from.</figcaption>
</figure>

Curating a file is a _reasoning_ act. For every session in a history, the model reads the current index, decides what is worth keeping, and rewrites a
line. Over a full ingest that came to roughly **246k reasoning tokens per history** and about **35 minutes** of wall-clock per history on my hardware.
Structured memory writes by embedding, no model in the loop, which finished the same history in about **5 minutes**, roughly a sevenfold speedup on
the write path. The two write costs are in different currencies (one is LLM reasoning tokens, the other is embedding-model tokens), so I never
subtract one from the other, but the direction is not close.

The read paths differ too, in a way that compounds. File-based recall is iterative: keep the index in view, grep, read a file, maybe grep again, then
answer. That longer, multi-round path also turned out to be more fragile. Under a busy serving layer the file-based arm hit truncation on 20 of 144
answers against the structured arm's 3, precisely because it asks the model to generate more, over more rounds, with more chances to be cut off. Some
of that is my serving setup, but part of it is intrinsic: a longer read path has more surface to fail on.

#### The long haystack: LongMemEval-M

The -M variant asks the same questions over roughly ten times the history. The two store-only rows in [Tab. 3](#table-3) ran on the same
pre-registered 100-question sample, one retrieval and one reader call each under the benchmark's official per-category judging, so their comparison is
paired even though neither is paired with the main experiment:

<figure id="table-3" class="table-figure">

| System (LongMemEval-M)                  |     Score | Questions scored                                |
| --------------------------------------- | --------: | ----------------------------------------------- |
| **Hybrid (store-only)**                 | **0.750** | 100 (pre-registered sample)                     |
| Place-organized (MemPalace, store-only) |     0.600 | The same 100                                    |
| Hybrid (full agent loop)                |     0.632 | 500 (complete set, different harness)           |
| Entity-and-time (Graphiti OSS)          |      None | None: ~12 GPU-days, or ~\$7,000, just to ingest |

<figcaption>Table 3. LongMemEval-M, the long-haystack variant. The two store-only rows are paired on one pre-registered sample; the agent-loop row
is a different harness and sample, directional only.</figcaption>
</figure>

Long histories are the regime structure exists for, and the paired rows put a number on the claim: fifteen points, rescuing 22 questions against
losing 7, exact p = 0.008 under the same paired test as the head-to-head below. The gap clears the sample's own confidence interval, and the shape of
the win matches the mechanism, with the hybrid sweeping the single-session categories (14/14 and 11/11) and pulling ahead on the multi-session and
temporal content that long haystacks exist to test. Two disclosures ride along. The flat store's number moved: an earlier run scored 0.530 on a sample
whose per-question rows were later lost, so both arms were re-drawn on a fresh pre-registered sample, and 0.600 is what it scores there. And the
hybrid's store-only 0.750 sitting above its own agent-loop 0.632 is not the paradox it looks like. Store-only hands the reader one ranked context and
asks for one answer; the agent loop has to decide when to search, what to search for, and how to read the results over multiple rounds, and every one
of those decisions is a place to fail. A bare store measures the retrieval; the loop measures the whole system operating it, and the same ordering
appears on LongMemEval-S, where store-only scores 0.80 against the loop's 0.72 on one sample under one rubric. A disclosed confound rides with both
gaps: the store-only rows answer under the shared competitor prompt while the loop uses its own, so part of each gap is prompt rather than loop
overhead, and the split between the two was not isolated. Read the sizes as directional. But hold onto the shape of it, because it is this post's
ending seen early: deciding when to search, what to ask, and whether to trust the answer is a competence in its own right, and the experience
architecture at the end of this post is what it looks like when that competence is trained into the model instead of billed to a scaffold. The empty
row is its own finding, and the reason it is empty is the finding: a graph store spends a reasoning call on every one of the haystack's 3.7 million
messages where an embedder spends milliseconds. Ingesting it on my own hardware measured out at roughly twelve days of continuous GPU time, and
renting a small hosted model to do the same work would have cost roughly \$7,000 at list prices. I was not willing to spend either on one row of one
table, so the row stays empty and the reason is published. That is not a knock on the lineage so much as a statement of what it costs to reach the
regime that matters: -M is where real assistants drift, and the paired rows above show it is where the benchmarks disagree, since the flat store that
ties the hybrid at short haystacks falls 15 points behind exactly here, where multi-session organization starts to pay.

### LoCoMo

A single benchmark is a single opinion, so the same three arms (no memory, file-based, structured) also ran on
[LoCoMo](https://arxiv.org/abs/2402.17753), the other widely used long-term-conversation suite: 10 very long two-speaker conversations, each spanning
dozens of sessions, with 1,986 questions across single-hop, multi-hop, temporal, open-domain, and adversarial (unanswerable) categories.

LoCoMo needs its story told before its numbers can be trusted, because it is the benchmark on which the field's most public scoring fight happened.
Zep reported 84% on it. mem0's CTO [filed an issue against their evaluation code](https://github.com/getzep/zep-papers/issues/5) arguing the real
number was 58.44: the adversarial category had been counted in the numerator but excluded from the denominator, and the baseline configurations
differed. Zep's [rebuttal](https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/) re-ran with the error fixed and
reported 75.14, while pointing back at mem0's own reporting (whose LoCoMo figure has been cited
[at both 67% and 92.5%](https://arxiv.org/abs/2504.19413) depending on the write-up). One system, one benchmark, three published numbers spanning 25
points, and the memory architecture never changed: the swing came entirely from scoring conventions, judge choice, and which categories count.

So why keep the benchmark? Because the dispute indicts the reporting, not the questions; because it is the suite the vendors actually compete on, so
results on it travel; and because the fight teaches exactly this study's premise, that a number means something only inside a fixed, published
protocol. The dispute constrains the protocol here in three ways. Every score is published under both scopes, with and without adversarial, because
whether to count that category is precisely the axis Zep and mem0 fought over. The analysis resamples whole conversations rather than questions,
because LoCoMo's questions cluster inside just 10 conversations and pretending otherwise makes intervals too tight. And I evaluate a disclosed,
seeded, category-stratified sample of roughly 30 questions per conversation. The rest of the benchmark's fine print (retrieval recall confused with
answer accuracy in the wild, saturation critiques) lives in the [appendix](#appendix-methods-and-caveats).

#### Accuracy

The run completed ([Tab. 4](#table-4), [Fig. 10](#figure-10)), and the result is the study's most honest one, because the verdict depends on the scope
in exactly the way the dispute predicts:

<figure id="table-4" class="table-figure">

| LoCoMo (300 questions, cluster CI) | No memory | File-based | Structured |
| ---------------------------------- | --------: | ---------: | ---------: |
| All questions                      |     0.217 |      0.387 |      0.497 |
| Excluding adversarial              |     0.017 |      0.356 |      0.561 |

<figcaption>Table 4. LoCoMo accuracy under both scopes. The verdict depends on whether the adversarial category counts, which is the axis the vendors dispute.</figcaption>
</figure>

<figure id="figure-10">
  <img src="/blog/the-shapes-of-agent-memory/locomo_accuracy_light.svg" class="dark:hidden" alt="A grouped bar chart of LoCoMo accuracy by question type, structured memory in blue against file-based memory in orange. Structured wins the memory categories: temporal 69 versus 31 percent, temporal-inference 52 versus 26, open-domain 66 versus 41. File-based wins single-hop 44 versus 37 and adversarial 51 versus 25. Overall 0.497 versus 0.387 on all questions, 0.561 versus 0.356 excluding adversarial; the no-memory floor of 0.217 is entirely adversarial refusals." />
  <img src="/blog/the-shapes-of-agent-memory/locomo_accuracy_dark.svg" class="hidden dark:block" alt="A grouped bar chart of LoCoMo accuracy by question type, structured memory in blue against file-based memory in orange. Structured wins the memory categories: temporal 69 versus 31 percent, temporal-inference 52 versus 26, open-domain 66 versus 41. File-based wins single-hop 44 versus 37 and adversarial 51 versus 25. Overall 0.497 versus 0.387 on all questions, 0.561 versus 0.356 excluding adversarial; the no-memory floor of 0.217 is entirely adversarial refusals." />
  <figcaption>Figure 10. LoCoMo accuracy by question type. The structured arm dominates every memory category; the file-based arm wins single-hop,
  where curated one-line facts suffice, and adversarial, where having less to retrieve means less temptation to answer.</figcaption>
</figure>

Excluding adversarial (the scope the benchmark's own convention arguably prescribes), the structured arm wins clearly: the paired difference is +0.205
with a cluster confidence interval of [+0.063, +0.356], and it dominates the memory categories (temporal 0.694 against 0.306, open-domain 0.656
against 0.410). Include adversarial and the verdict collapses to a statistical tie (+0.110, CI [-0.007, +0.240]), because the file-based arm abstains
better on unanswerable questions (0.508 against 0.246): its curation-limited store simply has less material to over-answer with, while ranked
retrieval almost always surfaces _something_ plausible enough to tempt an answer. Even the no-memory baseline "wins" adversarial outright (1.000) by
refusing everything, which is why a blanket-refusal system still only scores 0.217 overall. The lesson generalizes: eager retrieval needs an
abstention discipline, and a store that remembers less over-answers less. Both readings are published; neither is smoothed away. One disclosure: the
file-based arm's run predates a serving-layer retry fix, and 18 of its 300 answers died to output truncation and count as wrong under the symmetric
rule; its numbers are floors.

#### Cost

The cost asymmetry survives the second benchmark, at a smaller scale ([Tab. 5](#table-5), [Fig. 11](#figure-11)). LoCoMo's conversations are far
shorter than the primary benchmark's haystacks, so the file arm's curation bill shrinks, but the ordering does not change: 22k reasoning tokens per
question against the structured arm's 12k, and 58k against 23k per correct answer, with each conversation's ingest amortized over its sampled
questions. The structured write path again spends zero LLM tokens (verified against the serving ledger) plus about 0.8k embedder tokens per question
in its separate currency. The gap compressing from roughly fifteenfold to roughly twofold is itself the finding: write-time curation is priced by
history length, which is the primary benchmark's cost story wearing smaller numbers.

<figure id="table-5" class="table-figure">

| Chat tokens per question                         | File-based |   Structured |
| ------------------------------------------------ | ---------: | -----------: |
| Writing memory (amortized per question)          |       4.9k | 0 (verified) |
| Answering (recall plus reasoning)                |      17.6k |        11.6k |
| **Total**                                        |  **22.4k** |    **11.6k** |
| Total per _correct_ answer                       |        58k |          23k |
| Embedder tokens per question (separate currency) |          0 |         0.8k |

<figcaption>Table 5. The token ledger on LoCoMo, with each conversation's ingest amortized over its sampled questions.</figcaption>
</figure>

<figure id="figure-11">
  <img src="/blog/the-shapes-of-agent-memory/locomo_token_cost_light.svg" class="dark:hidden" alt="A grouped bar chart of model-reasoning tokens on LoCoMo. Per question: file-based 22k in orange versus structured 12k in blue. Per correct answer: file-based 58k versus structured 23k. Ingest is amortized per question; the structured arm spends about 0.8k embedder tokens per question in a different currency, noted in the legend rather than summed." />
  <img src="/blog/the-shapes-of-agent-memory/locomo_token_cost_dark.svg" class="hidden dark:block" alt="A grouped bar chart of model-reasoning tokens on LoCoMo. Per question: file-based 22k in orange versus structured 12k in blue. Per correct answer: file-based 58k versus structured 23k. Ingest is amortized per question; the structured arm spends about 0.8k embedder tokens per question in a different currency, noted in the legend rather than summed." />
  <figcaption>Figure 11. LoCoMo model-reasoning tokens per question and per correct answer, ingest amortized. Shorter histories shrink the file arm's
  curation bill; the ordering and the currencies stay the same.</figcaption>
</figure>

### The lineages, head-to-head

Everything above compares files against one structured design, and it leaves the lineage question open: inside the structured shape, does the graph
earn its ingest bill? The head-to-head answers it in the most controlled frame available: strip every system down to its retrieval and hold everything
else constant. Each store contributes exactly its top-20 results for the same 1,540 non-adversarial LoCoMo questions; one fixed reader (gpt-4o-mini)
answers from that context alone, one fixed judge scores it, and every store's row is produced by the same script. The entity-and-time lineage appears
twice: as [Zep's published retrieval contexts](https://github.com/getzep/zep-papers), their production system's real output (and a fairness note they
are owed: their published 75.14 reproduces from their own artifacts; 0.7461 is the same context re-scored under this unified frame), and as their
open-source engine [Graphiti](https://github.com/getzep/graphiti) run end-to-end on their paper's recipe, both embedders it names. These rows sit far
above the bare-loop table above because everything about the frame differs; they are comparable to each other and to nothing else. For orientation,
[Tab. 6](#table-6) puts the four methods side by side (pure place-organized differs from the hybrid only by dropping the temporal layer, so the hybrid
bounds it closely):

<figure id="table-6" class="table-figure">

| Method                     | Write path                          | Read path                                          | Time handling                      | Aggregation                   | Where measured           |
| -------------------------- | ----------------------------------- | -------------------------------------------------- | ---------------------------------- | ----------------------------- | ------------------------ |
| File-based                 | LLM curates markdown                | Index in context + grep/read                       | None built in                      | Index + luck                  | Main experiment          |
| Place-organized            | Embed and file, no LLM              | Layered loads + ranked search                      | Ranking heuristics                 | Ranked-query hope             | This head-to-head        |
| Entity-and-time (Graphiti) | LLM extracts, resolves, invalidates | Distilled facts + entity summaries                 | Validity windows in the store      | Entity nodes, by construction | This head-to-head        |
| Hybrid (place + time)      | Embed and file, no LLM              | Ranked search; associative expansion in the design | Dated facts; windows in the design | Ranked-query as measured      | Main experiment and here |

<figcaption>Table 6. The four methods side by side, and where each one is measured in this post.</figcaption>
</figure>

#### Accuracy

<figure id="table-7" class="table-figure">

| Store (one reader and one judge throughout)          | LoCoMo (1,540 questions) | LongMemEval-S (100 questions) |
| ---------------------------------------------------- | -----------------------: | ----------------------------: |
| Hybrid (this study's structured arm)                 |               **0.7825** |                      **0.80** |
| Place-organized (MemPalace, dense over raw turns)    |                   0.7792 |                          0.60 |
| Entity-and-time (Zep Cloud, published contexts)      |                   0.7461 |                          None |
| Entity-and-time (Graphiti OSS, two embedder configs) |          0.5338 / 0.5286 |                          0.35 |

<figcaption>Table 7. Store-only accuracy on both benchmarks. Within each column every store is read and judged by one fixed model: `gpt-4o-mini` on
LoCoMo, and the local 35B under LongMemEval's official per-category rubric. The columns are therefore comparable down, not across.</figcaption>
</figure>

<figure id="figure-12">
  <img src="/blog/the-shapes-of-agent-memory/h2h_accuracy_light.svg" class="dark:hidden" alt="Two bar panels under one reader and judge. Left, LoCoMo over 1,540 questions: hybrid 78.3, place-organized MemPalace 77.9, Zep Cloud 74.6, Graphiti OSS 53.4 and 52.9 with the bge-m3 embedder. Right, LongMemEval-S over a 100-question sample with the official rubric: hybrid 80, place-organized 60, Graphiti OSS 35. Blue bars are raw dated facts with ranked recall, green bars are LLM-distilled graphs; the ranking does not transfer across benchmarks." />
  <img src="/blog/the-shapes-of-agent-memory/h2h_accuracy_dark.svg" class="hidden dark:block" alt="Two bar panels under one reader and judge. Left, LoCoMo over 1,540 questions: hybrid 78.3, place-organized MemPalace 77.9, Zep Cloud 74.6, Graphiti OSS 53.4 and 52.9 with the bge-m3 embedder. Right, LongMemEval-S over a 100-question sample with the official rubric: hybrid 80, place-organized 60, Graphiti OSS 35. Blue bars are raw dated facts with ranked recall, green bars are LLM-distilled graphs; the ranking does not transfer across benchmarks." />
  <figcaption>Figure 12. Store accuracy under one reader and one judge. Raw dated facts beat LLM-distilled graphs on LoCoMo; the flat store that ties
  the hybrid there trails it by 20 points on LongMemEval-S. No single benchmark ranks memory systems.</figcaption>
</figure>

Four findings ([Tab. 7](#table-7), [Fig. 12](#figure-12)).

- **The hybrid beats the graph vendor's published retrieval**, and the difference is real under a paired test
  ([McNemar's test](https://en.wikipedia.org/wiki/McNemar%27s_test), which scores only the questions the two systems disagree on; p < 0.01). So,
  separately, does the plain dense store: raw turns beat distilled facts here before any hybrid machinery is added at all.
- **The hybrid ties the flat vector index** (χ² = 0.06), which is the uncomfortable finding and belongs in the open. Place-plus-time buys nothing over
  plain dense retrieval on this benchmark. It is also only half the story: the same two stores, paired on LongMemEval-M's long haystacks
  ([Tab. 3](#table-3)), separate by 15 points (0.750 against 0.600, p = 0.008). The structure is dead weight at LoCoMo's scale and decisive at -M's,
  which is the benchmark-disagreement point again, made by one pair of systems.
- **Distillation loses to raw text.** Both graph rows hand the reader LLM-distilled facts and entity summaries; both trail every raw-turn store, and
  the strongest graph row loses 3.3 points to the flat index while spending six times its context. The pre-built entity aggregates that make the
  lineage attractive for enumeration questions do not surface as a net win anywhere in this table; whatever they recover, the distillation loses more
  elsewhere. This is the single-session regression Zep itself discloses, visible benchmark-wide once the reader is held constant.
- **An LLM-at-ingest design is bounded by its extractor, and the extractor bill is real.** Graphiti OSS with the vendor's own models lands around
  0.53, so much of its 21-point gap to the vendor's cloud contexts sits outside the extraction model's capability. Driven instead by this study's
  local 35-billion-parameter model, the same engine collapses to 0.29, and the mechanism is visible at ingest: it extracts several times fewer facts
  per message than the cloud output implies. A store that only knows what its extractor wrote down starves quietly.

The LongMemEval-S column of [Tab. 7](#table-7) is the same three stores under the benchmark's official per-category rubric on a pre-registered
100-question sample (the hybrid's 0.80 there is a single retrieval and a single read under a shared reader prompt, which is why it sits above the same
system's agent-loop 0.72 on this sample; [Tab. 3](#table-3)'s discussion unpacks that ordering). Read the two columns across and the point makes
itself: the flat store that ties the hybrid on LoCoMo trails it by 20 points on LongMemEval, because LoCoMo mostly rewards verbatim lookup inside a
few dozen sessions while LongMemEval forces multi-session organization. The two benchmarks disagree about the same pair of systems, in opposite
directions. No single benchmark ranks memory systems.

The same frame also measures the thing this post keeps insisting on, and it is worth putting a number on rather than gesturing at. Re-reading
byte-identical retrieval with a different reader moved the hybrid's LoCoMo score by 6.9 points (0.7130 under the local 35B, 0.7825 under gpt-4o-mini),
and re-judging identical answers under different judge prompts moved category-level accuracy by 5 to 15 points. Set that against the architecture
([Tab. 8](#table-8)): the hybrid and the flat index differ by 0.3 points, and both sit 3.3 to 3.6 from the hosted graph. **On this benchmark, changing
who reads the memory matters more than changing which of those three stores you built.** Only Graphiti OSS sits further away than the reader does, and
by a lot: even the cheapest route to it, Zep Cloud to Graphiti OSS, costs 21.2 points, three times the reader's swing. The scope matters, because the
claim inverts with the haystack: on LongMemEval-M the same hybrid-versus-flat pair that differs by 0.3 here differs by 15 ([Tab. 3](#table-3)), better
than twice the reader's swing. The reader dominates where the stores tie; the architecture dominates where the benchmark actually stresses it.

That last gap needs care, because three different things sit behind that number and conflating them makes it unreadable:

- **The reader** sits at the end and answers from whatever context it is handed. It is identical for every store, which is what makes the store
  comparison valid at all, and swapping it is the 6.9-point row.
- **The extractor** sits at the start, inside the store, and decides what ever gets written down. It is part of the store being compared, not part of
  the harness around it.
- **The pipeline** is what the extractor runs in: how many passes it makes over each message, what it resolves, what it keeps.

So which of the three explains the 21 points between the last two rows of [Tab. 7](#table-7), the hosted Zep Cloud at 0.7461 and the self-hosted
Graphiti OSS at 0.5338? Not the reader: it is the same model for both. Not the extraction model's capability either, because the open engine ran with
the same class of extractor the vendor's published numbers were built with and still landed where it did. What is left is everything the hosted
service does around that extractor, and this is the point where the comparison reaches the edge of what it can honestly claim.

Zep Cloud is a hosted product, and its row here is Zep's own published context. I can measure what reaches the reader on each side, not the ingestion
or ranking that produced it. The open engine's contexts are visibly thinner, carrying fewer stored facts and much shorter entity summaries, but that
is a property of the released artifacts rather than a description of anyone's internals. One known difference does not favour them: their published
ingestion reads a `blip_captions` key where the LoCoMo field is `blip_caption` ([zep-papers#9](https://github.com/getzep/zep-papers/issues/9)),
dropping image captions that my runs kept.

None of this suggests their published number is wrong. It reproduces from their own released grades, and their contexts re-scored under this study's
reader and judge give the 0.7461 in [Tab. 7](#table-7), within a point of their published 75.14. The 21-point gap is real and reproducible; its cause
is not observable from outside. Read "the hosted pipeline" as a label for the part I could not see, not a mechanism I verified. A store can only
answer from what its extractor wrote down, however good the reader in front of it, and that is why importing a number from someone else's protocol
tells you nothing.

<figure id="table-8" class="table-figure">

| What changed                                         | From                     | To                                 | Points lost |
| ---------------------------------------------------- | ------------------------ | ---------------------------------- | ----------: |
| **The reader**, retrieval byte-identical             | **`gpt-4o-mini` 0.7825** | **`Qwen3.6-35B-A3B-mxfp4` 0.7130** |     **6.9** |
| The store, reader unchanged                          | Hybrid 0.7825            | Place-organized 0.7792             |         0.3 |
| The store, reader unchanged                          | Hybrid 0.7825            | Zep Cloud 0.7461                   |         3.6 |
| The store, reader unchanged                          | Place-organized 0.7792   | Zep Cloud 0.7461                   |         3.3 |
| The embedder inside one store                        | Graphiti OSS 0.5338      | Graphiti bge-m3 0.5286             |         0.5 |
| The store, the _cheapest_ route into the open engine | Zep Cloud 0.7461         | Graphiti OSS 0.5338                |        21.2 |

<figcaption>Table 8. What each single change costs on LoCoMo, everything else held fixed. Here swapping the reader moves the score further than
swapping between any two of the three stores that work; on the long-haystack benchmark that ordering inverts ([Tab. 3](#table-3)). The last row is the cheapest of the six routes into the starved open engine, and even that costs three times what
the reader does; the dearest of the six, hybrid to the bge-m3 variant, costs 25.4. Zep Cloud and Graphiti OSS come from one vendor and are read by the
same model here, so what separates them sits inside the stores rather than in the reader in front of them.</figcaption>
</figure>

#### Cost

The graph lineage pays twice ([Tab. 9](#table-9), [Fig. 13](#figure-13)). At read time, distillation was supposed to buy density, but the graph rows
hand the reader six times the context of the raw-turn stores (21.5k chars median against 4.0k and 3.5k) and scores lower with it. Graphiti OSS is
leaner at 7.9k and scores lower still, so density alone is not what the hosted pipeline is buying. At write time, the raw-turn stores embed while the
graphs run an LLM over every message, and that difference compounds brutally with history length. Each message costs the graph a reasoning call, or
several: extract the entities and facts, resolve them against the entities already in the store, then check whether the new fact invalidates an old
one. Measured on this hardware that ran about 14 seconds per message, against a few milliseconds to embed one. LongMemEval-M's haystacks hold roughly
3.7 million messages, so the arithmetic lands at about twelve days of continuous GPU time to ingest one run, against hours for the embedding-only
stores, which is why the graph lineage has no long-haystack row at all.

Twelve days is a fact about my hardware, not about physics, and it is worth saying so plainly because the hosted vendors clearly do not wait twelve
days: the work parallelizes almost perfectly, so a hundred concurrent workers turn it into an afternoon. What does not parallelize away is the unit
economics. Every message costs the graph several LLM calls where the raw-turn stores cost one embedding, and at list prices for a small hosted model
that is roughly two orders of magnitude more per message: about \$14 of ingest for a single long user history, against about \$0.03. Graph memory is
affordable; it is just priced like a product decision rather than an implementation detail, and the bill scales with everything your users ever said.
Context sizes are medians over the same 1,540 questions; the ingest comparison is wall-clock on identical hardware.

<figure id="table-9" class="table-figure">

| Store                          | Median context / question | Ingest                                                         |
| ------------------------------ | ------------------------: | -------------------------------------------------------------- |
| Hybrid                         |                4.0k chars | Embedder only: ~\$0.03 per long user history                   |
| Place-organized (MemPalace)    |                3.5k chars | Embedder only: ~\$0.03 per long user history                   |
| Entity-and-time (Zep Cloud)    |               21.5k chars | LLM per message: ~\$14 per long user history                   |
| Entity-and-time (Graphiti OSS) |                7.9k chars | LLM per message: ~12 days of GPU time, or ~\$7,000, per -M run |

<figcaption>Table 9. What a retrieval costs in the head-to-head: context handed to the reader per question, and what ingest spends to build the
store. Ingest prices are list-price estimates for a small hosted model.</figcaption>
</figure>

<figure id="figure-13">
  <img src="/blog/the-shapes-of-agent-memory/h2h_context_cost_light.svg" class="dark:hidden" alt="A bar chart of median retrieved context per question in characters: hybrid 4.0k, place-organized MemPalace 3.5k, Zep Cloud 21.5k, Graphiti OSS 7.9k. A note adds that the raw-turn stores embed at ingest while the graphs run an LLM per message, measured at roughly twelve days of GPU time per run at LongMemEval-M scale against hours for the embedding-only stores." />
  <img src="/blog/the-shapes-of-agent-memory/h2h_context_cost_dark.svg" class="hidden dark:block" alt="A bar chart of median retrieved context per question in characters: hybrid 4.0k, place-organized MemPalace 3.5k, Zep Cloud 21.5k, Graphiti OSS 7.9k. A note adds that the raw-turn stores embed at ingest while the graphs run an LLM per message, measured at roughly twelve days of GPU time per run at LongMemEval-M scale against hours for the embedding-only stores." />
  <figcaption>Figure 13. Retrieval context per question in the head-to-head. The hosted graph spends six times the context of the raw-turn stores and
  still scores lower; their shared other bill, an LLM over every message at ingest, is what priced the lineage out of the long-haystack benchmark.</figcaption>
</figure>

## What file-based memory is actually good at

A fair comparison has to state the other side, because file-based memory is popular for real reasons, and none of them are refuted by the numbers
above.

- **It is human-readable and human-editable.** Your memory is a folder of markdown files. You can open it, read it, fix a wrong fact, delete a stale
  one, or commit it to git. A vector store is opaque by comparison. For a tool you operate yourself, this is worth a great deal.
- **It has zero infrastructure.** No embedder, no vector index, no background workers, no graph. If your agent already has file tools, memory is free
  to add. Structured memory is a small distributed system you have to run.
- **Its writes are distillation.** Because the model decides what to keep, each memory is a considered lesson, not a raw fragment. At small scale that
  curation produces a genuinely tidy, high-signal store, which is exactly the regime a personal coding assistant lives in.
- **Its reads are cheap when the store is small.** Everything above is the large-history regime the benchmark stresses. When the whole memory fits in
  the index, the read path is just the index in context, and the grep never fires. A few hundred lines of curated notes covers a lot of everyday use.

Read the accuracy numbers with that scope in mind. The benchmark deliberately lives in the hard regime: dozens of sessions, facts scattered across
them, questions that force a join. That is the regime where curation forgets and a small index cannot hold enough, and it is the regime a memory
_product_ has to survive. It is not the regime a single-project assistant with fifty lines of notes lives in, and there it is not just adequate, it is
the better engineering trade. The regime-dependence cuts both ways, and it is worth being honest about: on easier, factual-recall benchmarks the gap
narrows sharply. Letta, a memory startup, [reported 74% on LoCoMo](https://www.letta.com/blog/benchmarking-ai-agent-memory/) using nothing fancier
than plain files, and argued a filesystem may be most of what you need. The structured store earns its keep specifically where the questions force
joins across many sessions, which is the part of the problem I find most interesting and the part a memory product cannot dodge.

## Remembering what worked: the agentic benchmarks

Everything above measures one kind of remembering: what was said. An agent accumulates the other kind too, what _worked_: the know-how of past
attempts. The natural question is whether this post's architectures carry over, so the same structured store was put to work on the agentic benchmarks
the memory-training literature uses: [ALFWorld](https://alfworld.github.io/) (household tasks in a text world: find the mug, heat it, put it away) and
[WebShop](https://webshop-pnlp.github.io/) (find and buy the right product in a catalog, scored with partial credit). Memory here is an **experience
bank**: training-split episodes distilled into atomic entries (a task pattern, the moves that worked), embedded, and retrieved top-k into the acting
model's prompt. Nothing is trained; it is the same architecture as the conversational study, wearing different content.

The bar in this realm is MemHarness, the experience architecture described earlier: the 7-billion-parameter policy whose retrieval, critique, and
reconstruction were trained by reinforcement learning. Being trained rather than bolted on turns out to be the whole story. Two untrained actors ran
with and without the experience bank, everything else frozen, and each benchmark gets its own subsection below, mirroring the evaluation section. Two
reading notes apply to every table: MemHarness's out-of-distribution (OOD) number is the comparable one, since the untrained rows run unseen splits;
and "no memory" removes only the experience bank, the harness's task scaffolding (playbooks, target hints, loop guards) stays in every untrained row,
so the ablation isolates retrieved memory. There is no cost subsection here, deliberately: the three pay in currencies that do not share an axis
(self-hosted GPU time, API dollars, training compute), and charting the two we measured would imply a comparison the third cannot join.

### ALFWorld

[ALFWorld](https://alfworld.github.io/) is a text world of household tasks: find the mug, heat it, put it away. Six task categories, binary success
per game, scored as macro SR (success rate averaged over categories, so no category dominates). The evaluation runs the 134 unseen games.

#### Accuracy

<figure id="table-10" class="table-figure">

| Actor                                         |          Macro SR |
| --------------------------------------------- | ----------------: |
| Local 35B, no memory                          |             0.603 |
| Local 35B + experience bank                   |             0.645 |
| Frontier actor (`claude-sonnet-5`), no memory |             0.959 |
| Frontier actor + experience bank              |             0.973 |
| MemHarness (GRPO-trained 7B)                  | 0.852 / 0.859 OOD |

<figcaption>Table 10. ALFWorld macro success rate by actor, over 134 unseen games.</figcaption>
</figure>

<figure id="figure-14">
  <img src="/blog/the-shapes-of-agent-memory/alfworld_success_light.svg" class="dark:hidden" alt="A bar chart of ALFWorld macro success rate over 134 unseen games. The 35B scores 60.3 percent without memory and 64.5 percent with the experience bank. The frontier actor scores 95.9 without memory and 97.3 with the bank. MemHarness's out-of-distribution row is 85.9. Gray bars are no-memory with scaffolds kept, blue bars add the experience bank, green is the trained policy." />
  <img src="/blog/the-shapes-of-agent-memory/alfworld_success_dark.svg" class="hidden dark:block" alt="A bar chart of ALFWorld macro success rate over 134 unseen games. The 35B scores 60.3 percent without memory and 64.5 percent with the experience bank. The frontier actor scores 95.9 without memory and 97.3 with the bank. MemHarness's out-of-distribution row is 85.9. Gray bars are no-memory with scaffolds kept, blue bars add the experience bank, green is the trained policy." />
  <figcaption>Figure 14. ALFWorld success rate by actor. The weak actor gains 4.2 points from retrieved experience, though not significantly; at
  frontier quality the benchmark saturates and memory rescued exactly two games.</figcaption>
</figure>

The ablation runs at both actor tiers, and the deltas line up as the actor-headroom law predicts: the weak actor gains 4.2 points from the experience
bank, the frontier actor 1.4. Only the direction is claimable, though. The weak actor's gain rescued 16 games and cost 10, which an exact paired test
puts at p = 0.164, inconclusive under the pre-registered threshold, so ALFWorld corroborates the law without carrying it; the significant weak-actor
evidence is WebShop's alone. One detail inside that null is worth keeping: five of six categories move positive with memory, while the category the
35B fails by looping is unmoved to three decimals. Retrieved experience does not repair a policy-level failure mode.

At frontier quality the benchmark saturates instead ([Tab. 10](#table-10), [Fig. 14](#figure-14)): the tasks yield entirely to strong reasoning
(ten-step solves, four of six categories perfect), memory rescued exactly 2 games and hurt none (p = 0.5), and the untrained frontier baseline exceeds
MemHarness's number. That last fact is not claimed as a beat: it is actor class plus harness scaffolding, not a method comparison. The right reading
is that ALFWorld's bar is procedural competence, find the object, use the appliance, with a ceiling any sufficiently strong actor reaches, and there
are two routes to that ceiling: MemHarness trained the competence into a 7B; this study rented it from a frontier model. Memory is rounding error on
both routes (ours +1.4 points at p = 0.5, theirs +2.2, and their own ablation shows raw replay _hurts_ their trained policy), so lining the results up
gives an ordering that is actor class all the way down: frontier, then trained 7B, then scaffolded 35B, then a frontier model on their plain
scaffold-free harness (their strongest closed-model row, 62.1). Memory has no headroom left to buy here, the agentic twin of the head-to-head's
"hybrid ties a flat index" finding: the actor dominates, memory works the margin.

### WebShop

[WebShop](https://webshop-pnlp.github.io/) is product search against a 1,000-item catalog with a purchase at the end: 500 test sessions, a 15-step
budget. Two metrics bracket it: **score** grants partial credit for a near-miss purchase, and **SR** counts only perfect ones. The small catalog often
contains no exact match for the instruction, which caps attainable reward for every actor.

#### Accuracy

<figure id="table-11" class="table-figure">

| Actor                                         | Score |    SR |
| --------------------------------------------- | ----: | ----: |
| Local 35B, no memory                          |  63.5 | 0.376 |
| Local 35B + experience bank                   |  66.0 | 0.418 |
| Frontier actor (`claude-sonnet-5`), no memory |  65.1 | 0.444 |
| Frontier actor + experience bank              |  65.2 | 0.450 |
| MemHarness (GRPO-trained 7B)                  |  87.4 | 0.756 |

<figcaption>Table 11. WebShop score and strict success rate by actor, over 500 test sessions.</figcaption>
</figure>

<figure id="figure-15">
  <img src="/blog/the-shapes-of-agent-memory/webshop_success_light.svg" class="dark:hidden" alt="A bar chart of WebShop strict success rate over 500 sessions. The 35B scores 37.6 without memory and 41.8 with the experience bank, the agentic benchmarks' only significant memory-ablation effect. The frontier actor scores 44.4 and 45.0. MemHarness's trained policy stands alone at 75.6. Gray bars are no-memory with scaffolds kept, blue bars add the experience bank, green is the trained policy." />
  <img src="/blog/the-shapes-of-agent-memory/webshop_success_dark.svg" class="hidden dark:block" alt="A bar chart of WebShop strict success rate over 500 sessions. The 35B scores 37.6 without memory and 41.8 with the experience bank, the agentic benchmarks' only significant memory-ablation effect. The frontier actor scores 44.4 and 45.0. MemHarness's trained policy stands alone at 75.6. Gray bars are no-memory with scaffolds kept, blue bars add the experience bank, green is the trained policy." />
  <figcaption>Figure 15. WebShop success rate by actor. The weak actor gains 4.2 points from retrieved experience, the frontier actor gains noise,
  and only the trained policy reaches the bar.</figcaption>
</figure>

WebShop delivers the agentic benchmarks' only significant memory-ablation effect, and their clearest boundary ([Tab. 11](#table-11),
[Fig. 15](#figure-15)). The weak actor gains 4.2 points of success rate from the bank (paired McNemar, p = 0.022), exactly where theory puts it: far
from its ceiling, in a domain where episode know-how (query phrasing, option discipline, the scoring rules) transfers between tasks. The frontier
actor gains +0.1 (p = 0.8); the catalog ceiling binds it to nearly the same total as the 35B. Note what that ceiling does to actor class: the same
actor swap that buys 31 points of success rate on ALFWorld buys +1.6 score here, because WebShop's reward is shaped by the catalog and its
partial-credit mechanics, not by actor smarts. The deeper difference between the two benchmarks is what each one hides. ALFWorld states its goal in
the observation, so success yields to reasoning and a capable enough actor needs nothing else, which is exactly what its frontier row shows. WebShop
grades with a rubric the agent never sees, weighing attributes, options, and price into partial credit over a catalog that often has no exact match,
and no amount of reasoning over the observation reveals how that grader will score a near-miss. Only the reward signal teaches it, and retrieval never
sees the reward: a bank stores what the agent did, not what the grader thought of it. That is why only training reaches the bar: every training-free
arm lands at a score of 63 to 66 against MemHarness's 87.4, and their number comes from reinforcement learning against the environment's own reward,
which teaches the policy the reward's _mechanics_, when to settle for a partial match, when to stop browsing, what an option is worth. Neither
prompting nor a stronger actor replicates that, and no store, of any design, closes the gap from the outside.

That claim can also be tested from the inside, and the inside test is the cleanest one in this post: hold MemHarness's own frozen 7B actor fixed on
WebShop (full catalog, 500 sessions) and swap what its memory holds. Its own released 7,859-episode bank, injected through its own wire format and
retrieval semantics, scores 69.5 with a 0.306 success rate against the no-memory 71.0 and 0.300 (p = 0.69). The same bank under a different retrieval
semantics, situation-match instead of memory-text match, scores 69.1 and 0.298. A three-way statistical tie, every delta under two points: at a frozen
actor, not even the trained system's own bank helps it, under either way of reading it. Whatever their published 0.756 success rate is made of, it is
not the bank's content and not the retrieval mechanics, because both are present here and buy nothing; it is the reconstruction _training_. Their own
ablation says the same thing from above, since raw replay _hurts_ their trained policy, the same null as our frontier arms.

Lay the results beside each other and one law explains the realm: **memory's value is inversely proportional to the actor's headroom.** A weak actor
far from ceiling gains real points from retrieved experience; a frontier actor saturates the task and gains nothing; a policy trained for the task is
actively hurt by raw replay. This is the consolidation null from earlier in the post seen from the other side: there a capable reader absorbed the
store's disorder and left tidying nothing to buy, here a capable actor absorbs the task and leaves memory nothing to buy. Training buys its bar at the
price of narrowness, too: served frozen outside its own harness, the released MemHarness model is acutely sensitive to exact prompt format, the
specialization reinforcement learning produces, where a frontier actor's robustness is precisely the thing you rent. That places every
retrieval-shaped system in this post, files, stores, temporal graphs, and hybrids alike, on one side of a line: bolt-on memory, model-agnostic, paid
for at write and read time, its value floating on the gap between the actor and the task. MemHarness sits on the other side: memory as trained
behavior, paid for in training compute, inseparable from its actor. The conversational benchmarks reward the first kind everywhere; the agentic
benchmarks reward it only while the actor is weak; past that line the question stops being "which store" and becomes "whose weights".

One more disclosure belongs with the bar itself, because it cuts against the comparison. MemHarness's numbers above are quoted from its paper. Running
their _released_ model on my own serving stack, under a faithful port of their harness and prompts, does not reach them: 0.581 macro on ALFWorld
against their 0.830 without memory, and 71.0 score with a 0.300 success rate on WebShop against their 87.4 and 0.756. The shortfall has the same
signature on both benchmarks: the approach reproduces and the precision does not, exact option matches on WebShop and multi-step thermal sequences on
ALFWorld, which points at serving numerics and 8-bit quantization of a sharply peaked policy rather than at anything about memory. I report it because
it makes the comparison's frame explicit. Their published bar stands as published; my arms are measured on my stack; and the distance between those
two statements is the same cross-stack caution this post applies to every other number it does not own.

Provenance, disclosed: WebShop's official dataset is org-locked, so the runs used the community mirror of the same files (1,000-product setting); all
frozen arms are single runs, and the memory ablations are paired per-episode. The frontier arms cost about \$22 of API spend on ALFWorld and \$34 on
WebShop, the latter including two voided protocol iterations.

## Takeaways

- **The store architectures are bets about where memory's cost sits, and each is right somewhere.** File-based memory bets on the model's judgment and
  a filesystem, pays in reasoning tokens at write time and literal search at read time, and buys transparency and simplicity: the right bet when
  memory is small, human-owned, and secondary to the task. Structured memory bets on an embedder and a ranker, pays in infrastructure, and buys recall
  that does not degrade as history grows.
- **When memory is the task, structure wins on both axes at once.** Under a fixed model on a hard benchmark, the structured store beat files by **28.7
  points on held-out questions** (95% CI [22.1, 35.1]) at a fraction of the reasoning tokens per correct answer.
- **Sparse memory abstains for free.** File-based memory wins the questions whose right answer is "I don't know", on both benchmarks: remembering less
  means over-answering less. Build the structured kind and you must budget for an abstention discipline.
- **Raw dated facts beat LLM-distilled graphs, and cost less twice over.** Inside the structured family, a good ranker over raw facts beat the graph
  lineage on the benchmark the graph is sold on, while the hosted graph spent six times the reader context to score lower. Structure only shows its
  value once histories outgrow one ranked query.
- **Reasoning at ingest is a product decision, not an implementation detail.** A graph store spends several model calls on every message a user ever
  sends, where a raw-turn store spends one embedding: roughly two orders of magnitude more, about \$14 to ingest one long history against about
  \$0.03. It parallelizes, so it is a bill rather than a wall, but the bill scales with everything your users ever said. It is also why this study has
  no graph row on the long-haystack benchmark: that one row would have cost about twelve days of GPU time, or about \$7,000 of hosted inference, to
  fill.
- **Consolidation is the third path, and it pays late.** Both store architectures can run a background pass that reorganizes what is already stored,
  promoting what gets used or merging what repeats. It is built here and it measured as a null, because a capable reader deduplicates a handful of
  restatements in context for free. Tidying storage earns its keep only once the mess outgrows what the reader can hold.
- **The ruler can outweigh the architecture, and which one dominates depends on the benchmark.** Swapping the reader moved a score by 6.9 points on
  byte-identical retrieval, more than the gaps between the three stores that work where they tie (0.3 to 3.6 points); on the long haystack the same
  store pair separates by 15. No single benchmark ranks these systems, and no number means anything without its protocol attached.
- **Retrieved memory earns in proportion to the actor's headroom.** The agentic benchmarks draw the boundary around the whole design space: real
  points under a weak actor, noise under a frontier one, harm under a policy trained for the task. Where the task yields to reasoning, a frontier
  actor reaches the trained bar with no memory at all; where the reward has a structure only practice teaches, training stands alone, and it buys that
  bar at the price of narrowness. Below that line the architectures in this post are the game; at the line, the game becomes training.

Both headline numbers came from the same model answering the same questions. The only thing that changed was the shape of what it remembered with.

## Appendix: methods and caveats

_The story is complete without this section. What follows is the fine print: how the questions were split, every limitation I know about, and the
caveats each number carries. Nothing here overturns a result, but it tells you how far each one can be trusted._

### How the questions were split, and what "tuning" means

The 500 LongMemEval questions were split once, before any runs: a seeded, stratified 144-question tuning set, a 256-question holdout, and 100 left in
reserve. Tuning-set numbers are provisional and never the headline; the holdout is scored exactly once per configuration. "Tuning" means prompts and
configuration only, the model's weights never move: the shared answering discipline (a six-round tool budget, an output cap, a truncation-rescue step,
a facts-then-dates-then-verify format), the structured arm's retrieval depth (top-12) and question-blind recency preload, and the file arm's index
budget (200 lines or 25 KB) and recall tools. The file-based arm got an equal tuning budget, and two of its frozen settings came from watching its own
failures: the same truncation rescue the other arm has, and a guard against index-wiping writes. The holdout then judged both arms with everything
frozen.

### Limitations

- **The shared answering prompt has a heritage.** Its discipline was developed in earlier work whose read path resembled the structured arm's. Equal
  tuning budget in this study is not equal ancestry; a file-native prompt built from scratch might serve that arm better, and I did not build one.
- **The file-based arm is a reconstruction, deliberately.** Its curation instructions are a faithful-as-documented rewrite of an unpublished original,
  every mechanism decision traced to a cited public source in the released spec. I chose not to validate against the shipping CLI: a closed-product
  run is a snapshot of whichever model version shipped that week, unreproducible by design. The fidelity burden is met by the traceable spec, the
  oracle control below, and a published envelope check (save rates, index shapes, read patterns) that anyone with the real tool can run to falsify the
  reconstruction.
- **One model family judges itself, and an independent judge has now audited part of it.** In the main experiment the judge is identical across arms
  and finished with a deterministic refusal pass, but it shares a model family with the arms it scores. For the store head-to-head, that concern has
  been tested: a frontier judge from a different vendor re-scored every arm's published responses on a frozen 100-row sample. It grades uniformly
  stricter (4 to 7 points on every arm, agreement 0.91 to 0.96, Cohen's kappa 0.82 to 0.89, no arm-differential bias), and every ranking survives,
  with the hybrid's win over the graph vendor significant on a tenth of the data (p = 0.024). The main experiment's own judge remains unaudited.
- **The holdout was widened once, and the verdict stayed on the blind set.** Mid-study I extended the held-out set from 256 to all 356 non-tuning
  questions; the added questions had never been run or tuned on, but one arm's solo holdout score had been seen, which is partial peeking. An
  independent review called it, so the verdict was locked on the blind 256. The tables in this post report all 356, because that is the set whose
  per-question rows are published, and widening changed the gap by 0.0002, so the two agree to the fourth decimal. The commit history proves the
  ordering.
- **Truncation hit the arms unequally** (20 of 144 file-based answers against 3, under a busy serving layer). The frozen rule counts both as wrong
  symmetrically, and the gap survives excluding every truncated row.
- **Absolute numbers are floors.** Both arms run a deliberately minimal shared loop because mechanism isolation is the point; the same structured
  mechanism inside a full production agent reaches the mid-0.80s on this benchmark's held-out questions.
- **The oracle control splits the gap into mechanism and harness.** Answering with the file arm's _entire_ memory directory in context and no tools
  scores 57.1% held-out, between the file arm's 44.9% and the structured arm's 73.6%: 12.2 points of the gap is read-path friction (saved but not
  found) and 16.5 points is write-path loss (never written down). On preference questions the oracle beats the structured arm (72.2% against 61.1%), a
  pure search miss; on abstention it scores exactly what the file arm scores, so over-answering comes from eager retrieval, not context volume.
- **Wall-clock is indicative, not controlled**; token counts are the load-independent cost metric.
- **Reproducibility has a scope.** The baseline, file arm, judge, and analysis run against any OpenAI-compatible endpoint; the structured arm calls a
  memory service, and its raw per-question rows are published for inspection either way in [a40-labs/memory](https://github.com/a40-labs/memory). The
  protocol, including every amendment and its timing, was pre-registered in the repository before the scored runs.

### Reading LoCoMo

**Retrieval recall is not answer accuracy**, and LoCoMo numbers in the wild mix the two: a store can be scored on whether the right item merely
surfaces in its top-k, or the whole system on whether it answers correctly end-to-end. The gap is structural; this study's store surfaces the right
session about 95% of the time on LongMemEval while its end-to-end accuracy sits at 0.73, the answering step consuming the rest.
[MemPalace](https://github.com/mempalace/mempalace) publishes _only_ retrieval recall on LoCoMo, with an explicit no-QA disclaimer, while the QA
numbers people quote (Zep's disputed 84 / 75.14 / 58.44, mem0's ~67) are LLM-judged answer accuracy from entirely different systems; putting one next
to the other is comparing different sports. Beyond that, the benchmark is contested ground with no agreed state of the art and no clean third-party
reproduction of the leaders, and the research community has argued it is close to saturated. Its questions cluster inside 10 conversations, so honest
confidence intervals must resample conversations, not questions. And its adversarial category inverts the incentive, rewarding refusal and punishing
exactly the eager retrieval that helps everywhere else, which is why every LoCoMo score in this study is published under both scopes. One disclosure:
the file-based arm's LoCoMo run predates a serving-layer retry fix, and 18 of its 300 answers died to output truncation and count as wrong; its
numbers are floors.

### Head-to-head boundaries

Every head-to-head row is a single run, and identical reruns at temperature 0 drifted by 0.3 to 0.4 points, so the last decimal is noise. Graphiti-OSS
is a best-effort parity configuration of the vendor's open-source engine, not their hosted product. The hybrid's retrieval was verified against a call
ledger to confirm its reranker actually ran on every row, because that component fails open (a degraded run returns a full, silently unranked result
set; 295 early rows failed exactly that check and were quarantined and re-run). Per-question contexts, answers, and grades for every arm are published
as reproduction artifacts, with a verifier that re-tallies, re-judges, and re-reads them; the per-question verdicts and context sizes are in
[a40-labs/memory](https://github.com/a40-labs/memory), while Zep Cloud's retrieval contexts stay with
[their repository](https://github.com/getzep/zep-papers), since that row is their data and not mine to redistribute.

### A side note for Obsidian users

Many people wire an [Obsidian](https://obsidian.md/) vault (markdown notes joined by `[[wikilinks]]`) into an agent as its memory, usually over MCP;
[Basic Memory](https://github.com/basicmachines-co/basic-memory) is the clearest example. By this post's taxonomy that is the **file-based** kind:
storage the model curates, read back by text search. What the vault adds is an explicit link graph, but authored at write time by hand or by the model
(one more thing curation has to get right) and walked deterministically rather than ranked: a graph doing a retriever's job through foresight. The
vault crosses toward the structured kind only when an embedding index is bolted on
([Smart Connections](https://github.com/brianpetro/obsidian-smart-connections), Obsidian Copilot), which swaps the grep for exactly the ranked read
path the structured store uses while the storage stays plain markdown. The honest picture is a spectrum: a plain vault sits with the file arm, an
embedded vault sits closer to the structured one, and the write-side curation cost this post measured is paid the whole way across, right up until you
stop asking a model to decide what to keep.
