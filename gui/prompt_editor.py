import customtkinter as ctk
from tkinter import filedialog
import csv
import os

CARD_BG = "#2b2b2b"
ACCENT = "#3498db"


class PromptEditor(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build_ui()

    def _build_ui(self):
        # Style prefix section
        style_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        style_frame.pack(fill="x", pady=(0, 8))

        style_header = ctk.CTkFrame(style_frame, fg_color="transparent")
        style_header.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(style_header, text="Style Prefix",
                     font=("Segoe UI", 13, "bold")).pack(side="left")
        ctk.CTkLabel(style_header, text="Applied to ALL scenes",
                     font=("Segoe UI", 11), text_color="#7f8c8d").pack(side="right")

        self.style_text = ctk.CTkTextbox(style_frame, height=50, font=("Consolas", 12),
                                         fg_color="#1e1e1e", corner_radius=8)
        self.style_text.pack(fill="x", padx=12, pady=(0, 10))
        self.style_text.insert("1.0",
            "Ultra realistic, cinematic documentary style, natural colors, 4K, 16:9, "
            "no cartoon, no text, no watermark")

        # Scene prompts section
        prompt_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        prompt_frame.pack(fill="both", expand=True)

        prompt_header = ctk.CTkFrame(prompt_frame, fg_color="transparent")
        prompt_header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(prompt_header, text="Scene Prompts",
                     font=("Segoe UI", 13, "bold")).pack(side="left")

        self.count_label = ctk.CTkLabel(prompt_header, text="0 scenes",
                                        font=("Segoe UI", 12, "bold"), text_color=ACCENT)
        self.count_label.pack(side="right")

        # Toolbar
        toolbar = ctk.CTkFrame(prompt_frame, fg_color="transparent")
        toolbar.pack(fill="x", padx=12, pady=(0, 4))

        ctk.CTkButton(toolbar, text="Import TXT / CSV", width=140, height=32,
                      fg_color="#3a3a3a", hover_color="#4a4a4a",
                      command=self._import_file).pack(side="left")

        ctk.CTkButton(toolbar, text="Clear", width=70, height=32,
                      fg_color="#3a3a3a", hover_color="#e74c3c",
                      command=self._clear).pack(side="left", padx=8)

        ctk.CTkLabel(toolbar, text="One scene per line",
                     font=("Segoe UI", 11), text_color="#7f8c8d").pack(side="right")

        # Text area
        self.prompt_text = ctk.CTkTextbox(prompt_frame, font=("Consolas", 12),
                                          fg_color="#1e1e1e", corner_radius=8)
        self.prompt_text.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.prompt_text.bind("<KeyRelease>", lambda e: self._update_count())

    def _import_file(self):
        path = filedialog.askopenfilename(
            title="Import Scene Prompts",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        scenes = []
        ext = os.path.splitext(path)[1].lower()

        if ext == ".csv":
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    prompt = row.get("prompt", "").strip()
                    if prompt:
                        scenes.append(prompt)
        else:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            scenes = _parse_scene_text(content)

        if scenes:
            self.prompt_text.delete("1.0", "end")
            self.prompt_text.insert("1.0", "\n".join(scenes))
            self._update_count()

    def _clear(self):
        self.prompt_text.delete("1.0", "end")
        self._update_count()

    def _update_count(self):
        scenes = self.get_scenes()
        n = len(scenes)
        self.count_label.configure(text=f"{n} scene{'s' if n != 1 else ''}")

    def get_style_prefix(self) -> str:
        return self.style_text.get("1.0", "end").strip()

    def get_scenes(self) -> list[dict]:
        text = self.prompt_text.get("1.0", "end").strip()
        if not text:
            return []
        prompts = _parse_scene_text(text)
        return [{"id": i + 1, "prompt": p} for i, p in enumerate(prompts)]

    def set_scenes_text(self, text: str):
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", text)
        self._update_count()


import re

# Scene header pattern: "Scene 1 – Title ...", "Scene 2 - Title ...", "Canh 3: ..."
_SCENE_PATTERN = re.compile(
    r'^(?:Scene|Canh)\s+\d+\s*[–\-:.]',
    re.IGNORECASE
)


def _parse_scene_text(text: str) -> list[str]:
    """
    Parse scene text that may be multi-line per scene.

    Supports 2 formats:
      1. "Scene X – Title description..." (multi-line, separated by Scene headers)
      2. Simple one-line-per-scene (no Scene headers)

    Returns list of prompt strings (without the "Scene X – Title" prefix).
    """
    text = text.strip()
    if not text:
        return []

    lines = text.split("\n")

    # Check if text contains Scene headers
    has_scene_headers = any(_SCENE_PATTERN.match(l.strip()) for l in lines if l.strip())

    if has_scene_headers:
        # Multi-line mode: group lines between Scene headers
        scenes = []
        current_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if _SCENE_PATTERN.match(stripped):
                # Save previous scene
                if current_lines:
                    scenes.append(" ".join(current_lines))
                # Start new scene - remove "Scene X – Title" prefix
                cleaned = stripped
                for sep in ["–", "-", ":"]:
                    if sep in cleaned:
                        parts = cleaned.split(sep, 1)
                        if any(kw in parts[0].lower() for kw in ["scene", "canh"]):
                            cleaned = parts[1].strip()
                            break
                current_lines = [cleaned] if cleaned else []
            else:
                # Continuation line of current scene
                current_lines.append(stripped)

        # Don't forget the last scene
        if current_lines:
            scenes.append(" ".join(current_lines))

        return scenes

    else:
        # Simple mode: each non-empty line is one scene
        return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
