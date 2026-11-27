"""One image per part: start / middle / end frame of every rendered clip, side by side.

Keyframe grids answer "is the picture right". This answers "does it move": three frames of
the same clip show whether a sprite actually changes pose or the whole shot is a slow zoom
over a static card.

    python motion_grid.py --spec art/part1-spec.json --dir out/part1/shots --name part1
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
FFMPEG = 'C:/Users/Admin/FreeVideo/tools/ffmpeg/bin/ffmpeg.exe'


def font(size):
    for name in ('C:/Windows/Fonts/consola.ttf', 'C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/arial.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def grab(clip, t, size, out):
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-ss', f'{t:.3f}', '-i', str(clip),
                    '-frames:v', '1', '-vf', f'scale={size[0]}:{size[1]}', str(out)],
                   check=False)
    return out.exists()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--dir', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--suffix', default='-final')
    ap.add_argument('--out', default=None)
    ap.add_argument('--per-row', type=int, default=5)
    ap.add_argument('--tw', type=int, default=118)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    shots = spec['shots']
    tw = args.tw
    th = int(tw * spec['canvas'][1] / spec['canvas'][0])
    pad, label_h = 4, 26
    per_row = args.per_row
    rows = (len(shots) + per_row - 1) // per_row
    width = per_row * (3 * tw + 3 * pad) + pad
    height = rows * (th + label_h + pad) + pad
    grid = Image.new('RGB', (width, height), (14, 16, 20))
    draw = ImageDraw.Draw(grid)
    label = font(15)
    missing = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for i, shot in enumerate(shots):
            clip = Path(args.dir) / f"{shot['id']}{args.suffix}.mp4"
            if not clip.exists():
                clip = Path(args.dir) / f"{shot['id']}.mp4"
            x0 = pad + (i % per_row) * (3 * tw + 3 * pad)
            y0 = pad + (i // per_row) * (th + label_h + pad)
            draw.text((x0, y0), f"{shot['id']} {shot['seconds']}s {str(shot.get('camera', ''))[:12]}",
                      font=label, fill=(230, 230, 230))
            if not clip.exists():
                missing.append(shot['id'])
                continue
            duration = float(shot['seconds'])
            times = (0.12, duration * 0.5, max(0.2, duration - 0.15))
            for j, t in enumerate(times):
                out = tmp / f"{shot['id']}_{j}.png"
                if grab(clip, t, (tw, th), out):
                    grid.paste(Image.open(out).convert('RGB'), (x0 + j * (tw + pad), y0 + 20))

    out = Path(args.out) if args.out else ROOT / 'out' / 'storyboard' / f'{args.name}-motion.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    grid.save(out)
    print(f'motion grid -> {out}  ({len(shots)} shots, start/mid/end)')
    if missing:
        print('missing clips:', ', '.join(missing))


if __name__ == '__main__':
    main()
