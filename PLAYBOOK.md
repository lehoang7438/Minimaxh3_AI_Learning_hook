# PLAYBOOK GHẺ 27A — playbook tái dùng (chỉ mục, không phải luật gốc)

**Mục đích:** một nơi nhìn nhanh toàn bộ rule đang active trước khi sửa prompt / queue H3 / QA / ghi ALH.
**Phạm vi hiện tại:** chain **G01 → G02 → G03 → G05** (4 shot đang làm, đường H3 story-chain).
**Nguồn truth theo thứ tự:** `art/partN-spec.json` + `art/env/cabin-map.json` + `characters.json`
→ skill (SKILL.md) → ALH (`learning-log.jsonl` / `REPORT.md`) → QA (máy + Hy4 + agent chốt).
`global-context*.json` là **output**, không bao giờ làm nguồn prompt.

> **Trạng thái ALH (REPORT.md 27/11):** 281 event — 128 accepted / 100 archived / 49 proposed / 4 revoked.
> Accepted = **đang áp dụng**, nhưng **rule chỉ thành hard gate sau khi mirror vào SKILL.md / GLOBAL-RULES.md**;
> **99 accepted chưa mirror** (liệt kê mục "Accepted but not promoted" trong REPORT.md). Playbook này
> **không promote** rule nào — nó chỉ trỏ tới rule đã có bằng chứng.

---

## 1. Sơ đồ 3 tầng + sửa đúng 1 lớp

| Tầng | Là gì | Nguồn |
|---|---|---|
| 1 — Spec/context | sự kiện, hành động, thoại, hình học cabin (số ghế/trục/cửa sổ/ánh sáng), wardrobe, prop-state, duration | spec + cabin-map + bible + ledger; xung đột → **DỪNG, hỏi user**, không tự viết số vào prompt |
| 2 — Skill | prompt + workflow + asset: ép thứ tự field, lint, preflight, gate asset, 1 job/lần | 5 skill bắt buộc (bảng §2) |
| 3 — QA | `visual_qa.py` / `diagnose_shot.ps1` → Hy4 read-only → **agent tự chốt** | `visible_check=seen` + `script_fidelity=MET` mới PASS; cấm `PASS_WITH_WARN` |

**FAIL → E234:** truy ngược *nguồn → composer/prompt → workflow/node → gate → file trên đĩa → log* rồi mới hỏi user.
Chỉ hỏi khi **đã có bằng chứng + kết luận** hoặc **chạm trần retry**. Không hỏi ở lỗi đầu tiên, không sửa mù,
không retry cùng seed. Sửa **đúng 1 lớp** (asset → H3 Image; prompt → rebuild_prompts/context; workflow → node;
gate PASS mà video vẫn sai → đổi anchor/ref/seed) rồi render lại **chính shot đó**. **Không vá video bằng code,
không vẽ/keyframe bằng PIL, không hand-patch frame.**

---

## 2. 5 skill bắt buộc — load bằng tool `skill`, script không tự vào context

| Skill | Load khi | Đầu ra cụ thể (đường dẫn từ project root) |
|---|---|---|
| `comfyui-runner` | sửa workflow / queue / decode `node_errors` | 1 workflow API `art/comfy/chain4/h3-chain4.json`; `art/comfy/scripts/preflight_workflow.py`; `.opencode/skills/comfyui-runner/scripts/queue_prompt.ps1` |
| `h3-prompt-writing` | viết/đưa prompt H3 vào render | `art/tests/rebuild_prompts.py` → `prompts/part1-rebuilt/<Gxx>.txt`; style contract lấy từ `art/tests/h3_prompt_rules.py` |
| `h3-prompt-linter` | sau khi viết prompt, trước queue | `.opencode/skills/h3-prompt-linter/scripts/lint_h3.ps1 -FailOnWarn` + `validate_prompt()` lúc ghi file |
| `character-bible` | nhân vật định kỳ / identity | `characters.json` (appearance + wardrobe/upper_wardrobe, qa_passed, color_count); ref canon từ G02 |
| `asset-qa` | ngay sau **mỗi** asset gen | `story_to_asset_prompts.py` → `check_asset_prompt.py <job>` → `gen_image.py` (1 job) → QA ngay: size/panel/bible/script fidelity |
| `h3-visual-qa` (6 cột, bắt buộc thứ 4) | kiểm keyframe + clip | pass 1 `.opencode/skills/h3-visual-qa/scripts/visual_qa.py`; pass 2 `build_review_grid.py` **đọc grid bằng mắt**; clip: `diagnose_shot.ps1` + first/mid/last |

`freevideo-runner` dùng khi cần `fv.ps1 doctor/plan/submit/wait/download` (không bắt buộc nhưng `doctor`
là cổng cứng trước mỗi job). Mọi file/script mới phải trả lời *"nó vào node/input nào của H3?"* — nếu không, đừng tạo.

---

## 3. Checklist trước khi queue (copy và tick)

- [ ] `powershell -File .opencode\skills\freevideo-runner\scripts\fv.ps1 doctor` → **GO**, queue idle, không job ảnh nào đang chạy.
- [ ] **1 workflow duy nhất** `art/comfy/chain4/h3-chain4.json` (node 1 `FreeVideoMedia` = `"[]"` trừ khi có ref; node 2 `FreeVideoGenerate`: `text={{PROMPT}}, width=704, height=1280, seed, seconds, continue_from`). Không clone theo shot, không tự bật `python main.py`, không queue bằng browser.
- [ ] Prompt rebuilt, lint **PASS + 0 warning** đúng `-Seconds` của shot (`-Mode base -FailOnWarn`); style contract ở đầu `integrated_multimodal_description`, trước `[Shot 1]`.
- [ ] `preflight_workflow.py art\comfy\chain4\h3-chain4.json` = exit 0; `audit_refs.py` 0 hard; refs `qa_passed=True`, không `superseded`.
- [ ] Frame grid 24 fps (`17k+5`): **6 s = 158 frames (6.583 s thực)**, **8 s = 192**, 10 s = 243. So duration với mốc thực ±0.5 s.
- [ ] Canvas **704×1280**; `upscale_factor:"2"` = *no upscale* (không phải 1408×2560).
- [ ] `art/comfy/GPU-LOCK.json` một owner (`asset` hoặc `video`); chỉ set `free` sau job kết thúc **và** verdict đã ghi ledger.
- [ ] `workflow_state.py --check` sạch; ALH state fresh; không chốt verdict / không sleep khi QA shot hiện tại chưa xong.
- [ ] Download lỗi `IOException` do file mp4 bị app khác giữ → đọc `/history/<job_id>`, tải `/view` sang tên `-v2`, measure + copy handoff; **không queue lại GPU** (E282 proposed).

---

## 4. Rule prompt đang active — E267–E281 (có bằng chứng ALH)

Ghi chú trạng thái: **A** = accepted & đang áp dụng; chữ in nghiêng = chưa mirror SKILL.md. E278/E279 là bẫy, đọc kỹ.

| Event | Rule quyết định | Nơi áp dụng trong `art/tests/rebuild_prompts.py` | Status |
|---|---|---|---|
| **E267** | Dừng đổi từ/seed từng lần; review **hệ thống prompt**. Chuyển động mục tiêu: giật cổ tay + giật ngón tay, máu loang lổ. | định hướng sửa; sinh ra E268 | A |
| **E268** | `MOTION_MODE={'G01':'jerk'}` + `JERK_AMBIENCE` (đông cứng giữa các nhịp, **không** "continues evenly"); `BEAT_OVERRIDE['G01']` = 7 nhịp wrist/finger snap riêng biệt; `len(beats)` timecode tăng dần; máu = nhiều vệt đỏ sậm không đều; linter hard-FAIL nếu snap cổ tay/ngón tay lẫn drift even/slow/smooth. | `JERK_AMBIENCE` (~421), `MOTION_MODE` (~425), `BEAT_OVERRIDE['G01']` (~246) | A (E268 đã mirror vào h3-prompt-linter LEARNINGS) |
| **E270** | Thêm **1 cú lia ngang ngắn từ góc dưới ghế, scale không đổi**; giữ E268 + máu loang; **không** forward dolly, không tầm mắt hành khách, không asset mới, 1 render. | `UNDER_SEAT_PAN` (~401), `CAMERA_TEXT_OVERRIDE['G01']` (~413) | A |
| **E271** | Giao thức QA: nhớ yêu cầu user, dùng skill + ALH, QA kỹ, **auto-chốt PASS khi sạch**; chỉ hỏi khi FAIL có bằng chứng / mơ hồ / chạm ranh giới override. | quy trình QA, không phải hằng số | A |
| **E273** | G02 v1 FAIL gradient (46 % dark vs 60–75). Sửa đúng 1 lớp prompt: `G02_STYLE_CONTRACT` = **một tone phẳng cho mỗi bề mặt**, chỉ rows 27/28 + 4 cửa sổ, không grey ramp; `LIGHT_SUPPRESS` bỏ dòng `Light:` trùng. | `G02_STYLE_CONTRACT` (~71), `LIGHT_SUPPRESS` (~115) | A |
| **E274** | G02 v2 auto-PASS; ghế/cửa sổ lùi xa + tỉ lệ vùng sáng là **deviation được chấp nhận**, không FAIL thứ hai. | verdict, không đổi code | A |
| **E275** | **Pre-fix** G03/G05 trước render đầu: cùng plate 27A với G02 → áp ngay flat contract + `LIGHT_SUPPRESS`, khỏi tốn 2 job GPU phát hiện lại gradient. | `STYLE_OVERRIDE['G03'/'G05']`, `LIGHT_SUPPRESS` | A |
| **E276** | G03 PASS render đầu (đã bị E280 thay thế về trạng thái held-state; các phát hiện khác vẫn giữ). | verdict | A (superseded một phần bởi E280) |
| **E277** | Shot ngồi không được thừa beat đứng/đi và câu standing-pose của bible; G05 có 3 beat thức dậy khi ngồi + `SEATED_SHOTS` đổi câu tư thế. | `SEATED_SHOTS` (~428), `cast_appearance()` (~685) | A |
| **E278** | ❌ **ARCHIVED — ĐỪNG ÁP DỤNG LẠI.** Ép thứ tự awake→nod→đặt điện thoại là sai; user đã phủ nhận. | đã revert `ACTION_OVERRIDE`/`BEAT_OVERRIDE` | archived |
| **E279** | ❌ **REVOKED — ĐỪNG ÁP DỤNG.** G03 v1 vốn đúng script; E278 bị thu hồi, không re-render G03/G05 vì lý do này. | đã revert về dạng single-beat 2875 chars | revoked |
| **E280** | G03 = **held state**: đã gục ngủ từ frame 1, điện thoại **đã nằm trên đùi, không ai chạm**, màn hình tự sáng với 1 bánh sinh nhật được vây bởi ảnh nhóm. G05 Hy4 thấy eyebrows+mũi → `FACE_FLAT_CONTRACT` bỏ câu "tapered nose", thay bằng "exactly two dot eyes and one short mouth line and nothing else". | `ACTION_OVERRIDE['G03']` (~119), `BEAT_OVERRIDE['G03']` (~274), `FACE_FLAT_CONTRACT` (~104) | A |
| **E281** | **Duration fit action**: `DURATION_OVERRIDE={'G03':6.0,'G05':8.0}`; beat G03 dùng `{tc}` để không timecode nào vượt clip ngắn. G01 (7 snap) & G02 giữ 10 s. | `DURATION_OVERRIDE` (~462), `{tc}` trong beat (~272) | A |

Gợi ý chung vẫn sống trong SKILL.md: field 1 theo thứ tự *style → cỡ cảnh/camera → nhân vật+wardrobe → hành động+mặt đỡ → mood*;
cấm slug, cấm câu phủ định xoá vật/màu (E162/E200), `red_allowed=false` không nhắc đỏ, không path `.png` trong text (E226),
một câu text duy nhất cho UI shot, tiếng Việt chỉ trong `<d>...</d>`, frame 1 = mid-action.

---

## 5. Rule asset / visual QA (đo được + bằng mắt)

- **Flat 2D storytime horror v2:** solid fills, không gradient/shading/texture/3D; viền đen đậm không đều; palette navy / bone-white / **một** teal; đỏ chỉ blood/eyes/rec dot.
- **Mặt:** đúng 2 chấm mắt + 1 nét miệng; **không eyebrows, không mũi, không lashes** (E280 phát hiện G05 vi phạm). Tay: mitten/không ngón, trừ override G01 (`r8`: tay thật 4 ngón + móng đen, cuff navy rộng, máu đỏ sậm mọi vết cắn, teal 0).
- **G01–G05 cabin:** đúng **4 hành khách**, rows 27/28 (1+1), 4 ghế/4 cửa sổ; **teal chỉ ở thảm/tường/áo 27A**; **đỏ chỉ trong màn hình điện thoại/prop**, không đỏ lan.
- **Handoff:** G05 `continue_from` last-frame của G03; MAE G03_last→G05_first thấp (~1.8 là sạch); chain giữ trục 180°, prop-state, eyeline, relative_height.
- **Hy4 = mắt tai read-only**, tiếng Việt, **không verdict / không gợi ý fix**, kết thúc `Đã nhìn 1/1 ảnh`; hỏi nhiều vòng (mô tả tự do → vùng/đếm/tiếp xúc/viền/màu → mâu thuẫn thuật ngữ); agent đối chiếu từng câu + metric máy rồi mới chốt `MET|PARTIAL|MISSING`.
- Ngưỡng máy: character WARN >150 / FAIL >200; set plate WARN >300 / FAIL >450; prop WARN >250 / FAIL >400; ≥3 gutter full-frame = FAIL; `outfit` sai `wardrobe_id` = FAIL, thiếu = WARN.
- Asset lỗi logic → thêm **1 ref đúng đặc điểm đang drift**; lỗi style → nhắc lại cụm flat rồi gen lại **chính asset đó**; trần retry đọc từ `asset-contract.json`, chạm trần → dừng + ALH + hỏi user.

---

## 6. Vòng sản phẩm + ALH

`verdict → learn_hook.ps1 (ghi ngay tại cổng) → alh.py sync/verify → workflow_state.py --write/--check → WORKFLOW-INDEX note (3 dòng)`.

FAIL 1 lần → tự truy ngược E234 + sửa 1 lớp; **fail liên tiếp / new ambiguity / chạm retry-override → mới hỏi user**.
Chỉ user nâng `proposed → accepted`. Cuối phiên: `alh.py sync` + `verify = drift: none`. Nghi thức nhắc sau **mỗi** hoạt động:
`Vừa xong:` … / `Bước kế:` … / `ALH:` ….

---

## 7. Lệnh mẫu chain4 (chạy từ project root — **chỉ là mẫu**)

```powershell
# G03 — hard cut, 6s, seed 20263701 (ĐANG RENDER, chờ QA — không queue lại)
& ".\.venv-tts\Scripts\python.exe" art\tests\chain4_run.py --start 1 --shots 1 `
  --shot-ids G03 --seconds 6 --seed-base 20263700 `
  --chain-name story-g01 --outdir out/story-g01 --prompts prompts/part1-rebuilt

# G05 — 8s, continue_from last-frame G03 (CHỈ chạy SAU khi G03 QA PASS)
& ".\.venv-tts\Scripts\python.exe" art\tests\chain4_run.py --start 2 --shots 2 `
  --shot-ids G03,G05 --seconds 8 --seed-base <seed_mới> `
  --chain-name story-g01 --outdir out/story-g01 --prompts prompts/part1-rebuilt
# driver tự ghi node 2: continue_from=<G03.mp4>, seed=seed-base+segment, seconds; node 1 assets="[]" (không --ref-asset)
```

QA sau mỗi clip:

```powershell
& ".\.venv-tts\Scripts\python.exe" art\comfy\scripts\diagnose_shot.ps1 -Part part1 -Shot G03 -Video out\story-g01\G03\video.mp4
# trích first/mid/last + grid + probe 12 fps → Hy4 mô tả read-only → agent chốt → ghi review.json
powershell -NoProfile -ExecutionPolicy Bypass -File art\comfy\ALH\learn_hook.ps1 `
  -Event verdict -Shot G03 -Layer video -Detail '<1 câu>' -Skill h3-visual-qa -Part part1 -Status proposed -Actor agent
& '.\.venv-tts\Scripts\python.exe' art\comfy\ALH\alh.py sync
& '.\.venv-tts\Scripts\python.exe' art\comfy\ALH\alh.py verify
& '.\.venv-tts\Scripts\python.exe' art\tests\workflow_state.py --check
```

---

## 8. Trạng thái chain hiện tại (27/11 — không ghi verdict cho shot đang render)

| Shot | Trạng thái |
|---|---|
| **G01 v11** | PASS (E272, auto-chot theo E271). Cuff navy đọc ash-grey = **deviation đã chấp nhận** từ v10, không blocker. |
| **G02 v2** | PASS (E274, auto-chot). 2 deviation nhẹ: ghế/cửa sổ lùi xa, tỉ lệ vùng sáng phẳng. |
| **G03 v1** | Bị Hy4 re-QA bác: tay đưa điện thoại từ f003 (không phải held state). E280/E281 đã sửa prompt (held-state + face-flat + 6 s). **Seed 20263701, 6 s đang render nền — chờ QA, chưa có verdict.** |
| **G05 v1** | FAIL: eyebrows + mũi ở mid/last. Prompt đã face-flat (E280) + 8 s (E281). **Chưa queue — đợi G03 QA PASS rồi mới render 8 s `continue_from` last-frame G03 mới.** |

---

*Dùng playbook này như chỉ mục; luật gốc vẫn nằm trong SKILL.md + ALH accepted rules; mọi verdict ghi ALH + WORKFLOW-INDEX.*
