# Hướng Dẫn Sử Dụng AI Video Generator

## Giới Thiệu

Đây là công cụ tạo video AI tự động chạy trên Windows. Bạn chỉ cần nhập danh sách các phân cảnh (scene), công cụ sẽ gọi API của các dịch vụ AI tạo video để sinh ra từng video ngắn, tự động tải về máy tính.

**Điểm đặc biệt:** Sử dụng ChatGPT làm "đạo diễn AI" để đảm bảo nhân vật, bối cảnh, phong cách nhất quán xuyên suốt tất cả các phân cảnh.

---

## Yêu Cầu Hệ Thống

- **Windows 10/11**
- **Python 3.10** trở lên
- **ffmpeg** (chỉ cần nếu bật Frame Chaining)
- **Kết nối internet**

---

## Cài Đặt

### Bước 1: Cài thư viện Python
```bash
cd C:\Users\Windows\Desktop\tool-video
pip install -r requirements.txt
```

### Bước 2: Cài ffmpeg (tuỳ chọn)
```bash
winget install ffmpeg
```
Hoặc tải từ https://ffmpeg.org/download.html

### Bước 3: Chạy phần mềm
```bash
python main.py
```

---

## Cấu Hình API Keys

Nhấn nút **Settings** ở góc phải trên để mở cửa sổ cài đặt.

### Các API key cần thiết:

| Dịch vụ | Bắt buộc? | Lấy key tại | Mục đích |
|---------|-----------|-------------|----------|
| OpenAI (ChatGPT) | Có | https://platform.openai.com/api-keys | Xử lý và đồng bộ prompt |
| Google Veo 3 | 1 trong 4 | https://aistudio.google.com | Tạo video |
| Runway Gen-4 | 1 trong 4 | https://dev.runwayml.com | Tạo video |
| Kling AI | 1 trong 4 | https://app.klingai.com | Tạo video |
| Minimax Hailuo | 1 trong 4 | https://platform.minimax.io | Tạo video |

> **Tối thiểu cần:** 1 key OpenAI + 1 key video provider.

### Kiểm tra key:
Nhấn nút **Test** bên cạnh mỗi ô nhập key để kiểm tra key có hợp lệ không.
- Hiện **xanh lá** = key hợp lệ
- Hiện **đỏ** = key sai hoặc hết hạn

### Lưu key:
Nhấn **Save Settings**. Key được lưu vào `~/.ai-video-tool/config.json`, chỉ cần nhập **một lần duy nhất**, lần sau mở app sẽ tự động nạp lại.

---

## Cách Sử Dụng

### 1. Chọn Cài Đặt Tạo Video

| Tuỳ chọn | Mô tả |
|----------|-------|
| **Provider** | Chọn dịch vụ AI tạo video (Kling AI, Minimax, Runway, Veo 3) |
| **Resolution** | Độ phân giải: 720p hoặc 1080p |
| **Duration** | Thời lượng mỗi video: 5, 8 hoặc 10 giây |
| **Output** | Thư mục lưu video trên máy tính |

### 2. Bật/Tắt Các Tính Năng

| Tính năng | Mô tả |
|-----------|-------|
| **Frame Chaining** | Lấy khung hình cuối của video trước làm đầu vào cho video sau, giúp chuyển cảnh mượt mà |
| **ChatGPT Enhance** | Dùng ChatGPT để viết lại prompt chi tiết hơn, đồng bộ nhân vật và phong cách |
| **Seed** | Số seed cố định giúp AI tạo phong cách tương tự giữa các video |

### 3. Thêm Ảnh Tham Chiếu (Tuỳ Chọn)

Phần **Reference Images** cho phép tải lên ảnh mẫu:

#### Ảnh Chủ Thể (Subject / Character)
- Tải lên ảnh nhân vật chính, con vật, đối tượng chính trong video
- Ví dụ: Ảnh khủng long T-Rex, ảnh nhân vật chính
- AI sẽ dùng ảnh này làm tham chiếu để giữ hình dáng nhất quán

#### Ảnh Bối Cảnh (Background / Scene)
- Tải lên ảnh phong cảnh, bối cảnh mong muốn
- Ví dụ: Ảnh rừng cổ đại, bãi biển, thành phố
- AI sẽ dùng ảnh này để tạo bối cảnh tương tự

#### Thứ tự ưu tiên sử dụng ảnh:
1. **Frame Chaining** bật + có video trước → Dùng khung hình cuối của video trước
2. **Ảnh chủ thể** được tải lên + là cảnh đầu tiên → Dùng ảnh chủ thể
3. **Ảnh bối cảnh** được tải lên → Dùng ảnh bối cảnh
4. Không có ảnh nào → Tạo video từ văn bản thuần

### 4. Nhập Prompt Các Phân Cảnh

Có 2 cách nhập:

#### Cách 1: Nhập trực tiếp
Gõ vào ô **Scene Prompts**, mỗi phân cảnh cách nhau bằng tiêu đề `Scene X –`:

```
Scene 1 – Bối cảnh mở đầu Phong cảnh kỷ Phấn Trắng lúc bình minh,
đồng bằng ngập sương mù, núi lửa xa xa tỏa khói nhẹ,
rừng thông rậm rạp, ánh sáng vàng điện ảnh xuyên qua mây

Scene 2 – Không khí rừng Rừng tiền sử rậm rạp với thông cao
và dương xỉ, sương mù ẩm buổi sáng, côn trùng bay
trong ánh nắng dịu, camera đẩy tới chậm

Scene 3 – T-Rex ngủ Khủng long T-Rex khổng lồ nằm nghỉ
dưới tán cây cao, ẩn trong bóng râm, lồng ngực
phập phồng thở chậm, ánh sáng sáng sớm lọt qua lá
```

> Công cụ tự động nhận diện `Scene X –` là điểm bắt đầu phân cảnh mới. Các dòng tiếp theo được gom vào cùng một phân cảnh.

#### Cách 2: Nhập từ file
Nhấn **Import TXT / CSV** để tải file:

**File TXT:**
```
Scene 1 – Tiêu đề Mô tả chi tiết phân cảnh...
Scene 2 – Tiêu đề Mô tả chi tiết phân cảnh...
```

**File CSV:**
```csv
scene,prompt,duration
1,Phong cảnh kỷ Phấn Trắng lúc bình minh,8
2,Rừng tiền sử rậm rạp với thông cao,8
```

### 5. Tăng Cường Prompt Bằng ChatGPT (Khuyến Nghị)

Nhấn nút **Enhance Prompts (ChatGPT)**.

ChatGPT sẽ tự động:
1. **Tạo Character Bible** – Mô tả chi tiết ngoại hình từng nhân vật (màu da, vảy, kích thước, đặc điểm nhận dạng). Mô tả này sẽ giống hệt nhau ở mọi phân cảnh.
2. **Tạo Style Guide** – Bộ từ khoá phong cách thống nhất (ánh sáng, màu sắc, ống kính, tâm trạng).
3. **Viết lại prompt** – Mỗi phân cảnh được viết lại chi tiết bằng tiếng Anh, tối ưu cho AI tạo video.
4. **Thêm gợi ý chuyển cảnh** – Tư thế kết thúc của cảnh trước khớp với tư thế bắt đầu cảnh sau.
5. **Dịch tự động** – Nếu bạn viết tiếng Việt, ChatGPT sẽ dịch tự nhiên sang tiếng Anh.

Kết quả hiển thị trong ô **Enhanced Preview**. Bạn có thể xem và chỉnh sửa trước khi tạo video.

**Chi phí:** Khoảng $0.02 cho 10 phân cảnh (rất rẻ).

### 6. Tạo Video

Nhấn nút **Generate All Videos**.

Hộp thoại xác nhận sẽ hiện:
- Số lượng video
- Nhà cung cấp được chọn
- Chi phí ước tính
- Thư mục lưu

Nhấn **Yes** để bắt đầu.

### 7. Theo Dõi Tiến Trình

Trong quá trình tạo video:

| Thành phần | Mô tả |
|------------|-------|
| **Thanh tiến trình** | Hiển thị phần trăm hoàn thành tổng thể |
| **Bảng trạng thái** | Mỗi phân cảnh hiển thị: Pending → Submitting → Generating → Downloading → Done |
| **Nhật ký (Log)** | Chi tiết từng bước: gửi API, polling, tải về, lỗi |

Màu sắc trạng thái:
- **Xám** = Đang chờ (Pending)
- **Cam** = Đang gửi (Submitting)
- **Xanh dương** = Đang tạo (Generating)
- **Xanh lá** = Hoàn thành (Done)
- **Đỏ** = Thất bại (Failed)

### 8. Kết Quả

Video được lưu trong thư mục đầu ra với tên:
```
1.mp4
2.mp4
3.mp4
...
63.mp4
```

Mỗi file tương ứng với một phân cảnh theo đúng thứ tự.

---

## Luồng Hoạt Động Chi Tiết

```
Bạn nhập prompt (tiếng Việt hoặc Anh)
         │
         ▼
┌─────────────────────────────────┐
│   ChatGPT API (gpt-4o)         │
│                                 │
│   • Tạo Character Bible        │
│   • Tạo Style Guide            │
│   • Viết lại prompt chi tiết   │
│   • Dịch sang tiếng Anh        │
│   • Thêm gợi ý chuyển cảnh    │
└─────────────────────────────────┘
         │
         ▼
   Bạn xem & chỉnh sửa prompt
         │
         ▼
┌─────────────────────────────────┐
│   Video AI API                  │
│   (Veo 3 / Runway / Kling /    │
│    Minimax)                     │
│                                 │
│   Cảnh 1: text-to-video        │
│     → tải về 1.mp4             │
│     → trích xuất khung cuối    │
│                                 │
│   Cảnh 2: image-to-video       │
│     (dùng khung cuối cảnh 1)   │
│     → tải về 2.mp4             │
│     → trích xuất khung cuối    │
│                                 │
│   Cảnh 3: image-to-video       │
│     (dùng khung cuối cảnh 2)   │
│     → tải về 3.mp4             │
│     → ...tiếp tục              │
└─────────────────────────────────┘
         │
         ▼
   Tất cả video lưu trong thư mục
   1.mp4, 2.mp4, 3.mp4 ...
```

---

## 5 Kỹ Thuật Đồng Bộ Liên Mạch

Công cụ sử dụng 5 kỹ thuật để đảm bảo video các phân cảnh nhất quán:

### 1. ChatGPT Prompt Engine
- Tự động tạo **Character Bible** mô tả chi tiết nhân vật
- Mọi phân cảnh đều chứa cùng mô tả nhân vật → AI tạo hình giống nhau
- Áp dụng cùng **Style Guide** cho mọi phân cảnh

### 2. Frame Chaining (Nối Khung Hình)
- Trích xuất **khung hình cuối** của video cảnh trước
- Dùng làm **khung hình đầu** của video cảnh sau
- Giúp chuyển cảnh mượt mà, bối cảnh liên tục
- Yêu cầu: cài ffmpeg

### 3. Ảnh Tham Chiếu Chủ Thể
- Tải lên ảnh nhân vật/đối tượng chính
- AI dùng ảnh này làm mẫu để tạo nhân vật giống nhau ở mọi cảnh
- Đặc biệt hữu ích cho cảnh đầu tiên (chưa có frame chaining)

### 4. Ảnh Tham Chiếu Bối Cảnh
- Tải lên ảnh phong cảnh/bối cảnh mong muốn
- AI tạo cảnh với màu sắc, ánh sáng, không gian tương tự

### 5. Seed Cố Định
- Đặt cùng số seed cho tất cả các cảnh
- AI tạo phong cách, tông màu tương tự

---

## So Sánh Nhà Cung Cấp

| Nhà cung cấp | Giá/video (8s) | Chất lượng | Tốc độ | Ghi chú |
|--------------|---------------|------------|--------|---------|
| **Kling AI** | ~$0.05 | Cao | Nhanh | Rẻ nhất, phù hợp test |
| **Minimax Hailuo** | ~$0.05 | Cao | Nhanh | Rẻ, hỗ trợ first/last frame |
| **Runway Gen-4** | ~$0.40 | Rất cao | Nhanh | Chất lượng tốt |
| **Google Veo 3** | ~$1.20-4.00 | Rất cao | Trung bình | Đắt nhất, chất lượng cao nhất |
| **ChatGPT** | ~$0.02/10 cảnh | - | Rất nhanh | Xử lý prompt |

### Ước tính chi phí cho 63 phân cảnh:
- Kling AI: **~$3.15**
- Minimax: **~$3.15**
- Runway: **~$25.20**
- Veo 3 Fast: **~$75.60**
- Veo 3 Standard: **~$252.00**

---

## Xử Lý Sự Cố

### "ffmpeg not found"
- Cài ffmpeg theo hướng dẫn ở trên
- Hoặc tắt **Frame Chaining** nếu không cần

### "No API key"
- Mở **Settings** và nhập key
- Nhấn **Test** để kiểm tra

### "429 - Quota exceeded"
- Tài khoản hết credit/quota
- Nạp thêm credit hoặc đợi quota reset
- Hoặc đổi sang nhà cung cấp khác

### "Submit FAILED"
- Kiểm tra key hợp lệ (nhấn Test trong Settings)
- Kiểm tra kết nối internet
- Thử lại hoặc đổi provider

### Video bị lỗi giữa chừng
- Nhấn **Stop** để dừng
- Các video đã tải xong sẽ được giữ nguyên
- Nhấn **Generate All** lại → công cụ tự động bỏ qua các cảnh đã hoàn thành, tiếp tục từ cảnh đang dở

### Muốn tạo lại 1 cảnh cụ thể
- Xoá file video tương ứng (ví dụ: xoá `5.mp4`)
- Chạy lại → cảnh 5 sẽ được tạo lại

---

## Cấu Trúc Thư Mục Dự Án

```
tool-video/
├── main.py                    # Điểm khởi động
├── gui/
│   ├── app.py                 # Giao diện chính
│   ├── settings_dialog.py     # Cửa sổ cài đặt API key
│   └── prompt_editor.py       # Ô nhập và import prompt
├── providers/
│   ├── base.py                # Lớp cơ sở cho các nhà cung cấp
│   ├── veo3.py                # Google Veo 3
│   ├── runway.py              # Runway Gen-4
│   ├── kling.py               # Kling AI
│   └── minimax.py             # Minimax Hailuo
├── core/
│   ├── prompt_engine.py       # ChatGPT xử lý prompt
│   ├── task_manager.py        # Quản lý hàng đợi và tải video
│   ├── frame_utils.py         # Trích xuất khung hình (ffmpeg)
│   └── config.py              # Lưu/đọc cài đặt
├── requirements.txt           # Thư viện cần cài
├── HUONG_DAN.md               # File này
└── PLAN.md                    # Kế hoạch kỹ thuật
```
