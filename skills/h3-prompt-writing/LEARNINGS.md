# Learnings - h3-prompt-writing

## Auto-learned (ALH)

_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. **Only `Accepted rules` are active.** Detail/verdicts are in `RUN-LOG.md` and the log; a rule is mandatory only after it is mirrored into `SKILL.md` / `GLOBAL-RULES.md`._

### Accepted rules (active)

- [E093] ALH:E093 — G02 eye QA FAIL fixed at prompt layer: old first line referencing Picture 1 at 00:00 made H3 open on a keyed character sheet.
- [E099] ALH:E099 — UI black-screen shot review: the contract said 'no text' while the tail allowed '00:00' (two opposite rules), the waveform had no colour on near-black navy, 'lips remain closed' and breathing SFX were…
- [E156] ALH:E156 — Empty-panel and POV v3 shots must use per-shot positive beats and composition text.
- [E161] ALH:E161 — Panel rong va voices ngoai khung: cau phu dinh no people / no figure bi H3 ve nguoc.
- [E162] ALH:E162 — Xoa moi cau xoa doi tuong khoi prompt_visible: ACTION_OVERRIDE BEAT_OVERRIDE cabin-map scene objects va light.
- [E171] ALH:E171 — Mot prompt H3 chi mot hanh dong chinh.
- [E172] ALH:E172 — G04 FAIL do 3 beat camera drifts a little closer nhan len nhau thanh zoom cong don; khung last dien thoai va vien man hinh ra khoi khung, mat chu the phone screen cua script; zoom vuot xa 3%.
- [E176] ALH:E176 — Style contract cua global-context co cau flat amber restaurant accents ap cho MOI shot, keo vao cabin dem G01-G04 va co the prime mau am / nhan vat khong co trong script.
- [E178] ALH:E178 — G01 QA FAIL duoc user phan hoi tu preview ComfyUI va duoc Hy4 (seen, mo ta 3 khung) xac nhan: first co cau truc ghe va toan bo tay ao, mid mat cau truc ghe va vat the phong to, last tay ao bi cat mep …
- [E179] ALH:E179 — Sua G01 sau E178: truoc do cung 1 prompt co 3 lenh camera (camera line zoom 3% + beat drifts forward + ambience camera move continue) nen H3 cong don thanh zoom lon, mat cau truc ghe tu mid va cat tay…
- [E201] ALH:E201 — ALH E149 applied to G01-G04: Vietnamese mood outside <d> replaced with English (tense/gloomy) in rebuild_prompts.mood_text; all 4 prompts now have zero non-ASCII words and zero cabin-map negation clau…
- [E206] ALH:E206 — G02 prompt had a contradictory hand beat: one clause said the hand withdraws beneath the seat at the lower edge, the At 00:00 clause said it was already withdrawn; combined with the shared style contr…
- [E209] ALH:E209 — this is a horror film, so light and environment must be horror too - low-key, one or two motivated fixtures, slate walls lighter than navy seats, 60-75 percent flat shadow, heavy flat vignette; never …
- [E245] ALH:E245 — User rejected story-g01 G01 render: not scary enough; the bitten arm belongs UNDER the airplane seat; no object dragging in from the right edge - the CAMERA must pan/tilt toward that arm; the arm is b…
- [E247] ALH:E247 — G01 v2 near-passable but camera angle still shows seated passengers on the plane and the ambient light is not scary enough; asked agent to self-review before reporting.
- [E248] ALH:E248 — For G01 open already inside the under-seat recess, let the camera pan within the dark gap, and enforce one solid mitten, dot eyes without brows or nose, one dim cool edge light and 65-75 percent near-black.  [supersedes E182,E204]
- [E250] ALH:E250 — G01 v4 uses one unbroken navy-cuffed mitten with explicit snap-up/hold/drop and two uneven jerks; re-render once with a fresh seed, then stop at the retry cap.
- [E251] ALH:E251 — G01 v4 failed at the retry cap because the prop source of truth still describes four fingers and the workflow attached no QA silhouette; fix the element/cabin-map/asset/node layer before any v5 render.
- [E267] ALH:E267 — User directive: stop swapping words/seeds. Review the prompt system itself: every motion fix made the movement more fake. Target motion is jerky wrist + jerky finger snaps with blotchy splattered blood. No GPU until the composition review and proposed fix are presented.
- [E270] ALH:E270 — E270 override v11: add one short lateral camera slide from the low under-seat angle at one constant scale; keep E268 jerk-hold wrist/finger motion and blotchy blood; no forward dolly, no passenger-level view, no new asset, one render.
- [E273] ALH:E273 — E273 G02 v1 FAIL on smooth gradient (46 percent dark vs 60-75 contract) and extra receding rows. Fix one prompt layer: G02_STYLE_CONTRACT with one flat tone per surface, no grey ramp, only rows 27/28 and four windows, plus LIGHT_SUPPRESS to drop the duplicate global Light line. One fresh-seed retry; no new asset.
- [E275] ALH:E275 — E275 pre-fix: G03/G05 share the G02 seat-27A cabin plate, so apply the proven flat G02_STYLE_CONTRACT and LIGHT_SUPPRESS before their first render instead of spending two GPU jobs rediscovering the gradient FAIL.
- [E277] ALH:E277 — E277 pre-fix: seated shots must not inherit standing-walking beats or the bible standing-pose sentence. G05 gains three seated wake-up beats and SEATED_SHOTS swaps the standing clause for a seated posture; rebuilt prompt lint PASS before queue.
- [E280] ALH:E280 — E280 user held state: G03 = already asleep from frame 1, phone already on lap untouched (no hand places or touches it), screen lights up by itself with a birthday cake surrounded by a group photo. Also strip the tapered-nose/eyebrow clauses from G03/G05 contracts after Hy4 found drawn nose+eyebrows in G05 mid/last (FACE_FLAT_CONTRACT). Both prompts rebuilt lint PASS before re-render.
- [E281] ALH:E281 — E282 duration fits action: DURATION_OVERRIDE G03=6s G05=8s; G03 beats use {tc} so no timecode exceeds the short clip. G01 7 snaps and G02 hand-slip keep 10s. Both rebuilt prompts lint PASS at their own seconds.
- [E283] ALH:E283 — E283 G03 v2 FAIL: ceiling/floor gradient clearly heavier than the approved G02 v2 flat baseline (E273 recurrence); root trigger is the lights-up/lit-phone wording that primes H3 light spill. Prompt-only fix: screen changes from plain pale to flat picture, cabin keeps one-tone surfaces; rebuilt 3465 chars lint PASS 0 warning. v2 backed up as evidence; re-render once with fresh seed 20263901.
- [E285] ALH:E285 — E285 horror logic over literal compliance: G02 is the G01 hand aftermath - the same creepy arm stays deep under 27A, only a sliver peeks then eases back into black, nobody notices, G02 wide view unchanged. E284 revoked; prompt-only fix + 6s duration fit.  [supersedes E284]
- [E286] ALH:E286 — E285 G02 horror logic: the G01 creepy arm stays deep under 27A, only a dark-bone/navy-cuff sliver peeks then eases back, nobody reacts, wide G02 view unchanged. Prompt-only rewrite of ACTION/BEAT + 6s duration fit; v2 superseded, re-render after G03 v3 QA.
- [E287] ALH:E287 — E287 G03 gradient persists in v3 (v2-vs-v3 comparison: softer but structurally same), so lights-up wording was not the trigger. Root cause = Scene line: G02 flat set names solid bone-white ceiling strip + flat muted-teal floor runner; G03 seat_27a only said thin ceiling strip in a dark cabin. Fix one prompt layer: SCENE_OVERRIDE[G03] reuses the approved G02 geometry/objects wording plus the phone. Rebuilt 3591 chars lint 6s PASS 0 warning. Render v4 seed 20264101.
- [E288] ALH:E288 — E288 pre-fix G05 before its first render: same 27A plate inherits SCENE_OVERRIDE flat-surface anchors and drops lit/glowing-phone wording, so the E273/E287 gradient and light spill are not rediscovered after a GPU job. Rebuilt 4559 chars, lint 8s PASS 0 warning.
- [E289] ALH:E289 — E289 G01 v11 FAIL of E270: no visible camera pan; Hy4 saw only wrist/finger snaps with the seat edge static. Lateral-slide wording was too weak; add explicit parallax reference (fixed jagged seat edge and floor gap visibly travel sideways while hand keeps size) in style contract, camera line, action and jerk ambience. Rebuilt 5097 chars lint 10s PASS 0 warning. Render v12 fresh seed after G03 v4.
- [E294] ALH:E294 — E294 numbering correction: E292 = gradient payload diff / E293 = reviewer 3-layer architecture. Ignore the E293 label inside E292 rule text.
- [E296] ALH:E296 — E296 exact /history payload trace eliminates three G03 gradient hypotheses: E287 Scene wording (v4 byte-identical to approved G02 v2 yet still FAIL), E283 lit/glow vocabulary (G03 v1 and G05 v1 had glowing phones with no recorded gradient FAIL), medium framing and phone presence (both in v1/G05); seed-only cannot be isolated without a render. Fifth Scene rewrite or glow-word swap is not a valid fix.
- [E298] ALH:E298 — E298 reviewer correction + no-wait fixes: 3-layer architecture is useful for cheap audit but does NOT explain the gradient (style blocks already byte-identical). Applied: remove composited-later pipeline note from global-context and rebuild source; FACE_FLAT_CONTRACT on G02 v3 so the chain shares one face law; G04 flat phone-insert contract with no 2+2/seat-window assertion; inject Khang appearance+wardrobe block into G03 prompt-side; G03/G05 block eyes changed from oval to dot to match contract. All 5 prompts rebuilt, lint PASS 0 warning.

### Accepted run records (evidence, not rules)

- E144 verdict / G01 / prompt (detail in RUN-LOG.md)
- E191 verdict / G01 / prompt (detail in RUN-LOG.md)
- E246 verdict / G01 / prompt (detail in RUN-LOG.md)

### Proposed (needs review, not a rule yet)

- E107 proposed: rule_gap / G15 / prompt (detail in RUN-LOG.md)
- E108 proposed: rule_gap / G15 / prompt (detail in RUN-LOG.md)
- E115 proposed: rule_gap / G02 / prompt (detail in RUN-LOG.md)
- E124 proposed: rule_gap / G01 / prompt (detail in RUN-LOG.md)
- E149 proposed: rule_gap / FULL / prompt (detail in RUN-LOG.md)
- E220 proposed: rule_gap / G01-G04 / prompt (detail in RUN-LOG.md)
- E228 proposed: rule_gap / G01-G04 / prompt (detail in RUN-LOG.md)
- E232 proposed: rule_gap / G01-G04 / prompt (detail in RUN-LOG.md)
- E292 proposed: rule_gap / G03 / prompt (detail in RUN-LOG.md)
- E293 proposed: rule_gap / ALL / gate (detail in RUN-LOG.md)
- E297 proposed: rule_gap / G03 / prompt (detail in RUN-LOG.md)
- E300 proposed: rule_gap / G03 / prompt (detail in RUN-LOG.md)

### Revoked (do NOT apply - kept for history)

- E279 REVOKED - DO NOT APPLY: verdict / G03 / prompt (detail in RUN-LOG.md)

### Archived (pre-v2 history, 2 events)

_One line per layer. Evidence stays in `RUN-LOG.md` / the JSONL log._

- prompt (2x, E078-E278): evidence in RUN-LOG.md
