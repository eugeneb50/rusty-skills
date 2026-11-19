# Project structure, docs, observability and macros

Load when: creating a crate/workspace, organising modules, writing docs,
setting up logging/tracing, CI, or writing macros.

## Layout

- Small projects stay flat; split modules by **feature** (`orders/`,
  `billing/`), not by kind (`models/`, `utils/`). [proj-flat-small] [proj-mod-by-feature]
- `main.rs` parses args and calls `lib.rs`; logic lives in the library so
  it is testable. Multiple binaries in `src/bin/`. [proj-lib-main-split] [proj-bin-dir]
- Multi-file modules: `foo.rs` + `foo/` (modern) or `foo/mod.rs` — pick
  one per project. [proj-mod-rs-dir]
- Visibility as narrow as works: private → `pub(super)` → `pub(crate)` →
  `pub`. rustc `unreachable_pub` finds leaks. [proj-pub-crate-internal] [proj-pub-super-parent]
- Curate the public API with `pub use` re-exports; a `prelude` only for
  crates whose users import many items. [proj-pub-use-reexport] [proj-prelude-module]
- Workspaces when crates have separate consumers or build targets;
  `[workspace.dependencies]` + `dep.workspace = true` for one version per
  dep; `[workspace.lints]` once. [proj-workspace-large] [proj-workspace-deps] [lint-workspace-lints]
- Features are additive (enabling one never removes behaviour); test
  `--no-default-features` and `--all-features`. [proj-feature-additive]
- Declare `rust-version` (MSRV) and test it in CI; pin the toolchain in
  `rust-toolchain.toml` for reproducible builds. [proj-msrv-declare]
- `build.rs`: minimal, deterministic, idempotent, with
  `cargo:rerun-if-changed`; no network. [proj-build-rs-minimal]

## Documentation

- `///` on every public item; `//!` for crate/module overview;
  `#![warn(missing_docs)]` in libraries. [doc-all-public] [doc-module-inner] [lint-missing-docs]
- Sections: `# Examples` (runnable), `# Errors`, `# Panics`, `# Safety`. [doc-examples-section] [doc-errors-section] [doc-panics-section] [doc-safety-section]
- Examples use `?`, not `unwrap()`; hide setup lines with `# `. [doc-question-mark] [doc-hidden-setup]
- Intra-doc links: [`Type`], [`Self::method`]; `cargo doc` warns on
  broken ones (`rustdoc::broken_intra_doc_links`). [doc-intra-links] [doc-link-types]
- Comments explain **why**, never what; no history ("added in sprint 4",
  "per Bob"), no apologies — that's the commit message's job (lean.md).
- One README: `#![doc = include_str!("../README.md")]` so crate docs and
  README can't diverge. [doc-crate-readme]
- Published crates: `description`, `license`, `repository`, `readme`,
  `keywords`, `categories`, `rust-version` in Cargo.toml. [doc-cargo-metadata]

## Observability

- `tracing`, not `println!`/bare `log`; libraries emit through the facade
  and never install a subscriber — the binary does. [obs-tracing-over-log] [obs-library-facade]
- Structured fields: `info!(user_id, elapsed_ms, "request done")`, not
  values interpolated into the message. [obs-structured-fields]
- Spans per request/task (`#[instrument]`), async.md for awaits. [obs-instrument-spans]
- Levels mean something: `error` = someone must act; `warn` = degraded;
  `info` = lifecycle; `debug`/`trace` = diagnostics. Filter with
  `EnvFilter`/`RUST_LOG`. [obs-levels-filter]
- Log at boundaries and on errors (once, with chain); no "entering
  function" noise. [obs-error-chain]
- Never log secrets/PII. [obs-no-sensitive-data]
- `clippy::print_stdout`/`print_stderr`/`dbg_macro` in libraries and
  servers; stdout may be a protocol channel (MCP, LSP, pipes).

## Macros

- A function or generic first; a macro only for what they can't do
  (variadics, new syntax, compile-time codegen). [macro-prefer-functions]
- `macro_rules!`: precise fragment specifiers (`expr`, `ident`, `ty`) over
  `tt`; `$crate::` paths; hygiene keeps locals private. [macro-fragment-specifiers] [macro-rules-hygiene]
- Export with `#[macro_export]`; helpers behind
  `#[doc(hidden)] pub mod __private`. [macro-export-crate-path] [macro-private-helpers]
- Proc macros in a separate `proc-macro = true` crate, re-exported from
  the main crate; built with `syn` + `quote` + `proc-macro2`; errors as
  spanned `compile_error!`, never panics. [macro-proc-two-crate] [macro-proc-syn-quote] [macro-proc-error-spans]

## CI pipeline (the gate, mechanised)

`cargo fmt --check` → `cargo clippy --all-targets --all-features -- -D warnings`
→ `cargo nextest run` (or `cargo test`) → `cargo test --doc` →
`cargo deny check` → MSRV build → (unsafe crates) `miri` →
`rusty-audit ratchet`. [lint-rustfmt-check]
