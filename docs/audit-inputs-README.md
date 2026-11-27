# audit-inputs/

Ảnh chụp phẳng (flattened snapshot) để reviewer/AI khác audit mà không có máy local.
Tên file đổi `\` thành `__` (ví dụ `art__env__cabin-map.json`).

**Đây là snapshot, không phải nguồn truth.** Bản live nằm ở `skills/`, `alh/` và project
local. Snapshot được refresh mỗi lần chạy `tools/push_learning_bundle.ps1`.

Nhóm file:

- Spec/context: cabin-map, global-context part1/2/3, part1-spec.
- Prompt: `prompts__part1-rebuilt__G01..G05.txt`.
- Generator/audit: `rebuild_prompts.py`, `h3_prompt_rules.py`,
  `prompt_consistency_audit.py`, `chain4_run.py`, `h3-chain4.json`.
- ALH: log, REPORT, GLOBAL-RULES, CONDENSED draft, cleanup report.
- QA report: `prompt-consistency-report.json/md`, `prompt-system-review.md`,
  `g03-gradient-rootcause.md`, `audit-manual-check.md`.
- `queued-payloads/`: payload thật từ ComfyUI `GET /history/<job_id>` — dùng để bác bỏ
  giả thuyết; `/freevideo/agent/v1/history/...` trả 404.

Khi audit: đối chiếu structured field của spec/map/context, không so sánh văn xuôi
prompt-vs-prompt; CHƯA CHỐT phải giữ nguyên khi rule còn xung đột (seat/light).
