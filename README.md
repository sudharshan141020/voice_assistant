# 🎤 Voice Assistant with Memory

A feature‑rich, offline‑first voice assistant built in Python with **local JSON memory**, **wake words**, **system commands**, and a **Tkinter GUI**.
It listens for wake words (`pixel` or `alexa`), remembers facts, controls your PC, plays media, searches the web, and more – all without requiring an internet connection (except for speech recognition and web searches).

![GitHub repo size](https://img.shields.io/github/repo-size/sudharshan141020/voice-assistant)
![Python version](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

- **Voice Wake Words** – say `"pixel"` or `"alexa"` to activate (customisable).
- **Local Memory** – remembers facts, names, preferences in a `memory.json` file.
- **Optimised for Low‑Frequency Voices** – enhanced recognition for deeper tones (adjustable sensitivity).
- **System Control**
- Open/close apps (`"open chrome"`, `"close spotify"`)
- Adjust volume (`"set volume to 50%"`, `"increase volume by 10%"`)
- Take screenshots
- Lock PC, shutdown, restart
- Collapse all windows (`"collapse"`)
- Switch to any window (`"switch to YouTube"`)
- **Media Control**
- Play/pause (`"pause"`, `"resume"`, `"play"`)
- Next/previous track (`"next song"`, `"previous track"`)
- Spotify search (`"play [song] on spotify"`)
- **Web & Information**
- Google/YouTube/Wikipedia search
- Weather, time, date
- Calculator
- **Productivity**
- To‑do list, notes, reminders, shopping list (stored in SQLite)
- **Modern Tkinter GUI** with conversation history, status indicator, and settings.

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/sudharshan141020/voice-assistant.git
cd voice-assistant# 🎤 Voice Assistant with Memory

A feature‑rich, offline‑first voice assistant built in Python with **local JSON memory**, **wake words**, **system commands**, and a **Tkinter GUI**.
It listens for wake words (`pixel` or `alexa`), remembers facts, controls your PC, plays media, searches the web, and more – all without requiring an internet connection (except for speech recognition and web searches).

![GitHub repo size](https://img.shields.io/github/repo-size/sudharshan141020/voice-assistant)
![Python version](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

- **Voice Wake Words** – say `"pixel"` or `"alexa"` to activate (customisable).
- **Local Memory** – remembers facts, names, preferences in a `memory.json` file.
- **Optimised for Low‑Frequency Voices** – enhanced recognition for deeper tones (adjustable sensitivity).
- **System Control**
- Open/close apps (`"open chrome"`, `"close spotify"`)
- Adjust volume (`"set volume to 50%"`, `"increase volume by 10%"`)
- Take screenshots
- Lock PC, shutdown, restart
- Collapse all windows (`"collapse"`)
- Switch to any window (`"switch to YouTube"`)
- **Media Control**
- Play/pause (`"pause"`, `"resume"`, `"play"`)
- Next/previous track (`"next song"`, `"previous track"`)
- Spotify search (`"play [song] on spotify"`)
- **Web & Information**
- Google/YouTube/Wikipedia search
- Weather, time, date
- Calculator
- **Productivity**
- To‑do list, notes, reminders, shopping list (stored in SQLite)
- **Modern Tkinter GUI** with conversation history, status indicator, and settings.

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/sudharshan141020/voice-assistant.git
cd voice-assistant

### 2. Create a virtual environment (recommended)
bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

### 3. Install dependencies
bash
pip install -r requirements.txt

### 4.(Optional) Install extra features
If you want window switching and reliable screenshots, install:
bash
pip install pygetwindow

### 5.Run the assistant
bash
python assistant.py
The assistant starts listening automatically – no need to click START.
Say a wake word (pixel or alexa) to activate it.

Option B: Download ZIP from GitHub
Go to the repository: https://github.com/sudharshan141020/voice-assistant
Click the green Code button.
Select Download ZIP.
Extract the downloaded ZIP file to a folder on your computer.
Open a terminal in the extracted project folder.

2. Set up a virtual environment (recommended)
A virtual environment keeps the project dependencies isolated from other Python projects.

Windows:

bash
python -m venv venv
venv\Scripts\activate
After activation, your terminal prompt should show (venv).

macOS / Linux:

bash
python3 -m venv venv
source venv/bin/activate
3. Install dependencies
Make sure the virtual environment is activated, then run:

bash
pip install -r requirements.txt
This installs the core packages required by the assistant, including speech recognition, text‑to‑speech, and system automation.

4. (Optional) Enable window switching
The assistant supports a "switch to [window]" command.

To enable this feature, install pygetwindow:

bash
pip install pygetwindow
Without this package, the assistant will still run, but the window‑switching command will not work.

5. Run the assistant
bash
python assistant.py
The GUI will open and listening will start automatically – you do not need to press the START button.

Usage & Commands
Wake Words
"pixel" – primary wake word (configurable in Settings)

"alexa" – always available as a secondary wake word

Example Commands
Action	Say
Open app	"open notepad"
Close app	"close spotify"
Set volume	"set volume to 30%"
Increase volume	"increase volume by 20%"
Pause/Resume	"pause", "resume", "play"
Screenshot	"take a screenshot"
Collapse windows	"collapse" or "show desktop"
Switch window	"switch to YouTube"
Google search	"search Google for Python"
Wikipedia	"Wikipedia artificial intelligence"
Weather	"weather"
Time/Date	"what's the time", "date"
Remember	"remember that my name is Alex"
Recall	"what is my name"
Sleep	"sleep" (goes idle)
Exit	"goodbye" or "stop" (if no media playing)
Context‑aware "stop"
If a media window (YouTube, Spotify, etc.) is open, "stop" toggles pause.
Otherwise, "stop" exits the assistant.

🎤 Optimised for Low‑Frequency Voices
The assistant uses a lower energy threshold and dynamic adaptation to recognise deeper voices more reliably.
If you still have issues, you can fine‑tune these values inside the listen_loop method in assistant.py:
python
self.recognizer.energy_threshold = 200      # lower = more sensitive
self.recognizer.dynamic_energy_threshold = True
self.recognizer.pause_threshold = 0.8       # increase for slower speech
audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)   # longer commands

⚙️ Configuration
Settings are stored in assistant_config.json after first run.
You can change:
Assistant name
Primary wake word (pixel by default)
Voice (TTS voice index)
Speech rate and volume
Click the ⚙ SETTINGS button in the GUI to modify them.

Acknowledgements
SpeechRecognition – for voice input
pyttsx3 – text‑to‑speech
pyautogui – media keys & screenshots
pywhatkit – YouTube search
wikipedia – Wikipedia summaries
requests – weather API

 Files generated after first run
assistant_config.json – user settings

memory.json – remembered facts (e.g., "my name is Alex")

assistant_data.db – SQLite database for todos, notes, reminders, shopping list

These are automatically created – no need to edit them manually.