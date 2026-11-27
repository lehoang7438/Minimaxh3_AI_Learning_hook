# Manual re-check of Big Pickle's prompt consistency audit (27/11/2026)

Reviewer required hand-reading 3 FAIL + 3 PASS before trusting a cheap model's verdict. Sources on this machine, not the agent summary.

## FAILs confirmed

- **G02 props:** exact queued payload job `1005c5e3` contains `three generic passengers are composited later into the seats other than 27A`, while `cabin-map.json` says that phrase is QA metadata only, never prompt text. TRUE FAIL.
- **G03 wardrobe:** `art/part1-spec.json` shot G03 has layer outfit `khang-navy-longsleeve`, but `prompts/part1-rebuilt/G03.txt` has zero `khang:` label and zero appearance/wardrobe clause (only `Khang` in action text). G05 has `khang:` + navy long-sleeve, so same-plate shots are structurally inconsistent. TRUE FAIL.
- **G04 light:** current prompt still carries `one or two small emitting fixtures, cool dim slate walls clearly lighter than the navy seats` (superseded by E273 flat contract); exact queued G04 payload has the same wording. TRUE FAIL.

## PASSes confirmed

- **G01:** 5097-char prompt has zero passenger / four-seat / rows-27 / `khang:` / face clauses — correct for the under-seat insert.
- **G03 props:** `flat phone screen` + `bone-white phone` present on lap. PASS.
- **G05 wardrobe:** `khang:` label + navy long-sleeve + flat phone screen present. PASS.

## Extra finding the audit missed

G04 current prompt still says `Cabin rows hold 2+2 seats` while cabin-map and G02/G03/G05 say 1+1 / two rows / four seats. Big Pickle marked G04 layout PASS because `phone_ins` was excluded from the layout check. The sentence is a visible contradiction and must be reported FAIL / CHƯA CHỐT, never silently accepted.

## Conclusion

The report is usable as a triage list, not as evidence. Its 6 FAILs survive manual sampling; one extra visible FAIL was missed. This check changed no prompt, context, spec, ALH status or GPU state.
