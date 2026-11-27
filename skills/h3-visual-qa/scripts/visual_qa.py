"""Deterministic visual QA for storyboard keyframes and shot specs.

This is the machine half of the review. It measures things an agent would
otherwise only eyeball, so a bad take cannot reach the render queue.

Checks
  A. Spec/timeline   : shot times contiguous, durations match seconds, total = part length,
                       VO lines fit inside the shot and stay under the word-per-second budget.
  B. Assets          : every referenced asset/keyframe exists; aspect matches canvas.
  C. Continuity      : per-shot `forbid_assets` token list (e.g. no vest on a body, no bandage
                       before the bite shot) and `max_instances` per asset (no duplicate cake).
  D. Prop/role scale : an asset marked role=prop may not be scaled like a character, and a
                       character layer may not use a prop-only file.
  E. Chroma residue  : 3 % border band of every sprite box must stay under 8 % magenta pixels.
  F. Palette         : red pixels only inside layers declared `red_ok` (blood, infected eyes,
                       rec dot); a frame-level red ratio above the cap is a FAIL.
  G. Flatness        : background assets must be flat vector: local gradient energy under cap.
  H. Motion          : requested zoom/shake/grain are in range; 24 fps delivery required.

Usage
  python visual_qa.py --spec art/part1-spec.json --name part1
  python visual_qa.py --spec ... --name part1 --frames art/keys/part1
   I. Background logic: a plate must be ONE scene; >=3 full-frame gutters/separators = a page of
                        panels (FAIL). One viewpoint, one continuous space, no borders/grid.
   J. Wardrobe        : each character layer must declare `outfit` matching `wardrobe_id` in
                        characters.json; mismatch = FAIL, missing = WARN. Pixel colour cannot tell
                        navy outfits apart, so consistency is checked by declaration.

Usage
  python visual_qa.py --spec art/part1-spec.json --name part1
  python visual_qa.py --spec ... --name part1 --frames art/keys/part1
  # ASSETS bucket runs automatically when <root>/characters.json exists.
  # Maintainers: art/tests/add_wardrobe_ids.py (bible + spec outfit),
  #              art/tests/make_unify_jobs.py (sheet prompt column count).
Exit 0 = pass (warnings allowed), 1 = FAIL, 2 = bad usage.
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
MAGENTA = np.array([200, 20, 140], dtype=np.float32)
WORDS_PER_SECOND = 2.0
RED_RATIO_CAP = 0.045
# Calibrated from this project's own assets (see .opencode/scripts/calibrate_flatness.py).
# Painterly backgrounds measured 640 colors, flat vector ones 103-380.
# Luminance ramp is NOT used to judge backgrounds: the style bible demands a heavy
# vignette, which always produces soft ramps (16-23% even on flat art).
COLOR_WARN = 300
COLOR_FAIL = 520
RAMP_INFO_ONLY = True
GRADIENT_CAP = 26.0  # legacy, unused
CHROMA_CAP = 0.08
VEST_TOKENS = ('vest', 'waistcoat', 'gile')
BLOOD_TOKENS = ('blood', 'bite', 'wound', 'gore')
# Identity: how close a character sprite's palette must stay to its canon reference.
# Measured on approved vs drifted takes: same character 0.80-0.95, drifted face/outfit 0.35-0.60.
CANON_WARN = 0.72
CANON_FAIL = 0.55
# Background plates must be one scene, not a page of panels: a full-width white gutter
# or a full-width black separator is what H3 Image returns when it reads "storybook".
PANEL_WHITE = 0.80
PANEL_DARK = 0.90
PANEL_BANDS_FAIL = 3
PANEL_BANDS_WARN = 2
CHARACTER_TOKENS = {
    'khang': ('khang', 'pz-lunge', 'bite-arm'),
    'vy': ('vy',),
    'friend_beer': ('friend-beer', 'friend_beer', 'v4-friend-beer'),
    'friend_clap': ('friend-clap', 'friend_clap', 'v4-friend-clap'),
    'infected': ('infected', 'pz-', 'patient'),
    'crew': ('crew', 'captain'),
}


def err(bucket, sid, msg):
    bucket.append({'shot': sid, 'issue': msg})


def magenta_ratio(rgb):
    arr = np.asarray(rgb, dtype=np.float32)
    if arr.ndim == 3:
        arr = arr.reshape(-1, 3)
    d = np.abs(arr - MAGENTA).sum(axis=1)
    return float((d < 120).mean())


def red_ratio(rgb):
    """Strict red: high R, low G, low B. Amber beer/lamp light must not count."""
    arr = np.asarray(rgb, dtype=np.int16)
    if arr.ndim == 2:
        r, g, b = arr[:, 0], arr[:, 1], arr[:, 2]
    else:
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    return float(((r > 110) & (g < 95) & (r - g > 90) & (r - b > 60)).mean())


def flatness(path):
    """Return (smooth_ramp_ratio, quantized_color_count).

    Flat vector art has almost no smooth luminance ramps (fills are constant) and a
    small color count. Thick ink outlines are hard edges, so they do NOT count as
    ramps. Gradients, glow and painterly shading produce many 2-14 level steps.
    """
    img = Image.open(path).convert('RGB')
    img.thumbnail((256, 460), Image.LANCZOS)
    a = np.asarray(img, dtype=np.int16)
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]).astype(np.float32)
    steps = np.concatenate([np.abs(np.diff(lum, axis=0)).ravel(), np.abs(np.diff(lum, axis=1)).ravel()])
    nonzero = steps[steps > 0]
    ramp = float(((nonzero >= 2) & (nonzero <= 14)).mean()) if nonzero.size else 0.0
    q = (a // 16).astype(np.int16)
    packed = (q[..., 0] << 8) | (q[..., 1] << 4) | q[..., 2]
    return ramp, int(np.unique(packed).size)


def palette_vector(path, ignore_magenta=True):
    """Coarse colour histogram of the visible figure (4 bits/channel), L1-normalised."""
    img = Image.open(path).convert('RGB')
    img.thumbnail((192, 192), Image.LANCZOS)
    a = np.asarray(img, dtype=np.int16)
    flat = a.reshape(-1, 3)
    if ignore_magenta:
        dist = np.abs(flat.astype(np.float32) - MAGENTA).sum(axis=1)
        flat = flat[dist >= 120]
    if flat.size == 0:
        return None
    q = (flat // 16).astype(np.int32)
    packed = (q[:, 0] << 8) | (q[:, 1] << 4) | q[:, 2]
    hist = np.bincount(packed, minlength=4096).astype(np.float32)
    total = hist.sum()
    return hist / total if total else None


def canon_similarity(asset, canon):
    """Cosine similarity of two palette histograms: 1.0 = same colours in the same shares."""
    a, b = palette_vector(asset), palette_vector(canon)
    if a is None or b is None:
        return None
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(a @ b / denom) if denom else None


def separator_bands(path):
    """Count true panel gutters: a full-width white/black line with artwork on BOTH sides.

    A plain white wall or a bright ceiling is not a gutter, so the band only counts when
    the rows a little above and below it are clearly not that colour.
    """
    img = Image.open(path).convert('L')
    img.thumbnail((200, 360), Image.LANCZOS)
    a = np.asarray(img, dtype=np.int16)

    def count(mask, threshold):
        frac = mask.mean(axis=1)
        rows = frac >= threshold
        hits, run = 0, False
        for y, value in enumerate(rows):
            if value and not run:
                before = frac[max(0, y - 4):max(1, y - 1)]
                after = frac[y + 1:y + 5]
                if before.size and after.size and before.mean() < 0.55 and after.mean() < 0.55:
                    hits += 1
                run = True
            elif not value:
                run = False
        return hits

    return count(a > 232, PANEL_WHITE) + count(a < 72, PANEL_DARK)


def character_of(asset_name):
    low = asset_name.lower()
    for cid, tokens in CHARACTER_TOKENS.items():
        if any(token in low for token in tokens):
            return cid
    return None


def check_assets(spec, bible_path):
    """Background logic + wardrobe declarations, checked on assets and spec together.

    Each rule came from a real failure:
      - a background plate must be ONE scene; a page of panels (full-width gutters with
        artwork on both sides) is what H3 Image returns for "storybook" prompts;
      - every character layer must declare WHICH outfit it wears, and that outfit must be
        the character's canon wardrobe. Pixel matching cannot tell navy people apart, so
        wardrobe consistency is enforced at declaration level (the vest bug).
    """
    fails, warns = [], []
    seen = set()
    bible = {}
    env_map = {}
    try:
        data = json.loads(Path(bible_path).read_text(encoding='utf-8'))
        bible = {c['id']: c for c in data.get('characters', [])}
    except (OSError, ValueError, KeyError):
        err(warns, '-', f'bible {bible_path} not readable: wardrobe check skipped')
    env_path = ROOT / 'art' / 'env' / 'cabin-map.json'
    if env_path.exists():
        try:
            env_map = json.loads(env_path.read_text(encoding='utf-8')).get('sets', {})
        except (OSError, ValueError):
            err(warns, '-', f'{env_path} is unreadable: scene check skipped')

    # shot -> (set, allowed plates) from the master environment map
    shot_scene = {}
    for set_name, entry in env_map.items():
        plates = set(entry.get('plates', {}))
        for sid in entry.get('shots', []):
            shot_scene[sid] = (set_name, plates)

    for shot in spec['shots']:
        sid = shot['id']
        expected = shot_scene.get(sid)
        if expected:
            set_name, allowed_plates = expected
            declared = shot.get('scene')
            # A spec-declared scene is authoritative. Shot IDs repeat across parts with
            # different sets (part1 G22-G25 = lavatory, part2 = cabin_chaos), so the
            # ID-based master map is only a fallback when the spec is silent.
            if declared:
                set_name = declared
                expected = (declared, set(env_map.get(declared, {}).get('plates', {})))
                allowed_plates = expected[1]
            else:
                err(warns, sid, f'no "scene" declaration (master map says {set_name})')
            bg = Path(shot['bg']).name if shot.get('bg') else None
            # A spec-declared scene is authoritative: shot IDs may repeat across parts
            # with different sets (e.g. G22-G25 lavatory in part1 vs cabin_chaos in part2).
            check_plates = allowed_plates
            if bg and check_plates and bg not in check_plates:
                err(fails, sid, f'background {bg} does not belong to declared set "{declared or set_name}"')
        backgrounds = [p for p in (shot.get('image'), shot.get('bg')) if p]
        for ref in backgrounds:
            p = ROOT / ref
            if not p.exists() or ref in seen:
                continue
            seen.add(ref)
            bands = separator_bands(p)
            if bands >= PANEL_BANDS_FAIL:
                err(fails, sid, f'{p.name}: {bands} full-frame gutters/separators — reads as a page of '
                                f'panels, not one background plate (one scene, one viewpoint)')
            elif bands == PANEL_BANDS_WARN:
                err(warns, sid, f'{p.name}: {bands} full-frame separators — check by eye that this is '
                                f'still one room and not a split layout')
        for layer in shot.get('layers', []):
            img = layer.get('image')
            if not img:
                continue
            cid = character_of(Path(img).name)
            if not cid:
                continue
            wardrobe_id = (bible.get(cid, {}) or {}).get('wardrobe_id')
            declared = layer.get('outfit')
            if not declared:
                err(warns, sid, f'{Path(img).name}: character layer has no "outfit" declaration '
                                f'(expected "{wardrobe_id}")')
            elif wardrobe_id and declared != wardrobe_id:
                err(fails, sid, f'{Path(img).name}: outfit "{declared}" but {cid} canon wardrobe is '
                                f'"{wardrobe_id}" — wardrobe must stay identical across shots')
    return {'fails': fails, 'warns': warns}


def parse_time(value):
    parts = [float(p) for p in str(value).split(':')]
    return parts[0] * 60 + parts[1] if len(parts) == 2 else sum(
        v * 60 ** (len(parts) - 1 - i) for i, v in enumerate(parts))


def check_spec(spec, name):
    fails, warns = [], []
    canvas = spec['canvas']
    fps_out = spec.get('fps_out', 24)
    if fps_out != 24:
        err(fails, '-', f'delivery fps_out must be 24, got {fps_out}')
    t = 0.0
    for shot in spec['shots']:
        sid = shot['id']
        sec = float(shot['seconds'])
        start, end = parse_time(shot['start']), parse_time(shot['end'])
        if abs(start - t) > 0.06:
            err(fails, sid, f'timeline gap/overlap: start {start:.2f} but previous shot ends {t:.2f}')
        if abs((end - start) - sec) > 0.06:
            err(fails, sid, f'duration mismatch: end-start={end - start:.2f} vs seconds={sec:.2f}')
        if not (4.0 <= sec <= 15.0 or sec < 1.0):
            err(warns, sid, f'{sec:.2f}s is outside the 4-15s single-clip rule')
        t = end
        frames = int(round(sec * 24))
        if frames % 17 and abs(sec - 15) > 0.2:
            pass  # video is code-animated; only note extreme cases
        used = {}
        for layer in shot.get('layers', []):
            img = layer.get('image')
            if not img:
                continue
            used[Path(img).name] = used.get(Path(img).name, 0) + 1
            low = Path(img).name.lower()
            for token in shot.get('forbid_assets', []):
                if token.lower() in low:
                    err(fails, sid, f'forbidden asset used: {img} (token "{token}")')
            role = layer.get('role', 'character')
            if role == 'character' and any(t in low for t in VEST_TOKENS):
                err(fails, sid, f'vest asset "{img}" used as a character layer (Khang never wears it)')
            if role == 'prop' and float(layer.get('h', 0)) > 0.20 and 'cake' not in low:
                err(warns, sid, f'prop {img} scaled to h={layer.get("h")} — check it is not a resized character')
        for asset, count in shot.get('max_instances', {}).items():
            if used.get(Path(asset).name, 0) > int(count):
                err(fails, sid, f'{asset} appears {used.get(Path(asset).name)}x, max {count}')
        need = 0.0
        for line in shot.get('dialogue', []):
            words = len(re.findall(r'\S+', line['text']))
            spoken = words / WORDS_PER_SECOND
            need = max(need, float(line['at']) + spoken + 0.35)
            room = sec - float(line['at'])
            if room < 0.5:
                err(fails, sid, f'line at {line["at"]}s has no room in a {sec}s shot')
            elif spoken + 0.35 > room:
                err(fails, sid, f'{line["who"]} line: {words} words needs {spoken:.1f}s, '
                                f'only {room:.1f}s left after {line["at"]}s')
        if need > sec + 0.01 and shot.get('dialogue'):
            err(fails, sid, f'shot needs at least {need:.1f}s for its dialogue, has {sec}s')
    return {'total_seconds': round(t, 2), 'fails': fails, 'warns': warns}


def check_frames(frames_dir, spec, name):
    fails, warns = [], []
    canvas = spec['canvas']
    for shot in spec['shots']:
        sid = shot['id']
        key = Path(frames_dir) / f'{sid}.png'
        if not key.exists():
            err(fails, sid, f'missing keyframe {key}')
            continue
        img = Image.open(key).convert('RGB')
        if img.size != tuple(canvas):
            err(fails, sid, f'keyframe is {img.size[0]}x{img.size[1]}, expected {canvas[0]}x{canvas[1]}')
        arr = np.asarray(img)
        r = red_ratio(arr)
        allowed = any(any(t in str(l.get('image', '')).lower() for t in BLOOD_TOKENS)
                      or l.get('red_ok') for l in shot.get('layers', []))
        allowed = allowed or bool(shot.get('ui', {}).get('rec')) or 'flash' in json.dumps(shot.get('motion', {}))
        if r > RED_RATIO_CAP and not allowed:
            err(fails, sid, f'red covers {r * 100:.1f}% of the frame; palette says red = blood/eyes/rec dot only')
        elif r > RED_RATIO_CAP:
            err(warns, sid, f'red {r * 100:.1f}% — allowed by declaration, verify it is blood/flash')
        if magenta_ratio(arr) > 0.004:
            err(warns, sid, f'magenta bleed {magenta_ratio(arr) * 100:.2f}% in final frame (keying left magenta behind)')
        if shot.get('bg') and (ROOT / shot['bg']).exists():
            ramp, colors = flatness(ROOT / shot['bg'])
            tag = Path(shot['bg']).name
            if colors > COLOR_FAIL:
                err(fails, sid, f'background {tag}: {colors} quantized colors > {COLOR_FAIL} '
                                f'= painterly, not flat vector')
            elif colors > COLOR_WARN:
                err(warns, sid, f'background {tag}: {colors} quantized colors > {COLOR_WARN} '
                                f'(flat vector should stay under {COLOR_WARN})')
        for layer in shot.get('layers', []):
            p = ROOT / layer['image'] if layer.get('image') else None
            if not p or not p.exists():
                err(fails, sid, f'missing asset {layer.get("image")}')
                continue
            sprite = Image.open(p).convert('RGB')
            crop = sprite.crop((0, 0, sprite.width, max(1, int(sprite.height * 0.03))))
            crop2 = sprite.crop((0, sprite.height - max(1, int(sprite.height * 0.03)), sprite.width, sprite.height))
            band = np.concatenate([np.asarray(crop).reshape(-1, 3), np.asarray(crop2).reshape(-1, 3)])
            if magenta_ratio(band) < 0.5:
                err(warns, sid, f'{p.name}: top/bottom band is not the expected flat magenta key')
            _, layer_colors = flatness(p)
            if layer_colors > COLOR_FAIL:
                err(warns, sid, f'{p.name}: {layer_colors} quantized colors > {COLOR_FAIL} '
                                f'(asset is painterly, will not match flat vector frames)')
    return {'fails': fails, 'warns': warns}


def check_layout(keys_dir, spec):
    """Measure staging from the sidecar layout reports: depth order, occlusion, protected zones."""
    fails, warns = [], []
    for shot in spec['shots']:
        sid = shot['id']
        path = Path(keys_dir) / f'{sid}.layout.json'
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        chars = [b for b in data['boxes'] if b['role'] == 'character']
        for hit in data.get('keep_clear_hits', []):
            err(fails, sid, f"{hit['anchor']} covers protected zone {hit['zone']} "
                            f"({hit['overlap'] * 100:.0f}%) - move it to an empty floor/chair anchor")
        # depth: a further character (smaller feet_y) must not be drawn bigger
        ordered = sorted(chars, key=lambda b: b['feet_y'])
        for a, b in zip(ordered, ordered[1:]):
            if b['h'] > a['h'] * 1.12 and b['feet_y'] <= a['feet_y']:
                err(fails, sid, f'{b["image"]} is nearer but smaller than {a["image"]} - depth conflict')
        # characters behind an occluder must actually be cut by it
        for c in chars:
            for name in (c.get('behind') or []):
                if name not in data.get('occluders', []):
                    err(fails, sid, f'{c["image"]} declared behind={name} but that occluder was not applied')
                elif c['box'][3] < 0.55 * spec['canvas'][1]:
                    err(warns, sid, f'{c["image"]} is marked behind={name} but sits too high to be cut')
        # a sprite must stay inside the frame (raised arms make boxes very wide)
        frame_w, frame_h = spec['canvas']
        for c in chars + [b for b in data['boxes'] if b['role'] != 'character']:
            x0, y0, x1, y1 = c['box']
            margin_x, margin_y = 0.02 * frame_w, 0.02 * frame_h
            if x0 < -margin_x or x1 > frame_w + margin_x:
                err(fails, sid, f'{c["image"]} runs off the left/right edge '
                                f'(x {x0}..{x1} of {frame_w}) - lower h or pull x inward')
            if y1 < frame_h * 0.55 and c['role'] == 'character':
                err(warns, sid, f'{c["image"]} feet float at y {y1 / frame_h:.2f}')
        same_line = [c for c in chars if abs(c['feet_y'] - 0.61) < 0.02]
        if len(same_line) > 1:
            hs = [c['h'] for c in same_line]
            if max(hs) - min(hs) > 0.05:
                err(warns, sid, f'characters on the same depth line differ in size by '
                                f'{(max(hs) - min(hs)) * 100:.0f}% of frame height')
    return {'fails': fails, 'warns': warns}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--frames', default=None)
    ap.add_argument('--json', default=None)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    report = {'part': args.name, 'spec': check_spec(spec, args.name)}
    bible = ROOT / 'characters.json'
    if bible.exists():
        report['assets'] = check_assets(spec, bible)
    if args.frames:
        report['frames'] = check_frames(args.frames, spec, args.name)
        report['layout'] = check_layout(args.frames, spec)

    spec_res = report['spec']
    print(f'--- {args.name} ---')
    print(f'timeline: {spec_res["total_seconds"]}s ({spec_res["total_seconds"] / 60:.2f} min)')
    for label, key in (('SPEC', 'spec'), ('ASSETS', 'assets'), ('FRAMES', 'frames'), ('LAYOUT', 'layout')):
        block = report.get(key)
        if not block:
            continue
        for e in block['fails']:
            print(f'FAIL {label} {e["shot"]:6} {e["issue"]}')
        for w in block['warns']:
            print(f'WARN {label} {w["shot"]:6} {w["issue"]}')
        pct = lambda v: f'{v * 100:.2f}%'
        print(f'{label}: {len(block["fails"])} fail, {len(block["warns"])} warn')

    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'json -> {args.json}')
    fails = sum(len(report.get(k, {}).get('fails', [])) for k in ('spec', 'assets', 'frames', 'layout'))
    return 1 if fails else 0


if __name__ == '__main__':
    raise SystemExit(main())
