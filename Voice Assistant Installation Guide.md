# 📥 Download & Setup Guide
# Voice Assistant — Installation Guide

This guide explains how to download, set up, and run the Voice Assistant project on your computer.
Follow these steps to get the **Voice Assistant** running on your computer.

---

## 1. Download the code

### Option A: Clone with Git (recommended)

Open a terminal and run:

```bash
git clone https://github.com/sudharshan141020/voice-assistant.git
cd voice-assistant

## Option B: Download ZIP from GitHub

1. Go to the repository:

   https://github.com/sudharshan141020/voice-assistant

2. Click the green **Code** button.
3. Select **Download ZIP**.
4. Extract the downloaded ZIP file to a folder on your computer.
5. Open a terminal in the extracted project folder.

---

## 1. Set Up a Virtual Environment

A virtual environment keeps the project's dependencies isolated from other Python projects.

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

After activation, your terminal prompt should show:

```text
(venv)
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 2. Install Dependencies

Make sure the virtual environment is activated, then run:

```bash
pip install -r requirements.txt
```

This installs the core packages required by the assistant, including speech recognition, text-to-speech, and system automation dependencies.

---

## 3. Optional: Enable Window Switching

The assistant supports a **"switch to [window]"** command.

To enable this feature, install `pygetwindow`:

```bash
pip install pygetwindow
```

Without this package, the assistant will still run, but the window-switching command will not be available.

---

## 4. Run the Assistant

Start the assistant with:

```bash
python assistant.py
```

The GUI will open, and listening will start automatically. You do not need to press the **START** button.

---

## 5. Using the Assistant

### Wake Words

Say either:

```text
pixel
```

or

```text
alexa
```

to activate the assistant.

### Give Commands

Once the assistant is active, speak your command normally.

For the complete list of supported commands and features, see the project's main README.

### Put the Assistant to Sleep

Say:

```text
sleep
```

### Exit the Assistant

Say:

```text
goodbye
```

or:

```text
stop
```

> Note: `stop` may not exit immediately when media is currently playing.

---

## Troubleshooting

### Python is not recognized

Make sure Python is installed and added to your system PATH.

Check your Python installation with:

```bash
python --version
```

### `pip install -r requirements.txt` fails

Make sure you are inside the project folder and that your virtual environment is activated.

You can verify the current environment with:

```bash
where python
```

on Windows, or:

```bash
which python
```

on macOS/Linux.

### Window switching does not work

Install the optional dependency:

```bash
pip install pygetwindow
```

---

## Quick Start

For Windows users, the basic setup is:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pygetwindow
python assistant.py
```

The Voice Assistant should now launch and begin listening automatically.