import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".ai-video-tool")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "api_keys": {
        "openai": "",
        "veo3": "",
        "runway": "",
        "kling": "",
        "minimax": "",
    },
    "settings": {
        "provider": "kling",
        "resolution": "720p",
        "duration": 8,
        "output_folder": os.path.join(os.path.expanduser("~"), "Videos", "ai-video-tool"),
        "frame_chaining": True,
        "consistent_seed": 0,
        "chatgpt_enhance": True,
        "chatgpt_model": "gpt-4o",
    },
}


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return json.loads(json.dumps(DEFAULT_CONFIG))
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        saved = json.load(f)
    # Merge with defaults so new keys are always present
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    for section in ("api_keys", "settings"):
        if section in saved:
            config[section].update(saved[section])
    return config


def save_config(config: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_api_key(config: dict, provider: str) -> str:
    return config.get("api_keys", {}).get(provider, "")
