# Cách cập nhật bundle

Bundle chỉ đi **một chiều: project local → repo**. Không edit trực tiếp `skills/`,
`alh/` hay `project-tools/` trên repo để tránh drift; thay đổi ở project rồi chạy
script mirror.

## 1. Quy trình ở project local

1. Đọc `WORKFLOW-INDEX.md` (3 dòng cuối: `Vừa xong / Bước kế / ALH`).
2. Load đúng skill bằng tool `skill` (skill không tự load).
3. Sửa **đúng 1 lớp** theo PLAYBOOK: spec/map → rule/skill → ref/context → workflow → prompt → seed/anchor.
4. Rebuild (`art/tests/rebuild_prompts.py`), lint (`lint_h3.ps1`), audit
   (`prompt_consistency_audit.py`) nếu đụng prompt.
5. Ghi ALH: `learn_hook.ps1 -Event ... -Status accepted|proposed|... -Actor user|agent -Detail ... -Rule ...`.
6. `alh.py sync` → `alh.py report` → `alh.py verify` (phải `drift: none`) → `workflow_state.py --write`.

## 2. Mirror lên repo

Từ thư mục project (script tự tìm repo nếu không truyền `-Repo`):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  tools\push_learning_bundle.ps1 -Src 'C:\Users\Admin\Documents\Default Project'
```

Script sẽ:

- xây lại `skills/`, `alh/`, `project-tools/` từ local (bỏ `__pycache__`, `*.pyc`, `.lock`);
- copy `PLAYBOOK.md`, refresh `audit-inputs/` (snapshot phẳng + `queued-payloads/`);
- ghi `MANIFEST.md` (timestamp, số file, hash);
- `git add -A`, commit, `git push origin main`.

Dùng `-NoCommit` nếu chỉ muốn xem diff trước khi đẩy.

## 3. Quy tắc cho AI khác

- Nếu làm trong project khác: đọc bundle, áp rule có `status=accepted` **và** đã mirror;
  rule accepted-chưa-mirror chỉ là bằng chứng, không phải hard gate.
- Event mới phải có `status_by` (`user` hoặc `agent`), `status_ts` do hook ghi.
- Muốn override rule cũ: ghi rõ `supersedes: E###` kèm lý do + payload/history làm bằng chứng.
- Không tự resolve cặp M1–M7 hay seat/light decision đang CHƯA CHỐT; hỏi user kèm bằng chứng.
- Không đẩy ảnh/video/asset lớn hay token; bundle chỉ chứa rule, script, snapshot văn bản.
- Nếu repo stale so với local, tin `MANIFEST.md` + local ALH log, không tin global
  `~/.config/opencode/skills` (bản cũ hơn).
