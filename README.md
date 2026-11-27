# GHẺ 27A — AI learning bundle

Repo này là **bản chia sẻ một chiều** của rule/workflow đã được học khi làm phim
GHẺ 27A (MiniMax H3 / FreeVideo). Mục đích: AI khác đọc để áp ngay rule đã có bằng
chứng, rồi tiếp tục cập nhật ALH thay vì học lại từ đầu.

> Nguồn truth vẫn là **project local**. Repo là snapshot để đọc/audit, không phải nơi
> sửa rule trực tiếp. Quy trình đẩy: xem `CONTRIBUTING.md`.

## Cấu trúc

| Đường dẫn | Nội dung | Ai nên đọc |
|---|---|---|
| `skills/` | 9 skill local đang chạy (`SKILL.md`, `LEARNINGS.md`, script/reference đi kèm) | Mọi AI trước khi sửa prompt/workflow/QA |
| `alh/` | Engine ALH (`alh.py`, `learn_hook.ps1`, `completion_handler.ps1`), `learning-log.jsonl`, `REPORT.md`, `GLOBAL-RULES.md`, `CONDENSED-RULES-DRAFT.md`, `RUN-LOG.md`, cleanup report | AI cần truy vết rule, ghi event mới, chốt status |
| `project-tools/` | Script dựng prompt / audit / chain4 và workflow `h3-chain4.json` | AI cần hiểu prompt được sinh và audit ra sao |
| `audit-inputs/` | Ảnh chụp phẳng spec/context/prompt/report + payload `/history` đã queue | Reviewer không có máy local |
| `PLAYBOOK.md` | Chỉ mục nhanh 3 tầng: spec → skill → ALH → QA | Đọc đầu tiên |
| `tools/push_learning_bundle.ps1` | Script mirror local → repo (loại `__pycache__`/`.pyc`) | Người cập nhật bundle |

`MANIFEST.md` (do script sinh) ghi thời điểm sync, số file và hash của các file chốt.

## Thứ tự đọc khuyến nghị

1. `PLAYBOOK.md` — sơ đồ 3 tầng, sửa đúng 1 lớp, anchor rule, retry cap.
2. `skills/<id>/SKILL.md` cho việc đang làm (bắt buộc: `h3-prompt-writing`,
   `h3-prompt-linter`, `character-bible`, `h3-visual-qa`, `asset-qa`,
   `comfyui-runner` khi đụng workflow/queue).
3. `alh/REPORT.md` → mục **Needs a decision** và **Accepted but not promoted**.
4. `alh/CONDENSED-RULES-DRAFT.md` — 39 rule gom từ accepted event; **chưa mirror**,
   chưa resolve 7 cặp M1–M7.
5. `audit-inputs/` để đối chiếu structured source-of-truth (không so prompt-vs-prompt).

## Trạng thái chốt tại lần sync này

- ALH: **302 event** — 142 accepted / 100 archived / 55 proposed / 5 revoked.
- **112 accepted chưa mirror** vào `SKILL.md` / `GLOBAL-RULES.md`; rule chỉ thành
  hard gate sau khi mirror và được user duyệt.
- GPU: `qa_hold`. G01 v12 / G02 v3 / G05 đã lint PASS nhưng **chưa queue**.
- G03 chờ user chọn hướng E271 (anchor G02 / `continue_from` / render đối chứng).
- Seat layout (E230/E231/E237), light (E273/E209) và quyền accept vẫn CHƯA CHỐT.

## Luật cứng khi dùng bundle

- `global-context*.json` là **output**, không làm nguồn prompt. Spec/map/bible mới là nguồn.
- Không promote event `proposed` thành rule; `supersedes`/`status_by` phải có khi viết rule condensed.
- Không queue GPU khi QA của shot trước chưa sạch; một job một lúc, `fv.ps1 doctor` GO.
- Không tự bật `python main.py`; app sở hữu server/token/DB.
- Khi audit: so structured field, không regex/văn xuôi prompt-vs-prompt; FAIL phải hand-check.
