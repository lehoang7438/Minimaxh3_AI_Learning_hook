# G03 gradient root-cause trace (27/11/2026)

Read-only. Evidence = exact prompts queued to ComfyUI (`/history/<job_id>`), not files on disk,
plus recorded QA verdicts. No GPU job was queued during this trace.

## Version matrix — one factor at a time

| Version | job / seed | Shot size | Scene / flat-surface wording | Phone wording | Recorded flatness verdict |
|---|---|---|---|---|---|
| G02 v2 (reference) | `1005c5e3` / 20263401 | wide | `one thin solid bone-white ceiling strip … one flat muted-teal floor runner`, `plain solid oval windows`, rows 27/28 1+1 | no phone | **PASS** — approved flat baseline (E273/E274) |
| G03 v1 | `eb839233` / 20263501 | medium | short `one dark night passenger cabin … one thin ceiling strip` + flat runner | `lying lit` / `one glowing phone`, static state | no gradient FAIL recorded at the time (older QA; **not** re-compared against the strict G02 baseline) |
| G05 v1 | `21989dcd` / 20263602 | medium | same short Scene, one-tone contract | `phone still glows`, static state | only face FAIL recorded (eyebrows + nose); no gradient FAIL recorded |
| G03 v2 | `d64c47c3` / 20263701 | medium | same short Scene | **new event clause:** `The phone screen lights up by itself …` + `the lit phone still lies untouched` | **FAIL 1** vs G02 baseline (E283) |
| G03 v3 | `48004c76` / 20263901 | medium | same short Scene | event clause rewritten: `screen changes by itself … only the flat content inside the screen changes and the cabin keeps its same one-tone surfaces` | **FAIL 2** — gradient persists (E285/E286) |
| G03 v4 | `fc194b2d` / 20264101 | medium | Scene upgraded to **byte-identical G02 flat wording** (E287) | `screen changes by itself` retained | **FAIL 3** — gradient persists, **plus new regression**: both mitten hands support the phone f01–f14 and head lifts f05–f08 (E291) |

## Factors eliminated by the existing evidence

1. **Scene wording (E287) — disproved.** G03 v4 `Scene:`/`Props:` flat-surface text is byte-identical
   to approved G02 v2 (`plain solid oval windows`, `one thin solid bone-white ceiling strip`,
   `one flat muted-teal floor runner`), yet v4 still ramps. A fifth Scene rewrite cannot be the fix.
2. **The words `lit`/`glowing` alone (E283) — disproved as sufficient.** G03 v1 and G05 v1 both
   describe a glowing/lit phone and neither was recorded as a gradient FAIL. Removing `lights up`
   in v3 only softened the ramp; it did not remove it. Caveat: v1/G05 v1 were not re-measured with
   the strict G02-baseline comparison later applied to v2–v4, so this eliminates the *vocabulary*,
   not every property of the earlier clips.
3. **Medium framing alone — not sufficient.** G03 v1 and G05 v1 are medium shots without a
   recorded gradient FAIL; G02 v2 wide is flat. Changing wide→medium is not, by itself, the trigger.
4. **Phone / passengers presence — not sufficient.** Present in G03 v1 and G05 v1.
5. **Prompt length — not sufficient.** G05 v1 is 4239 chars and was not flagged for gradient;
   G02 v2 is 3426 chars and is the flat baseline.
6. **Seed alone — unproven and not isolatable without a render.** v2/v3/v4 each changed the prompt
   as well as the seed, so there is no same-prompt/two-seed pair. GPU is on `qa_hold`; no test was run.

## Remaining ranked hypothesis (not proven; no new render allowed)

- **Prime suspect: event semantics, not light vocabulary.** The exact change that first
  accompanies FAIL is v1 → v2: a *static* lit phone becomes `The phone screen lights up by itself`
  / `lit phone still lies untouched`, i.e. an autonomous **change** event. v3 replaced `lights up`
  with `changes by itself` and kept the event; v4 kept it. H3 can be reading a changing screen as
  a light event and spilling a luminance ramp onto the oblique ceiling/floor planes. No prompt-only
  rewrite that keeps a "screen changes" event has been shown flat against the G02 baseline.
- **Secondary contributor: explicit depth wording in v4** (`front near the camera and tail far
  away`) may raise/sustain the ramp; it was added only in v4, so it cannot explain v2/v3.
- **Separate, localised regression:** v3 → v4 changed only Scene/Props and the face clause, and
  v4 alone gained hands-on-phone + head-lift. The E287 Scene rewrite is therefore the source of
  that regression, independent of the gradient.

## Consequence

Two prompt-only hypotheses have been *tested and disproved* (E283 light wording, E287 Scene
wording). The next action must change the **composition/anchor strategy** (approved G02 flat plate
as ref, `continue_from` G02, or a different shot class), or isolate the event-semantics hypothesis
with one controlled render — that choice belongs to the user under E271. Treatment of this trace
is recorded as E296 (elimination) / E297 (ranked hypothesis).
