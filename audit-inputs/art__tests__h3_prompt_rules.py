"""Shared rule engine for every H3 prompt (image assets AND video shots).

Single source of truth:
  art/env/asset-contract.json   - field order, hard gates, anti-patterns
  art/env/cabin-map.json        - master_plate owns geometry/light/palette
  characters.json               - appearance + wardrobe verbatim
  out/qa-asset-verdicts.json    - latest asset verdict

Nothing in this module paints or repairs pixels; it only composes and gates text.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "art/env/asset-contract.json"
MAP_PATH = ROOT / "art/env/cabin-map.json"
LEDGER_PATH = ROOT / "out/qa-asset-verdicts.json"

# Style negations are instructions about rendering, not object deletion. Keep them.
STYLE_NEGATIONS = (
    "no gradient", "no shading", "no soft shadow", "no shadow", "no blur",
    "no 3d", "not 3d", "no beam", "no texture", "no panel", "no border",
    "no text", "no watermark", "not realistic", "never a vest", "no eyebrows",
    "no eyelashes", "no nails", "no finger joint", "no extra limb",
)
# Object-deletion negations: H3 draws the denied object instead of removing it.
DELETION_RE = re.compile(
    r"\b(?:no|not|never|without|remove|delete|don't|do not)\b[^.;]{0,120}?"
    r"\b(?:passenger|people|person|head|face|seated figure|figure|crowd|"
    r"body part|extra seat|second seat|third seat|another seat|"
    r"cake|candle|beer|glass|table|phone|plant|flower|screen|"
    r"signage|subtitle|label|timer)\b",
    re.I,
)
STALE_SEAT_RE = re.compile(
    r"\b(?:three|3)\s*(?:\+|\s+on each side of|seats on each side)"
    r"|\brow of (?:three|3)\b"
    r"|\bthree empty seats\b"
    r"|\b(?:2\+2|3\+3)\b",
    re.I,
)
PANEL_RE = re.compile(r"\b(?:storybook page|comic panel|multiple views|six panels|a sequence of)\b", re.I)
RED_RE = re.compile(r"\bred\b|\bđỏ\b", re.I)  # both English and Vietnamese colour names prime H3.

# Red allowed only for blood, infected eyes, the recording dot and the G01 arm.
RED_ALLOWED_ASSETS = ("bloody-arm", "g01", "rec-card", "infected", "veins", "blood")


def load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8-sig"))


def load_map() -> dict:
    return json.loads(MAP_PATH.read_text(encoding="utf-8-sig"))


def latest_verdicts() -> dict[str, dict]:
    if not LEDGER_PATH.exists():
        return {}
    rows = json.loads(LEDGER_PATH.read_text(encoding="utf-8-sig"))
    out: dict[str, dict] = {}
    for row in rows:
        asset = row.get("asset")
        if asset and (asset not in out or str(row.get("time", "")) >= str(out[asset].get("time", ""))):
            out[asset] = row
    return out


def master() -> dict:
    return load_map()["master_plate"]


def seat_count() -> tuple[int, int]:
    """Canonical count is read from master_plate/geometry, never a stale convention.

    The old fallback returned (2, 2) when parsing failed, so a map edit could silently
    validate prompts against 2+2 while the canon was 1+1. Fail closed instead.
    """
    m = master()
    geo = load_map().get("cabin_geometry_contract") or {}
    for line in list(m.get("invariants") or []) + [str(geo.get("rows", ""))]:
        hit = re.search(r"\b(\d+)\s*\+\s*(\d+)\b", str(line))
        if hit:
            return int(hit.group(1)), int(hit.group(2))
    spelled = re.search(r"\b(one|two|three|four)\s+seats?\s+on\s+each\s+side",
                        str(geo.get("layout", "")), re.I)
    if spelled:
        n = {"one": 1, "two": 2, "three": 3, "four": 4}[spelled.group(1).lower()]
        return n, n
    raise SystemExit("cabin-map: cannot read the canonical seat pair (N+N) from "
                     "master_plate.invariants or cabin_geometry_contract.rows")


def geometry_text() -> str:
    """Prompt-visible geometry only.

    `invariants` are QA facts: row numbers and later compositing cast in that list
    primed H3 to draw a long multi-row cabin (r6: 12 seats, 8 windows). The map may
    now carry a `layout_prompt` written as positive silhouette counts; it is the
    single source reaching the prompt, exactly like lighting_contract.prompt_visible.
    """
    m = master()
    if m.get("layout_prompt"):
        return str(m["layout_prompt"]).strip()
    return ". ".join(str(x).strip().rstrip(".") for x in m["invariants"])


def light_text() -> str:
    """Positive light sentence only.

    `forbid` is QA metadata, never prompt text: concatenating it used to write
    "pink/purple rim light" into H3's conditioning and produced a lavender wall.
    The single visible sentence lives in lighting_contract.prompt_visible so the
    map and the master cannot disagree on the shadow percentage (E228).
    """
    lc = load_map()["lighting_contract"]
    return lc["prompt_visible"]


def style_contract(kind: str, red_allowed: bool = False) -> str:
    """Field 1 at the very top: flatness first, palette second, red only if allowed."""
    left, right = seat_count()
    cabin_clause = (
        f"Cabin rows hold {left}+{right} seats; oval windows on BOTH sides. "
        if "background plate" in str(kind).lower() else ""
    )
    text = (
        f"Vertical 9:16 STRICT FLAT 2D storytime horror {kind}. "
        f"Solid flat colour fills with at most two tone values per surface; depth comes only "
        f"from overlapping flat shapes and straight perspective lines. "
        f"Extra thick uneven black ink outlines. Palette: near-black navy, bone white and one "
        f"muted teal only. {cabin_clause}"
        f"One continuous space, one viewpoint, no comic-book gutter layout, no borders, no text. "
        f"No gradient, no shading, no soft shadow, no blur, no simulated 3D depth, no beam of "
        f"light, no texture, not realistic."
    )
    if red_allowed:
        text += " Red is confined to blood, infected eyes and the recording dot."
    return text


def video_style_contract() -> str:
    """Field 1 for H3 VIDEO prompts: same flat/horror law as the plates.

    Unlike an image prompt this one never says 'no text' - a UI shot may own one
    on-screen timer, declared once by the caller.
    """
    left, right = seat_count()
    lc = load_map()["lighting_contract"]
    return (
        "Vertical 9:16 flat 2D storytime horror, icon-like. Solid flat colour fills with at "
        "most two tone values per surface, clean edges with bold uneven black outlines. "
        "Low-key night-horror lighting: one or two small emitting fixtures, cool dim slate "
        "walls clearly lighter than the navy seats, and 60 to 75 percent of each frame held "
        "in flat near-black shadow shapes with a heavy flat vignette. Palette: near-black "
        "navy, bone white and one muted teal only. "
        f"Cabin rows hold {left}+{right} seats and oval windows stand on BOTH sides. "
        "All clothing is near-black navy, bone white or one muted teal. "
        "All hair is one solid black silhouette. Faces show two simple solid dot eyes and one "
        "short mouth line, with a small tapered nose visible in side profile. Human hands show "
        "four gently curved fingers with small gaps and one separated thumb, softly rounded "
        "tips, solid fill. Figures are relaxed adults with continuous outer outlines and gently "
        "curved joints, about 1:6.5 to 1:7 head-to-body. Backgrounds keep layered flat depth "
        "and one-point perspective. The number of visible figures stays fixed from the first "
        "frame to the last. Depth comes only from overlap and straight perspective lines; "
        f"{lc['vignette']} No gradient, no shading, no soft shadow, no blur, no 3D, no texture, not realistic."
    )


def reference_block(refs: list[dict]) -> str:
    """Label every image ref by role; flat master must be Picture 1 for cabin plates."""
    if not refs:
        return ""
    lines = []
    for i, ref in enumerate(refs, 1):
        role = ref.get("role", "reference")
        lines.append(f"<Picture {i}> is the {role}. Copy only its {ref.get('copy', 'form')}; keep the flat storytime style.")
    return " ".join(lines)


def crowd_identity_text() -> str:
    """One-row generic passenger sheet; never carries Khang/Vy identity (E231)."""
    return (
        "Four distinct generic adult passengers, not the recurring leads, seated in one "
        "single horizontal row of equal-width cells: short combed black hair, side-parted "
        "black hair, close-cropped black hair and a low tied black knot; two solid dot eyes "
        "and one short mouth line on each face; relaxed adult proportions about 1:6.5 to "
        "1:7; hands with four gently curved fingers and one separated thumb resting on laps; "
        "each outfit a different flat fill drawn only from near-black navy, bone white and "
        "one muted teal."
    )


def strip_object_deletions(text: str) -> str:
    """Remove object-deletion clauses from prompt_visible, preserve style negations."""
    segments = re.split(r"(?<=[.;])\s+", str(text))
    kept = []
    for seg in segments:
        if DELETION_RE.search(seg) and not any(s in seg.lower() for s in STYLE_NEGATIONS):
            continue
        kept.append(seg)
    return re.sub(r"\s{2,}", " ", " ".join(kept)).strip()


def red_allowed_for(out_path: str, override: bool | None = None) -> bool:
    if override is not None:
        return bool(override)
    return any(token in str(out_path).lower() for token in RED_ALLOWED_ASSETS)


def validate_prompt(text: str, *, kind: str = "asset", red_allowed: bool = False,
                    refs: list[str] | None = None, out: str = "") -> tuple[list[str], list[str]]:
    """Return (hard_errors, warnings) for one prompt before it reaches H3."""
    hard: list[str] = []
    warn: list[str] = []
    t = str(text or "")

    if not t.strip():
        return ["empty prompt"], []
    # Field 1 position: style contract must lead.
    if not re.search(r"solid flat (?:colour|color) fills", t[:500], re.I):
        warn.append("style contract not found in first 500 chars")
    # E215: never inject a 3D topology image into a flat plate.
    if "/flat/" in out and any("route-map-3d" in str(r) for r in (refs or [])):
        hard.append("3D route map used as image ref for a flat plate (E215)")
    # E202: cabin variants need a Picture anchor.
    is_master = "cabin-master" in out  # the master itself is generated from the contract, not from a Picture ref
    if "/flat/" in out and not is_master and any(k in out for k in ("aisle", "seat27a", "phone-ins")):
        if not refs:
            hard.append("cabin plate has no Picture ref (E202)")
        elif refs[0] != master()["path"]:
            hard.append("first ref is not the QA-passed flat master")
    # E216: no stale seat count. The canonical pair is read from master_plate,
    # which changed from 2+2 to 1+1 on 26/11; compare EVERY pair in the text.
    left, right = seat_count()
    for m in re.finditer(r"\b(\d)\+(\d)\b", t):
        if (int(m.group(1)), int(m.group(2))) != (left, right):
            hard.append(f"stale seat pair {m.group(0)}; canonical is {left}+{right} (E216)")
    if STALE_SEAT_RE.search(t):
        hard.append(f"stale row/seat wording; canonical is {left}+{right} (E216)")
    # E298: cabin-map.compositing_note is QA metadata only. "composited later"
    # leaked from global-context into the G02 queued prompt and the gate only
    # warned afterwards. Fail at generation time, not after a GPU job.
    if re.search(r"\bcomposited\b|\bcompositing stage\b", t, re.I):
        hard.append("pipeline/compositing metadata in prompt_visible (E298)")
    # E162: object-deletion negations.
    if DELETION_RE.search(t):
        bad = DELETION_RE.search(t).group(0)
        hard.append(f"object-deletion negation in prompt: {bad!r} (E162)")
    # E200: colour priming.
    if not red_allowed and (RED_RE.search(t) or "đỏ" in t):
        hard.append("red mentioned while red_allowed=false (E200)")
    # Panel generator cue.
    if PANEL_RE.search(t):
        hard.append("panel/storybook-page cue in prompt")
    # E267/E268: a jerk shot must not pair discrete wrist/finger snaps with an
    # even/slow/smooth camera line. The trailing ambience line used to undo the beats.
    if (kind == "video" and re.search(r"\bwrist\b", t, re.I)
            and re.search(r"\bfingers\b", t, re.I)
            and re.search(r"\b(?:snap|snaps|jerk|jerks|flick|flicks|spasm|spasms)\b", t, re.I)
            and re.search(r"\b(?:continue evenly|continues evenly|slides slowly|slow pan|smoothly|eases closer|keeps drifting)\b", t, re.I)):
        hard.append("motion contradiction: wrist/finger snaps paired with even/slow/smooth drift (E268)")
    # E226: a raw asset path must never reach H3 visible prompt text. It becomes
    # spurious visual tokens and stray strokes near the vanishing point.
    if re.search(r"\b[\w\-./\\:]+\.(?:png|jpe?g|webp|json)\b", t, re.I):
        hard.append("raw asset path in visible prompt (E226)")
    # E227: every cabin plate carries the one positive light sentence from the map.
    if any(k in out for k in ("cabin-master", "aisle-flat", "seat27a-empty")):
        if "night-horror light" not in t.lower():
            hard.append("cabin plate has no lighting_contract.prompt_visible light field (E227)")
    if refs:
        verdicts = latest_verdicts()
        for r in refs:
            if not (ROOT / str(r)).exists():
                hard.append(f"ref file missing: {r}")
                continue
            v = verdicts.get(str(r))
            if not v:
                warn.append(f"ref not in QA ledger (legacy, not canon): {r}")
            elif v.get("superseded"):
                hard.append(f"ref is superseded: {r}")
            elif v.get("verdict") != "PASS":
                hard.append(f"ref latest verdict is {v.get('verdict')}: {r}")
    # E231: one-row crowd sheet waiver. Four distinct figures, one row, no lead names.
    if "crowd" in out.lower():
        low = t.lower()
        if "four distinct generic" not in low:
            hard.append("crowd sheet must state four distinct generic figures (E231)")
        if "one single horizontal row" not in low:
            hard.append("crowd sheet must be one single horizontal row (E231)")
        if re.search(r"\b(khang|vy)\b", t, re.I):
            hard.append("recurring character name leaked into crowd sheet prompt (E231)")
    return hard, warn


if __name__ == "__main__":
    c = load_contract()
    print(f"asset-contract {c['version']} | seat={seat_count()} | master={master()['path']}")
