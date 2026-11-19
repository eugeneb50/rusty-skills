# Sources, licenses and what was condensed

Load when: tracing a rule to its origin, checking licenses, or updating
from upstream. All sources are MIT or MIT OR Apache-2.0; this skill is MIT.

| Source | Version read | License | Taken |
|---|---|---|---|
| [rust-skills](https://github.com/leonardomso/rust-skills) (Leonardo Maldonado) | fd2a861, 2026-06-14; 265 rules, ~894 KB | MIT | every rule, condensed to one line + check; ids kept in `[brackets]` |
| [rust-anything](https://github.com/erkamyaman/rust-anything) (Erkam Yaman) | 98adbe2, 2026-11-19; v1.5.1 | MIT | record → diff → gate method, semantic traps, stall rule, known-diffs, INFALLIBLE marker, error-path coverage, fingerprinted recordings, DECISIONS/STATUS/PITFALLS/MAP/HANDOFF practices, measured-claims rule |
| [ponytail](https://github.com/DietrichGebert/ponytail) (DietrichGebert) | 45f7d2f, 2026-06-17 | MIT | the YAGNI ladder, "never simplify away" list, shortcut markers + debt ledger (here `// lean:`), review tags and `net: -N lines` scoring, one-check-per-branch minimum |
| [debloatify](https://github.com/jetmirrama/debloatify) (Jetmir Rama) | c230047, 2026-05-19 | MIT | slop taxonomy (factory-for-one, defensive theatre, premature config/async, comment/archaeology slop, dead files...), Rust slop, severity scale, deterministic linter as CI companion to judgment |
| [zeroclaw](https://github.com/zeroclaw-labs/zeroclaw) (ZeroClaw Labs) | 6877da56d, 2026-11-10 | MIT OR Apache-2.0 | AGENTS.md contract + architecture map, PR evidence template, gates vs standards, tested CI gates, ratchets, risk labels by path/added lines, untrusted-input doctrine, eval rules, superseding/stacking, measured self-assessment (open-source.md) |

Not adopted, with reason:
- Personas and voice (debloatify's reviewer character, ponytail's
  intensity levels): style, not quality; costs context.
- rust-skills' per-rule Bad/Good essays: the compiler, clippy and one-line
  rules carry the same signal at ~7% of the size (63 KB vs 931 KB); the upstream repo keeps
  the long form if an agent needs an example.
- rust-anything's codegen/bridge internals: tool-specific.
- ponytail's benchmark numbers (80–94% less code, Claude models, its own
  5 tasks): cited as motivation, not re-measured here.

Additions not in any source (general Rust practice): task lifecycle with
TaskTracker/CancellationToken, subscribe-then-snapshot, `tokio::fs`
flush, atomic file writes, SQLite `BEGIN IMMEDIATE`, leases/dead-letter,
trust-boundary list, supply chain (cargo-deny/audit), mutation testing,
coverage of error branches, lint adoption by measurement, ratchet, the
self-improvement loop, string byte-slicing panics.

Facts cited in open-source.md about other projects (Rust bors/crater,
SQLite testing, Linux, Kubernetes OWNERS/ladder, Apache, Python,
PostgreSQL, CHAOSS, OpenSSF Scorecard) come from their public docs:
sqlite.org/testing.html, rustc-dev-guide (crater), kubernetes.dev OWNERS
guide, chaoss.community, scorecard.dev.

## Condensation data

- Upstream rule text: ~894 KB (rust-skills rules) + 37 KB index.
- This skill: SKILL.md (always loaded) + 14 guides loaded on demand; the
  test suite enforces SKILL.md ≤ 200 lines / 14 KB and each guide ≤ 24 KB,
  and that every one of the 265 upstream ids appears in a guide.
- Typical task loads SKILL.md + 1–3 guides.

## Updating from upstream

```sh
cd <rust-skills checkout> && git pull
grep -E '^- \[`' SKILL.md | sed -E 's/^- \[`([^`]+)`.*/\1/' > <this>/scripts/upstream-ids.txt
cd <this>/scripts && python3 -m unittest test_rusty_audit   # lists new uncovered ids
```
Add each new id to the right guide as one line (rule, why, check), or
note here why it was rejected.
