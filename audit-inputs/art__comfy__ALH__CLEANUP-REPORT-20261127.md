# Cleanup report — 2026-11-27

Status: **completed conservatively — 0 files/directories deleted by the subagent, 0 bytes reclaimed, 0 errors.**
Parent-session addendum: after the scan, the parent removed exactly 4 `__pycache__` directories (`art/comfy/ALH`, `art/comfy/scripts`, `art/tests`, `learning_system`) as an explicitly allowed, regenerable cleanup. No other candidate below was touched.
No GPU work, no pipeline commands, no prompt/context/spec/workflow edits, no git writes.

## Scan scope (light pass)

- Location A: `C:\Users\Admin\Documents\Default Project`
  - Top-level entries enumerated; one targeted file pass over `art/` + root files; targeted shallow pass (`-Depth 3`) over `.hf-tts/`, `.venv-tts/`, `learning_system/`, `studio/`.
  - **Not scanned at all:** `out/`, `tools/`, `.opencode/`, `prompts/` (protected/excluded).
  - No file contents read, no hashing, no large-file handling.
- Location B: `C:\Users\Admin\AppData\Local\Temp\opencode\Minimaxh3_AI_Learning_hook`
  - `git status --short` only. Output was empty → clean tree, no untracked junk. No `.git/`, `PLAYBOOK.md`, `audit-inputs/`, or tracked file touched.

Cutoffs used at scan time (2026-11-27 22:32 +07:00): recent = modified after 2026-11-25 22:32; stale = modified before 2026-11-20 22:32.

## Safe categories applied

1. `__pycache__/` + `*.pyc` except under `.opencode/` and `tools/BitNet/`.
2. `~$*`, `*.tmp`, `*.swp`, `.DS_Store`, `Thumbs.db`.
3. `*.bak`, `*.old`, `*.log` only when unreferenced, older than 7 days, and outside protected roots.
4. Empty directories left after those deletions.

## Candidate manifest — Location A

Every file below matched a safe *pattern*, but **none** qualified for deletion: each is protected, active-env, newer than 7 days, or modified in the last 48 h. No deletion was performed.

| Path | Bytes | Category | Decision / reason |
|---|---:|---|---|
| `art\comfy\ALH\__pycache__\alh.cpython-312.pyc` | 39,941 | 1 | PROTECTED — inside `art/comfy/ALH/` (also <48 h) |
| `art\comfy\ALH\learning-log.v1.jsonl.bak` | 44,283 | 3 | PROTECTED — inside `art/comfy/ALH/` |
| `art\comfy\scripts\__pycache__\validate_ui_workflow.cpython-312.pyc` | 9,117 | 1 | PROTECTED — inside `art/comfy/scripts/` |
| `art\tests\__pycache__\_qa_crowd_sheet.cpython-312.pyc` | 5,320 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\asar_extract_runtime.cpython-312.pyc` | 2,723 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\audit_refs.cpython-312.pyc` | 11,115 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\build_global_context.cpython-312.pyc` | 29,878 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\build_h3_qa_grid.cpython-312.pyc` | 4,275 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\build_p3g12_anchor.cpython-312.pyc` | 3,519 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\build_single_node_ui.cpython-312.pyc` | 19,141 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\build_v3_specs.cpython-312.pyc` | 15,110 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\chain4_recover.cpython-312.pyc` | 7,297 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\chain4_run.cpython-312.pyc` | 14,237 | 1 | PROTECTED — inside `art/tests/` (also <48 h) |
| `art\tests\__pycache__\check_asset_prompt.cpython-312.pyc` | 11,480 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\check_first_frame.cpython-312.pyc` | 4,485 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\feed_h3_context.cpython-312.pyc` | 16,333 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\h3_prompt_rules.cpython-312.pyc` | 19,120 | 1 | PROTECTED — inside `art/tests/` (also <48 h) |
| `art\tests\__pycache__\rebuild_prompts.cpython-312.pyc` | 28,156 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\record_verdict.cpython-312.pyc` | 3,118 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\story_chain_qa.cpython-312.pyc` | 7,934 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\story_to_asset_prompts.cpython-312.pyc` | 18,508 | 1 | PROTECTED — inside `art/tests/` |
| `art\tests\__pycache__\workflow_state.cpython-312.pyc` | 10,559 | 1 | PROTECTED — inside `art/tests/` |
| `art\archive\old-role-20261124\logs\render-freshstart.log` | 11,962 | 3 | SKIPPED — 2026-11-25 17:22, younger than 7 days |
| `art\archive\old-role-20261124\logs\render-g02-sample.log` | 900 | 3 | SKIPPED — 2026-11-25 20:35, younger than 7 days |
| `art\archive\old-role-20261124\logs\render-film.log` | 12,458 | 3 | SKIPPED — modified <48 h (2026-11-25 23:57) |
| `art\archive\old-role-20261124\logs\render-g02-r7.log` | 356 | 3 | SKIPPED — modified <48 h (2026-11-26 00:56) |
| `.hf-tts\xet\logs\xet_20261123T215036685+0700_17912.log` | 140,490 | 3 | SKIPPED — active TTS env cache, younger than 7 days (2026-11-23) |
| `.venv-tts\Lib\site-packages\__pycache__\brotli.cpython-312.pyc` | 2,034 | 1 | SKIPPED — active TTS virtualenv |
| `.venv-tts\Lib\site-packages\__pycache__\soundfile.cpython-312.pyc` | 79,272 | 1 | SKIPPED — active TTS virtualenv |
| `.venv-tts\Lib\site-packages\__pycache__\threadpoolctl.cpython-312.pyc` | 86,001 | 1 | SKIPPED — active TTS virtualenv |
| `.venv-tts\Lib\site-packages\__pycache__\typing_extensions.cpython-312.pyc` | 166,651 | 1 | SKIPPED — active TTS virtualenv |
| `.venv-tts\Lib\site-packages\__pycache__\_soundfile.cpython-312.pyc` | 3,660 | 1 | SKIPPED — active TTS virtualenv |
| `.venv-tts\Lib\site-packages\__pycache__\_virtualenv.cpython-312.pyc` | 4,127 | 1 | SKIPPED — active TTS virtualenv |
| `learning_system\__pycache__\alh_core.cpython-312.pyc` | 35,702 | 1 | SKIPPED — modified <48 h (2026-11-27 13:12), ALH-related |
| `studio\work\selftest-ad30-01\assemble.log` | 11,253 | 3 | SKIPPED — younger than 7 days (2026-11-23 21:47) |

Category 2 (`~$*`, `*.tmp`, `*.swp`, `.DS_Store`, `Thumbs.db`): **no matches** in the scanned scopes.
Empty directories: **none created or removed**.

## PROTECTED / skipped list (intentionally untouched)

- `art/comfy/ALH/` — entire tree, including `learning-log.jsonl`, `*.bak`, `__pycache__`, and this report.
- `art/comfy/GPU-LOCK.json`, `art/comfy/chain4/`, `art/comfy/scripts/`, `art/comfy/patches/`, `art/comfy/*.json`.
- `art/tests/`, `art/env/`, `art/part*.json`, `art/animation-plan.json`, `art/bg-layout.json`, `art/jobs*.json`.
- `prompts/`, `characters.json`, `WORKFLOW-INDEX.md`, `AGENTS.md`, `.opencode/`, `tools/`, `out/` — not scanned/modified.
- `.hf-tts/` and `.venv-tts/` — active TTS environments; all matched files skipped.
- `learning_system/`, `studio/` — matched files skipped by recency rule.
- Location B: `.git/`, `PLAYBOOK.md`, `audit-inputs/`, all tracked files — untouched. `git status --short` clean.

## Verification

- Deleted files: **0**. Deleted directories: **0**.
- Bytes reclaimed: **0**.
- Errors: **0**.
- Only new file created: `art/comfy/ALH/CLEANUP-REPORT-20261127.md` (this report).
- No delete commands were run because no candidate passed all SAFE + age + reference + protection gates.
