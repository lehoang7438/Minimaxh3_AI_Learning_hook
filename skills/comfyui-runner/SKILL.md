---
name: comfyui-runner
description: Queue a MiniMax H3 render through a local ComfyUI API-format workflow. Use when the deliverable is an editable ComfyUI graph, when a workflow file must be validated before queueing, or when a queued job returned node_errors and needs decoding.
---

# ComfyUI Runner

Sau khi sửa workflow / queue / decode node_errors → mở `WORKFLOW-INDEX.md` để nhắc bước kế + ALH.
Không thay browser queue bằng tay; workflow phải ở API format và qua `preflight_workflow.py`.

**Hợp đồng 3 tầng (24/11/2026):** Spec định nghĩa chuẩn → Skill ngăn lỗi trước GPU → QA đối
chiếu đúng chuẩn đó. Không chờ tới lúc ra video mới soi (ca G02 tốn 3 lần render vì thiếu mốc).

- **Tầng 1 — Spec** (`global-context.json` + `cabin-map.json`): `render` (fps/resolution/aspect),
  `shots[].shot_size` (wide/medium/close-up), `camera_motion`, `mood`, `eyeline`, `props_state`
  (vật + mặt đỡ + trạng thái cuối), `target_duration`, `wardrobe_ids`, `relative_height`; chain giữ
  trục 180°. Mọi ref (character/set/prop) mang `qa_passed` + `color_count`.
- **Tầng 2 — Skill**: `h3-storyboard` xếp shot (không 3–4 shot liên tiếp cùng cỡ cảnh/góc, giữ trục
  180°, tránh text cận cảnh khi không yêu cầu); `h3-prompt-writing/linter` ép thứ tự
  *style → cỡ cảnh & camera → nhân vật + wardrobe → hành động + mặt đỡ → mood ánh sáng*; `asset-qa`
  khóa ref (ngưỡng màu **theo loại** character/set/prop); `comfyui-runner` ép thông số render.
  **Voice ref là `timbre`** (màu giọng 4–5 s), KHÔNG phải driving audio — độ dài do `target_duration`
  / frame count quyết định; nếu dùng driving audio thì phải cắt đúng đoạn khớp từng shot.
  Khi ghép: `strip_model_audio=true` bỏ audio rác của H3 (`-an`), và concat **encode lại 1 lần**
  (`reencode_once`) thay vì `-c copy` thuần — `-c copy` chỉ an toàn khi mọi clip cùng codec/fps/timebase
  và không trim dead frame.
- **Tầng 3 — QA**: `diagnose_shot.ps1` so khớp tự động (fps/res/aspect, duration vs target, frozen
  frame, mọi ref `qa_passed`); `h3-visual-qa` soi **per-shot** (5 mục) rồi **chain QA** (3–5 shot
  liền với voice: eyeline, tỷ lệ cao–thấp, trôi màu/ánh sáng, nhịp cắt, khớp thoại).

**Anchor rule (sửa sau ca G02):** first-frame anchor phải là **ref flat đã QA** (`qa_passed: true`),
không phải frame từ bản phim cũ — bản `out/part1.mp4` có vignette/gradient, H3 sẽ copy nhiễu đó dù
prompt cấm gradient. Chọn anchor **linh hoạt**, không fix cứng:
- **Cú cắt** (khác góc/INS, hành động không nối được) → `anchor_mode: "plate"`: dùng set plate phẳng
  đã QA + kế thừa cast của chain (option 1). VD G02→G03→G04 nhà hàng.
- **Hành động nối liền** trong cùng chain → `anchor_mode: "last_to_first"`: dùng last-frame clip trước
  (option 2). Chỉ dùng khi clip trước **verdict = PASS** — clip `PASS_WITH_WARN` không được làm anchor.
- Fallback cuối: `"film"` (frame `out/part1.mp4`).
`feed_h3_context.py` và `Ghe27AContext` đọc `anchor_mode`; `ANCHOR_OVERRIDE` trong
`build_global_context.py` cho phép sửa từng shot. Video FAIL dù gate máy PASS thì kiểm **anchor** trước.

**Tách metadata vs prompt (quan trọng):** chỉ field `prompt_visible` được đưa vào prompt H3.
`fps`, `resolution`, `aspect_ratio`, `target_duration`, quy tắc trục 180°, `relative_height` so với
shot trước và ghi chú Chain QA là `metadata_only` — để script/QA kiểm, **không nhồi vào prompt**
(nhồi dài làm H3 loãng trọng số, đúng lỗi style contract ở cuối field 1).

For a plain local H3 render prefer the `freevideo-runner` agent API. Use this skill when the
artifact itself is a workflow (the user opens it in the browser, edits it, hands it over).

## Role contract — đọc đầu tiên (24/11/2026)

**H3 là người tạo video. Agent không tạo video, không vẽ lại bằng code.** Mọi việc của agent
phải phục vụ workflow hoặc H3; nếu một file/script không trả lời được *"nó vào node/input nào
của H3?"* thì **không tạo** (hoặc cho vào `art/archive/old-role-*`).

Agent **chỉ** làm 6 việc:

1. **Giữ đúng 1 workflow** — `art/comfy/h3-master.json` (API) + `art/comfy/h3-single-node-ui.json`
   (UI) + custom node `ComfyUI/custom_nodes/Ghe27AContext`. Không tạo bản sao theo shot.
2. **Giữ global context** — `art/env/global-context.json`: style/prompt contract, nhân vật +
   wardrobe + canon ref, side character, set/background, prop, voice, chain, shot map. Đây là
   nơi duy nhất định nghĩa thứ dùng lại; `cabin-map.json` và `characters.json` là nguồn để build.
3. **Soạn & kiểm soát prompt/tài nguyên** — 3 field (base) hoặc 6 (Ref2VA), dòng first-frame,
   set continuity, wardrobe, style contract; ≤8 ref, mỗi role 1 ảnh, audio ≤15 s, canvas/frames
   hợp lệ, two-pass 8+3. Lint trước khi queue.
4. **Check lỗi** — preflight workflow + validate UI trước queue, đọc `node_errors` để sửa đúng
   node, QA output sau render. Lỗi thì sửa **workflow/prompt**, không retry mù, không vá video.
5. **Gọi H3 Image khi thiếu tài nguyên** — prompt đúng `generation_prompt_contract`, gen 1 ảnh,
   QA ngay (size, panel, bible), FAIL thì sửa prompt/gen lại ảnh đó, rồi đăng ký vào global
   context làm reference.
6. **Chạy tuần tự & ghép cuối** — 1 job/lần; `run_master.ps1` inject `{{SHOT}}/{{SECONDS}}/
   {{SEED}}/{{PROMPT}}`, queue, probe, rồi ffmpeg concat. Không tự project-anim bằng code.

**Không làm (role cũ):** tạo `h3-context-Gxx/h3-ui-Gxx/h3-node-Gxx`, driver riêng từng thử
nghiệm, graph native `UNETLoader/LoraLoader` khi chưa có model, ảnh/keyframe vẽ bằng PIL, sửa
frame bằng code, JSON schema mới trùng global context, hay script chỉ phục vụ bookkeeping của agent.

**1 Shot → 1 QA Gate (bắt buộc, sửa sau ca G02).** Không batch mù:
- Chỉ chạy batch nhiều shot khi **1–2 shot mẫu đầu** đại diện cho chain/nhân vật/set đó đã QA PASS
  và global context / prompt template **không còn thay đổi**.
- Sau **mỗi lần sửa** H3/ref/prompt/node → chạy **đúng 1 shot**, kiểm tra ngay.
- Vòng cứng cho mỗi shot: `feed_h3_context` + `lint` + `diagnose_shot.ps1` (gate trước) → render
  1 shot qua `h3-master.json` → QA sản phẩm (`first.png`, `mid.png`, video + probe duration) →
  **PASS mới sang shot N+1**; FAIL → dừng queue, phân loại Asset / Prompt / Context / Workflow,
  sửa đúng **1 lớp** bằng H3 rồi chạy lại **chính shot đó**.
- Không để 25 shot chạy xong mới phát hiện shot 2 lệch style — ca G02 đã đốt GPU vô ích vì điều này.

Mọi file mới phải chỉ được vào một trong các chỗ trên. Khi cần thứ gì đó cho H3 → sửa workflow
hoặc global context; khi cần thứ gì đó cho agent → không tạo.

## Product QA loop — sau khi workflow đã đẹp thì ra sản phẩm và test sản phẩm

Chạy `powershell -File art\comfy\scripts\diagnose_shot.ps1 -Shot G02 [-Video <mp4>]`. Script
thu thập bằng chứng theo đúng thứ tự có thể gây lỗi: global context → asset (size/gutter/color)
→ prompt lint → workflow preflight → clip (nếu có). Output là bản đồ nguyên nhân, **không tự sửa video**.

| Nguyên nhân | Dấu hiệu | Sửa bằng H3 / workflow |
|---|---|---|
| Asset | gutter ≥3, size sai, color >520, sai Bible | gọi lại H3 Image với `generation_prompt_contract`, QA, đăng ký vào global context |
| Prompt | lint ERROR, thiếu set continuity / wardrobe / first-frame | sửa `prompts/<shot>.txt` hoặc `global-context.json`, inject lại `{{PROMPT}}` |
| Workflow | `node_errors`, preflight FAIL | sửa `h3-master.json` hoặc dây `Ghe27AContext`, validate UI lại |
| Khác (mọi gate PASS nhưng video vẫn lệch) | mặt/nền/hành động sai | đổi first-frame anchor, bộ ref hoặc seed **trong workflow/context**, rồi chạy lại H3 |

**diagnose phải fail ồn ào (duyệt 25/11):** `diagnose_shot.ps1` kiểm `$LASTEXITCODE` sau mọi lời gọi
python/ffmpeg; lỗi in `! ... PYTHON FAIL exit=N` rồi `exit 1`. Không được để lỗi here-string/imolation
khiến asset/style gate chạy im lặng mà vẫn in PASS — gate im lặng chính là ca G02/G03.
**Anchor slot (duyệt 25/11):** plate cảnh phải là **picture/ref số 1**, character ref đứng sau; nếu
character sheet (nền key hồng) đứng trước thì frame 1 của video là sheet hồng, dù `first` đã nối plate.
Nếu đã đúng slot 1 mà frame 1 **vẫn** mở bằng sheet: bỏ character sheet khỏi Media panel cho shot đó
(`MEDIA_CHAR_DROP` trong `FreeVideoGhe27AContext`, ca G02) — danh tính giữ nguyên trong wardrobe text;
đừng sửa prompt thêm lần nữa.

**Prompt composition trên đường UI (duyệt 25/11):** node `Ghe27AContext` là nguồn prompt thật của
workflow UI. Nó phải **cắt field rebuilt tại `[Shot 1]`** — không dò câu cuối của contract, vì
`allow_text` đổi câu đó và marker cũ (`no watermark.`) trượt → contract bị chèn **hai lần** và trôi
xuống ~1900 ký tự (đúng lỗi G02/G01). Chỉ chèn thêm dòng first-frame và `<Audio 1>` (khi audio thật
sự được nối) giữa contract và `[Shot 1]`; **không** prepend lại scene/objects/light/wardrobe.
Report của context và của Generate phải nối `PreviewAny` (shot/part/refs/first/voice/canvas/seconds),
SaveVideo prefix theo shot (`ghe27a/G01_h3`), seed `fixed`.
`upscale_factor "2"` = **không upscale** (sentinel, `comfy_nodes.py:94`) — output đúng bằng canvas
704×1280; `first_frame_reference`/`voice_reference` chỉ có tác dụng khi `continue_from` được set
(`comfy_nodes.py:413-414`), nên `False` trong graph là bình thường: ảnh đầu và giọng đi qua
`FreeVideoMedia`.

Không vá frame bằng PIL, không dựng lại clip bằng code, không retry mù. Mỗi lần sửa chỉ đụng đúng
1 lớp rồi chạy lại `diagnose_shot.ps1`. `run_master.ps1` mặc định **dừng sau mỗi shot** để soi
`first.png`/`mid.png`; chỉ thêm `-BatchVerified` khi 1–2 shot mẫu đã PASS và context/prompt không
đổi nữa.

## Before queueing (non-negotiable)

1. **Never start a second ComfyUI.** The FreeVideo app owns the server, the `agent/token` file and
   `user/comfyui.db`. A hand-started `python main.py` collides on the database
   (`Could not acquire lock on database '...comfyui.db'`) and on VRAM. If nothing answers on
   `127.0.0.1:8188`, ask the user to open FreeVideo.
2. Run `fv.ps1 doctor` once (see `freevideo-runner`) — GO/NO-GO, queue idle, no stray picture job.
3. Validate the workflow against the live server:

```powershell
python art\comfy\scripts\preflight_workflow.py art\comfy\h3-1-t2v.json
# exit 0 = queueable, 1 = errors, 2 = server/JSON problem
```

It checks unknown node types, misspelled inputs, dangling links, required inputs, combo options,
numeric ranges, and the H3 traps: `two_pass` without `base_steps 8`, canvas not a multiple of 32,
canvas outside the capability sizes, duration vs frame grid, placeholder prompts.

4. Lint the prompt (`h3-prompt-linter`) — a malformed prompt wastes a 12–17 minute slot.

## Ready-made workflows (canonical — chỉ 2 file)

| File | Vai trò |
|---|---|
| `art/comfy/h3-master.json` | **Workflow duy nhất** cho mọi shot. Node `Ghe27AContext` đọc `{{SHOT}}`, xuất assets/first-frame/voice vào `FreeVideoMedia`; `FreeVideoGenerate.text = {{PROMPT}}`; `{{SECONDS}}`/`{{SEED}}` do `run_master.ps1` điền. |
| `art/comfy/h3-single-node-ui.json` | Bản UI của cùng graph: đổi `shot_id` trên node 30 rồi Queue lại; không cần file riêng cho G08/G09. |

Mọi file khác trong `art/comfy/` (bản T2V/I2V/Ref2V/lip-sync cũ, native, per-shot, pilot driver)
đã chuyển vào `art/archive/old-role-20261124/`. KHÔNG phục hồi chúng nếu không có yêu cầu mới.

Build lại: `python art/tests/build_global_context.py` → `python art/tests/feed_h3_context.py <shot>`
→ `python art/tests/build_single_node_ui.py`. Chạy: `art/comfy/scripts/run_master.ps1`.

## Format rules

- **API format only** for queueing: `{"1": {"class_type": ..., "inputs": {...}}}`. A UI workflow
  (`nodes` + `links`) must be exported with *Export (API)* first; the preflight refuses it.
- Input names must match `/object_info` exactly. `FreeVideoGenerate` optional inputs are:
  `first, last, references, loras, conditioning, media, two_pass, base_steps, refine_steps,
  force_regenerate, preview, refine_from, continue_from, frames, first_frame_reference,
  voice_reference, hide_tail, step_cache, upscale_factor, allow_empty_prompt, upscale_from,
  upscale_to`.
- `FreeVideoMedia` slots: `assets` (JSON string `"[]"`), `first`, `last`,
  `reference`, `reference_2 … reference_8`, `reference_audio` (≤15 s), `audio_use`.
- `FreeVideoReference` takes **exactly one** of `image` / `video` / `audio`, then `previous`.
- Never hand-edit widget order in a UI file; node widget values are positional. Rebuild with the
  generator instead of patching JSON.
- The Generate node *is* an output node and saves the MP4 itself; add `SaveVideo` only when a
  second, re-encoded copy is the point (e.g. the 2K upscale chain).

## Queueing

```powershell
powershell -File .opencode\skills\comfyui-runner\scripts\queue_prompt.ps1 `
  -Workflow art\comfy\h3-1-t2v.json -PromptFile art\comfy\prompts\t2v-train-snow.txt `
  -OutDir out\h3 -TimeoutSec 5400
```

- One H3 job at a time on 12 GB VRAM; a second one OOMs.
- `node_errors` = the workflow is wrong, not the server: read `node_errors.<id>.errors[].message`,
  fix that node, re-run the preflight, do not retry blindly.
- Outputs land in `/history` under `images` (with `animated: true` for video), `gifs`, or `videos`
  depending on the node; download with `/view?filename=&subfolder=&type=output`.
- Keep `<output>.request.json` / the job's `ref` so a take can be reproduced.

## Failure table

| Symptom | Cause | Fix |
|---|---|---|
| `Could not acquire lock on database` | second ComfyUI running | close the extra one, keep FreeVideo's |
| `comfyui-workflow-templates is not installed` | hand-started server, missing templates package | harmless for API work; ignore |
| `node_errors` with `Required input is missing` | typo in `inputs` key | preflight names the exact input |
| `prompt is not the expected shape` / frozen video | wrong prompt sections | 3 sections (base) or 6 (Ref2VA), lint first |
| `Value not in list` | combo value not an option (`step_cache` has no `none`) | use `easycache-av` / `fbcache` or omit |
| two-pass ignored | `base_steps != 8` | set 8, or accept one pass |
| job sits in `queued` | another job owns the GPU | `fv.ps1 jobs`, wait, do not resubmit |
