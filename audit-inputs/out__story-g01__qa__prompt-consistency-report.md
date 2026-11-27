# Báo cáo soát prompt GHẺ 27A — structured-source audit

Verdict: **FAIL** — FAIL 3, CHƯA CHỐT 7, PASS 35. Exit 1.

Chỉ đọc cabin-map / global-context / spec / bible / ALH / prompt. Không sửa prompt, context, spec, ALH, PLAYBOOK, GPU-LOCK; không queue GPU. **Output là đề xuất** — reviewer sẽ đọc lại bằng tay 3 shot FAIL + 3 shot PASS trước khi tin.

## 1. cabin-map tự mâu thuẫn về bố cục ghế

Trạng thái: **CHƯA CHỐT** — E212-E214 accepted 3+3 invariant / E216 accepted 2+2 master; E231 (proposed) rewrote cabin-map to 1+1. No accepted event makes 1+1 authoritative, so the tool does not pick a winner.

| Nguồn | Status | Dòng gây lệch |
|---|---|---|
| cabin_geometry_contract.layout | map text | narrow-body single aisle, EXACTLY two rows (27 near the camera, 28 far) with ONE seat on each side of the aisle (1+1) in every row: four seats total; redesign approved by user 26/11, pending QA master r6 |
| cabin_geometry_contract.window_seats | map text | the outer seat on each side touches an oval window; seat 27A is the LEFT window seat |
| master_plate.invariants[0] | map text | exactly two rows (27 and 28) with four seats total, one seat on each side of the aisle in every row |
| master_plate.deviation_note | map text | 26/11/2026 user redesign: exactly two rows and four seats total, one seat per side (1+1). The former 3+3, five-row and 2+2-per-row conventions are retired; the old r4 master is missing on disk and r5/r5d/r5e are archived. Master r6 FAILED QA (3 rows x 4 seats, 8 windows, fixture at far end) and is … |
| generation_prompt_contract[6] | map text | Copy seat count, axis, window side and light values from master_plate / lighting_contract. Never hardcode a convention from memory: exactly two rows of 1+1 (four seats total) is canonical by user decision 26/11, pending QA master r6. A 2+2 reading would create eight seats and is FAIL under the new … |
| design_change_20261126 | map text | User approved exactly two rows / four seats (1+1 per row), a one-row four-figure generic crowd sheet composited into the three seats other than 27A, and Khang retained in 27A. The 2-row/4-seat label means 1+1, NOT 2+2; any prompt saying 2+2 or eight seats is FAIL. |
| E036 | archived | p3-chaos-flat was rendered top-down with horizontal seat rows, losing the narrow-body 3+3 aisle structure. Enforced cabin_geometry_contract in cabin-map.json: 3+3 seats, A=left window, front-near/tail-far, EYE-LEVEL view mandatory for all cabin plates incl. chaos/barricade. Regenerate at eye level. |
| E041 | archived | Master aisle plate r2 measured floor teal near-target 59.95% (was 3.3%), wall bone 25.83% and seat navy 34.62%; visually warm bone walls, broad teal floor, navy seats, 3+3 oval windows, eye-level. Accept as master; all variants must now reference THIS plate and only veil the image, not recolor obje… |
| E212 | accepted | Route-map 3D r1 is geometry authority for the whole G01-G04 rebuild, but Hy4 description-only QA found 1+1 seats per row and only one visible window wall instead of the cabin-map invariant 3+3 (A-B-C/D-E-F, 27A left window, oval windows both sides). Recorded FAIL/PARTIAL, never use as plate ref. r2… |
| E213 | accepted | Route-map 3D r2 still rendered 1+1 seats and one window wall after an explicit 3+3 prompt; the wrong-count r1 placed first in refs anchored the geometry. Recorded FAIL/PARTIAL. Rule: for a derived reference, order refs by which one owns the invariant - the QA-passed flat master must be Picture 1 fo… |
| E214 | accepted | User clarified the shared map is a full 3D draft of every nook the protagonist walks through. Three H3 Image attempts produced 1+1, 1+1 and 2+2 seats and only one window wall; 3+3 in a 3D cutaway was not achievable. Decision: scope the 3D map to ROUTE TOPOLOGY ONLY (route, cockpit/galley door, lava… |
| E216 | accepted | Master r4 PASS at plate level: horror contract met (mean 52.2, 54 pct machine shadow, Hy4 70-80 pct, both window walls, tail lavatory door, one fixture, no people/props/text/red/magenta, no 3D depth). Two deviations documented: 2+2 seats (G01-G04 never specify a count; 3+3 collapsed in four H3 atte… |
| E226 | proposed | Master r5b FAIL/PARTIAL attempt 2/3: 3+3 seats despite 2+2 contract. Fix only prompt layer with positive per-row count; last allowed attempt r5c with new seed. |
| E227 | proposed | Master r5c FAIL PARTIAL at attempt 3 of 3. Seats fixed to 2+2 but light contract and palette regressed: no visible emitting fixture, 44.1 percent machine shadow versus 60 to 75 contract, lavender wall and door, stray strokes near vanishing point. Retry cap reached; stop and ask user before any four… |
| E230 | proposed | User approved redesign: master shows exactly two rows of 2+2 seats; generic background passengers are one sheet of four distinct figures in a single row composited into the three seats other than 27A; 27A stays reserved for Khang so G03 action is unchanged. Crowd sheet is a documented waiver of one… |
| E231 | proposed | E231: user label 2 rows (4 seats) means 1+1 per row, not 2+2. Corrected cabin-map master/geometry/contract before any r6 prompt was emitted; generalized seat gate to compare every N+M pair. |
| E237 | proposed | r6 master FAIL/PARTIAL under 5-retry override (6th image): Hy4 3 rounds saw 3 rows x 4 seats (2+2)=12 and 8 oval windows, fixture far not near; machine gate PASS and prompt/map correct, root cause H3 generative drift; retry cap reached, stop and ask user with evidence. |

## 2. Ma trận shot × chiều (theo set_id)

### set_id: `aisle`

| Shot | layout_seat | light_tier | sightline | palette_hex | props_state | character_wardrobe | language_negation | timecode_duration | refs |
|---|---|---|---|---|---|---|---|---|---|
| G01 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
### set_id: `aisle_flat`

| Shot | layout_seat | light_tier | sightline | palette_hex | props_state | character_wardrobe | language_negation | timecode_duration | refs |
|---|---|---|---|---|---|---|---|---|---|
| G02 | CHƯA CHỐT | PASS | FAIL | PASS | PASS | CHƯA CHỐT | CHƯA CHỐT | PASS | PASS |
### set_id: `seat_27a`

| Shot | layout_seat | light_tier | sightline | palette_hex | props_state | character_wardrobe | language_negation | timecode_duration | refs |
|---|---|---|---|---|---|---|---|---|---|
| G03 | CHƯA CHỐT | PASS | FAIL | PASS | PASS | PASS | CHƯA CHỐT | PASS | PASS |
### set_id: `phone_ins`

| Shot | layout_seat | light_tier | sightline | palette_hex | props_state | character_wardrobe | language_negation | timecode_duration | refs |
|---|---|---|---|---|---|---|---|---|---|
| G04 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
### set_id: `seat_27a`

| Shot | layout_seat | light_tier | sightline | palette_hex | props_state | character_wardrobe | language_negation | timecode_duration | refs |
|---|---|---|---|---|---|---|---|---|---|
| G05 | CHƯA CHỐT | PASS | FAIL | PASS | PASS | PASS | CHƯA CHỐT | PASS | PASS |

## 3. FAIL + CHƯA CHỐT kèm trích dòng

### G02 — `aisle_flat`
- **layout_seat: CHƯA CHỐT** — Prompt asserts 1+1; map invariant_architecture[0] = 'exactly two rows (27 and 28) with four seats total, 1+1 per row'. E212-E214 accepted 3+3 invariant / E216 accepted 2+2 master; E231 (proposed) rewrote cabin-map to 1+1. No accepted event makes 1+1 authoritative, so the tool does not pick a winner.
  - `prompt.contract`: “Cabin rows hold 1+1 seats”
  - `cabin-map.invariant_architecture[0]`: “exactly two rows (27 and 28) with four seats total, 1+1 per row”
  - `E231 (proposed)`: “E231: user label 2 rows (4 seats) means 1+1 per row, not 2+2. Corrected cabin-map master/geometry/contract before any r6 prompt was emitted; generali…”
  - ghi chú: 27A left-window source: cabin-map.cabin_geometry_contract.window_seats='the outer seat on each side touches an oval window; seat 27A is the LEFT window seat'; prompt says 'left window seat 27A'=True
- **sightline: FAIL** — Map requires: aisle_direction='one aisle down the middle; front/galley is NEAR the camera, tail/lavatory is FAR; never flip this axis', eye_level='standing eye level for wide/aisle plates; the aisle stays centered and continuous across every plate', set.camera_height='standing eye level for wide/aisle plates; the aisle stays centered and continuo…'. Prompt omits: camera eye level
  - `prompt.camera_sentence`: “wide shot, camera held at one fixed scale and framing from the first frame to the last frame”
  - `prompt.Scene`: “one continuous narrow-body passenger cabin aisle, front near the camera and tail far away, exactly rows 27 and 28 with one seat per side (1+1, four seats total), plain solid oval windows, c…”
  - `cabin-map.eye_level`: “standing eye level for wide/aisle plates; the aisle stays centered and continuous across every plate”
  - ghi chú: 27A description in prompt = 'Scene: one continuous narrow-body passenger cabin aisle, front near the camera and tail far away, exactly row…'
- **character_wardrobe: CHƯA CHỐT** — Prompt names Khang but spec.layers and context.characters are empty; there is no structured wardrobe source to compare against.
  - `prompt.body`: “wide shot, camera held at one fixed scale and framing from the first frame to the last frame. Scene: one continuous narrow-body passenger cabin aisle, front near the camera and tail far awa…”
  - `spec.layers`: “[]”
  - `global-context.shots.G02.characters`: “[]”
  - ghi chú: no FAIL: source missing, not a proven prompt contradiction
- **language_negation: CHƯA CHỐT** — cabin-map.generation_prompt_contract forbids object-deletion negation, but accepted E273 explicitly added this row/window denial to the same shot contract. Two accepted rules conflict; the tool does not pick one.
  - `prompt.contract`: “no receding extra rows”
  - `cabin-map.generation_prompt_contract`: “Do not delete an object with a negation. Describe the intended object count and placement positively; keep forbidden facts in this map for QA only.”
  - `ALH E273 (accepted)`: “G02 v1 (seed 20263301) FAIL with evidence-backed style-contract breach, first G02 attempt so not a recurring fail chain. E234 trace full path: spec/map/bible = art/part1-spec.json G02 (wide…”
  - `ALH E162 (accepted)`: “Xoa moi cau xoa doi tuong khoi prompt_visible: ACTION_OVERRIDE BEAT_OVERRIDE cabin-map scene objects va light. Thay bang noi dung khung khang dinh. Identity/style negations tu bible nhu Nev…”
  - ghi chú: style negations (no gradient/no 3D) are allowed by the skills

### G03 — `seat_27a`
- **layout_seat: CHƯA CHỐT** — Prompt asserts 1+1; map invariant_architecture[0] = 'exactly two rows (27 and 28) with four seats total, 1+1 per row'. E212-E214 accepted 3+3 invariant / E216 accepted 2+2 master; E231 (proposed) rewrote cabin-map to 1+1. No accepted event makes 1+1 authoritative, so the tool does not pick a winner.
  - `prompt.contract`: “Cabin rows hold 1+1 seats”
  - `cabin-map.invariant_architecture[0]`: “exactly two rows (27 and 28) with four seats total, 1+1 per row”
  - `E231 (proposed)`: “E231: user label 2 rows (4 seats) means 1+1 per row, not 2+2. Corrected cabin-map master/geometry/contract before any r6 prompt was emitted; generali…”
  - ghi chú: 27A left-window source: cabin-map.cabin_geometry_contract.window_seats='the outer seat on each side touches an oval window; seat 27A is the LEFT window seat'; prompt says 'left window seat 27A'=False
- **sightline: FAIL** — Map requires: aisle_direction='one aisle down the middle; front/galley is NEAR the camera, tail/lavatory is FAR; never flip this axis', eye_level='standing eye level for wide/aisle plates; the aisle stays centered and continuous across every plate', set.camera_height='level with a seated passenger'. Prompt omits: camera eye level
  - `prompt.camera_sentence`: “medium shot, camera held at one fixed scale and framing from the first frame to the last frame”
  - `prompt.Scene`: “one continuous narrow-body passenger cabin aisle, front near the camera and tail far away, exactly rows 27 and 28 with one seat per side (1+1, four seats total), plain solid oval windows, c…”
  - `cabin-map.eye_level`: “standing eye level for wide/aisle plates; the aisle stays centered and continuous across every plate”
  - `global-context.sets.seat_27a.camera_height`: “level with a seated passenger”
  - ghi chú: 27A description in prompt = 'Medium view of the same two rows 27 and 28: Khang is ALREADY slumped asleep in seat 27A from the first frame,…'
- **language_negation: CHƯA CHỐT** — cabin-map.generation_prompt_contract forbids object-deletion negation, but accepted E273 explicitly added this row/window denial to the same shot contract. Two accepted rules conflict; the tool does not pick one.
  - `prompt.contract`: “no receding extra rows”
  - `cabin-map.generation_prompt_contract`: “Do not delete an object with a negation. Describe the intended object count and placement positively; keep forbidden facts in this map for QA only.”
  - `ALH E273 (accepted)`: “G02 v1 (seed 20263301) FAIL with evidence-backed style-contract breach, first G02 attempt so not a recurring fail chain. E234 trace full path: spec/map/bible = art/part1-spec.json G02 (wide…”
  - `ALH E162 (accepted)`: “Xoa moi cau xoa doi tuong khoi prompt_visible: ACTION_OVERRIDE BEAT_OVERRIDE cabin-map scene objects va light. Thay bang noi dung khung khang dinh. Identity/style negations tu bible nhu Nev…”
  - ghi chú: style negations (no gradient/no 3D) are allowed by the skills

### G05 — `seat_27a`
- **layout_seat: CHƯA CHỐT** — Prompt asserts 1+1; map invariant_architecture[0] = 'exactly two rows (27 and 28) with four seats total, 1+1 per row'. E212-E214 accepted 3+3 invariant / E216 accepted 2+2 master; E231 (proposed) rewrote cabin-map to 1+1. No accepted event makes 1+1 authoritative, so the tool does not pick a winner.
  - `prompt.contract`: “Cabin rows hold 1+1 seats”
  - `cabin-map.invariant_architecture[0]`: “exactly two rows (27 and 28) with four seats total, 1+1 per row”
  - `E231 (proposed)`: “E231: user label 2 rows (4 seats) means 1+1 per row, not 2+2. Corrected cabin-map master/geometry/contract before any r6 prompt was emitted; generali…”
  - ghi chú: 27A left-window source: cabin-map.cabin_geometry_contract.window_seats='the outer seat on each side touches an oval window; seat 27A is the LEFT window seat'; prompt says 'left window seat 27A'=False
- **sightline: FAIL** — Map requires: aisle_direction='one aisle down the middle; front/galley is NEAR the camera, tail/lavatory is FAR; never flip this axis', eye_level='standing eye level for wide/aisle plates; the aisle stays centered and continuous across every plate', set.camera_height='level with a seated passenger'. Prompt omits: camera eye level
  - `prompt.camera_sentence`: “medium shot, camera slow push-in of about 3% over the shot, with a faint handheld sway”
  - `prompt.Scene`: “one continuous narrow-body passenger cabin aisle, front near the camera and tail far away, exactly rows 27 and 28 with one seat per side (1+1, four seats total), plain solid oval windows, c…”
  - `cabin-map.eye_level`: “standing eye level for wide/aisle plates; the aisle stays centered and continuous across every plate”
  - `global-context.sets.seat_27a.camera_height`: “level with a seated passenger”
  - ghi chú: 27A description in prompt = 'Medium view of the same two rows 27 and 28: Khang lifts the bowed head in seat 27A and opens two dot eyes abr…'
- **language_negation: CHƯA CHỐT** — cabin-map.generation_prompt_contract forbids object-deletion negation, but accepted E273 explicitly added this row/window denial to the same shot contract. Two accepted rules conflict; the tool does not pick one.
  - `prompt.contract`: “no receding extra rows”
  - `cabin-map.generation_prompt_contract`: “Do not delete an object with a negation. Describe the intended object count and placement positively; keep forbidden facts in this map for QA only.”
  - `ALH E273 (accepted)`: “G02 v1 (seed 20263301) FAIL with evidence-backed style-contract breach, first G02 attempt so not a recurring fail chain. E234 trace full path: spec/map/bible = art/part1-spec.json G02 (wide…”
  - `ALH E162 (accepted)`: “Xoa moi cau xoa doi tuong khoi prompt_visible: ACTION_OVERRIDE BEAT_OVERRIDE cabin-map scene objects va light. Thay bang noi dung khung khang dinh. Identity/style negations tu bible nhu Nev…”
  - ghi chú: style negations (no gradient/no 3D) are allowed by the skills

## 4. Dải luma cho phép

- dim_night_flight: E045 mean_luma 39.2 (archived baseline) → E216 mean 52.2 (accepted master r4) = band [39.2, 52.2]. Prompt không mang số luma; đây là metadata QA plate.
- state_chain: chaos keeps cups/scraps/bags + dark-red stains; barricade keeps the SAME bags piled into overturned carts (no new cart design). No audited shot is a chaos/barricade variant, so the inheritance check is N/A here but remains a hard gate for part2/3 variants.
