"""Ghe27AContext — one node that resolves the project's global H3 context.

Reads art/env/global-context.json, picks the right character/scene/prop references,
voice sample and first-frame anchor for a shot, and exposes them as real ComfyUI outputs
so they can be wired into FreeVideoMedia / FreeVideoGenerate in the UI.

Install: copy this folder under ComfyUI/custom_nodes/ (already done) and restart ComfyUI.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from comfy_extras.nodes_audio import load as load_audio
import folder_paths

ROOT = Path(r"C:\Users\Admin\Documents\Default Project")
DEFAULT_CONTEXT = str(ROOT / "art" / "env" / "global-context.json")
FILM = ROOT / "out" / "part1.mp4"
CLIPS = ROOT / "out" / "part1-t2v"


def route_rules():
    """Load the single source of truth shared with art/tests/h3_route_validate.py."""
    import importlib.util
    path = ROOT / "art" / "tests" / "h3_route_rules.py"
    spec = importlib.util.spec_from_file_location("ghe27a_h3_route_rules", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def part_of(context_path: str) -> str:
    """Part number from the context file name, so part2/part3 resolve their own prompts.

    global-context.json is the merged/part-1 view and keeps the old behaviour.
    """
    import re
    match = re.search(r"global-context-part(\d+)", Path(context_path).name)
    return match.group(1) if match else "1"


def _shots():
    """Shot ids across every part context, so one graph can pick G01..G50.

    global-context.json only carries part 1; the combo used to stop at G25 and made
    part2/part3 shots unselectable even though the node resolves them fine.
    """
    ids = set()
    for path in sorted((ROOT / "art" / "env").glob("global-context*.json")):
        try:
            ids.update(json.loads(path.read_text(encoding="utf-8-sig"))["shots"])
        except Exception:
            continue
    return sorted(ids) or ["G01"]


def resolve_context(context_path: str, shot_id: str):
    """Open the context, and re-point it when the shot lives in another part.

    A relative `context_path` is resolved against the project root so the widget can read
    `art/env/global-context.json` instead of an absolute Windows path. Picking G35 while
    the widget still points at part 1 used to raise a bare KeyError with no hint; now the
    node finds the context that owns the shot and says so in `report`.
    """
    path = Path(context_path)
    if not path.is_absolute():
        path = ROOT / path
    ctx = json.loads(path.read_text(encoding="utf-8-sig"))
    if shot_id in (ctx.get("shots") or {}):
        return path, ctx, ""
    for candidate in sorted((ROOT / "art" / "env").glob("global-context*.json")):
        try:
            other = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if shot_id in (other.get("shots") or {}):
            return (candidate, other,
                    f"context={candidate.name} (context_path pointed at {path.name})")
    raise ValueError(f"shot {shot_id} is not in {path.name} or any global-context*.json")


def spec_shot(part: str, shot_id: str) -> dict:
    """The spec entry: dialogue lives there, not in the global-context shot entry."""
    try:
        spec = json.loads((ROOT / "art" / f"part{part}-spec.json").read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return next((s for s in spec.get("shots", []) if s.get("id") == shot_id), {})


def compose_prompt(raw: str, ctx: dict, scene: dict, shot_id: str, shot: dict,
                   part: str, has_voice: bool = True, with_first: bool = True) -> str:
    """Keep the rebuilt field's order: style contract first, then refs, then [Shot 1].

    v1 prepended a "Set continuity / Objects / Light / wardrobe" blob, which pushed the
    style contract ~1900 characters into field 1 and repeated every scene fact (the G02
    painterly drift). The rebuilt prompt already carries scene, props, wardrobe and the
    close-up prop filtering, so this only adds the first-frame sentence and the <Audio 1>
    line, both AFTER the contract and BEFORE [Shot 1].
    """
    raw = raw.replace("\r\n", "\n")
    head, sep, tail = raw.partition("overall_soundscape:")
    if not sep:
        return strip_negations(raw.strip())

    label = "integrated_multimodal_description:"
    body = head.strip()
    if body.startswith(label):
        body = body[len(label):].strip()
    # The rebuilt field is exactly "contract [Shot 1] ..." — split there instead of
    # hunting for the contract's last sentence, which changes when allow_text edits it
    # ("no text except the on-screen timer 00:00"). The old marker check silently missed
    # and appended the context contract a second time (G01).
    tag = body.find("[Shot 1]")
    if tag > 0:
        contract, rest = body[:tag].strip(), body[tag:].strip()
    else:
        contract = ctx["style"]["prompt_contract"].strip()
        if not shot.get("red_allowed"):
            contract = contract.replace(
                "Red only for blood, infected eyes and the recording dot.", "").strip()
        rest = body
    addon = []
    if with_first:
        addon.append("Start from the supplied first-frame image as frame 0 of the target video; "
                     "keep its composition and background at the start of the shot.")
    if has_voice:
        addon.append("The narrator voice is <Audio 1>: " + ctx["voice"]["description"] + ".")
    return (strip_negations(f"{label} {contract} {' '.join(addon)} {rest}").strip()
            + "\n\noverall_soundscape:" + tail)


def to_seconds(value):
    parts = [float(p) for p in str(value).split(":")]
    return parts[0] * 60 + parts[1] if len(parts) == 2 else sum(
        v * 60 ** (len(parts) - 1 - i) for i, v in enumerate(parts))


def input_copy(path: Path, name: str) -> str:
    target = Path(folder_paths.get_input_directory()) / name
    if not target.exists():
        shutil.copy2(path, target)
    return name


# QA facts stay in global context; object/colour denials must not reach prompt text.
# Shots where keyed character sheets in the Media panel override the supplied first
# frame at t=0 (G02: 2 attempts opened on a pink sheet). For those, the plate is the
# only picture; cast identity stays in prompt_visible wardrobe text.
MEDIA_CHAR_DROP = set()  # G02 attempt 5: restore cast refs; improved feed keeps plate as ref slot 1

NEGATION_DROP = (
    "NO red anywhere in this shot; do not draw red eyes.",
    "no potted plant, no extra furniture",
    "no plant, no flowers, no second table",
    "no faces, no figures, no text",
    "No visible text, no signage, no watermark.",
    "no cake, no candles",
)


def strip_negations(text: str) -> str:
    import re
    for clause in NEGATION_DROP:
        text = text.replace(clause, "")
    return re.sub(r"\s{2,}", " ", text).replace(" ,", ",").replace(",;", ";").replace(" ;", ";").strip()


def video_frame(video: Path, at: float | None):
    """Return one RGB frame as a torch IMAGE batch [1,H,W,3] in 0..1."""
    import av
    with av.open(str(video)) as container:
        last = None
        for frame in container.decode(video=0):
            arr = frame.to_ndarray(format="rgb24")
            last = arr
            if at is not None:
                t = float(frame.pts or 0) * float(frame.time_base or 0)
                if t >= at:
                    break
        if last is None:
            raise ValueError(f"no frame decoded from {video}")
        return torch.from_numpy(last.astype(np.float32) / 255.0)[None, ...]


class FreeVideoGhe27AContext:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "shot_id": (_shots(),),
                "context_path": ("STRING", {"default": DEFAULT_CONTEXT}),
                "include_voice": ("BOOLEAN", {"default": True}),
                "include_first": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                # Legacy graphs omit all five and keep the old behaviour.
                "route": (("auto", "fresh", "fresh_audio", "continue_voice",
                           "continue_anchor", "continue_media", "continue_media_plain"),
                          {"default": "auto"}),
                "route_media": ("STRING", {"default": "[]"}),
                "route_audio": ("STRING", {"default": ""}),
                "route_continue_from": ("STRING", {"default": ""}),
                "route_anchor": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "IMAGE", "AUDIO", "STRING", "FLOAT", "INT", "INT",
                    "STRING", "BOOLEAN", "BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = ("assets", "prompt", "first_frame", "reference_audio", "report",
                    "seconds", "width", "height", "continue_from",
                    "first_frame_reference", "voice_reference", "audio_use", "route_report")
    FUNCTION = "resolve"
    CATEGORY = "Ghe27A/Context"

    def resolve(self, shot_id, context_path, include_voice, include_first,
                route="auto", route_media="[]", route_audio="",
                route_continue_from="", route_anchor=""):
        plan = route_rules().validate_route(
            route=route, media=route_media, audio=route_audio or None,
            continue_anchor=route_anchor or None,
            continue_from=route_continue_from or None,
            first_frame_reference=False)
        path, ctx, context_note = resolve_context(context_path, shot_id)
        shot = ctx["shots"][shot_id]
        scene = ctx["sets"].get(shot.get("scene"), {})
        part = part_of(str(path))
        clips = ROOT / "out" / f"part{part}-t2v"
        film = ROOT / "out" / f"part{part}.mp4"
        render = ctx.get("render") or {}
        width = int(render.get("width") or 704)
        height = int(render.get("height") or 1280)

        route_id = plan["route"]
        # auto and the media routes keep the context-built plate/cast/props. Fresh cuts
        # and continue_anchor intentionally carry no other picture conditioning.
        use_context_assets = route_id in ("auto", "continue_media", "continue_media_plain")
        assets, used = [], []
        plate = shot.get("bg") or scene.get("plate")
        if use_context_assets:
            # Picture slot 1 is the plate: <Picture 1> in the prompt must resolve to the
            # scene, otherwise H3 opens on a keyed character sheet (G02 #e41363).
            if plate and (ROOT / plate).exists():
                assets.append({"file": input_copy(ROOT / plate, f"ref_scene_{shot_id.lower()}.png"),
                               "role": "reference",
                               "cast": {"id": f"scene_{shot.get('scene')}", "setting": True}})
                used.append(shot.get("scene"))
            if shot_id not in MEDIA_CHAR_DROP:
                for cid in shot.get("characters", []):
                    ref = ctx["characters"].get(cid, {}).get("ref")
                    if ref and (ROOT / ref).exists():
                        assets.append({"file": input_copy(ROOT / ref, f"ref_{cid}_{shot_id.lower()}.png"),
                                       "role": "reference", "cast": {"id": cid}})
                        used.append(cid)
            for prop in shot.get("props", []):
                if (ROOT / prop).exists():
                    assets.append({"file": input_copy(ROOT / prop, f"ref_prop_{shot_id.lower()}_{len(used)}.png"),
                                   "role": "reference", "cast": {"id": f"prop_{shot_id.lower()}", "prop": True}})

        # --media rows reach us as {kind, path} only; stage them here. The engine
        # computes sha256/bytes from the staged file.
        for index, row in enumerate(plan["media"]):
            source = Path(row["path"])
            if not source.is_absolute():
                source = ROOT / source
            if not source.exists():
                raise ValueError(f"--media[{index}] not found: {source}")
            name = input_copy(source, f"ref_{route_id}_{shot_id.lower()}_m{index}.png")
            assets.append({"file": name, "role": "reference",
                           "cast": {"id": f"route_media_{index}"}})
            used.append(f"media{index}")

        raw = (ROOT / "prompts" / f"part{part}-rebuilt" / f"{shot_id}.txt").read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        base_has_voice = bool(include_voice and spec_shot(part, shot_id).get("dialogue")
                              and ctx["voice"].get("ref")
                              and (ROOT / ctx["voice"]["ref"]).exists())
        has_voice = base_has_voice or route_id == "fresh_audio"
        with_first = route_id not in ("fresh", "fresh_audio")
        prompt = compose_prompt(raw, ctx, scene, shot_id, shot, part, has_voice, with_first)

        first = torch.zeros((1, height, width, 3), dtype=torch.float32)
        origin = "none"
        if plan["anchor"]:
            anchor_path = Path(plan["anchor"])
            if not anchor_path.is_absolute():
                anchor_path = ROOT / anchor_path
            if not anchor_path.exists():
                raise ValueError(f"route_anchor not found: {anchor_path}")
            im = Image.open(anchor_path).convert("RGB")
            first = torch.from_numpy(np.asarray(im, dtype=np.float32) / 255.0)[None, ...]
            origin = f"route anchor {anchor_path.name}"
        elif include_first and route_id not in ("fresh", "fresh_audio"):
            chain = next((c for c in ctx["chains"] if c["id"] == shot.get("chain")), {})
            prev = shot.get("prev")
            previous = None
            if prev and chain.get("last_to_first"):
                previous = next(iter((clips / prev).glob("*.mp4")), None)
            plate = shot.get("bg") or scene.get("plate")
            if previous:
                first = video_frame(previous, None)
                origin = f"last frame of {prev}"
            elif plate and scene.get("qa_passed") and (ROOT / plate).exists():
                # flat QA-passed plate: the old film frame had vignette/gradient and
                # was the root cause of G02's painterly spotlight.
                im = Image.open(ROOT / plate).convert("RGB")
                first = torch.from_numpy(np.asarray(im, dtype=np.float32) / 255.0)[None, ...]
                origin = f"flat set plate {Path(plate).name}"
            elif film.exists():
                first = video_frame(film, to_seconds(shot["start"]) + 0.2)
                origin = f"approved out/part{part}.mp4"

        audio = {"waveform": torch.zeros((1, 1, 1024)), "sample_rate": 48000}
        audio_origin = "none"
        wav_ref = plan["audio"] or (ctx["voice"].get("ref") if has_voice else "")
        if wav_ref:
            wav_path = Path(wav_ref)
            if not wav_path.is_absolute():
                wav_path = ROOT / wav_path
            if not wav_path.exists():
                raise ValueError(f"audio reference not found: {wav_path}")
            wav = input_copy(wav_path, f"ref_voice_{shot_id.lower()}_{route_id}.wav")
            waveform, sample_rate = load_audio(str(Path(folder_paths.get_input_directory()) / wav))
            audio = {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}
            audio_origin = wav

        report = (f"shot={shot_id} part={part} scene={shot.get('scene')} chain={shot.get('chain')} "
                  f"route={route_id} refs={len(assets)} [{', '.join(used)}] first={origin} voice={audio_origin} "
                  f"continue_from={plan['continue_from'] or '-'} audio_use={plan['audio_use']} "
                  f"voice_reference={plan['voice_reference']} "
                  f"canvas={width}x{height} sec={float(shot.get('seconds') or 5.0):.1f} "
                  f"prompt={len(prompt)}c")
        if context_note:
            report += " | " + context_note
        seconds = float(shot.get("seconds") or shot.get("target_duration") or 5.0)
        return (json.dumps(assets, ensure_ascii=False), prompt, first, audio, report,
                seconds, width, height, plan["continue_from"],
                plan["first_frame_reference"], plan["voice_reference"],
                plan["audio_use"], report)


NODE_CLASS_MAPPINGS = {"FreeVideoGhe27AContext": FreeVideoGhe27AContext, "Ghe27AContext": FreeVideoGhe27AContext}
NODE_DISPLAY_NAME_MAPPINGS = {"FreeVideoGhe27AContext": "Ghe27A · Global Context"}
