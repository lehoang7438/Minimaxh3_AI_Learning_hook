---
name: character-bible
description: Keep recurring characters consistent across MiniMax H3 Ref2VA shots. Use when storing a character's fixed appearance, wardrobe, voice and reference files, mapping them to <Subject N>/<Picture N>/<Audio N> labels, or reusing the exact same description in every prompt of a series.
---

# Character Bible

A project-level record of who each character is, so `<Subject 1>` reads the same in shot 1 and shot 40.

**Identity audit 25/11 (chưa apply, chờ batch xong):** `friend_clap.must_keep` ghi "navy t-shirt"
nhưng `wardrobe` là **charcoal tee** → xung đột thật, phải sửa. Hai cảnh báo khác là giả vì nằm trong
phủ định có chủ đích: khang "Never a vest" / "no vest"; friend_beer "navy tee + charcoal **trousers**".

**Tóc cá nhân hoá:** giữ **tóc đen xù** làm nhận diện riêng của Khang; tách 2 bạn:
`friend_beer` = **short neat combed black hair**, `friend_clap` = **side-parted swept black hair**.
**Quy tắc đồng bộ text↔ảnh:** đổi `appearance`/tóc trong bible thì **phải gen lại canon ref bằng H3
Image + asset-qa** rồi mới cập nhật `refs[].path`. Tuyệt đối không để bible ghi "tóc gọn" mà ref
đưa vào node vẫn là "tóc xù" — text và ảnh sẽ đánh nhau trong prompt.

**Hai mức wardrobe:** mỗi character có `wardrobe` (đầy đủ: áo + quần + giày) và `upper_wardrobe`
(chỉ cổ/vai/tay áo). Prompt **WS/MS** dùng `appearance + wardrobe`; prompt **CU/INS** dùng
`appearance + upper_wardrobe` — không chèn quần charcoal/chân trần vào cận cảnh mặt hay ly.

**Vai trò:** bible là nguồn để `build_global_context.py` tạo phần `characters` (ref + wardrobe_id +
appearance) trong `art/env/global-context.json`. Không tạo bản định nghĩa nhân vật song song, không
gen lại character khi đã có canon ref — chỉ bổ sung 1 ảnh ref khi nhân vật bị drift.

Ref chỉ được đăng ký sau Asset QA: mỗi `refs[]` phải có `qa_passed: true` và `color_count`
(sau khi `asset-qa` soi xong). Scene crop painterly (>150–200 màu) bị cấm làm canon ref — chính nó
kéo H3 sang gradient và sai màu quần áo trong ca G02.

Khi một shot trong chain không có layer nhân vật nhưng hành động cần tay/người (vd G03 cụng ly),
cast được **kế thừa từ shot trước cùng set** — dùng chính canon ref đó, không gen character mới.
`v3-r1-restaurant.png` (có bánh) dùng cho G02/G03; `v3-r1b-empty-table.png` (134 màu, flat) dùng
cho G04 sau tiệc — cùng set, khác state.

## Storage

```
.opencode/skills/character-bible/characters.example.json   # template
<project>/characters.json                                  # your copy
refs/                                                      # images / video / audio
```

Copy the example next to your project and edit. Keys per character:

| Key | Meaning |
|---|---|
| `id` | stable slug used by scripts |
| `subject_label` | the H3 label, e.g. `<Subject 1>` |
| `appearance` | one paragraph, order: age/ethnicity, face, hair, build, distinguishing marks |
| `wardrobe` | exact clothing and colours; separate `wardrobe_by_shot` if it changes |
| `voice` | timbre, pace, accent, language — used for `<d>[Language]` lines |
| `refs` | label → local path → what it fixes (face, costume, gait, voice) |
| `must_keep` | traits that may never change |
| `may_change` | lighting, pose, camera side, mood |
| `notes` | free text |
| `scale_anchor` (top-level) | user-chosen canonical frame/ref that defines body scale (e.g. Khang from G02, 1:6, 85–90% frame) |
| `relative_height` | this character's height as a ratio of the anchor (1.00 = same height) |
| `wardrobe_id` | **machine-checkable** outfit slug; every character layer in a spec must declare the same `outfit` |
| `wardrobe_hex` | dominant torso colour of the canon asset (reference only — colour alone cannot identify an outfit when everyone wears navy) |
| `forbidden_tokens` | tokens that must never appear on this character (Khang: vest/jacket/scarf; infected: shoes) |

**Wardrobe lock (bắt buộc từ 24/11/2026).** Quần áo phải giữ nguyên qua mọi shot, trừ khi có
`wardrobe_by_shot` khai báo rõ. H3 không tự nhớ trang phục, và pixel cũng không phân biệt được
hai người cùng mặc navy — nên nhất quán được **khai báo**, không đo màu:

1. Mỗi character có `wardrobe_id` + `wardrobe_hex` + `forbidden_tokens` trong `characters.json` (script: `art/tests/add_wardrobe_ids.py`).
2. Mỗi layer `role: character` trong spec có `"outfit": "<wardrobe_id>"`. Script điền: `art/tests/add_wardrobe_ids.py [part1 part2 part3]`.
3. `h3-visual-qa/scripts/visual_qa.py` → bucket **ASSETS**: `outfit` khác canon = FAIL, thiếu = WARN, token cấm = FAIL.
4. Khi gen lại asset: copy `wardrobe` **nguyên văn** vào prompt kèm `forbidden_tokens` dạng negative; nếu drift, dùng thêm 1 ảnh ref đúng đặc điểm đang drift (không thêm tính từ).

**Scale rule:** never let each character invent its own proportions. Pick one anchor from a frame the user actually approved, then generate every other character at `relative_height × anchor`. If the user rejects the first auto-generated take, re-anchor to the frame they name and regenerate — do not patch adjectives.

**Wardrobe rule:** outfits must be **logical for the role and visibly distinct** — never dress every character in identical navy. Copy `wardrobe` from the bible exactly; `wardrobe_rules.pairs` in `characters.json` lists who wears what. Palette stays navy / bone white / one muted teal; red only for blood, infected eyes, recording dot.

## Label rules (important)

H3 labels are **positional**, not permanent IDs: `<Picture 1>` means "the first picture uploaded with this request". Before generating, confirm the upload order matches the `refs` order in the bible. If it cannot match, renumber the bible entry for that shot instead of guessing.

Never write `<<character_1>>` or invent `<Subject 9>` — only the four valid forms: `<Subject N>`, `<Picture N>`, `<Video N>`, `<Audio N>`.

## Workflow

1. Read `characters.json` and pick the characters in the shot.
2. Compose `subject_definitions` from `appearance` + `wardrobe` + `refs`, one line per label, word-for-word from the bible.
3. In `detailed_description`, refer to the character only by label, never by a paraphrased description.
4. Build dialogue with the voice profile: `<d>[Vietnamese] ...</d>`.
5. Run `h3-prompt-linter`; every label used must be defined.
6. After an accepted render, update the bible only if the character's canon changed — not because a take looked nice.

## Consistency rules

- Copy the description string exactly; do not "improve" wording between shots.
- Keep `must_keep` short (3–5 items). A long list constrains the model and flattens performance.
- One reference per role (face, costume, voice). Extra pictures dilute attention.
- If a character drifts, add a picture reference for the drifting feature instead of adding adjectives.
- Wardrobe changes belong in `wardrobe_by_shot`, not in a rewritten `appearance`.

## FreeVideo Media panel (Characters / Scenes / Props)

Widget `assets` của node `FreeVideoMedia` là **chuỗi JSON** gồm các row. Mỗi row trỏ tới một ảnh đã copy vào `C:\Users\Admin\FreeVideo\ComfyUI\input`:

```json
{"file": "ref_khang.png", "role": "reference", "cast": {"id": "khang"}}
```

| Tab | `cast` |
|---|---|
| Characters | `{"id": "<character id>"}` — khớp `id` trong `characters.json` |
| Scenes | `{"id": "scene_<shot>", "setting": true}` |
| Props | `{"id": "prop_<shot>", "prop": true}` |

- Copy ref trước: `art/assets/h3/refs/*` → `ComfyUI/input/` (đặt tên `ref_*.png`).
- **Mỗi role chỉ 1 ảnh** — nhiều ảnh làm loãng attention. Nếu nhân vật bị drift, thêm ảnh cho đúng đặc điểm đang drift, đừng thêm tính từ vào prompt.
- Script điền tự động: `art/tests/fill_workflow_params.py` (đọc bible + spec, ghi `assets` cho từng Media node).
- `audio_use` để `"reference"`; nếu dùng `"original"` thì phải nối `reference_audio`.

## Helper

```powershell
powershell -File .opencode\skills\character-bible\scripts\build-definitions.ps1 `
  -Bible .\characters.json -Ids lan,minh
```

Prints a ready `subject_definitions:` line using each character's stored text and labels, so it can be pasted (or piped) into the Ref2VA prompt unchanged.

## Related skills

- `h3-prompt-writing` — Ref2VA six-section format.
- `h3-storyboard` — assigns labels per shot.
- `h3-prompt-linter` — checks label definitions and usage.
