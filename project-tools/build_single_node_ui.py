"""Build the ONE H3 UI workflow: Ghe27AContext -> FreeVideoMedia -> FreeVideoGenerate -> SaveVideo.

    python art/tests/build_single_node_ui.py              # auto: wire only what the live node supports
    python art/tests/build_single_node_ui.py --shot G02   # bake G02 prompt/seconds/prefix (pre-restart)
    python art/tests/build_single_node_ui.py --wire off   # never wire seconds/width/height
    python art/tests/build_single_node_ui.py --wire on    # force wiring (file for after the restart)

The graph is generated from scratch, never copied from a master template. Switching `shot_id`
on the context node re-resolves assets, prompt, first frame, voice, duration and canvas, so no
per-shot workflow files are needed.

Canvas and duration come from `art/env/global-context.json` (`render.width/height`, per-shot
`seconds`) through the node's `seconds` / `width` / `height` outputs. Those three outputs were
added on 2026-11-25, so a server started before that still reports five outputs and would raise
`IndexError` in `validate_inputs` if a prompt linked slot 5-7. `--wire auto` therefore checks
`/object_info` and skips those three links until ComfyUI is restarted; re-run the builder then
(or queue `--wire on`) to switch duration/canvas from widgets to live context values.
"""
from __future__ import annotations

import argparse
import json
import shutil
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "art" / "comfy"
CONTEXT = ROOT / "art" / "env" / "global-context.json"
UI_DIR = Path(r"C:\Users\Admin\FreeVideo\ComfyUI\user\default\workflows\H3-AllInOne")

DEFAULT_SHOT = "G01"
FALLBACK = {"width": 704, "height": 1280, "seconds": 5.0}
SEED = 2026112501
ROUTE_CHOICES = ("auto", "fresh", "fresh_audio", "continue_voice",
                 "continue_anchor", "continue_media", "continue_media_plain")
ROUTE_NOTE = """
ROUTES (context node widgets): auto | fresh | fresh_audio | continue_voice |
continue_anchor | continue_media | continue_media_plain. `route_media` is a JSON
array of up to three {"kind":"image","path":"..."} rows; `route_audio` defaults to
G01's timbre sample art/env/voice-narrator.wav for fresh_audio; `route_continue_from`
is the previous clip for continue_* routes; `route_anchor` is the single anchor image.
Hard conflicts (checked in the node before the GPU): continue_anchor + route_media,
route_audio + any continue_* route, four or more images, and continue_anchor +
first_frame_reference. Every route writes audio_use='reference'.

The route outputs need the rebuilt Ghe27AContext node. After editing the node,
RESTART ComfyUI, then re-run `python art/tests/build_single_node_ui.py` so the
route links are wired; before that restart this file stays queueable without them.
"""

NOTE_WIRED = """GHẾ 27A · H3 single chain

Ghe27AContext -> FreeVideoMedia -> FreeVideoGenerate -> SaveVideo
                                  \\-> PreviewAny (context report)

Change `shot_id` (G01..G50) and press Queue Prompt. Assets, prompt, first frame, voice,
duration and canvas all come from art/env/global-context.json. `context_path` points at art/env/global-context.json (absolute until the 25/11 node is loaded,
then the builder writes it relative); point it at global-context-part2.json / -part3.json for shots G21+ of those
parts (the node also re-points itself and says so in the report if the shot lives elsewhere).

seconds / width / height ARE wired from the context node: changing shot_id changes clip
length (shots[].seconds) and canvas (render.width/height) with no other edit.

Sampling: two-pass acceleration, 8 first-pass steps + 3 second-pass steps (defaults).
Seed: FIXED — a take can be reproduced; set it back to `randomize` only when hunting.
Output: SaveVideo -> output/ghe27a/<shot>_h3_*.mp4 (e.g. G01_h3_00001.mp4). The prefix is
stamped for the shot this file was built for: re-run the builder (or edit the prefix) when
you change shot_id, otherwise every take lands under the same name.
Resolution: upscale_factor `2` is the engine's "no upscale" sentinel (it returns no option),
so the file stays at the canvas above — it does NOT render 1408x2560.

The report outputs are wired to PreviewAny: the context report prints shot, part, refs,
first-frame origin, voice file, canvas, seconds and prompt length; H3's own report prints what
the sampler actually received. Read them when a shot looks wrong.
"""

NOTE_WIDGETS = """GHẾ 27A · H3 single chain

Ghe27AContext -> FreeVideoMedia -> FreeVideoGenerate -> SaveVideo
                                  \\-> PreviewAny (context report)

Change `shot_id` (G01..G50) and press Queue Prompt. Assets, prompt, first frame, voice come
from art/env/global-context.json. `context_path` is relative to the project root; point it at
global-context-part2.json / -part3.json for shots G21+ of those parts (the node also
re-points itself and says so in the report if the shot lives elsewhere).

DURATION AND CANVAS ARE WIDGETS IN THIS FILE: {w} x {h}, {s:.1f} s. This session still runs
the context-node build from before 25/11 (5 outputs), so linking seconds/width/height would
break the queue. Restart ComfyUI once, then re-run `python art/tests/build_single_node_ui.py`
(auto mode wires the three outputs) to make shot_id drive duration and canvas.

Sampling: two-pass acceleration, 8 first-pass steps + 3 second-pass steps (defaults).
Seed: FIXED — a take can be reproduced; set it back to `randomize` only when hunting.
Output: SaveVideo -> output/ghe27a/<shot>_h3_*.mp4 (e.g. G01_h3_00001.mp4). The prefix is
stamped for the shot this file was built for: re-run the builder (or edit the prefix) when
you change shot_id, otherwise every take lands under the same name.
Resolution: upscale_factor `2` is the engine's "no upscale" sentinel (it returns no option),
so the file stays at the canvas above — it does NOT render 1408x2560.

The report outputs are wired to PreviewAny: the context report prints shot, part, refs,
first-frame origin, voice file, canvas, seconds and prompt length; H3's own report prints what
the sampler actually received. Read them when a shot looks wrong.
"""


def node(nid: int, kind: str, pos, size, title: str, order: int,
         inputs=None, outputs=None, widgets=None) -> dict:
    return {
        "id": nid, "type": kind, "pos": list(pos), "size": list(size),
        "flags": {}, "order": order, "mode": 0,
        "inputs": inputs or [], "outputs": outputs or [],
        "properties": {"Node name for S&R": kind},
        "widgets_values": widgets or [],
        "title": title,
    }


def out(name: str, kind: str, slot: int) -> dict:
    return {"name": name, "type": kind, "links": [], "slot_index": slot}


def socket(name: str, kind: str) -> dict:
    return {"name": name, "type": kind, "link": None}


def widget(name: str, kind: str) -> dict:
    return {"name": name, "type": kind, "link": None, "widget": {"name": name}}


def load_context(shot_id: str | None = None) -> dict:
    """Context that owns the shot: part2/part3 shots are not in the default file."""
    if shot_id:
        for path in sorted((ROOT / "art" / "env").glob("global-context*.json")):
            try:
                ctx = json.loads(path.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            if shot_id in (ctx.get("shots") or {}):
                return ctx
    return json.loads(CONTEXT.read_text(encoding="utf-8-sig"))


def default_prompt(shot_id: str) -> str:
    for part in (1, 2, 3):
        path = ROOT / "prompts" / f"part{part}-rebuilt" / f"{shot_id}.txt"
        if path.exists():
            return path.read_text(encoding="utf-8-sig")[:8000]
    return "integrated_multimodal_description: [Shot 1] ...\n\noverall_soundscape: ...\n\nnon_diegetic_music: N/A"


def context_outputs(server: str) -> list[str] | None:
    """Output types the LIVE server reports for the context node (None when unreachable)."""
    try:
        with urllib.request.urlopen(f"{server}/object_info/FreeVideoGhe27AContext", timeout=4) as reply:
            return list(json.load(reply)["FreeVideoGhe27AContext"]["output"])
    except Exception:
        return None


def build(ctx: dict, wire_motion: bool, shot_id: str | None = None,
          relative_context: bool = False, wire_routes: bool = False) -> dict:
    shots = sorted(ctx.get("shots") or {})
    if not (shot_id and shot_id in shots):
        shot_id = DEFAULT_SHOT if DEFAULT_SHOT in shots else (shots[0] if shots else DEFAULT_SHOT)
    render = ctx.get("render") or {}
    width = int(render.get("width") or FALLBACK["width"])
    height = int(render.get("height") or FALLBACK["height"])
    shot = (ctx.get("shots") or {}).get(shot_id) or {}
    seconds = float(shot.get("seconds") or shot.get("target_duration") or FALLBACK["seconds"])
    note = (NOTE_WIRED if wire_motion else NOTE_WIDGETS.format(w=width, h=height, s=seconds))
    note += ROUTE_NOTE

    context_node = node(
        2, "FreeVideoGhe27AContext", (40, 420), (380, 280),
        "Ghe27A · CONTEXT — change shot_id here", 1,
        outputs=[out("assets", "STRING", 0), out("prompt", "STRING", 1),
                 out("first_frame", "IMAGE", 2), out("reference_audio", "AUDIO", 3),
                 out("report", "STRING", 4), out("seconds", "FLOAT", 5),
                 out("width", "INT", 6), out("height", "INT", 7),
                 out("continue_from", "STRING", 8),
                 out("first_frame_reference", "BOOLEAN", 9),
                 out("voice_reference", "BOOLEAN", 10),
                 out("audio_use", "STRING", 11),
                 out("route_report", "STRING", 12)],
        widgets=[shot_id, "art/env/global-context.json" if relative_context else str(CONTEXT),
                 True, True, "auto", "[]", "", "", ""],
    )

    # Input order mirrors FreeVideoMedia.input_order from /object_info: a positional
    # widgets_values array only lines up when the widget inputs sit where the schema says.
    media_inputs = [widget("assets", "STRING"), socket("first", "IMAGE"), socket("last", "IMAGE")]
    media_inputs += [socket("reference" if i == 1 else f"reference_{i}", "IMAGE") for i in range(1, 9)]
    media_inputs += [socket("reference_audio", "AUDIO"), widget("audio_use", "COMBO")]
    media_node = node(
        3, "FreeVideoMedia", (520, 420), (420, 700),
        "H3 · media (plate + cast + voice)", 2,
        inputs=media_inputs,
        outputs=[out("media", "FREEVIDEO_MEDIA", 0)],
        widgets=["[]", "reference"],
    )

    # FreeVideoGenerate.input_order: text, width, height, seconds, seed (required) then
    # first ... media, two_pass. The app serialises two_pass last because it is optional.
    generate_inputs = [
        widget("text", "STRING"), widget("width", "INT"),
        widget("height", "INT"), widget("seconds", "FLOAT"),
        widget("seed", "INT"),
        socket("first", "IMAGE"), socket("last", "IMAGE"),
        socket("references", "FREEVIDEO_REFERENCES"), socket("loras", "FREEVIDEO_LORAS"),
        socket("conditioning", "CONDITIONING"), socket("media", "FREEVIDEO_MEDIA"),
        socket("continue_from", "STRING"), socket("first_frame_reference", "BOOLEAN"),
        socket("voice_reference", "BOOLEAN"), widget("two_pass", "BOOLEAN"),
    ]
    generate_node = node(
        4, "FreeVideoGenerate", (1000, 420), (660, 980),
        f"H3 · generate ({width}x{height}, 9:16)", 3,
        inputs=generate_inputs,
        outputs=[out("video", "VIDEO", 0), out("report", "STRING", 1)],
        widgets=[default_prompt(shot_id), width, height, seconds, SEED, "fixed", True],
    )

    save_node = node(
        5, "SaveVideo", (1720, 420), (380, 280),
        "H3 · save", 4,
        inputs=[socket("video", "VIDEO")],
        outputs=[out("VIDEO", "VIDEO", 0)],
        widgets=[f"ghe27a/{shot_id}_h3", "mp4"],
    )

    # The context report is otherwise invisible: a wrong shot_id or a context_path pointing at
    # another part resolved silently. PreviewAny prints it in the queue result.
    report_node = node(
        6, "PreviewAny", (40, 780), (380, 320),
        "Ghe27A · context report (check this)", 5,
        inputs=[socket("source", "*")],
        outputs=[out("STRING", "STRING", 0)],
        widgets=[],
    )

    # H3's own report says what the sampler really received (first frame, voice, upscale).
    generate_report_node = node(
        7, "PreviewAny", (1720, 760), (380, 300),
        "H3 · generate report", 6,
        inputs=[socket("source", "*")],
        outputs=[out("STRING", "STRING", 0)],
        widgets=[],
    )

    doc = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "ghe27a-h3-single-chain")),
        "revision": 4,
        "last_node_id": 7,
        "last_link_id": 0,
        "nodes": [node(1, "Note", (40, 40), (960, 320), "How to use", 0, widgets=[note]),
                  context_node, media_node, generate_node, save_node, report_node,
                  generate_report_node],
        "links": [],
        "groups": [{"title": "H3 · context -> media -> generate -> save",
                    "bounding": [20, 380, 2120, 1100], "color": "#3f789e",
                    "font_size": 30, "flags": {}}],
        "config": {},
        "extra": {"ds": {"scale": 0.75, "offset": [40, 40]}, "freevideo_studio": True},
        "version": 0.4,
    }

    by_id = {n["id"]: n for n in doc["nodes"]}

    def wire(src: int, src_slot: int, dst: int, input_name: str, kind: str) -> None:
        target = by_id[dst]
        index = next(i for i, item in enumerate(target["inputs"]) if item["name"] == input_name)
        lid = doc["last_link_id"] + 1
        doc["last_link_id"] = lid
        doc["links"].append([lid, src, src_slot, dst, index, kind])
        target["inputs"][index]["link"] = lid
        by_id[src]["outputs"][src_slot]["links"].append(lid)

    wire(2, 0, 3, "assets", "STRING")
    wire(2, 1, 4, "text", "STRING")
    wire(2, 2, 3, "first", "IMAGE")
    wire(2, 3, 3, "reference_audio", "AUDIO")
    wire(2, 4, 6, "source", "STRING")
    wire(3, 0, 4, "media", "FREEVIDEO_MEDIA")
    wire(4, 0, 5, "video", "VIDEO")
    wire(4, 1, 7, "source", "STRING")
    if wire_motion:
        wire(2, 5, 4, "seconds", "FLOAT")
        wire(2, 6, 4, "width", "INT")
        wire(2, 7, 4, "height", "INT")
    if wire_routes:
        wire(2, 11, 3, "audio_use", "STRING")
        wire(2, 8, 4, "continue_from", "STRING")
        wire(2, 9, 4, "first_frame_reference", "BOOLEAN")
        wire(2, 10, 4, "voice_reference", "BOOLEAN")

    return doc


def resolve_wiring(mode: str, outputs: list[str] | None, server: str) -> tuple[bool, str]:
    if mode == "on":
        return True, "forced by --wire on"
    if mode == "off":
        return False, "disabled by --wire off"
    if outputs is None:
        return False, f"server {server} unreachable — widgets keep the graph queueable"
    if "seconds" in outputs and "width" in outputs and "height" in outputs:
        return True, f"live node exposes {len(outputs)} outputs including seconds/width/height"
    return False, (f"live node still exposes {len(outputs)} outputs — restart ComfyUI, "
                   f"then re-run this builder")


def resolve_route_wiring(mode: str, outputs: list[str] | None, server: str) -> tuple[bool, str]:
    if mode == "on":
        return True, "forced by --wire-routes on"
    if mode == "off":
        return False, "disabled by --wire-routes off"
    if outputs is None:
        return False, f"server {server} unreachable — route widgets keep the graph queueable"
    if "route_report" in outputs and len(outputs) >= 13:
        return True, f"live node exposes the 13 route-aware outputs"
    return False, (f"live node still exposes {len(outputs)} outputs — restart ComfyUI, "
                   f"then re-run this builder")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wire", choices=("auto", "on", "off"), default="auto")
    ap.add_argument("--wire-routes", choices=("auto", "on", "off"), default="auto")
    ap.add_argument("--shot", default=None,
                    help="bake this shot into the widgets (prompt, seconds, save prefix) — "
                         "use it before the restart, when shot_id cannot drive duration")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--out", type=Path, default=OUT / "h3-single-node-ui.json")
    args = ap.parse_args()

    outputs = context_outputs(args.server)
    wire_motion, reason = resolve_wiring(args.wire, outputs, args.server)
    wire_routes, route_reason = resolve_route_wiring(args.wire_routes, outputs, args.server)
    # Relative context_path needs the 25/11 node (it resolves it against the project root).
    # The old build reads it from ComfyUI's CWD, so the shipped file keeps the absolute path
    # until the restart, then the builder switches it automatically.
    relative_context = bool(outputs and "seconds" in outputs)
    doc = build(load_context(args.shot), wire_motion, args.shot, relative_context, wire_routes)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.out.resolve() == (OUT / "h3-single-node-ui.json").resolve() and UI_DIR.exists():
        shutil.copy2(args.out, UI_DIR / "h3-single-node-ui.json")

    active = [n for n in doc["nodes"] if n["mode"] == 0 and n["type"] != "Note"]
    main_chain = [n for n in active if n["type"] != "PreviewAny"]
    print(f"{args.out}  nodes={len(doc['nodes'])} links={len(doc['links'])} "
          f"active={len(active)} groups={len(doc['groups'])}")
    print("chain: " + " -> ".join(n["type"] for n in main_chain)
          + "   (context + generate reports -> PreviewAny)")
    print(f"wiring seconds/width/height: {'ON ' if wire_motion else 'OFF'} ({reason})")
    print(f"wiring route outputs:       {'ON ' if wire_routes else 'OFF'} ({route_reason})")
    if not wire_routes:
        print("note: routes are in the widgets but their outputs are not linked until ComfyUI is restarted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
