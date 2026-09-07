import speech_recognition as sr
import pyttsx3
import requests
import re
import os
import subprocess
import webbrowser
import urllib.parse
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile
import time
import threading
import tkinter as tk
from tkinter import scrolledtext
import pyautogui
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = "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"

API_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://your-site-or-project.com",
    "X-Title": "Pluck Assistant"
}


# ============================================================
# MICROPHONE SETTINGS
# ============================================================

recognizer = sr.Recognizer()

SAMPLE_RATE = 16000
CHANNELS = 1

# Voice-activity settings for continuous listening
SILENCE_DURATION = 0.9
MAX_UTTERANCE_SECONDS = 15
MIN_SPEECH_SECONDS = 0.25
PRE_ROLL_SECONDS = 0.25


# ============================================================
# GLOBAL VARIABLES
# ============================================================

running = True
listening = False
speaking = False


# ============================================================
# TEXT TO SPEECH
# ============================================================

def speak(text):

    global speaking

    if not text:
        return

    text = re.sub(
        r'[*_#>`{}\[\]|]',
        '',
        text
    )

    text = re.sub(
        r'\s+',
        ' ',
        text
    ).strip()

    print("\n🔊 Pluck:", text)

    try:

        speaking = True

        engine = pyttsx3.init()

        engine.setProperty(
            "rate",
            180
        )

        engine.setProperty(
            "volume",
            1.0
        )

        engine.say(text)

        engine.runAndWait()

        engine.stop()

    except Exception as e:

        print("❌ TTS Error:", e)

    finally:

        speaking = False


# ============================================================
# DISPLAY PLUCK MESSAGE
# ============================================================

def display_pluck(text):

    chat_box.config(
        state=tk.NORMAL
    )

    chat_box.insert(
        tk.END,
        "\nPluck: ",
        "pluck_name"
    )

    chat_box.insert(
        tk.END,
        text + "\n",
        "pluck_text"
    )

    chat_box.config(
        state=tk.DISABLED
    )

    chat_box.see(
        tk.END
    )


# ============================================================
# DISPLAY USER MESSAGE
# ============================================================

def display_user(text):

    chat_box.config(
        state=tk.NORMAL
    )

    chat_box.insert(
        tk.END,
        "\nYou: ",
        "user_name"
    )

    chat_box.insert(
        tk.END,
        text + "\n",
        "user_text"
    )

    chat_box.config(
        state=tk.DISABLED
    )

    chat_box.see(
        tk.END
    )


# ============================================================
# CONTINUOUS SOUNDDEVICE MICROPHONE
# ============================================================

def listen():

    global listening

    listening = True

    try:

        print("\n🎤 Pluck is listening...")

        # Open the microphone directly with SoundDevice.
        # This does NOT require PyAudio.
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=320
        ) as stream:

            # ------------------------------------------------
            # Calibrate the background noise briefly
            # ------------------------------------------------
            print("🎚️ Calibrating microphone...")

            calibration_frames = max(1, int(SAMPLE_RATE * 0.7 / 320))
            noise_levels = []

            for _ in range(calibration_frames):

                if not continuous_listening or not running:
                    return None

                data, _ = stream.read(320)
                samples = data[:, 0].astype("float32")
                noise_levels.append(float((samples * samples).mean() ** 0.5))

            noise_level = sum(noise_levels) / max(1, len(noise_levels))

            # Dynamic threshold: enough above room/mic noise
            threshold = max(350.0, noise_level * 2.8)

            print(
                f"🟢 Ready. Noise level: {noise_level:.0f}, "
                f"voice threshold: {threshold:.0f}"
            )

            # ------------------------------------------------
            # Wait for speech, then record until silence
            # ------------------------------------------------
            pre_roll = []
            audio_chunks = []
            speech_started = False
            silence_time = 0.0
            speech_time = 0.0
            utterance_time = 0.0

            chunk_seconds = 320 / SAMPLE_RATE

            while continuous_listening and running:

                data, _ = stream.read(320)

                chunk = data.copy()
                samples = chunk[:, 0].astype("float32")
                level = float((samples * samples).mean() ** 0.5)
                is_speech = level > threshold

                # Keep a small amount of audio before speech starts
                pre_roll.append(chunk)
                max_pre_roll_chunks = max(1, int(PRE_ROLL_SECONDS / chunk_seconds))

                if len(pre_roll) > max_pre_roll_chunks:
                    pre_roll.pop(0)

                if is_speech:

                    if not speech_started:

                        speech_started = True
                        audio_chunks.extend(pre_roll)
                        print("🗣️ Speech detected...")

                    audio_chunks.append(chunk)
                    speech_time += chunk_seconds
                    utterance_time += chunk_seconds
                    silence_time = 0.0

                elif speech_started:

                    audio_chunks.append(chunk)
                    silence_time += chunk_seconds
                    utterance_time += chunk_seconds

                    # Stop after natural silence
                    if (
                        silence_time >= SILENCE_DURATION
                        and speech_time >= MIN_SPEECH_SECONDS
                    ):
                        break

                # Safety limit for one sentence
                if utterance_time >= MAX_UTTERANCE_SECONDS:
                    break

            if not audio_chunks:
                return None

            # ------------------------------------------------
            # Save captured speech as WAV
            # ------------------------------------------------
            audio_data = np.concatenate(
                audio_chunks,
                axis=0
            )

            temp = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            )

            filename = temp.name
            temp.close()

            write(
                filename,
                SAMPLE_RATE,
                audio_data
            )

            print("🔍 Recognizing...")

            try:

                with sr.AudioFile(filename) as source:
                    audio = recognizer.record(source)

                text = recognizer.recognize_google(audio)

                print(
                    "👤 You:",
                    text
                )

                return text

            except sr.UnknownValueError:

                return None

            except sr.RequestError as e:

                print(
                    "❌ Speech recognition error:",
                    e
                )

                return None

            finally:

                try:
                    os.remove(filename)
                except:
                    pass

    except Exception as e:

        print(
            "❌ Microphone error:",
            e
        )

        return None

    finally:

        listening = False


# ============================================================
# AI REQUEST
# ============================================================

def ask_ai(question):

    try:

        data = {

            "model": "openrouter/free",

            "messages": [

                {
                    "role": "system",

                    "content":
                    "You are Pluck, a personal AI assistant. "
                    "Your name is Pluck. "
                    "Answer naturally and clearly. "
                    "Keep answers reasonably concise. "
                    "Do not use markdown unless the user asks for it."
                },

                {
                    "role": "user",
                    "content": question
                }

            ],

            "max_tokens": 500
        }


        response = requests.post(

            API_URL,

            headers=HEADERS,

            json=data,

            timeout=60
        )


        if response.status_code != 200:

            print(
                "\n❌ AI Error:",
                response.status_code
            )

            print(
                response.text
            )

            return None


        result = response.json()

        answer = (
            result["choices"][0]
            ["message"]
            ["content"]
        )


        # Some routed models may append an internal safety classification.
        # Remove it so Pluck only displays the actual assistant response.
        answer = re.sub(
            r'(?i)\b(?:user\s+)?safety\s*:\s*(?:safe|unsafe|allowed|blocked)\b[.:,-]*',
            '',
            answer
        )

        # Remove a complete standalone safety-classifier line if present.
        answer = re.sub(
            r'(?im)^\s*(?:user\s+)?safety\s*(?:check|classification)?\s*[:=-].*$',
            '',
            answer
        )

        answer = re.sub(
            r'[*_#>`{}\[\]|]',
            '',
            answer
        )

        answer = re.sub(
            r'\s+',
            ' ',
            answer
        ).strip()


        return answer


    except Exception as e:

        print(
            "❌ AI connection error:",
            e
        )

        return None


# ============================================================
# OPEN CHROME
# ============================================================

def open_chrome():

    paths = [

        r"C:\Program Files\Google\Chrome\Application\chrome.exe",

        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",

        os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        )
    ]


    for path in paths:

        if os.path.exists(path):

            subprocess.Popen(
                [path]
            )

            return True


    return False


# ============================================================
# OPEN APPLICATION
# ============================================================

def open_application(app):

    app = app.lower().strip()


    if "chrome" in app:

        if open_chrome():

            speak(
                "Opening Chrome."
            )

        else:

            speak(
                "Chrome was not found."
            )

        return True


    if (
        "vs code" in app
        or "vscode" in app
        or "visual studio code" in app
    ):

        try:

            subprocess.Popen(
                ["code"]
            )

            speak(
                "Opening Visual Studio Code."
            )

        except:

            speak(
                "Visual Studio Code was not found."
            )

        return True


    if "notepad" in app:

        subprocess.Popen(
            ["notepad.exe"]
        )

        speak(
            "Opening Notepad."
        )

        return True


    if (
        "calculator" in app
        or "calc" in app
    ):

        subprocess.Popen(
            ["calc.exe"]
        )

        speak(
            "Opening Calculator."
        )

        return True


    if (
        "file explorer" in app
        or app == "explorer"
    ):

        subprocess.Popen(
            ["explorer.exe"]
        )

        speak(
            "Opening File Explorer."
        )

        return True


    if "whatsapp" in app:

        try:

            os.startfile(
                "whatsapp:"
            )

            speak(
                "Opening WhatsApp."
            )

        except:

            speak(
                "I couldn't open WhatsApp."
            )

        return True


    return False


# ============================================================
# OPEN WEBSITE
# ============================================================

def open_website(url):

    if not url.startswith(
        "http"
    ):

        url = "https://" + url

    webbrowser.open(
        url
    )

    speak(
        "Opening the website."
    )


# ============================================================
# GOOGLE SEARCH
# ============================================================

def google_search(query):

    encoded = urllib.parse.quote_plus(
        query
    )

    url = (
        "https://www.google.com/search?q="
        + encoded
    )

    webbrowser.open(
        url
    )

    speak(
        f"Searching Google for {query}."
    )


# ============================================================
# OPEN FOLDER
# ============================================================

def open_folder(name):

    home = os.path.expanduser(
        "~"
    )

    folders = {

        "desktop":
        os.path.join(
            home,
            "Desktop"
        ),

        "downloads":
        os.path.join(
            home,
            "Downloads"
        ),

        "documents":
        os.path.join(
            home,
            "Documents"
        ),

        "pictures":
        os.path.join(
            home,
            "Pictures"
        ),

        "music":
        os.path.join(
            home,
            "Music"
        ),

        "videos":
        os.path.join(
            home,
            "Videos"
        )
    }


    name = name.lower().strip()


    if name in folders:

        path = folders[name]

        if os.path.exists(path):

            os.startfile(path)

            speak(
                f"Opening {name}."
            )

            return True


    speak(
        "I couldn't find that folder."
    )

    return True


# ============================================================
# CREATE FOLDER
# ============================================================

def create_folder(name):

    desktop = os.path.join(
        os.path.expanduser("~"),
        "Desktop"
    )

    path = os.path.join(
        desktop,
        name
    )


    try:

        os.makedirs(
            path,
            exist_ok=True
        )

        speak(
            f"I created {name} on your Desktop."
        )

    except:

        speak(
            "I couldn't create that folder."
        )


# ============================================================
# SCREENSHOT
# ============================================================

def take_screenshot():

    try:

        desktop = os.path.join(
            os.path.expanduser("~"),
            "Desktop"
        )

        filename = (
            "Pluck_Screenshot_"
            + str(int(time.time()))
            + ".png"
        )

        path = os.path.join(
            desktop,
            filename
        )

        screenshot = pyautogui.screenshot()

        screenshot.save(
            path
        )

        speak(
            "Screenshot saved to your Desktop."
        )

    except:

        speak(
            "I couldn't take the screenshot."
        )


# ============================================================
# VOLUME
# ============================================================

def volume_up():

    pyautogui.press(
        "volumeup",
        presses=3
    )

    speak(
        "Volume increased."
    )


def volume_down():

    pyautogui.press(
        "volumedown",
        presses=3
    )

    speak(
        "Volume decreased."
    )


def mute():

    pyautogui.press(
        "volumemute"
    )

    speak(
        "Volume muted."
    )


# ============================================================
# LOCK
# ============================================================

def lock_pc():

    speak(
        "Locking the computer."
    )

    time.sleep(1)

    os.system(
        "rundll32.exe user32.dll,LockWorkStation"
    )


# ============================================================
# SHUTDOWN
# ============================================================

def shutdown():

    speak(
        "Shutting down the computer."
    )

    time.sleep(1)

    os.system(
        "shutdown /s /t 1"
    )


# ============================================================
# RESTART
# ============================================================

def restart():

    speak(
        "Restarting the computer."
    )

    time.sleep(1)

    os.system(
        "shutdown /r /t 1"
    )


# ============================================================
# PROCESS COMMAND
# ============================================================

def process_command(command):

    text = command.lower().strip()

    print(
        "\n⚙️ Processing:",
        command
    )


    # ========================================================
    # EXIT
    # ========================================================

    if any(
        word in text
        for word in [
            "exit",
            "quit",
            "bye",
            "close pluck"
        ]
    ):

        speak(
            "Goodbye."
        )

        return False


    # ========================================================
    # CHROME
    # ========================================================

    if (
        "open chrome" in text
        or
        "launch chrome" in text
        or
        "start chrome" in text
    ):

        open_application(
            "chrome"
        )

        return True


    # ========================================================
    # VS CODE
    # ========================================================

    if (
        "open vs code" in text
        or
        "open vscode" in text
        or
        "launch vs code" in text
        or
        "open visual studio code" in text
    ):

        open_application(
            "vscode"
        )

        return True


    # ========================================================
    # NOTEPAD
    # ========================================================

    if "open notepad" in text:

        open_application(
            "notepad"
        )

        return True


    # ========================================================
    # CALCULATOR
    # ========================================================

    if (
        "open calculator" in text
        or
        "open calc" in text
    ):

        open_application(
            "calculator"
        )

        return True


    # ========================================================
    # FILE EXPLORER
    # ========================================================

    if (
        "open file explorer" in text
        or
        "open explorer" in text
    ):

        open_application(
            "explorer"
        )

        return True


    # ========================================================
    # WHATSAPP
    # ========================================================

    if "open whatsapp" in text:

        open_application(
            "whatsapp"
        )

        return True


    # ========================================================
    # WEBSITE
    # ========================================================

    websites = {

        "youtube":
        "https://www.youtube.com",

        "google":
        "https://www.google.com",

        "instagram":
        "https://www.instagram.com",

        "facebook":
        "https://www.facebook.com",

        "github":
        "https://github.com"
    }


    for name, url in websites.items():

        if (
            f"open {name}" in text
            or
            f"launch {name}" in text
        ):

            open_website(
                url
            )

            return True


    # ========================================================
    # GOOGLE SEARCH
    # ========================================================

    if "search for" in text:

        query = text.split(
            "search for",
            1
        )[1].strip()

        if query:

            google_search(
                query
            )

        return True


    if text.startswith(
        "google "
    ):

        query = text.replace(
            "google ",
            "",
            1
        ).strip()

        if query:

            google_search(
                query
            )

        return True


    # ========================================================
    # FOLDERS
    # ========================================================

    folders = [
        "downloads",
        "desktop",
        "documents",
        "pictures",
        "music",
        "videos"
    ]


    for folder in folders:

        if (
            f"open {folder}" in text
            or
            f"open my {folder}" in text
        ):

            open_folder(
                folder
            )

            return True


    # ========================================================
    # CREATE FOLDER
    # ========================================================

    if "create folder" in text:

        name = text.split(
            "create folder",
            1
        )[1].strip()

        if name:

            create_folder(
                name
            )

        return True


    if "make folder" in text:

        name = text.split(
            "make folder",
            1
        )[1].strip()

        if name:

            create_folder(
                name
            )

        return True


    # ========================================================
    # SCREENSHOT
    # ========================================================

    if (
        "take screenshot" in text
        or
        "take a screenshot" in text
        or
        "capture screen" in text
    ):

        take_screenshot()

        return True


    # ========================================================
    # VOLUME
    # ========================================================

    if (
        "increase volume" in text
        or
        "turn up volume" in text
        or
        "volume up" in text
    ):

        volume_up()

        return True


    if (
        "decrease volume" in text
        or
        "turn down volume" in text
        or
        "volume down" in text
    ):

        volume_down()

        return True


    if "mute" in text:

        mute()

        return True


    # ========================================================
    # LOCK
    # ========================================================

    if (
        "lock computer" in text
        or
        "lock my computer" in text
        or
        "lock pc" in text
    ):

        lock_pc()

        return True


    # ========================================================
    # SHUTDOWN
    # ========================================================

    if (
        "shutdown" in text
        or
        "shut down" in text
    ):

        shutdown()

        return False


    # ========================================================
    # RESTART
    # ========================================================

    if (
        "restart computer" in text
        or
        "restart pc" in text
        or
        text == "restart"
    ):

        restart()

        return False


    # ========================================================
    # NORMAL AI QUESTION
    # ========================================================

    answer = ask_ai(
        command
    )


    if answer:

        display_pluck(
            answer
        )

        # Speak AI answer
        threading.Thread(
            target=speak,
            args=(answer,),
            daemon=True
        ).start()

    else:

        display_pluck(
            "Sorry, I couldn't get a response from the AI."
        )

        threading.Thread(
            target=speak,
            args=(
                "Sorry, I couldn't get a response from the AI.",
            ),
            daemon=True
        ).start()


    return True


# ============================================================
# TEXT SEND BUTTON
# ============================================================

def send_message():

    message = entry.get().strip()

    if not message:

        return

    entry.delete(
        0,
        tk.END
    )

    display_user(
        message
    )

    # Run command in background
    threading.Thread(
        target=process_command,
        args=(message,),
        daemon=True
    ).start()


# ============================================================
# ENTER KEY
# ============================================================

def enter_pressed(event):

    send_message()


# ============================================================
# VOICE BUTTON
# ============================================================

def voice_button():

    def voice_thread():

        display_pluck(
            "Listening..."
        )

        text = listen()

        if not text:

            display_pluck(
                "I couldn't understand you."
            )

            speak(
                "I couldn't understand you."
            )

            return


        display_user(
            text
        )


        # Process voice command
        process_command(
            text
        )


    threading.Thread(
        target=voice_thread,
        daemon=True
    ).start()


# ============================================================
# CLEAR CHAT
# ============================================================

def clear_chat():

    chat_box.config(
        state=tk.NORMAL
    )

    chat_box.delete(
        "1.0",
        tk.END
    )

    chat_box.config(
        state=tk.DISABLED
    )


# ============================================================
# CLOSE PROGRAM
# ============================================================

def close_program():

    global running

    running = False

    root.destroy()


# ============================================================
# ============================================================
# BEAUTIFUL PLUCK GUI
# ============================================================

# GUI-only variables
root = None
chat_box = None
entry = None
voice = None
orb_canvas = None
status_label = None
pulse_phase = 0
continuous_listening = False
voice_thread_running = False


# ============================================================
# CHAT DISPLAY
# ============================================================

def _append_chat(sender, text, name_tag, text_tag):
    chat_box.config(state=tk.NORMAL)

    chat_box.insert(
        tk.END,
        f"{sender}: ",
        name_tag
    )

    chat_box.insert(
        tk.END,
        f"{text}\n\n",
        text_tag
    )

    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)


def display_pluck(text):
    if root is None:
        return

    root.after(
        0,
        lambda: _append_chat(
            "Pluck",
            text,
            "pluck_name",
            "pluck_text"
        )
    )


def display_user(text):
    if root is None:
        return

    root.after(
        0,
        lambda: _append_chat(
            "You",
            text,
            "user_name",
            "user_text"
        )
    )


# ============================================================
# ANIMATED NEON ORB
# ============================================================

def animate_orb():
    global pulse_phase

    if orb_canvas is None:
        return

    pulse_phase += 0.12

    import math

    pulse = (math.sin(pulse_phase) + 1) / 2

    center_x = 100
    center_y = 100

    orb_canvas.delete("orb")

    # Outer rings
    for i in range(5):
        radius = 62 + i * 8 + int(pulse * 4)

        orb_canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            outline="#24113F",
            width=2,
            tags="orb"
        )

    # Neon rings
    radius1 = 48 + int(pulse * 5)
    radius2 = 37 + int(pulse * 4)

    orb_canvas.create_oval(
        center_x - radius1,
        center_y - radius1,
        center_x + radius1,
        center_y + radius1,
        outline="#5A189A",
        width=3,
        tags="orb"
    )

    orb_canvas.create_oval(
        center_x - radius2,
        center_y - radius2,
        center_x + radius2,
        center_y + radius2,
        outline="#8A2BE2",
        width=3,
        tags="orb"
    )

    # Core
    core_radius = 25 + int(pulse * 5)

    orb_canvas.create_oval(
        center_x - core_radius,
        center_y - core_radius,
        center_x + core_radius,
        center_y + core_radius,
        fill="#24103D",
        outline="#B388FF",
        width=3,
        tags="orb"
    )

    # Center
    orb_canvas.create_oval(
        center_x - 11,
        center_y - 11,
        center_x + 11,
        center_y + 11,
        fill="#8A2BE2",
        outline="#D8B4FE",
        width=2,
        tags="orb"
    )

    # Orbiting dots
    for i in range(8):
        angle = pulse_phase + i * (math.pi / 4)

        x = center_x + math.cos(angle) * 68
        y = center_y + math.sin(angle) * 68

        dot_size = 2 + int(
            (math.sin(pulse_phase * 2 + i) + 1) * 1.5
        )

        orb_canvas.create_oval(
            x - dot_size,
            y - dot_size,
            x + dot_size,
            y + dot_size,
            fill="#B388FF",
            outline="",
            tags="orb"
        )

    root.after(35, animate_orb)


# ============================================================
# STATUS
# ============================================================

def set_status(text):
    if root is None:
        return

    root.after(
        0,
        lambda: status_label.config(text=text)
    )


# ============================================================
# TEXT CHAT
# ============================================================

def send_message():
    message = entry.get().strip()

    if not message:
        return

    display_user(message)

    entry.delete(0, tk.END)

    set_status("● PROCESSING")

    threading.Thread(
        target=process_command,
        args=(message,),
        daemon=True
    ).start()


def enter_pressed(event):
    send_message()


def open_chat():
    """Focus the text chat box when CHAT is clicked."""
    entry.focus_set()
    set_status("● CHAT READY")


# ============================================================
# CONTINUOUS VOICE LISTENING
# ============================================================

def voice_button():
    global continuous_listening
    global voice_thread_running

    # If already listening, this click stops the loop.
    if continuous_listening:
        continuous_listening = False

        voice.config(
            text="🎙  START LISTENING",
            bg=PURPLE
        )

        set_status("● READY")

        display_pluck(
            "Voice listening stopped."
        )

        return

    # Start continuous listening.
    continuous_listening = True

    voice.config(
        text="■  STOP LISTENING",
        bg=PURPLE_DARK
    )

    set_status(
        "● LISTENING — CLICK STOP TO END"
    )

    display_pluck(
        "Continuous voice mode is on. I am listening."
    )

    if not voice_thread_running:
        voice_thread_running = True

        threading.Thread(
            target=continuous_voice_loop,
            daemon=True
        ).start()


def continuous_voice_loop():
    global continuous_listening
    global voice_thread_running

    try:

        while continuous_listening and running:

            # Never listen to Pluck while Pluck is speaking.
            while speaking and continuous_listening and running:
                time.sleep(0.1)

            if not continuous_listening or not running:
                break

            set_status(
                "● LISTENING — SPEAK NATURALLY"
            )

            text = listen()

            if not continuous_listening or not running:
                break

            if not text:
                continue

            display_user(text)

            set_status("● PROCESSING")

            # Execute the existing command/AI logic exactly as before.
            process_command(text)

            # Wait for any TTS started by process_command() to finish
            # before reopening the microphone.
            while speaking and continuous_listening and running:
                time.sleep(0.1)

            if continuous_listening and running:
                set_status(
                    "● LISTENING — SPEAK NATURALLY"
                )

    finally:

        continuous_listening = False
        voice_thread_running = False

        if root is not None:

            root.after(
                0,
                lambda: voice.config(
                    text="🎙  START LISTENING",
                    bg=PURPLE
                )
            )

            set_status("● READY")


# ============================================================
# CLEAR CHAT
# ============================================================

def clear_chat():
    chat_box.config(state=tk.NORMAL)
    chat_box.delete("1.0", tk.END)
    chat_box.config(state=tk.DISABLED)

    display_pluck(
        "Chat cleared. How can I assist you?"
    )


# ============================================================
# CLOSE PROGRAM
# ============================================================

def close_program():
    global running
    global continuous_listening

    running = False
    continuous_listening = False

    try:
        root.destroy()
    except:
        pass


# ============================================================
# MAIN GUI
# ============================================================

root = tk.Tk()

root.title(
    "PLUCK • AI COMPUTER ASSISTANT"
)

root.geometry(
    "720x850"
)

root.minsize(
    600,
    700
)

root.configure(
    bg="#08050D"
)


# ============================================================
# COLORS
# ============================================================

BG_MAIN = "#08050D"
BG_PANEL = "#120C1D"
BG_CHAT = "#0D0915"
PURPLE = "#8A2BE2"
PURPLE_DARK = "#5A189A"
PURPLE_SOFT = "#B388FF"
WHITE = "#FFFFFF"
GREY = "#776A8C"
CYAN = "#00F5D4"


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    root,
    bg=BG_MAIN
)

header.pack(
    fill=tk.X,
    pady=(18, 5)
)


title = tk.Label(
    header,
    text="P L U C K",
    font=("Segoe UI", 25, "bold"),
    fg=PURPLE_SOFT,
    bg=BG_MAIN
)

title.pack()


subtitle = tk.Label(
    header,
    text="N E U R A L   A I   A S S I S T A N T",
    font=("Consolas", 9),
    fg="#776A8C",
    bg=BG_MAIN
)

subtitle.pack(
    pady=(0, 6)
)


# ============================================================
# STATUS
# ============================================================

status_label = tk.Label(
    header,
    text="● READY",
    font=("Consolas", 9, "bold"),
    fg=CYAN,
    bg=BG_MAIN
)

status_label.pack(
    pady=(0, 8)
)


# ============================================================
# ORB
# ============================================================

orb_canvas = tk.Canvas(
    header,
    width=200,
    height=200,
    bg=BG_MAIN,
    highlightthickness=0
)

orb_canvas.pack(
    pady=(0, 8)
)

animate_orb()


# ============================================================
# VOICE BUTTON
# ============================================================

voice = tk.Button(
    header,
    text="🎙  START LISTENING",
    font=("Segoe UI", 10, "bold"),
    bg=PURPLE,
    fg=WHITE,
    activebackground=PURPLE_DARK,
    activeforeground=WHITE,
    bd=0,
    padx=25,
    pady=9,
    cursor="hand2",
    relief="flat",
    command=voice_button
)

voice.pack(
    pady=(0, 12)
)


# ============================================================
# CHAT DISPLAY
# ============================================================

chat_frame = tk.Frame(
    root,
    bg=BG_PANEL,
    bd=1,
    highlightthickness=1,
    highlightbackground="#3A2A5E"
)

# Keep a fixed amount of space for chat history so the
# input box and buttons below it are ALWAYS visible.
chat_frame.pack(
    padx=20,
    pady=8,
    fill=tk.X,
    expand=False
)

chat_frame.configure(
    height=230
)

# Prevent the ScrolledText from making chat_frame taller.
chat_frame.pack_propagate(False)


chat_box = scrolledtext.ScrolledText(
    chat_frame,
    wrap=tk.WORD,
    bg=BG_CHAT,
    fg=WHITE,
    font=("Segoe UI", 11),
    bd=0,
    insertbackground=WHITE,
    padx=15,
    pady=15
)

chat_box.pack(
    fill=tk.BOTH,
    expand=True
)

chat_box.config(
    state=tk.DISABLED
)


# Chat text styles
chat_box.tag_config(
    "pluck_name",
    foreground=PURPLE_SOFT,
    font=("Segoe UI", 11, "bold")
)

chat_box.tag_config(
    "pluck_text",
    foreground=WHITE,
    font=("Segoe UI", 11)
)

chat_box.tag_config(
    "user_name",
    foreground=CYAN,
    font=("Segoe UI", 11, "bold")
)

chat_box.tag_config(
    "user_text",
    foreground="#E8FFF9",
    font=("Segoe UI", 11)
)


# ============================================================
# CHAT INPUT AREA
# ============================================================

input_frame = tk.Frame(
    root,
    bg=BG_MAIN
)

input_frame.pack(
    fill=tk.X,
    padx=20,
    pady=(8, 6)
)


entry = tk.Entry(
    input_frame,
    bg=BG_PANEL,
    fg=WHITE,
    font=("Segoe UI", 11),
    insertbackground=PURPLE_SOFT,
    bd=0,
    highlightthickness=1,
    highlightbackground="#4D3678",
    highlightcolor=PURPLE,
    relief="flat"
)

entry.pack(
    side=tk.LEFT,
    fill=tk.X,
    expand=True,
    ipady=10,
    padx=(0, 10)
)

entry.bind(
    "<Return>",
    enter_pressed
)


# ============================================================
# SEND BUTTON
# ============================================================

send_btn = tk.Button(
    input_frame,
    text="➤  SEND",
    font=("Segoe UI", 9, "bold"),
    bg=PURPLE,
    fg=WHITE,
    activebackground=PURPLE_DARK,
    activeforeground=WHITE,
    bd=0,
    padx=18,
    pady=8,
    cursor="hand2",
    relief="flat",
    command=send_message
)

send_btn.pack(
    side=tk.RIGHT
)


# ============================================================
# BOTTOM BUTTONS
# ============================================================

button_frame = tk.Frame(
    root,
    bg=BG_MAIN
)

button_frame.pack(
    fill=tk.X,
    padx=20,
    pady=(3, 16)
)


# CHAT BUTTON
chat_btn = tk.Button(
    button_frame,
    text="💬  CHAT",
    font=("Segoe UI", 9, "bold"),
    bg=PURPLE_DARK,
    fg=WHITE,
    activebackground=PURPLE,
    activeforeground=WHITE,
    bd=0,
    padx=20,
    pady=8,
    cursor="hand2",
    relief="flat",
    command=open_chat
)

chat_btn.pack(
    side=tk.LEFT,
    padx=(0, 8)
)


# VOICE BUTTON
voice_bottom_btn = tk.Button(
    button_frame,
    text="🎙  VOICE",
    font=("Segoe UI", 9, "bold"),
    bg=BG_PANEL,
    fg=PURPLE_SOFT,
    activebackground=PURPLE_DARK,
    activeforeground=WHITE,
    bd=1,
    relief="solid",
    highlightthickness=0,
    padx=20,
    pady=7,
    cursor="hand2",
    command=voice_button
)

voice_bottom_btn.pack(
    side=tk.LEFT,
    padx=4
)


# CLEAR BUTTON
clear_btn = tk.Button(
    button_frame,
    text="🗑  CLEAR",
    font=("Segoe UI", 9),
    bg=BG_PANEL,
    fg="#9D8BB5",
    activebackground="#3F2B66",
    activeforeground=WHITE,
    bd=0,
    padx=15,
    pady=8,
    cursor="hand2",
    command=clear_chat
)

clear_btn.pack(
    side=tk.RIGHT
)


# ============================================================
# CLOSE EVENT
# ============================================================

root.protocol(
    "WM_DELETE_WINDOW",
    close_program
)


# ============================================================
# START GUI
# ============================================================

STARTUP_GREETING = "Hi Queen, I am Pluck, your assistant. How can I help you today?"

display_pluck(STARTUP_GREETING)

threading.Thread(
    target=speak,
    args=(STARTUP_GREETING,),
    daemon=True
).start()

root.mainloop()
