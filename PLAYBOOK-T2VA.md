# PLAYBOOK T2VA — bản hiệu chỉnh cho pipeline ĐỪNG THƯA (27/11/2026)

Nguồn: `PLAYBOOK-upstream.md` (fetch từ `lehoang7438/Minimaxh3_AI_Learning_hook`).
Upstream mô tả nhánh chain4/ComfyUI 10 s (G01–G05); **đây là bản đã map sang T2VA 67 shot**
(704×1280, 24 fps, 158 frames fresh / 175-22 continue, một shot một QA gate).

> Đây là **chỉ mục rule đã adapt**, không copy y nguyên: chỉ giữ rule có bằng chứng QA ngay trên pipeline
> T2VA này; bỏ chain4/10 s, bỏ E278/E279, bỏ face-flat cấm lông mày/ngón tay (user relax #1).
> Luật gốc vẫn ở `AGENTS.md` + SKILL.md + `learning_system/events/events.jsonl`.
> Không promote rule upstream lên hard gate khi chưa có bằng chứng QA trên pipeline này.

---

## 1. Truth order & sửa đúng 1 lớp

`art/part1-spec.json` → SKILL.md → ALH accepted → QA (máy + hy4 + agent chốt).
`global-context*.json` / `art/t2v/*/prompt.txt` là **output**, không phải nguồn sự kiện.

FAIL → truy ngược: *spec → composer/prompt → runner/workflow → gate → file trên đĩa → log*.
Sửa **đúng 1 lớp**, rồi render lại **chính shot đó** với **seed mới** (cache trả clip cũ nếu trùng prompt+seed).
Cấm vá video bằng code, cấm vẽ/keyframe bằng PIL, cấm hand-patch frame.
Chỉ hỏi user khi đã có bằng chứng + kết luận, hoặc chạm trần retry.
**Adapt riêng T2VA (ALH `c8f31ee2`):** trước khi restart driver, liệt kê process và đảm bảo driver cũ đã thoát hẳn;
hai driver chồng nhau va chạm `out/t2v/<G>.artifacts` (`FileExistsError WinError 183`), không sửa prompt hay asset khi lỗi này.

## 2. Rule mang sang được (đã có bằng chứng trên pipeline này)

| Rule | Nội dung | Trạng thái ở đây |
|---|---|---|
| E234 / E271 | Truy ngược 6 bước; auto-chốt PASS khi sạch, chỉ hỏi khi FAIL có bằng chứng | đang áp dụng |
| E273 + E275 | **Pre-fix trước render** các shot cùng plate/light: đưa trạng thái sáng bất biến lên **đầu** style contract; bỏ `Light:` trùng | áp dụng từ G04 (bài học G02 3 lần / G03 2 lần). **Adapt thêm (ALH `90461a0d`):** không dùng câu "already fully visible at frame one / identical width" — H3 hiểu là sự kiện bật đèn và mở cửa. Dùng mô tả tĩnh "a thin flat solid teal line ... for the whole shot" |
| h3-storyboard close-up | Close-up/Locked-off **loại prop ngoài khung khỏi prompt**; danh sách cả phòng priming H3 render thành wide | áp dụng từ G04 (lỗi G03 v1) |
| E162 / E200 | Cấm câu phủ định xoá vật/màu (`no lamp`, `NO red anywhere`); giữ fact trong metadata cho QA | đang áp dụng |
| E226 | Không path `.png` trong prompt; tiếng Việt **chỉ** trong `<d>[Vietnamese] …</d>` | đang áp dụng |
| E281 | Timecode phải tăng dần và ≤ duration; beat cuối không vượt clip | đang áp dụng |
| ALH E114 | Đổi seed khi sửa prompt/media/context | đang áp dụng |
| Frame math | 158 frames = 6.583 s; continue 175 → 153 mới sau overlap 22; canvas 704×1280 | đang áp dụng |
| Adapt C4 (27/11, user) | `continue_from` **được phép cắt cảnh bên trong clip** khi mục đích là khóa giọng: dùng record G02 làm voice reference. Engine trim **0.917 s đầu của cả video lẫn audio** (`frames[22:]`, `audio_latents*800`), nên mọi timecode quan trọng phải dời +0.917 s so với bản fresh: cú cắt ≥00:01.000, VO ≥00:01.417 trên timeline sinh 175 frame. upstream C4 cấm nối qua cắt → **chỉ adapt cho voice-lock**, không áp cho chain thường | áp dụng G03 attempt 5 |
| Voice reference | Engine chỉ xét `--voice-reference` khi có `--continue-from`; lấy 6 s audio đầu clip nguồn (G02). `dialogue_reason()` trả `None` = **đủ điều kiện** (chỉ `no_lines`/`singing` mới chặn); route `t2va + sound + 1 audio ref` đã validate. Kiểm tra report `voice_reference.used = true` sau render. Bằng chứng G03: `out/t2v/G03.request.json → /voice_reference = {requested:true, used:true, reason:null}` và `G03.engine.json → conditioning_info.reference_audio_tokens = 480` ở **cả 2 sampling pass**; user nghe lại xác nhận giọng khớp G01/G02. Voice ref chỉ khóa timbre — thời lượng vẫn do số frame quyết định | đã đóng lớp giọng G03 |
| User verdict is final (27/11, G03) | hy4-flash-free/advisory reviewer FAIL **does not override** the user's eye verdict. When the user says a clip is acceptable (even "tạm dùng đc"), record the reviewer's objections as `warnings` in `art/qa/t2v-approved/<shot>.json`, set status `PASS_WITH_WARN` (driver treats it as PASS), and continue — do not burn a re-render. Voice layer already confirmed by the user must stay closed | G03 attempt 5 seed 2026114603 |
| G04 light contract (27/11) | Bốn câu nói sáng rời rạc vẫn để H3 bật dần fill (luma 75→80→101). Giữ **đúng 1** câu ở đầu field 1, nêu rõ *colour + brightness + direction + first frame to last frame*; xoá mọi câu lặp (`Flat uniform…`, `The light stays flat…`, `flat and still`). FAIL → sửa layer prompt, seed mới, không vá video | áp dụng từ G04 attempt 2 |
| Driver stale-clip gate (27/11) | Engine từ chối ghi đè (`FileExistsError`), nhưng `run.ps1` không `exit $LASTEXITCODE` nên PowerShell trả 0 và driver probe **clip cũ**. Đã vá driver: xoá output cũ trước generate + propagate exit code + so sánh `nb_frames` với `expected_frames` | đã vá trong `run_t2v_workflow.py` |
| Hy4 | Đọc ảnh/read-only, trả mô tả + phát hiện; **agent đối chiếu metric rồi mới chốt verdict** | đang áp dụng |
| Machine QA có điểm mù (G03) | `frame_qa.py` đo màu/độ phẳng **toàn khung** nên không bắt được (a) vệt sáng/teal **mới xuất hiện ở mid** và (b) cỡ cảnh lùi từ insert sang wide. Luôn giao hy4 soi first/mid/last, agent mới chốt | đã áp dụng G03→G04 |
| Smart chain cut (user duyệt 27/11) | H3 cắt trong chain qua `--continue-from` **chỉ khi** cùng chain + cùng `set` + cùng lighting tier + không ranh giới UI đen; nhảy môi trường (yard/bedroom/phone_ui/under_bed/flashback) hoặc tier sáng (morning/night/warm_flashback/unprotective) → fresh. Tool `art/tests/smart_chain.py` (read-only): 0 downgrade của 16 shot đã nối, 17 shot đủ điều kiện nối thêm. Đổi mode → 175 frame/153 output, dời beat +0.917 s, seed mới, lint lại | rule bắt buộc trong `freevideo-runner/SKILL.md` §8.6 |
| Chain QA theo run_position | `art/t2v/plan.json` có 10 chain (`chain-home` G01–G05, `chain-flashback` G06–G09, … `chain-morning` G61–G67). Sau khi chain cuối cùng được approve: xem liền first/mid/last của cả chain (eyeline trục 180°, relative_height, trôi màu/ánh sáng, nhịp cắt không 3–4 shot cùng cỡ, khớp VO). Chỉ sửa spec/context của chain, không vá clip lẻ | lên lịch sau chain-home |

## 3. Rule upstream **KHÔNG áp dụng** (xung đột với quyết định user / pipeline khác)

- E278 archived, E279 revoked — đừng ép thứ tự awake→nod→đặt điện thoại, đừng re-render vì lý do đó.
- E280 `FACE_FLAT_CONTRACT` bỏ "tapered nose" / cấm eyebrows+fingers: **user relax #1 (27/11) chấp nhận lông mày, ngón tay, ngón chân** cho cả 67 shot; là soft note, không FAIL. Không re-add câu `no brows / no fingers / no nose`.
- Lệnh `chain4_run.py`, `art/comfy/chain4/*`, `.venv-tts`, 10 s, 192/243 frames: thuộc nhánh khác. Ở đây dùng `art/tests/run_t2v_workflow.py` + `art/t2v/<Gxx>/run.ps1`.
- Bảng trạng thái G01–G05 của upstream (G03 held-state, điện thoại trên đùi, 6 s/8 s): **khớp kịch bản khác**, không đem vào spec này.
- Ngưỡng color-count upstream (character 150/200, set 300/450): pipeline này dùng `frame_qa.py` (off-palette %, flatness, luma) + hy4; không trộn ngưỡng.
- Upstream C4 (`continue_from` chỉ nối hành động liên tục, không nối qua cú cắt) **không áp nguyên**: user chọn dùng `continue_from` G02 để khóa giọng rồi cắt cứng sang close-up trong chính clip G03. Giữ hướng này cho S1 narrator khi cần, nhưng vẫn cấm nối qua cắt ở các chain thông thường (G07/G08, G26, G29–G31, v.v.). E280 face-flat và E278/E279 vẫn bị loại như trên.

## 4. Gate cứng khi QA clip (không nới)

- Style: solid flat fills, **không gradient/shading/texture**, viền mực đen dày, palette navy/bone/one teal.
- Đỏ chỉ blood/infected eye/recording dot; shot không cho phép thì red% phải 0.
- Sai cỡ cảnh (wide thay close-up), sai nguồn sáng/shaft/bóng đổ, flicker/bật sáng giữa clip, ghosting/melt = FAIL.
- Set/prop continuity, một điểm nhìn, không chữ/watermark, motion > 0.25, 704×1280, 24 fps, AAC.
- Soft note: lông mày / ngón tay / ngón chân; noise texture nhẹ; deviation nhẹ đã được user chấp nhận.

## 5. Nhịp sản phẩm

`render 1 shot → machine QA → hy4 vision → agent chốt → ghi art/qa/t2v-approved/<G>.json → ALH → shot sau`.
Mỗi hoạt động kết thúc bằng: `Vừa xong:` … / `Bước kế:` … / `ALH:` ….
Cuối phim: integrate → final QA → giao file → `art/tests/sleep_pc.ps1`.
