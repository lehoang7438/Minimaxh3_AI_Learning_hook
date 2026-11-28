---
name: h3-visual-qa
description: Find visual and continuity errors in storyboard keyframes before rendering. Use when checking composited 2D frames for palette violations, magenta chroma bleed, sprite slicing artifacts, duplicated props, vest-on-character errors, timeline gaps, VO lines that overflow a shot, and flat-vector style drift.
---

# H3 Visual QA

Sau khi QA xong (kể cả PASS) → mở `WORKFLOW-INDEX.md` để nhắc bước kế + ALH.
Hy4 chỉ mô tả bằng tiếng Việt và kết thúc `Đã nhìn 1/1 ảnh`; agent tự chốt verdict,
`visible_check: seen` + `script_fidelity: MET` mới được PASS. Cấm `PASS_WITH_WARN`.

Two passes. Never skip pass 1: it is cheap and catches the boring mistakes. Pass 2 catches the ones a script cannot see.

**Chain QA (Tầng 3 — nhịp thứ 2, sau Per-shot).** Mỗi cụm 3–5 shot cùng chain: xem liền mạch với
`voice-narrator.wav`, đối chiếu **eyeline** (trục 180° của cabin-map), **tỷ lệ cao–thấp** giữa các
nhân vật (`relative_height`), **trôi màu/ánh sáng** giữa shot, **nhịp cắt** (không 3–4 shot cùng cỡ
cảnh/góc liên tiếp) và **khớp thoại** với `target_duration`. Chain FAIL thì sửa spec/context, không
sửa từng clip một. Các field dùng ở đây là `metadata_only`, không đưa vào prompt H3.

**Vai trò:** QA nhằm sửa **workflow / global context / prompt** rồi chạy lại — không tự sửa frame,
không tạo file QA rời rạc làm artifact của agent (chỉ `out/<name>/qa/*.png` để đọc bằng mắt).
FAIL thuộc về node/input nào thì sửa đúng node/input đó trong `h3-master.json` hoặc context.

## Checklist chấm PASS/FAIL sau MỖI video (bắt buộc)

Chỉ cần **1 mục FAIL là clip FAIL** — dừng, phân loại, sửa đúng 1 lớp bằng H3/workflow, chạy lại
chính shot đó. Đọc `first.png` + `mid.png` bằng mắt (không chỉ tin machine gate).

| # | Mục | Câu hỏi chấm điểm |
|---|---|---|
| 1 | **Style contract** | Có giữ flat fill / nét sạch không, hay gradient tường–đèn–sàn, bóng mờ, painterly? |
| 2 | **Palette lock** | Màu có nằm navy / bone / teal (+ amber nhà hàng) không, hay lọt hồng/teal lạ (vd bánh)? |
| 3 | **Character & Wardrobe lock** | Trang phục đúng `wardrobe_id`/`hex` không (quần bạn charcoal/dark, KHÔNG teal)? Mặt giữ canonical? |
| 4 | **Anatomy & rule riêng** | Tay có đúng **mitten, không mọc ngón** không? Nhận diện có ổn giữa first và mid không? |
| 5 | **Motion / Continuity / Audio** | Chuyển động có gãy/biến dạng nặng không; khớp anchor chain, duration probe và thoại không? |

`target_duration` trong global context là **số giây thực tế sau làm tròn lưới frame** (`17k+5`,
vd 6 s → 158 frame → 6.583 s), không phải số nguyên yêu cầu — so duration với mốc này (±0.5 s).
Chain QA phải so thêm **prop-state** giữa các shot (vd G02 ly đầy/bánh có nến → G03 cụng →
G04 ly cạn/bánh đã dọn) và **cast kế thừa** (G03 có tay người cầm ly, không phải ly tự cụng).

**Identity QA (input↔QA khép kín, bản nháp chờ batch):** trước khi duyệt shot phải kiểm:
- prompt **không có slug** dạng `khang-navy-longsleeve` / `vy-crew-*` (thay bằng câu bible);
- `must_keep` không xung đột `wardrobe` (friend_clap navy vs charcoal) — phủ định "Never a vest"
  là hợp lệ, không báo giả;
- **text↔ảnh đồng bộ**: nếu bible đổi tóc (friend_beer chải gọn, friend_clap rẽ ngôi) thì canon ref
  phải được **gen lại bằng H3 Image + `qa_passed`**; ref cũ tóc xù bị loại;
- CU/INS chỉ dùng `upper_wardrobe`, không kéo quần/chân trần vào cận cảnh.
Gate máy (`visual_qa.py`, `diagnose_shot.ps1`) chỉ bắt lỗi đo được; checklist này bắt phần còn lại.
G02 từng lọt qua mọi gate máy nhưng FAIL ở mục 1/3/4 — đó là lý do checklist là bắt buộc.

## Pass 1 — machine check (`scripts/visual_qa.py`)

```powershell
python .opencode\skills\h3-visual-qa\scripts\visual_qa.py `
  --spec art\part1-spec.json --name part1 --frames art\keys\part1 --json out\qa-part1.json
```

Exit `0` = no FAIL (warnings allowed), `1` = at least one FAIL.

Measured checks:

| | What it measures | Why it exists |
|---|---|---|
| A | Timeline contiguous, `end-start == seconds`, part total, 4–15 s per clip | cuts that overlap or leave holes |
| A | VO/dialogue words vs remaining time, budget 2 words/second | the brief's own rule; over-long lines desync |
| B | every referenced asset and keyframe exists, canvas 704×1280 | silent missing layer = half-built frame |
| C | per-shot `forbid_assets` tokens, `max_instances` per asset | bandage before the bite shot, two cakes, duplicate character |
| D | a `vest`/`waistcoat` asset used as a **character** layer = FAIL | the "Khang never wears the vest" rule |
| E | magenta share in the 3 % top/bottom band of every sprite, magenta bleed in the final frame | bad chroma key leaves pink halos |
| F | red pixel ratio vs 4.5 % cap unless the shot declares blood/flash/rec | red is reserved for blood, infected eyes, rec dot |
| G | Quantized color count of each background and asset (WARN > 300, FAIL > 520) | flat vector vs painterly drift. Calibrated on this project: old painterly restaurant bg = 640 colors, flat bgs = 103–380, characters = 51–236. **Do not use luminance ramps for this** — the required heavy vignette always produces soft ramps (16–23 %) even on correct flat art. |
| H | `fps_out` must be 24, zoom/shake/grain ranges sane | mixed-frame-rate delivery breaks the cut |
| **ASSETS** (new) | ≥3 full-frame white/black gutters in a background = FAIL, 2 = WARN | H3 Image reads "storybook" and returns a **page of panels** instead of one background plate; `v3-r1-restaurant.png` measured 3 |
| **ASSETS** (new) | every character layer declares `outfit` equal to `wardrobe_id` in `characters.json`; mismatch FAIL, missing WARN | wardrobe must stay logically identical across shots; pixel colour cannot separate two navy outfits |

Declare the guards inside the spec so they can be measured:

```json
{ "id": "G05",
  "forbid_assets": ["vest", "bandage", "infected-eyes"],
  "max_instances": { "art/assets/v3-cake.png": 1 },
  "layers": [ { "image": "art/assets/v3-khang-sing.png", "role": "character",
                "outfit": "khang-navy-longsleeve", "x": 0.48, "y": 0.92, "h": 0.46 } ] }
```

`characters.json` now carries `wardrobe_id` / `wardrobe_hex` / `forbidden_tokens` per character;
`art/tests/add_wardrobe_ids.py` fills the bible and all part specs in one pass. The ASSETS bucket
runs automatically when `characters.json` exists — no extra flag needed.

## Pass 2 — agent eyeball pass (what pass 1 cannot see)

Build the grid, then look at it as images, not as text:

```powershell
python .opencode\skills\h3-visual-qa\scripts\build_review_grid.py --spec art\part1-spec.json --name part1 --first 5
```

Open `out/storyboard/part1-grid.png`. Ask these eight questions per shot — this is the exact list that found the real bugs in this project:

1. **Wardrobe on the right layer?** A prop asset appearing *on* a body (Khang wearing the vest) is invisible to pixel math.
2. **Sprite integrity?** Two-row sheets sliced by columns cut bodies in half: floating mitten hands, a diagonal band of the neighbour's shirt across a chest, legs without a torso.
3. **Does the background already contain the prop?** If yes, the extra prop layer becomes a second cake, a second cart, a second phone.
4. **Face consistency?** Any asset with eyebrows, nose, hair strands or chin shading breaks the flat rule and reads as a different character.
5. **Is the shot readable at thumbnail size?** Oversized props (four beer glasses filling the frame) or a background-only aisle with nobody in it fail this.
6. **Is the background one scene?** Panels, borders, two viewpoints or a grid = FAIL, even if each panel looks fine (machine check I catches the big ones).
7. **Do objects have a support surface?** Chairs must reach the floor, the cake sits on the table, cups sit on a tray/table, a door has a frame. Anything floating or growing out of a body fails.
8. **Is the light logical and consistent?** One source with a visible fixture, shadows all in the same direction, colour inside the navy/bone/teal palette — no pink rim light, no two conflicting window lights.

## Rules learned the hard way

- One character per asset. Multi-person or multi-pose sheets must be single row, evenly spaced, and never split a figure. If unsure, generate separate single-character files.
- A background that contains a prop must not receive that prop again as a layer.
- Red candles, red karaoke lights, red TV art: all palette violations. Amber, white, teal only.
- Candles and food are baked into the background for wide shots; prop assets are for close-ups.
- Emotion words in an image prompt ("exhausted", "terrified") push H3 Image toward semi-realistic faces. Always restate: *no eyebrows, no nose, dot eyes, solid fills*.

## Calibration

Thresholds must be measured on your own assets, not guessed:

```powershell
python .opencode\scripts\calibrate_flatness.py
```

It prints ramp % and color count per asset. Set `COLOR_WARN` / `COLOR_FAIL` around the
gap between the good flat assets and the bad painterly ones.

## How to check (the actual recipe that found this project's bugs)

1. `visual_qa.py` on the spec → timeline, VO length, asset existence, forbidden props.
2. `visual_qa.py` on the keyframes → red budget, chroma bleed, painterly assets.
3. `build_review_grid.py` → one image of all shots.
4. Read the grid **as images** and answer the eight questions above, per shot.
5. Every bug found in step 4 that was invisible in steps 1–2 becomes a new machine check:
   add a `forbid_assets` / `max_instances` / `role` field to the spec so it cannot come back.

Bugs this recipe caught, and the guard each one became:

| Bug seen by eye | Guard added |
|---|---|
| Khang wearing the vest in the karaoke shot | asset regenerated with "ONLY navy shirt, no vest"; `forbid_assets: ["vest"]` |
| Three-person sheet sliced into half-bodies, floating hands | one character per asset file, `role: character`, `forbid_assets: ["friends-sheet"]` |
| Second cake floating in front of the table (bg already had one) | prop baked into bg for wide shots; `max_instances: {"v3-cake.png": 1}` |
| Beer glasses filling the whole frame, unreadable | prop re-generated smaller, `h` cap + thumbnail pass |
| Faces with eyebrows/nose/shading in a flat cast | prompt restates "no eyebrows, no nose, dot eyes"; color-count check flags painterly faces |
| VO line of 19 words in a 7 s shot | 2 words/second rule is now a hard FAIL |
| `v3-r1-restaurant.png` came back as a 6-panel comic page | machine check I: ≥3 full-frame gutters = FAIL; "one continuous scene, no panels/grid" in the prompt |
| `v2-hand-grip.png` had fingers instead of mittens | `asset-qa` eyeball rule; restate "mittens, no fingers" in the prompt |
| Navy outfits are indistinguishable by colour | `outfit` declaration per character layer + `wardrobe_id` in the bible (machine check J) |

## Handoff — khi QA FAIL thì sửa ở đâu

Dùng `art/comfy/scripts/diagnose_shot.ps1 -Shot <id> [-Video <mp4>]` để phân loại nguyên nhân
trước khi sửa: context → asset → prompt → workflow → clip. Sửa **đúng 1 lớp** rồi chạy lại QA.
- Asset FAIL → gọi lại H3 Image (contract prompt), QA, cập nhật global context.
- Prompt FAIL → sửa prompt nguồn / global context, không váoutput.
- Workflow FAIL → sửa node/input trong `h3-master.json` hoặc `Ghe27AContext`.
- Mọi gate PASS mà video vẫn sai → đổi anchor/ref/seed trong context, render lại bằng H3.
Không tự vẽ/keyframe bằng code, không hand-patch frame.

### Quy trình handoff gốc

- FAIL from pass 1 → fix asset, spec or compositor, re-run pass 1.
- Issue from pass 2 → regenerate the asset (single character, explicit negatives), rebuild keyframe, re-run both passes.
- Only when pass 1 is clean and pass 2 has no open items does the shot go to `render_part1.py`.

## Related skills

- `h3-storyboard` — defines the shot list this tool validates.
- `h3-prompt-linter` — text-side gate; it explicitly does not check wardrobe or taste.
- `character-bible` — source of truth for what a character may and may not wear.
