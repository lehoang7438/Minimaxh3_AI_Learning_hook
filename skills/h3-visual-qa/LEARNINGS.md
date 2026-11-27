# Learnings - h3-visual-qa

## Auto-learned (ALH)

_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. **Only `Accepted rules` are active.** Detail/verdicts are in `RUN-LOG.md` and the log; a rule is mandatory only after it is mirrored into `SKILL.md` / `GLOBAL-RULES.md`._

### Accepted rules (active)

- [E136] ALH:E136 — Fix a widened INS shot at the source with a dedicated QA-passed INS first-frame plate and positive cast-count lock; never patch frames.
- [E153] ALH:E153 — Hy4 QA blocker 26/11: subagent calls with agent=general and no explicit model use a non-vision model; read tool returns no image support for every PNG, so agent returned script_fidelity=MISSING and FA…
- [E158] ALH:E158 — Machine color_count quantize 128x128 PASS nhưng Hy4 thấy gradient/halo/vệt sáng vô nguồn.
- [E168] ALH:E168 — Hy4 CHI la mat mo ta, KHONG duoc tu cham PASS/FAIL va KHONG duoc de xuat fix.
- [E170] ALH:E170 — User override: pov-shoulders-flat-r1 FAIL.
- [E260] ALH:E260 — G01 v6 FAIL: real hand and ragged bite pass, but cuff rendered pale silver not navy, nails/tone drifted light, and the jerk reads as zoom/shift. Override consumed; stop until a new user override.
- [E265] ALH:E265 — G01 v8 FAIL: teal removed, but the cuff regressed to grey and all motion died under a locked camera (MAE 1.212). Best next combination is the v7 camera wording with the r8 dark-red-only reference; no GPU until a new override.
- [E266] ALH:E266 — Override-v9: user picked the v6 motion as best; reuse the teal-free r8 prop, restore the v6 recess-pan/snapping-arm motion text, keep the no-cool-edge dark-fill contract and make generous dark-red blood the only brighter shape. One render only, no new asset, no v10.
- [E269] ALH:E269 — G01 v10 FAIL only on the wide navy cuff: the E268 jerk-hold motion and blotchy-blood fixes are confirmed by Hy4 and the 12 fps probe. No GPU until the user accepts v10 with the cuff residual or grants a new override.
- [E271] ALH:E271 — E271 QA protocol: remember the user requirements, use the skills and ALH, QA carefully, and auto-chot PASS when clean; never ask for chot on a clean QA, only on evidence-backed FAIL, ambiguity or override boundary.
- [E272] ALH:E272 — G01 v11 auto-PASS per E271: E270 lateral under-seat pan verified (red centroid -14.9px, bbox height slope -0.001, Hy4 no enlarging hand/passenger-level view); E268 snap-holds and blotchy blood intact; wide-cuff grey residual disclosed at v10 is a known accepted deviation; no v12.
- [E274] ALH:E274 — E274 G02 v2 auto-PASS: E273 gradient cleared by flat contract; four figures and hand-slip beat intact. Receding empty seats/windows and flat bright-area share recorded as accepted deviations, not a second FAIL. No v3.
- [E276] ALH:E276 — E276 G03 auto-PASS first render: E275 flat contract pre-fix worked, Khang bowed asleep in 27A with lit phone (one cake + one group photo, no text), three other passengers fixed, no fifth person; vignette falloff accepted, no retry. G05 continues from this last frame.
- [E290] ALH:E290 — E290 prompt audit must compare each prompt against ONE structured source of truth (cabin-map/global-context) by set_id, not prompt-vs-prompt; dimensions = light tier/luma band, seat layout, geometry/camera, palette hex, prop state_chain, wardrobe/feet/proportion, language leakage. Seat layout 3+3/2+2/1+1 still contradictory across rules: report CHUA CHOT, do not pick. Big Pickle output needs manual 3 FAIL + 3 PASS verification.
- [E295] ALH:E295 — E295 Big Pickle audit hand-checked: 3 sampled FAIL (G02 composited-later leakage, G03 missing khang wardrobe clause, G04 superseded fixture/slate light) and 3 sampled PASS (G01 clean insert, G03 phone props, G05 khang wardrobe clause) all confirmed. Extra miss: G04 still says 2+2 seats while cabin-map/G02/G03/G05 say 1+1. Cheap-model PASS is not evidence; sample by hand before acting.

### Accepted run records (evidence, not rules)

- E134 verdict / G01 / qa_reviewer (detail in RUN-LOG.md)
- E138 verdict / G14 / spec (detail in RUN-LOG.md)
- E139 verdict / G01 / anchor (detail in RUN-LOG.md)
- E146 verdict / G01 / prompt (detail in RUN-LOG.md)
- E169 verdict / G18 / qa_reviewer (detail in RUN-LOG.md)
- E211 verdict / G03 / context (detail in RUN-LOG.md)

### Proposed (needs review, not a rule yet)

- E098 proposed: qa_fail / G02 / visual (detail in RUN-LOG.md)
- E105 proposed: qa_fail / G48 / palette_lock (detail in RUN-LOG.md)
- E106 proposed: qa_fail / G29 / camera_composition (detail in RUN-LOG.md)
- E111 proposed: rule_gap / UI / workflow (detail in RUN-LOG.md)
- E113 proposed: qa_fail / G02 / visual (detail in RUN-LOG.md)
- E129 proposed: verdict / G01 / qa_reviewer (detail in RUN-LOG.md)
- E135 proposed: qa_fail / G01 / prompt (detail in RUN-LOG.md)
- E291 proposed: qa_fail / G03 / clip (detail in RUN-LOG.md)

### Revoked (do NOT apply - kept for history)

- E284 REVOKED - DO NOT APPLY: warn_accepted / G02 / clip (detail in RUN-LOG.md)

### Archived (pre-v2 history, 4 events)

_One line per layer. Evidence stays in `RUN-LOG.md` / the JSONL log._

- prompt (1x, E094-E094): evidence in RUN-LOG.md
- spec_identity (1x, E060-E060): evidence in RUN-LOG.md
- visual (2x, E074-E075): evidence in RUN-LOG.md
