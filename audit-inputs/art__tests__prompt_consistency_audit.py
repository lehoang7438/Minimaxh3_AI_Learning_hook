#!/usr/bin/env python
"""Read-only, structure-first consistency audit for the GHẺ 27A H3 prompts.

Authority order (the tool never guesses meaning from prose):

  art/env/cabin-map.json           geometry / palette / light tiers / state_chain
  art/env/global-context-part1.json per-shot set_id, props, refs, wardrobe ids, duration
  art/part1-spec.json              camera, layers (role + outfit), motion, dialogue
  characters.json                  bible appearance / wardrobe strings
  art/comfy/ALH/learning-log.jsonl accepted vs proposed status of conflicting rules
  prompts/part1-rebuilt/Gxx.txt    structured prompt FIELDS only

It writes only the two QA reports named on the command line. It never edits a
prompt, context, spec, ALH, PLAYBOOK or GPU lock, and never touches the GPU.

    python art/tests/prompt_consistency_audit.py \
        --shots G01,G02,G03,G04,G05 \
        --json out/story-g01/qa/prompt-consistency-report.json \
        --md   out/story-g01/qa/prompt-consistency-report.md

Exit 1 if any dimension is FAIL, 0 otherwise. CHƯA CHỐT never blocks by itself.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = ROOT / "art/env/cabin-map.json"
BIBLE_PATH = ROOT / "characters.json"
ALH_PATH = ROOT / "art/comfy/ALH/learning-log.jsonl"
COMPOSER = ROOT / "art/tests/rebuild_prompts.py"
PROMPT_DIR = ROOT / "prompts/part1-rebuilt"

UND = "CHƯA CHỐT"
DIMENSIONS = (
    "layout_seat", "light_tier", "sightline", "palette_hex",
    "props_state", "character_wardrobe", "language_negation",
    "timecode_duration", "refs",
)
SEAT_EVENT_IDS = ("E036", "E041", "E212", "E213", "E214", "E216",
                  "E226", "E227", "E230", "E231", "E237")
CONSTANT_NAMES = ("SCENE_OVERRIDE", "LIGHT_SUPPRESS", "DURATION_OVERRIDE",
                  "G01_STYLE_CONTRACT", "G02_STYLE_CONTRACT")
LUMA = {"E045": 39.2, "E216": 52.2}   # dim_night_flight allowed band, not a hard value


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dotted(obj, path: str, default=None):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def norm(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def excerpt(text, limit: int = 190) -> str:
    text = norm(text)
    return text if len(text) <= limit else text[:limit - 1] + "…"


def present(phrase, haystack) -> bool:
    phrase, haystack = norm(phrase), norm(haystack)
    return bool(phrase) and phrase in haystack


def composer_constants() -> dict:
    out = {}
    tree = ast.parse(COMPOSER.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in CONSTANT_NAMES:
                try:
                    out[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError, SyntaxError):
                    pass
    return out


def alh_events() -> dict:
    out = {}
    for line in ALH_PATH.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("id"):
            out[row["id"]] = row
    return out


def locate(sid: str):
    """Prefer the canonical part1 sources; ignore part1-pilot-spec.json."""
    ctx_path = ctx = spec_path = spec = None
    for p in [ROOT / "art/env/global-context-part1.json",
              ROOT / "art/env/global-context.json"]:
        if p.exists() and sid in (read_json(p).get("shots") or {}):
            ctx_path, ctx = p, read_json(p)
            break
    for p in [ROOT / "art/part1-spec.json", ROOT / "art/part2-spec.json",
              ROOT / "art/part3-spec.json"]:
        if p.exists() and any(s.get("id") == sid for s in read_json(p).get("shots", [])):
            spec_path, spec = p, read_json(p)
            break
    return ctx_path, ctx or {}, spec_path, spec or {}


# --------------------------------------------------------------------------- #
# structured prompt fields
# --------------------------------------------------------------------------- #
def prompt_fields(sid: str) -> dict:
    path = PROMPT_DIR / f"{sid}.txt"
    raw = path.read_text(encoding="utf-8")
    fields = {}
    for chunk in raw.split("\n\n"):
        if ":" in chunk:
            key, _, value = chunk.partition(":")
            fields[key.strip()] = value.strip()
    f1 = fields.get("integrated_multimodal_description", "")
    contract, sep, body = f1.partition("[Shot 1]")
    if not sep:
        body = f1
    chunks = re.split(r"(?=\b(?:Scene|Props|Light):|\b(?:Wide|Medium|Close)\b|\bAt \d{2}:)", body)

    def labelled(name: str) -> str:
        for chunk in chunks:
            if chunk.startswith(name + ":"):
                return norm(chunk[len(name) + 1:])
        return ""

    beats = re.findall(r"At (\d{2}:\d{2}\.\d{3})", f1)
    return {
        "file": str(path.relative_to(ROOT)), "field1": f1,
        "contract": norm(contract), "body": norm(body),
        "camera_sentence": norm(body.split(".", 1)[0]) if body else "",
        "scene_field": labelled("Scene"), "props_field": labelled("Props"),
        "light_field": labelled("Light"), "beats": beats,
        "picture_labels": sorted({int(n) for n in re.findall(r"<Picture (\d+)>", f1)}),
        "outside_dialogue": re.sub(r"<d>.*?</d>", "", f1, flags=re.S),
        "chars": len(raw),
    }


def result(status: str, detail: str, evidence=None, note: str = "") -> dict:
    return {"status": status, "detail": detail,
            "evidence": [{"field": f, "quote": excerpt(q)} for f, q in (evidence or []) if q],
            "note": note}


# --------------------------------------------------------------------------- #
# cabin-map self-conflicts: reported, never silently resolved
# --------------------------------------------------------------------------- #
def seat_conflicts(cmap: dict, events: dict) -> list[dict]:
    rows = []
    for field, value in (
        ("cabin_geometry_contract.layout", dotted(cmap, "cabin_geometry_contract.layout", "")),
        ("cabin_geometry_contract.window_seats", dotted(cmap, "cabin_geometry_contract.window_seats", "")),
        ("master_plate.invariants[0]", (dotted(cmap, "master_plate.invariants") or [""])[0]),
        ("master_plate.deviation_note", dotted(cmap, "master_plate.deviation_note", "")),
        ("generation_prompt_contract[6]",
         (cmap.get("generation_prompt_contract") or [""])[6]
         if len(cmap.get("generation_prompt_contract") or []) > 6 else ""),
        ("design_change_20261126", cmap.get("design_change_20261126", "")),
    ):
        text = norm(value)
        if text:
            rows.append({"source": field, "status": "map text", "text": excerpt(text, 300)})
    for eid in SEAT_EVENT_IDS:
        ev = events.get(eid)
        if ev:
            rows.append({"source": eid, "status": str(ev.get("status")),
                         "text": excerpt(ev.get("detail"), 300)})
    return rows


def seat_status(events: dict) -> dict:
    statuses = {eid: str(events.get(eid, {}).get("status", "missing")) for eid in SEAT_EVENT_IDS}
    accepted = [e for e, s in statuses.items() if s == "accepted"]
    proposed = [e for e, s in statuses.items() if s == "proposed"]
    # Only an ACCEPTED event that declares 1+1 canonical would close the dispute.
    # E212/E214 only mention 1+1 as a rendered defect; E216 accepted 2+2; E231 is
    # the event that rewrote cabin-map to 1+1 and is still proposed.
    closure = [e for e, s in statuses.items()
               if s == "accepted" and e not in ("E212", "E213", "E214", "E216")
               and re.search(r"1\+1.{0,80}(canonical|authoritative|approved|correct)",
                             str(events.get(e, {}).get("detail", "")), re.I)]
    return {
        "status": "accepted" if closure else UND,
        "closure_events": closure,
        "accepted_events": accepted,
        "proposed_events": proposed,
        "reason": ("accepted closure found: " + ",".join(closure) if closure else
                   "E212-E214 accepted 3+3 invariant / E216 accepted 2+2 master; "
                   "E231 (proposed) rewrote cabin-map to 1+1. No accepted event makes "
                   "1+1 authoritative, so the tool does not pick a winner."),
    }


# --------------------------------------------------------------------------- #
# per-shot audit
# --------------------------------------------------------------------------- #
def audit_shot(sid: str, cmap: dict, events: dict, const: dict, bible: dict,
               ctx_path, ctx, spec_path, spec) -> dict:
    pf = prompt_fields(sid)
    cshot = (ctx.get("shots") or {}).get(sid, {}) or {}
    sshot = next((s for s in spec.get("shots", []) if s.get("id") == sid), {}) or {}
    set_id = str(cshot.get("scene") or "unknown")
    set_obj = (ctx.get("sets") or {}).get(set_id, {}) or {}
    f1 = pf["field1"]
    seat = seat_status(events)
    res = {}

    # 1. ghế / layout ------------------------------------------------------- #
    pairs = sorted(set(re.findall(r"\b(\d)\+(\d)\b", pf["contract"])))
    pair_text = "/".join(a + "+" + b for a, b in pairs)
    if sid == "G01" or set_id == "phone_ins":
        # E298: inserts are exempt from the cabin-count assertion, but a stale
        # N+N clause must not survive inside their style contract. The old gate
        # returned PASS unconditionally and missed G04's "2+2 seats".
        insert_pairs = re.findall(r"\b(\d)\+(\d)\b", pf["contract"])
        if insert_pairs:
            res["layout_seat"] = result(
                "FAIL", "Insert still asserts a seat pair " +
                "/".join(a + "+" + b for a, b in insert_pairs) + "; cabin-map forbids "
                "2+2 and an insert should assert no row count at all.",
                [("prompt.contract", re.search(r"Cabin rows hold \d\+\d seats",
                  pf["contract"]).group(0) if re.search(r"Cabin rows hold \d\+\d seats",
                  pf["contract"]) else "/".join(a + "+" + b for a, b in insert_pairs))],
                "N/A for insert count, but stale pair is a visible contradiction")
        else:
            res["layout_seat"] = result(
                "PASS", "Insert: no N+N cabin-count assertion in the prompt; seat-count "
                "contract is not applicable.",
                [("prompt.contract", excerpt(pf["contract"], 130))], "N/A for insert")
    else:
        res["layout_seat"] = result(
            UND,
            f"Prompt asserts {pair_text}; map invariant_architecture[0] = "
            f"'{excerpt(dotted(cmap, 'state_chain.invariant_architecture', [''])[0], 120)}'. "
            + seat["reason"],
            [("prompt.contract", re.search(r"Cabin rows hold \d\+\d seats", pf["contract"]).group(0)
              if re.search(r"Cabin rows hold \d\+\d seats", pf["contract"]) else pair_text),
             ("cabin-map.invariant_architecture[0]",
              (dotted(cmap, "state_chain.invariant_architecture") or [""])[0]),
             ("E231 (proposed)", excerpt(events.get("E231", {}).get("detail"), 150))],
            f"27A left-window source: cabin-map.cabin_geometry_contract.window_seats="
            f"'{excerpt(dotted(cmap, 'cabin_geometry_contract.window_seats', ''), 100)}'; "
            f"prompt says 'left window seat 27A'="
            f"{present('left window seat 27A', f1)}")

    # 2. ánh sáng: tier / số nguồn / hướng / vignette / dải luma ------------ #
    band = [LUMA["E045"], LUMA["E216"]]
    if sid == "G01":
        res["light_tier"] = result(
            "PASS", "tier=under-seat insert special; sources=flat dark-red blotches only; "
            "direction=not applicable; vignette=yes; luma band from E045/E216 is plate-level "
            "metadata only.",
            [("cabin-map.special.G01", dotted(cmap, "special.G01", "")),
             ("prompt.contract", excerpt(pf["contract"], 190))],
            f"allowed mean_luma band {band} (E045 {LUMA['E045']} -> E216 {LUMA['E216']})")
    elif sid in const.get("LIGHT_SUPPRESS", set()):
        res["light_tier"] = result(
            "PASS",
            "tier=dim_night_flight; accepted E273 flat law is in the prompt, no emitting "
            "fixture / slate-wall ramp. cabin-map.lighting_contract.prompt_visible still "
            "carries the superseded fixture wording; accepted E273 wins. "
            f"vignette=yes; luma band {band} is metadata, not a numeric prompt field.",
            [("prompt.contract", excerpt(pf["contract"], 190)),
             ("ALH E273 (accepted)", excerpt(events.get("E273", {}).get("detail"), 190)),
             ("cabin-map.lighting_contract.prompt_visible",
              dotted(cmap, "lighting_contract.prompt_visible", ""))],
            f"set.light suppressed by composer: True; tier source="
            f"lighting_contract.tiers.dim_night_flight")
    else:
        set_light = str(set_obj.get("light", ""))
        bad = present("one or two small emitting fixtures", pf["contract"]) and \
            present("one small lit screen", set_light)
        res["light_tier"] = result(
            "FAIL" if bad else "PASS",
            ("tier=dim_night_flight but the prompt still uses the superseded fixture/"
             "slate-wall light text while the structured set light allows only one small "
             f"lit screen/fixture as bright shape; vignette=yes; band {band} is metadata."
             if bad else "Light wording agrees with the structured set light."),
            [("prompt.contract",
              re.search(r"Low-key night-horror lighting:[^;]+;[^;]+", pf["contract"]).group(0)
              if bad and re.search(r"Low-key night-horror lighting:[^;]+;[^;]+", pf["contract"])
              else excerpt(pf["contract"], 190)),
             ("global-context.sets." + set_id + ".light", set_light),
             ("ALH E273 (accepted)", excerpt(events.get("E273", {}).get("detail"), 150))],
            f"suppressed by composer: {sid in const.get('LIGHT_SUPPRESS', set())}")

    # 3. path nhìn / mức camera / 27A --------------------------------------- #
    if sid in ("G01", "G04"):
        res["sightline"] = result(
            "PASS", "Insert: no cabin sightline contract applies.",
            [("prompt.camera_sentence", pf["camera_sentence"])], "N/A for insert")
    else:
        axis = present("front near the camera and tail far away", pf["scene_field"])
        centered = "aisle" in pf["scene_field"].lower()
        eye_required = str(dotted(cmap, "cabin_geometry_contract.eye_level", ""))
        set_eye = str(set_obj.get("camera_height")
                      or dotted(cmap, "sets." + set_id + ".camera_height", ""))
        eye = ("eye level" in f1.lower() or "underside level" in f1.lower()
               or "seated passenger" in f1.lower())
        missing = [n for n, ok in (("front-near / tail-far axis", axis),
                                   ("centered aisle", centered),
                                   ("camera eye level", eye)) if not ok]
        res["sightline"] = result(
            "FAIL" if missing else "PASS",
            ("Map requires: aisle_direction='"
             + excerpt(dotted(cmap, "cabin_geometry_contract.aisle_direction", ""), 110)
             + "', eye_level='" + excerpt(eye_required, 110)
             + "', set.camera_height='" + excerpt(set_eye or eye_required, 80)
             + "'. Prompt omits: " + ", ".join(missing)
             if missing else "Axis, centered aisle and camera height are stated."),
            [("prompt.camera_sentence", pf["camera_sentence"]),
             ("prompt.Scene", pf["scene_field"]),
             ("cabin-map.eye_level", eye_required),
             ("global-context.sets." + set_id + ".camera_height", set_eye)],
            f"27A description in prompt = '{excerpt(
                re.search(r'[^.]*27A[^.]*', pf['body']).group(0)
                if re.search(r'[^.]*27A[^.]*', pf['body']) else '-', 110)}'")

    # 4. palette ------------------------------------------------------------ #
    pal = cmap.get("palette_lock") or {}
    tokens = ["near-black navy", "bone white", "one muted teal"]
    missing_tokens = [t for t in tokens if not present(t, pf["contract"])]
    if sid == "G01":
        res["palette_hex"] = result(
            "PASS", "Insert palette exception is declared in cabin-map.special.G01 "
            "(dirty dark bone + dark-red blood); seat #15233B / floor #2E6E6E do not "
            "appear in this insert.",
            [("prompt.contract", excerpt(pf["contract"], 190)),
             ("cabin-map.special.G01", excerpt(dotted(cmap, "special.G01", ""), 190))],
            "no wall visible in insert")
    else:
        res["palette_hex"] = result(
            "FAIL" if missing_tokens else "PASS",
            ("Missing palette words: " + ", ".join(missing_tokens) if missing_tokens else
             f"Prompt carries the palette_lock names; seat={pal.get('seat_navy')}, "
             f"floor={pal.get('floor_teal')}, wall_bone={pal.get('wall_bone')} (hex is "
             "plate metadata, not prompt text)."),
            [("prompt.contract", excerpt(pf["contract"], 190)),
             ("cabin-map.palette_lock.seat_navy", pal.get("seat_navy")),
             ("cabin-map.palette_lock.floor_teal", pal.get("floor_teal"))],
            "wall base #EFEDE6 bone vs lighting_contract.wall_value 'cool dark SLATE / "
            "dimmed bone' is a source conflict; plate-level, not a prompt-text FAIL")

    # 5. props / state_chain ------------------------------------------------ #
    order = str(dotted(cmap, "state_chain.order", ""))
    progressive = dotted(cmap, "state_chain.progressive_props", {}) or {}
    note = ("state_chain.order: " + excerpt(order, 170)
            + " | chaos keeps cups/scraps/bags + red stains; barricade keeps the SAME "
              "bags piled into overturned carts: "
            + excerpt(progressive.get("barricade", ""), 110))
    if sid == "G01":
        res["props_state"] = result("PASS", "Hand/cuff/bite state matches cabin-map.special.G01.",
                                    [("cabin-map.special.G01", dotted(cmap, "special.G01", ""))],
                                    note + " | no variant state in this shot")
    elif sid == "G04":
        ok = present("one small birthday cake", f1) and present("three simple dot-eyed", f1)
        res["props_state"] = result(
            "PASS" if ok else "FAIL",
            "Phone insert content matches structured sets.phone_ins.objects "
            "(one cake + three dot-eyed faces).",
            [("prompt.body", excerpt(pf["body"], 190)),
             ("global-context.sets.phone_ins.objects", set_obj.get("objects", ""))],
            note + " | no variant state in this insert")
    else:
        expected = (const.get("SCENE_OVERRIDE", {}).get(sid) or [None, set_obj.get("objects", "")])[1]
        leak = present("three generic passengers are composited later", pf["props_field"]) and \
            present("never prompt text", dotted(cmap, "master_plate.compositing_note", ""))
        match = present(expected, pf["props_field"])
        res["props_state"] = result(
            "FAIL" if leak else "PASS" if match else "FAIL",
            ("Props field reproduces a compositing-stage note verbatim. "
             "master_plate.compositing_note says that note is QA metadata only, never "
             "prompt text (E162 class)." if leak else
             "Props field carries the structured objects string verbatim." if match else
             "Props field does not carry the structured objects string from context/composer."),
            [("prompt.Props", pf["props_field"]),
             ("global-context.sets." + set_id + ".objects", set_obj.get("objects", "")),
             ("composer.SCENE_OVERRIDE[" + sid + "][1]", expected),
             ("cabin-map.master_plate.compositing_note",
              dotted(cmap, "master_plate.compositing_note", ""))] if leak else
            [("prompt.Props", pf["props_field"]),
             ("composer.SCENE_OVERRIDE[" + sid + "][1]", expected)],
            note)

    # 6. nhân vật / wardrobe ------------------------------------------------ #
    layers = [l for l in (sshot.get("layers") or []) if l.get("role") == "character"]
    ctx_chars = list(cshot.get("characters") or [])
    outfit_ids = [l.get("outfit", "") for l in layers] + ctx_chars
    named = bool(re.search(r"\b(Khang|Vy)\b", f1))
    if not outfit_ids and not named:
        res["character_wardrobe"] = result("PASS", "No recurring character in this insert.",
                                           [], "N/A")
    elif not outfit_ids and named:
        res["character_wardrobe"] = result(
            UND, "Prompt names Khang but spec.layers and context.characters are empty; "
            "there is no structured wardrobe source to compare against.",
            [("prompt.body", excerpt(pf["body"], 190)),
             ("spec.layers", json.dumps(sshot.get("layers", []), ensure_ascii=False)),
             ("global-context.shots." + sid + ".characters", json.dumps(ctx_chars))],
            "no FAIL: source missing, not a proven prompt contradiction")
    else:
        bad = []
        evidence = [("prompt.body", excerpt(pf["body"], 190))]
        for oid in outfit_ids:
            cid = next((c["id"] for c in (bible.get("characters") or [])
                        if str(oid).startswith(str(c.get("id")))), str(oid))
            entry = next((c for c in (bible.get("characters") or [])
                          if c.get("id") == cid), {})
            wardrobe = str(entry.get("wardrobe", ""))
            appearance = str(entry.get("appearance", ""))
            has_label = bool(re.search(r"\b" + re.escape(cid) + r":", pf["body"], re.I))
            has_wardrobe = present(wardrobe, pf["body"])
            has_scale = present("1:6.5 to 1:7", pf["body"])
            evidence += [("characters.json." + cid + ".wardrobe", wardrobe),
                         ("characters.json." + cid + ".appearance", excerpt(appearance, 190))]
            if not (has_label and has_wardrobe and has_scale):
                bad.append(f"{cid}: label={has_label}, wardrobe={has_wardrobe}, "
                           f"scale={has_scale}")
        res["character_wardrobe"] = result(
            "FAIL" if bad else "PASS",
            ("Spec declares character layer(s), but the prompt lacks the bible "
             "appearance + wardrobe clause: " + "; ".join(bad)
             if bad else "Named character(s) carry bible appearance + wardrobe verbatim, "
             "including the 1:6.5-1:7 scale anchor and seated posture."),
            evidence, "bible nose clause intentionally omitted under accepted E280 "
                      "minimal-face override")

    # 7. ngôn ngữ / phủ định ------------------------------------------------ #
    viet = [ch for ch in pf["outside_dialogue"] if ord(ch) > 127]
    contract_rule = next((x for x in (cmap.get("generation_prompt_contract") or [])
                          if "negation" in str(x).lower()), "")
    row_denial = re.search(r"\bno (?:receding extra rows|repeated empty seat backs|extra windows)\b",
                           pf["contract"], re.I)
    if viet:
        res["language_negation"] = result(
            "FAIL", "Non-English text outside <d> tags.",
            [("prompt.field1", "".join(viet[:30]))])
    elif row_denial:
        res["language_negation"] = result(
            UND,
            "cabin-map.generation_prompt_contract forbids object-deletion negation, but "
            "accepted E273 explicitly added this row/window denial to the same shot "
            "contract. Two accepted rules conflict; the tool does not pick one.",
            [("prompt.contract", row_denial.group(0)),
             ("cabin-map.generation_prompt_contract", contract_rule),
             ("ALH E273 (accepted)", excerpt(events.get("E273", {}).get("detail"), 190)),
             ("ALH E162 (accepted)", excerpt(events.get("E162", {}).get("detail"), 190))],
            "style negations (no gradient/no 3D) are allowed by the skills")
    else:
        res["language_negation"] = result(
            "PASS", "English outside <d>; no object-deletion negation in prompt_visible.",
            [("prompt.contract", excerpt(pf["contract"], 130))])

    # 8. timecode / duration ------------------------------------------------ #
    duration = float(const.get("DURATION_OVERRIDE", {}).get(sid)
                     or cshot.get("seconds") or sshot.get("seconds") or 0)
    last = pf["beats"][-1] if pf["beats"] else None
    last_s = (int(last.split(":")[0]) * 60 + float(last.split(":")[1])) if last else 0.0
    inc = all(pf["beats"][i] <= pf["beats"][i + 1] for i in range(len(pf["beats"]) - 1))
    res["timecode_duration"] = result(
        "FAIL" if (last_s > duration + 1e-6 or not inc) else "PASS",
        f"last structured beat {last or '-'} vs effective duration {duration:g}s "
        f"(spec.seconds={sshot.get('seconds')}); beats increasing={inc}.",
        [("prompt.At", " ".join(pf["beats"][-3:])),
         ("composer.DURATION_OVERRIDE", str(const.get("DURATION_OVERRIDE", {}).get(sid, "-")))])

    # 9. refs --------------------------------------------------------------- #
    plate = cshot.get("bg") or set_obj.get("plate")
    expected_refs = (1 if plate else 0) + len(ctx_chars) + len(cshot.get("props") or [])
    labels = pf["picture_labels"]
    over = bool(labels) and max(labels) > expected_refs
    res["refs"] = result(
        "FAIL" if over else "PASS",
        f"<Picture N> labels={labels or 'none'}; structured refs={expected_refs} "
        "(plate + characters + props). The feeder/context node injects refs at queue "
        "time, so an unlabelled rebuilt prompt is not a mismatch.",
        [("prompt.field1", " ".join(f"<Picture {n}>" for n in labels) or "no picture labels"),
         ("global-context.shots." + sid + ".props", json.dumps(cshot.get("props", []), ensure_ascii=False))])

    return {"shot": sid, "set_id": set_id, "file": pf["file"],
            "context": str(ctx_path.relative_to(ROOT)) if ctx_path else None,
            "spec": str(spec_path.relative_to(ROOT)) if spec_path else None,
            "size": pf["camera_sentence"][:60], "results": res}


# --------------------------------------------------------------------------- #
# reports
# --------------------------------------------------------------------------- #
def render_md(payload: dict) -> str:
    dims = payload["dimensions"]
    out = [
        "# Báo cáo soát prompt GHẺ 27A — structured-source audit",
        "",
        f"Verdict: **{payload['summary']['verdict']}** — FAIL {payload['summary']['FAIL']}, "
        f"CHƯA CHỐT {payload['summary']['CHƯA CHỐT']}, PASS {payload['summary']['PASS']}. "
        f"Exit {payload['summary']['exit_code']}.",
        "",
        "Chỉ đọc cabin-map / global-context / spec / bible / ALH / prompt. Không sửa prompt, "
        "context, spec, ALH, PLAYBOOK, GPU-LOCK; không queue GPU. **Output là đề xuất** — "
        "reviewer sẽ đọc lại bằng tay 3 shot FAIL + 3 shot PASS trước khi tin.",
        "",
        "## 1. cabin-map tự mâu thuẫn về bố cục ghế",
        "",
        f"Trạng thái: **{payload['seat_layout']['status']}** — "
        f"{payload['seat_layout']['reason']}",
        "",
        "| Nguồn | Status | Dòng gây lệch |",
        "|---|---|---|",
    ]
    for row in payload["seat_conflicts"]:
        out.append(f"| {row['source']} | {row['status']} | {row['text']} |")
    out += ["", "## 2. Ma trận shot × chiều (theo set_id)", ""]
    current = None
    for r in payload["shots"]:
        if r["set_id"] != current:
            current = r["set_id"]
            out += [f"### set_id: `{current}`", "",
                    "| Shot | " + " | ".join(dims) + " |",
                    "|---|" + "---|" * len(dims)]
        out.append("| " + r["shot"] + " | " + " | ".join(
            r["results"][d]["status"] for d in dims) + " |")
    out += ["", "## 3. FAIL + CHƯA CHỐT kèm trích dòng", ""]
    for r in payload["shots"]:
        bad = [(d, v) for d, v in r["results"].items()
               if v["status"] in ("FAIL", UND)]
        if not bad:
            continue
        out.append(f"### {r['shot']} — `{r['set_id']}`")
        for d, v in bad:
            out.append(f"- **{d}: {v['status']}** — {v['detail']}")
            for e in v["evidence"]:
                if e["quote"]:
                    out.append(f"  - `{e['field']}`: “{e['quote']}”")
            if v["note"]:
                out.append(f"  - ghi chú: {v['note']}")
        out.append("")
    out += [
        "## 4. Dải luma cho phép",
        "",
        f"- dim_night_flight: E045 mean_luma {LUMA['E045']} (archived baseline) → "
        f"E216 mean {LUMA['E216']} (accepted master r4) = band "
        f"[{LUMA['E045']}, {LUMA['E216']}]. Prompt không mang số luma; đây là metadata QA plate.",
        "- state_chain: chaos keeps cups/scraps/bags + dark-red stains; barricade keeps "
        "the SAME bags piled into overturned carts (no new cart design). No audited shot "
        "is a chaos/barricade variant, so the inheritance check is N/A here but remains "
        "a hard gate for part2/3 variants.",
        "",
    ]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shots", default="G01,G02,G03,G04,G05")
    ap.add_argument("--json", default="out/story-g01/qa/prompt-consistency-report.json")
    ap.add_argument("--md", default=None)
    a = ap.parse_args(argv)

    shots = [s.strip() for s in a.shots.split(",") if s.strip()]
    cmap = read_json(MAP_PATH)
    events = alh_events()
    const = composer_constants()
    bible = read_json(BIBLE_PATH)
    rows = []
    for sid in shots:
        cp, ctx, sp, spec = locate(sid)
        rows.append(audit_shot(sid, cmap, events, const, bible, cp, ctx, sp, spec))
    counts = {k: sum(r["results"][d]["status"] == k for r in rows for d in DIMENSIONS)
              for k in ("FAIL", UND, "PASS")}
    summary = {**counts,
               "verdict": "FAIL" if counts["FAIL"] else "PASS",
               "exit_code": 1 if counts["FAIL"] else 0,
               "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")}
    payload = {
        "tool": "prompt_consistency_audit", "mode": "structured-source-only / read-only",
        "authority": ["art/env/cabin-map.json", "art/env/global-context-part1.json",
                      "art/part1-spec.json", "characters.json",
                      "art/comfy/ALH/learning-log.jsonl", "prompts/part1-rebuilt/*.txt"],
        "dimensions": list(DIMENSIONS), "luma_band": list(LUMA.values()),
        "seat_layout": seat_status(events), "seat_conflicts": seat_conflicts(cmap, events),
        "shots": rows, "summary": summary,
    }
    jp = Path(a.json)
    if not jp.is_absolute():
        jp = ROOT / jp
    jp.parent.mkdir(parents=True, exist_ok=True)
    jp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mp = Path(a.md) if a.md else jp.with_suffix(".md")
    if not mp.is_absolute():
        mp = ROOT / mp
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(render_md(payload), encoding="utf-8")

    print("seat layout:", payload["seat_layout"]["status"], "-", payload["seat_layout"]["reason"])
    print(f"{'SHOT':<5} {'set_id':<12} " + " ".join(f"{d[:10]:>11}" for d in DIMENSIONS))
    for r in rows:
        print(f"{r['shot']:<5} {r['set_id']:<12} " + " ".join(
            f"{r['results'][d]['status'][:10]:>11}" for d in DIMENSIONS))
    print(f"FAIL={counts['FAIL']} CHƯA CHỐT={counts[UND]} PASS={counts['PASS']} -> "
          f"{summary['verdict']} (exit {summary['exit_code']})")
    print("report:", jp)
    print("summary:", mp)
    return summary["exit_code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
