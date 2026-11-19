# Async, tokio and concurrency

Load when: writing tokio code, background tasks, channels, shutdown,
event streams, threads, or atomics. Async is for waiting on I/O; CPU work
and blocking calls go elsewhere. Don't make code async that has nothing to
await (`clippy::unused_async`).

## Task lifecycle: every task has an owner, a stop signal and a join

```rust
let tracker = TaskTracker::new();          // tokio-util
let shutdown = CancellationToken::new();   // tokio-util
let child = shutdown.child_token();        // cancelled with its parent
tracker.spawn(async move {
    tokio::select! {
        _ = child.cancelled() => {}
        r = worker() => if let Err(e) = r { tracing::error!("{e:#}") },
    }
});
// on shutdown:
shutdown.cancel(); tracker.close(); tracker.wait().await;
```

- A bare `tokio::spawn` whose `JoinHandle` is dropped = a task nobody stops,
  joins, or hears panic. Use `TaskTracker`/`JoinSet`; check `JoinError::is_panic`. [async-joinset-structured]
- Token tree (root → subsystem → item) for graceful shutdown; cancel the
  parent, wait on the tracker with a timeout. [async-cancellation-token]
- Supervise long-lived loops: restart with capped exponential backoff,
  log each restart, give up loudly after N.
- Runtime: `#[tokio::main]` is fine for most binaries; build it by hand
  when something must initialise first (telemetry hubs — see below) or
  you need worker/blocking-pool tuning. [async-tokio-runtime]

## Never block the executor

- CPU-heavy or blocking calls (`std::fs`, sync DB drivers, compression,
  hashing big inputs) → `spawn_blocking` or rayon. [async-spawn-blocking]
- In async code use `tokio::fs`/`tokio::process`/`tokio::time::sleep`. [async-tokio-fs]
  **`tokio::fs::File` writes complete on a blocking thread: call
  `.flush().await` (and `sync_all` for durability) before you report
  success or drop it** — otherwise data can be lost or reordered.
- A UI/event loop must not await a slow request inline: spawn it and
  redraw from the result.

## Locks across `.await`

- Never hold a `std::sync::Mutex`/`RwLock` guard across `.await`
  (`clippy::await_holding_lock`; deadlocks and `!Send` futures). Scope the
  guard in a block, copy out what you need, then await. [async-no-lock-await] [anti-lock-across-await]
- `tokio::sync::Mutex` only when the critical section itself must await.
- Clone the `Arc`/data you need before awaiting instead of holding
  references across suspension. [async-clone-before-await]
- Nursery lints worth enabling: `significant_drop_tightening`,
  `significant_drop_in_scrutinee`, `future_not_send`.

## Channels: pick by shape

| Shape | Channel |
|---|---|
| Work queue, many producers → one consumer | `mpsc::channel(n)` — **bounded** [async-mpsc-queue] [async-bounded-channel] |
| One reply to one request | `oneshot` [async-oneshot-response] |
| Every subscriber sees every event | `broadcast` (slow receivers get `Lagged(n)`: handle it) [async-broadcast-pubsub] |
| Only the latest state matters | `watch` [async-watch-latest] |

- Unbounded channels hide overload until memory runs out; bounded ones push
  back. An `unbounded_channel` needs a written reason. [async-bounded-channel]
- A channel is a **wake-up**, not storage: anything that must survive a
  crash is written durably first (state-io.md), then signalled.

## select!, join!, cancellation safety

- `join!`/`try_join!` for independent futures you need all of
  (`try_join!` returns on the first error). [async-join-parallel] [async-try-join]
- `select!` races futures and **drops the losers**. Only put
  cancel-safe futures in a looping `select!` (`recv`, `accept`,
  `read` into a buffer kept outside the loop, `cancelled()`); a half-done
  `read_exact`, `write_all` or multi-step operation loses its progress. Pin a
  long future outside the loop and poll `&mut fut` instead. [async-select-racing] [async-cancel-safety]
- Timeouts: `tokio::time::timeout(d, fut)`; every external call has one.

## Event streams without gaps or polling

- **Subscribe first, then snapshot**: open the subscription, then read the
  current state, then apply events; otherwise events between snapshot and
  subscribe are lost.
- Per-key subscriptions need a reconciler for keys that appear later.
- Reconnect with backoff and re-snapshot after every reconnect (missed
  events are not replayed).
- `sleep`-polling loops are a last resort: prefer a notification (channel,
  `Notify`, OS watcher, DB hook). If you must poll, name the interval and why.

## Threads and atomics (sync code)

- Data parallelism: rayon `par_iter()` — for CPU-bound work over many
  items, measured. [conc-rayon-par-iter]
- `std::thread::scope` to borrow stack data in threads without `Arc`. [conc-scoped-threads]
- Atomics: the weakest **correct** ordering. `Relaxed` for counters;
  `Release`/`Acquire` pairs to publish data; `SeqCst` only when you can say
  why. If unsure, use a `Mutex`. [conc-atomic-ordering]
- `thread_local!` with `Cell`/`RefCell` instead of `static mut`. [conc-thread-local]

## Observability across awaits

- Tasks hop threads; thread-local context is lost. Attach context with
  spans: `#[tracing::instrument(skip(big_args))]` or
  `fut.instrument(span)`. Never hold `span.enter()` across `.await`. [obs-instrument-spans]
- Hub-based SDKs (e.g. Sentry): init before building the runtime, keep the
  guard alive for the process, `.bind_hub(Hub::current())` spawned futures;
  in tower/axum, the per-request hub layer must run before the transaction
  layer (axum `.layer()` applies bottom-up).

## Testing async code (see tdd.md)

- `#[tokio::test]`; `start_paused = true` + `tokio::time::advance` for
  time-dependent logic — no real sleeps in tests. [test-tokio-async]
- `loom` for lock-free/atomic algorithms; it explores interleavings. [test-loom-concurrency]
- Race regressions: drive the interleaving deterministically (a fake peer
  that emits at the worst moment), assert nothing is lost.
