# Learnings - h3-prompt-linter

## Auto-learned (ALH)

_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. **Only `Accepted rules` are active.** Detail/verdicts are in `RUN-LOG.md` and the log; a rule is mandatory only after it is mirrored into `SKILL.md` / `GLOBAL-RULES.md`._

### Accepted rules (active)

- [E268] ALH:E268 — E268 systemic prompt fix: jerk shots get MOTION_MODE, a frozen-pose ambience instead of continues-evenly, len(beats) discrete wrist/finger snap timecodes, locked framing and blotchy blood; linter hard-FAILs wrist/finger snaps mixed with even/slow/smooth drift.
- [E299] ALH:E299 — E299 gate hardening: validate_prompt and lint_h3.ps1 now hard-FAIL composited/compositing-stage pipeline metadata in prompt_visible; prompt_consistency_audit now FAILs a stale N+N pair inside phone_ins instead of unconditional PASS. Re-audit: FAIL 3 / CHUA CHOT 7 / PASS 35 (was FAIL 6 / PASS 32); fixed G02 props, G03 character, G04 light+layout. Remaining FAILs are sightline/camera-height, awaiting user seat/elevation decision.
