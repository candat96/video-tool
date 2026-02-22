import requests
import os
import base64
from .base import BaseProvider

BASE_URL = "https://api.minimaxi.chat/v1"


class MinimaxProvider(BaseProvider):
    name = "minimax"
    supports_image_to_video = True

    def __init__(self, api_key: str, model: str = "T2V-01"):
        super().__init__(api_key)
        self.model = model

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def submit_text_to_video(self, prompt: str, duration: int = 8,
                             resolution: str = "720p", seed: int = 0) -> str:
        url = f"{BASE_URL}/video_generation"
        payload = {
            "model": self.model,
            "prompt": prompt,
        }

        resp = requests.post(url, json=payload, headers=self._headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("task_id", "")

    def submit_image_to_video(self, prompt: str, image_path: str,
                              duration: int = 8, resolution: str = "720p",
                              seed: int = 0) -> str:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        url = f"{BASE_URL}/video_generation"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "first_frame_image": f"data:image/png;base64,{image_b64}",
        }

        resp = requests.post(url, json=payload, headers=self._headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("task_id", "")

    def check_status(self, task_id: str) -> dict:
        url = f"{BASE_URL}/query/video_generation"
        params = {"task_id": task_id}
        resp = requests.get(url, params=params, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status", "")
        if status == "Success":
            file_id = data.get("file_id", "")
            if file_id:
                video_url = self._get_download_url(file_id)
                return {"status": "completed", "video_url": video_url}
            return {"status": "failed", "error": "No file_id returned"}
        elif status == "Fail":
            return {"status": "failed", "error": data.get("base_resp", {}).get("status_msg", "Unknown")}
        else:
            return {"status": "processing"}

    def _get_download_url(self, file_id: str) -> str:
        url = f"{BASE_URL}/files/retrieve"
        params = {"file_id": file_id}
        resp = requests.get(url, params=params, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        file_data = data.get("file", {})
        return file_data.get("download_url", "")

    def download_video(self, video_url: str, save_path: str) -> str:
        resp = requests.get(video_url, stream=True, timeout=120)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path

    def get_cost_estimate(self, duration: int, resolution: str) -> float:
        return 0.05
