# AI Video Generator Tool - Ke Hoach Chi Tiet

## Tong Quan
Desktop tool chay tren Windows, su dung Python + tkinter GUI.
Cho phep nhap danh sach prompt theo tung scene, goi API cua 4 AI video generation service,
tu dong tai video ve luu vao thu muc local.

**Diem noi bat**: Su dung **ChatGPT API (OpenAI)** lam "dao dien AI" de tu dong
dong bo nhan vat, boi canh, phong cach giua cac scene truoc khi gui den video API.

---

## Cau Truc Thu Muc

```
tool-video/
├── main.py                    # Entry point, khoi dong GUI
├── gui/
│   ├── __init__.py
│   ├── app.py                 # Main window (tkinter)
│   ├── settings_dialog.py     # Dialog nhap API keys (5 keys)
│   └── prompt_editor.py       # Widget nhap/import prompt
├── providers/
│   ├── __init__.py
│   ├── base.py                # Abstract base class cho video providers
│   ├── veo3.py                # Google Veo 3 API
│   ├── runway.py              # Runway Gen-4 API
│   ├── kling.py               # Kling AI API
│   └── minimax.py             # Minimax Hailuo API
├── core/
│   ├── __init__.py
│   ├── prompt_engine.py       # ★ ChatGPT prompt processor (CORE MOI)
│   ├── task_manager.py        # Quan ly hang doi, polling, download
│   ├── frame_utils.py         # Extract last frame tu video (ffmpeg)
│   └── config.py              # Load/save API keys va settings
├── requirements.txt
└── .env.example
```

---

## ★ TINH NANG MOI: ChatGPT Prompt Engine (Dong Bo Lien Mach)

### Vai tro
ChatGPT API dong vai tro **"dao dien AI"** - nhan danh sach scene tho tu user,
xu ly va tra ve bo prompt hoan chinh, dam bao lien mach ve nhan vat, boi canh,
phong cach xuyen suot tat ca scenes.

### 5 Chuc Nang Chinh

#### 1. Auto Character Bible
User chi can viet prompt don gian, ChatGPT tu dong trich xuat va tao Character Bible:

```
User nhap:
  Scene 1: Co gai di dao tren bai bien
  Scene 2: Co gai ngoi uong ca phe

ChatGPT tu dong tao:
  [Character Bible]
  Main character: Young Vietnamese woman, early 20s, long flowing black hair,
  wearing a white linen dress, slender build, soft brown eyes, gentle smile.
  Skin tone: warm light tan.
```

#### 2. Scene Prompt Enhancement
ChatGPT nhan tung scene prompt tho → viet lai thanh prompt chi tiet,
toi uu cho video AI, giu nhat quan voi Character Bible:

```
Input:  "Co gai di dao tren bai bien"

Output: "A young Vietnamese woman with long flowing black hair and white
linen dress walks barefoot along a sandy beach. Golden hour sunlight
casts warm shadows. Gentle waves lap at her feet. Camera: medium shot,
tracking left to right. Style: cinematic, shallow depth of field,
warm color grading, shot on 35mm film."
```

#### 3. Scene Transition Hints
ChatGPT them goi y chuyen canh de video muot hon:

```
Scene 1 ending hint: "...she turns to look at the horizon (END: facing right)"
Scene 2 starting hint: "(START: facing right) She sits down at the cafe..."
```

→ Dam bao huong nhin, tu the, vi tri nhat quan giua 2 scene.

#### 4. Style Consistency
ChatGPT ap dung cung style keywords cho moi scene:

```
Global style: "cinematic, warm color grading, golden hour,
shallow depth of field, 35mm film aesthetic, 24fps"

→ Duoc them vao CUOI moi scene prompt
```

#### 5. Prompt Translation
Neu user viet tieng Viet → ChatGPT tu dong dich sang tieng Anh
(video AI hoat dong tot nhat voi prompt tieng Anh)

### API Call Flow

```
User prompts (tho, co the tieng Viet)
        │
        ▼
┌──────────────────────────────┐
│   ChatGPT API (gpt-4o)      │
│                              │
│  System prompt:              │
│  "Ban la dao dien phim.     │
│   Nhan danh sach scene,      │
│   tao Character Bible,       │
│   viet lai prompt chi tiet,  │
│   dam bao lien mach."        │
│                              │
│  Input: raw scene list       │
│  Output: JSON structured     │
│  {                           │
│    character_bible: "...",   │
│    style_prefix: "...",      │
│    scenes: [                 │
│      {                       │
│        id: 1,                │
│        original: "...",      │
│        enhanced_prompt: ".",│
│        transition_note: ".."│
│      }, ...                  │
│    ]                         │
│  }                           │
└──────────────────────────────┘
        │
        ▼
Enhanced prompts → GUI hien thi de user review/chinh sua
        │
        ▼
Gui den Video AI API (Veo3 / Runway / Kling / Minimax)
```

### Chi phi ChatGPT
- Model: `gpt-4o` (~$2.50/1M input tokens, ~$10/1M output tokens)
- Moi lan xu ly 10 scenes ~ 2000 tokens → **~$0.02** (rat re)
- Co the dung `gpt-4o-mini` de tiet kiem hon (~10x re hon)

---

## 5 Ky Thuat Dong Bo Lien Mach

| # | Ky thuat | Mo ta | Ai xu ly |
|---|----------|-------|----------|
| 1 | **ChatGPT Prompt Engine** | Tu dong tao Character Bible, enhance prompt, dich sang EN | ChatGPT API |
| 2 | **Frame Chaining** | Last frame scene N → first frame scene N+1 | Tool (ffmpeg) |
| 3 | **Reference Image** | 1 anh nhan vat dinh kem moi scene | User cung cap |
| 4 | **Consistent Seed** | Cung seed number → style tuong tu | Video API |
| 5 | **Style Prefix** | ChatGPT tao 1 style chung, ap dung moi scene | ChatGPT API |

### Frame Chaining Chi Tiet
```python
# core/frame_utils.py
# Dung ffmpeg de lay frame cuoi cua video
def extract_last_frame(video_path: str) -> str:
    """Tra ve duong dan anh last frame (PNG)"""
    output = video_path.replace('.mp4', '_lastframe.png')
    # ffmpeg -sseof -0.1 -i video.mp4 -frames:v 1 lastframe.png
    subprocess.run([
        'ffmpeg', '-sseof', '-0.1', '-i', video_path,
        '-frames:v', '1', '-y', output
    ])
    return output
```

Flow xu ly moi scene:
```
Scene 1: text-to-video (prompt enhanced by ChatGPT)
    → download video_01.mp4
    → extract last frame → frame_01.png

Scene 2: image-to-video (first_frame=frame_01.png, prompt enhanced)
    → download video_02.mp4
    → extract last frame → frame_02.png

Scene 3: image-to-video (first_frame=frame_02.png, prompt enhanced)
    → ...
```

---

## 5 API Keys Can Thiet

| # | Service | Muc dich | Lay key tai |
|---|---------|----------|-------------|
| 1 | **OpenAI (ChatGPT)** | Xu ly prompt, dong bo lien mach | platform.openai.com |
| 2 | **Google Veo 3** | Tao video | aistudio.google.com |
| 3 | **Runway** | Tao video | dev.runwayml.com |
| 4 | **Kling AI** | Tao video | app.klingai.com |
| 5 | **Minimax** | Tao video | platform.minimax.io |

Chi can API key cua ChatGPT + 1 video provider la du de chay.

---

## 4 AI Video Providers

### 1. Google Veo 3
- **API**: REST (Vertex AI / Gemini API)
- **Auth**: API Key hoac OAuth2
- **Models**: `veo-3.0-generate-001`, `veo-3.1-generate-001`, `veo-3.1-fast-generate-001`
- **Video**: 4-8 giay, 720p/1080p, 24fps, MP4
- **Gia**: $0.15-$0.75/giay (tuy model)
- **Rate limit**: 10 req/phut
- **Flow**: POST predictLongRunning → poll operation ID → download tu GCS
- **Image-to-video**: Co ho tro (dung cho frame chaining)

### 2. Runway Gen-4
- **API**: `https://api.runwayml.com/v1/`
- **Auth**: Bearer Token (API Key)
- **SDK**: `runway-python` (pip install)
- **Models**: `gen4_turbo`, `gen4.5`
- **Video**: 2-10 giay, 1280x720
- **Gia**: $0.05-$0.15/giay (tuy model)
- **Rate limit**: Khong gioi han RPM (auto queue)
- **Flow**: POST /v1/text_to_video → poll GET /v1/tasks/{id} → download URL
- **Image-to-video**: `promptImage` parameter

### 3. Kling AI (Kuaishou)
- **API**: `https://api.klingapi.com/v1/`
- **Auth**: Bearer Token (API Key)
- **Models**: `kling-3.0`, `kling-3.5-pro`
- **Video**: 5-10 giay, 720p/1080p
- **Gia**: ~$0.01-$0.10/video (re nhat)
- **Rate limit**: 20-50 req/phut
- **Flow**: POST /v1/videos/text2video → poll task → download URL
- **Image-to-video**: Co ho tro

### 4. Minimax Hailuo
- **API**: `https://api.minimax.io/v1/`
- **Auth**: Bearer Token (API Key)
- **Models**: `MiniMax-Hailuo-2.3`, `MiniMax-Hailuo-2.3-Fast`
- **Video**: 6-10 giay, 768p/1080p
- **Gia**: ~$0.01-$0.10/video (re nhat)
- **Rate limit**: 20-50 req/phut
- **Flow**: POST /v1/video_generation → poll status → GET file download URL
- **Image-to-video**: `first_frame_image`, `last_frame_image` parameter

---

## GUI Layout (tkinter)

```
┌─────────────────────────────────────────────────────────┐
│  ★ AI Video Generator                          [Settings]│
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Video Provider: [▼ Veo 3 / Runway / Kling / Minimax ] │
│  Resolution:     [▼ 720p / 1080p]                       │
│  Duration:       [▼ 5s / 8s / 10s]                      │
│  Output Folder:  [C:\Users\Videos\project1] [Browse]    │
│                                                         │
│  ═══ Consistency Settings ═══════════════════════════   │
│                                                         │
│  ☑ ChatGPT Prompt Enhancement (gpt-4o)                  │
│  ☑ Frame Chaining (last frame → next scene)             │
│  ☐ Reference Image: [         ] [Browse]                │
│  ☐ Consistent Seed: [ 42 ]                              │
│                                                         │
│  ═══ Scene Prompts ══════════════════════════════════   │
│  [Import TXT/CSV]                                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 1. Co gai di dao tren bai bien luc hoang hon    │    │
│  │ 2. Can canh song vo vao da                      │    │
│  │ 3. Goc nhin tu tren cao bo bien                 │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  [✨ Enhance Prompts]  ← Goi ChatGPT xu ly truoc       │
│                                                         │
│  ═══ Enhanced Preview (sau khi ChatGPT xu ly) ═══════  │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Character: Young Vietnamese woman, long black   │    │
│  │ hair, white linen dress, brown eyes...          │    │
│  │ Style: cinematic, warm grading, 35mm film...    │    │
│  │─────────────────────────────────────────────────│    │
│  │ #1: A young Vietnamese woman with long black    │    │
│  │     hair walks barefoot along sandy beach...    │    │
│  │ #2: Close-up of turquoise waves crashing on     │    │
│  │     dark volcanic rocks, white foam spray...    │    │
│  │ #3: Aerial drone shot of the coastline...       │    │
│  └─────────────────────────────────────────────────┘    │
│  (User co the chinh sua truoc khi generate)             │
│                                                         │
│  [▶ Generate All Videos]                                │
│                                                         │
│  ═══ Progress ═══════════════════════════════════════   │
│  ████████░░░░░░░░░░ 2/5 scenes (40%)                   │
│                                                         │
│  #  │ Prompt (rut gon)        │ Status      │ Action    │
│  ───┼─────────────────────────┼─────────────┼────────── │
│  1  │ Woman walks on beach... │ ✅ Done     │ [Open]    │
│  2  │ Waves crashing rocks... │ ⏳ Generating│          │
│  3  │ Aerial coastline...     │ ⏸ Pending   │          │
│                                                         │
│  ═══ Log ════════════════════════════════════════════   │
│  [14:30:01] ChatGPT: Enhanced 3 prompts OK             │
│  [14:30:05] Scene 1: Submitted to Kling API            │
│  [14:30:15] Scene 1: Generating... (poll #1)           │
│  [14:30:45] Scene 1: Done! Downloaded scene_01.mp4     │
│  [14:30:46] Extracting last frame from scene_01.mp4    │
│  [14:30:47] Scene 2: Submitted (with frame chaining)   │
└─────────────────────────────────────────────────────────┘
```

---

## Flow Hoat Dong (Cap Nhat)

```
1. Mo app (python main.py)
        │
2. Nhap API keys (Settings) → luu config.json
   - OpenAI key (bat buoc)
   - It nhat 1 video provider key
        │
3. Nhap scene prompts (truc tiep hoac import TXT/CSV)
        │
4. Chon provider + resolution + duration + output folder
        │
5. ★ Nhan "Enhance Prompts" (goi ChatGPT API)
   │   ├─ ChatGPT tao Character Bible
   │   ├─ ChatGPT enhance tung scene prompt
   │   ├─ ChatGPT them style prefix + transition hints
   │   └─ Dich sang tieng Anh (neu can)
   │
   ▼
6. User review enhanced prompts → chinh sua neu can
        │
7. Nhan "Generate All Videos"
        │
8. Scene 1: text-to-video (enhanced prompt)
   │   ├─ Submit → poll → download video_01.mp4
   │   └─ Extract last frame → frame_01.png
   │
9. Scene 2: image-to-video (frame_01.png + enhanced prompt)
   │   ├─ Submit → poll → download video_02.mp4
   │   └─ Extract last frame → frame_02.png
   │
10. Scene N: image-to-video (frame_N-1.png + enhanced prompt)
   │   └─ ... (lap lai)
   │
11. Tat ca xong → Thong bao hoan thanh
        │
12. (Tuy chon) Merge tat ca video thanh 1 file (ffmpeg concat)
```

---

## ChatGPT System Prompt (prompt_engine.py)

```
You are an expert film director and cinematographer. Your job is to take
a list of rough scene descriptions and produce a comprehensive, consistent
set of video generation prompts.

Rules:
1. Create a CHARACTER BIBLE describing every character's appearance in detail
   (hair, face, body, clothing, skin tone, age, distinguishing features).
   These descriptions must be IDENTICAL across all scenes.

2. Create a STYLE GUIDE with consistent visual keywords
   (lighting, color grading, camera lens, film stock, mood).

3. For each scene, write a detailed English prompt that:
   - Includes the character description from the bible
   - Describes the action, setting, and camera movement
   - Ends with the style keywords
   - Includes transition hints (ending pose/direction matches next scene's start)

4. Keep each prompt under 500 characters (video AI limit).

5. If input is not English, translate naturally to English.

Output as JSON:
{
  "character_bible": "...",
  "style_guide": "...",
  "scenes": [
    {
      "id": 1,
      "original": "user's original text",
      "enhanced_prompt": "detailed English prompt",
      "transition_to_next": "ending state description"
    }
  ]
}
```

---

## Dependencies (Cap Nhat)

```
# requirements.txt
openai>=1.30.0          # ChatGPT API - prompt engine
requests>=2.31.0        # HTTP client cho Veo3, Kling, Minimax
runway-python>=0.5.0    # Runway SDK
Pillow>=10.0.0          # Xu ly anh (reference image, frame preview)
```

Yeu cau them:
- **ffmpeg** cai tren Windows (dung cho frame chaining + merge video)
  - Download tai: https://ffmpeg.org/download.html
  - Hoac: `winget install ffmpeg`

---

## So Sanh Chi Phi (tham khao)

| Provider | Video 5-8s | Chat luong | Toc do |
|----------|-----------|------------|--------|
| Veo 3 Fast | ~$1.20 | Cao | Nhanh |
| Veo 3 Standard | ~$4.00 | Rat cao | Trung binh |
| Runway Gen-4 Turbo | ~$0.25-0.50 | Cao | Nhanh |
| Kling 3.0 | ~$0.01-0.10 | Cao | Nhanh |
| Minimax Hailuo 2.3 | ~$0.01-0.10 | Cao | Nhanh |
| **ChatGPT (prompt engine)** | **~$0.02/10 scenes** | - | Nhanh |

---

## Thu Tu Trien Khai

- [ ] **Buoc 1**: Tao cau truc thu muc + file co ban
- [ ] **Buoc 2**: Implement `core/config.py` (load/save 5 API keys + settings)
- [ ] **Buoc 3**: Implement `core/prompt_engine.py` ★ (ChatGPT dong bo prompt)
- [ ] **Buoc 4**: Implement `core/frame_utils.py` (extract last frame - ffmpeg)
- [ ] **Buoc 5**: Implement `providers/base.py` (abstract class)
- [ ] **Buoc 6**: Implement 4 video providers (veo3, runway, kling, minimax)
- [ ] **Buoc 7**: Implement `core/task_manager.py` (queue + frame chaining logic)
- [ ] **Buoc 8**: Implement GUI (app.py, settings, prompt editor, enhanced preview)
- [ ] **Buoc 9**: Ket noi GUI ↔ Prompt Engine ↔ Task Manager ↔ Providers
- [ ] **Buoc 10**: Test end-to-end voi tung provider
- [ ] **Buoc 11**: Them tinh nang merge video (ffmpeg concat)
- [ ] **Buoc 12**: Polish UI + error handling + packaging (.exe)
