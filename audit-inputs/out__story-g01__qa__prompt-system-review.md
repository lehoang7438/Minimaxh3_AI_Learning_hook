# G01 prompt-system review (E267)

User directive: "càng sửa di chuyển càng dở vậy, xem lại hệ thống prompt đi ... nó phải giật giật cổ tay giật giật ngón tay, máu loang lổ." No GPU until this review is approved.

## Root causes found in code

1. **The ambience line cancels the beats.** `dialogue_text()` line 452 unconditionally appends
   `AMBIENCE = "Small subject motion and the camera move continue evenly for the whole shot."`
   after all motion beats. In G01 the beats say "snaps up / drops back / two quick unequal jerks /
   one last sharp spasm"; the final line says motion continues evenly. H3 follows the global
   last instruction and smooths everything into a dolly. This is why v6→v7→v8→v9 each got
   *less* jerky as the beat wording got stronger.

2. **Smooth adverbs outnumber jerk cues six to three.** Style contract: "camera slides slowly ...
   hand lifts and settles". `CAMERA_TEXT_OVERRIDE['G01']`: "a slow short pan". Beat 1: "camera
   begins a slow short pan". Beat 2: "camera has slid closer". Beat 3: "camera settles". Action:
   "slides slowly ... eases closer ... hand grows larger". The remaining cues are "snaps/jerks",
   so H3 resolves the conflict toward continuous camera travel.

3. **The beat engine cannot express more than three events.** `dialogue_text()` hardcodes
   `positions = ((0.0,0), (45% of end,1), (end,2))` for any `len(beats) > 2`. Adding extra beats
   to `BEAT_OVERRIDE` is silently ignored. A real jerk needs snap–hold–drop–hold–snap–hold;
   with only three spaced timecodes H3 interpolates smoothly between them.

4. **Beats describe camera states, not subject state changes.** They say "the camera begins /
   has slid / settles". The requested motion is wrist and finger events. Beats must name the
   part that moves and the frozen hold between snaps.

5. **No vocabulary for blotchy blood.** "generous flat dark-red blood fills every notch and
   spreads across" produced four clean geometric patches. "Máu loang lổ" needs irregular
   blotches of assorted sizes, ragged edges, separate spots and short streaks, still flat fills.

6. **G01 contract primes faces that are not on screen.** The insert contract still contains
   "Faces show two solid dot eyes ... no eyebrows, no nose, no eyelashes." with zero characters
   in the shot; this is a known prime for passenger/face intrusions and should be removed for
   characterless inserts.

7. **The linter cannot catch the contradiction.** `lint_h3.ps1` checks fields, timecodes and
   contract position but not "evenly/smoothly/slowly" co-occurring with "snap/jerk/flick", so
   every contradictory prompt shipped as PASS 0 warning.

## Proposed systemic fix (one render, reuse r8, no new asset)

- Add a per-shot `MOTION_MODE = "jerk"` path. For jerk shots, `dialogue_text()` appends a
  `JERK_AMBIENCE` line ("the wrist and fingers hold perfectly still between snaps; no
  continuous drift") instead of `AMBIENCE`, and the style contract drops all "slides slowly"
  wording.
- Generalise beat positions to `len(beats)` explicit fractions with short inter-beat gaps, so
  G01 can carry 5–7 discrete snap/hold beats inside 10 s with increasing timecodes.
- Rewrite G01 beats as wrist/finger state changes: snap up and freeze, drop and freeze, two
  rapid unequal wrist jerks with fingers flicking open and closed, final spasm, hold.
- Lock the framing again *only after* removing the "evenly" line; with discrete beats and no
  dolly wording, the arm must supply the movement. (v8 failed because the locked camera was
  paired with `AMBIENCE_LOCK`, which also said motion continues evenly.)
- Add blood vocabulary: irregular dark-red blotches of assorted sizes, ragged edges, separate
  spots and short streaks scattered over hand, wrist and forearm, still flat fills.
- Remove the face clause from characterless insert contracts.
- Add a linter rule: jerk/snap/flick beats plus evenly/smoothly/slow drift = FAIL.

No render until the user approves this plan.
