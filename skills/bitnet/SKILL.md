---
name: BitNet Cleanup
description: Dọn dẹp và sắp xếp thư mục tài liệu/job theo phân loại. Gọi khi cần dọn project, archive job cũ, hoặc tổ chức lại docs.
---

# BitNet — Cleanup & Organizer

Vai trò: dọn dẹp và sắp xếp **tài liệu, job file, json, md** của dự án GHẾ 27A theo phân loại. Không sửa nội dung sáng tạo (spec, prompt, keyframe, VO, phim).

> BitNet hiện **chạy được** (user-scope build, `tools/BitNet/run-bitnet.ps1`, ~10 tok/s CPU). Model 2B nên chỉ giao việc nhỏ: phân loại file, chọn A/B, kiểm tra mâu thuẫn ngắn. Công việc xóa/move file vẫn do agent thực thi theo rules dưới đây.

## Phân loại

| Nhóm | Đường dẫn | Nội dung |
|---|---|---|
| Active jobs | `art/jobs/active/` | Job đang dùng: `jobs-h3-assets-batch*.json`, `jobs-h3-kf-batch*.json`, `jobs-rig-sheets.json`, `jobs-canon-refs.json` |
| Archive jobs | `art/jobs/archive/` | Job cũ đã thay thế: `jobs-v*.json`, `jobs-h3-g02/g05*.json`, `jobs-pilot-*.json`, `jobs-fix*.json` |
| Canon docs | `art/docs/` | `characters.json`, `animation-plan.json`, `level3-prompts.json`, `bg-layout.json`, `*-spec.json`, `AGENTS.md` (giữ bản gốc ở root, copy tham chiếu) |
| Tests | `art/tests/` | Script + ảnh thử nghiệm |

## Quy tắc bắt buộc

1. **Dry-run trước**: liệt kê các file sẽ move/xóa, báo user, mới thực hiện.
2. **Không xóa file đang được reference** bởi spec, script, AGENTS.md hoặc job đang chạy. Dò bằng `cleanup.py --check` và grep tên file.
3. **Không move job đang chạy**: nếu có tiến trình `gen_image.py` đang đọc batch, giữ nguyên path `art/jobs-h3-*-batch*.json`.
4. **Không xóa asset/reference**: `art/assets/**`, `characters.json`, `art/assets/h3/refs/**` là canon.
5. Mỗi lần dọn xong ghi lại: số file move/xóa, dung lượng giải phóng, lý do.

## Lệnh

```powershell
python .opencode\scripts\cleanup.py --check
python .opencode\scripts\cleanup.py
```
