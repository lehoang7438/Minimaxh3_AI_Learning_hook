# Learnings - h3-prompt-writing

## Auto-learned (ALH)

_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. Only rules moved into SKILL.md are mandatory._

### Accepted (applied and verified - read as a rule)

- [E093] rule_gap / G02 / prompt - G02 eye QA FAIL fixed at prompt layer: old first line referencing Picture 1 at 00:00 made H3 open on a keyed character sheet. Replaced with explicit instruction to start from the supplied first-frame image. Plate was already ref slot 1; no asset or workflow change. Re-render G02 only.
- [E099] rule_gap / G01 / prompt - UI black-screen shot review: the contract said 'no text' while the tail allowed '00:00' (two opposite rules), the waveform had no colour on near-black navy, 'lips remain closed' and breathing SFX were emitted with no cast on screen, a flat graphic got handheld sway, and the Vietnamese scene description sat next to <d>[Vietnamese]. rebuild_prompts.py now merges allow_text into the contract ('no text except the on-screen timer 00:00'), states bone-white waveform + red recording dot + timer, gates SFX and the lips clause on cast presence, drops sway for ui shots, and writes an English ui_action(); 55/55 lint PASS.

### Archived (pre-v2 history, 1 events)

_Full text: `alh.py report --status archived`. One line per layer, latest kept._

- prompt (1x, E078-E078): User approved and promoted: object/colour denials like no plant and NO red anywhere must stay out of prompt_visible and remain QA metadata only; diagnose_shot.ps1 must check native exit codes and fail loudly; scene plate must be picture ref slot 1; every wardrobe clause must name its character; style contract appears once only.
- [E107] **rule_gap / G15 / prompt** - 55/55 rebuilt prompts carry Vietnamese outside <d>: spec description is Vietnamese and action_text copies it verbatim, mood_text falls back to the literal 'u am'. The rule promoted yesterday (E099) was only applied to the ui branch. Fix: description_en per shot (single source of truth in the spec), English mood map with 'cold and uneasy' fallback, and a linter FAIL on Vietnamese outside <d>.
- [E115] **rule_gap / G02 / prompt** - User approved a one-shot style trial: Flat-icon Storytime v3 for G02 only. Changes: 3 character refs (Khang + 2 male friends) + two female friends as flat silhouettes with dot eyes; style contract with two-value flat tone, icon-like edges, simple oval paddle hands instead of mitten/no-finger denials; wide pulled-back framing so five people fit; added flat restaurant details (amber panels/trim, 2 teal bars). No global bible change until user reviews. Cleanup: removed only superseded key retries and temp G02 frames; kept art/tests and out/part1. New seed 2026112603.
