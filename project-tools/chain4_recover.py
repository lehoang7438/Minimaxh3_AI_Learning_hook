r"""Recover a ComfyUI job that was queued by chain4_run.py but whose driver died.

The queue lives on the server, so a killed client does NOT cancel the render. This
script waits on /history/<prompt_id>, downloads the MP4 into --outdir/<shot>/, copies
it into ComfyUI/output/<chain>/<shot>.mp4 for the next continue_from segment, and
writes the same qa.json the driver would have written.

    python art/tests/chain4_recover.py --id <prompt_id> --shot G01 \
        --outdir out/story-g01 --chain-name story-g01 --seconds 10
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chain4_run import DEFAULT_COMFY_OUTPUT, measure, newest_mp4  # noqa: E402

SERVER = 'http://127.0.0.1:8188'


def get_json(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--id', required=True, help='ComfyUI prompt_id from "queued:" line')
    ap.add_argument('--shot', required=True)
    ap.add_argument('--outdir', type=Path, default=ROOT / 'out/story-g01')
    ap.add_argument('--chain-name', default='story-g01')
    ap.add_argument('--seconds', type=float, default=10.0)
    ap.add_argument('--max-wait', type=int, default=3600)
    args = ap.parse_args()

    dest = args.outdir / args.shot
    dest.mkdir(parents=True, exist_ok=True)
    history_url = f'{SERVER}/history/{args.id}'
    deadline = time.time() + args.max_wait
    print(f'waiting for {args.id} (max {args.max_wait}s)...', flush=True)
    entry = None
    while time.time() < deadline:
        try:
            history = get_json(history_url)
        except Exception as exc:
            print(f'  history read failed: {exc}', flush=True)
            time.sleep(10)
            continue
        candidate = history.get(args.id)
        if candidate:
            status = str(candidate.get('status', {}).get('status_str', ''))
            outputs = candidate.get('outputs') or {}
            if status == 'error':
                print(json.dumps(candidate.get('status'), ensure_ascii=False, indent=2))
                raise SystemExit('job error in ComfyUI history')
            if outputs:
                entry = candidate
                break
        time.sleep(10)

    if entry is None:
        raise SystemExit(f'timeout after {args.max_wait}s; job may still be running; '
                         f'check /queue and do NOT requeue')

    files = []
    for node in (entry.get('outputs') or {}).values():
        for key in ('images', 'gifs', 'videos'):
            for item in node.get(key, []) or []:
                query = (f'filename={urllib.parse.quote(str(item.get("filename", "")))}'
                         f'&subfolder={urllib.parse.quote(str(item.get("subfolder", "")))}'
                         f'&type={urllib.parse.quote(str(item.get("type", "")))}')
                target = dest / str(item['filename'])
                with urllib.request.urlopen(f'{SERVER}/view?{query}', timeout=300) as src:
                    target.write_bytes(src.read())
                files.append(target)
                print(f'downloaded {target.name} ({target.stat().st_size / (1024 * 1024):.1f} MB)', flush=True)

    mp4s = [f for f in files if f.suffix.lower() == '.mp4']
    if not mp4s:
        mp4s = list(dest.glob('*.mp4'))
    if not mp4s:
        raise SystemExit('finished but no MP4 output found')
    video = max(mp4s, key=lambda p: p.stat().st_mtime)
    handoff = DEFAULT_COMFY_OUTPUT / args.chain_name / f'{args.shot}.mp4'
    handoff.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(video, handoff)
    print(f'handoff: {handoff}', flush=True)
    measure(video, dest / 'qa.json')
    print(f'RECOVERED {args.shot}: {video}', flush=True)


if __name__ == '__main__':
    main()
