import os
import time
import threading
from typing import Callable

from providers.base import BaseProvider
from core.frame_utils import extract_last_frame

POLL_INTERVAL = 10  # seconds
MAX_RETRIES = 1


class SceneTask:
    def __init__(self, scene_id: int, prompt: str, enhanced_prompt: str = ""):
        self.scene_id = scene_id
        self.prompt = prompt
        self.enhanced_prompt = enhanced_prompt or prompt
        self.status = "pending"  # pending, submitting, processing, downloading, completed, failed
        self.task_id = ""
        self.video_url = ""
        self.video_path = ""
        self.error = ""
        self.retries = 0


class TaskManager:
    def __init__(self, provider: BaseProvider, output_folder: str,
                 frame_chaining: bool = True, seed: int = 0,
                 duration: int = 8, resolution: str = "720p",
                 subject_refs: list[str] = None, bg_refs: list[str] = None):
        self.provider = provider
        self.output_folder = output_folder
        self.frame_chaining = frame_chaining
        self.seed = seed
        self.duration = duration
        self.resolution = resolution
        self.subject_refs = subject_refs or []  # Paths to subject/character reference images
        self.bg_refs = bg_refs or []            # Paths to background/scene reference images
        self.scenes: list[SceneTask] = []
        self._running = False
        self._thread: threading.Thread | None = None
        self._on_update: Callable | None = None
        self._on_log: Callable | None = None
        self._on_complete: Callable | None = None

    def set_callbacks(self, on_update: Callable = None, on_log: Callable = None,
                      on_complete: Callable = None):
        self._on_update = on_update
        self._on_log = on_log
        self._on_complete = on_complete

    def _log(self, msg: str):
        if self._on_log:
            self._on_log(msg)

    def _update(self):
        if self._on_update:
            self._on_update()

    def load_scenes(self, scenes: list[SceneTask]):
        self.scenes = scenes

    def estimate_cost(self) -> float:
        cost_per = self.provider.get_cost_estimate(self.duration, self.resolution)
        return cost_per * len(self.scenes)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        os.makedirs(self.output_folder, exist_ok=True)
        last_frame_path = None

        for scene in self.scenes:
            if not self._running:
                self._log("Generation stopped by user.")
                break

            if scene.status == "completed":
                # Resume: skip completed, but get last frame if needed
                video_path = scene.video_path
                if self.frame_chaining and os.path.isfile(video_path):
                    try:
                        last_frame_path = extract_last_frame(video_path)
                    except Exception:
                        last_frame_path = None
                continue

            self._process_scene(scene, last_frame_path)

            if scene.status == "completed" and self.frame_chaining:
                try:
                    last_frame_path = extract_last_frame(scene.video_path)
                    self._log(f"Scene {scene.scene_id}: Extracted last frame for chaining")
                except Exception as e:
                    self._log(f"Scene {scene.scene_id}: Frame extraction failed: {e}")
                    last_frame_path = None

        self._running = False
        if self._on_complete:
            self._on_complete()

    def _process_scene(self, scene: SceneTask, first_frame_path: str = None):
        prompt = scene.enhanced_prompt
        save_path = os.path.join(self.output_folder, f"{scene.scene_id}.mp4")

        # Determine which image to use as reference
        ref_image = None
        ref_mode = "text-to-video"

        if first_frame_path and self.frame_chaining and self.provider.supports_image_to_video:
            # Priority 1: Frame chaining (last frame of previous scene)
            ref_image = first_frame_path
            ref_mode = "image-to-video, frame chaining"
        elif self.subject_refs and self.provider.supports_image_to_video:
            # Priority 2: Subject reference image (for first scene or when no chaining)
            ref_image = self.subject_refs[0]
            ref_mode = "image-to-video, subject reference"
        elif self.bg_refs and self.provider.supports_image_to_video:
            # Priority 3: Background reference image
            ref_image = self.bg_refs[0]
            ref_mode = "image-to-video, background reference"

        # Submit
        scene.status = "submitting"
        self._update()
        try:
            if ref_image:
                self._log(f"Scene {scene.scene_id}: Submitting ({ref_mode})...")
                scene.task_id = self.provider.submit_image_to_video(
                    prompt, ref_image, self.duration, self.resolution, self.seed
                )
            else:
                self._log(f"Scene {scene.scene_id}: Submitting (text-to-video)...")
                scene.task_id = self.provider.submit_text_to_video(
                    prompt, self.duration, self.resolution, self.seed
                )
        except Exception as e:
            scene.status = "failed"
            scene.error = str(e)
            self._log(f"Scene {scene.scene_id}: Submit FAILED - {e}")
            self._update()
            if scene.retries < MAX_RETRIES:
                scene.retries += 1
                self._log(f"Scene {scene.scene_id}: Retrying ({scene.retries}/{MAX_RETRIES})...")
                time.sleep(5)
                self._process_scene(scene, first_frame_path)
            return

        # Poll status
        scene.status = "processing"
        self._update()
        self._log(f"Scene {scene.scene_id}: Processing (task_id: {scene.task_id[:20]}...)")

        poll_count = 0
        while self._running:
            time.sleep(POLL_INTERVAL)
            poll_count += 1
            try:
                result = self.provider.check_status(scene.task_id)
            except Exception as e:
                self._log(f"Scene {scene.scene_id}: Poll error: {e}")
                continue

            status = result.get("status", "")
            if status == "completed":
                scene.video_url = result.get("video_url", "")
                self._log(f"Scene {scene.scene_id}: Generation complete! Downloading...")
                break
            elif status == "failed":
                scene.status = "failed"
                scene.error = result.get("error", "Unknown error")
                self._log(f"Scene {scene.scene_id}: FAILED - {scene.error}")
                self._update()
                if scene.retries < MAX_RETRIES:
                    scene.retries += 1
                    self._log(f"Scene {scene.scene_id}: Retrying ({scene.retries}/{MAX_RETRIES})...")
                    time.sleep(5)
                    self._process_scene(scene, first_frame_path)
                return
            else:
                self._log(f"Scene {scene.scene_id}: Still processing... (poll #{poll_count})")

        if not scene.video_url:
            return

        # Download
        scene.status = "downloading"
        self._update()
        try:
            self.provider.download_video(scene.video_url, save_path)
            scene.video_path = save_path
            scene.status = "completed"
            self._log(f"Scene {scene.scene_id}: Downloaded -> {save_path}")
        except Exception as e:
            scene.status = "failed"
            scene.error = str(e)
            self._log(f"Scene {scene.scene_id}: Download FAILED - {e}")

        self._update()
