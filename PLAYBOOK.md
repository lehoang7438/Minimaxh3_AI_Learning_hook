# PLAYBOOK GHẺ 27A — playbook tái dùng (chỉ mục, không phải luật gốc)

**Mục đích:** một nơi nhìn nhanh toàn bộ rule đang active trước khi sửa prompt / queue H3 / QA / ghi ALH.
**Phạm vi hiện tại:** chain **G01 → G02 → G03 → G05** (4 shot đang làm, đường H3 story-chain).
**Nguồn truth theo thứ tự:** `art/partN-spec.json` + `art/env/cabin-map.json` + `characters.json`
→ skill (SKILL.md) → ALH (`learning-log.jsonl` / `REPORT.md`) → QA (máy + Hy4 + agent chốt).
`global-context*.json` là **output**, không bao giờ làm nguồn prompt.

> **Trạng thái ALH (REPORT.md 27/11):** 300 event — 140 accepted / 100 archived / 55 proposed / 5 revoked.
> Accepted = **đang áp dụng**, nhưng **rule chỉ thành hard gate sau khi mirror vào SKILL.md / GLOBAL-RULES.md**;
> **111 accepted chưa mirror** (liệt kê mục "Accepted but not promoted" trong REPORT.md). Playbook này
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
- [ ] **Chưa active — E282 đang `proposed`, chỉ áp dụng sau khi user nâng accepted:** download lỗi `IOException` do file mp4 bị app khác giữ → đọc `/history/<job_id>`, tải `/view` sang tên `-v2`, measure + copy handoff; **không queue lại GPU**.

---

## 4. Rule prompt đang active — E267–E300 (có bằng chứng ALH)

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
| **E281** | **Duration fit action**: beat dùng `{tc}` để không timecode nào vượt clip ngắn. G01 (7 snap) giữ 10 s; E285 sau đó rút G02 xuống 6 s. | `DURATION_OVERRIDE` (~466), `{tc}` trong beat | A |
| **E282** | Lỗi tải file mp4 bị app khác giữ → đọc `/history/<job_id>`, tải `/view` sang tên `-v2`, measure + copy handoff; **không queue lại GPU** (job đã success). | quy trình queue/download | proposed |
| **E283** | G03 v2 gradient trần/sàn nặng hơn baseline G02 v2 đã duyệt (tái phạm E273). Trigger = cụm "lights up / lit phone" kích H3 vẽ ánh sáng lan. Sửa 1 lớp prompt: "screen changes by itself from a plain pale rectangle to one flat picture", "cabin keeps its same one-tone surfaces". | `ACTION_OVERRIDE['G03']`, `BEAT_OVERRIDE['G03']` | A |
| **E284** | ❌ **REVOKED — ĐỪNG ÁP DỤNG.** Em đọc máy móc câu "tay rút xuống" và chấp nhận bàn tay trắng nổi bật; user phủ nhận vì thiếu logic kinh dị. Xem E285. | verdict cũ, đã thu hồi | revoked |
| **E285** | **Logic kinh dị > compliance chữ**: G02 là *hậu quả của G01*, không phải hoạt hình bàn tay biến mất. Cánh tay ma G01 vẫn nằm sâu dưới gầm 27A; chỉ một méo nhỏ màu xương bẩn + cuff xanh đen ló ra rồi rụt vào bóng tối, **không ai để ý**. View vẫn là view wide G02, lối đi đứng yên. Đây là dramatic irony: khán giả nhận ra, nhân vật thì không. | chỉnh `ACTION_OVERRIDE['G02']`, `BEAT_OVERRIDE['G02']`, `DURATION_OVERRIDE['G02']=6.0` | A |
| **E286** | Triển khai E285 đúng 1 lớp prompt: bỏ "bone-white hand", thêm "dirty dark-bone forearm / near-black nails / wide near-black navy cuff", "thin sliver ... peeks a little ... eases back", "nobody turns, looks down or reacts"; beat dùng `{tc}` (00:00.000/00:02.900/00:05.700). Rebuild 4175 chars, lint 6 s PASS 0 warning. G02 v2 bị supersede, chờ GPU rảnh để render lại. | `rebuild_prompts.py` G02 action/beats + duration | A |
| **E287** | G03 v3 gradient vẫn nặng hơn baseline dù đã bỏ "lights up" (so v2↔v3: nhẹ hơn nhưng cấu trúc không đổi). Trigger thật = dòng `Scene`: G02 phẳng có "plain solid oval windows + thin solid bone-white ceiling strip + flat muted-teal floor runner", G03 `seat_27a` chỉ có "dark night cabin + thin ceiling strip". Sửa 1 lớp prompt: `SCENE_OVERRIDE['G03']` mượn geometry/objects đã duyệt của G02 + điện thoại phẳng trên đùi. Rebuild 3591 chars, lint 6 s PASS. | `SCENE_OVERRIDE` (~117), `build_prompt` (~750) | A |
| **E288** | Pre-fix G05 theo E275: cùng plate 27A nên kế thừa `SCENE_OVERRIDE` phẳng và bỏ hẳn "lit phone / glows / still lit" trước render đầu. Rebuild 4559 chars, lint 8 s PASS 0 warning (00:00/00:03.900/00:07.700). | `SCENE_OVERRIDE['G05']`, `ACTION/BEAT_OVERRIDE['G05']` | A |
| **E289** | G01 v11 FAIL E270 theo user + Hy4: khung đứng yên, chỉ tay giật; "short lateral slide" bị H3 bỏ qua. Sửa 1 lớp prompt: 3 chỗ đều nói "one clear short sideways pan" + parallax "fixed jagged seat edge and dark floor gap travel visibly ... hand keeps its size", vẫn 7 nhịp jerk, không dolly. Rebuild 5097 chars, lint 10 s PASS 0 warning. E272 chỉ đúng phần jerk/blood, **verdict lia camera bị E289 thay thế**. | `G01_STYLE_CONTRACT`, `UNDER_SEAT_PAN`, `ACTION_OVERRIDE['G01']`, `JERK_AMBIENCE` | A |
| **E290** | Audit prompt phải so **prompt ↔ cabin-map/global-context** theo `set_id` bằng trường có cấu trúc (tier ánh sáng + dải luma, ghế 1+1/2+2/3+3, geometry/camera, hex, `state_chain` props, wardrobe/chân/tỉ lệ, rò rỉ tiếng Việt/phủ định) — không so prompt↔prompt bằng regex. Bố cục ghế đang mâu thuẫn across rules → báo **CHƯA CHỐT**, không tự chọn. Output Big Pickle phải đọc lại tay 3 FAIL + 3 PASS. | gate mới `prompt_consistency_audit.py` (Big Pickle dựng) | A |
| **E291** | G03 v4 FAIL lần 3 (seed 20264101, 6.58 s, job `fc194b2d…`): Hy4 so sánh trần/sàn với G02 baseline vẫn thấy quầng xám mềm + ramps teal xa điện thoại → E287 `SCENE_OVERRIDE` không đủ; thêm regression mới: hai tay mitten đỡ/cầm máy f01–f14 và đầu Khang ngẩng nhẹ f05–f08, phá E280/E281. Hai giả thuyết prompt-only đã cạn (E283, E287) → dừng, hỏi user theo E271 trước khi render hoặc đổi T2V/`continue_from`. | clip G03 v4 (không sửa prompt lúc này) | **P** |
| **E292** | Payload `/history` chứng minh **E287 bị bác**: Scene + Props flat-surface của G03 v4 **byte-identical** với G02 v2 đã duyệt (job `1005c5e3` ↔ `fc194b2d`); chỉ còn khác `wide→medium` và khối điện thoại đổi nội dung. Không viết lại Scene thêm lần nữa. | bằng chứng diff payload | **P** |
| **E293** | Reviewer đề xuất kiến trúc 3 lớp: 1 style contract duy nhất + 1 plate block theo `set_id` byte-identical giữa G02/G03/G05 + 1 shot block; linter cấm từ ánh sáng/nền trong shot block; audit cả clip rendered (60–75 % bóng phẳng, palette, số ghế/cửa sổ). Gom accepted rule thành danh sách ngắn + supersede trước khi mirror SKILL.md. | đề xuất, chờ user duyệt | **P** |
| **E294** | Sửa nhãn: E292 là phát hiện gradient payload-diff (text bên trong tự gọi nhầm là E293); E293 là kiến trúc 3 lớp. | ALH bookkeeping | A |
| **E295** | Audit Big Pickle đã đọc lại tay 3 FAIL + 3 PASS: đúng hết, nhưng sót G04 vẫn nói `2+2 seats` dù map/G02/G03/G05 dùng 1+1. PASS của model rẻ không phải bằng chứng. | `prompt-consistency-report.md` + đối chiếu file | A |
| **E296** | Payload `/history` loại thêm 3 giả thuyết gradient: Scene (v4 byte-identical G02 v2 vẫn FAIL), từ `lit/glowing` (G03 v1 và G05 v1 có mà không FAIL), medium/điện thoại (có ở v1/G05). Seed không tách được khi chưa render. Cấm viết lại Scene lần 5 hoặc đổi chữ sáng. | `g03-gradient-rootcause.md` | A |
| **E297** | Giả thuyết còn lại (**P**): phone **tĩnh** (v1/G05) ổn, phone **tự đổi/lên sáng** (v2 `lights up`, v3/v4 `changes by itself`) FAIL 3 lần → H3 đọc sự kiện đổi màn hình làm ánh sáng, tràn ramp lên trần/sàn xiên. E287 cũng gây regression tay bám máy/ngẩng đầu ở v4. Chờ user chọn đổi anchor/composition theo E271; GPU vẫn `qa_hold`. | đề xuất, chưa render | **P** |
| **E298** | Reviewer đính chính: kiến trúc 3 lớp tốt cho audit rẻ nhưng **không giải thích gradient** (block style đã byte-identical). Áp ngay các sửa không cần chờ: bỏ `composited later` khỏi global-context + rebuild source; `FACE_FLAT_CONTRACT` cho G02 v3; G04 dùng contract phẳng phone-ins bỏ 2+2/cửa sổ; chèn khối Khang vào G03; mắt trong khối G03/G05 đổi `oval`→`dot`. 5 prompt rebuild, lint PASS 0 warning. | reviewer + `rebuild_prompts.py` | A |
| **E299** | Cứng gate: `validate_prompt` + `lint_h3.ps1` hard-FAIL `composited`/`compositing stage`; audit FAIL cặp N+N trong `phone_ins` thay vì PASS vô điều kiện. Audit lại: FAIL 3 / CHƯA CHỐT 7 / PASS 35 (trước FAIL 6 / PASS 32). Còn FAIL sightline/camera-height, chờ quyết định ghế/độ cao. | gate + audit report | A |
| **E300** | Reviewer đề xuất (**P**, chưa áp): khai báo điện thoại là shape sáng thứ ba, đặt timecode đổi màn hình, bỏ `no hand touches it`, bỏ câu bốn cửa sổ khỏi G03/G05. Cùng chờ chốt: E231 vs E212/E213/E216/E230/E237; E273 có supersede E209 không; quyền accept của agent; spec 10s/action cũ. GPU vẫn `qa_hold`. | đề xuất, chờ user | **P** |

Gợi ý chung vẫn sống trong SKILL.md: field 1 theo thứ tự *style → cỡ cảnh/camera → nhân vật+wardrobe → hành động+mặt đỡ → mood*;
cấm slug, cấm câu phủ định xoá vật/màu (E162/E200), `red_allowed=false` không nhắc đỏ, không path `.png` trong text (E226),
một câu text duy nhất cho UI shot, tiếng Việt chỉ trong `<d>...</d>`, frame 1 = mid-action.

---

## 5. Rule asset / visual QA (đo được + bằng mắt)

- **Flat 2D storytime horror v2:** solid fills, không gradient/shading/texture/3D; viền đen đậm không đều; palette navy / bone-white / **một** teal; đỏ chỉ blood/eyes/rec dot.
- **Mặt:** đúng 2 chấm mắt + 1 nét miệng; **không eyebrows, không mũi, không lashes** (E280 phát hiện G05 vi phạm). Tay: mitten/không ngón, trừ override G01 (`r8`: tay thật 4 ngón + móng đen, cuff navy rộng, máu đỏ sậm mọi vết cắn, teal 0).
- **G02/G03/G05 cabin (không áp cho G01 under-seat insert, E248):** đúng **4 hành khách**, rows 27/28 (1+1 theo cabin-map, nhưng E230/E231/E237 vẫn `proposed` → audit báo CHƯA CHỐT), 4 ghế/4 cửa sổ; **teal chỉ ở thảm/tường/áo 27A**; **đỏ chỉ trong màn hình điện thoại/prop**, không đỏ lan (quy tắc đỏ toàn cục vẫn là blood/infected eyes/recording dot).
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
# G03 v3 — hard cut, 6s, seed 20263901 (ĐÃ render, đang QA — không queue lại)
& ".\.venv-tts\Scripts\python.exe" art\tests\chain4_run.py --shots 1 `
  --shot-ids G03 --seconds 6 --seed-base 20263900 `
  --chain-name story-g01 --outdir out/story-g01-r3 --prompts prompts/part1-rebuilt

# G02 v3 — E285 horror logic, 6s, seed mới (CHỈ queue sau khi G03 v3 QA xong)
& ".\.venv-tts\Scripts\python.exe" art\tests\chain4_run.py --shots 1 `
  --shot-ids G02 --seconds 6 --seed-base <seed_mới> `
  --chain-name story-g01 --outdir out/story-g02-v3 --prompts prompts/part1-rebuilt

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
| **G01 v11** | E272 PASS chỉ cho jerk/blood; **phần lia camera bị user + Hy4 bác (E289)**: khung đứng yên. Prompt đã sửa (5097 chars, lint 10 s PASS), **chưa render v12 — đợi user chốt hướng G03 (E291) rồi queue seed mới kèm r8**. |
| **G02 v2** | Bị user phủ nhận (E285): đúng chữ nhưng sai logic kinh dị — bàn tay trắng nổi bật, không phải cánh tay ma G01 ló nhẹ dưới gầm. E284 đã revoked. Prompt đã sửa (E286), 6 s, **chưa render lại — đợi GPU rảnh**. |
| **G03 v2** | Held-state đúng nhưng gradient trần/sàn nặng hơn baseline G02 → tái phạm E273 (E283). Backup `video-v2-gradient-fail.mp4`. |
| **G03 v3** | Seed 20263901, 6 s: held-state sạch nhưng trần/sàn vẫn gradient nặng hơn G02 → E273 tái phạm lần 2; E287 sửa dòng Scene. |
| **G03 v4** | Seed 20264101, 6.58 s, `SCENE_OVERRIDE` phẳng: **FAIL lần 3 (E291)** — trần vẫn quầng xám mềm, sàn vẫn ramp teal xa máy; hai tay cầm máy + đầu ngẩng nhẹ. `GPU-LOCK = qa_hold`, **chờ user chọn** (a) anchor ref G02 / (b) `continue_from` G02 / (c) thêm 1 pass prompt + seed mới. |
| **G05** | v1 FAIL eyebrows + mũi (E280). Prompt đã face-flat + 8 s + `SCENE_OVERRIDE` + bỏ light wording (E288), lint PASS. **Chưa queue — đợi user chốt hướng G03 (E291) rồi mới render 8 s `continue_from` last-frame G03 mới.** |

---

*Dùng playbook này như chỉ mục; luật gốc vẫn nằm trong SKILL.md + ALH accepted rules; mọi verdict ghi ALH + WORKFLOW-INDEX.*
