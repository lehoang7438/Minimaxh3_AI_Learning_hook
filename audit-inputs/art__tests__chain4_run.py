r"""Run the universal one-workflow H3 chain loop.

The ComfyUI graph itself cannot loop; this driver does. It reuses ONE API-format
workflow file, rewriting only node 2 inputs.continue_from / seed / seconds before
each queue, then copies the downloaded MP4 into ComfyUI/output/<chain>/ so the next
iteration can continue from it. A hard cut starts a fresh T2V segment; only a
continuous action sets continue_from. No frame is edited or quantized by hand.

    python art/tests/chain4_run.py --shots 4
    python art/tests/chain4_run.py --shot-ids G01,G02,G03,G05 --seconds 10 \
        --chain-name story-g01 --outdir out/story-g01 --prompts prompts/part1-rebuilt

Seed rule (E319): --seed-base is OFFSET BY THE SEGMENT NUMBER, so segment 2 with
base 20264401 renders with seed 20264403, not 20264402. Use --seed for a single
approved retry: it is the EXACT seed sent to FreeVideoGenerate and no longer
depends on --start/--shots. Long jobs must be launched with a shell timeout of
at least 7200000 ms; a 120 s timeout SIGTERMs the driver while the GPU job lives
on and forces an ad-hoc /history recovery (E244/E319).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FFMPEG = Path('C:/Users/Admin/FreeVideo/tools/ffmpeg/bin/ffmpeg.exe')
FFPROBE = Path('C:/Users/Admin/FreeVideo/tools/ffmpeg/bin/ffprobe.exe')
DOCTOR = ROOT / '.opencode/skills/freevideo-runner/scripts/fv.ps1'
PREFLIGHT = ROOT / 'art/comfy/scripts/preflight_workflow.py'
QUEUE = ROOT / '.opencode/skills/comfyui-runner/scripts/queue_prompt.ps1'
DEFAULT_WORKFLOW = ROOT / 'art/comfy/chain4/h3-chain4.json'
DEFAULT_PROMPTS = ROOT / 'art/comfy/prompts/chain4'
DEFAULT_COMFY_OUTPUT = Path('C:/Users/Admin/FreeVideo/ComfyUI/output')
COMFY_INPUT = Path('C:/Users/Admin/FreeVideo/ComfyUI/input')


def ps(script: Path, *args: str) -> list[str]:
    return ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
            str(script), *[str(a) for a in args]]


def doctor() -> None:
    result = subprocess.run(ps(DOCTOR, 'doctor'), cwd=ROOT, text=True,
                            encoding='utf-8', errors='replace', capture_output=True)
    print(result.stdout, end='')
    if result.returncode != 0 or 'GO' not in result.stdout:
        raise SystemExit('doctor did not return GO; nothing queued')


def load_workflow(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def set_shot(path: Path, previous: Path | None, seed: int, seconds: float,
             ref_asset: Path | None = None) -> None:
    wf = load_workflow(path)
    node = wf['2']['inputs']
    node['continue_from'] = '' if previous is None else str(previous)
    node['seed'] = seed
    node['seconds'] = float(seconds)
    # One shared workflow: the picture slot changes at queue time only. Omitting
    # --ref-asset resets it, so later cut shots cannot inherit the G01 prop.
    media = wf['1']['inputs']
    if ref_asset is None:
        media['assets'] = '[]'
    else:
        COMFY_INPUT.mkdir(parents=True, exist_ok=True)
        name = f'ref_chain4_{ref_asset.stem}.png'
        shutil.copy2(ref_asset, COMFY_INPUT / name)
        media['assets'] = json.dumps([{'file': name, 'role': 'reference'}],
                                     ensure_ascii=False)
    path.write_text(json.dumps(wf, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    target = node['continue_from'] or '(T2V seed)'
    print(f'workflow set: continue_from={target}  seed={seed}  seconds={seconds}  '
          f'refs={media["assets"]}', flush=True)


def preflight(path: Path) -> None:
    result = subprocess.run([sys.executable, str(PREFLIGHT), str(path)], cwd=ROOT,
                            text=True, encoding='utf-8', errors='replace', capture_output=True)
    print(result.stdout, end='')
    if result.returncode != 0:
        raise SystemExit('preflight_workflow failed; nothing queued')


def newest_mp4(folder: Path) -> Path:
    files = [p for p in folder.glob('*.mp4') if p.is_file()]
    if not files:
        raise SystemExit(f'no mp4 downloaded into {folder}')
    return max(files, key=lambda p: p.stat().st_mtime)


def measure(video: Path, qa_path: Path) -> None:
    probe = subprocess.run(
        [str(FFPROBE), '-v', 'error', '-show_entries',
         'format=duration:stream=width,height,r_frame_rate', '-of', 'json', str(video)],
        cwd=ROOT, text=True, encoding='utf-8', errors='replace', capture_output=True, check=True)
    info = json.loads(probe.stdout or '{}')
    stream = next((s for s in info.get('streams', []) if s.get('width')), {})
    duration = float(info.get('format', {}).get('duration', 0) or 0)
    fps = stream.get('r_frame_rate', '')
    try:
        num, den = (int(x) for x in fps.split('/'))
        fps_value = round(num / den, 3)
    except Exception:
        fps_value = None
    frame = qa_path.parent / 'last.png'
    subprocess.run([str(FFMPEG), '-y', '-loglevel', 'error', '-sseof', '-0.2',
                    '-i', str(video), '-frames:v', '1', str(frame)], cwd=ROOT, check=True)
    from PIL import Image
    import numpy as np
    with Image.open(frame) as image:
        rgb = np.asarray(image.convert('RGB'))
    colors = int(len(np.unique(rgb.reshape(-1, 3), axis=0)))
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    red_pct = round(float(np.mean((r > 110) & (g < 80) & (b < 80)) * 100), 3)
    result = {
        'video': str(video.relative_to(ROOT)) if video.is_relative_to(ROOT) else str(video),
        'duration': round(duration, 3),
        'canvas': [stream.get('width'), stream.get('height')],
        'fps': fps_value,
        'last_frame_colors': colors,
        'last_frame_red_pct': red_pct,
        'verdict': 'MEASURED',
        'visual_review': 'pending',
    }
    qa_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('QA ' + json.dumps(result, ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--shots', type=int, default=4)
    parser.add_argument('--start', type=int, default=1, help='segment number to render')
    parser.add_argument('--workflow', type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument('--prompts', type=Path, default=DEFAULT_PROMPTS)
    parser.add_argument('--outdir', type=Path, default=ROOT / 'out/chain4')
    parser.add_argument('--comfy-output', type=Path, default=DEFAULT_COMFY_OUTPUT)
    parser.add_argument('--seed-base', type=int, default=20262210,
                        help='offset by segment number; prefer --seed for one approved retry')
    parser.add_argument('--seed', type=int, default=None,
                        help='EXACT seed for a single-shot retry; overrides --seed-base entirely')
    parser.add_argument('--shot-ids', default='',
                        help='comma list, e.g. G01,G02,G03,G05; default seg1..segN')
    parser.add_argument('--seconds', type=float, default=5.0,
                        help='seconds written into FreeVideoGenerate per segment')
    parser.add_argument('--chain-name', default='chain4',
                        help='subfolder under ComfyUI/output holding handoff MP4s')
    parser.add_argument('--ref-asset', type=Path, default=None,
                        help='one QA-passed picture reference for <Picture 1>; resets to [] when omitted')
    args = parser.parse_args()
    segments_to_run = args.shots - args.start + 1
    if segments_to_run < 1:
        raise SystemExit('--start is past --shots; nothing to render')
    if args.seed is not None and segments_to_run != 1:
        raise SystemExit('--seed is exact and only valid when ONE segment is rendered; '
                         'use --seed-base for multi-segment chains')
    if args.ref_asset is not None and not args.ref_asset.is_file():
        raise SystemExit(f'ref asset not found: {args.ref_asset}')

    ids = [x.strip() for x in args.shot_ids.split(',') if x.strip()] if args.shot_ids else []
    if ids and len(ids) < args.shots:
        raise SystemExit(f'--shot-ids has {len(ids)} entries but --shots is {args.shots}')
    if not args.workflow.is_file():
        raise SystemExit(f'workflow not found: {args.workflow}')
    comfy_chain = args.comfy_output / args.chain_name
    comfy_chain.mkdir(parents=True, exist_ok=True)
    args.outdir.mkdir(parents=True, exist_ok=True)

    for segment in range(args.start, args.shots + 1):
        sid = ids[segment - 1] if ids else f'seg{segment}'
        prev_sid = ids[segment - 2] if ids and segment > 1 else f'seg{segment - 1}'
        prompt = args.prompts / f'{sid}.txt'
        if not prompt.is_file():
            raise SystemExit(f'prompt not found: {prompt}')
        previous = comfy_chain / f'{prev_sid}.mp4' if segment > 1 else None
        if previous and not previous.is_file():
            raise SystemExit(f'previous clip not found: {previous}')
        print(f'\n===== {sid} ({segment}/{args.shots}) =====', flush=True)
        seed = args.seed if args.seed is not None else args.seed_base + segment
        set_shot(args.workflow, previous, seed, args.seconds, args.ref_asset)
        doctor()
        preflight(args.workflow)
        dest = args.outdir / sid
        dest.mkdir(parents=True, exist_ok=True)
        subprocess.run(ps(QUEUE, '-Workflow', args.workflow, '-PromptFile', prompt,
                          '-OutDir', dest, '-TimeoutSec', '5400'), cwd=ROOT, check=True)
        video = newest_mp4(dest)
        shutil.copy2(video, comfy_chain / f'{sid}.mp4')
        measure(video, dest / 'qa.json')
        print(f'{sid} saved: {video}', flush=True)
    print(f'\nDONE: {args.shots} segments; one workflow reused: {args.workflow.relative_to(ROOT)}', flush=True)


if __name__ == '__main__':
    main()
