import requests
import os
import time
import base64
from .base import BaseProvider

BASE_URL = "https://api.dev.runwayml.com/v1"


class RunwayProvider(BaseProvider):
    name = "runway"
    supports_image_to_video = True

    def __init__(self, api_key: str, model: str = "gen4_turbo"):
        super().__init__(api_key)
        self.model = model

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }

    def submit_text_to_video(self, prompt: str, duration: int = 8,
                             resolution: str = "720p", seed: int = 0) -> str:
        url = f"{BASE_URL}/text_to_video"
        duration = max(5, min(duration, 10))
        payload = {
            "model": self.model,
            "promptText": prompt[:1000],
            "duration": duration,
            "ratio": "1280:720",
        }
        if seed > 0:
            payload["seed"] = seed

        resp = requests.post(url, json=payload, headers=self._headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("id", "")

    def submit_image_to_video(self, prompt: str, image_path: str,
                              duration: int = 8, resolution: str = "720p",
                              seed: int = 0) -> str:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        url = f"{BASE_URL}/image_to_video"
        duration = max(5, min(duration, 10))
        payload = {
            "model": self.model,
            "promptImage": f"data:image/png;base64,{image_b64}",
            "promptText": prompt[:1000],
            "duration": duration,
            "ratio": "1280:720",
        }
        if seed > 0:
            payload["seed"] = seed

        resp = requests.post(url, json=payload, headers=self._headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("id", "")

    def check_status(self, task_id: str) -> dict:
        url = f"{BASE_URL}/tasks/{task_id}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status", "").upper()
        if status == "SUCCEEDED":
            outputs = data.get("output", [])
            video_url = outputs[0].get("url", "") if outputs else ""
            return {"status": "completed", "video_url": video_url}
        elif status == "FAILED":
            return {"status": "failed", "error": data.get("failure", "Unknown error")}
        else:
            return {"status": "processing"}

    def download_video(self, video_url: str, save_path: str) -> str:
        resp = requests.get(video_url, stream=True, timeout=120)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path

    def get_cost_estimate(self, duration: int, resolution: str) -> float:
        # Gen-4 Turbo: ~$0.05/sec
        return duration * 0.05
