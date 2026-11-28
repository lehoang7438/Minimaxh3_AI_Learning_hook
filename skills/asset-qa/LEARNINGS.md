# Learnings - asset-qa

## Reviewed / promoted 2026-11-25 (user approved)

- **Rule key character ref (sửa lần 3, user duyệt; E132/E205 thay E082):** H3 Image không tạo nổi `#FF00FF` chính xác. Chấp nhận **near-magenta** sau downscale 1024²: corner `R≥240, G≤40, B≥200`, uniform ≥95 %, corner-sampled keyer cắt sạch. `B≥230` đã bị thu hồi (canon r1 có `B=222`; keyer `compose_keyframe.py` lấy median 4 góc rồi key theo khoảng cách màu, không dùng ngưỡng tuyệt đối). Cũng **không thêm số kênh RGB** vào prompt — dùng cụm near-magenta đã chứng minh rồi đổi seed. Key hồng chỉ là nền tạm của ref nhận diện; **nền thật trong video lấy từ set plate QA**. Raspberry cũ (`B≈100–137`) vẫn FAIL. Cụm `exact FF00FF` vẫn giữ trong prompt để kéo màu sát nhất.
- Khang r2-1024: corner `(255,8,246)`, color_count 112, band 0, nhân vật đúng bible → **PASS**, đăng ký canon. Các entry `warn_accepted ... magenta_key` cũ chỉ áp dụng lại với ngưỡng mới này.

## Auto-learned (ALH)

_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. **Only `Accepted rules` are active.** Detail/verdicts are in `RUN-LOG.md` and the log; a rule is mandatory only after it is mirrored into `SKILL.md` / `GLOBAL-RULES.md`._

### Accepted rules (active)

- [E083] ALH:E083 — friend_beer regenerated ref key corner (255,8,128) after 1024 downscale - blue channel far too low, raspberry not near-magenta; FAIL under approved option A (needs B>=230).
- [E126] ALH:E126 — User rejected Hy4 PASS_WITH_WARN for G01 hand: v3 script explicitly requires a hand that is blood-soaked OR bitten/chipped with blood spreading.
- [E128] ALH:E128 — Promoted ALH E126 into mandatory asset-qa SKILL.md: Asset QA must compare each asset against the shot script/spec (script fidelity), not only the bible; PASS_WITH_WARN is not allowed when the script s…
- [E132] ALH:E132 — Use the corner-sampled near-magenta key gate R>=240, G<=40, B>=200 on a uniform field with RGB-distance keying; do not require B>=230.  [supersedes E082]
- [E133] ALH:E133 — Keep one unbroken paddle-mitten with a jagged bite notch, flat dark-red blood, a flat key and a low colour count on the G01 bite ref.
- [E148] ALH:E148 — Final shot P3G12 had no bg in the v3 spec; SCENE_OVERRIDE had assigned the cabin_chaos set, so the live Ghe27AContext node would have opened the final black-card shot on a chaotic cabin plate (blood-s…
- [E154] ALH:E154 — Full part1 QA of 18 shots: only G01/G05/G11/G12 PASS; 14 FAIL.
- [E159] ALH:E159 — Shot POV-K không dùng canon ref toàn thân: H3 đổi góc sang 3P và vẽ trọn người.
- [E164] ALH:E164 — seat27a-flat-r2 FAIL: mat nhan vat co vong cung nhamat thay vi 2 cham den, ban tay co duong tach ngon cai, manh hinh teal trong khong co anh sinh nhat.
- [E165] ALH:E165 — lav-mirror-flat-r2 FAIL: mat trong guong drift sang toc bob va vai tran, khong phai Khang toc xu xao ao navy dai tay.
- [E181] ALH:E181 — User 26/11 chot huong moi cho kho asset: nen duoc phep GIAU CHI TIET va CO CHIEU SAU, nhan vat van flat tuyet doi; lam lai toan bo kho 60 shot v3, xoa asset cu, ra soat lai prompt asset cho nhat quan,…
- [E188] ALH:E188 — G01 take 2026112906 (camera-lock prompt sau E179/E180) render xong, 2 file video cung hash.
- [E189] ALH:E189 — User da approve xoa toan bo asset cu.
- [E190] ALH:E190 — Hy4 soi cabin-master-map-v4: dat 1 diem nhin, perspective 1 diem, 3 lop phang co che khuat, 0 nguoi/0 do ro, khong magenta/amber -> dung huong nen sau.
- [E193] ALH:E193 — Khang turnaround v4 seed 20261126100: Hy4 mo ta 1/1 - 4 hinh dung 1 hang/cung scale/chan cung baseline, 1:6, 4 ngon thang+1 cai khong mong, khop vai/khuyu co.
- [E194] ALH:E194 — User 26/11 quyet dinh: 9 sheet turnaround 4 huong LA anchor nhan dang/bố cuc, KHONG duoc dua lam <Picture N> trong video va KHONG qua keyer, nen co the dung nen bone-white phang; bo cong magenta R>=24…
- [E199] ALH:E199 — Hy4 soi friend_girl_bob seed 43106 thay cham/dau tron nho o vai va khuỷu tay.
- [E200] ALH:E200 — Plate G02 (red_allowed=false) ra 2 cham do nho gan diem hoi tu du du prompt co cum `red only for blood and recording dot` trong style contract.
- [E202] ALH:E202 — Cabin variant plates generated without any <Picture N> drifted twice on G03 (third seat, amber dot) even with tight positive prompts.
- [E205] ALH:E205 — Restore the proven vivid near-magenta wording and change the seed when a chroma-key ref fails; do not add numeric RGB channel minima.  [supersedes E082]
- [E210] ALH:E210 — one aisle plate does not match the map.
- [E212] ALH:E212 — Route-map 3D r1 is geometry authority for the whole G01-G04 rebuild, but Hy4 description-only QA found 1+1 seats per row and only one visible window wall instead of the cabin-map invariant 3+3 (A-B-C/…
- [E213] ALH:E213 — Route-map 3D r2 still rendered 1+1 seats and one window wall after an explicit 3+3 prompt; the wrong-count r1 placed first in refs anchored the geometry.
- [E215] ALH:E215 — Master horror r3 FAIL/PARTIAL.
- [E252] ALH:E252 — User override past the 3/3 cap: regenerate the G01 mitten prop from corrected story-assets/cabin-map, Asset QA and register it, wire it as <Picture 1> in the one shared workflow, then render one fresh-seed G01 with the same visual review.
- [E254] ALH:E254 — The G01 bitten mitten must look ragged and chewed: several uneven chunks torn from the edge with blood in the notches, while remaining one unbroken silhouette with a solid navy cuff and no inner finger lines.
- [E256] ALH:E256 — The G01 reference is the 1024x1024 ragged mitten with a solid navy cuff, bright near-magenta key and one unbroken hand; wire it as <Picture 1>, keep the sleeve crop warning documented, and do not regenerate past asset retry 3.
- [E257] ALH:E257 — G01 v5 is FAIL: the hand must look like a real hand with thumb, separate fingers and nails, not a one-piece mitten; this supersedes E248/E133 for G01 while E254 ragged bite and blood still apply.
- [E258] ALH:E258 — Override-v6: G01 must use a realistic flat-2D hand with thumb, four separate fingers, short dark nails, a dirty darker ash-grey bone tone, ragged chewed bite and navy cuff; supersedes the v5 mitten for G01 only.
- [E259] ALH:E259 — Override-v6 asset bloody-arm-real-r6-1024.png is PASS_WITH_WARN: real flat hand with thumb, four fingers, dark nails, darker split ash-grey/bone tone, navy cuff, ragged blood, bright key; use it as <Picture 1> and do not regenerate without a new override.
- [E261] ALH:E261 — Override-v7: one final G01 pass must lock the cuff and nails as the darkest near-black navy fills, use uniformly dirty dark bone skin, remove the cool edge light that bleached them, and make the forearm snap up/down twice instead of only zooming.
- [E262] ALH:E262 — Override-v7 prop bloody-arm-real-r7-1024.png is PASS_WITH_WARN: wide near-black navy cuff, real flat hand with thumb/four fingers/near-black nails, one uniform dirty dark bone tone, ragged bite; pale teal in a few notches and cropped cuff top are documented warnings. Use as <Picture 1>; no regeneration without a new override.
- [E263] ALH:E263 — Override-v8: r8 prop must fill every chewed notch with flat dark-red blood only (no teal anywhere on the prop); the G01 camera and ambience are locked so the whole forearm rises twice with fingers spread, not camera pan or finger curl.
- [E264] ALH:E264 — Override-v8 prop bloody-arm-real-r8-1024.png is PASS_WITH_WARN: all four chewed notches are dark-red only with measured teal_pct 0.0, wide navy cuff, near-black nails, uniform dirty dark bone tone; cuff top edge cropped. Use as <Picture 1>; no regeneration without a new override.

### Accepted run records (evidence, not rules)

- E192 verdict / G01 / asset (detail in RUN-LOG.md)
- E195 verdict / G01 / asset (detail in RUN-LOG.md)
- E216 verdict / G02 / asset (detail in RUN-LOG.md)
- E217 verdict / G02 / asset (detail in RUN-LOG.md)
- E218 verdict / G03 / asset (detail in RUN-LOG.md)
- E219 verdict / G04 / asset (detail in RUN-LOG.md)
- E239 verdict / G01-G04 / asset (detail in RUN-LOG.md)

### Proposed (needs review, not a rule yet)

- E103 proposed: asset_qa_fail / G29 / magenta_key (detail in RUN-LOG.md)
- E109 proposed: rule_gap / G37 / prop_identity (detail in RUN-LOG.md)
- E117 proposed: rule_gap / G01 / asset_qa (detail in RUN-LOG.md)
- E127 proposed: asset_qa_fail / G01 / asset_qa (detail in RUN-LOG.md)
- E130 proposed: asset_qa_fail / G01 / asset_qa (detail in RUN-LOG.md)
- E151 proposed: rule_gap / FULL / asset (detail in RUN-LOG.md)
- E221 proposed: rule_gap / G01-G04 / asset (detail in RUN-LOG.md)
- E223 proposed: rule_gap / G01-G04 / asset (detail in RUN-LOG.md)
- E224 proposed: asset_qa_fail / G01-G04 / asset (detail in RUN-LOG.md)
- E226 proposed: asset_qa_fail / G01-G04 / asset (detail in RUN-LOG.md)
- E227 proposed: asset_qa_fail / G01-G04 / asset (detail in RUN-LOG.md)
- E229 proposed: asset_qa_fail / G01-G04 / asset (detail in RUN-LOG.md)
- E231 proposed: rule_gap / G01-G04 / story (detail in RUN-LOG.md)
- E233 proposed: rule_gap / G01-G04 / qa (detail in RUN-LOG.md)
- E236 proposed: rule_gap / ALL / qa (detail in RUN-LOG.md)
- E237 proposed: asset_qa_fail / G01-G04 / asset (detail in RUN-LOG.md)
- E238 proposed: rule_gap / G01-G04 / qa (detail in RUN-LOG.md)
- E241 proposed: verdict / G01-G04 / asset (detail in RUN-LOG.md)
- E253 proposed: asset_qa_fail / G01 / asset (detail in RUN-LOG.md)
- E255 proposed: asset_qa_fail / G01 / asset (detail in RUN-LOG.md)

### Revoked (do NOT apply - kept for history)

- E082 REVOKED - DO NOT APPLY: warn_accepted / freshstart-khang-magenta-r2-1024 / magenta_key (detail in RUN-LOG.md)
- E204 REVOKED - DO NOT APPLY: verdict / G01 / asset (detail in RUN-LOG.md)

### Archived (pre-v2 history, 76 events)

_One line per layer. Evidence stays in `RUN-LOG.md` / the JSONL log._

- aisle_geometry (1x, E022-E022): evidence in RUN-LOG.md
- archived_hair_refs (1x, E003-E003): evidence in RUN-LOG.md
- asset_qa (4x, E085-E123): evidence in RUN-LOG.md
- asset_reuse (2x, E089-E090): evidence in RUN-LOG.md
- assets (1x, E056-E056): evidence in RUN-LOG.md
- cabin_geometry (2x, E036-E037): evidence in RUN-LOG.md
- camera_composition (2x, E023-E024): evidence in RUN-LOG.md
- camera_view (1x, E035-E035): evidence in RUN-LOG.md
- character_bible (1x, E046-E046): evidence in RUN-LOG.md
- composition_palette (1x, E015-E015): evidence in RUN-LOG.md
- identity (1x, E032-E032): evidence in RUN-LOG.md
- injury_logic (6x, E063-E071): evidence in RUN-LOG.md
- lighting_logic (6x, E043-E059): evidence in RUN-LOG.md
- magenta_key (11x, E006-E086): evidence in RUN-LOG.md
- mitten_anatomy (8x, E004-E088): evidence in RUN-LOG.md
- palette_lock (5x, E038-E042): evidence in RUN-LOG.md
- panel_layout (1x, E020-E020): evidence in RUN-LOG.md
- pose_logic (3x, E049-E051): evidence in RUN-LOG.md
- prop_identity (2x, E028-E029): evidence in RUN-LOG.md
- qa (1x, E235-E235): evidence in RUN-LOG.md
- set_geometry (6x, E016-E027): evidence in RUN-LOG.md
- sheet_contract (3x, E047-E057): evidence in RUN-LOG.md
- style_eyes (4x, E034-E054): evidence in RUN-LOG.md
- style_flatness (1x, E011-E011): evidence in RUN-LOG.md
- style_geometry (1x, E018-E018): evidence in RUN-LOG.md
- window_fill (1x, E021-E021): evidence in RUN-LOG.md
