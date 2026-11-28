# Chain4 multi-route workflow (28/11/2026)

Một workflow duy nhất: `art/comfy/chain4/h3-chain4.json`, điều khiển bởi
`art/tests/chain4_run.py`. Không tạo `t2v_route.py`, `run.ps1`, `media.json` hay
workflow riêng cho từng shot. Omit `--route` = legacy (`auto`) giữ nguyên hành vi cũ.

## Khi nào dùng route nào

| Route | Dùng khi | Ảnh / audio vào node 1 | `continue_from` | `voice_reference` / `first_frame_reference` | `audio_use` |
|---|---|---|---|---|---|
| `auto` | Chạy chain4 cũ, `--ref-asset` như trước | `[]` hoặc 1 `--ref-asset` | segment trước (legacy) | giữ nguyên graph (`True`/`False`) | giữ nguyên graph (`reference`) |
| `fresh` | Cú cắt T2V, không ref, không audio | `[]` | `''` | `False` / `False` | `reference` |
| `fresh_audio` | Cú cắt nhưng cần **timbre giọng G01** | `[]` + `LoadAudio` → `reference_audio` | `''` | `False` / `False` (chỉ metadata trên fresh) | `reference` |
| `continue_voice` | Nối clip trước, giữ giọng thoại của đoạn mở đầu | `[]` | clip trước | `True` / `False` | `original` |
| `continue_anchor` | Nối clip trước nhưng ép 1 ảnh anchor do user chọn | đúng 1 ảnh `--continue-anchor` | clip trước | `False` / `False` | `reference` |
| `continue_media` | Nối clip trước kèm 1–3 ảnh tham chiếu | 1–3 ảnh `--media` | clip trước | `False` / `False` | `reference` |
| `continue_media_plain` | Như `continue_media` nhưng audio để dạng "as is" theo route map | 1–3 ảnh `--media` | clip trước | `False` / `False` | `original` |

G01 audio ref = `art/env/voice-narrator.wav` (4.16 s). Đây là **timbre** (màu giọng),
KHÔNG phải driving audio; `fresh_audio` tự dùng file này khi không truyền `--audio`.
Trên cú cắt fresh, `voice_reference`/`first_frame_reference` bị bỏ qua ở
`comfy_nodes.py:412-414` — đường dẫn có tác dụng là `FreeVideoMedia.reference_audio`
+ `audio_use: 'reference'`.

## Luật cứng (preflight `validate_route()`, chạy trước `doctor()` và trước mọi mutation)

* Tối đa **3 ảnh** `--media` — engine `continuation.PICTURES_MAX = 3` áp cho phần tiếp nối.
* `--continue-anchor` xung đột `--media` **và** `--first-frame-reference`
  (`generate.py:579-581`); driver luôn ghi `first_frame_reference=False` cho route này.
* `--audio` xung đột mọi route `continue_*`; chỉ dùng cho `fresh_audio` (hoặc fresh có ref).
* Route `continue_*` bắt buộc có clip trước (dùng `--start 2 --shots 2 --shot-ids G01,G02`
  để render đúng shot 2 từ handoff `G01.mp4`); route `fresh_*` không được có `continue_from`.
* Mọi file được dẫn chiếu phải tồn tại.

Ranh giới dữ liệu: cấu hình route nhận `{kind: "image", path: "..."}`; script **không**
tự viết `sha256` / `bytes` (engine `media_request.file_info` tự tính). Ở ranh giới
ComfyUI, `FreeVideoMedia.assets` vẫn đúng định dạng đã chạy ổn:
`[{"file": "<tên file trong ComfyUI/input>", "role": "reference"}]`; driver tự stage file
vào `C:/Users/Admin/FreeVideo/ComfyUI/input`. Ở agent API (`fv.ps1` / `POST /jobs`),
khi có `continue_from` chỉ cho phép `media.references`; trường audio `use:'original'`
có segmentation tồn tại ở flow nâng cao nhưng **không được hỗ trợ ở đây**.

> Caveat chưa test GPU: `comfy_assets.connect_assets()` từ chối `audio_use='original'`
> khi không có `reference_audio` được nối. Vì luật cấm `--audio` trên route tiếp nối,
> `continue_voice` / `continue_media_plain` mới chỉ được chứng minh **queueable về mặt
> graph** (preflight PASS), chưa chạy thật; cần quyết định riêng trước khi đốt GPU.

## Lệnh mẫu (copy-paste; thay seed bằng seed đã duyệt)

```powershell
# fresh — cú cắt T2V, G01
& ".\.venv-tts\Scripts\python.exe" art\tests\chain4_run.py --route fresh --shots 1 --start 1 --shot-ids G01 --seconds 6 --seed 20269901 --outdir out\route\fresh --chain-name route-fresh --prompts prompts\part1-rebuilt

# fresh_audio — cú cắt G01 với timbre giọng G01 (mặc định voice-narrator.wav)
& ".\.venv-tts\Scripts\python.exe" art\tests\chain4_run.py --route fresh_audio --shots 1 --start 1 --shot-ids G01 --seconds 6 --seed 20269901 --outdir out\route\fresh_audio --chain-name route-fresh-audio --prompts prompts\part1-rebuilt

# continue_voice — nối G01 → G02, giữ giọng thoại
& ".\.venv-tts\Scripts\python.exe" art\tests\chain4_run.py --route continue_voice --shots 2 --start 2 --shot-ids G01,G02 --seconds 6 --seed 20269901 --outdir out\route\continue_voice --chain-name story-g02-v11 --prompts prompts\part1-rebuilt

# continue_anchor — nối G01 → G02, ép 1 ảnh anchor (không --media, không first-frame)
& ".\.venv-tts\Scripts\python.exe" art\tests\chain4_run.py --route continue_anchor --continue-anchor art\assets\h3\refs\bloody-arm-real-r6-1024.png --shots 2 --start 2 --shot-ids G01,G02 --seconds 6 --seed 20269901 --outdir out\route\continue_anchor --chain-name story-g02-v11 --prompts prompts\part1-rebuilt

# continue_media — nối G01 → G02 kèm 1–3 ảnh (tối đa 3)
& ".\.venv-tts\Scripts\python.exe" art\tests\chain4_run.py --route continue_media --media art\assets\h3\refs\bloody-arm-mitten-r5-1024-down.png art\assets\h3\refs\bloody-arm-real-r6-1024.png --shots 2 --start 2 --shot-ids G01,G02 --seconds 6 --seed 20269901 --outdir out\route\continue_media --chain-name story-g02-v11 --prompts prompts\part1-rebuilt

# continue_media_plain — như trên nhưng audio_use='original'
& ".\.venv-tts\Scripts\python.exe" art\tests\chain4_run.py --route continue_media_plain --media art\assets\h3\refs\bloody-arm-mitten-r5-1024-down.png --shots 2 --start 2 --shot-ids G01,G02 --seconds 6 --seed 20269901 --outdir out\route\continue_media_plain --chain-name story-g02-v11 --prompts prompts\part1-rebuilt
```

Chỉ chạy từng lệnh sau khi doctor GO và seed đã được duyệt; mỗi lệnh là đúng 1 job,
không batch mù.
