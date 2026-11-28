---
name: freevideo-runner
description: Drive the local MiniMax H3 install (FreeVideo engine) from the command line: preflight the machine, plan and estimate, submit, wait, download, and recover from the exact errors this install returns. Use for any local H3 video or picture render instead of hand-writing ComfyUI workflows.
---

# FreeVideo Runner (local H3)

**Role boundary:** H3 tạo video; agent chỉ dựng workflow/global context, kiểm soát prompt + tài
nguyên, check lỗi và gọi H3 Image khi thiếu ref. **Kiểm tra là một nửa quy trình sản phẩm** —
không chạy batch 25 shot khi mẫu đầu chưa QA PASS; sau mỗi clip phải `diagnose_shot.ps1` + soi
`first/mid.png`. Mọi kỹ năng ở đây phục vụ `h3-master.json` + `Ghe27AContext`. Không tạo script/file chỉ để bookkeeping, không tự vẽ/keyframe bằng code, không
nhân bản workflow theo từng shot. Xem `comfyui-runner` → *Role contract*.

One GPU, one server, one job at a time. The engine already exposes an agent HTTP API on the
ComfyUI port the user has open — use it. Do not build a second ComfyUI, do not invent workflow
JSON for a plain render, and do not queue a video while a picture job runs.

## 1. Which path

| Task | Path |
|---|---|
| One video / picture, keyframes, references, lip-sync, continue, upscale | **agent API** (`fv.ps1`, this skill) |
| Give the user a graph they can open and edit in the browser | `comfyui-runner` + `art/comfy/*.json` |
| Full project pipeline (spec → keyframes → part render) | the scripts in `AGENTS.md`, not this skill |

## 2. Hard facts on this host

| Thing | Value |
|---|---|
| Engine root (has `agent/token`) | `C:\Users\Admin\FreeVideo\FreeVideo-engine` |
| Agent source (for MCP / CLI) | `...\FreeVideo-engine\launcher\source\<newest version>` |
| Server | not fixed: 8188 normally, 8189 when 8188 is taken. `fv.ps1` auto-detects the live one |
| Agent base | `/freevideo/agent/v1`, header `Authorization: Bearer <token>` |
| Token file | `<engine>\agent\token` — never print it |
| Engine version | 0.6.9, build 2026.11.24.535 |
| CLI | `<engine>\launcher\source\<version>\freevideo.cmd --root <engine>` |
| **Stale copy to ignore** | `%USERPROFILE%\Downloads\FreeVideo\src\FreeVideo-main` (v2026.9.16 — wrong flags, wrong models) |

`--root` for the CLI and MCP is the **engine** folder (`...\FreeVideo-engine`), not the parent
`...\FreeVideo` install root. With the parent you get `no_token`.

## 3. Golden loop

```powershell
$fv = ".opencode\skills\freevideo-runner\scripts\fv.ps1"

powershell -File $fv doctor                     # GO / NO-GO + the reason
powershell -File $fv plan -JobFile art\comfy\jobs\shot.json    # frames + minutes, no render
powershell -File $fv submit -JobFile art\comfy\jobs\shot.json  # prints job id
powershell -File $fv wait -Id <job>             # blocks until terminal, prints error.next on failure
powershell -File $fv download -Id <job> -Out out\shot.mp4
```

Job file (`art/comfy/jobs/*.json`):

```json
{ "kind": "generate", "label": "Tau xuyen tuyet", "ref": "opencode-t2v-train-01",
  "prompt": "integrated_multimodal_description: ...", "seconds": 10, "aspect": "16:9" }
```

- `ref` = new name per request. The same `ref` repeats a submission whose answer was lost; never
  use it to ask for a second take.
- `label` = 1–4 words in the user's language (they see it on the job card).
- `seconds` / `aspect` are what the user asked for (10 s / `16:9` if they said nothing).

API equivalents if the script is not usable: `POST /plan`, `POST /jobs`,
`GET /jobs/{id}?wait=25`, `GET /jobs`, `POST /connect/hello`, `GET /capabilities`, `GET /guide`.

## 4. Legal geometry (from `GET /capabilities`)

| MP | 16:9 | Use |
|---|---|---|
| 0.5 | 960x544 | draft |
| 0.75 | 1184x672 | fast check |
| **0.98** | **1344x768** | **default / "0.9 MP" of the reference video** |
| 1.0 | 1376x768 |  |
| 1.5 | 1664x928 |  |
| 2.0 | 1920x1088 | heavy |

- `1280x736` is **not** a legal canvas on this build — it is what the promo video shows. Nearest
  legal values are 1184x672 and 1344x768. Sizes are multiples of 32; model minimum 256.
- Lengths, 24 fps, frames on `17k+5`: 2 s = 56, 3 s = 73, 4 s = 107, 5 s = 124, 6 s = 158,
  7 s = 175, 8 s = 192, 9 s = 226, 10 s = 243, 15 s = 362. A requested 10 s renders as
  10.12 s — say the real length, not the frame count.
- Training range ~124–362 frames (5–15 s). Past 15 s the engine chains parts; state that before
  starting.

## 5. Quality presets → job fields

| Preset | Fields |
|---|---|
| `light` (default) | `two_pass: true, base_steps: 8, refine_steps: 3, upscale_factor: 2` |
| `medium` | same, `upscale_factor: 1.5` |
| `high` | `two_pass: false, base_steps: 16, step_cache: "easycache-av"` |
| `max` | `two_pass: false, base_steps: 20, step_cache: "easycache-av"` |

- Two-pass runs **only** with `base_steps: 8`; any other count silently becomes one pass.
- `step_cache` accepts `easycache-av` / `fbcache` only — there is no `none` value to pass.
- Upscale of a finished MP4: `--upscale-from file.mp4` (1.5x step) instead of a re-render.

## 6. Measured on this machine (RTX 3060 12 GB / 16 GB RAM)

| Canvas | Length | Quality | Wall clock |
|---|---|---|---|
| 1344x768 | 10 s | light | 16.6 min *(plan estimate, 243 frames, 11 steps)* |
| 1280x704 | 10 s | light | 12.5 min *(seed of the earlier bench)* |
| 1920x1088 | 10 s | light | 34 min |

Tell the user the plan estimate before any run over ~10 min. Draft at 960x544 when the goal is
"What does this prompt do?", then render the keeper once.

## 7. Errors this install actually returns → next step

| Code / symptom | Meaning | Do this |
|---|---|---|
| `no_token` | CLI/MCP started with the wrong `--root` | Point `--root` at `...\FreeVideo-engine` (folder with `agent\token`) |
| `too_large` | payload > 1 MiB (usually a prompt file accidentally nested) | Send only the prompt text, never a wrapper object |
| `busy_video` | picture job and video engine fight for the GPU | Finish or stop the picture job, then retry once |
| `invalid_request` about size/length | canvas or frames not in the legal table | Resubmit once with the nearest legal value, change nothing else |
| `needs_confirmation` | the user must approve in the FreeVideo window | Wait for the user, repeat the identical call once |
| queue busy | another job owns the GPU | `wait -Id <job>`, never a tight loop |
| `not_ready` / `host_memory_low` | models not loaded / RAM too low | Close browsers + Ollama, retry; the engine preloads on demand |
| two `main.py` processes / `Could not acquire lock on database` | a second ComfyUI was started | Kill the extra one, keep the server FreeVideo opened; never run `python main.py` yourself |
| a port has a listener but `/system_stats` never answers | half-started server (lost the DB lock to another instance) | `fv.ps1 doctor` names the port; restart the FreeVideo app so it owns 8188 again |
| `comfyui-workflow-templates is not installed` | harmless banner from a hand-started server | Ignore for API work, or let the launcher start the server |
| `numpy` traceback from `freevideo agent` | the launcher env is used without `--root` | Always pass `--root`; see `fv.ps1` |
| result looks wrong (not an error) | prompt / canvas problem | Fix the prompt (`h3-prompt-writing`), re-plan, one retry; then change the approach, not the seed |

## 8. Rules

1. `doctor` first. A NO-GO line is a stop, not a warning to ignore.
2. Never start ComfyUI yourself; the app owns the server, the token file and the DB lock.
3. One render at a time; look at a frame before reporting success (`fv.ps1` + contact sheet).
4. Lint every prompt: `h3-prompt-linter` (3 sections base, 6 sections Ref2VA).
5. Report the real duration and the estimate you promised; keep `ref` stable only for retries.

## Related skills

- `h3-prompt-writing`, `h3-prompt-linter`, `h3-storyboard` — prompt production.
- `character-bible` — recurring cast, `<Picture N>` mapping.
- `h3-visual-qa` — QC of what came back.
- `comfyui-runner` — only when the deliverable is an editable graph.
