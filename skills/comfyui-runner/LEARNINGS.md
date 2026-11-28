# Learnings - comfyui-runner

## Reviewed / promoted 2026-11-25 (user approved)

- `diagnose_shot.ps1` phải kiểm `$LASTEXITCODE` sau **mọi** lời gọi python/ffmpeg. Lỗi in `! ... PYTHON FAIL exit=N` và script `exit 1`; không được để here-string mất nháy làm asset/style gate chạy im lặng rồi báo PASS. Đã áp vào script.
- Mọi gen/queue phải chạy sau khi sample shot QA PASS bằng mắt; không `-BatchVerified` khi prompt/context/node còn thay đổi.

## Auto-learned (ALH)

_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. **Only `Accepted rules` are active.** Detail/verdicts are in `RUN-LOG.md` and the log; a rule is mandatory only after it is mirrored into `SKILL.md` / `GLOBAL-RULES.md`._

### Accepted rules (active)

- [E092] ALH:E092 — G02 first QA by eye FAIL: frame 1 (t=0.2s) is a 72.6% pink character sheet of Khang, not the restaurant plate, despite plate being ref slot 1 and first_frame anchored to the QA plate.
- [E095] ALH:E095 — G02 attempt 3 layer=anchor/reference: dropped keyed character sheets from Media panel for G02 (MEDIA_CHAR_DROP) so only the QA restaurant plate is a picture; cast identity remains in prompt wardrobe t…
- [E096] ALH:E096 — G02 attempt 3: first frame now correct restaurant plate (pink sheet fixed by MEDIA_CHAR_DROP).
- [E097] ALH:E097 — ALH v1 lost lessons in two ways: completion_handler built its qa-notes path by concatenating 'part' + 'part1' (out\partpart1-t2v, which never existed, so every session summary reported 0 verdicts) and…
- [E100] ALH:E100 — Context node (the UI prompt path) still prepended the 'Set continuity/Objects/Light/wardrobe' blob and re-appended the context contract, so the style contract sat ~1900 chars into field 1 - the same b…
- [E101] ALH:E101 — upscale_factor '2' is the engine's no-upscale sentinel: UPSCALE_OPTIONS=('2','1.5','1.2') and upscale_option() returns {} for '2' (comfy_nodes.py:94), so output stays at the graph canvas (704x1280), n…
- [E102] ALH:E102 — UI workflow review: the context report floated unconnected, context_path was an absolute Windows path, SaveVideo prefix was identical for every shot, and seed was randomize.
- [E150] ALH:E150 — User rule 26/11: never batch-render.
- [E152] ALH:E152 — Hy4 QA of the batch-rendered part1 clips (G04-G07) found 3 FAILs of 4: G04 script PARTIAL (flat phone-screen INS rendered as a wide three-woman restaurant scene), G06 hard palette FAIL (old khang-face…
- [E155] ALH:E155 — When a shot plate is replaced after QA fail, run_master seed must change too: ComfyUI caches the Ghe27AContext node by the context filename, so reusing the old seed serves the rejected plate even when…
- [E157] ALH:E157 — Node Ghe27AContext chỉ đọc shot.bg cho Picture1 + first frame.
- [E160] ALH:E160 — FAIL của clip cũ trước khi sửa source không chứng minh source mới sai.
- [E163] ALH:E163 — Rebuild global context TRUOC roi moi rebuild prompts.
- [E166] ALH:E166 — run_master.ps1 -DryRun van goi mix_h3_audio va assemble part1-t2v-final.mp4 tu clip cu.
- [E167] ALH:E167 — Background render G04 bi SIGTERM do goi shell background voi timeout 1000ms.
- [E174] ALH:E174 — Mo hinh Flow cho G01-G04: mot bo ref co dinh gom background plate QA-passed + character/body/voice/avatar (Ghe27AContext assets/first/voice) + prop; moi hanh dong = 1 clip, G01/G02/G03/G04 moi shot co…
- [E175] ALH:E175 — Khong noi context output 5/6/7 seconds/width/height vao FreeVideoGenerate: engine custom validation yeu cau seconds la widget literal; lien ket context [1,5] khien validate_inputs bao Duration must be…
- [E177] ALH:E177 — Khi user phan nan prompt/video tren ComfyUI UI khong dung, khong ket luan ngay tu file prompt tren dia: UI widget co the giu prompt cua job cu.
- [E180] ALH:E180 — Phat hien them 1 lop camera bi xung dot: feed_h3_context.py first_line luon chen Only the supplied subject moves; the camera only drifts or pushes in vao MOI enriched prompt, mau thuuan truc tiep voi …
- [E185] ALH:E185 — ref asset moi phai di dung vao workflow de H3 gen chuan.
- [E203] ALH:E203 — Per-shot PLATE_OVERRIDE in build_global_context only set shot.bg; the custom node gates first-frame injection on scene.qa_passed, so G01/G03 showed plate=<file> but first_from_plate=False and fell bac…
- [E244] ALH:E244 — A chain4_run.py driver can be SIGTERM-ed by a 120s shell timeout AFTER queueing: the ComfyUI prompt keeps running server-side (queue_running=1, history empty).
- [E249] ALH:E249 — ALH v2 log + v3 rule rendering is the single source of truth; alh_core.py is telemetry-only, the hook never writes LEARNINGS.md, sync owns every auto section, and status changes are audited.
- [E305] ALH:E305 — E305 G02-first queue: G02 v2 visual PASS was superseded by E285 story/horror-logic rejection, so option (a) anchor G03 from an approved G02 plate is invalid until G02 v3 is rendered and QA PASS. G02 v3 (6 s, seed 20264201) queued alone via art/comfy/chain4/h3-chain4.json --shot-ids G02 after doctor GO; G03/G01/G05 stay unqueued. Re-evaluate E271 only after G02 v3 clean verdict.
- [E311] ALH:E311 — E311 accepted (user): after E307 FAIL and E308/E309/E310 prompt fixes, queue exactly one G02 v4 job with seed 20264301 via art/comfy/chain4/h3-chain4.json (same single graph). Gates: doctor GO, lint 6s PASS 0 warning, prompt audit FAIL 0 / CHUA CHOT 6 / PASS 39, no hand/finger/nail/ease/front-near wording. Handoff saved as story-g02-v4/G02.mp4 for a possible E306 continue-from trial. No G03/G01/G05 queue until G02 v4 visual QA verdict; no verdict before Hy4 reads frames.
- [E316] ALH:E316 — E316 accepted (user override): G02 v5 is a controlled smart-chain trial, not a fresh T2V: continue_from G01 -> G02 on the one chain4 workflow, with an explicit timed hard cut after the 22-frame overlap, the same r8 arm picture reference attached as <Picture 1>, adjacent flick/snap beats, and a fresh seed. This supersedes the strict hard-cut reading of E242/E174 for G01->G02 and redirects E306 to this pair. It stays a single-shot trial: no G03/G01/G05 queue, doctor GO and preflight before queue, clip QA and visual QA after render.  [supersedes E242,E174,E306,E311]
- [E317] ALH:E317 — E317 accepted (user): queue exactly one G02 v5 job on the single chain4 workflow with seed 20264402 (seed-base 20264401 segment 2), 6 s, continue_from story-g02-v5/G01.mp4, --ref-asset art/assets/h3/refs/bloody-arm-real-r8-1024.png. Doctor GO and workflow preflight are gates; no G01/G03/G05 job and no verdict before clip QA + enlarged Hy4 frames + Big Pickle hand-check 3 FAIL / 3 PASS.  [supersedes E311]
- [E318] ALH:E318 — E318 accepted (agent, pre-GPU driver fix): chain4_run.py must receive --prompts prompts/part1-rebuilt when rendering G01/G02 by shot id; the default art/comfy/prompts/chain4 only holds legacy seg1-seg4 and is not the delivery prompt source. A missing prompt exits before doctor and before queue, so the E317 approval is still unconsumed.
- [E319] ALH:E319 — E319 accepted (agent, disclosed deviation): recover this render from /history/<prompt_id>, download its video, copy the handoff and run clip_qa; do NOT re-queue. The actual seed is 20264403 (off by one from the approved 20264402) and must be recorded in the verdict. Future chain4 --seed-base must account for seed_base+segment before claiming a seed.  [supersedes E317 (seed number only)]
- [E325] ALH:E325 — E325 accepted (agent, supersedes E319): chain4_run.py now has --seed for an EXACT one-segment seed and validates that only one segment runs; --seed-base remains documented as segment-offset. Long jobs require a shell timeout >=7200000 ms. v6 uses --seed 20264501.  [supersedes E319]
- [E326] ALH:E326 — E326 accepted (agent, supersedes E314 for G02): align the G02 truth layers with E308/E309/E316 - spec seconds 6 + rear viewpoint metadata, cabin-map shot_overrides.G02, global-context VIEWPOINT_OVERRIDE/STATE_OVERRIDE, and audit report scope PRE-RENDER only with an E324 arm regression gate. Scope is G02 only; cabin-map remains authoritative for G03/G05.  [supersedes E314]
- [E327] ALH:E327 — E327 accepted (user): queue exactly one G02 v6 retry after the fixes, on the single chain4 workflow, 6 s, continue_from story-g02-v6/G01.mp4, r8 arm reference, EXACT seed 20264501 via --seed. Doctor GO and preflight are gates; no G01/G03/G05 queue and no verdict before clip QA + Hy4 flash-free + Big Pickle hand-check 3 FAIL / 3 PASS.  [supersedes E320,E321]

### Accepted run records (evidence, not rules)

- E131 verdict / FULL / workflow (detail in RUN-LOG.md)
- E137 verdict / FULL / audio (detail in RUN-LOG.md)
- E141 verdict / G01 / workflow (detail in RUN-LOG.md)
- E142 verdict / G01 / workflow (detail in RUN-LOG.md)
- E145 verdict / FULL / context (detail in RUN-LOG.md)
- E147 verdict / FULL / workflow (detail in RUN-LOG.md)
- E242 verdict / CHAIN4 / workflow (detail in RUN-LOG.md)

### Proposed (needs review, not a rule yet)

- E104 proposed: qa_fail / G23 / prop_identity (detail in RUN-LOG.md)
- E112 proposed: rule_gap / G02 / anchor (detail in RUN-LOG.md)
- E114 proposed: rule_gap / G02 / workflow (detail in RUN-LOG.md)
- E116 proposed: qa_fail / G02 / ref/style (detail in RUN-LOG.md)
- E173 proposed: qa_fail / G01 / workflow (detail in RUN-LOG.md)
- E186 proposed: qa_fail / G01 / context (detail in RUN-LOG.md)
- E187 proposed: qa_fail / G01 / visual (detail in RUN-LOG.md)
- E207 proposed: qa_fail / G03 / ref/style (detail in RUN-LOG.md)
- E222 proposed: verdict / G01-G04 / workflow (detail in RUN-LOG.md)
- E225 proposed: rule_gap / G01-G04 / workflow (detail in RUN-LOG.md)
- E240 proposed: rule_gap / S01 / workflow (detail in RUN-LOG.md)
- E282 proposed: rule_gap / G03 / workflow (detail in RUN-LOG.md)
- E306 proposed: rule_gap / G02,G03 / workflow (detail in RUN-LOG.md)
- E329 proposed: rule_gap / G02 / workflow (detail in RUN-LOG.md)
- E331 proposed: rule_gap / G02 / gate (detail in RUN-LOG.md)
- E335 proposed: rule_gap / G03 / workflow (detail in RUN-LOG.md)
- E336 proposed: rule_gap / G03 / workflow (detail in RUN-LOG.md)

### Archived (pre-v2 history, 17 events)

_One line per layer. Evidence stays in `RUN-LOG.md` / the JSONL log._

- anchor (1x, E143-E143): evidence in RUN-LOG.md
- audio (1x, E140-E140): evidence in RUN-LOG.md
- job_json (1x, E005-E005): evidence in RUN-LOG.md
- ref/style (2x, E079-E121): evidence in RUN-LOG.md
- workflow (12x, E002-E125): evidence in RUN-LOG.md
