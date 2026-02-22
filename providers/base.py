from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base class for all AI video generation providers."""

    name: str = "base"
    supports_image_to_video: bool = False

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def submit_text_to_video(self, prompt: str, duration: int = 8,
                             resolution: str = "720p", seed: int = 0) -> str:
        """Submit a text prompt for video generation. Returns task_id."""

    @abstractmethod
    def submit_image_to_video(self, prompt: str, image_path: str,
                              duration: int = 8, resolution: str = "720p",
                              seed: int = 0) -> str:
        """Submit with a reference/first-frame image. Returns task_id."""

    @abstractmethod
    def check_status(self, task_id: str) -> dict:
        """
        Check generation status.
        Returns: {"status": "pending"|"processing"|"completed"|"failed",
                  "video_url": str|None, "error": str|None}
        """

    @abstractmethod
    def download_video(self, video_url: str, save_path: str) -> str:
        """Download video to local path. Returns save_path."""

    def get_cost_estimate(self, duration: int, resolution: str) -> float:
        """Estimated cost per video in USD. Override in subclass."""
        return 0.0
