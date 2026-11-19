# Security, unsafe and supply chain

Load when: handling untrusted input (network, files, CLI args, env,
other processes, LLM output), spawning processes, serving HTTP, writing
`unsafe`/FFI, or adding dependencies. These are never "simplified away"
(lean.md).

## Trust boundaries

- List the boundaries: who can send this input? Parse it into validated
  types right there (types-api.md: parse, don't validate).
- **Data is never code**: no shell strings from data (`Command::new(bin).arg(x)`,
  never `sh -c format!(...)`); no data-chosen binary or path without an
  allow list; templated values are looked up by name in a user-owned map,
  not pasted into commands.
- **Paths**: reject `..`, absolute paths, separators and NUL in names;
  after joining, canonicalise and verify the prefix. Distinct names must
  never alias one file.
- **HTTP servers**: bind loopback unless told otherwise (warn when not);
  check `Origin`/`Host` on state-changing requests (CSRF / DNS rebinding);
  size-limit bodies; timeouts on everything.
- **Outbound requests** to user-given URLs: block private/link-local
  ranges after DNS resolution (SSRF), and remember a proxy resolves names
  itself — re-check there.
- Secrets: from env or a secret store, never logged, never in errors,
  `Debug` impls redact them (`secrecy` crate or a manual impl). [obs-no-sensitive-data]
- Limits on everything an attacker controls: input size, recursion depth,
  collection length, regex complexity (the `regex` crate is linear-time;
  `fancy-regex` is not).
- `HashMap`'s default SipHash resists HashDoS; keep it for attacker
  keys (perf.md: faster hashers only for trusted keys).

## unsafe

- Default `#![forbid(unsafe_code)]` per crate; isolate necessary unsafe in
  one small module.
- Every `unsafe` block has a `// SAFETY:` comment proving its
  preconditions; every `unsafe fn` has a `# Safety` doc section
  (`clippy::undocumented_unsafe_blocks`, `missing_safety_doc`). [unsafe-safety-comment] [doc-safety-section] [lint-unsafe-doc]
- Smallest possible block: only the operation that needs it; one unsafe op
  per block (`clippy::multiple_unsafe_ops_per_block`); rustc
  `unsafe_op_in_unsafe_fn`. [unsafe-minimize-scope]
- Uninitialised memory via `MaybeUninit<T>`; never `mem::uninitialized`
  or `mem::zeroed` for types with invalid bit patterns. [unsafe-maybeuninit]
- Manual `Send`/`Sync` impls document the invariant; prefer auto traits. [unsafe-send-sync-manual]
- Edition 2024: `unsafe extern "C" { safe fn ...; }`,
  `#[unsafe(no_mangle)]`, `#[unsafe(export_name)]`, `#[unsafe(link_section)]`;
  `std::env::set_var` is unsafe (call it before spawning threads). [unsafe-extern-block] [unsafe-no-mangle-unsafe]
- `cargo +nightly miri test` in CI for crates with unsafe. [unsafe-miri-ci]
- FFI panics must not unwind across the boundary: `catch_unwind` at the
  edge or `panic = "abort"`.

## Supply chain (run in CI)

- `cargo deny check` — licenses (allow list, e.g. MIT/Apache-2.0/BSD/ISC/
  Zlib/Unicode), advisories, banned and duplicate crates, sources.
- `cargo audit` (RustSec advisories) if not using cargo-deny.
- Commit `Cargo.lock` for binaries; review new deps: maintenance, license,
  transitive count (`cargo tree -e normal`), `unsafe` use (`cargo geiger`).
- Before adding a dependency: does std, or a crate already in the tree, do
  it in a few lines? (lean.md ladder)
- Two crates that each `links = "x"` (e.g. two `libsqlite3-sys`
  versions) cannot be in one build — check before adopting a crate that
  pins an old version.
- `build.rs` and proc macros run arbitrary code at build time: minimal,
  deterministic, no network (project.md). [proj-build-rs-minimal]
