# Learnings - global

## Auto-learned (ALH)

_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. **Only `Accepted rules` are active.** Detail/verdicts are in `RUN-LOG.md` and the log; a rule is mandatory only after it is mirrored into `SKILL.md` / `GLOBAL-RULES.md`._

### Accepted rules (active)

- [E234] ALH:E234 — Every FAIL or blocker in any phase must be traced end to end and logged in ALH before asking the user; ask only with evidence or at the retry cap.
- [E302] ALH:E302 — E302 skill sharing: three copies existed and were NOT merged - project .opencode/skills (active, newest, has LEARNINGS.md), global ~/.config/opencode/skills (stale 11/23-11/24, 8/9 differ, no LEARNINGS), and the repo (no skills, only PLAYBOOK + flattened audit-inputs snapshots). Shareable rule: mirror the whole project skills tree into repo skills/ (exclude __pycache__/*.pyc) and into global config; repo stays a one-way snapshot, never edit there. Local ALH log remains source of truth; accepted rules are not mirrored into SKILL.md until user approves the condensed draft.
- [E303] ALH:E303 — E303 bundle layout: repo is a one-way snapshot of local truth, structured as skills/, alh/, project-tools/, audit-inputs/, docs/, tools/push_learning_bundle.ps1 plus README/CONTRIBUTING/MANIFEST. Exclude __pycache__/*.pyc; never edit repo dirs directly; other AIs read accepted+mirrored rules only, keep proposed/supersedes/status_by discipline; global ~/.config/opencode/skills stays stale and untouched.
