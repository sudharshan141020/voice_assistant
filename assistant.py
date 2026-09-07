# =============================================================================
# VOICE ASSISTANT - with mini‑brain (repeat last command)
# Wake: pixel / alexa
# =============================================================================

import os
import json
import threading
import datetime
import time
import webbrowser
import subprocess
import re
import ctypes
from tkinter import *
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk

import speech_recognition as sr
import pyttsx3
import pywhatkit as kit
import requests
import wikipedia

# -----------------------------------------------------------------------------
# Optional imports
# -----------------------------------------------------------------------------
try:
    import pyautogui
    PY_AUTOGUI_AVAILABLE = True
except ImportError:
    PY_AUTOGUI_AVAILABLE = False

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False

# -----------------------------------------------------------------------------
# SIMPLE MEMORY
# -----------------------------------------------------------------------------
MEMORY_FILE = "memory.json"

class Memory:
    def __init__(self):
        self.data = self.load()

    def load(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save(self):
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def remember(self, key, value):
        self.data[key] = value
        self.save()

    def recall(self, key):
        return self.data.get(key, None)

    def search(self, text):
        matches = {}
        for k, v in self.data.items():
            if k.lower() in text.lower() or text.lower() in k.lower():
                matches[k] = v
        return matches

# -----------------------------------------------------------------------------
# COMMAND PROCESSOR (with mini‑brain)
# -----------------------------------------------------------------------------
class CommandProcessor:
    def __init__(self, gui):
        self.gui = gui
        self.memory = Memory()
        self.engine = None
        self.speak_func = None

        # ---- Mini‑brain: store last command and response ----
        self.last_instruction = None
        self.last_response = None
        self._processing_repeat = False   # avoid infinite loops

    def set_tts(self, engine, speak_func):
        self.engine = engine
        self.speak_func = speak_func

    def _extract_number(self, text):
        nums = re.findall(r'\d+', text)
        return int(nums[0]) if nums else None

    def _extract_query(self, text, keywords):
        for kw in keywords:
            text = text.replace(kw, "")
        return text.strip()

    def _set_volume_absolute(self, level):
        print(f"Setting volume to {level}%")

    def _change_volume_relative(self, delta):
        if PY_AUTOGUI_AVAILABLE:
            key = "volumeup" if delta > 0 else "volumedown"
            presses = abs(delta) // 2
            pyautogui.press(key, presses=presses)
        else:
            print("pyautogui not installed; can't change volume.")

    def _toggle_media_pause(self):
        if PY_AUTOGUI_AVAILABLE:
            pyautogui.press("playpause")
        else:
            print("pyautogui not installed; can't pause.")

    def _is_media_window_open(self):
        if PYGETWINDOW_AVAILABLE:
            media_keywords = ["youtube", "spotify", "music", "player", "sound", "audio", "netflix", "prime", "vimeo"]
            windows = gw.getAllWindows()
            for win in windows:
                if win.title:
                    title_lower = win.title.lower()
                    for kw in media_keywords:
                        if kw in title_lower:
                            return True
            return False
        return False

    def _switch_to_window(self, title_keyword):
        if PYGETWINDOW_AVAILABLE:
            windows = gw.getWindowsWithTitle(title_keyword)
            if windows:
                windows[0].activate()
                return True
            return False
        else:
            print("pygetwindow not installed; install with: pip install pygetwindow")
            return False

    def process(self, instruction):
        instruction = instruction.lower().strip()
        if not instruction:
            return "I didn't hear anything."

        # ---------- REPEAT LAST COMMAND (mini‑brain) ----------
        if instruction in ["repeat", "do that again", "say that again", "repeat last command", "again"]:
            if self._processing_repeat:
                return "I'm already repeating the last command."
            if self.last_instruction is not None:
                self._processing_repeat = True
                try:
                    # Re‑run the last instruction
                    response = self.process(self.last_instruction)
                    return response
                finally:
                    self._processing_repeat = False
            else:
                return "I don't have any previous command to repeat."

        # ---------- SLEEP / SHUTDOWN / RESTART ----------
        if any(w in instruction for w in ["sleep", "go to sleep"]):
            self.gui.go_to_sleep()
            response = f"Going to sleep. Say {', '.join(self.gui.wake_phrases)} to wake me up."
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- CONTEXT-AWARE "STOP" ----------
        if instruction in ["stop", "exit", "goodbye"]:
            if self._is_media_window_open():
                self._toggle_media_pause()
                response = "Paused (media detected)."
            else:
                self.gui.stop_listening()
                self.gui.root.after(500, self.gui.root.destroy)
                response = "Goodbye!"
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- SHUTDOWN / RESTART (if combined with other words) ----------
        if "shutdown" in instruction:
            self._shutdown_pc()
            response = "Shutting down PC. Goodbye!"
            self.last_instruction = instruction
            self.last_response = response
            return response

        if "restart" in instruction or "reboot" in instruction:
            self._restart_pc()
            response = "Restarting PC. Goodbye!"
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- CLOSE APP ----------
        if "close" in instruction:
            app = instruction.replace("close", "").strip()
            if app:
                app_map = {
                    "spotify": "spotify.exe",
                    "notepad": "notepad.exe",
                    "chrome": "chrome.exe",
                    "firefox": "firefox.exe",
                    "calculator": "calc.exe",
                    "paint": "mspaint.exe",
                    "explorer": "explorer.exe",
                    "cmd": "cmd.exe",
                    "word": "winword.exe",
                    "excel": "excel.exe",
                    "powerpoint": "powerpnt.exe",
                    "outlook": "outlook.exe",
                    "discord": "discord.exe",
                    "slack": "slack.exe",
                    "edge": "msedge.exe",
                    "code": "code.exe",
                    "teams": "teams.exe",
                }
                exe = app_map.get(app.lower(), app + ".exe")
                try:
                    os.system(f"taskkill /f /im {exe}")
                    response = f"Closed {app}."
                except Exception:
                    response = f"Could not close {app}."
            else:
                response = "What would you like me to close?"
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- COLLAPSE ----------
        if "collapse" in instruction or "show desktop" in instruction:
            try:
                ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
                ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)
                response = "Collapsed all windows."
            except:
                if PY_AUTOGUI_AVAILABLE:
                    pyautogui.hotkey('win', 'd')
                    response = "Collapsed all windows."
                else:
                    response = "Could not collapse windows."
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- SWITCH TO WINDOW ----------
        if "switch to" in instruction:
            target = instruction.replace("switch to", "").strip()
            if target:
                if self._switch_to_window(target):
                    response = f"Switched to {target}."
                else:
                    response = f"Could not find a window matching '{target}'."
            else:
                response = "What window would you like to switch to?"
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- VOLUME ----------
        if "volume" in instruction:
            set_match = re.search(r'set volume to (\d+)', instruction)
            if set_match:
                level = int(set_match.group(1))
                self._set_volume_absolute(level)
                response = f"Volume set to {level}%."
            else:
                inc_match = re.search(r'increase volume by (\d+)', instruction)
                if inc_match:
                    delta = int(inc_match.group(1))
                    self._change_volume_relative(delta)
                    response = f"Increased volume by {delta}%."
                else:
                    dec_match = re.search(r'decrease volume by (\d+)', instruction)
                    if dec_match:
                        delta = int(dec_match.group(1))
                        self._change_volume_relative(-delta)
                        response = f"Decreased volume by {delta}%."
                    else:
                        if "increase" in instruction or "up" in instruction:
                            self._change_volume_relative(10)
                            response = "Volume increased."
                        elif "decrease" in instruction or "down" in instruction:
                            self._change_volume_relative(-10)
                            response = "Volume decreased."
                        elif "mute" in instruction:
                            if PY_AUTOGUI_AVAILABLE:
                                pyautogui.press("volumemute")
                                response = "Toggled mute."
                            else:
                                response = "pyautogui not installed."
                        else:
                            num = self._extract_number(instruction)
                            if num is not None:
                                self._set_volume_absolute(num)
                                response = f"Volume set to {num}%."
                            else:
                                response = "Please say 'set volume to 30' or 'increase volume by 10'."
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- SCREENSHOT ----------
        if "screenshot" in instruction:
            self._take_screenshot()
            response = "Screenshot taken and saved."
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- OPEN APP (generic) ----------
        if ("open" in instruction or "launch" in instruction) and not (
            "google" in instruction or "youtube" in instruction or
            "spotify" in instruction or "settings" in instruction
        ):
            app = instruction.replace("open", "").replace("launch", "").strip()
            if app:
                self._open_application(app)
                response = f"Opening {app}."
            else:
                response = "What would you like to open?"
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- SPOTIFY (improved auto‑play) ----------
        if "spotify" in instruction:
            if "play" in instruction:
                query = instruction
                for word in ["play", "spotify", "open", "and", "song", "music", "on"]:
                    query = query.replace(word, "")
                query = query.strip()
                if query:
                    try:
                        if PYGETWINDOW_AVAILABLE:
                            spotify_windows = gw.getWindowsWithTitle("Spotify")
                            if not spotify_windows:
                                subprocess.Popen("spotify")
                                time.sleep(3)
                        else:
                            subprocess.Popen("spotify")
                            time.sleep(3)

                        os.startfile(f"spotify:search:{query}")
                        time.sleep(3.5)

                        if PYGETWINDOW_AVAILABLE:
                            spotify_windows = gw.getWindowsWithTitle("Spotify")
                            if spotify_windows:
                                spotify_windows[0].activate()
                                time.sleep(0.5)

                        if PY_AUTOGUI_AVAILABLE:
                            pyautogui.press('tab')
                            time.sleep(0.2)
                            pyautogui.press('tab')
                            time.sleep(0.2)
                            pyautogui.press('enter')
                            response = f"Searching for '{query}' on Spotify and playing the first result."
                        else:
                            response = f"Searching for '{query}' on Spotify (pyautogui missing – cannot auto‑play)."
                    except Exception as e:
                        webbrowser.open(f"https://open.spotify.com/search/{query}")
                        response = f"Searching for '{query}' on Spotify web (auto‑play failed: {str(e)})"
                else:
                    try:
                        subprocess.Popen("spotify")
                        response = "Opening Spotify app."
                    except:
                        webbrowser.open("https://open.spotify.com")
                        response = "Opening Spotify web."
            else:
                try:
                    subprocess.Popen("spotify")
                    response = "Opening Spotify app."
                except:
                    webbrowser.open("https://open.spotify.com")
                    response = "Opening Spotify web."
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- YOUTUBE (before generic media controls) ----------
        if "youtube" in instruction and ("search" in instruction or "open" in instruction or "play" in instruction):
            query = self._extract_query(instruction, ["youtube", "search", "open", "play"])
            if query:
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
                response = f"Searching YouTube for {query}."
            else:
                response = "What would you like to search on YouTube?"
            self.last_instruction = instruction
            self.last_response = response
            return response
        elif "youtube" in instruction and "open" in instruction:
            webbrowser.open("https://www.youtube.com")
            response = "Opening YouTube."
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- GENERIC MEDIA CONTROLS ----------
        if any(w in instruction for w in ["pause", "resume", "play", "stop music", "play music"]):
            self._toggle_media_pause()
            response = "Toggled play/pause."
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- GOOGLE ----------
        if "google" in instruction and ("search" in instruction or "open" in instruction):
            query = self._extract_query(instruction, ["google", "search", "open"])
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query}")
                response = f"Searching Google for {query}."
            else:
                response = "What would you like to search on Google?"
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- WIKIPEDIA ----------
        if "wikipedia" in instruction or "wiki" in instruction:
            query = self._extract_query(instruction, ["wikipedia", "wiki"])
            if query:
                try:
                    summary = wikipedia.summary(query, sentences=2)
                    response = f"Wikipedia says: {summary}"
                except:
                    response = f"Sorry, I couldn't find information on {query}."
            else:
                response = "What would you like to search on Wikipedia?"
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- WEATHER ----------
        if "weather" in instruction or "temperature" in instruction:
            city = "London"
            try:
                url = f"https://wttr.in/{city}?format=%C+%t"
                weather_text = requests.get(url).text.strip()
                response = f"The weather in {city}: {weather_text}"
            except:
                response = "I couldn't fetch the weather right now."
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- TIME ----------
        if "time" in instruction:
            now = datetime.datetime.now().strftime("%I:%M %p")
            response = f"The current time is {now}"
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- DATE ----------
        if "date" in instruction:
            today = datetime.datetime.now().strftime("%B %d, %Y")
            response = f"Today is {today}"
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- CALCULATOR ----------
        if "calculate" in instruction or "calculator" in instruction or "what is" in instruction:
            expr = self._extract_query(instruction, ["calculate", "calculator", "what is"])
            expr = expr.replace("plus", "+").replace("minus", "-")
            expr = expr.replace("times", "*").replace("multiplied by", "*")
            expr = expr.replace("divided by", "/").replace("divided", "/")
            try:
                result = eval(expr)
                response = f"The result is {result}"
            except:
                response = "I couldn't compute that."
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- NEXT / PREVIOUS ----------
        if "next" in instruction and ("song" in instruction or "track" in instruction):
            if PY_AUTOGUI_AVAILABLE:
                pyautogui.press("nexttrack")
                response = "Skipped to next track."
            else:
                response = "pyautogui not installed."
            self.last_instruction = instruction
            self.last_response = response
            return response
        if "previous" in instruction and ("song" in instruction or "track" in instruction):
            if PY_AUTOGUI_AVAILABLE:
                pyautogui.press("prevtrack")
                response = "Previous track."
            else:
                response = "pyautogui not installed."
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- MEMORY ----------
        if "remember" in instruction:
            parts = instruction.split("remember", 1)
            if len(parts) > 1:
                fact = parts[1].strip()
                if fact:
                    if " is " in fact:
                        key, value = fact.split(" is ", 1)
                        key = key.strip()
                        value = value.strip()
                        self.memory.remember(key, value)
                        response = f"Okay, I remembered that {key} is {value}."
                    else:
                        self.memory.remember(fact, "yes")
                        response = f"Okay, I remembered: {fact}"
                else:
                    response = "What would you like me to remember?"
            else:
                response = "What would you like me to remember?"
            self.last_instruction = instruction
            self.last_response = response
            return response

        if any(w in instruction for w in ["what is", "do you remember", "recall", "tell me about"]):
            key = None
            for phrase in ["what is", "do you remember", "recall", "tell me about"]:
                if phrase in instruction:
                    key = instruction.split(phrase, 1)[1].strip()
                    break
            if not key:
                key = instruction
            if key:
                matches = self.memory.search(key)
                if matches:
                    if len(matches) == 1:
                        k, v = list(matches.items())[0]
                        response = f"You told me that {k} is {v}."
                    else:
                        lines = ["Here's what I remember:"]
                        for k, v in matches.items():
                            lines.append(f"- {k}: {v}")
                        response = "\n".join(lines)
                else:
                    val = self.memory.recall(key)
                    if val:
                        response = f"You told me: {key} is {val}."
                    else:
                        response = "I don't remember anything about that."
            else:
                response = "What would you like me to recall?"
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- WHO ARE YOU / HELP ----------
        if "who are you" in instruction or "what is your name" in instruction:
            response = f"I am {self.gui.config.get('assistant_name', 'Assistant')}, your voice assistant."
            self.last_instruction = instruction
            self.last_response = response
            return response

        if "help" in instruction or "what can you do" in instruction:
            response = ("I can search the web, control your PC, remember facts, tell time, calculate, "
                        "control Spotify, close apps, collapse windows, switch windows, and more.\n"
                        "Try: 'remember that my name is Alex', 'what is my name',\n"
                        "'set volume to 30', 'increase volume by 20',\n"
                        "'pause', 'switch to YouTube', 'close spotify', 'collapse'.\n"
                        "Wake words: pixel or alexa. Say 'sleep' to idle, 'stop' to pause if media is playing, else exit.")
            self.last_instruction = instruction
            self.last_response = response
            return response

        # ---------- FALLBACK ----------
        if instruction in self.memory.data:
            val = self.memory.recall(instruction)
            response = f"You told me: {instruction} is {val}."
            self.last_instruction = instruction
            self.last_response = response
            return response

        response = "I'm not sure how to handle that. Try saying 'help' for ideas."
        self.last_instruction = instruction
        self.last_response = response
        return response

    # ---- Action methods ----
    def _open_application(self, app_name):
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "cmd": "cmd.exe",
            "explorer": "explorer.exe",
            "firefox": "firefox",
            "chrome": "chrome",
            "settings": "ms-settings:",
        }
        key = app_name.lower()
        if key in app_map:
            try:
                subprocess.Popen(app_map[key])
            except:
                webbrowser.open(app_map[key])
        else:
            try:
                subprocess.Popen(key)
            except:
                try:
                    subprocess.Popen(key + ".exe")
                except:
                    webbrowser.open(key)

    def _take_screenshot(self):
        if PY_AUTOGUI_AVAILABLE:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            pyautogui.screenshot(filename)
            print(f"Screenshot saved as {filename}")
        else:
            print("pyautogui not available.")

    def _shutdown_pc(self):
        os.system("shutdown /s /t 5")

    def _restart_pc(self):
        os.system("shutdown /r /t 5")

# -----------------------------------------------------------------------------
# GUI (Tkinter) – Auto‑start listening
# -----------------------------------------------------------------------------
class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant")
        self.root.geometry("700x600")
        self.root.resizable(False, False)

        self.config = self.load_config()
        self.assistant_name = self.config.get("assistant_name", "Assistant")

        self.engine = pyttsx3.init()
        self.setup_tts()

        self.processor = CommandProcessor(self)
        self.processor.set_tts(self.engine, self.speak)

        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.listening = False

        self.primary_wake = self.config.get("wake_word", "pixel")
        self.wake_phrases = [self.primary_wake.lower(), "alexa"]
        self.mode = "idle"

        self.history = []

        self.setup_ui()

        wake_list = ', '.join(self.wake_phrases)
        self.add_conversation("System", f"Assistant ready. Say {wake_list} to wake me up.")

        self.root.after(1000, self.start_listening)

        try:
            self.root.iconbitmap("assistant.ico")
        except:
            pass

    def load_config(self):
        default = {
            "assistant_name": "Assistant",
            "wake_word": "pixel",
            "voice_id": 0,
            "speech_rate": 150,
            "volume": 0.8,
            "wake_word_enabled": True,
            "theme": "light",
            "default_browser": "chrome",
        }
        config_file = "assistant_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_config(self):
        with open("assistant_config.json", 'w') as f:
            json.dump(self.config, f, indent=2)

    def setup_tts(self):
        voices = self.engine.getProperty('voices')
        voice_id = self.config.get("voice_id", 0)
        if voices and voice_id < len(voices):
            self.engine.setProperty('voice', voices[voice_id].id)
        self.engine.setProperty('rate', self.config.get("speech_rate", 150))
        self.engine.setProperty('volume', self.config.get("volume", 0.8))

    def speak(self, text):
        if not text:
            return
        self.add_conversation("Assistant", text)
        self.engine.say(text)
        self.engine.runAndWait()

    def go_to_sleep(self):
        self.mode = "idle"
        wake_list = ', '.join(self.wake_phrases)
        self.update_status(f"Idle (waiting for {wake_list})")
        self.add_conversation("System", f"Sleeping. Say {wake_list} to wake.")

    def wake_up(self):
        self.mode = "active"
        self.update_status("Active")
        self.speak("I'm awake. How can I help?")

    def setup_ui(self):
        main_frame = Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=BOTH, expand=True)

        title = Label(main_frame, text="VOICE ASSISTANT", font=("Helvetica", 20, "bold"),
                      fg="white", bg="#2c3e50")
        title.pack(pady=10)

        self.last_command_label = Label(main_frame, text="", font=("Helvetica", 14, "bold"),
                                        fg="#f1c40f", bg="#2c3e50", wraplength=600)
        self.last_command_label.pack(pady=5)

        self.status_var = StringVar(value="Idle (waiting for pixel, alexa)")
        status_frame = Frame(main_frame, bg="#34495e")
        status_frame.pack(fill=X, padx=20, pady=5)
        Label(status_frame, textvariable=self.status_var, font=("Helvetica", 12),
              fg="white", bg="#34495e").pack(side=LEFT, padx=5)

        self.mic_label = Label(main_frame, text="💤", font=("Helvetica", 48), bg="#2c3e50")
        self.mic_label.pack(pady=10)

        conv_frame = Frame(main_frame, bg="#2c3e50")
        conv_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        self.conv_text = scrolledtext.ScrolledText(conv_frame, height=12, font=("Consolas", 10),
                                                   bg="#ecf0f1", state='disabled')
        self.conv_text.pack(fill=BOTH, expand=True)

        self.command_var = StringVar()
        Entry(main_frame, textvariable=self.command_var, font=("Consolas", 11),
              bg="#ecf0f1").pack(fill=X, padx=20, pady=5)

        btn_frame = Frame(main_frame, bg="#2c3e50")
        btn_frame.pack(pady=10)

        self.start_btn = Button(btn_frame, text="▶ START", font=("Helvetica", 12),
                                command=self.start_listening, bg="#27ae60", fg="white",
                                padx=20, pady=5)
        self.start_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = Button(btn_frame, text="⏹ STOP", font=("Helvetica", 12),
                               command=self.stop_listening, bg="#e74c3c", fg="white",
                               padx=20, pady=5, state=DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=10)

        self.settings_btn = Button(btn_frame, text="⚙ SETTINGS", font=("Helvetica", 12),
                                   command=self.open_settings, bg="#3498db", fg="white",
                                   padx=20, pady=5)
        self.settings_btn.grid(row=0, column=2, padx=10)

    def add_conversation(self, speaker, message):
        self.conv_text.config(state='normal')
        timestamp = datetime.datetime.now().strftime("%H:%M")
        self.conv_text.insert(END, f"[{timestamp}] {speaker}: {message}\n")
        self.conv_text.see(END)
        self.conv_text.config(state='disabled')

    def update_status(self, status):
        self.status_var.set(status)
        if "Active" in status:
            self.mic_label.config(text="🎙️", fg="#27ae60")
        elif "Idle" in status or "sleep" in status.lower():
            self.mic_label.config(text="💤", fg="white")
        else:
            self.mic_label.config(text="🎙️", fg="white")

    def start_listening(self):
        if self.listening:
            return
        self.listening = True
        self.start_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        self.mode = "idle"
        wake_list = ', '.join(self.wake_phrases)
        self.update_status(f"Idle (waiting for {wake_list})")
        self.add_conversation("System", "Listening...")
        threading.Thread(target=self.listen_loop, daemon=True).start()

    def stop_listening(self):
        self.listening = False
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
        self.update_status("Stopped")
        self.add_conversation("System", "Stopped listening.")

    def listen_loop(self):
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.recognizer.energy_threshold = 150
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.6
            while self.listening:
                try:
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio)
                    text = text.lower().strip()
                    if text:
                        self.command_var.set(text)
                        self.last_command_label.config(text=f"🗣️ {text}")
                        self.add_conversation("You", text)

                        if self.mode == "idle":
                            matched = None
                            for phrase in self.wake_phrases:
                                if text == phrase or text.startswith(phrase + " "):
                                    matched = phrase
                                    break
                            if matched:
                                self.wake_up()
                                command = text[len(matched):].strip()
                                if command:
                                    self.process_command(command)
                            else:
                                wake_list = ', '.join(self.wake_phrases)
                                self.update_status(f"Idle (waiting for {wake_list})")
                        else:
                            self.process_command(text)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    print(f"Listen error: {e}")

        self.update_status("Stopped")
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)

    def process_command(self, text):
        response = self.processor.process(text)
        if response:
            self.add_conversation("Assistant", response)
            self.speak(response)
        if self.mode == "idle":
            wake_list = ', '.join(self.wake_phrases)
            self.update_status(f"Idle (waiting for {wake_list})")
        else:
            self.update_status("Active")

    def open_settings(self):
        settings_win = Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("400x500")
        settings_win.resizable(False, False)

        frame = Frame(settings_win)
        frame.pack(padx=20, pady=20, fill=BOTH, expand=True)

        row = 0

        Label(frame, text="Assistant Name:").grid(row=row, column=0, sticky=W, pady=5)
        name_entry = Entry(frame)
        name_entry.insert(0, self.config.get("assistant_name", "Assistant"))
        name_entry.grid(row=row, column=1, pady=5)
        row += 1

        Label(frame, text="Wake Word:").grid(row=row, column=0, sticky=W, pady=5)
        wake_entry = Entry(frame)
        wake_entry.insert(0, self.config.get("wake_word", "pixel"))
        wake_entry.grid(row=row, column=1, pady=5)
        row += 1

        Label(frame, text="Voice:").grid(row=row, column=0, sticky=W, pady=5)
        voices = self.engine.getProperty('voices')
        voice_names = [f"{v.name} ({v.languages})" for v in voices]
        voice_combo = ttk.Combobox(frame, values=voice_names, state="readonly")
        current_voice_id = self.config.get("voice_id", 0)
        if current_voice_id < len(voices):
            voice_combo.set(voice_names[current_voice_id])
        else:
            voice_combo.set(voice_names[0])
        voice_combo.grid(row=row, column=1, pady=5)
        row += 1

        Label(frame, text="Speech Rate:").grid(row=row, column=0, sticky=W, pady=5)
        rate_scale = Scale(frame, from_=100, to=250, orient=HORIZONTAL)
        rate_scale.set(self.config.get("speech_rate", 150))
        rate_scale.grid(row=row, column=1, pady=5)
        row += 1

        Label(frame, text="Volume:").grid(row=row, column=0, sticky=W, pady=5)
        vol_scale = Scale(frame, from_=0, to=100, orient=HORIZONTAL)
        vol_scale.set(self.config.get("volume", 0.8) * 100)
        vol_scale.grid(row=row, column=1, pady=5)
        row += 1

        Label(frame, text="Note: 'alexa' is also a wake word.", font=("Helvetica", 9), fg="gray").grid(row=row, columnspan=2, pady=5)
        row += 1

        def save_settings():
            self.config["assistant_name"] = name_entry.get()
            new_wake = wake_entry.get().strip().lower()
            if new_wake:
                self.config["wake_word"] = new_wake
                self.primary_wake = new_wake
                self.wake_phrases = [new_wake, "alexa"]
            sel = voice_combo.current()
            self.config["voice_id"] = sel if sel >= 0 else 0
            self.config["speech_rate"] = int(rate_scale.get())
            self.config["volume"] = int(vol_scale.get()) / 100.0
            self.save_config()
            self.setup_tts()
            wake_list = ', '.join(self.wake_phrases)
            self.update_status(f"Idle (waiting for {wake_list})")
            settings_win.destroy()
            self.add_conversation("System", "Settings updated.")

        Button(frame, text="Save", command=save_settings, bg="#2ecc71", fg="white").grid(row=row, columnspan=2, pady=20)

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    root = Tk()
    app = VoiceAssistantGUI(root)
    root.mainloop()