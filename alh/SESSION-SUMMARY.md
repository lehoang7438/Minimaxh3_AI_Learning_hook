# ALH session summary - alh-v3-refactor-20261127

Finished: 2026-11-27T13:16:19.5101707+07:00

## part1
verdicts: 20 recorded, 3 PASS, 0 PASS_WITH_WARN, 17 FAIL
  - G04: FAIL context
  - G05: FAIL workflow
  - G06: FAIL asset
  - G07: FAIL context
  - G20: FAIL asset
  - G12: FAIL asset
  - G13: FAIL asset
  - G14: FAIL prompt
  - G15: FAIL prompt
  - G09: FAIL context
  - G10: FAIL prompt
  - G11: FAIL asset
  - G16: FAIL context
  - G17: FAIL context
  - G18: FAIL asset
  - G19: FAIL context
  - G03: FAIL context/plate/prompt
clips: 20 / 24 shot(s) have an mp4

## part2
verdicts: 0 recorded, 0 PASS, 0 PASS_WITH_WARN, 0 FAIL
clips: 0 / 24 shot(s) have an mp4

## part3
verdicts: 0 recorded, 0 PASS, 0 PASS_WITH_WARN, 0 FAIL
clips: 0 / 12 shot(s) have an mp4

## Learning log
# ALH report - 2026-11-27 13:16

log: `art\comfy\ALH\learning-log.jsonl`  |  total 249 event(s)

### Status

| value | n | share |
|---|---|---|
| accepted | 100 | 40% |
| archived | 99 | 40% |
| proposed | 47 | 19% |
| revoked | 3 | 1% |

### Event

| value | n | share |
|---|---|---|
| rule_gap | 86 | 35% |
| asset_qa_fail | 49 | 20% |
| warn_accepted | 40 | 16% |
| qa_fail | 36 | 14% |
| verdict | 32 | 13% |
| node_error | 4 | 2% |
| promoted | 2 | 1% |

### Skill

| value | n | share |
|---|---|---|
| asset-qa | 127 | 51% |
| comfyui-runner | 58 | 23% |
| h3-prompt-writing | 28 | 11% |
| h3-visual-qa | 22 | 9% |
| character-bible | 9 | 4% |
| h3-storyboard | 3 | 1% |
| bitnet | 1 | 0% |
| global | 1 | 0% |

### Layer

| value | n | share |
|---|---|---|
| workflow | 41 | 16% |
| asset | 36 | 14% |
| prompt | 31 | 12% |
| magenta_key | 15 | 6% |
| asset_qa | 12 | 5% |
| context | 9 | 4% |
| mitten_anatomy | 8 | 3% |
| visual | 8 | 3% |
| set_geometry | 6 | 2% |
| palette_lock | 6 | 2% |
| lighting_logic | 6 | 2% |
| injury_logic | 6 | 2% |
| anchor | 5 | 2% |
| qa_reviewer | 5 | 2% |
| qa | 5 | 2% |
| prop_identity | 4 | 2% |
| identity | 4 | 2% |
| style_eyes | 4 | 2% |
| ref/style | 4 | 2% |
| camera_composition | 3 | 1% |
| sheet_contract | 3 | 1% |
| pose_logic | 3 | 1% |
| cabin_geometry | 2 | 1% |
| asset_reuse | 2 | 1% |
| audio | 2 | 1% |
| story | 2 | 1% |
| archived_hair_refs | 1 | 0% |
| job_json | 1 | 0% |
| style_flatness | 1 | 0% |
| composition_palette | 1 | 0% |
| style_geometry | 1 | 0% |
| panel_layout | 1 | 0% |
| window_fill | 1 | 0% |
| aisle_geometry | 1 | 0% |
| camera_view | 1 | 0% |
| character_bible | 1 | 0% |
| assets | 1 | 0% |
| spec_identity | 1 | 0% |
| review | 1 | 0% |
| model | 1 | 0% |
| spec | 1 | 0% |
| wardrobe | 1 | 0% |
| cast | 1 | 0% |

### Needs a decision

- [E098] qa_fail / G02 / visual - G02 attempt 4: frame 1 is the correct flat restaurant plate (no pink sheet); mid has no amber beam or gradient, so style/anchor/palette/wardrobe/anatomy all PASS.
- [E103] asset_qa_fail / G29 / magenta_key - key_magenta despill was mean(r+b)/2 - g, which is positive for navy too (blue>green) so it quietly shifted every navy garment, and at 0.55 it left a 1-2 px raspberry ring on 4 assets.
- [E104] qa_fail / G23 / prop_identity - props-chaos/props-galley/props-blood are ONE object per file, but the spec declared count 2-3, so split_pose cut them into equal columns and each fragment was scaled to layer height.
- [E105] qa_fail / G48 / palette_lock - edge_tint adds red at frame edges for the whole clip (animate_pilot: r += edge*200, g/b *= 1-edge*0.85).
- [E106] qa_fail / G29 / camera_composition - G29 placed khang-sheetB at h 0.48 y 0.92 and pz-sheet at h 0.34 y 0.90: 2 percent apart on the same foot line but 30 percent shorter, so the infected reads as a child next to a giant.
- [E107] rule_gap / G15 / prompt - 55/55 rebuilt prompts carry Vietnamese outside <d>: spec description is Vietnamese and action_text copies it verbatim, mood_text falls back to the literal 'u am'.
- [E108] rule_gap / G15 / prompt - Shots whose cast exists only as sprite layers get no identity clause: the context characters list is empty for G15 (pz-lunge), G12, G28 and G29 (pz-sheet) and misses friend_group on G06, so the promptΓÇª
- [E109] rule_gap / G37 / prop_identity - bite-arm-navy.png is a severed forearm: it ends in a bare rounded stump (no mitten) and its wound is a multi-tone gradient blot with drips, both against BODY-LITE/flat-fill.
- [E110] rule_gap / G03 / visual - G03 carried blur 6 on the whole canvas, so the only blurred keyframe of part 1 was the toast: ink contour gone, foam turned into soft blobs, and the clip had the lowest motion of the part (1.85).
- [E111] rule_gap / UI / workflow - h3-visual-qa only scored keyframes, so a frozen card, a wrong duration, a red wash or a 100 percent red frame could ship unnoticed.
- [E112] rule_gap / G02 / anchor - G02 attempt 5 layer=anchor/reference: restored the 5 character refs to the Media panel (MEDIA_CHAR_DROP emptied) because attempt 3-4 with plate-only media produced generic backs and dropped friend_beeΓÇª
- [E113] qa_fail / G02 / visual - G02 attempt 5: restoring 5 keyed character refs fixed cast/action (3 friends clapping, correct wardrobe) but reintroduced a large ceiling spotlight beam and floor gradient, so h3-visual-qa item 1/2 FAΓÇª
- [E114] rule_gap / G02 / workflow - G02 attempt 6 returned a pixel-identical clip to attempt 5 despite removing all character refs from context and Media.
- [E115] rule_gap / G02 / prompt - User approved a one-shot style trial: Flat-icon Storytime v3 for G02 only.
- [E116] qa_fail / G02 / ref/style - see diagnose output; layer(s) failed machine gate
- [E117] rule_gap / G01 / asset_qa - v3 script opening shot G01 needs a blood-stained oval paddle hand dragging under row 27.
- [E122] rule_gap / G01 / workflow - Refactor cleanup.py: art/tests holds ACTIVE v3 builders (build_v3_specs/build_global_context/rebuild_prompts/feed_h3_context).
- [E124] rule_gap / G01 / prompt - Hy4 style QA: removed deprecated light-flicker/crawling-shadow/slow-dust, neutral-stare negations, no-gradient/no-spotlight and no-text priming, two-tone/flat conflict at source in rebuild_prompts.py ΓÇª
- [E127] asset_qa_fail / G01 / asset_qa - Hy4 r2 QA FAIL: blood placement improved but silhouette regressed to fingered hand, bite read as torn cuff not missing palm chunk, blood had soft airbrushed halos (color_count 282).
- [E129] verdict / G01 / qa_reviewer - Model discovery correction: Gemini 4 Hydrogen is not available.
- [E130] asset_qa_fail / G01 / asset_qa - Hy4 r3 QA FAIL: paddle-mitten silhouette and flatness were fixed (color_count 207, bands 0), but near-magenta key down corner (238,20,200) hard FAILs R>=240/B>=230, and script fidelity is only PARTIALΓÇª
- [E135] qa_fail / G01 / prompt - G01 sample render Hy4 QA FAIL: H3 generated 20+ extra passengers, blonde/orange hair, eyebrows and red clothing, finger-like passenger hands, prop absent in frame 0 and framing widened from the INS unΓÇª
- [E149] rule_gap / FULL / prompt - Audit of all 60 rebuilt prompts found Vietnamese mood text outside dialogue tags in 60 of 60 files (Mood: u am / am ap / cang thang) and cabin-map negation clauses leaking into prompt_visible in 9 filΓÇª
- [E151] rule_gap / FULL / asset - Skill role contract re-read on user prompt: agent must not draw assets/keyframes with PIL and must not hand-patch video.
- [E173] qa_fail / G01 / workflow - G01 render FAIL / node_errors
- [E186] qa_fail / G01 / context - see diagnose output; layer(s) failed machine gate
- [E187] qa_fail / G01 / visual - G01 machine QA FAIL: context : FAIL
- [E207] qa_fail / G03 / ref/style - see diagnose output; layer(s) failed machine gate
- [E220] rule_gap / G01-G04 / prompt - Video prompts now derive the style contract from h3_prompt_rules.video_style_contract (same source as asset prompts); shared validate_prompt gates deletion negations and red priming before rebuild_proΓÇª
- [E221] rule_gap / G01-G04 / asset - Story-to-asset system: asset-contract.json + story_to_asset_prompts.py + check_asset_prompt.py turn spec/map/bible/ledger into one job per element, gate 8/8 PASS.
- [E222] verdict / G01-G04 / workflow - B╞░ß╗¢c 5 feed: 4 enriched prompts lint PASS 0 warning; 6 copies in ComfyUI/input hash-match canonical QA-passed assets; h3-master.json preflight PASS (placeholder warnings expected); h3-single-node-ui.jΓÇª
- [E223] rule_gap / G01-G04 / asset - User ordered full regeneration of all 8 canonical assets.
- [E224] asset_qa_fail / G01-G04 / asset - Master r5 FAIL/PARTIAL: no visible emitting fixture, shadow 40% vs low-key contract, far-door identity ambiguous.
- [E225] rule_gap / G01-G04 / workflow - User logic review of WORKFLOW-INDEX: restructured into setup-once / per-shot loop / completion; added audio+assembly+final-film QA, dependency+anchor invalidation tables, 3-attempt retry cap, WARN legΓÇª
- [E226] asset_qa_fail / G01-G04 / asset - Master r5b FAIL/PARTIAL attempt 2/3: 3+3 seats despite 2+2 contract.
- [E227] asset_qa_fail / G01-G04 / asset - Master r5c FAIL PARTIAL at attempt 3 of 3.
- [E228] rule_gap / G01-G04 / prompt - Root cause of three master FAILs found in composer not seed: bare-space join leaked raw route-map .png path into visible prompt (E226), map type skipped light_text (E227), light_text appended forbid lΓÇª
- [E229] asset_qa_fail / G01-G04 / asset - Master r5d FAIL PARTIAL attempt 4: systemic prompt bugs fixed and metrics excellent, but far door square remains dark instead of bone-white.
- [E230] rule_gap / G01-G04 / story - User approved redesign: master shows exactly two rows of 2+2 seats; generic background passengers are one sheet of four distinct figures in a single row composited into the three seats other than 27A;ΓÇª
- [E231] rule_gap / G01-G04 / story - E231: user label 2 rows (4 seats) means 1+1 per row, not 2+2.
- [E232] rule_gap / G01-G04 / prompt - E232: reference_block() was still writing raw .png paths into visible prompt text for ref-based cabin plates; removed path, kept role/copy only, job.reference carries paths.
- [E233] rule_gap / G01-G04 / qa - User rule 26/11: on FAIL do not ask immediately; trace story -> map -> rule/composer -> ref/QA ledger -> workflow -> seed/anchor, log ALH, then ask only with evidence or at retry cap.
- [E236] rule_gap / ALL / qa - Correction of E235 (archived due to encoding): interrogate Hy4 in detailed multi-round dialogue so the agent gains pixel-level eyes.
- [E237] asset_qa_fail / G01-G04 / asset - r6 master FAIL/PARTIAL under 5-retry override (6th image): Hy4 3 rounds saw 3 rows x 4 seats (2+2)=12 and 8 oval windows, fixture far not near; machine gate PASS and prompt/map correct, root cause H3 ΓÇª
- [E238] rule_gap / G01-G04 / qa - Retry cap reached on map_master (6th image, override of 5).
- [E240] rule_gap / S01 / workflow - Z-Image workflow with null unet_name/clip_name cannot run here: local models are FreeVideo int8_convrot, core UNETLoader/CLIPLoader have no loader; rebuilt graph as local H3 T2VA (FreeVideoMedia -> FrΓÇª
- [E241] verdict / G01-G04 / asset - map_master r7 PASS/MET: Hy4 3 rounds saw 4 seats in 2 rows of 1+1, 4 oval windows, fixture near camera, one teal aisle, 0 people/red/text; machine 53 colors 65pct shadow 0 red.

### Accepted but not promoted to SKILL.md/GLOBAL-RULES.md

- [E083] asset-qa / freshstart-friend-beer-magenta-r1 / magenta_key - friend_beer regenerated ref key corner (255,8,128) after 1024 downscale - blue channel far too low, raspberry not near-magenta; FAIL under approved option A (needs B>=230).
- [E092] comfyui-runner / G02 / visual - G02 first QA by eye FAIL: frame 1 (t=0.2s) is a 72.6% pink character sheet of Khang, not the restaurant plate, despite plate being ref slot 1 and first_frame anchored to the QA plate.
- [E093] h3-prompt-writing / G02 / prompt - G02 eye QA FAIL fixed at prompt layer: old first line referencing Picture 1 at 00:00 made H3 open on a keyed character sheet.
- [E095] comfyui-runner / G02 / anchor - G02 attempt 3 layer=anchor/reference: dropped keyed character sheets from Media panel for G02 (MEDIA_CHAR_DROP) so only the QA restaurant plate is a picture; cast identity remains in prompt wardrobe tΓÇª
- [E096] comfyui-runner / G02 / prompt - G02 attempt 3: first frame now correct restaurant plate (pink sheet fixed by MEDIA_CHAR_DROP).
- [E097] comfyui-runner / alh-v2 / review - ALH v1 lost lessons in two ways: completion_handler built its qa-notes path by concatenating 'part' + 'part1' (out\partpart1-t2v, which never existed, so every session summary reported 0 verdicts) andΓÇª
- [E099] h3-prompt-writing / G01 / prompt - UI black-screen shot review: the contract said 'no text' while the tail allowed '00:00' (two opposite rules), the waveform had no colour on near-black navy, 'lips remain closed' and breathing SFX wereΓÇª
- [E100] comfyui-runner / G01 / workflow - Context node (the UI prompt path) still prepended the 'Set continuity/Objects/Light/wardrobe' blob and re-appended the context contract, so the style contract sat ~1900 chars into field 1 - the same bΓÇª
- [E101] comfyui-runner / G01 / model - upscale_factor '2' is the engine's no-upscale sentinel: UPSCALE_OPTIONS=('2','1.5','1.2') and upscale_option() returns {} for '2' (comfy_nodes.py:94), so output stays at the graph canvas (704x1280), nΓÇª
- [E102] comfyui-runner / UI / workflow - UI workflow review: the context report floated unconnected, context_path was an absolute Windows path, SaveVideo prefix was identical for every shot, and seed was randomize.
- [E126] asset-qa / G01 / asset_qa - User rejected Hy4 PASS_WITH_WARN for G01 hand: v3 script explicitly requires a hand that is blood-soaked OR bitten/chipped with blood spreading.
- [E128] asset-qa / G01 / asset_qa - Promoted ALH E126 into mandatory asset-qa SKILL.md: Asset QA must compare each asset against the shot script/spec (script fidelity), not only the bible; PASS_WITH_WARN is not allowed when the script sΓÇª
- [E133] asset-qa / G01 / asset_qa - Keep one unbroken paddle-mitten with a jagged bite notch, flat dark-red blood, a flat key and a low colour count on the G01 bite ref.
- [E136] h3-visual-qa / G01 / prompt - Fix a widened INS shot at the source with a dedicated QA-passed INS first-frame plate and positive cast-count lock; never patch frames.
- [E148] asset-qa / P3G12 / context - Final shot P3G12 had no bg in the v3 spec; SCENE_OVERRIDE had assigned the cabin_chaos set, so the live Ghe27AContext node would have opened the final black-card shot on a chaotic cabin plate (blood-sΓÇª
- [E150] comfyui-runner / FULL / workflow - User rule 26/11: never batch-render.
- [E152] comfyui-runner / G04-G07 / asset - Hy4 QA of the batch-rendered part1 clips (G04-G07) found 3 FAILs of 4: G04 script PARTIAL (flat phone-screen INS rendered as a wide three-woman restaurant scene), G06 hard palette FAIL (old khang-faceΓÇª
- [E153] h3-visual-qa / FULL / qa_reviewer - Hy4 QA blocker 26/11: subagent calls with agent=general and no explicit model use a non-vision model; read tool returns no image support for every PNG, so agent returned script_fidelity=MISSING and FAΓÇª
- [E154] asset-qa / G04-G20 / asset - Full part1 QA of 18 shots: only G01/G05/G11/G12 PASS; 14 FAIL.
- [E155] comfyui-runner / G08 / workflow - When a shot plate is replaced after QA fail, run_master seed must change too: ComfyUI caches the Ghe27AContext node by the context filename, so reusing the old seed serves the rejected plate even whenΓÇª
- [E156] h3-prompt-writing / G13-G20 / prompt - Empty-panel and POV v3 shots must use per-shot positive beats and composition text.
- [E157] comfyui-runner / G02 / context - Node Ghe27AContext chß╗ë ─æß╗ìc shot.bg cho Picture1 + first frame.
- [E158] h3-visual-qa / G20 / qa - Machine color_count quantize 128x128 PASS nh╞░ng Hy4 thß║Ñy gradient/halo/vß╗çt s├íng v├┤ nguß╗ôn.
- [E159] asset-qa / G18 / asset - Shot POV-K kh├┤ng d├╣ng canon ref to├án th├ón: H3 ─æß╗òi g├│c sang 3P v├á vß║╜ trß╗ìn ng╞░ß╗¥i.
- [E160] comfyui-runner / G16 / workflow - FAIL cß╗ºa clip c┼⌐ tr╞░ß╗¢c khi sß╗¡a source kh├┤ng chß╗⌐ng minh source mß╗¢i sai.
- [E161] h3-prompt-writing / G17 / context - Panel rong va voices ngoai khung: cau phu dinh no people / no figure bi H3 ve nguoc.
- [E162] h3-prompt-writing / G03 / prompt - Xoa moi cau xoa doi tuong khoi prompt_visible: ACTION_OVERRIDE BEAT_OVERRIDE cabin-map scene objects va light.
- [E163] comfyui-runner / G03 / workflow - Rebuild global context TRUOC roi moi rebuild prompts.
- [E164] asset-qa / G03 / asset_qa - seat27a-flat-r2 FAIL: mat nhan vat co vong cung nhamat thay vi 2 cham den, ban tay co duong tach ngon cai, manh hinh teal trong khong co anh sinh nhat.
- [E165] asset-qa / G11 / asset_qa - lav-mirror-flat-r2 FAIL: mat trong guong drift sang toc bob va vai tran, khong phai Khang toc xu xao ao navy dai tay.
- [E166] comfyui-runner / G04 / workflow - run_master.ps1 -DryRun van goi mix_h3_audio va assemble part1-t2v-final.mp4 tu clip cu.
- [E167] comfyui-runner / G04 / workflow - Background render G04 bi SIGTERM do goi shell background voi timeout 1000ms.
- [E168] h3-visual-qa / G18 / qa_reviewer - Hy4 CHI la mat mo ta, KHONG duoc tu cham PASS/FAIL va KHONG duoc de xuat fix.
- [E170] h3-visual-qa / G18 / visual - User override: pov-shoulders-flat-r1 FAIL.
- [E171] h3-prompt-writing / G04 / prompt - Mot prompt H3 chi mot hanh dong chinh.
- [E172] h3-prompt-writing / G04 / prompt - G04 FAIL do 3 beat camera drifts a little closer nhan len nhau thanh zoom cong don; khung last dien thoai va vien man hinh ra khoi khung, mat chu the phone screen cua script; zoom vuot xa 3%.
- [E174] comfyui-runner / G01 / workflow - Mo hinh Flow cho G01-G04: mot bo ref co dinh gom background plate QA-passed + character/body/voice/avatar (Ghe27AContext assets/first/voice) + prop; moi hanh dong = 1 clip, G01/G02/G03/G04 moi shot coΓÇª
- [E175] comfyui-runner / G01 / workflow - Khong noi context output 5/6/7 seconds/width/height vao FreeVideoGenerate: engine custom validation yeu cau seconds la widget literal; lien ket context [1,5] khien validate_inputs bao Duration must beΓÇª
- [E176] h3-prompt-writing / G01 / prompt - Style contract cua global-context co cau flat amber restaurant accents ap cho MOI shot, keo vao cabin dem G01-G04 va co the prime mau am / nhan vat khong co trong script.
- [E177] comfyui-runner / G01 / workflow - Khi user phan nan prompt/video tren ComfyUI UI khong dung, khong ket luan ngay tu file prompt tren dia: UI widget co the giu prompt cua job cu.
- [E178] h3-prompt-writing / G01 / prompt - G01 QA FAIL duoc user phan hoi tu preview ComfyUI va duoc Hy4 (seen, mo ta 3 khung) xac nhan: first co cau truc ghe va toan bo tay ao, mid mat cau truc ghe va vat the phong to, last tay ao bi cat mep ΓÇª
- [E179] h3-prompt-writing / G01 / prompt - Sua G01 sau E178: truoc do cung 1 prompt co 3 lenh camera (camera line zoom 3% + beat drifts forward + ambience camera move continue) nen H3 cong don thanh zoom lon, mat cau truc ghe tu mid va cat tayΓÇª
- [E180] comfyui-runner / G01 / workflow - Phat hien them 1 lop camera bi xung dot: feed_h3_context.py first_line luon chen Only the supplied subject moves; the camera only drifts or pushes in vao MOI enriched prompt, mau thuuan truc tiep voi ΓÇª
- [E181] asset-qa / G01 / asset - User 26/11 chot huong moi cho kho asset: nen duoc phep GIAU CHI TIET va CO CHIEU SAU, nhan vat van flat tuyet doi; lam lai toan bo kho 60 shot v3, xoa asset cu, ra soat lai prompt asset cho nhat quan,ΓÇª
- [E183] character-bible / G01 / asset - User 26/11 yeu cau them 2 ref goc cho kho moi: (1) ban scan 4 huong toan than cua nhan vat chinh Khang front/left/back/right, mot hang, cung scale, chan tren mot duong co so, lam anchor nhan dang va tΓÇª
- [E184] character-bible / G01 / asset - User 26/11 chot them: scan 4 huong toan than phai co cho MOI nhan vß║¡t, ke ca nhan vat phu, zombie/infected va b├│ng ─æen/silhouette - khong chi Khang.
- [E185] comfyui-runner / G01 / workflow - ref asset moi phai di dung vao workflow de H3 gen chuan.
- [E188] asset-qa / G01 / asset - G01 take 2026112906 (camera-lock prompt sau E179/E180) render xong, 2 file video cung hash.
- [E189] asset-qa / G01 / asset - User da approve xoa toan bo asset cu.
- [E190] asset-qa / G01 / asset - Hy4 soi cabin-master-map-v4: dat 1 diem nhin, perspective 1 diem, 3 lop phang co che khuat, 0 nguoi/0 do ro, khong magenta/amber -> dung huong nen sau.
- [E193] asset-qa / G01 / asset - Khang turnaround v4 seed 20261126100: Hy4 mo ta 1/1 - 4 hinh dung 1 hang/cung scale/chan cung baseline, 1:6, 4 ngon thang+1 cai khong mong, khop vai/khuyu co.
- [E194] asset-qa / G01 / asset - User 26/11 quyet dinh: 9 sheet turnaround 4 huong LA anchor nhan dang/bß╗æ cuc, KHONG duoc dua lam <Picture N> trong video va KHONG qua keyer, nen co the dung nen bone-white phang; bo cong magenta R>=24ΓÇª
- [E196] character-bible / ALL / wardrobe - ngoai viec ao/quan/giay phai tach lop, MOI nhan vat phai co trang phuc khac nhau ro (mau + kieu), khong duoc gop chung 1 block navy hoac mac y hiet.
- [E198] character-bible / ALL / identity - tu tu vy hoi beo - yeu cau cham lai, ky hon.
- [E199] asset-qa / ALL / identity - Hy4 soi friend_girl_bob seed 43106 thay cham/dau tron nho o vai va khuß╗╖u tay.
- [E200] asset-qa / G02 / asset - Plate G02 (red_allowed=false) ra 2 cham do nho gan diem hoi tu du du prompt co cum `red only for blood and recording dot` trong style contract.
- [E201] h3-prompt-writing / FULL / prompt - ALH E149 applied to G01-G04: Vietnamese mood outside <d> replaced with English (tense/gloomy) in rebuild_prompts.mood_text; all 4 prompts now have zero non-ASCII words and zero cabin-map negation clauΓÇª
- [E202] asset-qa / G03 / asset - Cabin variant plates generated without any <Picture N> drifted twice on G03 (third seat, amber dot) even with tight positive prompts.
- [E203] comfyui-runner / FULL / workflow - Per-shot PLATE_OVERRIDE in build_global_context only set shot.bg; the custom node gates first-frame injection on scene.qa_passed, so G01/G03 showed plate=<file> but first_from_plate=False and fell bacΓÇª
- [E206] h3-prompt-writing / G02 / prompt - G02 prompt had a contradictory hand beat: one clause said the hand withdraws beneath the seat at the lower edge, the At 00:00 clause said it was already withdrawn; combined with the shared style contrΓÇª
- [E209] h3-prompt-writing / G01 / context - this is a horror film, so light and environment must be horror too - low-key, one or two motivated fixtures, slate walls lighter than navy seats, 60-75 percent flat shadow, heavy flat vignette; never ΓÇª
- [E210] asset-qa / G02 / asset - one aisle plate does not match the map.
- [E212] asset-qa / G02 / asset - Route-map 3D r1 is geometry authority for the whole G01-G04 rebuild, but Hy4 description-only QA found 1+1 seats per row and only one visible window wall instead of the cabin-map invariant 3+3 (A-B-C/ΓÇª
- [E213] asset-qa / G02 / asset - Route-map 3D r2 still rendered 1+1 seats and one window wall after an explicit 3+3 prompt; the wrong-count r1 placed first in refs anchored the geometry.
- [E214] character-bible / G02 / context - User clarified the shared map is a full 3D draft of every nook the protagonist walks through.
- [E215] asset-qa / G02 / asset - Master horror r3 FAIL/PARTIAL.
- [E243] h3-storyboard / STORY-CHAIN / cast - User requires 3-4 passengers on the plane: Khang in 27A plus three generic passengers in rows 27/28 (part1 spec G02/G03, cabin-map 1+1 four seats).
- [E244] comfyui-runner / STORY-G01 / workflow - A chain4_run.py driver can be SIGTERM-ed by a 120s shell timeout AFTER queueing: the ComfyUI prompt keeps running server-side (queue_running=1, history empty).
- [E245] h3-prompt-writing / G01 / prompt - User rejected story-g01 G01 render: not scary enough; the bitten arm belongs UNDER the airplane seat; no object dragging in from the right edge - the CAMERA must pan/tilt toward that arm; the arm is bΓÇª
- [E247] h3-prompt-writing / G01 / prompt - G01 v2 near-passable but camera angle still shows seated passengers on the plane and the ambient light is not scary enough; asked agent to self-review before reporting.
- [E249] comfyui-runner / ALL / workflow - ALH v2 log + v3 rule rendering is the single source of truth; alh_core.py is telemetry-only, the hook never writes LEARNINGS.md, sync owns every auto section, and status changes are audited.

### Contradictions / superseded-but-active

- G01 / asset

### Skills with no learning events

- freevideo-runner, h3-prompt-linter


Review: `python art/comfy/ALH/alh.py report` then `set <id> accepted|revoked`, then `sync`.
