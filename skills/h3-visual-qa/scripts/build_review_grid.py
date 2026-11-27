"""Build a review grid of keyframes so pass-2 eyeball checks are one image, not 25 files."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]


def font(size):
    for name in ('C:/Windows/Fonts/consola.ttf', 'C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/arial.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--frames', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--first', type=int, default=0, help='only the first N shots')
    ap.add_argument('--cols', type=int, default=5)
    ap.add_argument('--tw', type=int, default=220)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    shots = spec['shots'][:args.first] if args.first else spec['shots']
    frames = Path(args.frames) if args.frames else ROOT / 'art' / 'keys' / args.name
    out = Path(args.out) if args.out else ROOT / 'out' / 'storyboard' / f'{args.name}-grid.png'
    out.parent.mkdir(parents=True, exist_ok=True)

    canvas = spec.get('canvas') or [spec['render']['width'], spec['render']['height']]
    tw, th = args.tw, int(args.tw * canvas[1] / canvas[0])
    pad, label_h = 10, 46
    cols = args.cols
    rows = (len(shots) + cols - 1) // cols
    grid = Image.new('RGB', (cols * (tw + pad) + pad, rows * (th + label_h + pad) + pad), (16, 18, 22))
    d = ImageDraw.Draw(grid)
    f_small, f_id = font(15), font(18)

    missing = []
    for i, shot in enumerate(shots):
        sid = shot['id']
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + label_h + pad)
        key = frames / f'{sid}.png'
        d.text((x, y), sid, font=f_id, fill=(235, 235, 235))
        if key.exists():
            img = Image.open(key).convert('RGB').resize((tw, th), Image.LANCZOS)
            grid.paste(img, (x, y + 22))
        else:
            d.rectangle([x, y + 22, x + tw, y + 22 + th], outline=(120, 40, 40), width=3)
            d.text((x + 6, y + 30), 'MISSING', font=f_small, fill=(200, 80, 80))
            missing.append(sid)
        secs = shot.get('seconds', shot.get('duration', 0))
        layers = shot.get('layers') or shot.get('cast') or []
        meta = f"{shot.get('camera', '')} | {secs}s | {len(layers)} layer(s)"
        d.text((x + 2, y + 22 + th + 3), meta[:34], font=f_small, fill=(150, 165, 175))

    grid.save(out)
    print(f'grid -> {out}  ({len(shots)} shots, {cols}x{rows})')
    if missing:
        print('missing keyframes:', ', '.join(missing))

    checklist = [
        '1 vest/wardrobe on the WRONG layer (prop appearing on a body)',
        '2 sprite integrity: floating hands, halved bodies, neighbour bleed-through',
        '3 duplicated prop: background already contains it',
        '4 face consistency: eyebrows/nose/hair strands = style break',
        '5 readable at thumbnail: oversized prop, or nobody in the frame',
    ]
    print('pass-2 checklist:')
    for line in checklist:
        print('  ', line)


if __name__ == '__main__':
    main()
