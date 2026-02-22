import requests
import os
from .base import BaseProvider

BASE_URL = "https://api.klingapi.com/v1"


class KlingProvider(BaseProvider):
    name = "kling"
    supports_image_to_video = True

    def __init__(self, api_key: str, model: str = "kling-v1"):
        super().__init__(api_key)
        self.model = model

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def submit_text_to_video(self, prompt: str, duration: int = 8,
                             resolution: str = "720p", seed: int = 0) -> str:
        url = f"{BASE_URL}/videos/text2video"
        duration = max(5, min(duration, 10))
        payload = {
            "model_name": self.model,
            "prompt": prompt,
            "cfg_scale": 0.5,
            "mode": "std",
            "duration": str(duration),
            "aspect_ratio": "16:9",
        }

        resp = requests.post(url, json=payload, headers=self._headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Kling returns {"code": 0, "data": {"task_id": "..."}}
        task_data = data.get("data", {})
        return task_data.get("task_id", "")

    def submit_image_to_video(self, prompt: str, image_path: str,
                              duration: int = 8, resolution: str = "720p",
                              seed: int = 0) -> str:
        import base64
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        url = f"{BASE_URL}/videos/image2video"
        duration = max(5, min(duration, 10))
        payload = {
            "model_name": self.model,
            "prompt": prompt,
            "image": image_b64,
            "cfg_scale": 0.5,
            "mode": "std",
            "duration": str(duration),
            "aspect_ratio": "16:9",
        }

        resp = requests.post(url, json=payload, headers=self._headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        task_data = data.get("data", {})
        return task_data.get("task_id", "")

    def check_status(self, task_id: str) -> dict:
        url = f"{BASE_URL}/videos/text2video/{task_id}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()

        task_data = data.get("data", {})
        status = task_data.get("task_status", "")

        if status == "succeed":
            works = task_data.get("task_result", {}).get("videos", [])
            video_url = works[0].get("url", "") if works else ""
            return {"status": "completed", "video_url": video_url}
        elif status == "failed":
            return {"status": "failed", "error": task_data.get("task_status_msg", "Unknown")}
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
        # Kling: ~$0.01-0.05/video
        return 0.05
