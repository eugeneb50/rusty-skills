# Test-driven development and verification

Load when: starting any change, fixing a bug, refactoring, porting, or
deciding what to test. "Done" means a test proves it — not that it compiles.

## The loop (red → green → lean)

1. **Red**: write the smallest test that states the behaviour or reproduces
   the bug. Run it; it must fail **for the right reason** (read the
   failure). A bug fix without a failing-first test is unproven.
2. **Green**: the least code that passes. No extra branches "while here".
3. **Lean**: refactor with the test green — delete duplication, shrink
   (lean.md). Run the full gate (SKILL.md).
4. Commit the test with the code.

Rules that keep the loop honest:
- **Fix the code, never the test** to make it pass. Changing an expected
  value needs a reason (the old expectation was wrong) stated in the
  commit; an intended behaviour change is recorded as such.
- **Stall rule**: three edits in a row that don't increase passing cases →
  stop, list what still fails, ask or rethink. Thrashing is not progress.
- **Characterise before changing** untested code: first pin what it does
  today (snapshot/golden tests), then change it.

## What to test, by layer

| Layer | Where | Use for |
|---|---|---|
| Unit | `#[cfg(test)] mod tests { use super::*; }` in the module [test-cfg-test-module] [test-use-super] | pure logic, every branch, error paths |
| Integration | `tests/*.rs` (public API only) [test-integration-dir] | crate behaviour as users see it |
| Doc tests | `///` examples, run by `cargo test` [test-doctest-examples] [doc-examples-section] | API examples that can't rot |
| End to end | spawn the binary / server against temp dirs and fake peers | wiring, config, CLI contract |
| Property | `proptest`: invariants over generated inputs (round-trip, idempotence, ordering) [test-proptest-properties] | parsers, encoders, math |
| Snapshot | `insta` for large/structured output; review diffs with `cargo insta review` [test-snapshot-testing] | rendering, reports, JSON |
| Concurrency | `loom` (atomics/locks), deterministic interleavings with fakes [test-loom-concurrency] | races, lost events |
| Fuzz | `cargo fuzz` on anything that parses untrusted bytes | crashes, panics, hangs |
| Bench | `criterion` (perf.md) | speed claims |

## Writing good tests

- Name says the behaviour: `expired_lease_is_requeued`, not `test_reap`. [test-descriptive-names]
- Arrange / act / assert, visibly separated; one behaviour per test. [test-arrange-act-assert]
- Tests return `Result<(), Box<dyn Error>>` and use `?`; `unwrap` is fine
  in tests (clippy `allow-unwrap-in-tests`).
- Every deliberate error branch has a test that reaches it; assert the
  error **kind**, not its wording.
- Deterministic: no wall-clock sleeps (`tokio::time::pause`), seeded
  randomness, temp dirs (`tempfile`) per test, no shared global state, no
  network. Run twice; anything that differs (ids, timestamps) is
  normalised or a bug. [test-tokio-async]
- Cleanup via RAII guards (`TempDir`, a `Drop` that kills the child). [test-fixture-raii]
- Panics as a contract: `#[should_panic(expected = "...")]`. [test-should-panic]

## Test doubles: fakes over mocks

- Prefer a **fake** (a small working implementation: in-memory store, a
  fake server/CLI that speaks the real protocol) over mock expectations;
  fakes test behaviour, mocks test call sequences and break on refactors.
- Seam = a trait only when a test needs a double for an external system
  (network, clock, process). Don't add traits for internal code. [test-mock-traits]
- `mockall` when a fake is impractical and you need call verification. [test-mockall-mocking]
- Record real responses of external peers once (fixtures) and replay them;
  re-record when the peer's version changes.

## Characterisation / golden testing (prototype → Rust, refactors, ports)

- Turn the reference implementation's behaviour into **data**: cases of
  input → expected output (JSONL, trycmd files, insta snapshots).
- The reference must pass 100% of its own cases; then the new code runs
  the same file. The case file outlives the prototype — it becomes the
  single spec. (porting.md has the full method.)
- Record each case twice; fields that differ become wildcards.
- Store a fingerprint of the reference that produced the cases; fail when
  it changes without re-recording.
- An intended difference goes in a `known-diffs` list with a reason,
  approved by a human; the gate fails when the difference disappears.

## Coverage and mutation (data on test quality)

- `cargo llvm-cov` for line/branch coverage — look at **uncovered error
  branches**, not the percentage.
- `cargo mutants` to find code whose tests would still pass if it were
  wrong: the real measure of test strength. Run on changed files in CI.
- `cargo nextest run` for faster, isolated runs and flaky-test retries
  (a retry that passes is still a bug report).
