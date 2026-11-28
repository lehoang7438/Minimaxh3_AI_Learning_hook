# H3 MiniMax multi-route workflow (28/11/2026)

Workflow = graph H3 MiniMax, **không phải** driver chain4. Một graph duy nhất cho mọi shot:

| File | Vai trò |
|---|---|
| `art/comfy/h3-master.json` | API format, dùng để queue. Route vào node 1 qua `{{ROUTE}}`, `{{ROUTE_MEDIA}}`, `{{ROUTE_AUDIO}}`, `{{CONTINUE_FROM}}`, `{{ANCHOR}}`. |
| `art/comfy/h3-single-node-ui.json` | Bản UI ComfyUI của cùng chain `Ghe27AContext → FreeVideoMedia → FreeVideoGenerate → SaveVideo` + 2 `PreviewAny`. |
| `ComfyUI/custom_nodes/FreeVideoGhe27AContext/__init__.py` | Node đọc route, validate conflict, resolve asset/audio/anchor/continue, xuất 13 output. |
| `art/tests/h3_route_rules.py` | Nguồn luật duy nhất (dùng cho cả node lẫn validator). |
| `art/tests/h3_route_validate.py` | Preflight GPU-free. |
| `art/tests/build_single_node_ui.py` | Dựng lại UI graph (`--wire-routes on`). |

## Khi nào dùng route nào

| Route | Dùng khi | Ảnh / audio vào context | `continue_from` | `first_frame_reference` / `voice_reference` | `audio_use` |
|---|---|---|---|---|---|
| `auto` | Hành vi cũ, không route | plate/cast/prop + voice theo spec | `''` | giữ nguyên graph | `reference` |
| `fresh` | Cú cắt T2V, không ref, không audio | `[]` | `''` | `False` / `False` | `reference` |
| `fresh_audio` | Cú cắt nhưng cần **giọng G01** | `[]` + `route_audio` (mặc định `art/env/voice-narrator.wav`) | `''` | `False` / `False` | `reference` |
| `continue_voice` | Nối clip trước, giữ giọng mở đầu | `[]` | clip trước | `False` / `True` | `reference` |
| `continue_anchor` | Nối clip trước, ép 1 ảnh anchor | đúng 1 `route_anchor`, không ảnh khác | clip trước | `False` / `False` | `reference` |
| `continue_media` | Nối clip trước + 1–3 ảnh ref | `route_media` JSON `{kind,path}` | clip trước | `False` / `False` | `reference` |
| `continue_media_plain` | Alias của `continue_media` (giữ đúng bảng route) | như trên | clip trước | `False` / `False` | `reference` |

`route_media` nhận tối đa **3** ảnh (`continuation.PICTURES_MAX = 3`). Script/node chỉ viết
`{kind, path}`; engine tự tính `sha256`/`bytes` từ file đã stage.

## Luật cứng (preflight trước GPU)

- `route_anchor` + `route_media` → FAIL (`anchor_media` từ chối mọi conditioning khác).
- `route_audio` + bất kỳ `continue_*` → FAIL (giọng đi qua `continue_from` + `voice_reference`).
- `route_anchor` cần `continue_from`; `continue_*` đều cần `continue_from`; `fresh_*` không được có.
- `route_anchor` + `first_frame_reference` → FAIL (engine: chọn một trong hai).
- Mọi route đều ghi `audio_use='reference'`; `original` bị `connect_assets()` từ chối khi không có `reference_audio`.
- Chưa validate xong thì không queue, không chốt verdict.

## Lệnh

```powershell
# 1. GPU-free: 6 route hợp lệ + 5 conflict + cấu trúc 2 graph
& ".\.venv-tts\Scripts\python.exe" art\tests\h3_route_validate.py

# 2. SAU KHI RESTART ComfyUI (node có 13 output) dựng lại UI graph
& ".\.venv-tts\Scripts\python.exe" art\tests\build_single_node_ui.py --wire on --wire-routes on

# 3. Preflight API graph (chỉ PASS sau restart)
& ".\.venv-tts\Scripts\python.exe" art\comfy\scripts\preflight_workflow.py art\comfy\h3-master.json
```

Trước restart, preflight báo `unknown input 'route'` và output 8–12 chưa có — đó là trạng thái
dự kiến, không phải lỗi graph. **Không tự bật `python main.py`**; user restart app FreeVideo.

`art/tests/chain4_run.py` + `art/comfy/chain4/h3-chain4.json` là driver/graph cũ, giữ lại để
tham chiếu nhưng **không phải workflow H3** và không phải đường queue mới.
