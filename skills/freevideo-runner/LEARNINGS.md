# Learnings - freevideo-runner

## Auto-learned (ALH)

_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. **Only `Accepted rules` are active.** Detail/verdicts are in `RUN-LOG.md` and the log; a rule is mandatory only after it is mirrored into `SKILL.md` / `GLOBAL-RULES.md`._

### Accepted rules (active)

- [E301] ALH:E301 — E301 cleanup scope: delete only install-time junk in the MiniMax H3/FreeVideo install - old test-runs, temp FreeVideo-main clone+zip, one-off MinGit installer zip, empty uv temp (5 items, 2,578,665,597 bytes = 2.40 GiB). KEEP CHUA CHOT the 21.87 GiB prepared int8-convrot model cache (active reuse path), torch-wheels + uv-cache install caches (referenced by bootstrap.py for repair), kernel/input/continuations caches, setup-runs (render-ready.ps1/finish-setup.ps1 pick newest), and the stale Downloads\FreeVideo-main (four project scripts still reference it). Engine/models/envs/ComfyUI/agent-token untouched; no GPU work.
