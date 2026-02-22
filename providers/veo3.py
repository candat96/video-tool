import os
import time
from .base import BaseProvider

from google import genai
from google.genai import types


class Veo3Provider(BaseProvider):
    name = "veo3"
    supports_image_to_video = True

    MODELS = {
        "veo-3.1-quality": "veo-3.1-quality-generate-001",
        "veo-3.1-fast": "veo-3.1-fast-generate-preview",
        "veo-3.1": "veo-3.1-generate-preview",
        "veo-3.0": "veo-3.0-generate-001",
        "veo-3.0-fast": "veo-3.0-fast-generate-001",
        "veo-2.0": "veo-2.0-generate-001",
    }

    def __init__(self, api_key: str, model: str = "veo-3.0",
                 aspect_ratio: str = "16:9", resolution: str = "720p",
                 generate_audio: bool = True, no_watermark: bool = True,
                 negative_prompt: str = "", person_generation: str = "allow_all",
                 subject_refs: list[str] = None, bg_refs: list[str] = None):
        super().__init__(api_key)
        self.model_name = self.MODELS.get(model, self.MODELS["veo-3.0"])
        self.aspect_ratio = aspect_ratio
        self._resolution = resolution
        self.generate_audio = generate_audio
        self.no_watermark = no_watermark
        self.negative_prompt = negative_prompt
        self.person_generation = person_generation
        self.subject_refs = subject_refs or []
        self.bg_refs = bg_refs or []
        self.client = genai.Client(api_key=api_key)

    def _is_veo31(self) -> bool:
        return "3.1" in self.model_name

    def _upload_image(self, image_path: str):
        """Upload ảnh lên Google GenAI và đợi xử lý xong."""
        uploaded = self.client.files.upload(path=image_path)
        while uploaded.state and uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = self.client.files.get(name=uploaded.name)
        return uploaded

    def _read_image_bytes(self, image_path: str) -> tuple[bytes, str]:
        """Đọc ảnh thành bytes + mime type."""
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg", ".webp": "image/webp"}
        mime = mime_map.get(ext, "image/png")
        with open(image_path, "rb") as f:
            return f.read(), mime

    def _make_config(self, duration: int = 8, seed: int = 0) -> types.GenerateVideosConfig:
        kwargs = {
            "aspect_ratio": self.aspect_ratio,
            "number_of_videos": 1,
            "duration_seconds": duration,
            "person_generation": self.person_generation,
        }

        # generate_audio: chỉ Veo 3.1
        if self._is_veo31():
            kwargs["generate_audio"] = self.generate_audio

        # resolution: chỉ thêm nếu không phải 720p mặc định
        if "2.0" not in self.model_name and self._resolution != "720p":
            kwargs["resolution"] = self._resolution

        # negative_prompt
        if self.negative_prompt:
            kwargs["negative_prompt"] = self.negative_prompt

        # seed
        if seed > 0:
            kwargs["seed"] = seed

        # referenceImages: CHỈ Veo 3.1
        if self._is_veo31():
            ref_images = self._build_reference_images()
            if ref_images:
                kwargs["reference_images"] = ref_images

        return types.GenerateVideosConfig(**kwargs)

    def _build_reference_images(self) -> list[types.VideoGenerationReferenceImage]:
        """Tạo danh sách ảnh tham chiếu (tối đa 3, chỉ Veo 3.1)."""
        refs = []

        # Ảnh chủ thể → referenceType = ASSET
        for path in self.subject_refs[:2]:  # tối đa 2 ảnh chủ thể
            img_bytes, mime = self._read_image_bytes(path)
            refs.append(types.VideoGenerationReferenceImage(
                image=types.Image(image_bytes=img_bytes, mime_type=mime),
                reference_type="ASSET",
            ))

        # Ảnh bối cảnh → referenceType = STYLE
        remaining = 3 - len(refs)
        for path in self.bg_refs[:remaining]:  # tổng tối đa 3
            img_bytes, mime = self._read_image_bytes(path)
            refs.append(types.VideoGenerationReferenceImage(
                image=types.Image(image_bytes=img_bytes, mime_type=mime),
                reference_type="STYLE",
            ))

        return refs

    def submit_text_to_video(self, prompt: str, duration: int = 8,
                             resolution: str = "720p", seed: int = 0) -> str:
        config = self._make_config(duration, seed)

        operation = self.client.models.generate_videos(
            model=self.model_name,
            prompt=prompt,
            config=config,
        )
        return operation.name

    def submit_image_to_video(self, prompt: str, image_path: str,
                              duration: int = 8, resolution: str = "720p",
                              seed: int = 0) -> str:
        """Tạo video từ ảnh (first frame / frame chaining)."""
        uploaded_file = self._upload_image(image_path)
        config = self._make_config(duration, seed)

        operation = self.client.models.generate_videos(
            model=self.model_name,
            prompt=prompt,
            image=uploaded_file,
            config=config,
        )
        return operation.name

    def check_status(self, task_id: str) -> dict:
        operation = self.client.operations.get(operation=task_id)

        if operation.done:
            if hasattr(operation, 'error') and operation.error:
                return {"status": "failed", "error": str(operation.error)}

            # Lấy video từ kết quả
            if hasattr(operation, 'result') and operation.result:
                result = operation.result
                if hasattr(result, 'generated_videos') and result.generated_videos:
                    video = result.generated_videos[0]
                    if hasattr(video, 'video') and video.video:
                        return {"status": "completed", "video_url": video.video.uri}

            if hasattr(operation, 'response') and operation.response:
                resp = operation.response
                if hasattr(resp, 'generated_videos') and resp.generated_videos:
                    video = resp.generated_videos[0]
                    if hasattr(video, 'video') and video.video:
                        return {"status": "completed", "video_url": video.video.uri}

            return {"status": "failed", "error": "No video in response"}

        return {"status": "processing"}

    def download_video(self, video_url: str, save_path: str) -> str:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        import requests as req
        headers = {"x-goog-api-key": self.api_key}

        if "generativelanguage.googleapis.com" in video_url:
            sep = "&" if "?" in video_url else "?"
            download_url = f"{video_url}{sep}alt=media"
            resp = req.get(download_url, headers=headers, stream=True, timeout=300)
        elif video_url.startswith("gs://"):
            gcs_path = video_url.replace("gs://", "")
            download_url = f"https://storage.googleapis.com/{gcs_path}"
            resp = req.get(download_url, stream=True, timeout=300)
        else:
            resp = req.get(video_url, stream=True, timeout=300)

        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path

    def get_cost_estimate(self, duration: int, resolution: str) -> float:
        if "fast" in self.model_name:
            return duration * 0.15
        elif "quality" in self.model_name:
            return duration * 0.75
        elif "3.1" in self.model_name:
            return duration * 0.40
        return duration * 0.50
