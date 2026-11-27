---
name: h3-storyboard
description: Turn a rough video idea into MiniMax H3-ready shots of 4-15 seconds before prompt writing. Use when planning multi-shot scenes, deciding shot durations and frame counts, splitting a script into clips, or choosing camera angles, lighting and sound beats for H3 T2VA/I2VA/FL2VA/Ref2VA prompts.
---

# H3 Storyboard

Split an idea into clips MiniMax H3 can actually render, then hand each clip to `h3-prompt-writing`.

**Secure contract (Tầng 2 — trước khi đốt GPU):** khi ghi shot vào `global-context.json` phải có
`shot_size` (wide/medium/close-up), `camera_motion` (static/pan/zoom), `mood`, `eyeline` và
`props_state` (vật + mặt đỡ + trạng thái cuối làm anchor cho shot sau). Luật:
- Không xếp **3–4 shot liên tiếp cùng cỡ cảnh/góc máy** — H3 dễ sinh clip đứng im/trùng khung.
- Giữ **trục 180°** theo `cabin-map.json`; eyeline nhất quán trong cùng chain (metadata, không nhồi prompt).
- Nếu shot không yêu cầu đọc chữ/số (biển, màn hình, nhãn chai) → quy định **tránh text cận cảnh**
  để H3 không gen chữ giun dế; để linter chặn từ khóa sinh chữ.

**Kế thừa cast & prop-state trong cùng chain (quyết định 25/11, ca G02→G03→G04):**
cùng set thì giữ **cùng cast + cùng canon ref + plate**, chỉ đổi **hành động**; không tạo shot kiểu
"đồ vật tự cử động". G03 (4 ly cụng) dù spec không có layer nhân vật vẫn kế thừa
`characters = G02` (khang + friend_beer + friend_clap), action = *"bốn bàn tay mitten cầm bốn ly
cụng nhau trên bàn"*. Prop state đi theo chuỗi: **G02 ly đầy + bánh có nến → G03 đang cụng → G04 ly cạn,
bánh đã dọn, không nến**, dùng plate `v3-r1b-empty-table.png` cho G04.
Override cast/state được ghi trong `build_global_context.py` (`CAST_OVERRIDE`, `STATE_OVERRIDE`) —
là metadata + prompt_visible action, không phải sửa pixel sau render.

**Chọn anchor linh hoạt 1/2:** `anchor_mode` mỗi shot do chain quyết định:
- cú cắt (`plate`) → kế thừa cast + set plate phẳng, chỉ đổi action (G02→G03→G04);
- hành động nối (`last_to_first`) → last-frame shot trước, **chỉ khi shot đó PASS** (G11→G15);
- fallback `film`. `ANCHOR_OVERRIDE` cho phép sửa từng shot. Không ép last-frame qua cú cắt.

**Rule cỡ cảnh anchor (sửa sau ca G03 — bánh tan ở cận cảnh):** shot `close-up`/`INS`/`ui`
**không được dùng thẳng wide plate** làm first-frame — cỡ cảnh anchor phải khớp cỡ cảnh shot.
- Tốt nhất: dùng H3 Image tạo riêng 1 plate INS ở độ phân giải chuẩn cho góc đó (G03: 4 ly nâng
  cao ngang tầm cụng, bánh nằm **ngoài mép dưới khung** — vẫn tồn tại trong chuyện, chỉ ngoài khung),
  QA qua `asset-qa`, rồi đăng ký làm anchor riêng.
- Nếu bắt buộc thấy bánh: generate INS anchor vẽ sẵn 4 ly + bánh gọn từ đầu, có khoảng hở không
  để ly đè trực tiếp lên nến — **không crop thô từ wide plate** (ảnh mềm → H3 bệt màu).
- Không viết "không có bánh/không có nến" để xóa prop khỏi anchor: H3 local xử lý phủ định kém,
  cố xóa vật đang có trong frame đầu → vật càng tan (đúng bệnh G03).
- Flat-fill không có depth blur: vật nhỏ nhiều chi tiết bị foreground quét qua dễ mất object
  permanence → tan/chảy. Tránh bố cục có vật đó ngay sau vật chuyển động.

**Vai trò:** shot list / duration / chain phải được ghi vào `art/env/global-context.json` (`shots`,
`chains`, `sets`) để `Ghe27AContext` đọc. Không tạo storyboard file riêng làm artifact của agent.

## Why split

H3 renders 4-15 s per request and degrades when one shot carries too much action. One clip = one dominant action, one camera move, one emotional beat. Anything longer becomes several shots joined by hard cuts inside the clip.

## Shot limits (verified against the engine geometry)

Frames are 24 fps and must land on `17k + 5`. Ask for whole seconds; the engine rounds up to the next valid count:

| Seconds | Frames | Seconds | Frames |
|---|---|---|---|
| 4 | 107 | 10 | 243 |
| 5 | 124 | 11 | 277 |
| 6 | 158 | 12 | 294 |
| 7 | 175 | 13 | 328 |
| 8 | 192 | 14 | 345 |
| 9 | 226 | 15 | 362 |

Dialogue: keep each line under ~4 s of speech. For longer lines, split across shots or use `--hide-tail` in FreeVideo.

## Workflow

1. **Collect** idea, total length, aspect, characters, reference files (pictures/video/audio), and whether the clip starts or ends on a supplied frame.
2. **List beats** as one line each: what changes on screen.
3. **Assign shots**: one beat per shot, 4-15 s, total within the target length.
4. **Fill the shot card** for every shot (template below).
5. **Record continuity**: character labels, wardrobe, props, time of day, screen direction.
6. **Hand off**: one prompt per shot via `h3-prompt-writing`, then validate with `h3-prompt-linter`.

## Shot card

```
Shot 3 | 6 s | 158 frames | 1344x768
Composition : medium close-up, subject frame-left, negative space right
Subject     : <Subject 1> (unchanged wardrobe: ...)
Action      : one dominant action, visible start and end state
Camera      : dolly-in, small amplitude, slow speed
Lighting    : practical neon from camera-left, cool fill, no flicker
Sound       : rain on metal awning, distant traffic, no dialogue
Refs        : <Picture 1> = face, <Picture 2> = costume
Cut in/out  : hard cut from Shot 2; ends on door closing -> cut to Shot 4
Duration fit: 1 action + 1 camera move, no scene change
```

## Rules

- One camera move per shot. "Push in and orbit and tilt" reads as chaos.
- Name the cut point in seconds from clip start (`At 00:04.000`), matching the prompt format.
- Keep screen direction consistent; state left/right explicitly.
- Reuse identical description strings for recurring characters — do not paraphrase them per shot.
- If the idea needs more than 3 actions in 10 s, add a shot instead of packing the prompt.
- For Ref2VA, fix `<Subject N>` / `<Picture N>` / `<Video N>` / `<Audio N>` in the storyboard and keep them unchanged through every shot.
- Mention on-screen text and its language only when it is readable in frame.

## Output

Return a Markdown table (shot, seconds, frames, composition, action, camera, lighting, audio, refs) plus the continuity notes. Do not write the final H3 prompt text here — that belongs to `h3-prompt-writing`.

## Related skills

- `h3-prompt-writing` — writes the actual 3-field or 6-section prompt.
- `h3-prompt-linter` — checks field names, labels and timecodes before rendering.
- `character-bible` — keeps recurring character descriptions identical.
- `freevideo-runner` / `comfyui-runner` — render the clips.
