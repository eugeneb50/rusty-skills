# Process: single source of truth, SOPs, data, self-improvement

Load when: setting up a repo's working agreements, closing out a task,
after a bug or a review finding, or when improving this skill itself.

## Single source of truth (SSOT)

- One owner per fact: one implementation per concept, one store per piece
  of state, one doc per decision, one config value per setting. A second
  copy is a future inconsistency.
- Derived things are generated or tested against the source (README ↔
  crate docs via `include_str!`; schema ↔ types; CLI help ↔ docs).
- Replacing something deletes the old one in the same change (alpha
  projects: no shims; published APIs: deprecate once, remove on schedule).
- Prototypes are retired when the real thing lands; their behaviour lives
  on as recorded test cases (tdd.md).

## Repo files that make it stick (create only when needed)

| File | Holds | Rule |
|---|---|---|
| `DECISIONS.md` | table: # · decision · reason (+ date) | every non-obvious choice; revisit by editing the row |
| `PITFALLS.md` | each mistake made + the rule that prevents it | added **in the same change** as the fix |
| `STATUS.md` | each feature: Verified (run on real use) / Tested (fixtures) / Preview, + date last checked | claims match evidence |
| `MAP.md` + `HANDOFF.md` | multi-session work: units, claims, where it stands | update at each checkpoint |
| `CLAUDE.md`/`AGENTS.md` | the gate commands and pointers to the above | short; links, not copies |

## SOPs (standing procedures)

- **Before coding**: read the relevant guide(s) from SKILL.md's router;
  check `PITFALLS.md` for the area; look for prior art (std, existing deps,
  open-source projects — permissive licenses only, record the license).
- **Each change**: tdd.md loop → gate → commit test + code together.
- **Each bug**: failing test first; fix; add a `PITFALLS.md` row; ask
  "which lint/check would have caught it?" and add it if one exists.
- **Each review finding**: fix it or record why not; if the same finding
  appears twice, mechanise it (lint, test, script).
- **Done** = gate green + behaviour verified the way users use it + docs/
  STATUS updated + nothing replaced left behind.

## Data-driven quality

Measure, don't guess — and prefer cheap deterministic measurement
(scripts, compiler, lints) over judgment (LLM review):

- `rusty-audit signals` — production-code smell counts per kloc.
- `rusty-audit record` — append them to `.rusty/metrics.jsonl` per commit
  for a trend.
- `rusty-audit ratchet .rusty/baseline.json` in CI — a count may go down,
  never up; `--update` lowers the baseline.
- `rusty-audit clippy` — per-lint counts to choose lint levels (lints.md).
- Test strength: `cargo mutants` survivors; uncovered error branches
  (`cargo llvm-cov`).
- Bug classes: tag fix commits (`fix(area): ...`) and periodically count
  root causes (`git log --grep '^fix'`); the most frequent class gets a
  lint, a test pattern, or a guide section.

## Self-improvement loop (for any repo, and for this skill)

1. **Capture**: every bug/review finding → `PITFALLS.md` row with the rule.
2. **Mechanise**: a pitfall that recurs (or could be caught by a tool)
   becomes a lint, a test, or a `rusty-audit` signal. Prose is the
   fallback, not the goal.
3. **Measure**: track the counts; a rule that never fires and never
   prevents anything is a candidate for deletion (rules cost context).
4. **Promote** to this skill only what generalises beyond one repo,
   with evidence (a bug, a measurement, a cited source); keep project-
   specific facts in the project.
5. **Budget**: SKILL.md ≤ 200 lines, each guide ≤ 24 KB — enforced by
   `scripts/test_rusty_audit.py`. To add, cut or merge something.

## Changing this skill

- Edit the source repo, never an installed copy (installs are symlinks).
- A new rule needs: the situation (guide), the rule, why (evidence), and
  its check (lint/test/script) if one exists.
- Run `python3 -m unittest test_rusty_audit` in `scripts/` (structure,
  budgets, upstream coverage, audit behaviour).
- Record the change in `CHANGELOG.md` with the evidence that motivated it.
