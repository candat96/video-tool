# AI Video Generator - How to Run

## Yeu Cau He Thong
- **Python 3.10+** (download: https://www.python.org/downloads/)
- **ffmpeg** (chi can neu dung Frame Chaining)
- **Windows 10/11**

## Buoc 1: Cai Dat Python Dependencies

Mo Terminal (cmd / PowerShell / Git Bash) trong thu muc `tool-video`:

```bash
cd C:\Users\Windows\Desktop\tool-video
pip install -r requirements.txt
```

Dependencies se cai:
- `openai` - ChatGPT API
- `requests` - HTTP client
- `Pillow` - Xu ly anh

## Buoc 2: Cai Dat ffmpeg (Tuy Chon)

Chi can neu bat **Frame Chaining** (lay frame cuoi lam input scene tiep theo).

### Cach 1: Dung winget
```bash
winget install ffmpeg
```

### Cach 2: Download thu cong
1. Vao https://ffmpeg.org/download.html
2. Download ban Windows
3. Giai nen vao `C:\ffmpeg\`
4. Them `C:\ffmpeg\bin` vao PATH

## Buoc 3: Chay Tool

```bash
python main.py
```

## Buoc 4: Cau Hinh API Keys

1. Nhan nut **Settings** (goc phai tren)
2. Nhap API keys:
   - **OpenAI** (bat buoc): Lay tai https://platform.openai.com/api-keys
   - **Kling AI**: Lay tai https://app.klingai.com
   - **Minimax**: Lay tai https://platform.minimax.io
   - **Runway**: Lay tai https://dev.runwayml.com
   - **Google Veo 3**: Lay tai https://aistudio.google.com
3. Nhan **Test** de kiem tra key hop le
4. Nhan **Save**

> Chi can OpenAI key + 1 video provider key la du de chay.

## Buoc 5: Su Dung

### Nhap Prompt
- Nhap truc tiep vao khung "Scene Prompts", moi dong = 1 scene
- Hoac nhan **Import TXT/CSV** de load tu file

### Format file TXT:
```
A vast landscape at sunrise, misty floodplains
Dense prehistoric forest with tall conifers
Massive T-Rex resting beneath tall trees
```

### Format file CSV:
```csv
scene,prompt,duration
1,A vast landscape at sunrise,8
2,Dense prehistoric forest,8
3,T-Rex resting beneath trees,8
```

### Enhance voi ChatGPT
1. Nhap prompts
2. Nhan **Enhance Prompts (ChatGPT)**
3. ChatGPT se:
   - Tao Character Bible (mo ta nhan vat nhat quan)
   - Viet lai prompt chi tiet bang tieng Anh
   - Them style keywords dong nhat
4. Xem ket qua trong "Enhanced Preview"
5. Co the chinh sua truoc khi generate

### Generate Videos
1. Chon **Provider** (Kling AI re nhat)
2. Chon **Resolution** va **Duration**
3. Chon **Output Folder**
4. Bat/tat **Frame Chaining** va **ChatGPT Enhance**
5. Nhan **Generate All Videos**
6. Xac nhan chi phi
7. Doi va theo doi progress

### Ket Qua
Videos se luu trong output folder voi ten:
```
1.mp4
2.mp4
3.mp4
...
63.mp4
```

## Cac Tinh Nang

| Tinh nang | Mo ta |
|-----------|-------|
| ChatGPT Enhance | Tu dong tao Character Bible + enhance prompt |
| Frame Chaining | Lay frame cuoi scene N lam input scene N+1 |
| Test API Key | Kiem tra key hop le truoc khi generate |
| Resume | Scene da xong se bi skip khi chay lai |
| Auto Retry | Tu dong thu lai 1 lan neu scene bi fail |
| Import File | Ho tro TXT va CSV |
| Cost Estimate | Uoc tinh chi phi truoc khi generate |
| Stop | Dung bat ky luc nao, generate lai tu scene dang do |

## Troubleshooting

### "ffmpeg not found"
- Cai ffmpeg theo Buoc 2, hoac tat Frame Chaining

### "No API key"
- Mo Settings va nhap key, nhan Test de kiem tra

### "ChatGPT Error"
- Kiem tra OpenAI key hop le
- Kiem tra con credit trong tai khoan OpenAI

### "Generation FAILED"
- Kiem tra key cua video provider
- Kiem tra con credit/quota
- Thu lai voi provider khac

### Muon doi provider giua chung?
- Dung luc nay chua ho tro doi provider giua cac scene
- Phai generate xong tat ca scene voi 1 provider
