import subprocess
import shutil
import os


def find_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if path:
        return path
    common = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        os.path.join(os.path.expanduser("~"), "ffmpeg", "bin", "ffmpeg.exe"),
    ]
    for p in common:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(
        "ffmpeg not found. Install it: winget install ffmpeg  "
        "or download from https://ffmpeg.org/download.html"
    )


def extract_last_frame(video_path: str, output_path: str = None) -> str:
    """Extract the last frame of a video as PNG for frame chaining."""
    ffmpeg = find_ffmpeg()
    if output_path is None:
        base = os.path.splitext(video_path)[0]
        output_path = f"{base}_lastframe.png"

    cmd = [
        ffmpeg,
        "-sseof", "-0.5",
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        "-y",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    if not os.path.isfile(output_path):
        raise RuntimeError(f"Failed to extract last frame from {video_path}")
    return output_path
