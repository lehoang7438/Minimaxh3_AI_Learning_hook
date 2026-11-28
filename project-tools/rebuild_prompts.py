"""Rebuild shot prompts from Spec + global context, following h3-prompt-writing.

Legacy prompt files are deliberately not inputs: the spec is the source of truth for
visual descriptions, dialogue, and sound effects. This writes clean 3-field prompts:
  style contract -> shot size/camera -> characters+wardrobe -> action+support -> mood
Dialogue is copied verbatim from the spec and tagged; soundscape is derived from the set
and SFX list. No legacy prompt is read.

    python art/tests/rebuild_prompts.py part1      # all shots in part1
    python art/tests/rebuild_prompts.py part2 G21  # one shot
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import h3_prompt_rules as rules

ROOT = Path(__file__).resolve().parents[2]
CTX = ROOT / "art" / "env" / "global-context-part{}.json"
SPEC = ROOT / "art" / "part{}-spec.json"
OUT = ROOT / "prompts" / "part{}-rebuilt"

# User-authored G02 detail pass (28/11). Authoritative over the generated
# contract text below. Only two mechanical adaptations from the user's text:
# `At ` prefixes so the linter/audit see six increasing timecodes, and the
# audit-required `from behind the back of seat 27A` phrase (still on the aisle
# centreline, so the centre-aisle composition is unchanged), the `Props:` label
# with the composer's structured objects string, and the exact E324 phrase
# `clearly readable flat bone-tone strip`. Withdrawal beat widened from
# 00:02.900 to 00:03.000 per the user's render note; the 00:03.100 alternative
# is kept in out/story-g02-v6/qa/ for comparison.
G02_USER_PROMPT = """integrated_multimodal_description: Vertical 9:16 flat 2D storytime horror, icon-like. Solid flat colour fills with at most one tone per surface, clean edges with bold uneven black outlines; no gradient, no shading, no soft shadow, no blur, no 3D, no texture, not realistic. Palette restricted strictly to near-black navy, bone white, and one muted teal. Night-horror lighting is purely flat solid colour: 78 to 85 percent of the frame is held in flat near-black shadow shapes with heavy flat near-black corners. The ceiling, closed overhead bins, side walls, plain solid oval windows (two total), and far curtain are completely unlit and blacked out in one uninterrupted flat pitch-black ink-navy fill. The entire upper half of the frame, including the ceiling, closed overhead bins and upper walls, is submerged in that same blacked-out midnight navy with zero illumination. Every oval window is one flat solid pitch-black ink-navy fill, the same darkest tone as the ceiling. The only brighter elements are the narrow muted-teal floor runner along the empty central aisle and the clearly readable flat bone-tone mitten-shaped strip of the small visible forearm fragment inside the recess under the near-left seat.
[Shot 1] Use <Picture 1> as the identity and flat-fill reference for the G01 bitten forearm (one uniform bone tone, wide near-black navy cuff as the darkest fill, same flat fills inside the chewed notches, one solid mitten shape with no separated fingers). Scene: one single visible row of a narrow-body passenger cabin, with one seat on each side of the empty central aisle (28A left, 28C right), 1+1 layout, two seats total, plain solid pitch-black oval windows, closed overhead bins and one far curtain. The camera stands directly behind this only row, with the aisle ahead of the camera completely clear. Two relaxed adult passengers (1:6.5 to 1:7 head-to-body, continuous outer outlines, gently curved joints) sit in 28A and 28C, seen strictly from behind with solid black hair silhouettes covering the back of their heads and plain dark near-black navy or muted-teal uniform backs; the number of visible figures stays fixed and they remain motionless facing away for the whole shot.
Props: one narrow flat muted-teal floor runner lying on the cabin floor; two generic passengers seated in seats 28A and 28C, both seen strictly from behind; the central aisle stays empty.
Camera & Action: Starts at under-seat level for the G01 overlap, then hard-cuts to a single locked wide shot at standing eye level on the empty aisle centreline directly behind the only visible row, looking forward between the rear faces of its two seats (lower left and lower right). The open space below the left seat cushion is fully visible and unobstructed, so the under-seat recess reads clearly. After the hard cut, the camera stays locked at one fixed scale and framing until the last frame; depth comes only from flat overlap and straight perspective lines. All timecodes are on the untrimmed generation timeline (the delivered clip starts after the 22 overlap frames are removed):
At 00:00.000: Frame 1 holds the exact G01 under-seat view from <Picture 1>, with the bitten forearm lying flat in the dark recess under the near-left seat.
At 00:01.200: Hard cut to the locked standing eye-level wide shot on the aisle centreline directly behind the only visible row; the two seat backs sit at the lower left and lower right, the aisle between them stays empty, and the two rear-facing passengers sit beyond. Inside the black recess directly under the near-left seat, the same bone-tone mitten-shaped strip and wide near-black navy cuff edge remain clearly readable through the open gap below the seat cushion, parallel to the floor, wholly inside the seat footprint and away from the open aisle; the teal runner beside the left seat stays empty.
At 00:02.600: The bone-tone mitten strip and navy cuff draw a short, readable distance farther inward under the left seat cushion, away from the aisle opening.
At 00:03.000: That same strip and cuff slide fully out of sight into the black recess under the left cushion.
At 00:04.100: The under-seat recess is completely empty; the wide rear cabin holds still with framing and scale unchanged.
At 00:05.700: The cabin remains motionless until the end, with framing and scale unchanged.
The two-step inward pull under the near-left seat is the only motion after the cut. Mood: eerie dread.
overall_soundscape: A low aircraft engine hum and soft cabin ventilation continue underneath.
non_diegetic_music: N/A
"""

# Cues from the legacy prompts that reliably make H3 hallucinate.
BAD_CUES = {
    "ánh nến nhảy": "ánh nến là flat fill, không chùm sáng",
    "trong không trung": "trên mặt bàn, đáy ly tiếp xúc mặt bàn",
    "lơ lửng": "đặt chắc trên mặt bàn hoặc sàn",
    "ánh nến": "màu amber phẳng",
    "màn hình hồng": "màn hình hai vạch teal trên nền navy",
}
# The style contract is NO LONGER hand-written here. It is derived from the same
# asset-contract.json + cabin-map.json master_plate used by the H3 Image asset jobs,
# so a video prompt and its anchor plate cannot disagree on seat count or lighting.
CABIN_STYLE_CONTRACT = rules.video_style_contract()
# E248 (user 27/11): G01 is a tight under-seat insert, not a cabin wide shot. The
# shared cabin contract prime H3 with rows, oval windows and visible figures, so the
# first frame opened on two seated passengers in warm light. This contract keeps the
# flat/horror law but names ONLY the recess, the arm and flat dark fills; E261 removed
# the cool edge light that bleached the navy cuff and nails in v6.
G01_STYLE_CONTRACT = (
    "Vertical 9:16 flat 2D storytime horror, icon-like. Solid flat colour fills with at "
    "most two tone values per surface, clean edges with bold uneven black outlines. "
    "Low-key night-horror lighting: irregular flat dark-red blood blotches are the only "
    "brighter shape and scatter across the hand, wrist and forearm; the wide torn navy cuff, "
    "the near-black nails and the uniformly dirty bone skin stay flat dark fills with no "
    "light edge, and 65 to 75 percent of the frame is held in flat near-black shadow shapes "
    "with a heavy flat vignette; the corners fall to near-black. "
    "Palette in this insert: near-black navy, one uniform dirty dark ash-grey bone tone and "
    "flat dark-red blood only; the cuff and nails are the darkest navy fills, darker than "
    "the skin, and every wound uses that same dark red with no second wound colour. The camera "
    "makes one clear short sideways pan low inside the same recess at one constant scale, so the "
    "hand keeps the same size while the fixed jagged seat edge and the dark floor gap travel "
    "visibly across the frame; the wrist and fingers snap between frozen holds. This is one tight "
    "insert under a navy airline seat: the visible surfaces are the seat underside, a flat "
    "navy floor gap and one bitten forearm; every other shape is flat near-black navy shadow. "
    "Hands are a realistic flat human hand with one thumb, "
    "four separate gently curved fingers, small gaps between them and near-black nails on "
    "every fingertip; the skin is one uniform dirty dark bone tone. The bite is "
    "ragged and chewed, several uneven chunks torn out of the hand edge with flat dark-red "
    "blood blotches of assorted sizes inside every notch, plus separate ragged spots and "
    "short streaks across the palm and wrist. Depth comes only from flat overlap; no gradient, no shading, no "
    "soft shadow, no blur, no 3D, no texture, not photoreal."
)
# E273: G02 v1 rendered smooth luminance ramps on the ceiling, walls and carpet
# (measured: only 46 percent of pixels below luma 40 versus a 60-75 percent contract)
# plus a receding row of extra seat backs and windows. The shared contract says
# "walls clearly lighter" and "one or two emitting fixtures", which invites that
# gradient. This override keeps the flat law but states the exact frame contents.
G02_STYLE_CONTRACT = (
    "Vertical 9:16 flat 2D storytime horror, icon-like. Solid flat colour fills with at "
    "most one tone per surface, clean edges with bold uneven black outlines. "
    "Night-horror lighting is FLAT solid colour, never a light effect: the ceiling, side "
    "walls, seats and floor are each one uniform flat fill, with no grey ramp and no "
    "bright-to-dark transition anywhere. The thin bone-white ceiling strip and the flat "
    "muted-teal floor runner are the only brighter shapes. 65 to 75 percent of the frame "
    "is held in flat near-black shadow shapes with a heavy flat vignette; the corners "
    "fall to near-black. Palette: near-black navy, bone white and one muted teal only. "
    "Cabin rows hold 1+1 seats and oval windows stand on BOTH sides. This view contains "
    "only the two rows 27 and 28: four seats and four oval windows in total, with no "
    "receding extra rows, no repeated empty seat backs and no extra windows behind them. "
    "All clothing is near-black navy, bone white or one muted teal. "
    "All hair is one solid black silhouette. Faces show two simple solid dot eyes and one "
    "short mouth line, with a small tapered nose visible in side profile. Human hands show "
    "four gently curved fingers with small gaps and one separated thumb, softly rounded "
    "tips, solid fill. Figures are relaxed adults with continuous outer outlines and gently "
    "curved joints, about 1:6.5 to 1:7 head-to-body. Backgrounds keep layered flat depth "
    "and one-point perspective. The number of visible figures stays fixed from the first "
    "frame to the last. Depth comes only from overlap and straight perspective lines; "
    "no gradient, no shading, no soft shadow, no blur, no 3D, no texture, not realistic."
)
STYLE_OVERRIDE = {sid: CABIN_STYLE_CONTRACT for sid in ("G02", "G03", "G04")}
STYLE_OVERRIDE["G01"] = G01_STYLE_CONTRACT
# E280: Hy4 saw drawn eyebrows and a nose on the lifted faces in G05 mid/last.
# The style contract itself primed the nose ("small tapered nose visible in side
# profile") and the bible denial "no eyebrows, no eyelashes" did not hold with H3.
# E298 (reviewer): retire the old "keep G02's passed contract untouched" exception.
# G02 v3 is a fresh render in the same chain, so all three cabin/phone shots must
# carry the same minimal-face law or the chain changes faces mid-shot sequence.
FACE_FLAT_CONTRACT = G02_STYLE_CONTRACT.replace(
    "Faces show two simple solid dot eyes and one short mouth line, with a small tapered "
    "nose visible in side profile.",
    "Faces show exactly two simple solid dot eyes and one short mouth line and nothing "
    "else drawn on the face.",
)
STYLE_OVERRIDE["G03"] = FACE_FLAT_CONTRACT
STYLE_OVERRIDE["G05"] = FACE_FLAT_CONTRACT
# E308/E309 (user 27/11): G02 is the G01 aftermath seen from behind seat 27A, and
# the frame must be darker than v3. Keep the flat law; only lower the value
# balance and shrink the two bright flat shapes. No fixture/wall-ramp wording.
# E324 (user 28/11, supersedes E285/E307/E310 visibility clause, status_by user):
# the G01 arm must be READABLE, not a 1-2 cm almost-unnoticeable sliver; never
# a separated-finger hand. Palette, rear axis and 22-frame cut are unchanged.
G02_REAR_DARK_CONTRACT = (
    FACE_FLAT_CONTRACT.replace(
        "65 to 75 percent of the frame is held in flat near-black shadow shapes with a heavy flat vignette; the corners fall to near-black.",
        "78 to 85 percent of the frame is held in flat near-black shadow shapes with a heavy flat vignette; the corners fall to near-black. The ceiling, the closed overhead bins above the only visible row, the side walls, the two oval windows and the far curtain are completely unlit and blacked out in one uninterrupted flat pitch-black ink-navy fill; the entire upper half of the frame is submerged in that same blacked-out midnight navy with zero illumination. Each oval window is one flat solid pitch-black ink-navy fill matching the ceiling, and the narrow muted-teal floor runner lying on the floor is the only other brighter shape.",
    )
    .replace(
        "Human hands show four gently curved fingers with small gaps and one separated thumb, softly rounded tips, solid fill.",
        "The only visible fragment of the G01 bitten forearm is one clearly readable flat bone-tone mitten-shaped strip with one wide near-black navy cuff edge, already lying flat inside the open recess under the near-left seat, parallel to the floor beneath the seat cushion, wholly inside the seat footprint and away from the open aisle, with no separated fingers.",
    )
    # E315: v4 primed front-facing dot eyes/mouth and a repeated empty seat back
    # while asking for a rear view. State only backs of heads and one near
    # foreground seat back; keep the four-seat count positive for the gate.
    .replace(
        "Faces show exactly two simple solid dot eyes and one short mouth line and nothing else drawn on the face.",
        "Every visible passenger is seen strictly from behind, with solid black hair covering the back of the head and a plain uniform back panel; only the backs of heads and shoulders are drawn.",
    )
    .replace(
        "Cabin rows hold 1+1 seats and oval windows stand on BOTH sides. This view contains "
        "only the two rows 27 and 28: four seats and four oval windows in total, with no "
        "receding extra rows, no repeated empty seat backs and no extra windows behind them. ",
        "The camera stands on the centreline of the empty aisle directly behind the only "
        "visible row: one seat on each side of the aisle (28A left, 28C right), two seats "
        "and two pitch-black oval windows in total. The aisle itself stays a clear vertical "
        "strip from the bottom of the frame to the far curtain, occupied only by the empty "
        "floor and the narrow teal runner. The rear faces of the two seats sit at the lower "
        "left and lower right edges, with the open under-seat recess below the left cushion "
        "fully visible and unobstructed; the two passengers are seen from behind. ",
    )
    .replace(
        "Backgrounds keep layered flat depth and one-point perspective.",
        "The single viewpoint is on the empty aisle centreline directly behind the only visible row, looking forward between its two seat backs; all depth comes from flat overlap.",
    )
)
STYLE_OVERRIDE["G02"] = G02_REAR_DARK_CONTRACT
# E298: G04 is a flat phone close insert, not a cabin wide plate. The inherited
# G02 contract still asserted four seats/four windows, and the gate skipped seat
# checks for phone_ins, so a 2+2 stale clause survived in the chain. Strip the
# row/window assertion; the close insert describes only the phone and its pictures.
PHONE_INS_STYLE_CONTRACT = FACE_FLAT_CONTRACT.replace(
    "Cabin rows hold 1+1 seats and oval windows stand on BOTH sides. This view contains "
    "only the two rows 27 and 28: four seats and four oval windows in total, with no "
    "receding extra rows, no repeated empty seat backs and no extra windows behind them. ",
    "",
)
STYLE_OVERRIDE["G04"] = PHONE_INS_STYLE_CONTRACT
# E273: when a shot's own contract already carries the flat light law, the global
# context "Light:" line would repeat the old "walls clearly lighter / emitting
# fixtures" wording and re-prime H3 to paint a gradient.
LIGHT_SUPPRESS = {"G02", "G03", "G05"}
# E287: G02 (aisle_flat) renders flat because its Scene line names the ceiling
# strip and floor runner as single solid fills. G03/G05 (seat_27a) said only
# "one thin ceiling strip" inside a "dark night cabin" and both renders grew a
# grey/teal ramp on those surfaces even after E283 removed lights-up wording.
# Reuse the proven G02 geometry/objects wording as a prompt-only scene override;
# no change to spec, global-context or the chain4 graph.
SCENE_OVERRIDE = {
    # E308: local rear-view override for the G02 aftermath. The near foreground is
    # the rear face of seat 27A; the other three seats and passengers are beyond it
    # and seen from behind. This supersedes E304's standing front-near camera line
    # for this shot only, not for G03/G05.
    "G02": (
        "one continuous narrow-body passenger cabin aisle seen from the camera standing on the "
        "aisle centreline directly behind the only visible row and looking forward between its "
        "two seat backs; exactly one row with one seat on each side of the empty central aisle "
        "(28A left, 28C right), 1+1, two seats total, plain solid pitch-black oval windows, "
        "closed overhead bins sharing the ceiling's blacked-out flat pitch-black ink-navy fill; "
        "the open under-seat recess under the left cushion is fully visible and unobstructed",
        "one narrow flat muted-teal floor runner lying on the cabin floor; two generic passengers "
        "seated in seats 28A and 28C, both seen strictly from behind; the central aisle stays empty",
    ),
    "G03": (
        "one continuous narrow-body passenger cabin aisle, front near the camera and tail far "
        "away, exactly rows 27 and 28 with one seat per side (1+1, four seats total), plain solid "
        "oval windows, closed overhead bins",
        "one thin solid bone-white ceiling strip and one flat muted-teal floor runner resting on "
        "the cabin floor; one flat phone screen resting on Khang's lap; three generic passengers "
        "seated in the other seats",
    ),
    # E275/E287: G05 is the same 27A plate and continues G03's last frame; give it
    # the identical flat-surface anchors before its first render instead of finding
    # the same E273 ramp after the GPU job.
    "G05": (
        "one continuous narrow-body passenger cabin aisle, front near the camera and tail far "
        "away, exactly rows 27 and 28 with one seat per side (1+1, four seats total), plain solid "
        "oval windows, closed overhead bins",
        "one thin solid bone-white ceiling strip and one flat muted-teal floor runner resting on "
        "the cabin floor; one flat phone screen resting on Khang's lap showing the flat cake "
        "picture; three generic passengers seated in the other seats",
    ),
}

# E298: G03 runs as pure T2V (assets=[]) and its context entry has an empty
# characters list, so H3 invented Khang while G05 got the bible block from context.
# The spec already declares the khang-navy-longsleeve layer; inject the same
# appearance + wardrobe sentence prompt-side only, without attaching a new ref asset.
CAST_OVERRIDE = {"G03": ["khang"]}

# Positive composition lock for shots whose wide set plate previously tempted H3 to
# invent a crowd and drop the hero prop. Never deny an object or a colour here.
ACTION_OVERRIDE = {
    "G02": (
        "Wide night cabin aftermath continuing from the G01 under-seat insert: frame 1 still "
        "holds the exact bitten forearm from <Picture 1> lying flat in the black gap under the "
        "near-left seat, then a hard cut at the first beat places the camera on the empty aisle "
        "centreline directly behind the only visible row. The rear faces of its two seats frame "
        "the lower left and lower right, the aisle between them stays empty from the bottom of "
        "the frame to the far curtain, and the open under-seat recess below the left cushion is "
        "fully visible and unobstructed. Exactly two generic passengers occupy seats 28A and "
        "28C, both seen strictly from behind with solid black hair and plain uniform backs. The "
        "same forearm from G01 is already beneath the left seat: a readable flat bone-tone "
        "mitten-shaped strip and the edge of a wide near-black navy cuff, copied in fill and "
        "proportion from <Picture 1>, lying parallel to the floor under the seat cushion. On "
        "two adjacent beats it slides farther inward under the left cushion and is fully gone; "
        "the strip never crosses the seat edge into the aisle, never rests on a seat back or a "
        "passenger's shoulder, and never becomes a separated-finger hand. Both passengers keep "
        "their seats facing away for the whole shot. The closed overhead bins, side walls, "
        "pitch-black oval windows and far curtain are blacked out in the ceiling's single flat "
        "pitch-black ink-navy fill with zero illumination; only the narrow muted-teal floor "
        "runner is lighter. The frame stays heavily near-black. Only one row with two seats is "
        "present."
    ),
    "G03": (
        "Medium view of the same two rows 27 and 28: Khang is ALREADY slumped asleep in seat 27A "
        "from the first frame, head bowed and both dot eyes closed, with one bone-white phone "
        "ALREADY lying untouched on his lap; nobody places it and no hand touches it. The phone "
        "screen changes by itself from a plain pale flat rectangle to one flat picture of a small "
        "birthday cake surrounded by a small group photo of people gathered around it; only the "
        "flat content inside the screen changes and the cabin keeps its same one-tone surfaces "
        "throughout. The three generic passengers stay seated in the other three seats. All four "
        "figures keep the same seats and scale."
    ),
    "G05": (
        "Medium view of the same two rows 27 and 28: Khang lifts the bowed head in seat 27A "
        "and opens two dot eyes abruptly, then listens to the cabin with the flat phone screen "
        "still resting untouched on his lap; the three generic passengers stay seated in the "
        "other three seats. All four figures keep the same seats and scale through the shot, "
        "and the cabin keeps its same one-tone surfaces from the first frame to the last."
    ),
    "G01": (
        "Close insert already inside the dark gap under row 27: from the first frame the frame "
        "holds one blood-stained forearm in one uniform dirty dark bone tone and one "
        "realistic flat human hand with one thumb, four separate fingers and near-black nails "
        "lying palm up under the navy seat, the whole arm inside the recess. A WIDE torn "
        "solid near-black navy cuff at the top of the arm is the darkest fill in the frame. "
        "The bitten hand is deformed: several uneven ragged chunks are chewed out of its "
        "edge, the broken outline bending at a wrong angle, a second raw bite wound opens "
        "on the forearm, and irregular flat dark-red blood blotches of assorted sizes with "
        "ragged edges, separate spots and short streaks cover every notch and scatter across "
        "the hand, wrist and navy cuff; blood is the only brighter shape and reads clearly "
        "against the dark fills. The wrist and fingers move in discrete jerks: each snap "
        "changes the pose once, then the whole hand freezes in a held pose before the next "
        "snap; the thumb and separate fingers flick open and shut on the beats while the arm "
        "stays wholly inside the under-seat gap. The camera makes one clear short sideways pan "
        "along the same recess from the low under-seat angle, keeping one scale and staying at "
        "underside level: the fixed jagged seat edge and the dark floor gap travel visibly "
        "across the frame behind the hand. The layered near-black underside of the seat and "
        "a flat navy floor gap fill the rest of the frame."
    ),
    # v3 QA fix (26/11): every legacy plate imported a crowd, a gradient or a third-person
    # body. These positive compositions lock the actual shot content instead of denying it.
    "G04": (
        "Close insert: one flat bone-white smartphone fills the frame, its solid muted-teal "
        "screen holding exactly one small birthday cake and one small group photo of three "
        "simple dot-eyed bone-white faces; the phone, the cake and the group photo keep the "
        "same scale and framing from the first frame to the last."
    ),
    "G06": (
        "Close insert of one flat bone-white face with solid black hair, exactly two black "
        "dot eyes now open and one short straight mouth line, centred in a muted-teal frame."
    ),
    "G07": (
        "One seated passenger a few rows ahead sits perfectly still with the head bowed "
        "onto the chest, the only figure in the wide cabin frame."
    ),
    "G09": (
        "Close insert of one flat face only: the head starts bowed with two red infected "
        "eyes lowered, then the head snaps up so the two red infected eyes fix forward at "
        "Khang. The face alone fills the flat close insert."
    ),
    "G10": (
        "Khang steps fully through the lavatory doorway and pulls the flat navy door shut "
        "behind him; the final frame shows the closed navy door alone in the empty corridor "
        "with Khang inside."
    ),
    "G11": (
        "Close insert of one flat lavatory mirror only: inside it one bone-white face with "
        "solid black hair, exactly two black dot eyes and one short straight mouth line "
        "stays still while one dark flat silhouette begins to appear behind it; the sink "
        "and tap below are solid fills."
    ),
    "G12": (
        "Close insert inside the small lavatory only: the flat door and one flat mirror "
        "hold the empty room; the camera drifts once as if turning around, then holds the "
        "door and mirror again."
    ),
    "G13": (
        "The single closed navy lavatory door shakes in place under slow heavy pounding "
        "from the other side; the empty corridor and the closed door are all the frame "
        "holds."
    ),
    "G14": (
        "Close insert of the lower door gap only: dark-red blood seeps through the gap and "
        "spreads across the single flat dark floor with a hard flat edge; the closed door "
        "and the flat floor hold the whole frame."
    ),
    "G15": (
        "First-person point of view from Khang's eyes: the closed navy lavatory door fills "
        "the view and one white mitten paddle hand rises into the lower frame, frozen just "
        "short of the door; the frame holds only the door and that mitten hand."
    ),
    "G16": (
        "Close insert of the lower door gap only: the thin dark-red line already at the gap "
        "holds still and the floor remains one single flat dark field; the closed door and "
        "the flat floor hold the whole frame."
    ),
    "G17": (
        "The panel holds only the closed navy lavatory door and the empty muted-teal "
        "corridor; the second voice comes from outside the frame. The empty panel keeps "
        "its two flat tones throughout."
    ),
    "G18": (
        "First-person point of view from Khang's eyes inside the lavatory: only his raised "
        "shoulders and two white mitten paddle hands at the lower edges of the frame, "
        "frozen as he listens; the frame holds only the door, the shoulders and the two "
        "mitten hands."
    ),
    "G19": (
        "The flat navy door opens directly onto the wide passenger cabin, completely silent "
        "and still with every seat empty; the opening is the only action and the doorway "
        "and empty seats hold the frame."
    ),
    "G20": (
        "A single flight attendant lies face down on the flat navy cabin floor in a still "
        "navy uniform, the only figure in the frame, always face down."
    ),
}

# Generic "single visible object shifts position" beats invited unscripted characters into
# empty-panel inserts (G14/G16/G17) and turned POV beats into third-person gestures (G15/G18).
BEAT_OVERRIDE = {
    # G01-G04 short product: one action per clip (E171/E172). The four spec shots carry
    # exactly one visual action each, so the product is four clips - no action is repeated.
    "G01": (
        "At {tc}, the wrist is already mid-snap: it kicks upward once and the fingers flick "
        "open, then the whole pose freezes.",
        "At {tc}, the wrist drops sharply and the four fingers clamp around the bite; the new "
        "pose freezes.",
        "At {tc}, the wrist snaps upward again in a shorter uneven kick and two fingers flick "
        "apart; the pose freezes.",
        "At {tc}, the wrist jerks down and the thumb twitches sideways; the pose freezes.",
        "At {tc}, the wrist gives two rapid unequal jerks in place while the fingers flick open "
        "then shut; the pose freezes.",
        "At {tc}, the wrist twists sharply and the bitten fingers spread once more; the pose "
        "freezes.",
        "At {tc}, the wrist settles with one final spasm, the fingers half open, and the "
        "dark-red blotches hold their colour.",
    ),
    # User 28/11 prompt-detail pass (no new ALH rule): the arm is already tucked
    # under the near-left seat 27A and withdraws farther inward; it must not peek
    # past the seat edge. The first beat is the G01 last frame inside that recess;
    # the 22-frame trim still puts the hard cut at 00:01.200 and the two withdrawal
    # beats stay adjacent so no long interpolation can make the strip reappear.
    "G02": (
        "At {tc}, frame 1 still holds the exact G01 bitten forearm from <Picture 1> lying flat "
        "under the near-left seat inside the dark recess; the camera is still at under-seat "
        "level.",
        "At {tc}, a hard cut places the camera on the empty aisle centreline directly behind "
        "the only visible row; its two seat backs sit at the lower left and lower right, the "
        "aisle between them is empty, and two passengers in 28A and 28C are seen strictly from "
        "behind; the open under-seat recess below the left cushion is fully visible and the "
        "bone-tone mitten strip and cuff are already inside it.",
        "At {tc}, the bone-tone mitten strip and navy cuff, already under the left seat cushion, "
        "draw a readable short distance farther inward, away from the aisle opening.",
        "At {tc}, that same strip and cuff slide fully out of sight into the black recess "
        "under the left cushion.",
        "At {tc}, the recess is empty and the wide rear view holds only the empty central "
        "aisle, the two seats and two passengers seen from behind; framing and scale stay "
        "unchanged.",
        "At {tc}, the rear cabin remains still with the blacked-out flat navy ceiling, overhead "
        "bins, pitch-black oval windows and walls, and the narrow muted-teal floor runner, "
        "with framing and scale unchanged.",
    ),
    # E281 user: G03 is a held state, not an action sequence. Already asleep,
    # phone already on the lap and untouched; only the flat screen image changes.
    # E281: {tc} beats scale with DURATION_OVERRIDE so a short held-state clip has
    # no timecode past its own end (the old hard-coded 00:09.500 broke a 6s clip).
    "G03": (
        "At {tc}, Khang is already slumped asleep in seat 27A with the head bowed and both "
        "dot eyes closed, one bone-white phone already resting on his lap untouched, while the "
        "three other passengers hold their seats and the framing and scale stay exactly as in "
        "the first frame.",
        "At {tc}, the phone screen changes by itself from a plain pale rectangle to one flat "
        "picture of a small birthday cake surrounded by a small group photo, while Khang stays "
        "bowed asleep, no hand touches the phone, the cabin keeps its same one-tone surfaces and "
        "the other three passengers keep their seats.",
        "At {tc}, the phone still lies untouched on Khang's lap with the flat cake picture "
        "unchanged, the sleeper and the whole cabin holding their positions and their flat tones "
        "with the framing and scale exactly as in the first frame.",
    ),
    # E277: the generic medium beats talk about weight on the front foot; G05 is
    # a seated wake-up continued from G03's last frame, so it needs seated beats.
    # E283/E287: pre-fix the wake-up beats too - no lit/glowing-phone wording that
    # primes H3 to spill light onto the ceiling and floor of this same 27A plate.
    "G05": (
        "At {tc}, Khang is already lifting his bowed head in seat 27A, both dot eyes still closed, "
        "with the flat cake picture unchanged on the phone screen lying untouched on his lap and "
        "the three other passengers seated.",
        "At {tc}, Khang's head is fully raised and both dot eyes open abruptly as he listens; the "
        "flat phone screen and the cabin's same one-tone surfaces are unchanged and all four "
        "figures keep their seats and scale.",
        "At {tc}, Khang holds the wide-eyed listening pose with the flat phone picture still on "
        "his lap, the two cabin rows and the still aisle unchanged with their tones held flat.",
    ),
    "G04": (
        "At {tc}, the whole phone stays fully inside the frame from first frame to last with the cake and the group photo both visible, while the framing and the scale stay exactly as they are in the first frame.",
    ),
    "G06": (
        "At {tc}, the flat face is already centred with both dot eyes open.",
        "At {tc}, the eyes hold their open position and the camera drifts closer.",
        "At {tc}, the face settles into the next beat while the camera keeps drifting.",
    ),
    "G07": (
        "At {tc}, the single bowed passenger is already seated a few rows ahead and still.",
        "At {tc}, the bowed head stays lowered while the camera drifts closer.",
        "At {tc}, the figure remains seated and still while the camera keeps drifting.",
    ),
    "G09": (
        "At {tc}, the head is bowed low and the flat face fills the insert.",
        "At {tc}, the head snaps up and the two red infected eyes lock forward.",
        "At {tc}, the raised face holds while the camera keeps drifting.",
    ),
    "G10": (
        "At {tc}, Khang's hand is already on the handle and one foot crosses the lavatory threshold.",
        "At {tc}, the door swings inward as Khang steps fully inside.",
        "At {tc}, the flat door is fully closed behind him while the camera keeps drifting.",
    ),
    "G13": (
        "At {tc}, the closed door already trembles slightly on its hinges.",
        "At {tc}, the door shakes harder in short slow pulses and stays closed.",
        "At {tc}, the shaking settles into the next beat while the camera keeps drifting.",
    ),
    "G14": (
        "At {tc}, a thin dark-red line is already seeping under the closed door.",
        "At {tc}, the dark-red pool widens across the flat floor with a hard flat edge.",
        "At {tc}, the pool holds its dark flat edge while the camera keeps drifting.",
    ),
    "G15": (
        "At {tc}, the door already fills the view and one mitten hand is raised below it.",
        "At {tc}, the hand holds its position just short of the door while the camera drifts closer.",
        "At {tc}, the raised hand and the door settle into the next beat while the camera keeps drifting.",
    ),
    "G16": (
        "At {tc}, the thin dark-red line is already still at the closed door gap.",
        "At {tc}, the line and the flat dark floor hold their single tones while the camera drifts closer.",
        "At {tc}, the insert holds completely still except for the camera drift.",
    ),
    "G17": (
        "At {tc}, the empty corridor and the closed door already fill the frame alone.",
        "At {tc}, the door and floor hold their flat tones and the frame stays empty while the camera drifts closer.",
        "At {tc}, the empty panel stays completely empty except for the camera drift.",
    ),
    "G18": (
        "At {tc}, only raised shoulders and two white mitten hands are already frozen at the lower edges.",
        "At {tc}, the shoulders hold still as a cropped POV while the camera drifts closer.",
        "At {tc}, the listening pose stays cropped at the shoulders except for the camera drift.",
    ),
    "G19": (
        "At {tc}, the flat door is already opening onto the empty cabin aisle beyond.",
        "At {tc}, the cabin stays perfectly still and empty while the camera drifts forward.",
        "At {tc}, the open view holds its empty seats while the camera keeps drifting.",
    ),
    "G20": (
        "At {tc}, the single prone attendant is already lying face down on the cabin floor.",
        "At {tc}, the face-down pose and navy uniform hold flat while the camera drifts closer.",
        "At {tc}, the still figure holds without turning over except for the camera drift.",
    ),
}

# E315/E316: G01->G02 smart chain. Beats are placed on the untrimmed generation
# timeline; the saved part loses the first 22 frames (00:00.917). The flick and
# snap-back are 0.25 s apart so H3 cannot interpolate a four-second hand.
BEAT_FRACTIONS_OVERRIDE = {"G02": (0.0, 0.21, 0.45, 0.50, 0.72, 1.0)}

# POV specs mapped to "medium" in the context, which made H3 render a full third-person
# body. Override only the shot label; the cast list is emptied in build_global_context.
SIZE_LABEL_OVERRIDE = {
    "G11": "close-up insert of a flat mirror",
    "G12": "close-up insert inside a small empty lavatory",
    "G15": "first-person point-of-view shot from Khang's eyes",
    "G18": "first-person point-of-view shot from Khang's eyes",
    "G20": "close-up insert of a prone figure on the cabin floor",
}

SUPPORT_HINT = {
    "beer": "bốn ly bia bọt trắng trên mặt bàn tròn, bốn ly đều nhìn rõ, không có mặt hay mắt trên ly",
    "phone": "điện thoại đặt trong tay, màn hình phẳng sáng",
    "cake": "bánh đặt giữa mặt bàn tròn, một bánh duy nhất",
    "water": "chai nước đặt trong tay tiếp viên, chạm lòng bàn tay",
}

SFX_TEXT = {
    "breath": "quiet breathing",
    "click": "a small mechanical click",
    "khe": "a brief raspy throat-clear",
    "whoosh": "a short soft whoosh",
    "heartbeat": "slow heartbeat pulses",
    "bite": "a brief, muted bite impact",
}

# H3 treats a frozen camera as a frozen clip: the subject barely moves and the shot has to be
# re-timed later. Every shot therefore gets a moving camera plus environment motion, and the
# word "static" becomes a locked-off tripod with breathing drift instead of a dead frame.
CAMERA_PHRASE = {
    "static": "locked-off tripod with a slow breathing drift under 1% of the frame",
    "zoom": "slow push-in of about 3% over the shot, with a faint handheld sway",
    "pan": "slow lateral pan that keeps the subject framed, with a faint handheld sway",
    "tilt": "slow tilt that follows the subject, with a faint handheld sway",
    "dolly": "slow dolly toward the subject, with a faint handheld sway",
    "tracking": "slow tracking move that stays with the subject, with a faint handheld sway",
}
CAMERA_FALLBACK = "slow push-in with a faint handheld sway"
# E178: G01 compounded three separate camera instructions (camera line + beat + ambience)
# into a large zoom that cropped the sleeve and erased the row-27 seat structure. This
# close insert is the only G01-G04 shot that locks its camera outright; the locked wording
# is stated positively once per prompt instead of negating "no zoom".
CAMERA_LOCK = "held at one fixed scale and framing from the first frame to the last frame"
# E304: the consistency audit requires the cabin camera height to be stated in the
# prompt. cabin-map.eye_level covers wide/aisle plates (standing); the seat_27a set
# carries the specific seated height, so medium seat shots use that value. No Scene,
# Props or Light wording changes: this is one camera-sentence layer only.
CAMERA_LOCK_STANDING = (CAMERA_LOCK + ", at standing eye level")
CAMERA_LOCK_SEATED = (CAMERA_LOCK + ", at the eye level of a seated passenger")
CAMERA_LOCK_REAR = (
    CAMERA_LOCK + ", on the empty aisle centreline just behind row 27, looking forward "
    "between the two near seat backs at standing eye level"
)
CAMERA_ZOOM_SEATED = (
    "slow push-in of about 3% over the shot, with a faint handheld sway, "
    "at the eye level of a seated passenger"
)
UNDER_SEAT_PAN = (
    "makes one clear short sideways pan low inside the under-seat recess at one constant scale, "
    "with the camera staying at seat-underside level: the fixed jagged seat-underside edge and the "
    "dark floor-gap shapes visibly travel sideways across the frame while the hand keeps its size"
)
CAMERA_OVERRIDE = {
    # E178/E180: G02-G04 are single-action clips on a fixed plate. G01 is exempt: E270
    # adds a short sideways slide from the under-seat angle, at one constant scale.
    sid: CAMERA_LOCK for sid in ("G02", "G03", "G04")
}
CAMERA_TEXT_OVERRIDE = {
    # E270: the user wants the E248 under-seat pan back, but sideways only. No slow,
    # easing or growing-hand wording: the E268 wrist/finger snap system stays primary.
    "G01": UNDER_SEAT_PAN,
    # E308 (user supersede): G02 is the G01 aftermath seen from behind seat 27A,
    # no longer the standing front-near plate. G03/G05 keep the seated eye level;
    # G04 is an insert (N/A).
    "G02": CAMERA_LOCK_REAR,
    "G03": CAMERA_LOCK_SEATED,
    "G05": CAMERA_ZOOM_SEATED,
}
AMBIENCE = "Small subject motion and the camera move continue evenly for the whole shot."
AMBIENCE_LOCK = "The small subject motion continues evenly while the framing and scale hold exactly as in the first frame."
AMBIENCE_UI = "The recording dot keeps pulsing and the waveform keeps travelling across the black field."
# E307: the G02 sliver is one quick flick, not an evenly continuing hand animation.
AMBIENCE_SLIVER = (
    "All timecodes are on the untrimmed generation timeline; the delivered clip starts only "
    "after the 22 overlap frames are removed. The flick and its snap-back are two adjacent "
    "beats and form the only under-seat motion; between the cut, the flick and the snap-back "
    "the rear cabin holds still while framing and scale stay unchanged."
)
# E267/E268: a jerk shot must NOT end with the global "continues evenly" line - that
# trailing instruction is what smoothed v6-v9 into a dolly. Positives only: the pose
# freezes between snaps instead of denying smooth motion.
JERK_AMBIENCE = (
    "Between each listed snap the wrist and fingers hold a frozen pose; the camera pans sideways "
    "low inside the under-seat recess, sliding the fixed jagged seat edge and floor-gap shapes "
    "across the frame while every foreground shape keeps its size."
)
MOTION_MODE = {"G01": "jerk"}
# E277: the global character bible describes a standing pose. In a seat-27A
# shot that wording invites H3 to stand the subject up, so swap only that clause.
SEATED_SHOTS = {"G02", "G03", "G05"}
# Beat 0 also fixes the anchor: Frame 1 must already be mid-action, because H3 continues an
# idle pose instead of inventing movement (the "frozen shot" complaint).
MOTION_BEATS = {
    "wide": (
        "At {tc}, the subject is already mid-gesture with the weight on the front foot.",
        "At {tc}, the weight shifts, the head turns and the hands carry the gesture onward.",
        "At {tc}, the gesture settles into the next beat while the camera keeps drifting.",
    ),
    "medium": (
        "At {tc}, the subject is already mid-gesture with the weight on the front foot.",
        "At {tc}, the weight shifts, the head turns and the hands carry the gesture onward.",
        "At {tc}, the gesture settles into the next beat while the camera keeps drifting.",
    ),
    "close-up": (
        "At {tc}, the face is already mid-expression.",
        "At {tc}, the eyes move and the mouth shapes the next word.",
        "At {tc}, the expression settles into the next beat while the camera keeps drifting.",
    ),
    "object": (
        "At {tc}, the single visible object is already inside the frame and travels a short distance within it.",
        "At {tc}, the single visible object shifts position while the camera keeps drifting.",
        "At {tc}, the single visible object settles into the next beat while the camera keeps drifting.",
    ),
    "ui": (
        "At {tc}, the graphic is already in motion: the waveform travels and the recording dot pulses.",
        "At {tc}, the waveform amplitude changes and the dot keeps pulsing.",
        "At {tc}, the graphic settles with the dot still blinking.",
    ),
}
MOTION_MIN_SECONDS = 2.0
# E281 duration fit: shots with few beats should not be stretched to 10s. These
# durations are metadata for the rebuilt prompt's timecodes; chain4_run.py receives
# the matching --seconds per invocation. G01 (7 snaps) keeps 10s. E285: G02's tiny
# under-seat sliver also fits 6s instead of a conspicuous 10s hand animation.
DURATION_OVERRIDE = {"G02": 6.0, "G03": 6.0, "G05": 8.0}

# QA metadata lives in global context; these object/colour deletion cues must never
# reach prompt_visible. H3 draws the denied object instead of removing it.
NEGATION_DROP = (
    "NO red anywhere in this shot; do not draw red eyes.",
    "no potted plant, no extra furniture",
    "no plant, no flowers, no second table",
    "no faces, no figures, no text",
    "No visible text, no signage, no watermark.",
    "no cake, no candles",
)


LIGHT_REPLACE = {
    "NO visible light source, NO beam, NO gradient, NO shadow, NO spotlight; amber only as one flat tint, never as a light effect":
        "flat uniform colour lighting",
}


def strip_negations(text: str) -> str:
    for clause in NEGATION_DROP:
        text = text.replace(clause, "")
    for clause, replacement in LIGHT_REPLACE.items():
        text = text.replace(clause, replacement)
    return re.sub(r"\s{2,}", " ", text).replace(" ,", ",").replace(",;", ";").replace(" ;", ";").strip()


def timecode(value: float) -> str:
    value = max(0.0, float(value))
    return f"{int(value // 60):02d}:{value % 60:06.3f}"


def dialogue_text(shot: dict, seconds: float = 0.0, size: str = "wide",
                  on_screen: bool = True, beats: tuple | None = None,
                  ambience: str | None = None,
                  custom_fractions: tuple | None = None) -> str:
    """Keep the supplied Vietnamese dialogue unchanged and add local time tags.

    Dialogue and motion beats share ONE sorted timeline: the linter (and H3) require
    increasing `At` timecodes, so a collision is nudged by 50 ms instead of failing.
    `on_screen` gates the lips-closed clause: a black-screen UI shot has no lips to close.
    """
    beats = beats or MOTION_BEATS.get(str(size).lower(), MOTION_BEATS["medium"])
    events = []
    for line in shot.get("dialogue", []):
        text = str(line.get("text", ""))
        if not text:
            continue
        at = max(0.0, float(line.get("at", 0)))
        who = str(line.get("who", ""))
        if who.lower() in {"vo", "narrator", "voiceover"}:
            tail = " while the on-screen characters' lips remain completely closed." if on_screen else ""
            events.append((at, "d", ("The narrator", "says in an off-screen voiceover", text, tail)))
        else:
            events.append((at, "d", (who or "The speaker", "says", text, "")))
    if seconds >= MOTION_MIN_SECONDS:
        end = round(max(1.0, seconds - 0.3), 1)
        # E171/E172: one action per clip; E268: a jerk shot needs every discrete snap
        # on its own timecode. The old three-slot engine silently dropped beats 4-7,
        # so H3 interpolated smooth travel between the surviving beats.
        if custom_fractions and len(custom_fractions) == len(beats):
            # E316: a continued shot needs a late cut after the 22-frame overlap
            # and two adjacent beats for the under-seat flick.
            fractions = tuple(custom_fractions)
        elif len(beats) == 1:
            fractions = (0.0,)
        elif len(beats) == 2:
            fractions = (0.0, 1.0)
        elif len(beats) == 7:
            fractions = (0.0, 0.12, 0.25, 0.38, 0.52, 0.70, 0.88)
        else:
            fractions = tuple(i / (len(beats) - 1) for i in range(len(beats)))
        positions = tuple((round(end * f, 1), i) for i, f in enumerate(fractions))
        for at, index in positions:
            events.append((at, "m", index))
    events.sort(key=lambda item: item[0])

    lines, previous = [], -1.0
    for at, kind, payload in events:
        at = max(at, previous + 0.05)
        # A late beat can be nudged past the clip when dialogue is dense; dropping it keeps the
        # linter's "last timecode <= duration" rule true for short shots.
        if kind == "m" and seconds >= MOTION_MIN_SECONDS and at > seconds - 0.03:
            continue
        previous = at
        if kind == "d":
            speaker, delivery, text, tail = payload
            lines.append(f"At {timecode(at)}, {speaker} {delivery}: "
                         f"<d>[Vietnamese] {text}</d>{tail}")
        else:
            lines.append(beats[payload].format(tc=timecode(at)))
    if lines:
        lines.append(ambience or (AMBIENCE_UI if str(size).lower() == "ui" else AMBIENCE))
    return " ".join(lines)


def soundscape(shot: dict, scene: dict, on_screen: bool = True) -> str:
    """Build a compact English ambience/SFX bed from the authoritative spec.

    SFX only join the prompt when a body is on screen: G01 is a black screen with a voice,
    and "quiet breathing occurs naturally" made H3 look for a breathing person to draw.
    """
    scene_name = str(scene.get("geometry", "")).lower()
    if "table" in scene_name or "restaurant" in scene_name:
        bed = "Soft restaurant room tone and distant conversation continue underneath."
    elif "lavatory" in scene_name or "sink" in scene_name:
        bed = "A low aircraft engine hum and soft ventilation continue underneath."
    else:
        bed = "A low aircraft engine hum and soft cabin ventilation continue underneath."
    sounds = []
    for event in shot.get("sfx", []) if on_screen else []:
        name = SFX_TEXT.get(str(event.get("type", "")).lower())
        if name and name not in sounds:
            sounds.append(name)
    if sounds:
        bed += " " + " and ".join(sounds).capitalize() + " occur naturally at the specified moments."
    return bed


def ui_action(shot: dict) -> str:
    """English description for a black-screen UI shot.

    The spec description is Vietnamese ("Màn đen, chấm đỏ ghi âm nhấp nháy..."), and putting
    it next to <d>[Vietnamese] dialogue invited H3 to read it as speech. Colours are stated
    because "black ink contour on near-black navy" would swallow a dark waveform.
    """
    ui = shot.get("ui") or {}
    pieces = []
    if ui.get("rec_wave", True):
        pieces.append("a bone-white waveform travels across the lower third of a flat "
                      "near-black navy field")
        pieces.append("a small red recording dot pulses above it")
    timer = str(ui.get("clock") or "").strip()
    if timer:
        pieces.append(f"a bone-white timer in the top corner reads {timer}")
    if not pieces:
        pieces.append("a flat near-black navy field with one thin bone-white waveform")
    return "Black screen: " + ", ".join(pieces) + "."


def action_text(shot: dict, ctx_shot: dict, size: str = "medium") -> str:
    if str(size).lower() == "ui":
        return ui_action(shot)
    # Per-shot positive action override (composition + set detail): used when the
    # spec description alone cannot hold all cast or all props in one flat frame.
    override = ACTION_OVERRIDE.get(str(shot.get("id", "")))
    if override:
        # E162: G02 still carried "no passenger, no head, no face...". Describe the
        # intended count positively and let the shared scrub remove any remainder.
        return rules.strip_object_deletions(override)
    desc = str(shot.get("description", ""))
    for bad, good in BAD_CUES.items():
        desc = desc.replace(bad, good)
    supports = []
    for prop in ctx_shot.get("props", []):
        name = Path(prop).stem.lower()
        for key, text in SUPPORT_HINT.items():
            if key in name:
                supports.append(text)
    if supports:
        desc += " " + " ".join(supports)
    return desc.strip()


CAMERA_SIZE = {"3P": "wide", "INS": "close-up", "POV-K": "medium", "POV-PHONE": "medium",
               "MÀN ĐEN": "ui"}


def shot_size(shot: dict, resolved: dict) -> str:
    """Spec camera wins over the context value, which can be stale for UI/INS shots.

    build_global_context maps camera -> shot_size; a context written before that map
    existed leaves G01 as "medium", so the beats describe a man gesturing on a black
    screen. Deriving here keeps prompt and spec consistent without rewriting context.
    """
    derived = CAMERA_SIZE.get(str(shot.get("camera") or "").strip())
    return derived or resolved.get("shot_size") or "medium"


def mood_text(value: str, shot: dict) -> str:
    """Context `mood` sometimes carries the set's light contract; that is not a mood.

    G03 read "Mood: FLAT solid colour fields only ... NO visible light" while the same
    paragraph was already in `Light:` — duplicate weight on lighting instead of tone.
    """
    text = str(value or "").strip()
    poisoned = any(token in text.lower() for token in
                   ("flat solid", "solid colour", "solid color", "no visible light", "gradient"))
    if not text or poisoned:
        text = str(shot.get("mood") or "").strip() or "u ám"
    # h3-prompt-writing: every word outside <d> must be English. Vietnamese mood
    # strings were read as narration text by H3 (ALH E149).
    mood_en = {
        "u ám": "eerie dread", "căng thẳng": "tense dread", "ấm áp": "warm",
        "bí ẩn": "mysterious", "tĩnh lặng": "quiet", "hồi hộp": "eerie dread",
        "kinh hãi": "dread", "lạnh": "cold", "tối": "dark",
    }
    if not text.isascii():
        text = mood_en.get(text.lower(), "gloomy")
    return text.rstrip(".")


def text_allowance(allowed) -> str:
    """Phrase the shot's allow_text once, inside the contract, instead of contradicting it.

    G01 shipped "no text, no watermark." at the head and "Visible text allowed only: 00:00"
    at the tail — two opposite instructions about the same timer.
    """
    items = [str(a).strip() for a in (allowed or []) if str(a).strip()]
    if not items:
        return ""
    if all(re.fullmatch(r"\d{1,2}:\d{2}", a) for a in items):
        return "the on-screen timer " + " / ".join(items)
    return ", ".join(items)


def build_prompt(shot: dict, ctx: dict, part: str) -> str:
    sid = str(shot.get("id", ""))
    s = ctx["shots"][shot["id"]]
    scene = ctx["sets"].get(s.get("scene"), {})
    char_ids = [cid for cid in s.get("characters", []) if cid in ctx["characters"]]
    for cid in CAST_OVERRIDE.get(sid, []):
        if cid in ctx["characters"] and cid not in char_ids:
            char_ids.append(cid)
    characters = [(cid, ctx["characters"][cid]) for cid in char_ids]
    size = shot_size(shot, s)
    on_screen = bool(characters)
    beat_size = size if size == "ui" else ("object" if not on_screen else size)
    # Name every character in the wardrobe clause; orphan clothing fragments do not
    # tell H3 who wears what (the G02 regression).
    def cast_appearance(c: dict) -> str:
        text = c.get("appearance") or ""
        if sid in SEATED_SHOTS:
            text = text.replace(
                "relaxed asymmetrical standing pose with one hip a little lower, weight on one leg and elbows softly bent",
                "relaxed seated posture in the airline seat, shoulders squared to the aisle, one hand resting on the lap",
            )
        if sid in ("G03", "G05"):
            # E280: Hy4 saw drawn eyebrows and a nose on the lifted faces in
            # mid/last. The bible sentence itself primes both features, and
            # "no eyebrows, no eyelashes" is a denial that H3 ignored. State
            # the minimal flat face positively instead. E298: the same fix now
            # covers G03's injected Khang block (medium shot), and the eye
            # clause matches the contract's dot eyes instead of bible oval eyes.
            text = text.replace(
                "two simple solid oval eyes and one short straight neutral mouth line, "
                "a small simple tapered nose visibly protruding in side profile, "
                "no eyebrows, no eyelashes",
                "exactly two simple solid dot eyes and one short straight neutral mouth "
                "line and nothing else drawn on the face",
            )
        return text
    wardrobe = "; ".join(
        f"{cid}: {cast_appearance(c)}. " +
        ((c.get("upper_wardrobe") or c.get("wardrobe") or "") if size in ("close-up", "ui") else
         (c.get("wardrobe") or ""))
        for cid, c in characters)
    if str(shot.get("id", "")) in STYLE_OVERRIDE:
        # E261: the mitten is retired for G01. Stale context mitten wording is
        # replaced with a real flat hand and near-black nails; no light edge is added.
        hand = ("realistic flat human hands with one thumb, four gently curved fingers, "
                "small gaps between them and near-black nails on every fingertip")
        wardrobe = wardrobe.replace("mitten hands with no fingers", hand) \
                           .replace("mitten hands.", hand + ".")
    contract = STYLE_OVERRIDE.get(str(shot.get("id", "")), ctx["style"]["prompt_contract"])
    if not s.get("red_allowed"):
        # Do not replace this with "NO red anywhere" - a colour denial primes the
        # denied colour. The red_allowed=false fact stays in context for QA.
        contract = contract.replace("Red only for blood, infected eyes and the recording dot.", "")
    allowance = text_allowance(s.get("allow_text"))
    if allowance:
        contract = contract.rstrip(".") + "; the only written element is " + allowance + "."
    close = size in ("close-up", "ui")
    camera = CAMERA_TEXT_OVERRIDE.get(
        sid,
        CAMERA_OVERRIDE.get(sid, CAMERA_PHRASE.get(str(s.get("camera_motion")).lower(), CAMERA_FALLBACK)),
    )
    if size == "ui":
        # A flat graphic screen with handheld sway reads as a shaky camera fault.
        camera = camera.replace(", with a faint handheld sway", "")
    if MOTION_MODE.get(sid) == "jerk":
        ambience = JERK_AMBIENCE
    elif sid == "G02":
        ambience = AMBIENCE_SLIVER
    elif sid in CAMERA_OVERRIDE:
        ambience = AMBIENCE_LOCK
    else:
        ambience = None
    seconds = float(DURATION_OVERRIDE.get(sid, s.get("seconds") or 0))
    label = SIZE_LABEL_OVERRIDE.get(sid, f"{size} shot")
    geometry, objects = SCENE_OVERRIDE.get(
        sid, (scene.get("geometry", ""), scene.get("objects", "")))
    # E270/E315: the QA-passed r8 prop is an identity/fill reference, never a
    # first-frame plate. G02 needs it too: words alone re-invented the G01 arm.
    if sid == "G01":
        ref_line = (
            "Use <Picture 1> only to copy the exact realistic hand anatomy - one thumb, "
            "four separate fingers and near-black nails - the uniform dirty dark bone tone, "
            "the wide near-black navy cuff as the darkest fill, and the irregular dark-red "
            "blood blotches inside every notch; keep the flat dark under-seat lighting and "
            "the low sideways framing."
        )
    elif sid == "G02":
        ref_line = (
            "Use <Picture 1> only as the identity and fill reference for the same bitten "
            "forearm from G01: one uniform bone tone, the wide near-black navy cuff as "
            "the darkest fill, and the same flat fills inside the chewed notches; keep "
            "the visible fragment readable inside the recess and keep the wide rear framing."
        )
    else:
        ref_line = ""
    parts = [
        contract,
        ref_line,
        f"{label}, camera {camera}.",
        "" if close else (f"Scene: {geometry}".strip() if geometry else ""),
        "" if close else (f"Props: {objects}".strip() if objects else ""),
        "" if close or sid in LIGHT_SUPPRESS else (f"Light: {scene.get('light', '')}".strip() if scene.get("light") else ""),
        wardrobe,
        action_text(shot, s, size),
        dialogue_text(shot, seconds, beat_size, on_screen, BEAT_OVERRIDE.get(sid),
                      ambience, BEAT_FRACTIONS_OVERRIDE.get(sid)),
        f"Mood: {mood_text(s.get('mood'), shot)}.",
    ]
    # Style contract must be the very first thing in the field, BEFORE [Shot 1].
    contract = parts[0]
    rest = " ".join(p for p in parts[1:] if p)
    first = strip_negations(contract) + " [Shot 1] " + strip_negations(rules.strip_object_deletions(rest))

    return (
        "integrated_multimodal_description: " + first
        + "\n\noverall_soundscape: " + soundscape(shot, scene, on_screen)
        + "\n\nnon_diegetic_music: N/A"
    )


def main(argv):
    raw_part = argv[0] if argv and argv[0].startswith("part") else "part1"
    part = raw_part.replace("part", "")
    wanted = [a for a in argv if a != raw_part]
    ctx = json.loads(Path(str(CTX).replace("{}", part)).read_text(encoding="utf-8"))
    spec = json.loads(Path(str(SPEC).replace("{}", part)).read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in spec["shots"]}
    wanted = wanted or list(by_id)
    out_dir = Path(str(OUT).replace("{}", part))
    out_dir.mkdir(parents=True, exist_ok=True)
    fatal = False
    for sid in wanted:
        if sid not in by_id:
            continue
        if part == "1" and sid == "G02":
            # User-authored detail pass is the render authority for this retry.
            content = G02_USER_PROMPT
        else:
            content = build_prompt(by_id[sid], ctx, part)
        hard, warn = rules.validate_prompt(
            content, kind="video", red_allowed=bool(ctx["shots"][sid].get("red_allowed")), out="")
        for w in warn:
            print(f"  WARN {sid}: {w}")
        for h in hard:
            print(f"  FAIL {sid}: {h}")
            if part == "1" and sid in ("G01", "G02", "G03", "G04"):
                fatal = True
        target = out_dir / f"{sid}.txt"
        target.write_text(content, encoding="utf-8")
        print(f"{target.relative_to(ROOT)}  {len(content)} chars")
    if fatal:
        print("shared prompt gate FAILED for G01-G04 - fix the rule source, not the output file")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
