# rusty-skills

A context-lean Rust engineering skill for coding agents: test-driven,
measured, lean, single source of truth. `SKILL.md` (~140 lines) is always
loaded; 14 guides in `references/` load only when the code needs them.
Covers all 265 [rust-skills](https://github.com/leonardomso/rust-skills)
rules plus methods from rust-anything, ponytail and debloatify
(see `references/sources.md`).

## Install

Clone once, then link it where your agent looks for skills, so the clone
stays the single source and `git pull` updates every agent:

```sh
git clone https://github.com/eugeneb50/rusty-skills ~/code/rusty-skills
ln -s ~/code/rusty-skills ~/.claude/skills/rusty-skills     # Claude Code
ln -s ~/code/rusty-skills ~/.agents/skills/rusty-skills     # agents that read ~/.agents/skills
```

## Measure a repo

```sh
scripts/rusty-audit signals path/to/repo
scripts/rusty-audit ratchet path/to/repo/.rusty/baseline.json path/to/repo --update
```

## Develop

```sh
cd scripts && python3 -m unittest test_rusty_audit
```
The tests enforce the size budgets, that every guide is routed from
SKILL.md, that all upstream rule ids are covered, and the audit
script's behaviour. Change process: `references/process.md`.
