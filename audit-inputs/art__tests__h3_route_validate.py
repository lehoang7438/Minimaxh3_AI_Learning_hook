"""GPU-free preflight for the six H3 MiniMax routes.

    python art/tests/h3_route_validate.py

Checks every valid route and every hard conflict. Nothing is staged and no GPU
job is queued. Exits non-zero on any unexpected result.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from h3_route_rules import validate_route  # noqa: E402

PREV = "C:/Users/Admin/FreeVideo/ComfyUI/output/chain/G02.mp4"
ANCHOR = "C:/Users/Admin/FreeVideo/ComfyUI/input/g02-last.png"
IMAGE = "art/assets/h3/refs/cabin-plate.png"
VOICE = "art/env/voice-narrator.wav"

VALID = [
    ("fresh", dict(route="fresh")),
    ("fresh_audio", dict(route="fresh_audio")),
    ("continue_voice", dict(route="continue_voice", continue_from=PREV)),
    ("continue_anchor", dict(route="continue_anchor", continue_from=PREV, continue_anchor=ANCHOR)),
    ("continue_media", dict(route="continue_media", continue_from=PREV, media=[IMAGE])),
    ("continue_media_plain", dict(route="continue_media_plain", continue_from=PREV, media=[IMAGE])),
]

CONFLICTS = [
    ("anchor + media", dict(route="continue_anchor", continue_from=PREV,
                            continue_anchor=ANCHOR, media=[IMAGE])),
    ("audio + continue", dict(route="continue_voice", continue_from=PREV, audio=VOICE)),
    ("four images", dict(route="continue_media", continue_from=PREV,
                         media=[IMAGE] * 4)),
    ("anchor + first-frame", dict(route="continue_anchor", continue_from=PREV,
                                  continue_anchor=ANCHOR, first_frame_reference=True)),
    ("dirty row", dict(route="continue_media", continue_from=PREV,
                       media=[{"kind": "image", "path": IMAGE, "sha256": "x"}])),
]


def validate_graphs() -> list[str]:
    """Offline structural check; real /object_info preflight needs the ComfyUI restart."""
    root = Path(__file__).resolve().parents[2]
    problems = []
    api = json.loads((root / "art" / "comfy" / "h3-master.json").read_text(encoding="utf-8"))
    ctx = api["1"]["inputs"]
    for key in ("route", "route_media", "route_audio", "route_continue_from", "route_anchor"):
        if key not in ctx:
            problems.append(f"h3-master.json: node 1 missing {key}")
    if api["3"]["inputs"].get("continue_from") != ["1", 8]:
        problems.append("h3-master.json: continue_from is not wired from context slot 8")

    ui = json.loads((root / "art" / "comfy" / "h3-single-node-ui.json").read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in ui["nodes"]}
    names = [out["name"] for out in nodes[2]["outputs"]]
    for key in ("continue_from", "first_frame_reference", "voice_reference", "audio_use", "route_report"):
        if key not in names:
            problems.append(f"h3-single-node-ui.json: context output {key} missing")
    ginputs = [item["name"] for item in nodes[4]["inputs"]]
    for key in ("continue_from", "first_frame_reference", "voice_reference"):
        if key not in ginputs:
            problems.append(f"h3-single-node-ui.json: generate input {key} missing")
    return problems


def main() -> int:
    failures = []
    for problem in validate_graphs():
        print("FAIL ", problem)
        failures.append(problem)
    for name, kwargs in VALID:
        try:
            plan = validate_route(**kwargs)
        except ValueError as exc:
            failures.append(f"VALID {name} rejected: {exc}")
            continue
        assert plan["audio_use"] == "reference", name
        print(f"PASS  {name:22s} audio_use={plan['audio_use']} "
              f"voice={plan['voice_reference']} refs={len(plan['media'])}")
    for name, kwargs in CONFLICTS:
        try:
            validate_route(**kwargs)
        except ValueError as exc:
            print(f"BLOCK {name:22s} {exc}")
        else:
            failures.append(f"CONFLICT {name} was not blocked")
    for failure in failures:
        print("FAIL ", failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
