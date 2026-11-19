# Lint profile: mechanise the rules

Load when: setting up a crate/workspace, tightening quality, or a rule
keeps being broken in review. A lint that fails the build beats a page of
advice an agent may skip. Adopt by **measuring first**, then ratcheting.

## Adoption procedure (data-driven)

1. Run the candidate lints as warnings and count hits per lint:
   ```sh
   cargo clippy --all-targets --message-format=json -- -W clippy::expect_used \
     -W clippy::indexing_slicing ... > clippy.json
   rusty-audit clippy clippy.json
   ```
2. **0 hits** → `deny` now (free protection).
   **Few hits** → fix them in one PR, then `deny`.
   **Many hits** → `warn`, fix per touched file, track the count with
   `rusty-audit` and lower it; `deny` when it reaches zero.
3. Every `#[allow]`/`#[expect]` carries `reason = "..."`
   (`clippy::allow_attributes_without_reason`); prefer `#[expect]`
   (it errors when the lint no longer fires, so stale allows die).

Example measurement (one 31k-line tokio workspace, production code):
`indexing_slicing` 73, `let_underscore_must_use` 25, `print_stdout` 16,
`needless_pass_by_value` 8, `clone_on_ref_ptr` 8, `expect_used` 7,
`cast_possible_truncation` 5, `string_slice` 3 — and 0 for `panic`,
`await_holding_lock`, `unused_async`, `todo`, `dbg_macro`,
`undocumented_unsafe_blocks`. The zeros were denied immediately; the
`string_slice` sites were real panic risks on non-ASCII text.

## Recommended `[workspace.lints]`

```toml
[workspace.lints.rust]
unsafe_code = "forbid"              # or "deny" + scoped allow in one module
unsafe_op_in_unsafe_fn = "deny"
unused_must_use = "deny"
unexpected_cfgs = { level = "warn", check-cfg = [] }   # [lint-cfg-check]
unreachable_pub = "warn"
missing_docs = "warn"               # libraries

[workspace.lints.clippy]
# groups [lint-deny-correctness] [lint-warn-suspicious] [lint-warn-style] [lint-warn-complexity] [lint-warn-perf]
correctness = { level = "deny", priority = -1 }
suspicious  = { level = "warn", priority = -1 }
style       = { level = "warn", priority = -1 }
complexity  = { level = "warn", priority = -1 }
perf        = { level = "warn", priority = -1 }
# pedantic, selectively [lint-pedantic-selective]
needless_pass_by_value = "warn"
cast_possible_truncation = "warn"
cast_sign_loss = "warn"
cast_possible_wrap = "warn"
manual_let_else = "warn"
missing_errors_doc = "warn"         # libraries
missing_panics_doc = "warn"         # libraries
unused_async = "warn"
# restriction, chosen one by one
unwrap_used = "deny"
expect_used = "warn"                # deny for servers/daemons
panic = "warn"
indexing_slicing = "warn"
string_slice = "deny"
let_underscore_must_use = "warn"
let_underscore_future = "deny"
unwrap_in_result = "warn"
map_err_ignore = "warn"
clone_on_ref_ptr = "warn"
undocumented_unsafe_blocks = "deny"
multiple_unsafe_ops_per_block = "deny"
allow_attributes_without_reason = "warn"
todo = "warn"
dbg_macro = "deny"
print_stdout = "warn"               # libraries/servers
float_cmp = "warn"
# nursery, selectively [lint-clippy-nursery-selected]
redundant_clone = "warn"
significant_drop_tightening = "warn"
future_not_send = "warn"            # multithreaded async crates
```
Each crate: `[lints] workspace = true`. Every lint name and `clippy.toml`
key here was checked against clippy 0.1.96 (unknown names warn/error).

`clippy.toml`:
```toml
allow-unwrap-in-tests = true
allow-expect-in-tests = true
allow-indexing-slicing-in-tests = true
allow-panic-in-tests = true
allow-print-in-tests = true
```

- `clippy::cargo` group for published crates (metadata, duplicate deps). [lint-cargo-metadata]
- Don't enable whole `pedantic`/`nursery`/`restriction` groups:
  restriction lints contradict each other; pedantic has noisy ones
  (`module_name_repetitions`, `must_use_candidate`). Pick by measured value.
- Formatting is rustfmt's job, never review's: `cargo fmt --check` in CI. [lint-rustfmt-check]
