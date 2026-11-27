"""ALH curator - the review half of the Automatic Learning Hook (v3).

The runtime hook (learn_hook.ps1) only APPENDS events. This tool is the part that makes the
log usable, so a lesson can move proposed -> accepted/revoked instead of piling up:

    python art/comfy/ALH/alh.py migrate          # one-off: v1 log -> v2 (ids, skill, status)
    python art/comfy/ALH/alh.py upgrade          # v2 -> v3 fields (rule/supersedes/audit)
    python art/comfy/ALH/alh.py report           # what needs review, what contradicts what
    python art/comfy/ALH/alh.py sync             # rewrite LEARNINGS.md + RUN-LOG.md from the log
    python art/comfy/ALH/alh.py set E096 accepted
    python art/comfy/ALH/alh.py edit E234 --skill global --rule '...'
    python art/comfy/ALH/alh.py verify           # LEARNINGS vs log drift, both directions

v3 (27/11):
  - v2 is the ONLY source of truth; learning_system/alh_core.py no longer promotes;
  - LEARNINGS.md renders one active `rule` per accepted event, not a 400-char story;
    verdicts and run records live in RUN-LOG.md, evidence stays in learning-log.jsonl;
  - status changes are audited (status_by/status_ts) and can name superseded ids;
  - save is atomic and locked; verify checks both directions plus the `skill` field.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

try:  # Windows
    import msvcrt
except ImportError:  # pragma: no cover
    msvcrt = None
try:  # POSIX
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

ROOT = Path(__file__).resolve().parents[3]
ALH = ROOT / "art" / "comfy" / "ALH"
LOG = ALH / "learning-log.jsonl"
LOCK = ALH / ".lock"
SKILLS = ROOT / ".opencode" / "skills"
REPORT = ALH / "REPORT.md"
RUN_LOG = ALH / "RUN-LOG.md"
GLOBAL_RULES = ALH / "GLOBAL-RULES.md"
GLOBAL_SKILL = "global"

STATUSES = ("proposed", "accepted", "revoked", "archived")
RUN_EVENTS = {"verdict"}  # accepted verdicts are records, not rules, unless given an explicit rule
PARTS = ("", "all", "part1", "part2", "part3")
STATUS_LABEL = {
    "accepted": "Accepted (applied and verified - read as a rule)",
    "proposed": "Proposed (needs review, not a rule yet)",
    "revoked": "Revoked (do NOT apply - kept for history)",
}
AUTO_HEAD = "## Auto-learned (ALH)"
AUTO_NOTE = (
    "_Generated from `art/comfy/ALH/learning-log.jsonl` by `alh.py sync`. "
    "**Only `Accepted rules` are active.** Detail/verdicts are in `RUN-LOG.md` and the log; "
    "a rule is mandatory only after it is mirrored into `SKILL.md` / `GLOBAL-RULES.md`._"
)


# ---------------------------------------------------------------- io / locking
def load() -> list[dict]:
    if not LOG.exists():
        return []
    out = []
    for line in LOG.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(f"! unreadable log line skipped: {exc}")
    return out


ORDER = (
    "id", "ts", "schema", "event", "status", "skill", "part", "shot", "layer", "actor",
    "rule", "rule_source", "supersedes", "status_by", "status_ts", "detail",
)


@contextmanager
def log_lock():
    """One process at a time may read-modify-write the log or allocate an id."""
    ALH.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+b") as fh:
        if msvcrt:
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        elif fcntl:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if msvcrt:
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            elif fcntl:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def atomic_write(path: Path, text: str) -> None:
    """Never leave a half-written LEARNINGS.md or log behind."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def save(entries: list[dict]) -> None:
    """Caller must hold log_lock(); this replaces the log atomically."""
    rows = []
    for e in entries:
        row = {k: e.get(k, "") for k in ORDER}
        row.update({k: v for k, v in e.items() if k not in row})  # keep future fields
        rows.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    atomic_write(LOG, "".join(r + "\n" for r in rows))


def normalize_part(value) -> str:
    s = str(value or "").strip().lower()
    if s in {"1", "p1"}:
        return "part1"
    if s in {"2", "p2"}:
        return "part2"
    if s in {"3", "p3"}:
        return "part3"
    return s if s in PARTS else ""


def skills_on_disk() -> list[str]:
    names = []
    if SKILLS.exists():
        names = [p.name for p in SKILLS.iterdir() if (p / "SKILL.md").exists()]
    return sorted(set(names + [GLOBAL_SKILL]))


def skill_file(skill: str) -> Path:
    return GLOBAL_RULES if skill == GLOBAL_SKILL else SKILLS / skill / "LEARNINGS.md"


def promotion_file(skill: str) -> Path:
    return GLOBAL_RULES if skill == GLOBAL_SKILL else SKILLS / skill / "SKILL.md"


def derive_rule(entry: dict) -> str:
    """One-sentence fallback for legacy accepted events that have no `rule` field."""
    d = re.sub(r"\s+", " ", str(entry.get("detail") or "")).strip()
    d = re.sub(r"^(?:user|hy4|agent|machine)\s+\d{1,2}/\d{1,2}\s*:\s*", "", d, flags=re.I)
    first = re.split(r"(?<=[.!?])\s+", d)[0].strip(" -\u2013")
    return first[:200] + ("\u2026" if len(first) > 200 else "")


def rule_of(entry: dict) -> str:
    return str(entry.get("rule") or "").strip() or derive_rule(entry)


def is_run_record(entry: dict) -> bool:
    """An accepted verdict/attempt is evidence, not an active rule, unless promoted explicitly."""
    if entry.get("status") != "accepted":
        return False
    if entry.get("event") not in RUN_EVENTS:
        return False
    return entry.get("rule_source") in {"derived_run", ""} and not entry.get("rule_source") == "explicit"


def active_rules(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e.get("status") == "accepted" and not is_run_record(e)]


# ---------------------------------------------------------------- migrate / upgrade
def cmd_migrate(args) -> int:
    with log_lock():
        entries = load()
        if any(e.get("schema") == 2 for e in entries):
            print("already migrated (schema 2 present) - use `upgrade` for v3 fields")
            return 0
        backup = LOG.with_suffix(".v1.jsonl.bak")
        if LOG.exists() and not backup.exists():
            shutil.copy2(LOG, backup)
            print(f"backup -> {backup}")
        texts = {}
        for skill in skills_on_disk():
            f = skill_file(skill)
            texts[skill] = f.read_text(encoding="utf-8-sig") if f.exists() else ""
        for i, e in enumerate(entries, 1):
            e["id"] = e.get("id") or f"E{i:03d}"
            e["schema"] = 2
            e["actor"] = e.get("actor") or "agent"
            e["part"] = normalize_part(e.get("part"))
            owner = next((s for s, t in texts.items() if e["detail"][:60] in t), "comfyui-runner")
            e["skill"] = e.get("skill") or owner
            e["status"] = "archived"
        save(entries)
    print(f"migrated {len(entries)} entries -> schema 2, status=archived")
    print("re-open the live ones with: alh.py set <id> proposed")
    return 0


def cmd_upgrade(args) -> int:
    """Fill v3 fields in place. Safe to run repeatedly."""
    with log_lock():
        entries = load()
        changed = 0
        for e in entries:
            part = normalize_part(e.get("part"))
            if part != e.get("part", ""):
                e["part"] = part
                changed += 1
            if not e.get("status_by"):
                e["status_by"] = e.get("actor") or "legacy"
                changed += 1
            if not e.get("status_ts"):
                e["status_ts"] = e.get("ts") or ""
                changed += 1
            if "supersedes" not in e:
                e["supersedes"] = ""
                changed += 1
            if e.get("status") == "accepted" and not e.get("rule"):
                e["rule"] = derive_rule(e)
                changed += 1
            if not e.get("rule_source"):
                if e.get("status") == "accepted":
                    looks_run = e.get("event") in RUN_EVENTS or bool(
                        re.search(r"\battempt\b|re-render|\bPASS\b|\br\d\b", str(e.get("detail") or ""), re.I)
                    )
                    derived = str(e.get("rule") or "") == derive_rule(e)
                    e["rule_source"] = ("derived_run" if looks_run else "derived") if derived else "explicit"
                else:
                    e["rule_source"] = ""
                changed += 1
        if changed:
            save(entries)
    print(f"upgraded {changed} field(s) across {len(entries)} event(s)")
    return 0


# ---------------------------------------------------------------- sync
def render_section(entries: list[dict]) -> str:
    by_status = defaultdict(list)
    for e in entries:
        by_status[e.get("status", "proposed")].append(e)

    lines = [AUTO_HEAD, "", AUTO_NOTE, ""]
    accepted = sorted(active_rules(entries), key=lambda x: x["id"])
    if accepted:
        lines += ["### Accepted rules (active)", ""]
        for e in accepted:
            sup = f"  [supersedes {e['supersedes']}]" if e.get("supersedes") else ""
            lines.append(f"- [{e['id']}] ALH:{e['id']} \u2014 {rule_of(e)}{sup}")
        lines.append("")

    records = sorted([e for e in by_status.get("accepted", []) if is_run_record(e)], key=lambda x: x["id"])
    if records:
        lines += ["### Accepted run records (evidence, not rules)", ""]
        for e in records:
            lines.append(f"- {e['id']} {e.get('event')} / {e.get('shot')} / {e.get('layer')} (detail in RUN-LOG.md)")
        lines.append("")

    for status in ("proposed", "revoked"):
        group = sorted(by_status.get(status, []), key=lambda x: x["id"])
        if not group:
            continue
        lines += [f"### {STATUS_LABEL[status]}", ""]
        for e in group:
            tag = "proposed" if status == "proposed" else "REVOKED - DO NOT APPLY"
            lines.append(f"- {e['id']} {tag}: {e.get('event')} / {e.get('shot')} / {e.get('layer')} (detail in RUN-LOG.md)")
        lines.append("")

    archived = by_status.get("archived", [])
    if archived:
        per_layer = defaultdict(list)
        for e in archived:
            per_layer[e.get("layer", "")].append(e)
        lines += [f"### Archived (pre-v2 history, {len(archived)} events)", ""]
        lines.append("_One line per layer. Evidence stays in `RUN-LOG.md` / the JSONL log._")
        lines.append("")
        for layer in sorted(per_layer):
            group = sorted(per_layer[layer], key=lambda x: x["id"])
            lines.append(f"- {layer or '-'} ({len(group)}x, {group[0]['id']}-{group[-1]['id']}): evidence in RUN-LOG.md")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_run_log(entries: list[dict]) -> str:
    lines = [
        "# ALH run log",
        "",
        "_Verdicts, attempts and other run records. Not rules; generated by `alh.py sync`._",
        "",
    ]
    for e in sorted(entries, key=lambda x: x.get("id", "")):
        lines.append(
            f"- {e.get('id')} {e.get('status')}/{e.get('event')}/{e.get('skill')} "
            f"/{e.get('part') or '-'}/{e.get('shot')}/{e.get('layer')} \u2014 {e.get('detail')}"
        )
    return "\n".join(lines).rstrip() + "\n"


def cmd_sync(args) -> int:
    with log_lock():
        entries = load()
        if not entries:
            print("empty log - nothing to sync")
            return 1
        touched = 0
        for skill in skills_on_disk():
            mine = [e for e in entries if e.get("skill") == skill]
            if not mine and skill != GLOBAL_SKILL:
                continue
            f = skill_file(skill)
            body = f.read_text(encoding="utf-8-sig") if f.exists() else f"# Learnings - {skill}\n"
            idx = body.find(AUTO_HEAD)
            head = body[:idx].rstrip() + "\n\n" if idx >= 0 else body.rstrip() + "\n\n"
            atomic_write(f, head + render_section(mine))
            touched += 1
            print(f"synced {skill:18} {len(mine):3} entries")
        atomic_write(RUN_LOG, render_run_log(entries))
    print(f"{touched} skill file(s) rewritten; run log -> {RUN_LOG.name}")
    return 0


# ---------------------------------------------------------------- report
def fmt_counter(title: str, counter: Counter, total: int) -> list[str]:
    lines = [f"### {title}", "", "| value | n | share |", "|---|---|---|"]
    for key, n in counter.most_common():
        lines.append(f"| {key or '-'} | {n} | {100 * n / total:.0f}% |")
    lines.append("")
    return lines


def promoted_ids() -> set[str]:
    ids: set[str] = set()
    for skill in skills_on_disk():
        f = promotion_file(skill)
        if f.exists():
            ids.update(re.findall(r"ALH:(E\d{3})", f.read_text(encoding="utf-8-sig")))
    return ids


def is_promoted(entry: dict) -> bool:
    """Marker wins; otherwise the rule text itself must already live in SKILL.md."""
    f = promotion_file(str(entry.get("skill") or ""))
    if not f.exists():
        return False
    text = f.read_text(encoding="utf-8-sig")
    if f"ALH:{entry.get('id')}" in text:
        return True
    norm = re.sub(r"\W+", " ", rule_of(entry).lower()).strip()
    return bool(norm[:80] and norm[:80] in re.sub(r"\W+", " ", text.lower()))


def cmd_report(args) -> int:
    with log_lock():
        entries = load()
    if args.status:
        entries = [e for e in entries if e.get("status") == args.status]
    if args.skill:
        entries = [e for e in entries if e.get("skill") == args.skill]
    if not entries:
        print("no entries match the filter")
        return 0

    total = len(entries)
    by_status = Counter(e.get("status", "proposed") for e in entries)
    by_event = Counter(e.get("event") for e in entries)
    by_skill = Counter(e.get("skill") for e in entries)
    by_layer = Counter(e.get("layer") for e in entries)

    lines = [f"# ALH report - {datetime.now():%Y-%m-%d %H:%M}", "",
             f"log: `{LOG.relative_to(ROOT)}`  |  total {total} event(s)", ""]
    lines += fmt_counter("Status", by_status, total)
    lines += fmt_counter("Event", by_event, total)
    lines += fmt_counter("Skill", by_skill, total)
    lines += fmt_counter("Layer", by_layer, total)

    proposed = [e for e in entries if e.get("status") == "proposed"]
    if proposed:
        lines += ["### Needs a decision", ""]
        for e in sorted(proposed, key=lambda x: x["id"]):
            lines.append(f"- [{e['id']}] {e.get('event')} / {e.get('shot')} / {e.get('layer')} - {rule_of(e)}")
        lines.append("")

    accepted = active_rules(entries)
    superseded_ids = {s.strip() for e in entries for s in str(e.get("supersedes") or "").split(",") if s.strip()}
    checks = [
        ("Accepted but not promoted to SKILL.md/GLOBAL-RULES.md",
         [e for e in accepted if not is_promoted(e)]),
        ("Accepted without a one-sentence rule",
         [e for e in accepted if not str(e.get("rule") or "").strip()]),
        ("Invalid skill field (not synced anywhere)",
         [e for e in entries if e.get("skill") not in skills_on_disk()]),
        ("Active rule superseded by a newer event",
         [e for e in accepted if e["id"] in superseded_ids]),
    ]
    for title, group in checks:
        if group:
            lines += [f"### {title}", ""]
            for e in sorted(group, key=lambda x: x["id"]):
                lines.append(f"- [{e['id']}] {e.get('skill')} / {e.get('shot')} / {e.get('layer')} - {rule_of(e)}")
            lines.append("")

    superseded = {s.strip() for e in entries for s in str(e.get("supersedes") or "").split(",") if s.strip()}
    conflicts = defaultdict(set)
    for e in entries:
        conflicts[(e.get("shot"), e.get("layer"))].add(e.get("status"))
    hard_conflicts = {k for k, v in conflicts.items() if {"accepted", "revoked"} <= v}
    for eid in sorted(superseded):
        e = next((x for x in entries if x.get("id") == eid), None)
        if e and e.get("status") == "accepted":
            hard_conflicts.add((f"superseded:{eid}", e.get("layer")))
    if hard_conflicts:
        lines += ["### Contradictions / superseded-but-active", ""]
        for key in sorted(hard_conflicts, key=str):
            lines.append(f"- {key[0]} / {key[1]}")
        lines.append("")

    idle = [s for s in skills_on_disk() if s not in by_skill]
    if idle:
        lines += ["### Skills with no learning events", "", "- " + ", ".join(idle), ""]

    text = "\n".join(lines).rstrip() + "\n"
    if not args.print_only:
        atomic_write(REPORT, text)
        print(f"report -> {REPORT.relative_to(ROOT)}")
    print(text)
    return 0


# ---------------------------------------------------------------- set / edit / verify
def _stamp(e: dict, by: str, supersedes: str) -> None:
    e["status_by"] = by
    e["status_ts"] = datetime.now().astimezone().isoformat()
    if supersedes:
        e["supersedes"] = supersedes


def cmd_set(args) -> int:
    with log_lock():
        entries = load()
        index = {e.get("id"): e for e in entries}
        changed = 0
        for eid in args.ids:
            e = index.get(eid)
            if not e:
                print(f"! {eid} not found")
                continue
            e["status"] = args.status
            _stamp(e, args.by, args.supersedes or "")
            changed += 1
            print(f"{eid} -> {args.status} by {args.by}  ({e.get('event')} / {e.get('shot')} / {e.get('layer')})")
        if changed:
            save(entries)
    return 0 if changed else 1


def cmd_edit(args) -> int:
    with log_lock():
        entries = load()
        index = {e.get("id"): e for e in entries}
        changed = 0
        for eid in args.ids:
            e = index.get(eid)
            if not e:
                print(f"! {eid} not found")
                continue
            if args.skill is not None:
                e["skill"] = args.skill
            if args.part is not None:
                e["part"] = normalize_part(args.part)
            if args.rule is not None:
                e["rule"] = args.rule
                e["rule_source"] = "explicit"
            if args.supersedes is not None:
                e["supersedes"] = args.supersedes
            e["status_by"] = args.by
            e["status_ts"] = datetime.now().astimezone().isoformat()
            changed += 1
            print(f"{eid} metadata updated by {args.by}")
        if changed:
            save(entries)
    return 0 if changed else 1


def cmd_verify(args) -> int:
    with log_lock():
        entries = load()
    index = {e["id"]: e for e in entries}
    bad = 0

    for e in entries:
        if e.get("skill") not in skills_on_disk():
            print(f"! {e['id']}: unknown skill '{e.get('skill')}' - sync would drop it")
            bad += 1
        if normalize_part(e.get("part")) != str(e.get("part") or ""):
            print(f"! {e['id']}: non-canonical part '{e.get('part')}'")
            bad += 1

    expected = {
        e["id"]: e for e in active_rules(entries)
        if e.get("skill") in skills_on_disk()
    }
    seen: dict[str, str] = {}
    for skill in skills_on_disk():
        f = skill_file(skill)
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"^- \[(E\d{3})\]", line)
            if not m:
                continue
            eid = m.group(1)
            seen[eid] = skill
            e = index.get(eid)
            if not e:
                print(f"! {skill}: {eid} in LEARNINGS but not in log")
                bad += 1
            elif e.get("skill") != skill:
                print(f"! {skill}: {eid} belongs to skill '{e.get('skill')}'")
                bad += 1
            elif e.get("status") != "accepted":
                print(f"! {skill}: {eid} is {e.get('status')} but rendered as an active rule")
                bad += 1

    for eid, e in expected.items():
        if eid not in seen:
            print(f"! accepted rule {eid} missing from {skill_file(e['skill']).name}")
            bad += 1
        if not str(e.get("rule") or "").strip():
            print(f"! accepted rule {eid} has no one-sentence 'rule' field")
            bad += 1

    missing_promo = [e for e in expected.values() if not is_promoted(e)]
    if missing_promo:
        note = f"{len(missing_promo)} accepted rule(s) not mirrored into SKILL.md/GLOBAL-RULES.md"
        if args.require_promoted:
            for e in missing_promo:
                print(f"! {e['id']} accepted but not promoted to {promotion_file(e['skill']).name}")
            bad += len(missing_promo)
        else:
            print(f"note: {note} (use --require-promoted to make this a hard gate)")

    print("drift: none" if bad == 0 else f"drift: {bad} problem(s)")
    return 0 if bad == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ALH curator (v2 log, v3 rules)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("migrate", help="v1 log -> v2 schema").set_defaults(fn=cmd_migrate)
    sub.add_parser("upgrade", help="v2 log -> v3 fields").set_defaults(fn=cmd_upgrade)

    sub.add_parser("sync", help="rewrite LEARNINGS.md + RUN-LOG.md from the log").set_defaults(fn=cmd_sync)

    p_rep = sub.add_parser("report", help="curation report")
    p_rep.add_argument("--status", choices=STATUSES)
    p_rep.add_argument("--skill")
    p_rep.add_argument("--print-only", action="store_true", help="do not write REPORT.md")
    p_rep.set_defaults(fn=cmd_report)

    p_set = sub.add_parser("set", help="change status of one or more events")
    p_set.add_argument("ids", nargs="+")
    p_set.add_argument("status", choices=STATUSES)
    p_set.add_argument("--by", default="user", help="who made the decision (audit)")
    p_set.add_argument("--supersedes", default="", help="comma-separated older event ids")
    p_set.set_defaults(fn=cmd_set)

    p_edit = sub.add_parser("edit", help="set metadata without changing status")
    p_edit.add_argument("ids", nargs="+")
    p_edit.add_argument("--skill")
    p_edit.add_argument("--part")
    p_edit.add_argument("--rule")
    p_edit.add_argument("--supersedes")
    p_edit.add_argument("--by", default="user")
    p_edit.set_defaults(fn=cmd_edit)

    p_ver = sub.add_parser("verify", help="LEARNINGS vs log drift, both directions")
    p_ver.add_argument("--require-promoted", action="store_true",
                       help="also fail when an accepted rule is not in SKILL.md/GLOBAL-RULES.md")
    p_ver.set_defaults(fn=cmd_verify)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
