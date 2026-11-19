# Lean code: write less, delete more

Load when: designing a change, reviewing for bloat ("what can we
delete?"), or auditing a repo. Lean means the least code that is
**correct**: never simplify away validation at trust boundaries, error
handling that prevents data loss, security, accessibility, or what the
user explicitly asked for.

## The ladder (stop at the first rung that holds)

1. **Does it need to exist?** Speculative need → don't build it; say so in
   one line. Fix verified bugs, not hypothetical ones.
2. **std does it?** Use it (`split_once`, `chunks`, `retain`, `entry`,
   `sort_by_key`, `dedup`, `OnceLock`, `std::thread::scope`, `Duration`).
3. **The platform/peer does it?** DB constraint over app code, the OS
   (atomic rename, file locks), the protocol's own feature.
4. **A dependency already in `Cargo.lock` does it?** Use it. New crate only
   when a few lines can't do it (security.md for vetting).
5. **One expression?** One expression.
6. Only then: the minimum code that works — plus its test (tdd.md).

Two options the same size → take the one correct on edge cases.

## Mark deliberate shortcuts

A known ceiling gets a comment naming it and the trigger to revisit:
```rust
// lean: one global lock; per-key locks when contention shows in a profile
```
`rusty-audit ledger` lists every marker and flags ones with no trigger
(those rot into "later means never").

## Slop patterns (review tags)

Universal (from debloatify's taxonomy, Rust-flavoured):

| Pattern | Severity | Fix |
|---|---|---|
| `dead-code` / `dead-file`: no callers, replaced implementation left behind | CRITICAL | delete (git remembers) |
| `factory-for-one`, builder for a 2-field struct | HIGH | construct directly |
| `trait-for-one`: trait/generic with one impl "for testing/flexibility" | HIGH | concrete type until a 2nd impl exists [anti-over-abstraction] |
| `defensive-theatre`: checks for states the types already rule out; `Option` that is never `None` | HIGH | delete; encode in types |
| `swallowed-error`: `let _ =`, `.ok();`, `unwrap_or_default()` hiding failure | HIGH | handle or propagate (errors.md) |
| `reimplemented-std`: hand-rolled split/trim/join/sort/dedup/retry-sleep | HIGH | name the std fn |
| `premature-config`: a const promoted to a setting/env var/param nobody sets | MEDIUM | inline the const |
| `premature-async`: `async fn` with nothing to await | MEDIUM | make it sync (`clippy::unused_async`) |
| `premature-generic`: `impl Into<String>`/`AsRef` everywhere, `<T>` with one use | MEDIUM | concrete types |
| `clone-to-silence-borrowck` | MEDIUM | restructure borrows (ownership-memory.md) |
| `unsolicited-scaffolding`: files, docs, CI, examples nobody asked for | HIGH | delete |
| `wrapper-that-delegates`: a fn/struct that only forwards | MEDIUM | call the target |
| `comment-slop`: comments restating code; history/ticket/name comments; apologies | MEDIUM | delete; keep only *why* |
| `logging-noise`: "entering fn", "success" | MEDIUM | log boundaries + errors |
| `verbose-naming`: `UserAuthServiceManager`, `process_and_validate_data` | MEDIUM | shortest unambiguous name |
| `version-suffix`: `foo_v2`, `new_handler`, `old_` | MEDIUM | replace the old one |
| `type-annotation-noise`: `let x: Vec<String> = ...` that inference gives; explicit elidable lifetimes | LOW | delete |
| `intermediate-variable`: `let r = f(); r` | LOW | return the expression |
| `emoji-in-code` | LOW | delete |

Rust-specific slop:
- `unwrap()`/`expect()` on recoverable errors; ignoring a `Result`. [anti-unwrap-abuse]
- `.clone()` / `.to_string()` / `.to_vec()` where a borrow works. [anti-clone-excessive]
- `Box<dyn Trait>` where `impl Trait` works. [anti-type-erasure]
- `Arc<Mutex<T>>` for data one task could own.
- `Rc<RefCell<T>>` graphs where indices into a `Vec` would do.
- Index loops over iterators (`for i in 0..v.len()`). [anti-index-over-iter]
- Micro-optimisation without a profile. [anti-premature-optimize]
- Macros where a function works. [macro-prefer-functions]
- Hand-written `impl Display`/`Error` boilerplate where `thiserror` is
  already a dependency.
- Back-compat shims, deprecated aliases and feature flags in code with no
  external users: delete the old path.

## Review output format

One line per finding, worst first:
`path:line: <tag> <what>. <replacement>.`
Tags: `delete:` (nothing replaces it) · `std:` (name the fn) ·
`native:` (platform/peer feature) · `yagni:` (single-use abstraction) ·
`shrink:` (same logic, fewer lines — show it).
End with `net: -<N> lines, -<M> deps possible.` or `Lean already. Ship.`

Lean review is about complexity only; correctness, security and
performance get their own pass. A single small test per non-trivial
branch is the minimum, never bloat.

## Repo audit (whole tree)

Hunt: unused deps (`cargo machete`/`cargo udeps`), dead code (rustc
`dead_code` is silenced by `pub` — check `pub` items with no external
users), single-impl traits, wrappers that delegate, config nobody sets,
duplicate implementations of one concept (single source of truth), files
exporting one tiny thing. Rank biggest cut first.
