# =============================================================================
# VOICE ASSISTANT - Auto‑start listening, context‑aware stop, volume %, etc.
# Wake: pixel / alexa
# =============================================================================

import os
import json
import threading
import datetime
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
# COMMAND PROCESSOR
# -----------------------------------------------------------------------------
class CommandProcessor:
    def __init__(self, gui):
        self.gui = gui
        self.memory = Memory()
        self.engine = None
        self.speak_func = None

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
        # You can replace with pycaw if needed

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
        """Check if any window with media-related title is open."""
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

        # ---------- SLEEP / SHUTDOWN / RESTART ----------
        if any(w in instruction for w in ["sleep", "go to sleep"]):
            self.gui.go_to_sleep()
            return f"Going to sleep. Say {', '.join(self.gui.wake_phrases)} to wake me up."

        # ---------- CONTEXT-AWARE "STOP" ----------
        if instruction in ["stop", "exit", "goodbye"]:
            if self._is_media_window_open():
                self._toggle_media_pause()
                return "Paused (media detected)."
            else:
                self.gui.stop_listening()
                self.gui.root.after(500, self.gui.root.destroy)
                return "Goodbye!"

        # ---------- SHUTDOWN / RESTART (if combined with other words) ----------
        if "shutdown" in instruction:
            self._shutdown_pc()
            return "Shutting down PC. Goodbye!"

        if "restart" in instruction or "reboot" in instruction:
            self._restart_pc()
            return "Restarting PC. Goodbye!"

        # ---------- MEDIA CONTROL ----------
        if any(w in instruction for w in ["pause", "resume", "play", "stop music", "play music"]):
            self._toggle_media_pause()
            return "Toggled play/pause."

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
                    return f"Closed {app}."
                except Exception:
                    return f"Could not close {app}."
            else:
                return "What would you like me to close?"

        # ---------- COLLAPSE ----------
        if "collapse" in instruction or "show desktop" in instruction:
            try:
                ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
                ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)
                return "Collapsed all windows."
            except:
                if PY_AUTOGUI_AVAILABLE:
                    pyautogui.hotkey('win', 'd')
                    return "Collapsed all windows."
                else:
                    return "Could not collapse windows."

        # ---------- SWITCH TO WINDOW ----------
        if "switch to" in instruction:
            target = instruction.replace("switch to", "").strip()
            if target:
                if self._switch_to_window(target):
                    return f"Switched to {target}."
                else:
                    return f"Could not find a window matching '{target}'."
            else:
                return "What window would you like to switch to?"

        # ---------- VOLUME ----------
        if "volume" in instruction:
            set_match = re.search(r'set volume to (\d+)', instruction)
            if set_match:
                level = int(set_match.group(1))
                self._set_volume_absolute(level)
                return f"Volume set to {level}%."

            inc_match = re.search(r'increase volume by (\d+)', instruction)
            if inc_match:
                delta = int(inc_match.group(1))
                self._change_volume_relative(delta)
                return f"Increased volume by {delta}%."

            dec_match = re.search(r'decrease volume by (\d+)', instruction)
            if dec_match:
                delta = int(dec_match.group(1))
                self._change_volume_relative(-delta)
                return f"Decreased volume by {delta}%."

            if "increase" in instruction or "up" in instruction:
                self._change_volume_relative(10)
                return "Volume increased."
            elif "decrease" in instruction or "down" in instruction:
                self._change_volume_relative(-10)
                return "Volume decreased."
            elif "mute" in instruction:
                if PY_AUTOGUI_AVAILABLE:
                    pyautogui.press("volumemute")
                    return "Toggled mute."
                else:
                    return "pyautogui not installed."
            else:
                num = self._extract_number(instruction)
                if num is not None:
                    self._set_volume_absolute(num)
                    return f"Volume set to {num}%."
                else:
                    return "Please say 'set volume to 30' or 'increase volume by 10'."

        # ---------- SCREENSHOT ----------
        if "screenshot" in instruction:
            self._take_screenshot()
            return "Screenshot taken and saved."

        # ---------- OPEN APP ----------
        if ("open" in instruction or "launch" in instruction) and not (
            "google" in instruction or "youtube" in instruction or
            "spotify" in instruction or "settings" in instruction
        ):
            app = instruction.replace("open", "").replace("launch", "").strip()
            if app:
                self._open_application(app)
                return f"Opening {app}."
            else:
                return "What would you like to open?"

        # ---------- GOOGLE ----------
        if "google" in instruction and ("search" in instruction or "open" in instruction):
            query = self._extract_query(instruction, ["google", "search", "open"])
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return f"Searching Google for {query}."
            else:
                return "What would you like to search on Google?"

        # ---------- YOUTUBE ----------
        if "youtube" in instruction and ("search" in instruction or "open" in instruction or "play" in instruction):
            query = self._extract_query(instruction, ["youtube", "search", "open", "play"])
            if query:
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
                return f"Searching YouTube for {query}."
            else:
                return "What would you like to search on YouTube?"
        elif "youtube" in instruction and "open" in instruction:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube."

        # ---------- WIKIPEDIA ----------
        if "wikipedia" in instruction or "wiki" in instruction:
            query = self._extract_query(instruction, ["wikipedia", "wiki"])
            if query:
                try:
                    summary = wikipedia.summary(query, sentences=2)
                    return f"Wikipedia says: {summary}"
                except:
                    return f"Sorry, I couldn't find information on {query}."
            else:
                return "What would you like to search on Wikipedia?"

        # ---------- WEATHER ----------
        if "weather" in instruction or "temperature" in instruction:
            city = "London"
            try:
                url = f"https://wttr.in/{city}?format=%C+%t"
                response = requests.get(url)
                weather_text = response.text.strip()
                return f"The weather in {city}: {weather_text}"
            except:
                return "I couldn't fetch the weather right now."

        # ---------- TIME ----------
        if "time" in instruction:
            now = datetime.datetime.now().strftime("%I:%M %p")
            return f"The current time is {now}"

        # ---------- DATE ----------
        if "date" in instruction:
            today = datetime.datetime.now().strftime("%B %d, %Y")
            return f"Today is {today}"

        # ---------- CALCULATOR ----------
        if "calculate" in instruction or "calculator" in instruction or "what is" in instruction:
            expr = self._extract_query(instruction, ["calculate", "calculator", "what is"])
            expr = expr.replace("plus", "+").replace("minus", "-")
            expr = expr.replace("times", "*").replace("multiplied by", "*")
            expr = expr.replace("divided by", "/").replace("divided", "/")
            try:
                result = eval(expr)
                return f"The result is {result}"
            except:
                return "I couldn't compute that."

        # ---------- SPOTIFY ----------
        if "spotify" in instruction:
            if "play" in instruction:
                query = self._extract_query(instruction, ["play", "spotify", "open", "and", "song", "music"])
                if query:
                    try:
                        os.startfile(f"spotify:search:{query}")
                        return f"Searching for '{query}' on Spotify app."
                    except:
                        webbrowser.open(f"https://open.spotify.com/search/{query}")
                        return f"Searching for '{query}' on Spotify web."
                else:
                    try:
                        subprocess.Popen("spotify")
                        return "Opening Spotify app."
                    except:
                        webbrowser.open("https://open.spotify.com")
                        return "Opening Spotify web."
            else:
                try:
                    subprocess.Popen("spotify")
                    return "Opening Spotify app."
                except:
                    webbrowser.open("https://open.spotify.com")
                    return "Opening Spotify web."

        # ---------- NEXT / PREVIOUS ----------
        if "next" in instruction and ("song" in instruction or "track" in instruction):
            if PY_AUTOGUI_AVAILABLE:
                pyautogui.press("nexttrack")
                return "Skipped to next track."
            else:
                return "pyautogui not installed."
        if "previous" in instruction and ("song" in instruction or "track" in instruction):
            if PY_AUTOGUI_AVAILABLE:
                pyautogui.press("prevtrack")
                return "Previous track."
            else:
                return "pyautogui not installed."

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
                        return f"Okay, I remembered that {key} is {value}."
                    else:
                        self.memory.remember(fact, "yes")
                        return f"Okay, I remembered: {fact}"
                else:
                    return "What would you like me to remember?"
            else:
                return "What would you like me to remember?"

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
                        return f"You told me that {k} is {v}."
                    else:
                        lines = ["Here's what I remember:"]
                        for k, v in matches.items():
                            lines.append(f"- {k}: {v}")
                        return "\n".join(lines)
                else:
                    val = self.memory.recall(key)
                    if val:
                        return f"You told me: {key} is {val}."
                    else:
                        return "I don't remember anything about that."
            else:
                return "What would you like me to recall?"

        # ---------- WHO ARE YOU / HELP ----------
        if "who are you" in instruction or "what is your name" in instruction:
            return f"I am {self.gui.config.get('assistant_name', 'Assistant')}, your voice assistant."

        if "help" in instruction or "what can you do" in instruction:
            return ("I can search the web, control your PC, remember facts, tell time, calculate, "
                    "control Spotify, close apps, collapse windows, switch windows, and more.\n"
                    "Try: 'remember that my name is Alex', 'what is my name',\n"
                    "'set volume to 30', 'increase volume by 20',\n"
                    "'pause', 'switch to YouTube', 'close spotify', 'collapse'.\n"
                    "Wake words: pixel or alexa. Say 'sleep' to idle, 'stop' to pause if media is playing, else exit.")

        # ---------- FALLBACK ----------
        if instruction in self.memory.data:
            val = self.memory.recall(instruction)
            return f"You told me: {instruction} is {val}."

        return "I'm not sure how to handle that. Try saying 'help' for ideas."

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

        # ---- START LISTENING AUTOMATICALLY after a short delay ----
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
            while self.listening:
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    text = self.recognizer.recognize_google(audio)
                    text = text.lower().strip()
                    if text:
                        self.command_var.set(text)
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