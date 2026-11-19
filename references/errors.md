# Errors, panics and results

Load when: writing fallible code, error types, `?` chains, or reviewing
`unwrap`/`expect`/`let _ =`/`.ok()`. Tags in `[brackets]` are upstream
rust-skills rule ids (see sources.md).

## The contract

A failure is either **expected** (bad input, missing file, network, peer
gone) → `Result`, or a **bug** (a broken invariant you own) → panic. Never
the other way round. [err-result-over-panic] [type-result-fallible] [anti-panic-expected]

| Situation | Do |
|---|---|
| Library crate | One `thiserror` enum per failure domain; variants callers can match. [err-thiserror-lib] [err-custom-type] |
| Binary / app glue | `anyhow::Result` + `.context("what we were doing")`. [err-anyhow-app] [err-context-chain] |
| Propagate | `?`; implement `From<Inner>` (or `#[from]`) so `?` converts. [err-question-mark] [err-from-impl] |
| Wrap without losing cause | `#[source]` / `#[from]`; never `format!("{e}")` into a new string error. [err-source-chain] |
| Message text | lowercase, no trailing period, says what failed: `"read config {path}"`. [err-lowercase-msg] |
| Public fallible fn | `# Errors` doc section listing when it fails. [err-doc-errors] [doc-errors-section] |
| Function that can panic | `# Panics` doc section. [doc-panics-section] |

## Panics: allowed only for bugs

- `unwrap()` is banned outside tests. Deny `clippy::unwrap_used`, allow in
  tests via `clippy.toml: allow-unwrap-in-tests = true`. [err-no-unwrap-prod] [anti-unwrap-abuse]
- `expect("invariant: why this cannot fail")` only for states your own code
  guarantees. The message states the invariant, not the hope. [err-expect-bugs-only] [anti-expect-lazy]
- Stricter mode (servers, long-running daemons, anything that must not
  abort): also deny `clippy::expect_used`, `clippy::panic`,
  `clippy::indexing_slicing`, `clippy::string_slice`; mark a truly
  impossible state with `// INFALLIBLE: <why>` + a scoped
  `#[expect(clippy::expect_used, reason = "...")]`.
- A panic in a function that returns `Result` is a smell:
  `clippy::unwrap_in_result`.
- Indexing `v[i]` and `&s[a..b]` panic. Prefer `get(i)`, iterators,
  `split_once`, `char_indices`. **Byte-slicing a `&str` at a computed offset
  panics on non-ASCII text** (multi-byte char boundary). [anti-index-over-iter]
- `#[should_panic(expected = "...")]` tests prove invariant panics. [test-should-panic]
- Proc macros never panic: emit spanned `compile_error!` via `syn::Error`. [macro-proc-error-spans]

## Silently dropped errors (the most common real bug class)

- `let _ = fallible();` and `.ok();` discard failures. Each needs a reason
  next to it, or handling. Lints: `let_underscore_must_use`,
  `let_underscore_future` (a dropped future never runs), rustc
  `unused_must_use` (on by default — never `allow` it). [anti-empty-catch]
- Acceptable drops, with a comment: best-effort cleanup (`remove_file` of a
  temp), sending on a channel whose receivers may be gone, terminal restore
  on exit. Not acceptable: writes, flushes, persistence, process spawns
  whose failure changes behaviour.
- `map_err(|_| ...)` erases the cause: `clippy::map_err_ignore`.
- Mark your own results/builders `#[must_use]` when ignoring them is a bug. [api-must-use] [api-builder-must-use]
- **Detect failures where the other side actually reports them.** An
  external protocol's error flag/key/exit code is a contract: assert it in a
  test against a real or recorded response, so a renamed field can't turn
  every failure into "success".

## Logging errors

- Log an error **once**, at the boundary that handles it, with the full
  chain (`{:#}` for anyhow, or iterate `source()`). Lower layers return,
  they don't log-and-return. [obs-error-chain]
- Return errors to callers; don't print them from library code.

## Tests for error paths

Every deliberate failure branch (`return Err`, `bail!`, `?` on a validated
input) gets a test that reaches it. Compare error **kinds/variants**
(`matches!(e, Error::NotFound { .. })`), not message strings — wording is
not a contract (unless it is: a CLI's stderr that scripts parse).
See tdd.md.
