# skills/

Bản mirror của `.opencode/skills/` đang chạy trong project GHẺ 27A (local là nguồn truth).

| Skill | Khi nào load |
|---|---|
| `asset-qa` | Ngay sau mỗi lượt gen ảnh H3 Image; kiểm size + nhìn ảnh + bible trước khi dùng ref |
| `bitnet` | Dọn/sắp xếp docs & job theo phân loại |
| `character-bible` | Nhân vật định kỳ; giữ appearance/wardrobe/voice/ref cố định |
| `comfyui-runner` | Sửa workflow / queue ComfyUI / decode `node_errors` (API format + preflight) |
| `freevideo-runner` | Render local FreeVideo: doctor → plan → submit → wait → download |
| `h3-prompt-linter` | Lint mọi prompt trước khi vào slot render |
| `h3-prompt-writing` | Viết prompt H3 T2VA/I2VA/FL2VA/L2VA/Ref2VA; style contract lấy từ `h3_prompt_rules.py` |
| `h3-storyboard` | Chia shot 4–15 s, shot_size/camera/eyeline/props_state, chain 180° |
| `h3-visual-qa` | Pass 1 `visual_qa.py` + pass 2 `build_review_grid.py` (phải đọc grid bằng mắt) |

Mỗi skill có `SKILL.md` (luật bắt buộc) và `LEARNINGS.md` (ALH auto-learned, user duyệt
mới promote vào SKILL.md). Script/reference đi kèm được mirror nguyên vẹn, trừ
`__pycache__`/`*.pyc`.

**Không** sửa trực tiếp thư mục này trên repo — sửa ở project rồi chạy
`tools/push_learning_bundle.ps1`.
