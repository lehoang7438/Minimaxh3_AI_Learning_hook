"""Single source of truth for the six H3 MiniMax routes.

Both the ComfyUI node `FreeVideoGhe27AContext` and the GPU-free validator import
this file. It is pure: no files are staged, no GPU is touched, and no sha256/bytes
is ever written -- scripts hand over only {kind, path} rows.
"""
from __future__ import annotations

import json
from pathlib import Path

ROUTES = (
    "auto",
    "fresh",
    "fresh_audio",
    "continue_voice",
    "continue_anchor",
    "continue_media",
    "continue_media_plain",
)
CONTINUE_ROUTES = frozenset(r for r in ROUTES if r.startswith("continue"))
PICTURES_MAX = 3  # continuation.PICTURES_MAX on build 2026.11.25.61107
DEFAULT_VOICE = "art/env/voice-narrator.wav"


def route_fail(message: str) -> None:
    raise ValueError(f"route validation failed: {message}")


def normalize_media(media) -> list[dict]:
    """Accept a JSON string / list of image paths / {kind, path} rows."""
    if media is None or media == "":
        return []
    if isinstance(media, (str, Path)):
        text = str(media).strip()
        if not text:
            return []
        try:
            media = json.loads(text)
        except json.JSONDecodeError:
            media = [media]
    if not isinstance(media, (list, tuple)):
        route_fail("--media must be a JSON array, a path, or a list of paths")
    rows = []
    for index, item in enumerate(media):
        if isinstance(item, (str, Path)):
            item = {"kind": "image", "path": str(item)}
        if not isinstance(item, dict):
            route_fail(f"--media[{index}] must be a path or a {{kind, path}} row")
        if set(item) != {"kind", "path"}:
            route_fail(
                f"--media[{index}] may only contain keys kind and path, got {sorted(item)}"
            )
        if item["kind"] != "image":
            route_fail(f"--media[{index}].kind must be 'image', got {item['kind']!r}")
        rows.append({"kind": "image", "path": str(item["path"])})
    if len(rows) > PICTURES_MAX:
        route_fail(f"{len(rows)} images supplied; maximum is {PICTURES_MAX}")
    return rows


def validate_route(*, route: str = "auto", media=None, audio=None,
                   continue_anchor=None, continue_from=None,
                   first_frame_reference: bool = False) -> dict:
    """Resolve and validate a route before any file or graph mutation.

    Returns a plan consumed by the ComfyUI context node and by the validator:
    route, media rows, audio path, anchor, continue target, and the four flags
    wired into FreeVideoGenerate.
    """
    if route not in ROUTES:
        route_fail(f"unknown route {route!r}; choose one of {', '.join(ROUTES)}")
    rows = normalize_media(media)
    anchor = str(continue_anchor) if continue_anchor else ""
    audio_path = str(audio) if audio else ""
    target = str(continue_from) if continue_from else ""
    continuing = route in CONTINUE_ROUTES

    if anchor and rows:
        route_fail("--continue-anchor conflicts with --media (anchor_media refuses other media conditioning)")
    if audio_path and continuing:
        route_fail("--audio conflicts with continue_from (use the continuing clip's voice instead)")
    if anchor and not target:
        route_fail("--continue-anchor requires a continue target")
    if continuing and not target:
        route_fail(f"route {route!r} requires --continue-from / route_continue_from")
    if not continuing and target:
        route_fail(f"route {route!r} is a fresh cut; it cannot take --continue-from")
    if anchor and first_frame_reference:
        route_fail("choose first_frame_reference or continue_anchor, not both")
    if route == "auto" and (rows or audio_path or anchor or target):
        route_fail("legacy auto route cannot take route inputs; pass an explicit --route")
    if route == "continue_anchor" and len(rows) == 0 and not anchor:
        route_fail("continue_anchor needs route_anchor")
    if route in ("continue_media", "continue_media_plain") and not rows:
        route_fail(f"route {route!r} needs 1..{PICTURES_MAX} images in --media")
    if route == "fresh_audio" and not audio_path:
        audio_path = DEFAULT_VOICE
    if route not in ("auto", "fresh_audio") and audio_path and not continuing:
        route_fail("use --route fresh_audio for an external audio reference")

    return {
        "route": route,
        "media": rows,
        "audio": audio_path,
        "anchor": anchor,
        "continue_from": target,
        "first_frame_reference": bool(first_frame_reference) if route == "auto" else False,
        "voice_reference": route == "continue_voice",
        "audio_use": "reference",
        "continuing": continuing,
    }
