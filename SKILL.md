---
name: rusty-skills
description: >
  Rust engineering method for writing, reviewing, refactoring, porting and
  debugging Rust: test-driven, measured, lean, single source of truth.
  A short core plus guides loaded on demand (errors, ownership/memory,
  types/API, async/tokio, state/IO/serde, security/unsafe, perf, TDD,
  project/docs/observability, lints, lean review, porting, process,
  open-source collaboration).
  Covers all 265 rust-skills rules plus rust-anything, ponytail and
  debloatify methods. Use for any Rust code task, Rust code review,
  "is this over-engineered", Rust lint setup, or porting code to Rust.
license: MIT
---

# rusty-skills

Write the least Rust that is **proven** correct. Evidence over opinion:
tests, the compiler, lints and scripts decide; judgment fills the gaps.

## Core loop (every change)

1. **Understand**: read the code you touch and its tests; check the
   repo's `PITFALLS.md`/`DECISIONS.md` if present. Load the guide(s) for
   the situation (router below) — only those.
2. **Ladder** before writing (references/lean.md): does it need to exist?
   → std → platform/peer → a dep already in `Cargo.lock` → one expression
   → minimal code.
3. **Red**: a failing test that states the behaviour or reproduces the
   bug — failing for the right reason (references/tdd.md).
4. **Green**: least code to pass. **Fix the code, never the test.**
5. **Lean**: refactor with tests green; delete what you replaced.
6. **Gate** (below) green, then report with evidence.

**Stall rule**: three edits without a new passing test → stop, list what
still fails, rethink or ask.

## Always-on rules

Errors and panics
- Expected failures → `Result`; panics only for broken invariants you own.
  No `unwrap()` outside tests; `expect("why it can't fail")` for invariants.
- Never drop an error silently (`let _ =`, `.ok();`, `map_err(|_|..)`)
  without a written reason. Libraries: `thiserror`; apps: `anyhow` +
  `.context()`. Log an error once, at the boundary, with its chain.
- No byte-slicing `&str` at computed offsets, no `v[i]` on untrusted
  indices: `get`, iterators, `split_once`, `char_indices`.

Types and ownership
- Parse, don't validate: untrusted input → validated types at the
  boundary. Enums for states, newtypes for ids/units, no stringly APIs.
- Borrow by default (`&str`, `&[T]`, `&Path`); own only what you store.
  Every `.clone()` needs an ownership reason.
- No trait/generic/builder/factory with one implementation or one caller.

Async and state
- Every spawned task has an owner, a cancel signal and a join
  (`TaskTracker` + `CancellationToken`). No lock guard across `.await`.
  Bounded channels. No blocking calls on the executor.
- One owner per piece of state; durable writes are atomic (temp + flush +
  rename); multi-step DB changes are transactions.
- Subscribe before snapshot; timeouts on every external call.

Security
- Data never becomes code: no shell strings, paths or binaries built from
  input; allow lists for names; secrets never logged.
- `unsafe` only in a small module, each block with `// SAFETY:`.

Discipline
- Measure before optimising, and before choosing lint levels.
- Comments explain *why*; no history, apologies or restating code.
- Replace = delete the old path in the same change (single source of truth).
- Never simplify away: validation at trust boundaries, data-loss
  handling, security, accessibility, or what was explicitly asked for.

## Router: load a guide when the code needs it

| When you are... | Load |
|---|---|
| handling errors, `Result`, panics, `unwrap`, `let _ =` | references/errors.md |
| choosing param/return types, clones, `Arc`/`Rc`/`RefCell`/`Mutex`, allocations | references/ownership-memory.md |
| designing types, enums, traits, generics, conversions, numbers, closures, collections, naming, a public API | references/types-api.md |
| writing tokio/async code, tasks, channels, `select!`, shutdown, threads, atomics | references/async.md |
| touching files, config, SQLite/DBs, queues, serde formats, external processes | references/state-io.md |
| handling untrusted input, HTTP, paths, processes, `unsafe`, FFI, new dependencies | references/security.md |
| something is measured slow, or writing a known hot loop, release settings | references/perf.md |
| deciding what/how to test, fixing a bug, characterising old code, fakes vs mocks | references/tdd.md |
| creating crates/workspaces, modules, docs, tracing/logging, macros, CI | references/project.md |
| setting up or tightening clippy/rustc lints | references/lints.md |
| reviewing for bloat, auditing a repo, "what can we delete" | references/lean.md |
| rewriting a prototype or another language in Rust | references/porting.md |
| setting up SSOT/SOP files, closing out work, after a bug, improving this skill | references/process.md |
| publishing a project, contributors/agents, CONTRIBUTING/AGENTS.md/PR templates, CI, review routing, releases, governance | references/open-source.md |
| tracing a rule's origin or license, updating from upstream | references/sources.md |

Rule ids like `[err-context-chain]` in the guides are the upstream
rust-skills rule names, for traceability.

## Gate (done means all green)

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo nextest run --workspace        # or: cargo test --workspace
cargo test --workspace --doc
```
Plus, where set up: `cargo deny check`, MSRV build, `cargo miri test`
(unsafe crates), `rusty-audit ratchet .rusty/baseline.json`.
Then verify behaviour the way a user would (run the binary/server), not
only the unit tests.

## Measure first: scripts before judgment

`scripts/rusty-audit` (Python stdlib, no network) in this skill's folder:
- `signals [ROOT]` — production-code smell counts per kloc (unwrap,
  ignored results, clones, spawns, unbounded channels, sleeps, casts...).
- `clippy FILE.json` — per-lint counts from `cargo clippy --message-format=json`.
- `ledger [ROOT]` — every `// lean:` shortcut; flags ones with no trigger.
- `ratchet BASELINE [ROOT] [--update]` — fail if any count rose.
- `record [ROOT]` — append counts to `.rusty/metrics.jsonl` (trend).

Use the numbers to pick what to fix and which lints to deny
(references/lints.md); use review for what tools can't see.

## Reviewing

Separate passes, each with its own guide: correctness (errors, async,
state-io), security, lean (bloat), perf (only with measurements).
Findings: `path:line: <tag> <what>. <fix>.` worst first; cite the rule id
or pitfall; no hedging, no praise padding. End lean reviews with
`net: -N lines possible` or `Lean already. Ship.`

## Reporting

What changed (files, behaviour), the gate output, test counts, what was
verified live, and what is left or risky. Numbers you state are numbers
you ran. Say plainly when something was skipped or failed.

## Self-improvement

After a bug or repeated review finding: add the rule to the repo's
`PITFALLS.md` in the same change, and mechanise it (lint, test,
`rusty-audit` signal) when possible. Promote to this skill only what
generalises, with evidence; obey the size budgets (references/process.md).
