---
name: h3-prompt-linter
description: Validate MiniMax H3 prompts before rendering. Use when checking h3-prompt-writing output for required fields, subject/picture/video/audio label consistency, shot numbering, At MM:SS.mmm timecodes, dialogue tags, and duration against the requested seconds or frames.
---

# H3 Prompt Linter

Sau khi lint → mở `WORKFLOW-INDEX.md` để nhắc bước kế + ALH. Với G01–G04 dùng
`powershell -NoProfile -ExecutionPolicy Bypass -File .opencode\skills\h3-prompt-linter\scripts\lint_h3.ps1 -Path prompts\part1-rebuilt\<Gxx>.txt -Seconds 10 -Mode base`.
Ngoài linter PowerShell, prompt còn đi qua `h3_prompt_rules.validate_prompt()` ngay lúc `rebuild_prompts.py` ghi file.

Gate between `h3-prompt-writing` and rendering. It catches the mistakes that make local H3 output freeze, desync audio, or ignore references.

**Kiểm xung đột (Tầng 2):** chặn từ khóa mâu thuẫn với `mood` / `shot_size` đã khai báo trong spec
(vd shot `close-up` mà prompt ghi "wide aerial"), chặn từ dễ sinh **text rác** (`sign`, `label`,
`neon text`, `subtitle`, `screen text`, `watermark`) nếu shot không yêu cầu đọc chữ. `forbidden_tokens`
từ bible bị chặn tuyệt đối. Position check vẫn áp dụng: style contract phải trước field body.

**Ngoại lệ có chủ đích:** shot có thể khai báo `allow_text: ["27A"]` (số ghế, màn hình, biển hiệu
theo kịch bản) — linter cho phép các từ đó và **không** đưa vào prompt dạng "write the text ...";
các shot còn lại vẫn bị chặn mặc định. `allow_text` là `metadata_only`, không nhồi prompt.

**Cấm slug trong prompt:** không được chèn `wardrobe_id` dạng `khang-navy-longsleeve`,
`vy-crew-uniform-teal-scarf` vào `prompt_visible` — H3 không đọc được. Phải dùng câu
`appearance + wardrobe` nguyên văn từ bible (WS/MS) hoặc `appearance + upper_wardrobe` (CU/INS).
Validator phải báo lỗi nếu phát hiện pattern `-navy-|-crew-|-tee-` trong prompt cuối.

**Kiểm xung đột bible:** báo lỗi nếu `must_keep` mâu thuẫn `wardrobe` (vd friend_clap "navy t-shirt"
vs "charcoal tee") hoặc chứa từ trong `forbidden_tokens` **ở dạng khẳng định**. Không báo giả với
phủ định có chủ đích ("Never a vest", "no vest", "navy tee + charcoal trousers").

**Tránh priming màu/đối tượng cấm (sửa sau G02):** style contract không được nêu cụm
"infected eyes" ở shot có `red_allowed: false` — H3 đọc cụm đó rồi vẽ **mắt đỏ** cả trong flashback
nhà hàng. Cách xử lý: **bỏ hẳn cụm đó khỏi prompt**, chỉ giữ `red_allowed` trong
`global-context.json` cho QA đối chiếu. Tuyệt đối không thay bằng câu phủ định
("NO red anywhere in this shot; do not draw red eyes") — H3 local vẽ đúng thứ bị nhắc, và
`feed_h3_context.py` / `rebuild_prompts.py` chủ động strip các câu đó ra. `red_allowed` là metadata,
không phải lệnh vẽ.

**Vai trò:** chỉ trả PASS/FAIL cho `run_master.ps1` trước khi queue. Không tự tạo file/artifact
nào khác; lỗi thì sửa prompt nguồn hoặc global context, không vá output.

**Position & conflict check (sửa sau ca G02).** Linter/feeder phải kiểm thêm:
- **Position (đã đo, 25/11):** style contract (`Solid flat fills`, palette, rule tay mitten) phải nằm
  **ở đầu** `integrated_multimodal_description`, trước `[Shot 1]`. Linter WARN nếu 400 ký tự đầu
  không có `Solid flat fills`/`flat 2D` — trước đây check này chỉ xác nhận body bắt đầu bằng
  `[Shot 1]`, điều luôn đúng, nên contract trôi xuống 1900 ký tự mà vẫn PASS (ca G02).
- **Feed composition:** `feed_h3_context.py` chèn dòng first-frame **sau** contract, **trước**
  `[Shot 1]`, và **không** lặp lại scene/objects/light/wardrobe (bản rebuilt đã có, đúng thứ tự và
  đã lọc prop ngoài khung cho CU). Lặp lại làm prompt phình gấp đôi và làm loãng trọng số.
- **Static camera:** WARN nếu prompt ghi `camera static`/`static camera` mà không kèm
  drift/sway/handheld/push-in. `Fixed security camera view` (G49) không bị bắt.
- **Text allowance (duyệt 25/11):** FAIL nếu prompt còn câu `Visible text allowed only: ...`.
  Shot có `allow_text` phải gộp vào contract thành **một** câu `no text except ...`; hai câu
  ngược nhau (contract "no text" + đuôi "text allowed only") làm H3 chia đôi trọng số (G01).
- **UI shot:** không được có handheld sway trên graphic phẳng, không câu "lips remain closed"
  hay SFX bed khi shot không có nhân vật; mô tả hành động phải bằng tiếng Anh, tiếng Việt chỉ
  trong `<d>`.
- **Separator:** feed phải normalize CRLF và tách field bằng `overall_soundscape:` (một newline),
  không partition theo `\n\n...` — nếu không enrich âm thầm không áp dụng mà linter vẫn PASS.
- **Conflict:** `forbidden_tokens` từ `characters.json` bị chặn tuyệt đối ở cả prompt gốc lẫn phần
  enrich (Khang: vest/jacket/scarf; bạn: uniform/scarf; nhiễm: giày). Cấm từ mâu thuẫn style như
  `gradient`, `photorealistic`, `storybook page`, `comic panel`.

## Contract

Two prompt shapes exist. Do not mix them.

**Base (T2VA / I2VA / FL2VA / L2VA)** — exactly these fields, in this order:

```
integrated_multimodal_description: ...
overall_soundscape: ...
non_diegetic_music: ...
```

**Full-reference (Ref2VA)** — exactly these six, in this order:

```
subject_definitions: ...
summary: ...
retention_analysis: ...
detailed_description: ...
overall_soundscape: ...
non_diegetic_music: ...
```

Rules the linter enforces:

- Every field present, non-empty, and in the order above.
- Shot tags `[Shot 1]`, `[Shot 2]`, ... sequential from 1.
- Cut timecodes written `At 00:05.000` (minutes:seconds.milliseconds), strictly increasing, never past the clip length.
- Clip length matches the request: 24 fps, frames on `17k + 5` (10 s = 243 frames, 5 s = 124, 15 s = 362).
- Labels `<Subject N>`, `<Picture N>`, `<Video N>`, `<Audio N>`: every label used is defined in `subject_definitions`; unused definitions are a warning.
- Dialogue wrapped in `<d>[Language] text</d>`, tags balanced, language tag present.
- No placeholders: `{{`, `}}`, `TODO`, `TBD`, `[insert`.

## Run

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  .opencode\skills\h3-prompt-linter\scripts\lint_h3.ps1 `
  -Path .\prompt.txt -Seconds 10
```

Options: `-Frames 243` instead of `-Seconds`, `-Mode auto|base|ref` to force a shape.

Exit code `0` = pass (warnings allowed), `1` = errors. Fix every ERROR before queueing a render; treat WARN as review items.

## What it does not check

Meaning, taste, continuity of wardrobe, and whether the soundscape matches the picture. Those stay a human/agent review: read the description once and ask "does every stated sound have a visible or implied source?".

## Related skills

- `h3-prompt-writing` — produces the prompt being linted.
- `h3-storyboard` — supplies shot list, durations and labels.
- `character-bible` — source of truth for label-to-file mapping.
