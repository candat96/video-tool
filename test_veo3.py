"""Test Veo 3 with 4 dinosaur scenes."""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers.veo3 import Veo3Provider
from core.config import load_config, get_api_key
from gui.prompt_editor import _parse_scene_text

# --- Config ---
config = load_config()
api_key = get_api_key(config, "veo3")
if not api_key:
    print("ERROR: No Veo3 API key found. Run the app and add it in Settings.")
    sys.exit(1)

OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Videos", "ai-video-tool", "test")
os.makedirs(OUTPUT_DIR, exist_ok=True)

STYLE = "Ultra realistic, cinematic documentary style, natural colors, 4K, 16:9, no cartoon, no text, no watermark."

RAW_PROMPTS = """Scene 1 – Prehistoric Earth Establishing Shot A vast Late Cretaceous
landscape at sunrise, misty floodplains, distant volcano releasing light
smoke, dense conifer forests, cinematic golden light rays through
clouds, slow aerial camera movement

Scene 2 – Forest Atmosphere Dense prehistoric forest with tall conifers
and ferns, humid morning mist, insects flying in soft sunlight, subtle
camera push forward, immersive jungle ambience

Scene 3 – T-Rex Sleeping Massive Tyrannosaurus rex resting beneath tall
trees, partially hidden in shadow, slow breathing visible in chest
movement, early morning light filtering through leaves

Scene 4 – Eye Opening Close-up Extreme close-up of a Tyrannosaurus rex
eye opening, amber iris reflecting sunlight, detailed scales and skin
texture, cinematic lighting, shallow depth of field"""

# --- Parse scenes ---
scenes = _parse_scene_text(RAW_PROMPTS)
print(f"Parsed {len(scenes)} scenes\n")

# --- Init provider ---
provider = Veo3Provider(api_key, model="veo-3")
print(f"Provider: {provider.name} | Model: {provider.model}\n")

# --- Submit all scenes ---
tasks = {}  # scene_id -> (task_id, prompt)

for i, prompt in enumerate(scenes, 1):
    full_prompt = f"{prompt}. {STYLE}"
    print(f"[Scene {i}] Submitting...")
    print(f"  Prompt: {full_prompt[:80]}...")
    try:
        task_id = provider.submit_text_to_video(full_prompt, duration=8, resolution="720p")
        tasks[i] = (task_id, full_prompt)
        print(f"  OK -> task: {task_id[:50]}...")
    except Exception as e:
        print(f"  FAILED: {e}")
    print()

if not tasks:
    print("No tasks submitted successfully. Exiting.")
    sys.exit(1)

# --- Poll for completion ---
print("=" * 60)
print(f"Polling {len(tasks)} tasks... (checking every 15s)\n")

completed = {}
failed = {}
poll_count = 0
MAX_POLLS = 60  # 15 min max

while tasks and poll_count < MAX_POLLS:
    poll_count += 1
    time.sleep(15)
    timestamp = time.strftime("%H:%M:%S")

    for scene_id in list(tasks.keys()):
        task_id, prompt = tasks[scene_id]
        try:
            result = provider.check_status(task_id)
            status = result.get("status", "")

            if status == "completed":
                video_url = result.get("video_url", "")
                print(f"[{timestamp}] Scene {scene_id}: COMPLETED! URL: {video_url[:80]}...")

                # Download
                save_path = os.path.join(OUTPUT_DIR, f"{scene_id}.mp4")
                try:
                    provider.download_video(video_url, save_path)
                    size_mb = os.path.getsize(save_path) / (1024 * 1024)
                    print(f"  Downloaded: {save_path} ({size_mb:.1f} MB)")
                    completed[scene_id] = save_path
                except Exception as e:
                    print(f"  Download FAILED: {e}")
                    failed[scene_id] = str(e)

                del tasks[scene_id]

            elif status == "failed":
                error = result.get("error", "Unknown")
                print(f"[{timestamp}] Scene {scene_id}: FAILED - {error}")
                failed[scene_id] = error
                del tasks[scene_id]

            else:
                print(f"[{timestamp}] Scene {scene_id}: {status}... (poll #{poll_count})")

        except Exception as e:
            print(f"[{timestamp}] Scene {scene_id}: Poll error - {e}")

    print()

# --- Summary ---
print("=" * 60)
print("SUMMARY")
print(f"  Completed: {len(completed)}/{len(scenes)}")
print(f"  Failed:    {len(failed)}/{len(scenes)}")
print(f"  Timeout:   {len(tasks)}/{len(scenes)}")
for sid, path in sorted(completed.items()):
    print(f"  Scene {sid}: {path}")
for sid, err in sorted(failed.items()):
    print(f"  Scene {sid}: ERROR - {err}")
print(f"\nOutput folder: {OUTPUT_DIR}")
