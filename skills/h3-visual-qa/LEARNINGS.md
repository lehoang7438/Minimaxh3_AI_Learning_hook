# Learnings - h3-visual-qa

## Reviewed / promoted 2026-11-27 (user approved)

- **Smart chain cut (user: "rule này khá hay"):** H3 thực hiện cú cắt ngay trong clip khi shot sau dùng `--continue-from` shot trước, **chỉ khi** cùng chain + cùng `set` + cùng lighting tier (`cold_morning` / `cold_night` / `warm_flashback` / `unprotective_night`) + không ranh giới UI đen. Nhảy môi trường hoặc nhảy tier sáng → render fresh. Tool quyết định: `art/tests/smart_chain.py` (read-only; báo 0 downgrade trên 16 shot đã nối và 17 shot đủ điều kiện nối thêm). Khi đổi sang continue: 175 frame → 153 output, dời timecode +0.917 s, seed mới, lint lại. Rule bắt buộc nằm ở `freevideo-runner/SKILL.md` §8.6 và cross-ref ở `h3-visual-qa/SKILL.md` phần Chain QA.

## Auto-learned (ALH)

_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. Only rules moved into SKILL.md are mandatory._

### Proposed (review, then set accepted or revoked)

- [E113] **qa_fail / G02 / visual** - G02 attempt 5: restoring 5 keyed character refs fixed cast/action (3 friends clapping, correct wardrobe) but reintroduced a large ceiling spotlight beam and floor gradient, so h3-visual-qa item 1/2 FAIL. Learned: keyed sheets in Media drive both cast fidelity and the beam. Attempt 6 will keep the improved prompt (named cast + motion beats) and drop character refs via global-context shot.characters=[] (context layer, no server restart, no Python window), combining attempt 3 no-beam with attempt 5 cast text.

- [E111] **rule_gap / UI / workflow** - h3-visual-qa only scored keyframes, so a frozen card, a wrong duration, a red wash or a 100 percent red frame could ship unnoticed. Added clip_qa.py (duration vs spec, fps, canvas, mean motion, longest freeze, red share, red wash, luma) and motion_grid.py (start/mid/end of every clip in one image). First full run: 55 clips, 0 fail, 3 real warns (G15 2.6 s under the 4 s rule, G15/G17 red wash, G48 red wash).

- [E106] **qa_fail / G29 / camera_composition** - G29 placed khang-sheetB at h 0.48 y 0.92 and pz-sheet at h 0.34 y 0.90: 2 percent apart on the same foot line but 30 percent shorter, so the infected reads as a child next to a giant. relative_height is 1.00 for both. Rule: two sprites on the same foot line must share scale; if one is meant to be farther, move its feet line up as well (h 0.42 at y 0.86 for G29).

- [E105] **qa_fail / G48 / palette_lock** - edge_tint adds red at frame edges for the whole clip (animate_pilot: r += edge*200, g/b *= 1-edge*0.85). Measured red-dominant share: G15 42.2 percent, G17 46.1, G21 4.6 at 0.18, G48 69.1 at 0.75. Red is reserved for blood, infected eyes and the recording dot, and the radial falloff is a gradient. G48 is the only shot whose description asks for a red border: it should be a flat stepped ring, not a gradient; remove the tint from G15/G17/G21/G47.

- [E098] qa_fail / G02 / visual - G02 attempt 4: frame 1 is the correct flat restaurant plate (no pink sheet); mid has no amber beam or gradient, so style/anchor/palette/wardrobe/anatomy all PASS. FAIL remains at h3-visual-qa item 5: two friends face away from camera with backs filling frame, no visible clapping or beer glasses in hand, friend_beer and friend_clap are absent; spec requires three friends standing around the table holding beers and clapping. Machine gates PASS (12.25s, 24fps). User asked to stop after this QA for workflow improvement; do not re-render or change any layer.

### Archived (pre-v2 history, 4 events)

_Full text: `alh.py report --status archived`. One line per layer, latest kept._

- prompt (1x, E094-E094): G02 attempt 2 eye QA still FAIL: frame 1 (t=0.2s) remains a pink character sheet 72.0% pink despite replacing the Picture-1 prompt prefix with an explicit start-from-first-frame line. Mid frame correct restaurant with 5 friends clapping, cake, 4 glasses, 2 teal bars. Machine gates all PASS. Prompt-layer fix did not move the first-frame behaviour; next fix must be the anchor/reference/seed layer: test plate-only references (drop keyed character refs from frame-1 conditioning) or a different first-frame anchor/seed. Do not change prompt again.
- spec_identity (1x, E060-E060): Part1 and part2 reuse shot IDs G21-G25 with different sets (lavatory vs cabin_chaos). visual_qa maps by shot ID only, so one cabin-map entry cannot satisfy both and produced 4 false FAILs. Fix by namespacing part2 shot IDs to P2G21-P2G34 across spec, prompts and context; no script hardcodes these IDs.
- visual (2x, E074-E075): Eye QA FAIL: first frame is a magenta-background standing character ref (not the restaurant plate); mid frame contains forbidden potted plants and red candles although prompt says no plant/no red. Machine gate all PASS.
