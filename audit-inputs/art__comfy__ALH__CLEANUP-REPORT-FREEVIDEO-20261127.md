# Cleanup report — FreeVideo / MiniMax H3 install (2026-11-27)

Location: `C:\Users\Admin\FreeVideo\` plus the temporary clone at
`C:\Users\Admin\AppData\Local\Temp\opencode\freevideo\`.
Light targeted pass only (no hashing, no `out/`, no model-weight reads).
Nothing under `FreeVideo-engine`, `models`, `envs`, `ComfyUI`, `.freevideo`, or
`agent/token` was touched. No GPU work, no queue, no git writes.

## Decision table (inventory at 2026-11-27, all items last touched 2026-11-23)

| Path | Size | Decision | Reason |
|---|---:|---|---|
| `FreeVideo\test-runs\20261123T121632Z-14964` | 2300.8 MB | **DELETE** | Old smoke-test output (4 runs, report/inventory). Only reference in the project is the historical `.opencode/smoke-test.log`; no active script reads it. |
| `Temp\opencode\freevideo\FreeVideo-main` + `repo.zip` | 121.3 MB | **DELETE** | Temporary source clone + download zip from 11/23, never referenced by project scripts; project memory says this old build is to be ignored. |
| `FreeVideo\downloads\MinGit-2.55.0.5.zip` | 37.2 MB | **DELETE** | One-off installer payload; Git is installed and repo work succeeds without it. |
| `FreeVideo\tmp\uv` | ~0 MB | **DELETE** | Ephemeral uv temp directory. |
| `FreeVideo\downloads\torch-wheels` | 1837.1 MB | KEEP | Installer wheel cache referenced by `bootstrap.py:208` for repair/reinstall. CHƯA CHỐT — deleting would force a network re-download. |
| `FreeVideo\downloads\uv-cache` | 3585.3 MB | KEEP | uv environment cache referenced by `bootstrap.py:911`. CHƯA CHỐT. |
| `FreeVideo\prepared\edge-da37681f5a1f7015` | 21871.4 MB | KEEP | Prepared int8-convrot model cache actively selected by `prepared_model.select()` / `install_tuning.discover_prepared()` during setup and reuse. Far from safe to delete without a decision. |
| `FreeVideo\kernel-cache` | 45.0 MB | KEEP | Compiled cuda/triton/inductor kernels: deleting costs render speed. |
| `FreeVideo\input-cache` | 11.7 MB | KEEP | Conditioning / refined-text runtime cache. |
| `FreeVideo\continuations` | 7.9 MB | KEEP | Continuation safetensors, runtime state. |
| `FreeVideo\setup-runs` | 32.0 MB | KEEP | `render-ready.ps1` and `finish-setup.ps1` pick the newest run here; do not remove the directory. |
| `FreeVideo\transfer-reports` | 0.6 MB | KEEP | Tiny install-transfer records; no meaningful gain. |
| `Downloads\FreeVideo\src\FreeVideo-main` | not scanned | KEEP | Marked stale in AGENTS.md/skill, but four project scripts still reference the path; deleting it would break those helpers. |

## Result

5 exact-path removals succeeded, 0 errors, **2,578,665,597 bytes (≈2.40 GiB) reclaimed**:

| Removed path | Bytes |
|---|---:|
| `FreeVideo\test-runs\20261123T121632Z-14964` | 2,412,524,431 |
| `Temp\opencode\freevideo\FreeVideo-main` | 71,288,319 |
| `Temp\opencode\freevideo\repo.zip` | 55,863,159 |
| `FreeVideo\downloads\MinGit-2.55.0.5.zip` | 38,989,688 |
| `FreeVideo\tmp\uv` | 0 |

Post-delete check: all five paths absent. `FreeVideo\test-runs\` remains as an empty
directory (no active script depends on its contents). Engine, models, envs, ComfyUI,
`agent/token`, `prepared`, `kernel-cache`, `input-cache`, `continuations` and
`setup-runs` verified untouched. GPU was not touched; the chain remains `qa_hold`.
