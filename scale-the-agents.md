# Scaling the Agents: Autofill Architecture Evolution

This document traces the evolution of the collection autofill pipeline across four iterations: from per-row workflows (V0), to column-first batching
(V1), to concept elimination (V2), through 10B stress testing (V3), to LLM batch inference (V4). Each iteration addresses a specific scaling wall, and
the progression illustrates a general pattern: **optimize from the outermost loop inward** -- orchestration first, abstractions second, compute last.

---

## Context

Collections in Instill are spreadsheet-like structures where columns can have `enable_automatic_computation = true`. These "autofill" columns use LLM
inference to compute cell values based on column instructions, output schema, and the row's other cell values. Columns can depend on each other,
forming a DAG -- column B's instruction might reference column A's output.

When a user inserts rows, imports a file, or changes a column's instruction, the system must autofill the affected cells. The engineering challenge is
doing this correctly (respecting the DAG order), reliably (handling failures and concurrent mutations), and at scale.

---

## V0: Per-Row Workflows (Current)

### How It Works

Every trigger (InsertRows, recomputeColumn, file-ready event) dispatches **one Temporal workflow per row**. Each workflow independently:

1. **GetNamespaceActivity** -- resolve the namespace UID
2. **ConstructDAGActivity** -- fetch all columns, fetch the row, topologically sort columns into dependency layers, return cell UIDs grouped by layer
3. **CreateRowCacheActivity** -- collect files from FILE columns, fetch GCS URIs (with Redis cache), call the LLM worker to create a row-level cache,
   store metadata in Redis
4. **AutoFillActivity** (per cell, sequential within each layer) -- fetch the cell, call the LLM worker, update the cell in the DB, publish a
   `CellUpdatedEvent` via Redis SSE

```
Trigger
  └─ for each row
       └─ AutoFillWorkflow (autofill-{rowUID})
            ├─ GetNamespaceActivity
            ├─ ConstructDAGActivity
            ├─ CreateRowCacheActivity
            └─ for each DAG layer
                 └─ for each cell (sequential)
                      └─ AutoFillActivity
```

### The Numbers (1,000 rows × 10 autofill columns)

| Resource               | Count          |
| ---------------------- | -------------- |
| Temporal workflows     | 1,000          |
| GetNamespaceActivity   | 1,000          |
| ConstructDAGActivity   | 1,000          |
| CreateRowCacheActivity | 1,000          |
| AutoFillActivity       | 10,000         |
| Total activities       | 13,000         |
| DB queries             | ~15,000–20,000 |
| SSE events             | 10,000         |

### Why It Doesn't Scale

The fundamental issue is **redundant context loading**. Every row independently fetches and sorts the same column metadata, builds the same DAG, and
loads the same column instructions. For N rows and C columns, the system performs N × C fetch-and-process cycles when C cycles would suffice.

**Concrete bottlenecks:**

- **Temporal workflow explosion.** 1,000 rows → 1,000 workflow dispatches. Each dispatch involves a gRPC call to the Temporal server, task queue
  scheduling, and history initialization. At 100k rows, this saturates the Temporal cluster.
- **Sequential cell processing.** Within each workflow, AutoFillActivity runs cells one at a time per DAG layer. 10 columns processed sequentially per
  row means the workflow holds resources for 10× longer than necessary.
- **Per-cell DB round-trips.** Each AutoFillActivity performs its own SELECT (fetch cell) + UPDATE (persist result) + PUBLISH (SSE). At 10,000 cells,
  that's 30,000+ individual DB operations.
- **SSE flood.** 10,000 individual `CellUpdatedEvent` messages pumped through Redis. The frontend receives them one by one and applies them to AG Grid
  one by one, causing rendering churn.
- **Recompute amplification.** `recomputeCells` clears cells and publishes SSE events synchronously in the API handler before dispatching workflows.
  For 1,000 rows × 10 columns, that's 10,000 UPDATE + 10,000 PUBLISH calls blocking the API response.

**Hard ceiling:** At ~10k rows, the system begins to degrade. At 100k rows, it is effectively unusable. At 1M+ rows, it cannot even dispatch the
workflows.

---

## V1: Column-First Batch Processing (First Iteration)

### Core Insight

Autofill operations are **column-scoped**: the column instruction, output schema, type, and dependencies are identical for every row. The per-row
model reloads this shared context for every cell. By inverting the loop order from `for each row → for each column` to
`for each column → for each row chunk`, we:

- Load column metadata once per column, not once per cell
- Use bulk SQL with cursor pagination instead of per-cell UPDATEs
- Reduce Temporal workflow count from O(rows) to O(columns)
- Enable natural DAG ordering at the column level
- Aggregate events at the column level

**Equivalence proof:** The current model computes `for each row → for each column layer → process cell`. The proposed model computes
`for each column layer → for each row chunk → process cell`. These produce identical results because the DAG is defined by column dependencies, not
row data. Swapping loop order is safe.

### Architecture

```
Trigger
  └─ AutoFillBatchWorkflow (autofill-batch-{collectionUID})
       ├─ ConstructBatchDAGActivity → [[col_A, col_B], [col_C], ...]
       └─ for each DAG layer (sequential)
            └─ for each column in layer (parallel)
                 └─ AutoFillColumnWorkflow (autofill-col-{collectionUID}-{columnUID})
                      ├─ ClearCellsPageActivity (paginated, 10k/page)
                      └─ loop:
                           ├─ FetchChunkActivity (cursor, 500 rows)
                           ├─ AutoFillChunkActivity (bounded worker pool)
                           ├─ BulkUpdateCellsActivity
                           ├─ PublishProgressActivity
                           └─ if chunks >= MAX_PER_RUN → ContinueAsNew
```

**Two workflow types:**

- `AutoFillBatchWorkflow` (parent) -- constructs the DAG, dispatches column workflows in layer order, waits for each layer to complete before
  advancing
- `AutoFillColumnWorkflow` (child) -- processes all rows for one column with cursor pagination and ContinueAsNew to bound workflow history

**RowFilter abstraction** -- a serializable struct describing which rows to process:

```go
type RowFilter struct {
    CollectionUID datamodel.CollectionUID
    RowUIDs       []datamodel.RowUID  // explicit list (small batches, ≤5000)
    BatchUID      *datamodel.BatchUID // for very large InsertRows (>5000)
}
```

Activities resolve the filter into paginated DB queries with `ORDER BY "order" OFFSET $X LIMIT $Y`. No unbounded `IN` clauses.

**Five activity types:**

1. `ConstructBatchDAGActivity` -- topological sort + row count
2. `ClearCellsPageActivity` -- paginated bulk clear (10k rows/page)
3. `FetchChunkActivity` -- cursor-paginated cell fetch (500 rows)
4. `AutoFillChunkActivity` -- bounded LLM worker pool
5. `BulkUpdateCellsActivity` + `PublishProgressActivity` -- persist + notify

### The Numbers (1,000 rows × 10 columns, 8 DAG layers)

| Resource           | V0 (per-row)   | V1 (batch/column)         |
| ------------------ | -------------- | ------------------------- |
| Temporal workflows | 1,000          | 11 (1 parent + 10 column) |
| Total activities   | ~13,000        | ~90                       |
| DB queries         | ~15,000–20,000 | ~100                      |
| SSE events         | 10,000         | ~50                       |

V1 activities: 1 ConstructBatchDAG + 10 ClearCellsPage + (10 cols × 2 chunks × 4 per-chunk activities) = 91.

### What It Got Right

- Column metadata loaded once per column, not once per cell
- Bulk DB operations replaced per-cell round-trips
- DAG ordering was natural (process column layers in order)
- ContinueAsNew handled arbitrarily long columns
- Parent-child workflow topology isolated column failures

### What Was Still Rough

- **Too many concepts.** RowFilter had three modes (explicit UIDs, batch marker, collection-wide), each with different SQL generation paths. BatchUID
  required a schema migration.
- **Too many activity types.** Five activities per chunk iteration meant 5× Temporal dispatch overhead. FetchChunk → AutoFillChunk → BulkUpdateCells →
  PublishProgress always ran in the same order with no branching -- they were really one operation split into four.
- **Separate clearing phase.** ClearCellsPageActivity ran as a distinct phase before processing, adding latency and complexity. For InsertRows, cells
  are born uncomputed -- no clearing needed.
- **RowFilter payload risk.** Passing 5,000 row UIDs as workflow params approached Temporal's 2MB payload limit (~180KB at 5,000). Above that,
  BatchUID required a schema migration (`ALTER TABLE row ADD COLUMN batch_uid UUID`).

---

## V2: The Billion-Cell Architecture (Second Iteration)

### Design Principle: Nothing Unbounded, Nothing Redundant

V2 started by asking: **can I remove any concept from V1 without losing correctness or scalability?** Three concepts fell.

#### Elimination 1: RowFilter → `is_computed = false`

The database already knows which cells need processing. Every cell has an `is_computed` boolean: `false` for new cells and cleared cells, `true` after
autofill. Instead of telling the workflow _which rows_ to process, just tell it _which columns_ -- and it processes all cells where
`is_computed = false`.

This is:

- **Convergent.** If a batch is interrupted, the next one picks up exactly where it left off. Unprocessed cells still have `is_computed = false`.
- **Race-safe.** Two concurrent InsertRows both dispatch batch workflows. The second terminates the first. But cells already processed by the first
  have `is_computed = true` and are skipped. The second batch handles everything remaining.
- **Payload-free.** The workflow parameter is `{collectionUID, []columnUID}` -- ~200 bytes regardless of row count.
- **No schema migration.** `is_computed` already exists with the right semantics.

One partial index makes it fast:

```sql
CREATE INDEX idx_cell_uncomputed ON cell(column_uid) WHERE is_computed = false;
```

#### Elimination 2: Five Activities → Three

FetchChunk, AutoFillChunk, BulkUpdateCells, and PublishProgress always ran together in the same order with no branching. They became one
`ProcessChunkActivity` that does everything: fetch uncomputed cells, process with LLM pool, persist results, publish progress. One activity, one retry
boundary.

Each operation within the activity is idempotent: clearing an already-cleared cell is a no-op, re-running the LLM produces a valid result, database
updates target specific UIDs, duplicate progress events are harmless. Retrying the whole chunk is safe and bounded (500 cells).

**Final activity count:**

1. `ConstructBatchDAGActivity` -- topological sort + row count
2. `MarkForRecomputeActivity` -- heartbeated, can clear arbitrarily many cells without activity timeout
3. `ProcessChunkActivity` -- fetch + clear + LLM + persist + publish

#### Elimination 3: Separate Clearing Phase → Folded In

For InsertRows, cells are born with `is_computed = false`. No clearing needed. For recompute, `MarkForRecomputeActivity` runs once at the start of the
column workflow, using heartbeating to handle arbitrarily large clearing operations. The clearing/processing phase split disappears.

### Final Architecture

```
Trigger
  └─ AutoFillBatchWorkflow (autofill-batch-{collectionUID})
       ├─ ConstructBatchDAGActivity → [[col_A, col_B], [col_C], ...]
       └─ for each DAG layer (sequential)
            └─ for each column in layer (parallel)
                 └─ AutoFillColumnWorkflow (autofill-col-{collectionUID}-{columnUID})
                      ├─ MarkForRecomputeActivity (first run only, heartbeated)
                      └─ loop:
                           ├─ ProcessChunkActivity (fetch + LLM + persist + publish)
                           └─ if chunks >= MAX_PER_RUN → ContinueAsNew
```

**Component count: 2 workflows, 3 activities, 1 index, 2 event types.** Each exists because removing it would lose either correctness or scalability.

### Workflow Detail

**AutoFillBatchWorkflow** (parent):

```go
func AutoFillBatchWorkflow(ctx workflow.Context, param *AutoFillBatchWorkflowParam) error {
    // 1. ConstructBatchDAGActivity → [][]ColumnUID (topologically sorted layers)
    // 2. For each layer:
    //    a. Launch AutoFillColumnWorkflow as child for each column (parallel)
    //    b. Wait for all children before advancing to next layer
}
```

History budget: ~8 layers × ~20 columns × 3 events per child = ~480 events. Well within Temporal's 50k limit.

**AutoFillColumnWorkflow** (child, with ContinueAsNew):

```go
const MaxChunksPerRun = 100 // ~50k rows per run, keeps history under ~500 events

func AutoFillColumnWorkflow(ctx workflow.Context, param *AutoFillColumnWorkflowParam) error {
    // Phase 1 (first run only): mark cells for recompute
    if param.IsRecompute && !param.ClearingDone {
        MarkForRecomputeActivity(collectionUID, columnUID) // heartbeated
        param.ClearingDone = true
    }

    // Phase 2: process chunks with cursor pagination
    chunksProcessed := 0
    for chunksProcessed < MaxChunksPerRun {
        processed := ProcessChunkActivity(collectionUID, columnUID, param.Offset, ChunkSize)
        if processed == 0 { break } // no more uncomputed cells
        param.Offset += ChunkSize
        chunksProcessed++
    }

    if chunksProcessed == MaxChunksPerRun {
        return workflow.NewContinueAsNewError(ctx, AutoFillColumnWorkflow, param)
    }
    return nil
}
```

### Hybrid Dispatch

Small inserts stay fast. Large operations go through the batch path:

| Trigger              | Path                                       |
| -------------------- | ------------------------------------------ |
| InsertRows (≤5 rows) | Existing per-row `AutoFillWorkflow` (v0)   |
| InsertRows (>5 rows) | `AutoFillBatchWorkflow`                    |
| recomputeColumn      | `AutoFillBatchWorkflow` (isRecompute=true) |
| File ready event     | Per-row or batch depending on row count    |

### Event System

Two new event types replace the per-cell `CellUpdatedEvent` flood:

- `ColumnAutofillProgressEvent` -- sent once per chunk completion. The frontend uses this for column-level progress bars.
- `CellsBatchUpdatedEvent` -- carries the chunk's worth of cell results in a single Redis message. The frontend applies them to AG Grid in one
  `applyTransaction` call.

The existing `CellUpdatedEvent` remains for the per-row fast path (≤5 rows).

### Convergence Properties

The `is_computed = false` flag is the single source of truth. Every failure mode resolves naturally:

| Scenario                          | What happens                                                                                                                 |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Batch interrupted mid-column      | Unprocessed cells still have `is_computed = false`. Next batch resumes from there.                                           |
| Concurrent InsertRows             | Second dispatch terminates first. First's completed cells are `is_computed = true` and skipped.                              |
| Concurrent recompute + insert     | Recompute marks existing cells `is_computed = false`. Insert adds cells born `is_computed = false`. Both sets get processed. |
| User edits cell during processing | Conditional UPDATE (`WHERE user_input_text IS NULL`) prevents overwriting user input.                                        |
| Column workflow fails             | Other columns in the same layer are unaffected (child workflow isolation).                                                   |

---

## V3: 10B Stress Test

V2 handles 100k–10M cells cleanly. But does it hold at **10 billion** cells (e.g., 100M rows × 100 columns)?

This section stress-tests V2 at 10B and classifies every component into three buckets: holds, creaks, or breaks.

### What Holds (No Changes Needed)

**Database-is-the-queue cursor.** `is_computed = false` as the universal work marker is row-count-agnostic. `FetchUncomputedChunk` is always
`O(log N + chunk_size)` via the B-tree partial index. The index _shrinks_ as work completes. No state management, no cursor persistence, no lost work
on crash.

**ContinueAsNew.** At 100M rows per column with ChunkSize=500 and MaxChunksPerRun=100, each column needs 2,000 ContinueAsNew cycles. Each cycle is a
fresh, short-lived workflow execution with ~300 events -- well under Temporal's 50k limit. The only state carried across cycles is `param.Offset` (an
integer).

**Convergence.** New batch terminates old, picks up remaining `is_computed = false` cells. The database state is the single source of truth. No
workflow-level state is lost. This property is unconditionally correct regardless of row count.

**Bounded operations.** Every DB query, every activity payload, every workflow history is bounded by constant chunk/page sizes. No operation grows
with N.

**Horizontal scaling.** Processing throughput scales linearly with Temporal worker pods. 10× workers = 10× throughput. No single-writer bottleneck.

### What Creaks (Needs Tuning, Not Redesign)

**Temporal workflow execution count.** 100 columns × 2,000 ContinueAsNew cycles = 200,000 workflow executions per operation. Temporal can handle this,
but needs a properly sized cluster (sufficient history shards, adequate persistence backend). This is operational tuning, not an architecture problem.

**Processing time.** 10B LLM calls at 5 seconds each with a pool of 10 per chunk = ~250 seconds per chunk. 20M chunks total. With 100 worker pods × 10
concurrent activities = 1,000 parallel chunks. Total wall time: ~58 days. With 1,000 worker pods: ~5.8 days. ContinueAsNew ensures no workflow
accumulates unbounded history over weeks of processing.

**MarkForRecompute at 100M rows per column.** Paginated at 10k per UPDATE, that's 10,000 UPDATE statements per column with heartbeating. Takes
minutes, not hours.

### What Breaks (Requires Architectural Additions)

**Gap 1: PostgreSQL single-table scalability.** A `cell` table with 10B rows is ~5TB. Index maintenance on INSERT/UPDATE becomes expensive, VACUUM
overhead grows, single-node I/O becomes the bottleneck.

_Fix:_ Table partitioning by `collection_uid`. PostgreSQL native partitioning (`PARTITION BY HASH(collection_uid)`) keeps the architecture unchanged
-- every query already filters by `collection_uid`, so the query planner prunes to the right partition. No code changes needed, only a migration.

```sql
CREATE TABLE cell (
    ...
) PARTITION BY HASH (collection_uid);

-- 64 partitions, each ~80GB instead of one 5TB table
CREATE TABLE cell_p0 PARTITION OF cell FOR VALUES WITH (MODULUS 64, REMAINDER 0);
CREATE TABLE cell_p1 PARTITION OF cell FOR VALUES WITH (MODULUS 64, REMAINDER 1);
-- ...
```

**Gap 2: SSE event volume.** At 10B cells / 500 per chunk = 20M `CELLS_BATCH_UPDATED` events + 20M `COLUMN_AUTOFILL_PROGRESS` events. No browser can
consume 40M SSE events.

_Fix:_ Hybrid push/poll event model. For large batches (>10k cells), replace per-chunk SSE with a polling-based progress endpoint backed by
`CountUncomputedPerColumn` (fast query on partial index). Keep real-time SSE for small batches where responsiveness matters. Threshold determined by
`totalUncomputed` from `ConstructBatchDAGActivity`.

**Gap 3: LLM rate limiting.** At 10B cells with hundreds of workers, concurrent LLM API calls exceed provider rate limits. The current architecture
relies on activity retry with backoff, which wastes retry slots.

_Fix:_ Token-bucket rate limiter in Redis, acquired by `ProcessChunkActivity` before each LLM call. Provides proactive throttling instead of reactive
retry-on-429. Configurable per-model and per-namespace.

### Assessment

The three gaps are all **additive** -- table partitioning, polling, and rate limiting augment V2 without changing any core workflow logic. The
alternative at 10B (Kafka + Flink streaming) handles throughput natively but introduces massive operational complexity and loses the simplicity of
"database is the queue." For a platform where most users have <1M cells and a few power users push 10B, V2 + additions is more pragmatic.

---

## V4: LLM Batch Inference

### The Last Multiplier

V2 reduced the orchestration overhead from O(rows × columns) to O(columns × rows/chunk_size). But inside `ProcessChunkActivity`, the LLM call is still
**one per cell**. At 10B cells, this is the dominant cost and time factor. V4 addresses the innermost loop.

### Observation: Column-Scoped Redundancy

For all cells in the same column, the LLM call shares:

- Same column instruction
- Same column type and output schema
- Same knowledge base context
- Same collections context (cross-references)

What differs per cell is only the **row data** (the values from other columns in that row) and potentially the **row-level file cache** (for columns
that depend on FILE-type columns).

The current architecture constructs the same prompt envelope 500 times per chunk and sends 500 separate API calls. Each call carries the identical
system instruction, schema definition, and tool configuration.

### The Change

Instead of one LLM call per cell, batch N rows into a single LLM call with an array output schema:

```
Current (V2):  500 cells → 500 LLM calls (1 cell per call)
V4:            500 cells → 25 LLM calls (20 cells per call)
```

The output schema changes from a single value to an array of keyed results:

```json
// V2: single-cell output
{ "value": "Technology" }

// V4: batch output (20 rows)
[
  { "row_id": "row_001", "value": "Technology" },
  { "row_id": "row_002", "value": "Healthcare" },
  ...
]
```

### Implementation

**New gRPC RPC:** `ProcessBatchAutofill` -- accepts one column instruction/context with an array of row data, returns an array of results.

**ProcessChunkActivity splits cells into two paths:**

1. **Cached path** (rows with existing file-level row cache): processed individually through the current per-cell flow. Each row's cache contains
   unique file content that cannot be shared.
2. **Batch path** (rows without file dependencies): grouped into batches of ~20 rows. Each batch makes one LLM call with the shared column context and
   an array of row data.

```
ProcessChunkActivity (500 cells)
  ├─ Load column metadata ONCE
  ├─ Partition cells: cached (per-row files) vs. batchable
  ├─ Cached cells → existing per-cell LLM flow (e.g., 50 cells → 50 calls)
  ├─ Batchable cells → groups of 20 → batch LLM calls (e.g., 450 cells → 23 calls)
  ├─ Collect all results
  ├─ BulkUpdate + PublishProgress
  └─ Return
```

### Why 20 Rows Per Batch?

- **Token limits.** Each row contributes ~200–500 tokens of context. At 20 rows, the row data portion is ~4k–10k tokens, leaving ample room for the
  column instruction and output within most model context windows.
- **Error isolation.** If one row produces a malformed response, only 20 rows need retry, not 500.
- **Structured output reliability.** LLMs produce more reliable structured output for smaller arrays. At 50+ items, output parsing failures increase.
- **Configurable.** `llmBatchSize` is a column-type-level parameter, defaulting to 1 (current behavior) with opt-in batching for compatible column
  types.

### Tradeoffs

| Consideration             | Impact                                                    |
| ------------------------- | --------------------------------------------------------- |
| LLM API calls             | 20× reduction (dominant cost savings)                     |
| Prompt overhead           | Column instruction sent once per batch, not once per cell |
| Latency per cell          | Better (amortized API call overhead)                      |
| Error granularity         | Coarser (one bad row can fail a batch of 20)              |
| File-dependent columns    | Cannot batch (each row has unique file cache)             |
| Output parsing complexity | Higher (must reliably extract N keyed results)            |

### Impact on Scaling Math

At 1B cells (10M rows × 100 columns), with `llmBatchSize=20` and 100 worker pods:

| Metric          | V2 (per-cell LLM) | V4 (batch LLM) |
| --------------- | ----------------- | -------------- |
| LLM API calls   | 1,000,000,000     | 50,000,000     |
| API cost (est.) | ~$500k            | ~$25k          |
| Wall-clock time | ~6 days           | ~14 hours      |

LLM API calls drop by 20×. Wall-clock improves by ~10× (not 20×) because each batch call processes more tokens and takes roughly twice as long as a
single-cell call. The 20× reduction in API calls -- and the proportional cost reduction -- is the single largest efficiency multiplier in the entire
architecture. V1→V2 optimized the orchestration layer; V4 optimizes the compute layer.

---

## Side-by-Side Comparison

### 1,000 rows × 10 columns (8 DAG layers)

| Metric             | V0 (per-row)   | V1 (batch/column) | V2 (simplified) | V4 (+batch LLM) |
| ------------------ | -------------- | ----------------- | --------------- | --------------- |
| Temporal workflows | 1,000          | 11                | 11              | 11              |
| Total activities   | ~13,000        | ~90               | ~30             | ~30             |
| LLM API calls      | 10,000         | 10,000            | 10,000          | **500**         |
| DB queries         | ~15,000–20,000 | ~100              | ~50             | ~50             |
| SSE events         | 10,000         | ~50               | ~50             | ~50             |
| Workflow payload   | ~2KB each      | ~36KB (RowFilter) | ~200 bytes      | ~200 bytes      |
| Schema migration   | None           | Yes (batch_uid)   | None            | None            |
| Activity types     | 4              | 5                 | 3               | 3               |

### 100,000 rows × 10 columns (2 DAG layers)

| Metric             | V0 (per-row) | V1 (batch/column) | V2 (simplified) | V4 (+batch LLM) |
| ------------------ | ------------ | ----------------- | --------------- | --------------- |
| Temporal workflows | 100,000      | 11                | 11              | 11              |
| Total activities   | ~1,300,000   | ~2,010            | ~2,010          | ~2,010          |
| LLM API calls      | 1,000,000    | 1,000,000         | 1,000,000       | **50,000**      |
| SSE events         | 1,000,000    | ~2,010            | ~2,010          | ~2,010          |
| Feasible?          | Barely       | Yes               | Yes             | Yes             |

### 10,000,000 rows × 100 columns = 1B cells (8 DAG layers)

Wall-clock assumes: 500 cells/chunk, 10 goroutines/activity, 5s/LLM call, 10 activities/pod, 100 pods = 1,000 parallel chunks.

| Metric                | V0 (per-row)   | V1 (batch/column) | V2 (simplified) | V4 (+batch LLM) |
| --------------------- | -------------- | ----------------- | --------------- | --------------- |
| Temporal workflows    | 10,000,000     | 101               | 101             | 101             |
| ContinueAsNew cycles  | N/A            | 200/column        | 200/column      | 200/column      |
| Activities            | ~1B            | ~2,000,100        | ~2,000,100      | ~2,000,100      |
| LLM API calls         | 1,000,000,000  | 1,000,000,000     | 1,000,000,000   | **50,000,000**  |
| Workflow payload      | ~20GB total    | ~200 bytes        | ~200 bytes      | ~200 bytes      |
| Temporal history/run  | Unbounded      | ~500 events       | ~500 events     | ~500 events     |
| Wall-clock (100 pods) | **Impossible** | ~6 days           | ~6 days         | **~14 hours**   |
| Feasible?             | **Impossible** | Yes               | Yes             | Yes             |

---

## Complexity Bounds (V4)

| Dimension                | Bound                                                         |
| ------------------------ | ------------------------------------------------------------- |
| Temporal workflows       | O(columns) -- constant regardless of row count                |
| Temporal history per run | O(MaxChunksPerRun) -- bounded constant                        |
| Workflow payload         | O(columns) -- no row data, ever                               |
| Activities per column    | O(rows / chunk_size) -- linear, bounded per ContinueAsNew run |
| LLM API calls per chunk  | O(chunk_size / llm_batch_size) -- 20× reduction vs. per-cell  |
| DB round-trips per chunk | O(1) -- fetch + update + progress                             |
| SSE events               | O(columns × rows / chunk_size) -- per chunk, not per cell     |
| Memory                   | O(chunk_size) -- one chunk resident at a time                 |

The architecture is **row-count-agnostic**: it behaves identically for 100 rows and 10M rows. The only variable is how many ContinueAsNew cycles the
column workflow goes through, which Temporal handles transparently.

---

## Key Engineering Decisions

### Why ContinueAsNew Instead of Segment Parallelism?

An alternative considered was splitting each column into fixed-size segments (e.g., 100 segments of 100k rows) running as parallel workflows. This
eliminates ContinueAsNew and gives intra-column parallelism.

**Rejected because:**

- The LLM worker semaphore (25 concurrent executions) is the real throughput bottleneck, not workflow orchestration. Adding intra-column parallelism
  doesn't help if the LLM pool is already saturated from multiple columns running in parallel.
- Segment parallelism adds coordination overhead (aggregating progress across segments, handling partial failures).
- Sequential chunk processing gives predictable, steady progress tracking.
- Adding parallelism later is easy; removing accidental complexity later is hard.

### Why Not Skip Temporal Entirely?

A PostgreSQL job queue with a background worker would be simpler. **Rejected because** it sacrifices automatic retries, workflow visibility, DAG
ordering, durability guarantees, and ContinueAsNew for long-running operations -- all of which Temporal provides out of the box.

### Why a Thick ProcessChunkActivity?

Merging fetch + LLM + persist + publish into one activity means a DB failure after successful LLM processing causes the LLM calls to be re-executed on
retry. **Accepted because:**

- Chunks are 500 cells. Re-executing 500 LLM calls is negligible in a 1B-cell operation.
- The alternative (separate activities) means 4× Temporal dispatch overhead per chunk across potentially 20,000 chunks per column.
- All operations within the activity are idempotent, so retry is always safe.

### Why Keep the Per-Row Path for ≤5 Rows?

Single-row inserts are the most common user action. The per-row workflow provides lower latency (no DAG construction overhead, no batch dispatch) and
simpler observability. The threshold exists to avoid paying batch overhead for the common case.

---

## Literature Review: Bigtable, MapReduce, and Flink

The autofill pipeline operates on a 3-dimensional data model (collection × row × column → cell) and must process billions of cells with DAG-ordered
dependencies. This section positions the architecture against three canonical large-scale data systems to clarify what it borrows, what it rejects,
and why.

### Google Bigtable

**Reference:** Chang et al., "Bigtable: A Distributed Storage System for Structured Data," OSDI 2006.

Bigtable models data as `(row_key, column_family:qualifier, timestamp) → value` -- a sparse, distributed, persistent sorted map. Rows are
lexicographically sorted and split into **tablets** (contiguous row ranges), each assigned to a tablet server. Column families are the unit of access
control and storage locality. GFS provides the underlying distributed file system, and Chubby provides coordination.

**Structural parallels with autofill:**

| Concept                | Bigtable                                          | Autofill                                             |
| ---------------------- | ------------------------------------------------- | ---------------------------------------------------- |
| Data shape             | (row, column_family:qualifier, timestamp) → bytes | (row, column, collection) → computed value           |
| Partitioning unit      | Tablet (row range)                                | Chunk (500 cells by column)                          |
| Column grouping        | Column families (storage locality)                | Column-scoped processing (shared instruction/schema) |
| Work splitting         | Tablet server assignment                          | ContinueAsNew cycles per column                      |
| Background maintenance | Compaction (merge SSTables)                       | Convergent processing (`is_computed = false` → true) |

**Key divergence: passive vs. active cells.** A Bigtable cell is inert storage -- a versioned blob written by an external process. An autofill cell is
an active computation target with a state machine (`uncomputed → computed`) whose value is derived from an LLM inference call. This distinction makes
Bigtable's read/write optimization irrelevant; the bottleneck is not I/O throughput but inference latency.

**Distribution model.** Bigtable distributes the **data** across tablet servers and moves compute to where the data lives (data locality). Autofill
distributes the **compute** across Temporal worker pods while keeping data in a single PostgreSQL cluster. The inversion is justified: when each cell
operation is a 5-second LLM API call, a 1ms network hop to the database is noise. Data locality optimizes for microsecond storage latency; autofill's
bottleneck is measured in seconds.

**Where Bigtable's ideas do apply.** V3's `PARTITION BY HASH(collection_uid)` is the direct analog of tablet splitting. Both exploit the fact that
queries already filter by the partition key (row key range for Bigtable, `collection_uid` for autofill), so partition pruning is automatic and
requires no code changes.

### Google MapReduce

**Reference:** Dean and Ghemawat, "MapReduce: Simplified Data Processing on Large Clusters," OSDI 2004.

MapReduce decomposes computation into a **map** phase (apply a function to each input independently, emit key-value pairs) and a **reduce** phase
(aggregate all values for each key). The framework handles distribution, fault tolerance, and scheduling. Map tasks run close to the data (GFS data
locality). The model is embarrassingly parallel within each phase.

**Why MapReduce doesn't fit autofill:**

1. **No DAG ordering.** MapReduce assumes independence between map tasks. Autofill has column dependencies: column B's input includes column A's
   output. Processing column B before column A produces incorrect results. MapReduce has no native mechanism to express "all map tasks for partition A
   must complete before partition B begins."

2. **Would require chained jobs.** To express autofill's DAG in MapReduce, each DAG layer would be a separate MapReduce job: Layer 1 map-reduce
   completes, then Layer 2 reads Layer 1's output and runs its own map-reduce, and so on. This is exactly what higher-level frameworks (Pig, Hive,
   Beam) do -- and it introduces inter-job coordination, intermediate storage, and startup overhead per layer. Temporal's parent-child workflow model
   provides the same DAG ordering natively.

3. **Reduce phase is unnecessary.** Autofill has no aggregation step. Each cell's output is independent -- there's nothing to reduce. The computation
   is `map(cell) → LLM(cell) → result`, with the only constraint being DAG ordering across columns. MapReduce's shuffle-and-reduce machinery is pure
   overhead.

4. **Data locality is irrelevant.** MapReduce's core optimization is scheduling map tasks on the same machine that holds the GFS chunk. This matters
   when disk I/O is the bottleneck. For autofill, the dominant cost is a 5-15 second external API call -- scheduling a task "close to the data" saves
   nothing.

**What MapReduce gets right that autofill borrows:** fault tolerance through idempotent re-execution. MapReduce re-runs failed map tasks on different
workers; autofill re-runs failed `ProcessChunkActivity` on any available Temporal worker. Both rely on the idempotency of the per-unit operation (map
function or chunk activity) to make retry safe.

### Apache Flink

**Reference:** Carbone et al., "Apache Flink: Stream and Batch Processing in a Single Engine," IEEE Data Engineering Bulletin, 2015.

Flink is a distributed stream-and-batch processing engine built around a **dataflow DAG** of operators. Data flows through the DAG as records in
streams. Flink provides exactly-once semantics through **checkpointing** (periodic consistent snapshots of operator state), **watermarks** (progress
indicators for event time), and **backpressure** (flow control when downstream operators are slow).

**Flink is the closest architectural analog to autofill.** The structural mapping is tight:

| Concept           | Flink                                     | Autofill V2/V4                                        |
| ----------------- | ----------------------------------------- | ----------------------------------------------------- |
| Execution model   | Dataflow DAG of operators                 | DAG of column layers                                  |
| Parallelism unit  | Task slot (subtask per partition)         | Temporal worker activity slot                         |
| Data partitioning | Key groups (hash of key → partition)      | Column × chunk                                        |
| Windowing         | Time/count windows                        | Chunk size (500 cells)                                |
| Checkpointing     | Chandy-Lamport snapshots (periodic)       | ContinueAsNew (reset workflow history)                |
| Progress tracking | Watermarks (monotonic event-time markers) | `is_computed = false` count shrinking toward 0        |
| Backpressure      | TCP-based, per-channel                    | LLM semaphore (bounded concurrent calls)              |
| Exactly-once      | Checkpoint + deterministic replay         | Idempotent activities + convergent flag               |
| Fault recovery    | Rollback to last checkpoint, replay       | Re-run chunk from current offset (no rollback needed) |

**Where Flink would be stronger:**

- **Intra-operator parallelism.** Flink partitions each operator's input across task slots, giving automatic data parallelism within a single DAG
  node. Autofill processes each column sequentially (one chunk at a time per column workflow), relying on inter-column parallelism within a DAG layer.
  For a single column with 10M rows, Flink could partition across 100 slots; autofill processes the 20,000 chunks serially within one workflow (with
  ContinueAsNew). Adding segment parallelism (rejected in V2, see "Key Engineering Decisions") would close this gap, but the LLM semaphore makes it
  unnecessary -- the bottleneck is API concurrency, not chunk throughput.

- **Native backpressure propagation.** Flink's TCP-based backpressure automatically slows upstream operators when downstream operators can't keep up.
  Autofill's equivalent is the LLM semaphore, which bounds concurrent API calls but doesn't propagate pressure back to Temporal's task scheduling. At
  extreme scale, this means Temporal may queue more activities than workers can drain, but Temporal's own queue management handles this gracefully.

- **Event-time semantics.** Flink's watermarks enable processing of out-of-order events with well-defined completeness guarantees. Autofill doesn't
  need this -- the processing order is determined by the static column DAG, not by event arrival time.

**Where autofill is simpler by design:**

- **No distributed state.** Flink operators maintain partitioned state (key-value stores backed by RocksDB or heap), requiring checkpoint coordination
  across all operators. Autofill has no operator state -- the database is the single source of truth. `is_computed = false` is both the work queue and
  the checkpoint. This eliminates Flink's entire state management and recovery subsystem.

- **No shuffle.** Flink's DAG can include repartitioning (shuffle) between operators when the downstream key differs from the upstream key. Autofill's
  DAG is column-ordered with no repartitioning -- every chunk in a column uses the same column metadata, and the transition between DAG layers is a
  simple "wait for all children, then start next layer." No network shuffle, no intermediate serialization.

- **No cluster management.** Flink requires a JobManager, TaskManagers, checkpoint storage (S3/HDFS), and often ZooKeeper for HA. Autofill uses
  Temporal (which the platform already runs) and PostgreSQL (which the platform already runs). Zero additional infrastructure.

- **Convergent recovery vs. checkpoint rollback.** When a Flink job fails, it rolls back ALL operators to the last consistent checkpoint and replays
  input from that point. This means work done after the checkpoint is lost and re-executed. Autofill never loses completed work: cells already marked
  `is_computed = true` survive any failure. Recovery processes only the remaining `false` cells. For a 1B-cell operation that fails at 80% completion,
  Flink replays from the last checkpoint (potentially re-processing millions of records); autofill resumes from the 200M remaining cells.

**Why not use Flink?**

The autofill workload has a property that inverts Flink's value proposition: **the per-record operation dominates the per-record overhead by 4-5
orders of magnitude.** A Flink operator typically processes a record in microseconds to milliseconds (deserialization, computation, serialization).
The overhead of Flink's machinery (checkpointing, shuffle, state management) is justified because it's amortized across millions of fast operations.

Autofill's per-record operation is a 5-15 second LLM API call. The overhead of Temporal's activity dispatch (~10ms), PostgreSQL's query (~1ms), and
SSE publish (~1ms) totals ~12ms -- 0.2% of the LLM call. Flink's sophisticated machinery would optimize the 0.2%, not the 99.8%. The operational cost
of running a Flink cluster (JobManager, TaskManagers, checkpoint storage, monitoring) is not justified when the framework overhead is already
negligible relative to the workload.

### Positioning Summary

| Dimension           | Bigtable + MapReduce                                   | Apache Flink                                              | Autofill V2/V4                                 |
| ------------------- | ------------------------------------------------------ | --------------------------------------------------------- | ---------------------------------------------- |
| Primary problem     | Distribute petabytes for storage and batch computation | Stream/batch processing with exactly-once and low latency | Orchestrate DAG-ordered LLM inference at scale |
| Data model          | Sparse sorted map (row, column, timestamp)             | Unbounded/bounded streams of records                      | Relational table (collection × row × column)   |
| Distribution unit   | Tablet (row range, ~200MB)                             | Key group (hash partition)                                | Chunk (500 cells by column)                    |
| DAG support         | None (MapReduce is flat); requires chained jobs        | Native (dataflow graph of operators)                      | Native (Temporal parent-child workflows)       |
| Parallelism         | Embarrassingly parallel map tasks                      | Intra-operator data parallelism                           | Inter-column parallelism within DAG layers     |
| Fault tolerance     | Re-execute failed map/reduce tasks                     | Checkpoint rollback + replay                              | Convergent flag (no rollback, no replay)       |
| State management    | External (GFS/Bigtable)                                | Operator-local (RocksDB/heap) + checkpoints               | Database-is-the-truth (PostgreSQL)             |
| Scaling bottleneck  | Disk I/O, network bandwidth                            | Record throughput, state size                             | LLM API latency and rate limits                |
| Operational cost    | GFS + Bigtable + MapReduce cluster                     | JobManager + TaskManagers + checkpoint storage + ZK       | Temporal (shared) + PostgreSQL (shared)        |
| Per-record overhead | ~ms (disk seek + network)                              | ~μs–ms (serde + state access)                             | ~5–15s (LLM API call)                          |
| Sweet spot          | Petabyte scans, web indexing                           | High-throughput stream processing, windowed aggregation   | DAG-ordered external API orchestration         |

The autofill architecture occupies a design space that none of these systems target directly: **DAG-ordered, externally-bounded, cell-level
computation** where the per-cell cost is seconds (not microseconds), the data fits in a single database (not distributed storage), and correctness
requires column-dependency ordering (not embarrassingly parallel). It borrows Bigtable's partitioning insight, Flink's DAG structure, and MapReduce's
idempotent retry -- while avoiding the operational complexity of all three by exploiting the fact that when your bottleneck is a 5-second external API
call, framework overhead is irrelevant.

---

## Lessons

1. **The database is your filter.** Before inventing a filter abstraction (RowFilter, BatchUID), check if the database already has the answer.
   `is_computed = false` eliminated an entire concept and a schema migration.

2. **Activities that always run together are one activity.** If there's no branching between steps and retrying the whole sequence is safe, merge
   them. The overhead of splitting is real; the benefit is theoretical.

3. **Convergence beats coordination.** Instead of carefully tracking which rows were inserted, which were cleared, and which were processed, make the
   workflow idempotent: "process whatever has `is_computed = false`." Interruptions, concurrent triggers, and partial failures all resolve naturally.

4. **Invert the loop, not the abstraction.** V0 → V1 was a loop inversion: `for rows → for columns` became `for columns → for rows`. This single
   change reduced workflows from O(rows) to O(columns) while producing identical results. The equivalence proof is trivial because the DAG is
   column-defined, not row-defined.

5. **Bound everything.** Workflow payloads, SQL queries, Temporal history, DB updates, SSE payloads -- every data structure and operation must have a
   known upper bound. Unbounded anything is a scaling time bomb.

6. **Stress-test at 1000× before shipping at 1×.** V3 evaluated V2 at 10B cells and found three gaps (table partitioning, SSE volume, rate limiting)
   -- all additive fixes, none requiring redesign. Knowing the ceiling before hitting it is the difference between "we need to augment" and "we need
   to rewrite."

7. **Optimize the innermost loop last.** V1 optimized the orchestration (workflows). V2 optimized the concepts (fewer abstractions). V4 optimized the
   compute (LLM calls). Each layer was only worth addressing after the layer above it was clean. Batching LLM calls on top of V0's per-row model would
   have given 20× fewer LLM calls but still 100k workflows -- the wrong bottleneck.

8. **Shared context is a batching signal.** When N invocations share the same instruction, schema, and tools, and differ only in input data, that's a
   batching opportunity. The column-scoped nature of autofill made this natural: same prompt envelope, different row data.
