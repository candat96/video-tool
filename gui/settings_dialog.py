import customtkinter as ctk
from tkinter import messagebox
import threading
import requests
import openai

from core.config import load_config, save_config

# Colors
GREEN = "#2ecc71"
RED = "#e74c3c"
BLUE = "#3498db"
GRAY = "#7f8c8d"
CARD_BG = "#2b2b2b"


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("620x580")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.after(100, self.focus_force)

        self.config = load_config()
        self.key_entries = {}
        self.status_labels = {}
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        main = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(main, text="API Keys", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ctk.CTkLabel(main, text="OpenAI key + at least 1 video provider required.",
                     font=("Segoe UI", 12), text_color=GRAY).pack(anchor="w", pady=(2, 15))

        providers = [
            ("openai", "OpenAI (ChatGPT)", "Prompt enhancement engine"),
            ("veo3", "Google Veo 3", "Google AI Studio key"),
            ("runway", "Runway Gen-4", "Runway developer key"),
            ("kling", "Kling AI", "Kling API key"),
            ("minimax", "Minimax Hailuo", "Minimax platform key"),
        ]

        for key, label, hint in providers:
            card = ctk.CTkFrame(main, fg_color=CARD_BG, corner_radius=10)
            card.pack(fill="x", pady=4)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(10, 0))

            ctk.CTkLabel(top_row, text=label, font=("Segoe UI", 13, "bold")).pack(side="left")

            status_lbl = ctk.CTkLabel(top_row, text="", font=("Segoe UI", 11), width=180)
            status_lbl.pack(side="right")
            self.status_labels[key] = status_lbl

            bot_row = ctk.CTkFrame(card, fg_color="transparent")
            bot_row.pack(fill="x", padx=12, pady=(4, 10))

            entry = ctk.CTkEntry(bot_row, show="*", placeholder_text=hint,
                                 height=36, font=("Consolas", 12))
            entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.key_entries[key] = entry

            test_btn = ctk.CTkButton(bot_row, text="Test", width=70, height=36,
                                     fg_color="#3a3a3a", hover_color="#4a4a4a",
                                     command=lambda k=key: self._test_key(k))
            test_btn.pack(side="right")

        # Show/hide
        self.show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(main, text="Show API keys", variable=self.show_var,
                        command=self._toggle_show, font=("Segoe UI", 12)).pack(anchor="w", pady=(12, 0))

        # Model
        model_frame = ctk.CTkFrame(main, fg_color=CARD_BG, corner_radius=10)
        model_frame.pack(fill="x", pady=(12, 0))

        model_inner = ctk.CTkFrame(model_frame, fg_color="transparent")
        model_inner.pack(fill="x", padx=12, pady=12)

        ctk.CTkLabel(model_inner, text="ChatGPT Model", font=("Segoe UI", 13, "bold")).pack(side="left")
        self.model_var = ctk.StringVar(value="gpt-4o")
        ctk.CTkOptionMenu(model_inner, variable=self.model_var,
                          values=["gpt-4o", "gpt-4o-mini"],
                          width=150, height=34).pack(side="right")

        # Buttons
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        ctk.CTkButton(btn_frame, text="Cancel", width=100, height=40,
                      fg_color="#3a3a3a", hover_color="#4a4a4a",
                      command=self.destroy).pack(side="right")

        ctk.CTkButton(btn_frame, text="Save Settings", width=140, height=40,
                      fg_color=GREEN, hover_color="#27ae60",
                      text_color="white", font=("Segoe UI", 13, "bold"),
                      command=self._save).pack(side="right", padx=(0, 10))

    def _load_values(self):
        keys = self.config.get("api_keys", {})
        for key, entry in self.key_entries.items():
            val = keys.get(key, "")
            if val:
                entry.insert(0, val)
        self.model_var.set(self.config.get("settings", {}).get("chatgpt_model", "gpt-4o"))

    def _toggle_show(self):
        show = "" if self.show_var.get() else "*"
        for entry in self.key_entries.values():
            entry.configure(show=show)

    def _test_key(self, provider: str):
        api_key = self.key_entries[provider].get().strip()
        lbl = self.status_labels[provider]
        if not api_key:
            lbl.configure(text="No key entered", text_color=RED)
            return

        lbl.configure(text="Testing...", text_color=BLUE)

        def run_test():
            ok, msg = _test_api_key(provider, api_key)
            self.after(0, lambda: lbl.configure(
                text=msg, text_color=GREEN if ok else RED
            ))

        threading.Thread(target=run_test, daemon=True).start()

    def _save(self):
        for key, entry in self.key_entries.items():
            self.config["api_keys"][key] = entry.get().strip()
        self.config["settings"]["chatgpt_model"] = self.model_var.get()
        save_config(self.config)
        self.destroy()


def _test_api_key(provider: str, api_key: str) -> tuple[bool, str]:
    try:
        if provider == "openai":
            client = openai.OpenAI(api_key=api_key)
            client.models.list()
            return True, "Connected"

        elif provider == "veo3":
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return True, "Valid"
            return False, f"Error {resp.status_code}"

        elif provider == "runway":
            url = "https://api.dev.runwayml.com/v1/tasks"
            headers = {"Authorization": f"Bearer {api_key}", "X-Runway-Version": "2024-11-06"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code in (200, 404):
                return True, "Valid"
            if resp.status_code == 401:
                return False, "Invalid key"
            return False, f"Error {resp.status_code}"

        elif provider == "kling":
            url = "https://api.klingapi.com/v1/videos/text2video"
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code in (200, 405, 404):
                return True, "Valid"
            if resp.status_code == 401:
                return False, "Invalid key"
            return False, f"Error {resp.status_code}"

        elif provider == "minimax":
            url = "https://api.minimaxi.chat/v1/files/retrieve"
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code in (200, 400, 404):
                return True, "Valid"
            if resp.status_code == 401:
                return False, "Invalid key"
            return False, f"Error {resp.status_code}"

        return False, "Unknown"

    except openai.AuthenticationError:
        return False, "Invalid key"
    except requests.ConnectionError:
        return False, "No connection"
    except requests.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"
