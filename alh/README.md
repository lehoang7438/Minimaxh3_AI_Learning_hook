# alh/

Automatic Learning Hook — nơi ghi bằng chứng và trạng thái rule.

## File

| File | Vai trò |
|---|---|
| `learning-log.jsonl` | Append-only, schema 2, id `E###`; nguồn truth cho mọi rule/status |
| `REPORT.md` | Thống kê status/event/skill/layer + mục `Needs a decision`, `Accepted but not promoted` |
| `GLOBAL-RULES.md` | Chỉ rule đã mirror; hiện mới E234 |
| `CONDENSED-RULES-DRAFT.md` | 39 rule gom từ accepted event; **chưa mirror**, 7 cặp M1–M7 chưa resolve |
| `PLAYBOOK.md` (ở root repo) | Chỉ mục 3 tầng + anchor/retry/verdict protocol |
| `RUN-LOG.md`, `SESSION-SUMMARY.md` | Nhật ký chạy/tổng kết; đọc để truy nguyên |
| `alh.py` | `migrate` / `report` / `sync` / `set` / `verify` |
| `learn_hook.ps1` | Ghi event mới, fail-silent với pipeline |
| `completion_handler.ps1` | Tổng kết cuối `run_all_parts.ps1` trước khi sleep máy |
| `CLEANUP-REPORT-*.md` | Bằng chứng dọn rác project & FreeVideo |

## Lệnh chuẩn (ở project local)

```powershell
powershell -File art\comfy\ALH\learn_hook.ps1 -Event qa_fail -Shot G03 -Layer clip -Skill comfyui-runner -Part part1 -Status proposed -Actor agent -Detail '...' -Rule '...'
& '.\.venv-tts\Scripts\python.exe' art\comfy\ALH\alh.py sync
& '.\.venv-tts\Scripts\python.exe' art\comfy\ALH\alh.py report
& '.\.venv-tts\Scripts\python.exe' art\comfy\ALH\alh.py verify   # phải 'drift: none'
```

`alh.py set` mặc định `--by user` và stamp `status_by` / `status_ts`. Rule chỉ thành
hard gate sau khi user duyệt và mirror vào `SKILL.md` / `GLOBAL-RULES.md`.

## Nguyên tắc

- FAIL/blocker phải trace end-to-end rồi ghi ALH trước khi hỏi user (E234).
- `proposed` không tự thành `accepted`; `revoked` không tự phục hồi.
- Mọi override phải có `supersedes` + bằng chứng payload/history (`GET /history`, không tin UI).
- Agent không tự chốt verdict khi QA pass 2 chưa đọc bằng mắt.
