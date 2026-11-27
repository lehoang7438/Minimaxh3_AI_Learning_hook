r"""Build read-only QA images for the 4-segment continue_from trial."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
FFMPEG = Path('C:/Users/Admin/FreeVideo/tools/ffmpeg/bin/ffmpeg.exe')
BASE = ROOT / 'out/chain4'
QA = BASE / 'qa'
QA.mkdir(parents=True, exist_ok=True)


def grab(video: Path, at: str, dest: Path) -> Path:
    if not dest.exists():
        subprocess.run([str(FFMPEG), '-y', '-loglevel', 'error', '-ss', at,
                        '-i', str(video), '-frames:v', '1', str(dest)], check=True)
    return dest


rows = []
for segment in range(1, 5):
    video = BASE / f'seg{segment}' / 'video.mp4'
    folder = QA / f'seg{segment}'
    folder.mkdir(parents=True, exist_ok=True)
    first = grab(video, '0.10', folder / 'first.png')
    mid = grab(video, '2.10', folder / 'mid.png')
    last = grab(video, '-0.20' if False else '4.00', folder / 'last.png') \
        if segment > 1 else grab(video, '5.00', folder / 'last.png')
    # -ss after -i is safer for exact tail; redo last with -sseof.
    subprocess.run([str(FFMPEG), '-y', '-loglevel', 'error', '-sseof', '-0.20',
                    '-i', str(video), '-frames:v', '1', str(last)], check=True)
    rows.append((segment, first, mid, last))

thumb_w, thumb_h = 240, 436
grid = Image.new('RGB', (thumb_w * 3 + 40, thumb_h * 4 + 60), (18, 20, 28))
draw = ImageDraw.Draw(grid)
for r, (segment, first, mid, last) in enumerate(rows):
    for c, (label, path) in enumerate((('first', first), ('mid', mid), ('last', last))):
        with Image.open(path) as im:
            tile = im.convert('RGB').resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x, y = 10 + c * (thumb_w + 10), 10 + r * (thumb_h + 12)
        grid.paste(tile, (x, y))
        draw.text((x + 4, y + 4), f'seg{segment} {label}', fill=(240, 235, 215))
grid_path = QA / 'review-grid.png'
grid.save(grid_path)

with Image.open(rows[0][1]) as a_im, Image.open(rows[3][1]) as b_im:
    a = np.asarray(a_im.convert('RGB')).astype(int)
    b = np.asarray(b_im.convert('RGB')).astype(int)
compare_path = QA / 'compare-seg1-seg4-first.png'
canvas = Image.new('RGB', (704 * 2 + 20, 1280 + 30), (18, 20, 28))
canvas.paste(a_im.convert('RGB'), (0, 30))
canvas.paste(b_im.convert('RGB'), (724, 30))
d = ImageDraw.Draw(canvas)
d.text((6, 8), 'seg1 first (T2V)', fill=(240, 235, 215))
d.text((730, 8), 'seg4 first (3x continue_from)', fill=(240, 235, 215))
canvas.save(compare_path)

metrics = {
    'seg1_vs_seg4_first': {
        'mae_rgb': round(float(np.mean(np.abs(a - b))), 3),
        'seg1_colors': int(len(np.unique(a.reshape(-1, 3), axis=0))),
        'seg4_colors': int(len(np.unique(b.reshape(-1, 3), axis=0))),
    },
    'grid': str(grid_path.relative_to(ROOT)),
    'compare': str(compare_path.relative_to(ROOT)),
}
(QA / 'compare.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n',
                                 encoding='utf-8')
print(json.dumps(metrics, ensure_ascii=False, indent=2))
