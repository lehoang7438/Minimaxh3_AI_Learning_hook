# project-tools/

Script/project artifact được mirror để AI khác hiểu prompt và audit được sinh ra thế nào.
Chạy từ **project root**, không chạy trực tiếp trong repo.

| File | Dùng khi |
|---|---|
| `rebuild_prompts.py` | Sinh `prompts/part1-rebuilt/*.txt` từ spec + global context (nguồn prompt duy nhất) |
| `h3_prompt_rules.py` | `video_style_contract()` + `validate_prompt()` — dùng chung cho ảnh/video |
| `prompt_consistency_audit.py` | Audit prompt theo structured source-of-truth, output `PASS/FAIL/CHƯA CHỐT` |
| `chain4_run.py`, `chain4_prepare.py`, `chain4_qa.py`, `chain4_recover.py` | Chạy/QA/khôi phục chain G01→G02→G03→G05 |
| `workflow_state.py` | Ghi state/GPU lock sau mỗi hoạt động |
| `h3-chain4.json` | Workflow API duy nhất được phép queue cho chain này |

Quy tắc khi đọc code:

- `prompts/part1/*.txt` cũ đã deprecated; chỉ dùng bản `part1-rebuilt`.
- Metadata (`fps`, resolution, `target_duration`, trục 180°, `relative_height`) là
  `metadata_only` — script/QA đọc, **không nhồi vào prompt**.
- Style contract phải nằm đầu field `integrated_multimodal_description`, trước `[Shot 1]`.
- `composited later` bị cấm (E298); G01 under-seat là case riêng (E248/E289).
