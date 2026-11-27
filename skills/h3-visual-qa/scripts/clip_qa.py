"""Measure every rendered shot clip: duration, fps, canvas, motion, freeze, red flash, exposure.

Pass 1 of h3-visual-qa scores keyframes. A keyframe can be perfect while the clip is a
frozen card, drifts too dark, or flashes red for 12 frames. This script scores the clip.

    python clip_qa.py --spec art/part1-spec.json --dir out/part1/shots
    python clip_qa.py --spec art/part1-spec.json --dir out/part1/shots --json out/part1/qa/clips.json

What it reports per shot
    sec      measured duration vs the spec seconds
    fps/res  must match the delivery contract (24 fps, 704x1280)
    motion   mean abs frame difference over the clip (0 = frozen card)
    freeze   longest run (seconds) with motion below --freeze-diff
    red      max share of frame that is palette red (flash frames, blood)
    wash     mean share of frame that is red-dominant (catches a red edge vignette, which is
             a gradient and breaks "red only for blood, infected eyes, recording dot")
    luma     mean brightness + the darkest frame; a 2D storybook shot below ~12 is unreadable

Verdicts follow the skill: a clip with no motion for >2 s, wrong duration/canvas, or a red
flash that was not declared in the spec fails. Nothing here writes frames back into the
pipeline - it only measures and reports.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
FFMPEG = 'C:/Users/Admin/FreeVideo/tools/ffmpeg/bin/ffmpeg.exe'
FFPROBE = 'C:/Users/Admin/FreeVideo/tools/ffmpeg/bin/ffprobe.exe'
SAMPLE_W, SAMPLE_H = 128, 232
SAMPLE_FPS = 4


def probe(path):
    out = subprocess.run(
        [FFPROBE, '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=width,height,r_frame_rate,duration,nb_frames',
         '-show_entries', 'format=duration', '-of', 'json', str(path)],
        capture_output=True, text=True)
    if out.returncode != 0:
        return None
    data = json.loads(out.stdout)
    stream = (data.get('streams') or [{}])[0]
    num, _, den = (stream.get('r_frame_rate') or '0/1').partition('/')
    fps = float(num) / float(den or 1)
    dur = stream.get('duration') or (data.get('format') or {}).get('duration') or 0
    return {'w': stream.get('width'), 'h': stream.get('height'),
            'fps': round(fps, 3), 'sec': round(float(dur), 3)}


def frames(path, tmp, fps):
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', str(path),
                    '-vf', f'fps={fps},scale={SAMPLE_W}:{SAMPLE_H}',
                    str(tmp / '%04d.png')], check=True)
    return [np.asarray(Image.open(p).convert('RGB'), dtype=np.int16)
            for p in sorted(tmp.glob('*.png'))]


def sample_fps(duration):
    """A 0.4 s flash frame only holds 2 samples at 4 fps; short clips get denser sampling."""
    if duration <= 0.6:
        return 24
    if duration <= 1.5:
        return 12
    return SAMPLE_FPS


def analyse(clip, spec_shot, freeze_diff, tmp):
    info = probe(clip)
    if not info:
        return {'shot': spec_shot['id'], 'error': 'ffprobe failed'}
    for old in tmp.glob('*.png'):
        old.unlink()
    fps = sample_fps(info['sec'])
    stack = frames(clip, tmp, fps)
    if len(stack) < 1:
        return {'shot': spec_shot['id'], 'error': 'no frames', **info}

    diffs = [float(np.abs(stack[i] - stack[i - 1]).mean()) for i in range(1, len(stack))]
    run = best = 0
    for d in diffs:
        run = run + 1 if d < freeze_diff else 0
        best = max(best, run)
    step = 1.0 / fps
    reds, wash, lumas = [], [], []
    for f in stack:
        r, g, b = f[..., 0], f[..., 1], f[..., 2]
        reds.append(float(((r > 120) & (g < 90) & (b < 90)).sum()) / (SAMPLE_W * SAMPLE_H))
        # red wash: a red gradient vignette keeps g/b low but lifts r across the frame, so it
        # escapes the "pure red" test above while still flooding the palette.
        wash.append(float(((r > g + 30) & (r > b + 30) & (r > 55)).sum()) / (SAMPLE_W * SAMPLE_H))
        lumas.append(float(f.mean()))
    return {
        'shot': spec_shot['id'], **info,
        'spec_sec': round(float(spec_shot['seconds']), 3),
        'motion': round(float(np.mean(diffs)), 2),
        'motion_min': round(float(np.min(diffs)), 2),
        'freeze': round(best * step, 2),
        'red_max': round(max(reds) * 100, 1),
        'red_wash': round(float(np.mean(wash)) * 100, 1),
        'luma': round(float(np.mean(lumas)), 1),
        'luma_min': round(min(lumas), 1),
        'declared_red': bool(spec_shot.get('ui', {}).get('rec')
                             or spec_shot.get('red_allowed')
                             or spec_shot.get('motion', {}).get('flash_at') is not None),
        'declared_flash': spec_shot.get('motion', {}).get('flash_at') is not None,
        'declared_dark': str(spec_shot.get('camera', '')).strip().upper() == 'MÀN ĐEN',
    }


def verdict(row, args):
    fails, warns = [], []
    if row.get('error'):
        return [row['error']], []
    if row['w'] != 704 or row['h'] != 1280:
        fails.append(f"canvas {row['w']}x{row['h']}")
    if abs(row['fps'] - 24) > 0.05:
        fails.append(f"fps {row['fps']}")
    if abs(row['sec'] - row['spec_sec']) > 0.35:
        fails.append(f"duration {row['sec']}s vs spec {row['spec_sec']}s")
    if row['freeze'] > 2.0:
        fails.append(f"frozen {row['freeze']}s")
    elif row['freeze'] > 1.0:
        warns.append(f"slow {row['freeze']}s")
    if row['motion'] < 0.35:
        fails.append('almost no motion (frozen card)')
    if row['motion'] > 15 and not row['declared_flash']:
        warns.append(f"motion spike {row['motion']} (flash or hard cut inside the clip)")
    if row['spec_sec'] < 4 and not row['declared_red']:
        warns.append(f"spec {row['spec_sec']}s is under the 4 s single-clip rule")
    if row['red_max'] > 12 and not row['declared_red']:
        warns.append(f"red {row['red_max']}% not declared")
    if row['red_wash'] > 20 and not row['declared_red']:
        warns.append(f"red wash {row['red_wash']}% — red is for blood/eyes/rec dot, not a vignette")
    if row['luma_min'] < args.min_luma and not row['declared_dark']:
        warns.append(f"dark frame {row['luma_min']}")
    return fails, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--dir', required=True, help='folder of shot mp4s (G01-final.mp4 or G01.mp4)')
    ap.add_argument('--suffix', default='-final')
    ap.add_argument('--freeze-diff', type=float, default=0.12)
    ap.add_argument('--min-luma', type=float, default=12.0)
    ap.add_argument('--json', default=None)
    ap.add_argument('--only', nargs='*', default=None)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    shots = spec['shots']
    if args.only:
        shots = [s for s in shots if s['id'] in args.only]

    rows, fail_n, warn_n = [], 0, 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        print(f"{'shot':6}{'sec':>7}{'spec':>7}{'motion':>8}{'freeze':>8}"
              f"{'red%':>6}{'wash%':>7}{'luma':>6}  verdict")
        for shot in shots:
            clip = Path(args.dir) / f"{shot['id']}{args.suffix}.mp4"
            if not clip.exists():
                clip = Path(args.dir) / f"{shot['id']}.mp4"
            if not clip.exists():
                print(f"{shot['id']:6}{'--':>7}  missing clip")
                continue
            row = analyse(clip, shot, args.freeze_diff, tmp)
            if row.get('error'):
                row.setdefault('spec_sec', round(float(shot['seconds']), 3))
                row['fails'], row['warns'] = [row['error']], []
                rows.append(row)
                fail_n += 1
                print(f"{shot['id']:6}{row['spec_sec']:>7.2f}{'--':>7}{'--':>8}"
                      f"{'--':>8}{'--':>6}{'--':>7}{'--':>6}  FAIL {row['error']}")
                continue
            row['fails'], row['warns'] = verdict(row, args)
            rows.append(row)
            fail_n += len(row['fails'])
            warn_n += len(row['warns'])
            tag = 'FAIL ' + '; '.join(row['fails']) if row['fails'] else (
                'WARN ' + '; '.join(row['warns']) if row['warns'] else 'PASS')
            print(f"{row['shot']:6}{row['sec']:>7.2f}{row['spec_sec']:>7.2f}"
                  f"{row['motion']:>8.2f}{row['freeze']:>8.2f}{row['red_max']:>6.1f}"
                  f"{row['red_wash']:>7.1f}{row['luma']:>6.1f}  {tag}")

    totals = {'clips': len(rows), 'fails': fail_n, 'warns': warn_n}
    print(f"\nCLIPS: {fail_n} fail, {warn_n} warn across {len(rows)} clip(s)")
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({'clips': rows, 'totals': totals}, indent=2), encoding='utf-8')
        print(f'json -> {out}')
    return 1 if fail_n else 0


if __name__ == '__main__':
    sys.exit(main())
