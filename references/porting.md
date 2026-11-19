# Porting to Rust (from a prototype or another language)

Load when: rewriting a script/prototype (Python, JS, Go, Ruby, Java, C)
in Rust, or replacing one Rust implementation with another. Method from
rust-anything: the original is the source of truth until the port matches
it on every recorded case; then the original is retired.

## Method

1. **Plan, then stop for approval**: list units (folders/modules), port
   leaves first (units that import nothing unported), keep UI/editor code
   where it is, map each dependency to a crate — flag "no equivalent",
   never hand-roll silently.
2. **Record**: run the original on generated edge cases + its own test
   suite's calls + real-world inputs; save input → output/error as data
   (JSONL per function; trycmd files per CLI invocation; request/response
   files per HTTP route; a fresh copy of any state file per run).
3. **Port one unit**: plain Rust in its own module, `#![forbid(unsafe_code)]`;
   bindings/glue generated or kept separate.
4. **Diff**: replay every case against the port, through the same API
   callers use. N/N or it's not done. Fix the port, never the recording.
5. **Gate** (below), then **shadow** in production: run both, return the
   original's result, log mismatches; flip to the port when clean; keep a
   kill switch per unit until the end.
6. **Lift**: when every case passes with zero fallbacks, delete the
   original path, the bindings and the switches; the recorded cases become
   ordinary tests (`trycmd`/insta) run by `cargo test`.

## Semantic traps to record and check

- **Strings**: JS/Java/C# index UTF-16 code units, Python code points,
  Rust UTF-8 bytes. Lengths, slicing, `indexOf`, sorting by `<` all differ
  on emoji and non-BMP text; lone surrogates exist in JS strings.
- **Regex**: Rust `regex` has no lookaround/backreferences (`fancy-regex`
  does, without linear-time guarantees); `\w`, `\b`, `\d`, case-folding
  differ on non-ASCII (Turkish ı, Kelvin sign, final sigma, Arabic-Indic
  digits). Spell out ASCII classes when the original is ASCII-only.
- **Numbers**: JS numbers are f64; Python ints are unbounded and stay ints;
  signed division/modulo rounding differs; overflow edges; `-0`, `NaN`,
  `1e21` formatting differs between languages. Use `float_roundtrip` in
  serde_json; tolerance only for rounding, never formatting.
- **Ordering**: dict/object insertion order (→ `IndexMap`),
  `serde_json` `preserve_order` (and `shift_remove`, not `remove`).
- **Errors**: compare by kind/type, not message; a Rust panic never
  matches an original's error — return `Err` where it throws.
- **Nondeterminism**: record twice; values that differ become wildcards,
  order-only differences compared as sets, and each one reviewed — it may
  be a real concurrency difference.
- **Platform**: a recording proves behaviour on the machine that ran it.

## Gate for a ported unit

fmt · clippy `-D warnings` · tests · no `unsafe` without SAFETY · nothing
`todo!`/`unimplemented!` · every deliberate error of the original reached
by a recorded case · no `unwrap`/`expect`/`panic!` where the original
returns an error (impossible states: `// INFALLIBLE: <why>`) · port no more
than ~3× the original's lines (else use crates / fold repetition) · every
export present · every case matches · recording not stale (fingerprint of
the original unchanged).

## Speed claims

Benchmark original vs port **including the boundary**. A leaf function
called once per item across FFI often loses to a JIT; batch the loop
(items cross once, run on all cores) or port the caller too. Report the
verdict: ship, keep slower functions in the original, or port a bigger
unit.

## Across sessions/agents

Keep `MAP.md` (units + state: todo / claimed by X date / done with gate
results), claim a unit before starting, write `HANDOFF.md` at each
checkpoint, record decisions as ADR rows (process.md). Units in one wave
can be ported in parallel by separate agents, each owning its files.
