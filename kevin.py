import speech_recognition as sr
import pyautogui
import threading
import tempfile
import os
import time

from gtts import gTTS
from playsound import playsound
from rich.console import Console
from rich.panel import Panel

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Initialize rich console
console = Console()

# Setup audio interface (for volume control)
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# Function to speak text
def speak(text):
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        tts.save(temp_path)
        playsound(temp_path)
        os.remove(temp_path)
    except Exception as e:
        console.print(f"[red]Speech error:[/red] {e}")

# Show AI Panel UI
def show_ui():
    panel = Panel.fit(
        "[bold cyan]KEVIN AI SYSTEM[/bold cyan]\n[green]Listening...[/green]\n[italic]Voice Activated Assistant[/italic]",
        title="🤖 [bold red]KEVIN ONLINE[/bold red]",
    )
    console.print(panel)
    speak("Artificial Intelligence activated. I'm listening boss.")

# Handle keywords in command
def handle_command(command):
    command = command.lower()

    if "pause" in command:
        pyautogui.press("space")
        speak("Paused.")
    elif "play" in command:
        pyautogui.press("space")
        speak("Playing.")
    elif "move forward" in command or "forward" in command or "next" in command:
        pyautogui.press("right")
        speak("Moved forward.")
    elif "move back" in command or "back" in command or "previous" in command:
        pyautogui.press("left")
        speak("Moved back.")
    elif "scroll up" in command or "go up" in command:
        pyautogui.scroll(300)
        speak("Scrolling up.")
    elif "scroll down" in command or "go down" in command:
        pyautogui.scroll(-300)
        speak("Scrolling down.")
    elif "volume up" in command or "increase volume" in command:
        current = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(min(current + 0.1, 1.0), None)
        speak("Volume increased.")
    elif "volume down" in command or "decrease volume" in command:
        current = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(max(current - 0.1, 0.0), None)
        speak("Volume decreased.")
    elif "mute" in command:
        volume.SetMute(1, None)
        speak("Volume muted.")
    elif "unmute" in command:
        volume.SetMute(0, None)
        speak("Volume unmuted.")
    elif "good job" in command or "well done" in command or "nice work" in command:
        speak("Thank you, boss. I'm here to help.")
    elif "thank you" in command or "thanks" in command:
        speak("You're welcome. Always at your service.")

# Start listening in a background thread
def listen_forever():
    recognizer = sr.Recognizer()

    def loop():
        while True:
            with sr.Microphone() as source:
                try:
                    audio = recognizer.listen(source, phrase_time_limit=4)
                    query = recognizer.recognize_google(audio).lower()
                    console.print(f"[blue]🗣️ You said:[/blue] {query}")
                    handle_command(query)
                except sr.UnknownValueError:
                    pass  # silent on unknown input
                except Exception as e:
                    console.print(f"[red]Error listening:[/red] {e}")

    threading.Thread(target=loop, daemon=True).start()

# Entry point
if __name__ == "__main__":
    show_ui()
    listen_forever()

    while True:
        time.sleep(1)
