"""Read-only decision report for H3 cuts inside a chain.

Rule (user decision 27/11/2026): shot N continues from N-1 with --continue-from
and an H3 cut **only** when the scene conditions are compatible. A jump in
environment or lighting tier must stay fresh.

Usage:
    python art/tests/smart_chain.py            # full report vs plan.json
    python art/tests/smart_chain.py G05 G09    # explain specific shots

The script never edits the plan, prompts or clips.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CTX = ROOT / 'art/env/global-context.json'
PLAN = ROOT / 'art/t2v/plan.json'


def light_tier(shot: dict) -> str:
    mood = (shot.get('mood') or '').lower()
    if shot.get('set') == 'flashback_warm' or 'warm memory' in mood:
        return 'warm_flashback'
    if 'unprotective' in mood:
        return 'unprotective_night'
    if 'morning' in mood:
        return 'cold_morning'
    if 'night' in mood or 'dread' in mood:
        return 'cold_night'
    return 'other:' + mood[:24]


def is_ui_black(shot: dict) -> bool:
    return 'MÀN ĐEN' in (shot.get('camera') or '')


def decide(shots: list[dict], plans: dict) -> list[dict]:
    decisions = []
    for index, shot in enumerate(shots):
        sid = shot['id']
        if index == 0:
            decisions.append({'shot': sid, 'mode': 'fresh', 'why': 'first shot of chain'})
            continue
        prev = shots[index - 1]
        blockers = []
        if plans[sid]['chain'] != plans[prev['id']]['chain']:
            blockers.append('crosses chain boundary')
        if shot.get('set') != prev.get('set'):
            blockers.append('set %s -> %s' % (prev.get('set'), shot.get('set')))
        if light_tier(shot) != light_tier(prev):
            blockers.append('light %s -> %s' % (light_tier(prev), light_tier(shot)))
        if is_ui_black(shot) or is_ui_black(prev):
            blockers.append('UI black-screen boundary')
        if blockers:
            decisions.append({'shot': sid, 'mode': 'fresh', 'why': '; '.join(blockers)})
        else:
            decisions.append({'shot': sid, 'mode': 'continue_from', 'source': prev['id'],
                              'why': 'same chain/set/light tier %s; H3 cuts inside clip' % light_tier(shot)})
    return decisions


def main() -> int:
    ctx = json.loads(CTX.read_text(encoding='utf-8'))
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    plans = {r['shot']: r for r in plan['shots']}
    decisions = decide(ctx['shots'], plans)
    wanted = set(a.upper() for a in sys.argv[1:])

    if wanted:
        for row in decisions:
            if row['shot'] in wanted:
                current = plans[row['shot']]
                print(row['shot'], 'rule=', row['mode'], 'plan=', current['mode'], '|', row['why'])
        return 0

    upgrades = [r for r in decisions if r['mode'] == 'continue_from' and plans[r['shot']]['mode'] != 'continue_from']
    downgrades = [r for r in decisions if r['mode'] == 'fresh' and plans[r['shot']]['mode'] == 'continue_from']
    print('UPGRADE (plan fresh -> rule continue):')
    for r in upgrades:
        print(' ', r['shot'], '<-', r['source'], '|', r['why'])
    print('DOWNGRADE (plan continue -> rule fresh):')
    for r in downgrades:
        print(' ', r['shot'], '|', r['why'])
    print('KEEP continue:', sum(1 for r in decisions if r['mode'] == 'continue_from' and plans[r['shot']]['mode'] == 'continue_from'))
    print('RULE continue total:', sum(1 for r in decisions if r['mode'] == 'continue_from'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
