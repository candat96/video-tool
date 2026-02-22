import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
import os

from core.config import load_config, save_config, get_api_key
from core.prompt_engine import enhance_prompts_chunked
from core.task_manager import TaskManager, SceneTask
from gui.settings_dialog import SettingsDialog
from gui.prompt_editor import PromptEditor
from providers.veo3 import Veo3Provider
from providers.runway import RunwayProvider
from providers.kling import KlingProvider
from providers.minimax import MinimaxProvider

# Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Colors
ACCENT = "#3498db"
GREEN = "#2ecc71"
RED = "#e74c3c"
ORANGE = "#f39c12"
GRAY = "#7f8c8d"
CARD_BG = "#2b2b2b"
DARK_BG = "#1a1a1a"
INPUT_BG = "#1e1e1e"

PROVIDERS = {
    "Kling AI": ("kling", KlingProvider),
    "Minimax Hailuo": ("minimax", MinimaxProvider),
    "Runway Gen-4": ("runway", RunwayProvider),
    "Google Veo 3": ("veo3", Veo3Provider),
}

STATUS_COLORS = {
    "pending": GRAY,
    "submitting": ORANGE,
    "processing": ACCENT,
    "downloading": ACCENT,
    "completed": GREEN,
    "failed": RED,
}

STATUS_ICONS = {
    "pending": "  ",
    "submitting": "  ",
    "processing": "  ",
    "downloading": "  ",
    "completed": "  ",
    "failed": "  ",
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Video Generator")
        self.geometry("980x900")
        self.minsize(850, 750)

        self.config_data = load_config()
        self.task_manager: TaskManager | None = None
        self.enhanced_data: dict | None = None
        self.scene_labels: dict[int, ctk.CTkLabel] = {}

        self._build_ui()

    def _build_ui(self):
        # ========== TOP BAR ==========
        topbar = ctk.CTkFrame(self, height=60, fg_color=CARD_BG, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        title_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        title_frame.pack(side="left", padx=20)

        ctk.CTkLabel(title_frame, text="AI Video Generator",
                     font=("Segoe UI", 20, "bold")).pack(side="left")
        ctk.CTkLabel(title_frame, text="v1.0",
                     font=("Segoe UI", 11), text_color=GRAY).pack(side="left", padx=(8, 0), pady=(4, 0))

        ctk.CTkButton(topbar, text="Settings", width=100, height=36,
                      fg_color="#3a3a3a", hover_color="#4a4a4a",
                      command=self._open_settings).pack(side="right", padx=20)

        # ========== MAIN SCROLLABLE ==========
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=15, pady=10)

        # ========== SETTINGS ROW ==========
        settings_card = ctk.CTkFrame(self.main_scroll, fg_color=CARD_BG, corner_radius=12)
        settings_card.pack(fill="x", pady=(0, 8))

        settings_inner = ctk.CTkFrame(settings_card, fg_color="transparent")
        settings_inner.pack(fill="x", padx=15, pady=12)

        # Row 1: Provider, Resolution, Duration
        row1 = ctk.CTkFrame(settings_inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))

        self._add_labeled_widget(row1, "Provider",
            ctk.CTkOptionMenu(row1, variable=(sv := ctk.StringVar(value="Kling AI")),
                              values=list(PROVIDERS.keys()), width=160, height=34))
        self.provider_var = sv

        self._add_labeled_widget(row1, "Resolution",
            ctk.CTkOptionMenu(row1, variable=(rv := ctk.StringVar(value="720p")),
                              values=["720p", "1080p"], width=100, height=34))
        self.res_var = rv

        self._add_labeled_widget(row1, "Duration",
            ctk.CTkOptionMenu(row1, variable=(dv := ctk.StringVar(value="8")),
                              values=["5", "8", "10"], width=80, height=34))
        self.dur_var = dv

        ctk.CTkLabel(row1, text="sec", font=("Segoe UI", 12), text_color=GRAY).pack(side="left", padx=(2, 0))

        # Row 2: Output folder
        row2 = ctk.CTkFrame(settings_inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(row2, text="Output", font=("Segoe UI", 12, "bold"),
                     text_color=GRAY).pack(side="left", padx=(0, 8))

        self.output_var = ctk.StringVar(value=self.config_data["settings"]["output_folder"])
        ctk.CTkEntry(row2, textvariable=self.output_var, height=34,
                     font=("Consolas", 11), fg_color=INPUT_BG).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(row2, text="Browse", width=80, height=34,
                      fg_color="#3a3a3a", hover_color="#4a4a4a",
                      command=self._browse_output).pack(side="right")

        # Row 3: Toggles
        row3 = ctk.CTkFrame(settings_inner, fg_color="transparent")
        row3.pack(fill="x")

        self.chain_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(row3, text="Frame Chaining", variable=self.chain_var,
                      font=("Segoe UI", 12), progress_color=GREEN).pack(side="left", padx=(0, 20))

        self.enhance_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(row3, text="ChatGPT Enhance", variable=self.enhance_var,
                      font=("Segoe UI", 12), progress_color=GREEN).pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row3, text="Seed", font=("Segoe UI", 12, "bold"),
                     text_color=GRAY).pack(side="left", padx=(20, 5))
        self.seed_var = ctk.StringVar(value="0")
        ctk.CTkEntry(row3, textvariable=self.seed_var, width=70, height=30,
                     font=("Consolas", 12), fg_color=INPUT_BG).pack(side="left")

        # Row 4: Veo 3 advanced options
        row4 = ctk.CTkFrame(settings_inner, fg_color="transparent")
        row4.pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(row4, text="Veo 3 Options", font=("Segoe UI", 12, "bold"),
                     text_color=ACCENT).pack(side="left", padx=(0, 10))

        self._add_labeled_widget(row4, "Model",
            ctk.CTkOptionMenu(row4, variable=(mv := ctk.StringVar(value="veo-3.0")),
                              values=["veo-3.1-quality", "veo-3.1", "veo-3.1-fast",
                                      "veo-3.0", "veo-3.0-fast", "veo-2.0"],
                              width=145, height=30))
        self.veo_model_var = mv

        self._add_labeled_widget(row4, "Ratio",
            ctk.CTkOptionMenu(row4, variable=(ar := ctk.StringVar(value="16:9")),
                              values=["16:9", "9:16"], width=80, height=30))
        self.aspect_var = ar

        self.audio_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(row4, text="Audio", variable=self.audio_var,
                      font=("Segoe UI", 12), progress_color=GREEN).pack(side="left", padx=(10, 10))

        self.no_wm_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(row4, text="No Watermark", variable=self.no_wm_var,
                      font=("Segoe UI", 12), progress_color=GREEN).pack(side="left", padx=(0, 10))

        # Row 5: Veo negative prompt
        row5 = ctk.CTkFrame(settings_inner, fg_color="transparent")
        row5.pack(fill="x", pady=(4, 0))

        ctk.CTkLabel(row5, text="Negative Prompt", font=("Segoe UI", 11, "bold"),
                     text_color=GRAY).pack(side="left", padx=(0, 8))
        self.neg_prompt_var = ctk.StringVar(value="cartoon, anime, text, watermark, blurry, low quality")
        ctk.CTkEntry(row5, textvariable=self.neg_prompt_var, height=30,
                     font=("Consolas", 11), fg_color=INPUT_BG,
                     placeholder_text="Nội dung không muốn xuất hiện...").pack(side="left", fill="x", expand=True)

        # ========== REFERENCE IMAGES ==========
        ref_card = ctk.CTkFrame(self.main_scroll, fg_color=CARD_BG, corner_radius=12)
        ref_card.pack(fill="x", pady=(0, 8))

        ref_header = ctk.CTkFrame(ref_card, fg_color="transparent")
        ref_header.pack(fill="x", padx=15, pady=(10, 4))
        ctk.CTkLabel(ref_header, text="Reference Images",
                     font=("Segoe UI", 13, "bold")).pack(side="left")
        ctk.CTkLabel(ref_header, text="Helps AI keep characters & scenes consistent",
                     font=("Segoe UI", 11), text_color=GRAY).pack(side="right")

        ref_inner = ctk.CTkFrame(ref_card, fg_color="transparent")
        ref_inner.pack(fill="x", padx=15, pady=(0, 12))

        # Subject reference
        self.subject_refs: list[str] = []
        subj_frame = ctk.CTkFrame(ref_inner, fg_color=INPUT_BG, corner_radius=8)
        subj_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        subj_top = ctk.CTkFrame(subj_frame, fg_color="transparent")
        subj_top.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(subj_top, text="Subject / Character",
                     font=("Segoe UI", 12, "bold")).pack(side="left")
        ctk.CTkButton(subj_top, text="+ Add", width=60, height=28,
                      fg_color="#3a3a3a", hover_color="#4a4a4a",
                      command=self._add_subject_ref).pack(side="right")

        self.subj_preview_frame = ctk.CTkFrame(subj_frame, fg_color="transparent")
        self.subj_preview_frame.pack(fill="x", padx=10, pady=(0, 8))
        self.subj_label = ctk.CTkLabel(self.subj_preview_frame, text="No images",
                                       font=("Segoe UI", 11), text_color=GRAY)
        self.subj_label.pack(anchor="w")

        # Background reference
        self.bg_refs: list[str] = []
        bg_frame = ctk.CTkFrame(ref_inner, fg_color=INPUT_BG, corner_radius=8)
        bg_frame.pack(side="left", fill="both", expand=True, padx=(6, 0))

        bg_top = ctk.CTkFrame(bg_frame, fg_color="transparent")
        bg_top.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(bg_top, text="Background / Scene",
                     font=("Segoe UI", 12, "bold")).pack(side="left")
        ctk.CTkButton(bg_top, text="+ Add", width=60, height=28,
                      fg_color="#3a3a3a", hover_color="#4a4a4a",
                      command=self._add_bg_ref).pack(side="right")

        self.bg_preview_frame = ctk.CTkFrame(bg_frame, fg_color="transparent")
        self.bg_preview_frame.pack(fill="x", padx=10, pady=(0, 8))
        self.bg_label = ctk.CTkLabel(self.bg_preview_frame, text="No images",
                                     font=("Segoe UI", 11), text_color=GRAY)
        self.bg_label.pack(anchor="w")

        # ========== PROMPT EDITOR ==========
        self.prompt_editor = PromptEditor(self.main_scroll)
        self.prompt_editor.pack(fill="both", expand=True, pady=8)

        # ========== ACTION BUTTONS ==========
        action_card = ctk.CTkFrame(self.main_scroll, fg_color=CARD_BG, corner_radius=12)
        action_card.pack(fill="x", pady=8)

        action_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        action_inner.pack(fill="x", padx=15, pady=12)

        self.enhance_btn = ctk.CTkButton(
            action_inner, text="Enhance Prompts (ChatGPT)", width=240, height=40,
            fg_color="#8e44ad", hover_color="#9b59b6",
            font=("Segoe UI", 13, "bold"),
            command=self._enhance_prompts)
        self.enhance_btn.pack(side="left")

        self.cost_label = ctk.CTkLabel(action_inner, text="", font=("Segoe UI", 12),
                                       text_color=GRAY)
        self.cost_label.pack(side="left", padx=15)

        self.stop_btn = ctk.CTkButton(
            action_inner, text="Stop", width=80, height=40,
            fg_color=RED, hover_color="#c0392b", state="disabled",
            command=self._stop_generation)
        self.stop_btn.pack(side="right")

        self.gen_btn = ctk.CTkButton(
            action_inner, text="Generate All Videos", width=200, height=40,
            fg_color=GREEN, hover_color="#27ae60",
            font=("Segoe UI", 14, "bold"),
            command=self._start_generation)
        self.gen_btn.pack(side="right", padx=(0, 10))

        # ========== ENHANCED PREVIEW ==========
        preview_card = ctk.CTkFrame(self.main_scroll, fg_color=CARD_BG, corner_radius=12)
        preview_card.pack(fill="x", pady=(0, 8))

        preview_header = ctk.CTkFrame(preview_card, fg_color="transparent")
        preview_header.pack(fill="x", padx=15, pady=(10, 0))
        ctk.CTkLabel(preview_header, text="Enhanced Preview",
                     font=("Segoe UI", 13, "bold")).pack(side="left")
        ctk.CTkLabel(preview_header, text="After ChatGPT processing",
                     font=("Segoe UI", 11), text_color=GRAY).pack(side="right")

        self.preview_text = ctk.CTkTextbox(preview_card, height=100, font=("Consolas", 11),
                                           fg_color=INPUT_BG, corner_radius=8, state="disabled")
        self.preview_text.pack(fill="x", padx=15, pady=(5, 12))

        # ========== PROGRESS ==========
        progress_card = ctk.CTkFrame(self.main_scroll, fg_color=CARD_BG, corner_radius=12)
        progress_card.pack(fill="x", pady=(0, 8))

        progress_inner = ctk.CTkFrame(progress_card, fg_color="transparent")
        progress_inner.pack(fill="x", padx=15, pady=12)

        prog_top = ctk.CTkFrame(progress_inner, fg_color="transparent")
        prog_top.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(prog_top, text="Progress", font=("Segoe UI", 13, "bold")).pack(side="left")
        self.progress_label = ctk.CTkLabel(prog_top, text="Ready",
                                           font=("Segoe UI", 12, "bold"), text_color=ACCENT)
        self.progress_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(progress_inner, height=8,
                                                progress_color=GREEN, corner_radius=4)
        self.progress_bar.pack(fill="x", pady=(0, 8))
        self.progress_bar.set(0)

        # Scene status list
        self.scene_list_frame = ctk.CTkFrame(progress_inner, fg_color="transparent")
        self.scene_list_frame.pack(fill="x")

        # ========== LOG ==========
        log_card = ctk.CTkFrame(self.main_scroll, fg_color=CARD_BG, corner_radius=12)
        log_card.pack(fill="x")

        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.pack(fill="x", padx=15, pady=(10, 0))
        ctk.CTkLabel(log_header, text="Log", font=("Segoe UI", 13, "bold")).pack(side="left")

        self.log_text = ctk.CTkTextbox(log_card, height=120, font=("Consolas", 11),
                                       fg_color="#0d0d0d", text_color="#00ff88",
                                       corner_radius=8, state="disabled")
        self.log_text.pack(fill="x", padx=15, pady=(5, 12))

    def _add_labeled_widget(self, parent, label, widget):
        ctk.CTkLabel(parent, text=label, font=("Segoe UI", 12, "bold"),
                     text_color=GRAY).pack(side="left", padx=(0, 5))
        widget.pack(side="left", padx=(0, 15))

    # ─── Reference Images ─────────────────────────────────────────

    def _add_subject_ref(self):
        paths = filedialog.askopenfilenames(
            title="Select Subject / Character Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")]
        )
        for p in paths:
            if p and p not in self.subject_refs:
                self.subject_refs.append(p)
        self._refresh_ref_preview(self.subj_preview_frame, self.subj_label,
                                  self.subject_refs, "subject")

    def _add_bg_ref(self):
        paths = filedialog.askopenfilenames(
            title="Select Background / Scene Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")]
        )
        for p in paths:
            if p and p not in self.bg_refs:
                self.bg_refs.append(p)
        self._refresh_ref_preview(self.bg_preview_frame, self.bg_label,
                                  self.bg_refs, "bg")

    def _refresh_ref_preview(self, frame, label, ref_list, ref_type):
        for w in frame.winfo_children():
            w.destroy()

        if not ref_list:
            label = ctk.CTkLabel(frame, text="No images",
                                 font=("Segoe UI", 11), text_color=GRAY)
            label.pack(anchor="w")
            return

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x")

        for i, path in enumerate(ref_list):
            item = ctk.CTkFrame(row, fg_color="#333333", corner_radius=6)
            item.pack(side="left", padx=(0, 6), pady=2)

            try:
                from PIL import Image
                img = Image.open(path)
                img.thumbnail((50, 50))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(50, 50))
                ctk.CTkLabel(item, image=ctk_img, text="").pack(side="left", padx=4, pady=4)
            except Exception:
                pass

            name = os.path.basename(path)
            if len(name) > 15:
                name = name[:12] + "..."
            ctk.CTkLabel(item, text=name, font=("Segoe UI", 10),
                         text_color="#aaaaaa").pack(side="left", padx=(0, 4))

            ctk.CTkButton(item, text="x", width=24, height=24,
                          fg_color="#555555", hover_color=RED,
                          font=("Segoe UI", 11),
                          command=lambda idx=i, rt=ref_type: self._remove_ref(idx, rt)
                          ).pack(side="left", padx=(0, 4))

        total = len(ref_list)
        ctk.CTkLabel(row, text=f"{total} image{'s' if total > 1 else ''}",
                     font=("Segoe UI", 10), text_color=GRAY).pack(side="left", padx=8)

    def _remove_ref(self, idx, ref_type):
        if ref_type == "subject":
            self.subject_refs.pop(idx)
            self._refresh_ref_preview(self.subj_preview_frame, self.subj_label,
                                      self.subject_refs, "subject")
        else:
            self.bg_refs.pop(idx)
            self._refresh_ref_preview(self.bg_preview_frame, self.bg_label,
                                      self.bg_refs, "bg")

    # ─── Actions ──────────────────────────────────────────────────

    def _open_settings(self):
        SettingsDialog(self)
        self.config_data = load_config()

    def _browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_var.set(folder)

    def _log(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}]  {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _get_provider(self):
        name = self.provider_var.get()
        key_name, provider_cls = PROVIDERS[name]
        api_key = get_api_key(self.config_data, key_name)
        if not api_key:
            messagebox.showerror("Error", f"No API key for {name}.\nOpen Settings to add it.")
            return None

        if key_name == "veo3":
            return provider_cls(
                api_key,
                model=self.veo_model_var.get(),
                aspect_ratio=self.aspect_var.get(),
                resolution=self.res_var.get(),
                generate_audio=self.audio_var.get(),
                no_watermark=self.no_wm_var.get(),
                negative_prompt=self.neg_prompt_var.get(),
                subject_refs=list(self.subject_refs),
                bg_refs=list(self.bg_refs),
            )
        return provider_cls(api_key)

    # ─── Enhance ──────────────────────────────────────────────────

    def _enhance_prompts(self):
        scenes = self.prompt_editor.get_scenes()
        if not scenes:
            messagebox.showwarning("Warning", "No scenes entered.")
            return

        openai_key = get_api_key(self.config_data, "openai")
        if not openai_key:
            messagebox.showerror("Error", "OpenAI API key required.\nOpen Settings to add it.")
            return

        self.enhance_btn.configure(state="disabled", text="Enhancing...")
        self._log(f"Sending {len(scenes)} scenes to ChatGPT...")

        style = self.prompt_editor.get_style_prefix()
        model = self.config_data.get("settings", {}).get("chatgpt_model", "gpt-4o")

        def run():
            try:
                result = enhance_prompts_chunked(openai_key, scenes, style, model)
                self.after(0, lambda: self._on_enhance_done(result))
            except Exception as e:
                self.after(0, lambda: self._on_enhance_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _on_enhance_done(self, result: dict):
        self.enhanced_data = result
        self.enhance_btn.configure(state="normal", text="Enhance Prompts (ChatGPT)")

        bible = result.get("character_bible", "")
        style = result.get("style_guide", "")
        scenes = result.get("scenes", [])

        preview = f"CHARACTER BIBLE:\n{bible}\n\nSTYLE: {style}\n"
        for s in scenes:
            preview += f"\n#{s['id']}: {s['enhanced_prompt']}\n"

        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", preview)
        self.preview_text.configure(state="disabled")

        self._log(f"ChatGPT enhanced {len(scenes)} scenes successfully!")
        self._update_cost()

    def _on_enhance_error(self, error: str):
        self.enhance_btn.configure(state="normal", text="Enhance Prompts (ChatGPT)")
        self._log(f"ChatGPT ERROR: {error}")
        messagebox.showerror("ChatGPT Error", error)

    def _update_cost(self):
        provider = self._get_provider()
        if not provider:
            return
        scenes = self.prompt_editor.get_scenes()
        dur = int(self.dur_var.get())
        cost = provider.get_cost_estimate(dur, self.res_var.get()) * len(scenes)
        self.cost_label.configure(text=f"Est. ~${cost:.2f}  ({len(scenes)} videos)")

    # ─── Generate ─────────────────────────────────────────────────

    def _start_generation(self):
        scenes_raw = self.prompt_editor.get_scenes()
        if not scenes_raw:
            messagebox.showwarning("Warning", "No scenes entered.")
            return

        provider = self._get_provider()
        if not provider:
            return

        output = self.output_var.get()
        if not output:
            messagebox.showwarning("Warning", "Select output folder.")
            return

        # Build scene tasks
        enhanced_scenes = {}
        if self.enhanced_data and self.enhance_var.get():
            for s in self.enhanced_data.get("scenes", []):
                enhanced_scenes[s["id"]] = s.get("enhanced_prompt", "")

        scene_tasks = []
        for raw in scenes_raw:
            sid = raw["id"]
            enhanced = enhanced_scenes.get(sid, "")
            if enhanced and self.enhanced_data:
                style = self.enhanced_data.get("style_guide", "")
                if style and style not in enhanced:
                    enhanced = f"{enhanced}. {style}"
            task = SceneTask(sid, raw["prompt"], enhanced)
            scene_tasks.append(task)

        # Task manager
        self.task_manager = TaskManager(
            provider=provider,
            output_folder=output,
            frame_chaining=self.chain_var.get(),
            seed=int(self.seed_var.get() or 0),
            duration=int(self.dur_var.get()),
            resolution=self.res_var.get(),
            subject_refs=list(self.subject_refs),
            bg_refs=list(self.bg_refs),
        )
        self.task_manager.load_scenes(scene_tasks)
        self.task_manager.set_callbacks(
            on_update=lambda: self.after(0, self._update_progress),
            on_log=lambda msg: self.after(0, self._log, msg),
            on_complete=lambda: self.after(0, self._on_generation_complete),
        )

        # Build scene status list
        for w in self.scene_list_frame.winfo_children():
            w.destroy()
        self.scene_labels.clear()

        # Header
        header = ctk.CTkFrame(self.scene_list_frame, fg_color="#222222", corner_radius=6)
        header.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(header, text="#", width=40, font=("Segoe UI", 11, "bold"),
                     text_color=GRAY).pack(side="left", padx=8)
        ctk.CTkLabel(header, text="Scene Prompt", font=("Segoe UI", 11, "bold"),
                     text_color=GRAY).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(header, text="Status", width=120, font=("Segoe UI", 11, "bold"),
                     text_color=GRAY).pack(side="right", padx=8)

        for t in scene_tasks:
            row = ctk.CTkFrame(self.scene_list_frame, fg_color="transparent", height=28)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=str(t.scene_id), width=40,
                         font=("Consolas", 11), text_color=GRAY).pack(side="left", padx=8)

            short = t.prompt[:55] + "..." if len(t.prompt) > 55 else t.prompt
            ctk.CTkLabel(row, text=short, font=("Segoe UI", 11),
                         text_color="#cccccc", anchor="w").pack(side="left", fill="x", expand=True)

            status_lbl = ctk.CTkLabel(row, text="Pending", width=120,
                                      font=("Segoe UI", 11, "bold"), text_color=GRAY)
            status_lbl.pack(side="right", padx=8)
            self.scene_labels[t.scene_id] = status_lbl

        # Cost confirmation
        cost = self.task_manager.estimate_cost()
        n = len(scene_tasks)
        chain_txt = "ON" if self.chain_var.get() else "OFF"
        if not messagebox.askyesno("Confirm Generation",
            f"Generate {n} videos?\n\n"
            f"Provider: {self.provider_var.get()}\n"
            f"Est. cost: ~${cost:.2f}\n"
            f"Frame chaining: {chain_txt}\n\n"
            f"Output: {output}\n"
            f"Files: 1.mp4, 2.mp4 ... {n}.mp4"):
            return

        self.gen_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self._log(f"Starting: {n} scenes | {self.provider_var.get()} | chain={chain_txt}")
        self.task_manager.start()

    def _stop_generation(self):
        if self.task_manager:
            self.task_manager.stop()
        self.gen_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._log("Generation stopped by user.")

    def _update_progress(self):
        if not self.task_manager:
            return

        completed = 0
        total = len(self.task_manager.scenes)

        for t in self.task_manager.scenes:
            lbl = self.scene_labels.get(t.scene_id)
            if not lbl:
                continue

            display_map = {
                "pending": "Pending",
                "submitting": "Submitting...",
                "processing": "Generating...",
                "downloading": "Downloading...",
                "completed": "Done",
                "failed": "FAILED",
            }
            display = display_map.get(t.status, t.status)
            color = STATUS_COLORS.get(t.status, GRAY)
            lbl.configure(text=display, text_color=color)

            if t.status == "completed":
                completed += 1

        if total > 0:
            pct = completed / total
            self.progress_bar.set(pct)
            self.progress_label.configure(text=f"{completed}/{total}  ({pct*100:.0f}%)")

    def _on_generation_complete(self):
        self.gen_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._update_progress()

        completed = sum(1 for s in self.task_manager.scenes if s.status == "completed")
        total = len(self.task_manager.scenes)
        failed = sum(1 for s in self.task_manager.scenes if s.status == "failed")

        msg = f"Done! {completed}/{total} videos generated."
        if failed > 0:
            msg += f"\n{failed} scene(s) failed."
        self._log(msg)
        messagebox.showinfo("Complete", msg)
