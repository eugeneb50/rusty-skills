# Performance

Load when: something is measured to be slow, or you are writing a known
hot loop. Rule zero: **no optimisation without a measurement before and
after**. Readable code first; most code is not hot. [perf-profile-first] [anti-premature-optimize]

## Measure

1. Reproduce with a real workload (not a toy input).
2. Profile: `cargo flamegraph`, `perf record -g`, `samply`; for
   allocations `dhat`/`heaptrack`; for async `tokio-console`.
3. Benchmark the hot function: `criterion` (or `divan`), inputs through
   `std::hint::black_box` so the compiler can't delete the work. [test-criterion-bench] [perf-black-box-bench]
4. Report numbers honestly: hardware, core count, quiet machine, two runs,
   median, and the slow cases too. A number in a doc is something you ran.
5. Keep the benchmark; re-run it in the PR that claims a speed-up.

## The big wins, in the order they usually pay

1. **Algorithm and data structure** (O(n²) → O(n log n), a set instead of
   a scan, an index built once).
2. **Do less**: cache a computed value, avoid repeated parsing, batch I/O.
3. **Move the loop, not the leaf**: crossing a boundary (FFI, IPC, network,
   lock, allocation) per item costs more than the item; pass all items
   once and loop on the far side. Prepare items once (lowercase, masks,
   lookup tables), then query many times.
4. **Allocation**: reuse buffers, `with_capacity`, avoid `format!` in loops
   (ownership-memory.md). Multithreaded allocation-heavy code: try
   `mimalloc` — the system allocator can serialise threads.
5. **Parallelism**: rayon over independent items; measure scaling.
6. **Micro**: bounds checks, inlining, SIMD — last.

## Iterators

- Iterators over index loops: clearer and lets LLVM drop bounds checks. [perf-iter-over-index] [opt-bounds-check]
- Stay lazy; `collect` once at the end, not into intermediate `Vec`s. [perf-iter-lazy] [perf-collect-once] [anti-collect-intermediate]
- `extend` for batch insertion; `Vec::extend_from_slice` for copies. [perf-extend-batch]
- `collect_into` (nightly) / `extend` into an existing container to reuse it. [perf-collect-into]
- `chain` in a very hot loop can block vectorisation — split into two
  loops if a profile says so. [perf-chain-avoid]

## Hashing

- Default SipHash is DoS-resistant. For trusted keys in hot maps:
  `rustc-hash` (`FxHashMap`) or `ahash`/`foldhash`. [perf-ahash]

## Compiler and build settings (release)

```toml
[profile.release]
lto = "fat"          # or "thin" for faster builds [opt-lto-release]
codegen-units = 1    # [opt-codegen-units]
panic = "abort"      # smaller/faster, if nothing catches unwinds
# debug = "line-tables-only"  # profile release builds with symbols
```
[perf-release-profile]

- PGO (`cargo pgo`) for 10–20% on branchy code with a representative
  workload; BOLT after it. [opt-pgo-profile]
- `-C target-cpu=native` only when the binary runs on the build machine
  (it won't run on older CPUs). [opt-target-cpu]
- `#[inline]` on small cross-crate hot functions (generic fns are already
  inlinable); `#[inline(always)]` only with a benchmark; `#[cold]` +
  `#[inline(never)]` on error/slow paths to keep hot code tight. [opt-inline-small] [opt-inline-always-rare] [opt-inline-never-cold] [opt-cold-unlikely]
- Branch hints: structure code so the likely path is the fall-through;
  `likely`/`unlikely` intrinsics are nightly. [opt-likely-hint]
- Portable SIMD (`std::simd`, nightly) or `wide`/`pulp` on stable; check
  the autovectoriser first (`cargo asm`). [opt-simd-portable]
- Cache-friendly layout: struct-of-arrays for scans over one field,
  contiguous `Vec` over pointer-chasing, hot fields together. [opt-cache-friendly]
