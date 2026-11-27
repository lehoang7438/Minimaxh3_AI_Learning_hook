# Learnings - global

## Auto-learned (ALH)

_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. **Only `Accepted rules` are active.** Detail/verdicts are in `RUN-LOG.md` and the log; a rule is mandatory only after it is mirrored into `SKILL.md` / `GLOBAL-RULES.md`._

### Accepted rules (active)

- [E234] ALH:E234 — Every FAIL or blocker in any phase must be traced end to end and logged in ALH before asking the user; ask only with evidence or at the retry cap.
- [E302] ALH:E302 — E302 skill sharing: three copies existed and were NOT merged - project .opencode/skills (active, newest, has LEARNINGS.md), global ~/.config/opencode/skills (stale 11/23-11/24, 8/9 differ, no LEARNINGS), and the repo (no skills, only PLAYBOOK + flattened audit-inputs snapshots). Shareable rule: mirror the whole project skills tree into repo skills/ (exclude __pycache__/*.pyc) and into global config; repo stays a one-way snapshot, never edit there. Local ALH log remains source of truth; accepted rules are not mirrored into SKILL.md until user approves the condensed draft.
