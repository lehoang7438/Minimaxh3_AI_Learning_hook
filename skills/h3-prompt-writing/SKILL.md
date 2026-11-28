---
name: h3-prompt-writing
description: Write MiniMax H3 video generation prompts for T2VA, I2VA, FL2VA, L2VA, and Ref2VA. Use when rewriting multimodal requests into H3 prompt structures, composing integrated_multimodal_description, overall_soundscape, and non_diegetic_music, aligning keyframes, or defining reference labels for images, videos, and audio.
compatibility: Portable to any agent that can read local files — no external API calls, MiniMax Hub tools, or proprietary runtime required. The agents/openai.yaml file only adds optional ChatGPT/Codex UI metadata; it does not restrict the skill to OpenAI agents.
---

# H3 Prompt Writing

Sau khi viết/xuất prompt → lint (`h3-prompt-linter`) rồi mở `WORKFLOW-INDEX.md` để nhắc bước kế + ALH.
Style contract **không viết tay**: lấy từ `art/tests/h3_prompt_rules.py` (`video_style_contract()`), cùng nguồn
với prompt asset, để ảnh và video không lệch số ghế/ánh sáng. Mọi prompt đi qua `validate_prompt()` trước khi ghi file.

**Input contract — identity (24/11, bản nháp chờ batch xong):** lấy `appearance + wardrobe`
**nguyên văn** từ `characters.json`, **cấm slug** `wardrobe_id` (`khang-navy-longsleeve`,
`vy-crew-*`). **WS/MS** dùng `appearance + wardrobe` đầy đủ; **CU/INS** dùng `appearance +
upper_wardrobe` (cổ/vai/tay áo), không chèn quần/chân trần vào cận cảnh. Tóc là nhận diện riêng:
Khang = tóc đen xù, Vy = bún nâu, crew = tóc gọn; friend_beer/friend_clap đang tách thành tóc chải
gọn / rẽ ngôi — chỉ apply sau khi gen lại canon ref + asset-qa. `friend_clap.must_keep` lệch
"navy" so với `wardrobe` charcoal đã ghi bản sửa. Không đổi `appearance` khi ref vẫn là tóc cũ.

**Thứ tự bắt buộc trong field 1 (Tầng 2):** `style contract` → `cỡ cảnh & camera` → `nhân vật + wardrobe` → `hành động + tiếp xúc/mặt đỡ` → `mood ánh sáng`. Đây là thứ tự trọng số của H3; đảo ngược là video trôi style (ca G02).

**Chỉ đưa field `prompt_visible`.** Các field `metadata_only` (fps, resolution, aspect_ratio,
target_duration, trục 180°, relative_height so với shot trước, ghi chú Chain QA) phải nằm trong
global context để script/QA đối chiếu, **không viết vào prompt** — prompt dài làm loãng trọng số.

**ALH:E248 (user 27/11, G01 under-seat insert):** mở khung ngay trong khe tối dưới ghế, camera lia ngắn trong khe (không lia xuống từ tầm hành khách), một cánh tay bị cắn dạng **mitten liền**, mắt chấm không lông mày/mũi, một nguồn sáng lạnh mờ và 65–75 % near-black; contract riêng G01 không nhắc cabin rows/oval windows/ngồi.

**Vị trí style contract (sửa sau ca G02):** cụm `Solid flat fills / palette / mitten / no gradient`
phải đặt **ngay đầu field `integrated_multimodal_description`**, trước phần mô tả `[Shot 1]` —
không được dồn xuống cuối. H3 trọng số phần đầu cao hơn; đặt cuối thì linter vẫn PASS nhưng video
trôi sang painterly (đúng lỗi G02). Feeder (`feed_h3_context.py`) và custom node đã tuân theo quy
tắc này; khi viết prompt mới cũng phải giữ.

**Nguồn prompt trong dự án này:** `prompts/part1-rebuilt/*.txt` do `art/tests/rebuild_prompts.py`
sinh từ spec + global context theo đúng thứ tự trên. Bộ `prompts/part1/*.txt` cũ (từ
`spec_to_prompts.py`) đã deprecated — chứa cue xấu ("ánh nến nhảy", "trong không trung") khiến QA
phải bắt lỗi sau render. `feed_h3_context.py` và `Ghe27AContext` đều đọc bản rebuilt.

**Shot cận cảnh (sửa sau G03):** với `shot_size` = `close-up`/`ui`, tự động **loại khỏi prompt**
mọi prop/geometry nằm ngoài khung (TV, ghế, toàn thân nhân vật, bàn đầy đủ) — chỉ giữ cái nhìn
thấy trong khung. Không dùng câu phủ định ("no cake", "no candles") để xóa prop khỏi ảnh anchor:
H3 local cố xóa vật đang có trong frame đầu → vật tan biến. Thay bằng **soạn anchor INS riêng**
có bố cục đúng (xem `h3-storyboard` rule cỡ cảnh anchor).

**Cấm câu phủ định xoá vật/màu trong `prompt_visible` (duyệt 25/11):** không viết
`no plant`, `NO red anywhere in this shot`, `no cake`, `no candles`, `no visible text...` vào prompt
gửi H3. H3 local vẽ vật bị phủ định hoặc bị priming bởi màu bị cấm (G02: plate có chậu cây + nến đỏ
dù prompt cấm). Giữ các fact này ở `global-context.json` cho linter/QA đối chiếu.
Style contract chỉ có **một bản**, đặt đầu `integrated_multimodal_description`; feeder và custom
node không được chèn bản thứ hai trước field (gây nhân đôi, loãng trọng số).

**Tên nhân vật trong wardrobe (duyệt 25/11):** mỗi clause phải là `<cid>: appearance + wardrobe`
(WS/MS) hoặc `<cid>: appearance + upper_wardrobe` (CU/INS). Cấm để đoạn quần/áo rời rạc không chủ
nhân — H3 không map được ai mặc gì (lỗi G02).

**Mục đích:** tạo prompt text để inject vào `{{PROMPT}}` của `h3-master.json` qua
`art/comfy/prompts/partN/<shot>.txt`. Không tạo file prompt rời rạc ngoài chỗ đó. Mọi chi tiết
dùng chung (style, set continuity, wardrobe, voice) lấy từ `art/env/global-context.json`, không
viết lại ở mỗi shot. Output phải giữ nguyên 3 field (base) hoặc 6 (Ref2VA) + dòng first-frame.

## Continuous motion (25/11 — bắt buộc)

H3 không tự thêm chuyển động: frame 1 tư thế trung tính + "camera static" = clip đứng im, phải
re-time bằng tay. Mọi prompt phải có 3 lớp chuyển động:

1. **Camera:** mặc định slow push-in 2–4% hoặc handheld drift nhẹ. `static` chỉ được viết thành
   `locked-off tripod with a slow breathing drift` (kèm sway), không bao giờ "camera static".
2. **Môi trường:** light flicker, bóng đổ bò, bụi lơ lửng — nêu rõ trong câu, không để H3 tự nghĩ.
3. **Chủ thể — 3 nhịp:** `At 00:00.000` (đang giữa động tác) → `At ~45%` duration (đổi trọng tâm,
   quay đầu) → `At ~end` (chốt nhịp, camera vẫn trôi). Timecode phải **tăng dần**, nhịp cuối
   ≤ duration. Motion beat dùng chung timeline với dialogue; trùng giờ thì đẩy 50 ms — linter FAIL
   nếu timecode không tăng.

**Frame 1 phải là mid-action:** chọn/anchor ở tư thế đang cử động (tay đang nâng, đầu đang quay),
không phải đứng thẳng nhìn camera. H3 nối tiếp tư thế idle bằng cách giữ idle.

**`first_frame_reference` ≠ khoá frame 1.** Trong `FreeVideoGenerate` nó chỉ có tác dụng khi
`continue_from` được set (clip nối tiếp): engine thu frame đầu phim còn ~384 px cạnh ngắn rồi đưa
vào như *reference* để giảm drift giữa các part — không pixel-lock, không giảm biên độ chuyển
động. Với I2V thường, input `first` mới khoá frame 1; muốn cử động thì mô tả bằng beat, không tắt
flag. `two_pass` (mặc định true) chỉ đổi cách sample (8 bước hạ res → upscale latent → 3 bước
refine), không ảnh hưởng chuyển động.

## Frame-1 và ánh sáng (rule đã duyệt, 25/11)

- **Câu mở đầu frame 1 (E093):** không viết `at 0.00 seconds <Picture 1> is fully referenced` —
  H3 mở video bằng chính ảnh key (sheet hồng) thay vì plate. Dùng
  `Start from the supplied first-frame image as frame 0 of the target video; keep its composition
  and background at the start of the shot.` và để plate ở **picture slot 1**.
- **Không phủ định dày đặc ánh sáng (E096):** `NO beam, NO spotlight, NO gradient, NO shadow` làm
  H3 vẽ đúng cái bị nhắc (G02: beam amber + gradient). Thay cả cụm bằng một câu khẳng định ngắn:
  `flat uniform colour lighting`. Chi tiết cấm/cho phép giữ ở `global-context.json` cho QA, không
  nhồi vào `prompt_visible`.

## UI / black-screen shots (duyệt 25/11, ca G01)

- **Một câu text duy nhất.** Shot có `allow_text` phải gộp vào contract:
  `no text except the on-screen timer 00:00`. Không thêm dòng `Visible text allowed only: ...` ở
  cuối — hai câu ngược nhau và H3 tự chọn. Linter FAIL nếu còn câu đó.
- **Nêu màu cụ thể:** waveform **bone white** trên nền `flat near-black navy`, chấm ghi âm **red**,
  timer bone white. Chỉ ghi "waveform" trên nền navy thì nó chìm vào nền.
- **Không handheld sway** trên graphic phẳng (chỉ push-in 2–4%); sway chỉ dành cho cảnh có người.
- **Tiếng Anh cho hành động:** mô tả scene/UI viết bằng tiếng Anh (sinh từ `spec.ui`: `rec_wave`,
  `clock`); tiếng Việt chỉ nằm trong `<d>[Vietnamese] ...</d>`, nếu không H3 đọc phần mô tả như lời.
- **Chỉ chèn khi có nhân vật:** câu `lips remain completely closed` và SFX bed (`quiet breathing`,
  throat-clear) bỏ khỏi shot không có người trên khung — H3 sẽ đi tìm người để vẽ.

## Workflow

1. Identify the input mode: T2VA, I2VA, FL2VA, L2VA, or full-reference Ref2VA.
2. For base text/keyframe modes, read `references/base-en.txt` and follow its final prompt structure.
3. For full-reference mode, read `references/ref-en.txt` and follow its six-section rewrite format.
4. Preserve the exact field names, section order, labels, and timing notation from the selected guide.

## Base Modes

- T2VA: build the full audiovisual timeline from text.
- I2VA: start from the first frame and develop forward from it.
- FL2VA: describe the continuous path between the first and last frames.
- L2VA: infer a plausible opening and converge to the supplied last frame.

Use `integrated_multimodal_description`, `overall_soundscape`, and `non_diegetic_music` in the order shown in `references/base-en.txt`.

## Full-Reference Mode

Ref2VA rewrites use `subject_definitions`, `summary`, `retention_analysis`, `detailed_description`, `overall_soundscape`, and `non_diegetic_music` in that order. Reference labels stay consistent across all sections.

Read `references/ref-en.txt` for label rules, retention analysis, and complete examples.

## Output Rules

- Write rewrite sections in English; preserve dialogue, lyrics, and visible scene text in their original language.
- Describe each shot by composition, subjects, environment, actions, camera, sound, and the exact point where referenced content appears.
- Avoid plot summaries, unresolved reference labels, and timing that does not match the requested duration.
## Tips for Better Results
- Always match the total duration of the description to the requested video length (4–15 seconds).
- Keep reference labels consistent (e.g. `<Picture 1>`, `<Video 1>`, `<Audio 1>`) across every section.
- Prefer concrete visual and audio details over abstract words like "cinematic" or "beautiful".
- When using keyframes (I2VA / FL2VA / L2VA), clearly state how the first and/or last frame connects to the timeline.
- Keep the subject moving for the whole clip: a mid-action Frame 1 plus 2–3 timed beats (camera drift and environment motion included) reads better than a locked camera and a neutral pose.
