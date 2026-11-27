# CONDENSED RULES DRAFT — GHẺ 27A (chỉ để user review)

**Bản nháp, read-only.** Không mirror vào SKILL.md / GLOBAL-RULES.md / PLAYBOOK.md / LEARNINGS.md;
không queue, không đổi GPU-LOCK, không chốt verdict.
Nguồn duy nhất: `art/comfy/ALH/learning-log.jsonl` (297 event; 138 accepted / 100 archived /
54 proposed / 5 revoked) + `REPORT.md` + `PLAYBOOK.md` (đọc để đối chiếu, không sao chép luật cũ).

- **39 condensed rules**, chỉ gom event `status=accepted`; `proposed` nằm riêng ở mục cuối.
- **Accepted events represented: 138/138 — không represented: 0.**
- Các event verdict/one-off được gom làm bằng chứng cho rule tương ứng, không tách thành rule mới.
- `supersedes:` chỉ ghi khi rule condensed này override accepted ID cũ; override revoked/proposed được ghi chú trong ngoặc.
- Mọi ID trích dẫn đều có trong log; không suy diễn rule mới.

---

## 1. QA / retry / verdict protocol

### Q1. Trace_FAIL_end_to_end
- Rule: Trace mọi FAIL/blocker từ story→map→rule/composer→ref/QA ledger→workflow→seed/anchor→file/log, ghi ALH, chỉ hỏi user khi có bằng chứng hoặc chạm retry cap.
- Sources: E234, E251, E260, E265, E269
- supersedes: —
- status_by: user (E234/E251/E269), agent (E260/E265)
- Scope/exceptions: mọi phase (asset, prompt, context, workflow, render, audio, assembly, QA, cleanup); E233/E238 là proposed, không áp.

### Q2. No_batch_render
- Rule: Không batch-render; QA ngay sau mỗi clip, ghi verdict xong mới queue shot kế; một job GPU tại một thời điểm.
- Sources: E146, E150, E152, E242, E285, E287
- supersedes: —
- status_by: user (E150/E242/E285), agent (E146/E152/E287)
- Scope/exceptions: toàn pipeline; E147/E244 (driver timeout/SIGTERM) xử lý riêng ở F4/F5.

### Q3. Auto_chot_pass_clean
- Rule: Tự chốt PASS khi QA sạch; chỉ hỏi khi FAIL có bằng chứng, mơ hồ thật, hoặc chạm ranh giới override.
- Sources: E170, E271, E272, E274, E276
- supersedes: E274 (deviation chấp nhận) bị E285/E286 thu hẹp ở G02 — xem P6.
- status_by: user (E170/E271), agent (E272/E274/E276)
- Scope/exceptions: all QA; E291/E293/E297 đang proposed → không được dùng để mở lại QA đã chốt.

### Q4. Eyes_readonly_pinned
- Rule: Pin model Eyes (hy4-flash-free#high), yêu cầu `visible_check=seen`; Hy4 chỉ mô tả, agent chốt verdict/root_layer/fix; loại verdict từ subagent không pin model/không thấy ảnh.
- Sources: E134, E153, E158, E168, E169, E295
- supersedes: — (xem mâu thuẫn M1: E134 chọn reviewer khác E153)
- status_by: user (E168), agent (E134/E153/E158/E169/E295)
- Scope/exceptions: mọi asset/clip QA; E129 (Gemini-4-Argon) proposed, không áp.

### Q5. Machine_gate_not_evidence
- Rule: Machine gate PASS không thay mắt; color_count thấp không đảm bảo flat; audit của model rẻ chỉ là triage — đọc tay 3 FAIL + 3 PASS trước khi tin.
- Sources: E138, E158, E290, E295
- supersedes: —
- status_by: user (E290), agent (E138/E158/E295)
- Scope/exceptions: E138 timing check của `visual_qa.py` vẫn có giá trị trên đường H3; phần ASSETS/FRAMES cũ có false FAIL.

### Q6. Fix_one_layer_only
- Rule: Sửa đúng một lớp (asset / prompt / context / workflow / node / gate), render lại chính shot đó; không vá video bằng code, không vẽ keyframe bằng PIL; composite deterministic prop đã QA là staging, không phải asset mới.
- Sources: E139, E144, E148, E150, E152, E160, E172, E178, E206
- supersedes: —
- status_by: user (E150), agent (E139/E144/E148/E152/E160/E172/E178/E206)
- Scope/exceptions: E151 (cấm PIL/hand-patch) proposed; E139/E148 là ngoại lệ staging được phép.

### Q7. Retry_cap_override_discipline
- Rule: Chạm retry cap thì dừng GPU; chỉ render lại khi có override user mới, mỗi override = đúng 1 asset + 1 render seed mới; không regenerate khi chưa có override.
- Sources: E250, E251, E252, E260, E261, E263, E265, E266, E269
- supersedes: —
- status_by: user (E250/E251/E252/E261/E263/E266), agent (E260/E265/E269)
- Scope/exceptions: cap 3/3 từ asset-contract; phần lớn là G01 v4→v11; override v5–v9 đã tiêu, v10/v11 đã dùng; G03 `qa_hold` (E291 proposed) không phải override.

### Q8. Review_system_not_words
- Rule: Khi sửa mãi không khá, dừng đổi từ/seed; review hệ thống nguồn→composer→field order/weighting→lint→workflow rồi mới đề xuất fix; dùng payload `/history` làm bằng chứng.
- Sources: E251, E267, E268, E289, E296
- supersedes: —
- status_by: user (E251/E267), agent (E268/E289/E296)
- Scope/exceptions: E267 đặc thù chuyển động G01; E296 cấm viết lại Scene lần 5 / đổi chữ sáng khi đã có bằng chứng payload.

---

## 2. Prompt flatness / light / language

### P1. One_contract_at_head
- Rule: Chỉ một style contract, đặt đầu `integrated_multimodal_description` trước `[Shot 1]`; slice field tại `[Shot 1]`; suppress dòng `Light:` trùng từ global context.
- Sources: E099, E100, E176, E201, E273, E275, E288
- supersedes: E176 (amber restaurant accents áp mọi shot) và E209 (slate-wall/even-light wording) cho riêng G02/G03/G05; E100 > cơ chế prepend blob của context node.
- status_by: agent (E099/E100/E176/E201/E273/E275/E288)
- Scope/exceptions: contract UI G01 gộp "no text except timer 00:00" (E099); G02 đã PASS giữ nguyên contract của nó (E280).

### P2. Flat_one_tone_no_ramp
- Rule: Mỗi bề mặt một tone phẳng; cấm gradient/grey ramp/shading/soft shadow/3D/beam; 60–75 % near-black, vignette nặng, 1–2 fixture có động lực, tường slate sáng hơn ghế navy.
- Sources: E209, E215, E273, E274, E275, E283, E287, E288
- supersedes: E273/E275 > E176 + E209 light wording cho G02/G03/G05; E288 > E283 (từ "lights up/lit phone") và E287 (Scene line) — nhưng E296 đã bác cả hai giả thuyết, xem M3.
- status_by: user (E209), agent (E215/E273/E274/E275/E283/E287/E288)
- Scope/exceptions: E274 chấp nhận bright-area share 52.3 % nếu fill phẳng; E276 chấp nhận vignette falloff; đỏ chỉ trong phone screen (E276); G01 insert dùng contract riêng (E248).

### P3. No_deletion_negations
- Rule: Cấm câu phủ định xoá vật/màu trong `prompt_visible`; thay bằng nội dung khung khẳng định; giữ forbidden facts ở global-context để QA; khi `red_allowed=false` không nhắc chữ "red".
- Sources: E161, E162, E190, E200, E206
- supersedes: —
- status_by: agent (E161/E162/E190/E200/E206)
- Scope/exceptions: phủ định nhận dạng từ bible ("never a vest", "no eyebrows") vẫn được phép (E162); E148 override `RED_OVERRIDE[P3G12]=true` cho black-card.

### P4. English_outside_dialogue
- Rule: Tiếng Việt chỉ trong `<d>...</d>`; mood/action tiếng Anh; lint PASS 0 warning đúng `-Seconds` của shot.
- Sources: E099, E191, E201, E280, E281
- supersedes: —
- status_by: user (E280/E281), agent (E099/E191/E201)
- Scope/exceptions: E107 proposed báo 60/60 vẫn lọt tiếng Việt — chưa chốt; E201 chỉ áp G01–G04.

### P5. One_action_fit_duration
- Rule: Một prompt chỉ một hành động chính; chia sub-clip 3–4 s hoặc rút duration cho ít beat; beat dùng `{tc}` để không timecode nào vượt clip.
- Sources: E138, E171, E172, E281
- supersedes: —
- status_by: user (E171/E281), agent (E138/E172)
- Scope/exceptions: G03=6 s, G05=8 s; G01 7 snap và G02 hand-slip giữ 10 s (E281); E138 chỉnh G14 dialogue 8.0→5.0 s.

### P6. Horror_logic_over_literal
- Rule: Ưu tiên logic kinh dị hơn khớp chữ: G02 là hậu quả của G01 — cánh tay đã nằm sâu dưới 27A, chỉ ló méo rồi rụt lại, không ai phản ứng, view wide giữ nguyên.
- Sources: E128, E285, E286
- supersedes: E274 (chấp nhận bàn tay trắng hand-slip) bị E285/E286 thay thế; E284 revoked.
- status_by: user (E128/E285), agent (E286)
- Scope/exceptions: G02 only; không đổi G01/G03/G05 vì event này.

### P7. Insert_no_face_no_priming
- Rule: Shot insert/POV/characterless không priming passengers/face; dùng positive cast-count lock; shot ngồi không thừa beat đứng/đi; empty-panel dùng beat khẳng định riêng.
- Sources: E136, E156, E159, E248, E268, E277, E295
- supersedes: E248 > E182/E204 (revoked) cho G01 under-seat; E277 > standing-pose sentence của bible cho G05.
- status_by: user (E248), agent (E136/E156/E159/E268/E277/E295)
- Scope/exceptions: G01 under-seat insert không binding bởi rule 4 hành khách cabin (E295); POV/freeze `CAST_OVERRIDE=[]` (E159); G05 seated beats only.

---

## 3. Camera / motion / chain

### C1. One_camera_instruction
- Rule: Mỗi prompt chỉ một lệnh camera; khi script khóa khung thì giữ một scale tuyệt đối; xoá mọi drift/push-in/sway trùng ở beat, tail và feeder.
- Sources: E172, E178, E179, E180, E191, E289
- supersedes: E179/E180 > prompt 3 lệnh camera của E178; E289 > E270 (lateral slide quá yếu); E180 > first_line của feed_h3_context.
- status_by: agent (E172/E178/E179/E180/E191/E289)
- Scope/exceptions: E270/E289 là override G01; G02–G04 giữ nguyên khi sửa G01 (E179).

### C2. G01_under_seat_camera
- Rule: G01 mở ngay trong khe tối dưới ghế, camera lia trong khe, không lia từ tầm hành khách, không vật lôi từ mép phải; cánh tay đã bị cắn từ frame 1 và giật ngắn.
- Sources: E245, E246, E247, E248, E270
- supersedes: E248 > E182/E204 (revoked) — bỏ priming cabin rows/oval windows/figure cho G01.
- status_by: user (E245/E246/E247/E248/E270)
- Scope/exceptions: G01 only; contract riêng G01 (không dùng contract 4 passenger).

### C3. G01_parallax_pan
- Rule: Lia ngang G01 phải có vật cố định làm mốc (jagged seat edge + floor gap) di chuyển rõ trong khi bàn tay giữ nguyên kích thước; không dolly/phóng to, không tầm ngồi.
- Sources: E270, E272, E289
- supersedes: E289 > verdict lia của E272 (E272 chỉ đúng phần jerk/blood); E272 ghi nhận grey cuff residual là accepted deviation.
- status_by: user (E270), agent (E272/E289)
- Scope/exceptions: G01 only; verify bằng red centroid/bbox-height slope (E272) chứ không bằng FFT thô (E289).

### C4. Frame1_and_continue_from
- Rule: Frame 1 phải là plate phẳng đã QA được node tiêu thụ thật; nếu keyed sheet chiếm frame 1 thì plate-only media + câu "start from supplied first-frame image"; `continue_from` chỉ nối hành động liên tục, không nối qua cú cắt.
- Sources: E092, E093, E095, E096, E141, E144, E145, E157, E174, E203, E242, E244, E276
- supersedes: E141 > việc tin report `anchor=custom` mà node không đọc; E203 > PLATE_OVERRIDE chỉ set `shot.bg`.
- status_by: user (E174/E242), agent (E092/E093/E095/E096/E141/E144/E145/E157/E203/E244/E276)
- Scope/exceptions: INS/black-card cần plate riêng đã QA (E145/E148); chain4 replay chỉ rewrite `continue_from`+seed (E242); G05 tiếp last-frame G03 (E276).

---

## 4. Cabin geometry / seats

### G1. Flat_master_topology_only
- Rule: Cabin plate = một điểm nhìn, eye-level, lối đi giữa, front-near/tail-far, oval windows; dùng master phẳng đã QA làm form anchor; 3D route-map chỉ cung cấp topology dạng TEXT, không inject ảnh 3D vào plate phẳng.
- Sources: E190, E192, E210, E211, E212, E213, E214, E215, E217, E218
- supersedes: E215 > E214 (dùng ảnh 3D làm Picture 2 kéo 2+2 + gradient vào plate); E210 > PASS cũ của aisle-flat-r1 (far-end là tường tối).
- status_by: user (E210/E214), agent (E190/E192/E211/E212/E213/E215/E217/E218)
- Scope/exceptions: 3D map = route/cockpit/galley/lavatory only, out of scope seat count (E214); "cabin variant không prompt từ đầu" (E202) nằm ở A3.

### G2. Seat_layout_CHUA_CHOT
- Rule: Bố cục ghế CHƯA CHỐT (1+1 / 2+2 / 3+3): audit phải báo conflict, không tự chọn; G02/G03/G05 giữ 4 hành khách rows 27/28, count cố định frame 1→last.
- Sources: E212, E213, E214, E216, E217, E218, E239, E243, E274, E276, E290, E295
- supersedes: — (không override; E216/E217 2+2 PASS và E212–E214 3+3 invariant cùng accepted)
- status_by: user (E214/E239/E243/E290), agent (E212/E213/E216/E217/E218/E274/E276/E295)
- Scope/exceptions: part1 G01–G05; E230/E231/E237/E226/E227/E241 là proposed → không resolve; G04 vẫn nói 2+2 là lỗi đã ghi E295, không tự sửa trong bản này.

---

## 5. Wardrobe / identity

### W1. Distinct_wardrobe_verbatim
- Rule: Mỗi nhân vật có trang phục riêng biệt rõ (màu + kiểu), áo/quần/giày tách lớp; copy nguyên văn `wardrobe`/`upper_wardrobe` từ `characters.json`, không thêm tính từ, không gộp block navy đồng phục.
- Sources: E164, E165, E196, E197, E295
- supersedes: E196/E197 > bible cũ gộp chung navy; E197 >Negative-word priming ("mannequin/rigid/stiff") — dùng mô tả tích cực.
- status_by: user (E196/E197), agent (E164/E165/E295)
- Scope/exceptions: CU/INS dùng upper_wardrobe only; G03 missing wardrobe clause là TRUE FAIL đã ghi E295.

### W2. No_character_in_plate
- Rule: Không nhét nhân vật vào background plate; dùng canon single-view ref hoặc CAST_OVERRIDE; không đăng ký sheet 4 ô làm `characters[].ref` chỉ để tắt gate.
- Sources: E164, E165, E185, E194, E208
- supersedes: —
- status_by: user (E185/E194), agent (E164/E165/E208)
- Scope/exceptions: G03 `CAST_OVERRIDE=[]` + plate rỗng + appearance/wardrobe text (E208); plate đã bake hình thì empty injected cast (E156).

### W3. Turnaround_anchor_only
- Rule: 9 sheet turnaround 4 hướng = identity anchor: một hàng, cùng scale, chân cùng baseline, 1:6; không làm `<Picture N>` video, không qua keyer, nền bone-white được phép và miễn gate magenta cho riêng 9 sheet này.
- Sources: E183, E184, E185, E193, E194, E195, E197
- supersedes: E194 > magenta gate `R>=240/G<=40/B>=200` cho riêng turnaround; E195 > các seed có raspberry/3-4/chan chạm mép.
- status_by: user (E183/E184/E185/E194/E197), agent (E193/E195)
- Scope/exceptions: sprite ref đơn key trong video vẫn bắt buộc magenta gate (E194); canvas 2:1 + baseline nội bộ + head-lock (E195).

### W4. Dot_eyes_slim_identity
- Rule: Mặt = đúng 2 chấm mắt đặc + 1 nét miệng ngắn, không ring/pupil/lashes/mày/mũi; identity anchor phải kiểm body mass slim/narrow waist và không pivot-dot/seam; sửa bible trước khi regenerate job.
- Sources: E164, E193, E195, E198, E199, E248, E280
- supersedes: E198 > agent PASS của Vy turnaround (user override FAIL); E199 > cụm "subtle seams" trong bible; E280 > tapered-nose/no-eyebrows clause của G02 contract cho G03/G05.
- status_by: user (E198/E248/E280), agent (E164/E193/E195/E199)
- Scope/exceptions: đỏ chỉ cho mắt nhiễm (E193); G01 dùng real hand override nhưng mặt vẫn dot-eye (E248); FACE_FLAT_CONTRACT chỉ G03/G05 (E280).

---

## 6. Refs / assets

### A1. QA_each_asset_now
- Rule: QA ngay sau mỗi asset: size, panel/figure count, bible, script_fidelity; cấm PASS_WITH_WARN khi script state MISSING; FAIL → sửa đúng prompt/asset đó rồi mới sang asset kế.
- Sources: E126, E128, E169, E190, E193, E195, E256, E262, E264
- supersedes: E128 > verdict PASS_WITH_WARN của E126; E190/E193/E195 > PASS trước đó của master/turnaround.
- status_by: user (E128), agent (E126/E169/E190/E193/E195/E256/E262/E264)
- Scope/exceptions: PASS_WITH_WARN có warning đã ghi rõ (E256/E262/E264) được phép dùng làm `<Picture 1>` nếu core contract MET; verdict cuối vẫn là agent/user.

### A2. Magenta_key_gate
- Rule: Gate key = field đồng nhất, lấy median 4 góc, RGB-distance threshold 70, `R>=240, G<=40, B>=200`; không yêu cầu `B>=230`; key FAIL thì khôi phục wording "vivid bright saturated near-magenta matching RGB(255,0,255)" + đổi seed, không thêm channel minima số vào prompt.
- Sources: E083, E132, E133, E205
- supersedes: E132/E133 > rule `B>=230` cũ (E082 revoked); E205 > attempt thêm "R>=240 + BLUE AT LEAST 220" vào prompt.
- status_by: user (E132/E133/E205), agent (E083)
- Scope/exceptions: E083/E205 là evidence FAIL; turnaround 9 sheet được miễn (W3); keyer thực tế là corner-sampled, không absolute B.

### A3. No_variant_from_scratch
- Rule: Không gen cabin variant từ đầu; master QA-passed làm `<Picture 1>`, aisle làm `<Picture 2>` cho aisle form; ref xếp theo invariant owner; một plate phẳng QA cho mỗi set/shot_size.
- Sources: E154, E202, E212, E213, E216, E217, E218
- supersedes: E213 > ref order đặt route-map r1 sai lên đầu; E154 > plate legacy reuse.
- status_by: agent (E154/E202/E212/E213/E216/E217/E218)
- Scope/exceptions: E216 2+2 là deviation phải ghi cabin-map/ledger; E212–E214 3+3 conflict → CHƯA CHỐT (G2).

### A4. Prop_fix_at_source
- Rule: Prop lỗi thì sửa element/cabin-map, gen lại 1 ref, QA rồi đăng ký và wire `<Picture 1>` trước khi render; không tin prompt sửa mà bỏ qua ref.
- Sources: E219, E252, E256, E263, E264
- supersedes: E252 > ba retry prompt-only của G01 v4; E263 > E262 (pale teal trong notch).
- status_by: user (E252/E263), agent (E219/E256/E262/E264)
- Scope/exceptions: E219 phone-ins là prop PASS mẫu; E256/E264 là PASS_WITH_WARN được phép dùng; mỗi override chỉ 1 prop.

### A5. Asset_library_gates
- Rule: Chỉ xoá asset cũ sau user approve; gen revision mới seed mới, giữ file cũ; ref mới phải vào workflow và qua audit trước queue; dry-run cleanup bắt buộc trước cleanup thật.
- Sources: E139, E148, E181, E185, E189, E192, E195
- supersedes: E189 > trạng thái "chưa xoá" của E181; E185 > ref chỉ nằm trong bible mà không vào node.
- status_by: user (E181/E185/E189), agent (E139/E148/E192/E195)
- Scope/exceptions: E139/E148 deterministic composite là staging của asset đã QA, không phải gen asset mới; 145 file/396 MB đã xoá theo E189.

### A6. G01_bite_prop_final
- Rule: G01 dùng tay thật flat-2D: ngón cái + 4 ngón riêng, móng near-black, một tone bone bẩn đồng nhất, cuff navy rộng gần đen, vết cắn ragged, mọi notch chỉ đỏ sậm, không teal; dùng `r8` làm `<Picture 1>`, không regenerate khi chưa có override mới.
- Sources: E133, E188, E248, E254, E257, E258, E259, E261, E262, E263, E264, E265, E266, E272
- supersedes: E257/E258 > E248/E133 (mitten một khối) **cho riêng G01**; E261 > E260 (cuff silver); E263 > E262 (teal notch); E266/E272 > E265 (camera khoá làm chết motion); bible "hands are mittens" giữ nguyên ngoài G01.
- status_by: user (E248/E254/E257/E258/E261/E263/E266), agent (E133/E188/E259/E262/E264/E265/E272)
- Scope/exceptions: G01 only; E254 (nhiều vết cắn ragged + máu trong notch) vẫn áp; E272 chấp nhận residual cuff ash-grey; E265/E269/E260 là clip FAIL làm evidence.

---

## 7. Workflow / queue

### F1. One_API_workflow_literal_widgets
- Rule: Dùng một workflow API `chain4/h3-chain4.json`; `seconds/width/height` của `FreeVideoGenerate` là widget literal `{{SECONDS}}`/704/1280, không nối output 5/6/7 của context node.
- Sources: E101, E163, E174, E175, E242
- supersedes: E175 > graph nối context `[1,5]` bị `validate_inputs` từ chối.
- status_by: user (E174/E242), agent (E101/E163/E175)
- Scope/exceptions: rebuild context trước, rebuild prompts sau (E163); driver chỉ rewrite `continue_from`+seed (E242).

### F2. Upscale_sentinel_flags
- Rule: `upscale_factor:"2"` = no-upscale (output 704×1280); `first_frame_reference`/`voice_reference` chỉ có tác dụng khi có `continue_from`, nếu không thì để false.
- Sources: E101, E144, E175
- supersedes: —
- status_by: agent (E101/E144/E175)
- Scope/exceptions: first frame và voice đi qua `FreeVideoMedia` (E101); E144 xác nhận first_frame_reference không phải khoá frame-0 cứng.

### F3. UI_graph_hygiene
- Rule: UI graph: nối cả 2 report vào PreviewAny, `context_path` tương đối, prefix SaveVideo theo shot, seed fixed; `shot_id` chỉ drive duration/canvas sau khi node restart nạp output mới.
- Sources: E100, E102, E175
- supersedes: E100/E102 > context report float, absolute path, prefix trùng, seed randomize.
- status_by: agent (E100/E102/E175)
- Scope/exceptions: `--shot` bake prompt+seconds+prefix trước restart (E102); widget UI có thể stale — đọc payload (F4).

### F4. Doctor_preflight_payload
- Rule: Trước queue: doctor GO, preflight PASS, refs `qa_passed`, GPU lock một owner, timeout ≥ render; đọc `node_errors` từ POST và payload thực từ `/queue`/`/history`, không tin file trên đĩa hay widget UI.
- Sources: E142, E147, E155, E167, E175, E177, E185, E244, E295, E296
- supersedes: E177 > kết luận từ prompt file khi UI stale; E142/E155 > kiểm tra only file-on-disk / reuse seed cũ.
- status_by: user (E185), agent (E142/E147/E155/E167/E175/E177/E244/E295/E296)
- Scope/exceptions: E167 dùng TimeoutSec ~5400 không 1000 ms; E142 cache-bust context filename + seed; E296 dùng payload để loại giả thuyết.

### F5. SIGTERM_recovery
- Rule: Driver bị SIGTERM sau khi queue thì poll `/history/<prompt_id>`, tải MP4 bằng recover, ghi qa.json; không queue lại vì thiếu file local.
- Sources: E147, E167, E244
- supersedes: —
- status_by: agent (E147/E167/E244)
- Scope/exceptions: E282 (download IOException → `/view` `-v2`) proposed, chưa áp; queue_running=1/history rỗng ≠ job thất bại.

### F6. Audio_assembly_gates
- Rule: Dry-run không được tạo artifact delivery; assembly/chỉ chạy khi mọi shot PASS; mix audio (SFX bed + TTS VO) phải wired, không để phim câm.
- Sources: E137, E150, E166
- supersedes: E166 > việc coi `part1-t2v-final.mp4` từ dry-run là delivery.
- status_by: user (E150), agent (E137/E166)
- Scope/exceptions: `run_all_parts.ps1` assembly-only (E150); E137 là workflow wiring, không phải video patch.

---

## 8. ALH / gates

### L1. ALH_v2_source_of_truth
- Rule: ALH v2 log + rule rendering là nguồn truth; `alh_core.py` telemetry-only; hook lấy root từ `$PSScriptRoot` và verify write; `sync` owns auto sections; status changes audited; giữ 3 dòng `Vừa xong / Bước kế / ALH`.
- Sources: E097, E131, E249, E271
- supersedes: E097 > hook lấy root từ Get-Location / path `out\partpart1-t2v`; E249 > `alh_core.promote()` ghi SKILL.md.
- status_by: user (E131/E249/E271), agent (E097)
- Scope/exceptions: summary cuối phiên viết xong mới sleep; E131 cấm sleep khi render/QA còn chạy.

### L2. Prompt_audit_vs_source
- Rule: Audit prompt so với MỘT nguồn có cấu trúc theo `set_id` (light tier/luma band, seat, geometry/camera, palette hex, prop state_chain, wardrobe/feet/proportion, language leakage) — không so prompt↔prompt bằng regex; sửa nhãn E292/E293.
- Sources: E290, E294, E295
- supersedes: E294 > text bên trong E292 tự gọi nhầm là E293.
- status_by: user (E290), agent (E294/E295)
- Scope/exceptions: seat layout vẫn CHƯA CHỐT (G2); output Big Pickle phải hand-check 3 FAIL + 3 PASS (E295); E293 architecture proposed.

---

## Accepted-but-contradictory pairs (cờ cho user, không tự resolve)

- **M1 — reviewer QA:** E134 (`opencode/deepseek-v4.1-flash-free` làm independent cross-check) vs E153 (pin `hy4-flash-free#high`; E129 chọn `gemini-4-argon` đang **proposed**). Q4 giữ cả hai làm bằng chứng, không chọn model thay user.
- **M2 — G02 hand beat:** E274 auto-PASS chấp nhận hand-slip / bright-area share vs E285/E286 (user override) chấp nhận bàn tay trắng là sai logic kinh dị. Đã ghi `supersedes` ở P6; G02 v2 bị supersede bởi E285.
- **M3 — G03 gradient root cause:** E283 ("lights up/lit phone") và E287 (Scene line) đều accepted nhưng E296 chứng minh bằng payload `/history` rằng cả hai bị bác (Scene byte-identical với G02 v2 vẫn FAIL; v1/G05 v1 có glowing mà không FAIL). Giữ E283/E287 như lịch sử sửa prompt, **không** dùng làm chẩn đoán hiện tại; E291/E292/E297 proposed.
- **M4 — G01 camera:** E272 auto-PASS phần pan của E270 vs E289 evidence-backed FAIL của chính pan đó (H4 thấy seat edge đứng yên). E289 thắng ở C3; E272 chỉ giữ giá trị ở jerk/blood/cuff-deviation.
- **M5 — key wording:** E132 đặt gate `B>=200`, E205 cấm đưa channel minima số vào prompt. Hai cái không triệt tiêu nhau (gate vs prompt) nhưng dễ đọc nhầm — A2 tách rõ.
- **M6 — seat layout (CHƯA CHỐT):** E212–E214 (3+3 invariant, accepted) vs E216–E218 (2+2 PASS, accepted) vs E239/E243 (1+1/four seats, accepted) vs proposed E230/E231/E237/E241. Không pick trong draft này.
- **M7 — G01 hand:** E133/E248 (mitten một khối) bị E257/E258 override **cho G01 only**; bible "mittens" vẫn đúng cho shot khác. E254 (ragged bite) là accepted và áp cho G01.

---

## CHƯA CHỐT / proposed (54 event — KHÔNG phải rule, chỉ chờ user duyệt)

- **E098** G02 attempt 4: style/anchor/palette PASS, FAIL item 5 (2 friends quay lưng).
- **E103** G29: despill key_magenta làm lệch màu navy, để ring raspberry 1–2 px.
- **E104** G23: spec `count 2–3` trên prop 1 object → `split_pose` cắt thành mảnh khổng lồ.
- **E105** G48: `edge_tint` nhuộm đỏ toàn viền clip (G17 46 %, G48 69 %).
- **E106** G29: tỉ lệ chiều cao sai, infected read như trẻ con bên cạnh người khổng lồ.
- **E107** 55/55 prompt lọt tiếng Việt ngoài `<d>` (chỉ sửa nhánh ui ở E099).
- **E108** Shot chỉ có sprite layer không nhận identity clause (G15/G12/G28/G29, friend_group G06).
- **E109** G37: `bite-arm-navy.png` là cụt tay + vết thương gradient blot.
- **E110** G03: blur 6 toàn canvas, mất contour; blur chỉ cho POV/phone screen.
- **E111** UI: `visual_qa` chỉ chấm keyframe, có thể ship freeze/red wash/duration sai.
- **E112** G02 attempt 5: trả 5 keyed character refs vào Media để fix cast.
- **E113** G02 attempt 5: refs trở lại nhưng beam/gradient quay lại (xung đột với E095).
- **E114** G02 attempt 6: clip pixel-identical dù đổi media — cache hit do cùng prompt+seed.
- **E115** User thử style Flat-icon Storytime v3 cho riêng G02 (one-shot).
- **E116** G02 diagnose machine gate FAIL (diagnose output).
- **E117** G01 v3 cần paddle hand dính máu dưới row 27; asset cũ có thumb, không có máu.
- **E122** Refactor `cleanup.py`: art/tests là builder v3 active, không dọn.
- **E124** Hy4 QA: xoá deprecated light-flicker/crawling-shadow/no-gradient priming tại nguồn.
- **E127** G01 Hy4 r2 FAIL: fingered hand, bite đọc như cuffs, máu halo mềm (282 màu).
- **E129** Model discovery: Gemini-4-Hydrogen không có; chọn Gemini-4-Argon làm cross-check.
- **E130** G01 Hy4 r3: silhouette/flatness ổn nhưng key (238,20,200) FAIL gate cũ B>=230.
- **E135** G01 sample: H3 sinh 20+ hành khách, tóc vàng/đỏ, lông mày, prop absent frame 0.
- **E149** Audit 60/60 prompt: Vietnamese mood + negation clause lọt `prompt_visible`.
- **E151** Role contract: agent không vẽ asset/keyframe bằng PIL, không hand-patch video.
- **E173** G01 render FAIL / node_errors.
- **E186** G01 diagnose machine gate FAIL (context).
- **E187** G01 machine QA FAIL: `context : FAIL`.
- **E207** G03 diagnose machine gate FAIL (ref/style).
- **E220** Style contract video lấy từ `h3_prompt_rules.video_style_contract`; `validate_prompt()` chặn negation/red priming.
- **E221** Story-to-asset: `asset-contract.json` + 2 script sinh 1 job/element, gate 8/8 PASS.
- **E222** Feed G01–G04: lint PASS, 6 bản copy hash-match, preflight PASS, UI 7 node/8 link.
- **E223** User yêu cầu regenerate toàn bộ 8 canonical asset; file mới seed mới, giữ file cũ.
- **E224** Master r5 FAIL: không fixture, shadow 40 %, cửa xa mơ hồ.
- **E225** WORKFLOW-INDEX tách setup/per-shot/completion, retry cap 3, GPU lock.
- **E226** Master r5b: 3+3 dù contract 2+2 → **CHƯA CHỐT** (xem M6).
- **E227** Master r5c: 2+2 nhưng light/palette regressed (lavender wall, 44 % shadow).
- **E228** Root cause composer: raw `.png` path lọt prompt, map type bỏ `light_text`, forbid list prime lavender.
- **E229** Master r5d: metric tốt nhưng ô cửa xa vẫn tối; attempt cuối r5e.
- **E230** Thiết kế master 2 rows of 2+2 + sheet 4 passenger composite — **CHƯA CHỐT** (seat-layout).
- **E231** User label "2 rows (4 seats)" = 1+1/row, không 2+2; sửa cabin-map — **CHƯA CHỐT**.
- **E232** `reference_block()` vẫn ghi path `.png` vào prompt; bỏ path, giữ role/copy.
- **E233** User rule: FAIL thì trace story→map→composer→ledger→workflow→seed/anchor, log ALH rồi mới hỏi.
- **E236** Interrogate Hy4 đa vòng để có "mắt pixel": mô tả tự do → đếm/vị trí/điểm tiếp xúc → mâu thuẫn thuật ngữ.
- **E237** r6 master FAIL lần 6: Hy4 thấy 3 rows × 4 seats và 8 cửa sổ — **CHƯA CHỐT**.
- **E238** Retry cap map_master đạt (6th image, override của 5).
- **E240** Z-Image không chạy được (null unet/clip); rebuild thành local H3 T2VA.
- **E241** map_master r7 PASS/MET: 4 seats 2 rows 1+1, 4 windows, fixture gần — đối đầu với E216/E230 (CHƯA CHỐT).
- **E253** Override-v5 asset retry 1: key corner (136,9,87), raspberry.
- **E255** Override-v5 retry 2: key (250,12,246) ổn, vẫn mitten một khối.
- **E282** Download `IOException` (mp4 bị app khác giữ) → đọc `/history`, tải `/view` sang `-v2`; **không requeue GPU**.
- **E291** G03 v4 FAIL lần 3: ramp trần/sàn + tay cầm máy/ngẩng đầu, phá E280/E281; dừng, hỏi user.
- **E292** Payload diff: Scene/Props của G03 v4 byte-identical G02 v2 → E287 bị bác; còn wide→medium + đổi nội dung màn hình. (E294 sửa nhãn: đây là E292, không phải E293.)
- **E293** Kiến trúc 3 lớp reviewer: 1 style contract + 1 plate block byte-identical/set_id + 1 shot block; linter cấm light/background trong shot block; audit cả clip rendered.
- **E297** Giả thuyết xếp hạng: phone tĩnh ổn, phone tự đổi/lên sáng FAIL 3 lần → H3 đọc sự kiện đổi màn hình thành light event; cần user chọn anchor/composition, GPU `qa_hold`.

---

*Draft để user review. Chưa mirror vào skill, chưa promote proposed, chưa resolve seat layout. Sau khi user duyệt: mới cân nhắc `supersedes` thật và đồng bộ có kiểm soát.*
