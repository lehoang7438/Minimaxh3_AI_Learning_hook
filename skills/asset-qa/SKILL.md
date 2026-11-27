---
name: Asset QA
description: Kiểm tra tính logic và đúng đắn của asset mới gen (sau gen ảnh, trước khi đưa vào keyframe). Gọi ngay sau khi chạy gen_image.py.
---

# Asset QA

Dùng sau **mỗi lượt gen asset** bằng MiniMax H3 Image. Mục tiêu: bắt asset sai **trước khi** nó lan vào keyframe/phim.

**Mở rộng cổng (Tầng 2):** `qa_passed` + `color_count` áp dụng cho ** cả 3 loại ref** — character,
**set plate** và **prop** — không chỉ character. Ngoài màu/tay/wardrobe phải soi thêm **chữ rác,
chi tiết nhiễu, nền magenta dính viền**. Set/prop painterly cũng bị chặn trước khi vào
`global-context.json` — ngưỡng màu **theo loại ref** (xem bảng bên dưới), không dùng chung một số.

**Sync text↔ref:** nếu bible đổi tóc/trang phục, ref cũ không còn hợp lệ — gen lại bằng H3 Image với
prompt mô tả **đúng câu mới**, QA xong mới thay `refs[].path`. Không giữ ref tóc xù khi bible đã ghi
tóc gọn; không chấp nhận ref có ngón tay dù prompt nói mitten (phải sửa prompt/gen lại tối đa 2 lần).

**Cổng vào `global-context.json` (sửa sau ca G02).** Mọi ref — kể cả ref vừa gen lại bằng H3 — phải
qua Asset QA **trước khi** đăng ký làm canon. Không dùng **scene crop** làm canon character ref nếu
crop mang ánh sáng/bối cảnh/gradient hoặc kéo sai màu quần áo (`friend_beer.png` 439 màu,
`g02-khang-ref.png` 326 màu từng lọt vào context và kéo H3 sang painterly/teal).

Kiểm tra định lượng + định tính:

| Loại | Ngưỡng / yêu cầu |
|---|---|
| Canon flat ref | `qa_passed: true` là cổng chung. Ngưỡng màu **theo loại ref**: character WARN >150 / FAIL >200; set plate WARN >300 / FAIL >450 (nền phòng được phép vài sắc đèn nhưng vẫn flat fill); prop WARN >250 / FAIL >400. Dùng chung 1 ngưỡng gắt dễ chặn nhầm set sạch — mục tiêu là chặn ảnh crop painterly 300–450+ màu |
| Kích thước | sprite 1024×1024 sau downscale (H3 trả 2048²), nền 704×1280 |
| Nền key (character ref) | Phải **phẳng, đồng nhất, key-site chắc chắn**, band ≥95 %. H3 Image trên build này **không tạo nổi `#FF00FF` chính xác** (đã thử 2 lần: `#c61c79` raspberry rồi `(255,10,247)` near-magenta). User duyệt **near-magenta** cho character ref: chấp nhận corner `R≥240, G≤40, B≥230` sau downscale 1024², đo uniform ≥95 % và keyer corner-sampled cắt sạch. Key hồng **chỉ là nền tạm của ref nhận diện**; nền thật trong video lấy từ set plate QA, không lấy từ key này. Raspberry cũ (`B≈100–137`) vẫn **FAIL** — phải gen lại. Vẫn giữ cụm `exact FF00FF` trong prompt để kéo màu sát nhất |
| Bằng mắt | đúng flat fill, đúng wardrobe từ bible, tay **mitten** (không ngón), không eyebrow/mũi, không gradient |
| Gắn cờ | chỉ ghi `qa_passed: true` + `color_count` vào `refs[]` của `characters.json` **sau khi** qua hết các mục trên |

`build_global_context.py` copy các trường này sang `global-context.json`; `diagnose_shot.ps1` cảnh
báo nếu ref chưa `qa_passed` hoặc color count vượt ngưỡng.

**Tái sử dụng kho asset (duyệt 25/11):** trước khi gen mới, quét `art/assets/**` xem có asset nào đã QA và phù hợp yêu cầu (đúng nhân vật/đồ/key/đặt cạnh nguồn sáng) thì **dùng lại**, không gen lại. Chỉ gen khi không có asset phù hợp. Ghi rõ lý do vào ALH nếu vẫn phải gen.

**Vai trò:** QA quyết định asset có được đăng ký làm reference trong `art/env/global-context.json`
hay không. Chỉ gọi H3 Image khi workflow cần resource mà chưa có; FAIL thì sửa prompt/gen lại ảnh
đó. Không tạo ảnh "để sau này có thể dùng" và không tự vẽ asset bằng code.

## Quy trình (bắt buộc: kiểm tra NGAY sau mỗi asset)

**Không chờ hết lô mới soi.** Vòng lặp cho mỗi asset:

```
gen 1 asset → QA ngay asset đó → PASS? → gen asset tiếp theo
                              → FAIL? → sửa prompt → gen LẠI asset đó (tối đa 2 lần) → mới tiếp tục
```

Sau khi cả lô xong mới làm bước tổng hợp (contact sheet + soi lại toàn bộ).

### QA ngay sau từng asset (bắt buộc)
1. Kiểm tra kích thước: sprite `1024×1024`, nền `704×1280` (H3 luôn upscale ≥2048² → phải downscale).
2. `read` ảnh đó để nhìn trực tiếp — không dựng contact sheet cho bước này.
3. Đối chiếu ngay với `characters.json` + prompt vừa dùng (đúng nhân vật, đúng đồ, đúng nền magenta).
4. Nếu FAIL: ghi lỗi cụ thể, sửa đúng 1 điểm (thêm reference hoặc nhắc lại style), gen lại **asset đó**, rồi mới sang asset sau. Không để lỗi chạy tiếp sang asset khác.

### Logic nền — bố cục, ánh sáng, đồ vật (mới 24/11/2026)

Ba lỗi này H3 Image mắc đi mắc lại, phải soát **trước** khi chấp nhận một background:

| Lỗi | Dấu hiệu | Cách chặn |
|---|---|---|
| **Trang truyện nhiều khung** | ảnh ra lưới 4–6 panel, có đường kẻ trắng/đen chạy hết chiều ngang | `visual_qa.py` bắt tự động: ≥3 gutter full-frame = FAIL (bucket ASSETS). Prompt phải nói "one single continuous room, one viewpoint, full-frame background plate, not a page of panels, no grid, no borders" |
| **Đồ vật vô lý** | ghế không có chân tới sàn, bàn lơ lửng, vật không có mặt đỡ, 2 bánh sinh nhật, cửa sổ không có khung, đồ mọc trên người | Liệt kê đồ vật trong prompt theo **cặp "vật + mặt đỡ"** (chairs on the floor around the table, cake on the table center). Eyeball pass 2: mỗi vật phải có điểm tiếp xúc |
| **Ánh sáng không logic** | 2 hướng sáng ngược nhau, sáng không có nguồn, đèn màu ngoài palette (hồng/tím), bóng đổ ngược | Ghi `light` trong spec (`{"source": "windows-left", "color": "teal"}`); mọi nguồn sáng phải có vật thể phát sáng nhìn thấy; bóng phải cùng phía |

**Bố cục (composition) bắt buộc:** một background = **một cảnh, một điểm nhìn, một mặt phẳng
liên tục**. Cấm: chia panel, viền khung, chữ, watermark, 2 không gian khác nhau trong cùng ảnh.
Trục nhìn phải khớp với hậu cảnh sẽ dùng (ví dụ cabin nhìn dọc lối đi thì không được vẽ nhìn ngang).

**Đồ vật phải nhất quán giữa các shot:** bàn tròn 1 lần duy nhất, số ghế cố định, bánh + nến chỉ
một bộ, cửa khoang máy bay luôn cùng một kiểu. Nếu shot rộng đã nướng bánh vào nền thì **không**
chèn thêm prop bánh (`max_instances` trong spec).

### Quần áo (wardrobe) — kiểm bằng khai báo, không bằng pixel

Pixel không phân biệt được hai người cùng mặc navy, nên quy tắc là **khai báo**:

- `characters.json` mỗi nhân vật có `wardrobe_id`, `wardrobe_hex`, `forbidden_tokens`.
- Mỗi layer nhân vật trong spec **phải** có `"outfit": "<wardrobe_id>"`.
- `visual_qa.py` FAIL nếu `outfit` khác canon, WARN nếu thiếu khai báo.
- `forbidden_tokens` cấm lên hình: Khang không vest/jacket/scarf; nhiễm không giày; crew không t-shirt.
- Script điền: `art/tests/add_wardrobe_ids.py [part1 part2 part3]`.

<!-- phần QA cũ -->
### QA tổng hợp cuối lô
1. Dựng contact sheet: `python art/tests/asset_contact_sheet.py` → `out/storyboard/asset-contact-sheet.png`. Đọc grid bằng mắt.
2. Soi lại các asset từng lúc nghi ngờ.
3. Chạy measured check nếu có: `h3-visual-qa/scripts/visual_qa.py` (phần FRAMES) cho keyframe sau này.
4. Ghi bảng FAIL / WARN / PASS; chỉ gen lại asset FAIL còn sót.

## Danh mục kiểm tra

### Cấu trúc
- Mỗi file **đúng 1 nhân vật/đối tượng**; không sheet 2 hàng, không "neighbour bleed-through".
- Nền magenta phẳng `#FF00FF`, không gradient; crop không dính viền lạ.
- **Không tay ngón** (mittens), không thiếu/thừa chi, không đầu hoặc chân bị cụt.
- Rig sheet: các bộ phận tách rời, cùng tỉ lệ, đủ 4 miệng + 3 mắt theo prompt.

### Logic nhân vật (so với bible)
- Khang: tóc đen xù, mặt bone-white, 2 chấm mắt, 1 nét miệng, **áo navy, KHÔNG vest** — khớp `g02-khang-ref.png`.
- Vy: búi nâu, đồng phục navy có teal — khớp `vy_canon.png`.
- Bạn cầm bia / bạn vỗ tay: đúng người, không tráo đồ.
- Nhiễm: **chỉ mắt đỏ**, không đỏ lan toàn mặt; áo navy rách.
- Máu/gân đen: chỉ trong asset blood/veins; không dính vào nhân vật thường.

### Style bible (STORYTIME HORROR 2D v2)
- Flat fill, **không gradient/shading/texture/3D/realistic**.
- Viền đen đậm không đều; palette navy / bone-white / teal; đỏ chỉ cho blood/eyes/rec.
- Background: **không có người**, đúng 704×1280 sau downscale; sprite 1024×1024.
- Không chữ, không watermark, không logo.

### Kích thước & tên
- H3 Image luôn upscale canvas lên ≥2048² → phải downscale về spec (sprite 1024², nền 704×1280).
- Tên file khớp đường dẫn trong spec (`art/assets/<name>.png`).

## SCALE ANCHOR — làm đúng ngay từ đầu, không gen rồi mới sửa

**Nguyên tắc cốt lõi:** tỉ lệ cơ thể không được tự quyết định riêng cho từng nhân vật. Phải có **1 anchor do user chỉ định**, mọi nhân vật khác scale **tương đối** theo anchor đó.

- Anchor nằm trong `characters.json` → `scale_anchor`: nhân vật, **frame gốc do user chọn**, đường dẫn ref, tỉ lệ head:body, phần trăm frame chiếm.
- Ví dụ dự án này: user **không dùng Khang ở G01**, chọn **Khang ở G02** làm anchor → `g02-khang-ref.png`, 1:6, 85–90% frame.
- Mỗi character có `relative_height` (Khang 1.00, Vy 0.95, bạn 0.98–1.02, infected 1.00) = chiều cao anchor × ratio.

**Không coi asset đầu tiên tự sinh là canon.** Nếu user từ chối bản G01, phải **đổi anchor sang frame user chỉ định** rồi gen lại toàn bộ character theo anchor mới — không giữ bản cũ rồi vá adjective.

Prompt character LUÔN gắn anchor làm `<Picture 1>` (ref nhận diện riêng nếu cần → `<Picture 2>`):

```
Single full-body 2D character on a plain flat uniform magenta #FF00FF background, no vignette, no gradient.
ADULT HUMAN PROPORTIONS: head-to-body ratio 1:6, tall slim adult build, NOT chibi, NOT bobblehead, NOT doll-like.
Full body head to feet, figure fills 85-90% of frame height, head near top, feet near bottom, no cropped feet.
SAME scale and SAME body proportions as <Picture 1> (the scale anchor).
Height = <relative_height> x <Picture 1>. No fingers, no extra limbs.
```
Kèm `appearance` + `wardrobe` copy **nguyên văn** từ `characters.json`. Không dùng cụm "isolated element" cho character. Nếu user đổi anchor, cập nhật `scale_anchor` rồi gen lại — không chỉnh từng prompt riêng lẻ.

**Wardrobe logic (bắt buộc):** không để nhân vật nào mặc y hệt nhau. `wardrobe` trong bible đã phân theo vai trò: Khang sơ mi navy dài tay, Vy áo khoác + váy + khăn teal, bạn cầm bia áo navy + quần xám, bạn vỗ tay áo xám, nhiễm áo navy rách + chân trần, cơ trưởng áo phi công có cầu vai. Copy nguyên `wardrobe` — đừng thay bằng "navy shirt" chung chung.

## Quy tắc sửa
- Asset lỗi logic (sai trang phục, thừa tay, face drift) → thêm **1 ảnh reference đúng đặc điểm đang drift**, không thêm tính từ mới vào prompt.
- Asset lỗi style (painterly, 3D) → nhắc lại cụm "flat solid fills, no gradient, no shading, no texture, extra thick uneven black ink outline" rồi gen lại asset đó.
- Không xóa asset PASS để gen lại cả lô.
