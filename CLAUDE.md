# AI Video Generator Tool

## Project Overview
Desktop tool (Windows) for AI video generation from scene prompts. Supports multiple providers with ChatGPT prompt enhancement for consistency across scenes.

## Tech Stack
- **Language**: Python 3.10+
- **GUI**: customtkinter (dark theme)
- **AI Providers**: Google Veo 3 (google-genai SDK), Runway Gen-4, Kling AI, Minimax Hailuo
- **Prompt Engine**: OpenAI GPT-4o for prompt enhancement/translation
- **Build**: PyInstaller + Inno Setup installer

## Project Structure
```
tool-video/
├── main.py                  # Entry point
├── gui/
│   ├── app.py               # Main window (customtkinter)
│   ├── settings_dialog.py   # API key settings dialog
│   └── prompt_editor.py     # Scene prompt input/import widget
├── providers/
│   ├── base.py              # Abstract base class
│   ├── veo3.py              # Google Veo 3 (google-genai SDK)
│   ├── runway.py            # Runway Gen-4 (REST API)
│   ├── kling.py             # Kling AI (REST API)
│   └── minimax.py           # Minimax Hailuo (REST API)
├── core/
│   ├── config.py            # Load/save settings (~/.ai-video-tool/config.json)
│   ├── prompt_engine.py     # ChatGPT prompt enhancement
│   ├── task_manager.py      # Task queue, polling, download
│   └── frame_utils.py       # ffmpeg last frame extraction
├── build.spec               # PyInstaller spec
├── installer.iss            # Inno Setup installer script
└── requirements.txt
```

## Key Technical Details

### Veo 3 Provider (most complex)
- Uses `google-genai` SDK, NOT REST API
- `client.models.generate_videos()` / `types.GenerateVideosConfig`
- `generate_audio` only supported on Veo 3.1 models
- `referenceImages` (ASSET/STYLE) only supported on Veo 3.1, max 3 images
- `resolution` param: only add if not default 720p and not Veo 2.0
- Model names must include suffix like `-001` or `-preview`

### Frame Chaining
- Extract last frame of previous video via ffmpeg (`-sseof -0.5`)
- Use as first frame input for next scene's generation
- Priority: frame chaining > subject ref > background ref > text-only

### Prompt Engine
- Calls GPT-4o to create Character Bible + Style Guide
- Chunks >15 scenes to avoid token limits
- Returns enhanced prompts with transition hints

### Scene Text Parsing
- Supports multi-line format: `Scene X – Title\ncontinuation...`
- Regex pattern: `^(?:Scene|Canh)\s+\d+\s*[–\-:.]`
- Also supports simple one-line-per-scene format

## Commands
- **Run**: `python main.py`
- **Install deps**: `pip install -r requirements.txt`
- **Build exe**: `pyinstaller build.spec`
- **Build installer**: `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`

## Config
- API keys stored at `~/.ai-video-tool/config.json`
- Videos saved as `1.mp4`, `2.mp4`, ... in user-chosen output folder

## Language
- Code comments in Vietnamese
- Documentation in Vietnamese (HUONG_DAN.md) and English (HOW_TO_RUN.md)
