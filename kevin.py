import speech_recognition as sr
import pyautogui
import threading
import tempfile
import os
import time
import uuid
import sys
from datetime import datetime

from gtts import gTTS
from playsound import playsound
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align
from rich.rule import Rule
from rich.prompt import Prompt, IntPrompt

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Add new imports for better device handling
import sounddevice as sd
import soundfile as sf
import pyaudio
import wave
import contextlib
from typing import Optional, Tuple, List
import json
import atexit

# Console UI with custom theme
console = Console()

# Volume control setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# Enhanced state management
class KevinState:
    def __init__(self):
        self.is_listening = False
        self.last_command = "None"
        self.commands_processed = 0
        self.start_time = datetime.now()
        self.current_volume = 0.0
        self.is_muted = False
        self.status = "Initializing..."
        self.mic_device = None
        self.speaker_device = None
        self.mic_name = "Default"
        self.speaker_name = "Default"
        self.config_file = "kevin_config.json"
        self.audio_stream = None
        self.pyaudio_instance = None
        
    def save_config(self):
        """Save current device configuration"""
        config = {
            "mic_device": self.mic_device,
            "speaker_device": self.speaker_device,
            "mic_name": self.mic_name,
            "speaker_name": self.speaker_name
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not save config: {e}[/yellow]")

    def load_config(self):
        """Load saved device configuration"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.mic_device = config.get('mic_device')
                self.speaker_device = config.get('speaker_device')
                self.mic_name = config.get('mic_name', "Default")
                self.speaker_name = config.get('speaker_name', "Default")
                return True
        except FileNotFoundError:
            return False
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not load config: {e}[/yellow]")
            return False

state = KevinState()

# Enhanced device management
class AudioDeviceManager:
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        
    def get_input_devices(self) -> List[Tuple[int, str]]:
        """Get all available input devices"""
        devices = []
        try:
            for i in range(self.pa.get_device_count()):
                device_info = self.pa.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append((i, device_info['name']))
        except Exception as e:
            console.print(f"[red]Error getting input devices: {e}[/red]")
        return devices

    def get_output_devices(self) -> List[Tuple[int, str]]:
        """Get all available output devices"""
        devices = []
        try:
            for i in range(self.pa.get_device_count()):
                device_info = self.pa.get_device_info_by_index(i)
                if device_info['maxOutputChannels'] > 0:
                    devices.append((i, device_info['name']))
        except Exception as e:
            console.print(f"[red]Error getting output devices: {e}[/red]")
        return devices

    def test_microphone(self, device_index: int) -> bool:
        """Test if microphone is working"""
        try:
            stream = self.pa.open(
                rate=44100,
                channels=1,
                format=pyaudio.paFloat32,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024,
                start=False
            )
            stream.start_stream()
            time.sleep(0.1)  # Short test
            stream.stop_stream()
            stream.close()
            return True
        except Exception as e:
            console.print(f"[red]Microphone test failed: {e}[/red]")
            return False

    def test_speaker(self, device_index: int) -> bool:
        """Test if speaker is working"""
        try:
            stream = self.pa.open(
                rate=44100,
                channels=2,
                format=pyaudio.paFloat32,
                output=True,
                output_device_index=device_index,
                frames_per_buffer=1024,
                start=False
            )
            stream.start_stream()
            time.sleep(0.1)  # Short test
            stream.stop_stream()
            stream.close()
            return True
        except Exception as e:
            console.print(f"[red]Speaker test failed: {e}[/red]")
            return False

    def cleanup(self):
        """Cleanup PyAudio resources"""
        if self.pa:
            self.pa.terminate()

# Initialize audio device manager
device_manager = AudioDeviceManager()
atexit.register(device_manager.cleanup)

# Device selection functions
def list_microphones():
    """List available microphone devices"""
    console.print("\n[cyan]🎤 Available Microphone Devices:[/cyan]")
    mic_list = sr.Microphone.list_microphone_names()
    
    devices_table = Table(show_header=True, box=None)
    devices_table.add_column("Index", style="yellow", width=8)
    devices_table.add_column("Device Name", style="white")
    
    for i, name in enumerate(mic_list):
        devices_table.add_row(str(i), name)
    
    console.print(devices_table)
    return mic_list

def list_speakers():
    """List available audio output devices"""
    console.print("\n[cyan]🔊 Available Audio Output Devices:[/cyan]")
    
    # Get all audio devices
    import sounddevice as sd
    devices = sd.query_devices()
    
    devices_table = Table(show_header=True, box=None)
    devices_table.add_column("Index", style="yellow", width=8)
    devices_table.add_column("Device Name", style="white")
    devices_table.add_column("Type", style="green", width=12)
    
    output_devices = []
    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:  # Only output devices
            devices_table.add_row(str(i), device['name'], "Output")
            output_devices.append((i, device['name']))
    
    console.print(devices_table)
    return output_devices

def setup_dual_headset():
    """Enhanced interactive setup for dual headset configuration"""
    console.print(Rule("[bold cyan]🎧 DUAL HEADSET SETUP 🎧[/bold cyan]"))
    
    # Try to load previous configuration
    if state.load_config():
        use_previous = Prompt.ask(
            "\n[cyan]Previous configuration found. Use it?[/cyan]",
            choices=["y", "n"],
            default="y"
        )
        if use_previous == "y":
            # Test previous devices
            if (state.mic_device is None or 
                state.speaker_device is None or 
                not device_manager.test_microphone(state.mic_device) or 
                not device_manager.test_speaker(state.speaker_device)):
                console.print("[yellow]⚠️  Previous configuration invalid, starting fresh setup[/yellow]")
            else:
                console.print("[green]✅ Previous configuration loaded successfully![/green]")
                return

    # Microphone setup
    console.print("\n[cyan]🎤 Available Microphone Devices:[/cyan]")
    input_devices = device_manager.get_input_devices()
    
    devices_table = Table(show_header=True, box=None)
    devices_table.add_column("Index", style="yellow", width=8)
    devices_table.add_column("Device Name", style="white")
    
    for idx, name in input_devices:
        devices_table.add_row(str(idx), name)
    
    console.print(devices_table)
    
    while True:
        try:
            mic_choice = IntPrompt.ask(
                "\n[cyan]Select microphone device index[/cyan]",
                default=0
            )
            if any(idx == mic_choice for idx, _ in input_devices):
                if device_manager.test_microphone(mic_choice):
                    state.mic_device = mic_choice
                    state.mic_name = next(name for idx, name in input_devices if idx == mic_choice)
                    console.print(f"[green]✅ Microphone set to: {state.mic_name}[/green]")
                    break
                else:
                    console.print("[red]❌ Microphone test failed, please try another device[/red]")
            else:
                console.print("[red]❌ Invalid selection[/red]")
        except ValueError:
            console.print("[red]❌ Please enter a valid number[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Setup cancelled, using default microphone[/yellow]")
            state.mic_device = None
            state.mic_name = "Default"
            break

    # Speaker setup
    console.print("\n[cyan]🔊 Available Audio Output Devices:[/cyan]")
    output_devices = device_manager.get_output_devices()
    
    devices_table = Table(show_header=True, box=None)
    devices_table.add_column("Index", style="yellow", width=8)
    devices_table.add_column("Device Name", style="white")
    
    for idx, name in output_devices:
        devices_table.add_row(str(idx), name)
    
    console.print(devices_table)
    
    while True:
        try:
            speaker_choice = IntPrompt.ask(
                "\n[cyan]Select audio output device index[/cyan]",
                default=0
            )
            if any(idx == speaker_choice for idx, _ in output_devices):
                if device_manager.test_speaker(speaker_choice):
                    state.speaker_device = speaker_choice
                    state.speaker_name = next(name for idx, name in output_devices if idx == speaker_choice)
                    console.print(f"[green]✅ Audio output set to: {state.speaker_name}[/green]")
                    break
                else:
                    console.print("[red]❌ Speaker test failed, please try another device[/red]")
            else:
                console.print("[red]❌ Invalid selection[/red]")
        except ValueError:
            console.print("[red]❌ Please enter a valid number[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Setup cancelled, using default speakers[/yellow]")
            state.speaker_device = None
            state.speaker_name = "Default"
            break

    # Save configuration
    state.save_config()
    
    # Configuration summary
    console.print("\n[bold green]🎧 DUAL HEADSET CONFIGURATION:[/bold green]")
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Setting", style="cyan", width=15)
    config_table.add_column("Device", style="white")
    
    config_table.add_row("🎤 Microphone:", state.mic_name)
    config_table.add_row("🔊 Audio Output:", state.speaker_name)
    
    console.print(config_table)
    console.print("\n[green]✅ Dual headset setup complete![/green]")

# Enhanced speak function with better device handling
def speak(text):
    try:
        # Generate speech file
        filename = os.path.join(tempfile.gettempdir(), f"kevin_speech_{uuid.uuid4().hex}.wav")
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filename)
        
        # Play audio with specific device
        if state.speaker_device is not None:
            try:
                data, sample_rate = sf.read(filename)
                sd.play(data, sample_rate, device=state.speaker_device)
                sd.wait()
            except Exception as e:
                console.print(f"[yellow]⚠️  Device-specific playback failed, using default: {e}[/yellow]")
                playsound(filename)
        else:
            playsound(filename)
        
        # Cleanup
        try:
            os.remove(filename)
        except:
            pass
            
    except Exception as e:
        console.print(f"[red]⚠️  Speech error: {e}[/red]")

# Create dynamic status display with device info
def create_status_display():
    # Update volume info
    try:
        state.current_volume = int(volume.GetMasterVolumeLevelScalar() * 100)
        state.is_muted = volume.GetMute()
    except:
        state.current_volume = 0
        state.is_muted = False
    
    # Create main layout
    layout = Layout()
    
    # Header with title
    header = Panel(
        Align.center(
            Text("🎧 KEVIN AI - DUAL HEADSET VOICE CONTROLLER 🎧", style="bold cyan")
        ),
        style="bold blue",
        border_style="bright_blue"
    )
    
    # Status info table
    status_table = Table(show_header=False, box=None, expand=True)
    status_table.add_column("", style="cyan", width=20)
    status_table.add_column("", style="white")
    
    # Calculate uptime
    uptime = datetime.now() - state.start_time
    uptime_str = str(uptime).split('.')[0]
    
    status_table.add_row("🟢 Status:", f"[green]{state.status}[/green]")
    status_table.add_row("🎤 Listening:", f"[{'green' if state.is_listening else 'red'}]{state.is_listening}[/]")
    status_table.add_row("📝 Last Command:", f"[yellow]{state.last_command}[/yellow]")
    status_table.add_row("📊 Commands Processed:", f"[magenta]{state.commands_processed}[/magenta]")
    status_table.add_row("⏱️  Uptime:", f"[blue]{uptime_str}[/blue]")
    status_table.add_row("🔊 Volume:", f"[{'red' if state.is_muted else 'green'}]{state.current_volume}%{' (MUTED)' if state.is_muted else ''}[/]")
    
    status_panel = Panel(
        status_table,
        title="📊 [bold green]SYSTEM STATUS[/bold green]",
        border_style="green"
    )
    
    # Device configuration table
    device_table = Table(show_header=False, box=None, expand=True)
    device_table.add_column("", style="cyan", width=20)
    device_table.add_column("", style="white")
    
    device_table.add_row("🎤 Microphone:", f"[green]{state.mic_name}[/green]")
    device_table.add_row("🔊 Audio Output:", f"[green]{state.speaker_name}[/green]")
    
    device_panel = Panel(
        device_table,
        title="🎧 [bold cyan]DEVICE CONFIGURATION[/bold cyan]",
        border_style="cyan"
    )
    
    # Commands help table
    commands_table = Table(show_header=True, box=None)
    commands_table.add_column("🎵 Media Controls", style="cyan", width=20)
    commands_table.add_column("🔊 Volume Controls", style="yellow", width=20)
    commands_table.add_column("🖱️  Navigation", style="magenta", width=20)
    
    commands_table.add_row("'play' / 'pause'", "'volume up/down'", "'scroll up/down'")
    commands_table.add_row("'forward' / 'next'", "'increase/decrease volume'", "")
    commands_table.add_row("'back' / 'previous'", "'mute' / 'unmute'", "")
    
    commands_panel = Panel(
        commands_table,
        title="🎮 [bold cyan]AVAILABLE COMMANDS[/bold cyan]",
        border_style="cyan"
    )
    
    # Listening indicator
    listening_text = Text()
    if state.is_listening:
        listening_text.append("🎤 ", style="green")
        listening_text.append("LISTENING FOR COMMANDS...", style="bold green blink")
    else:
        listening_text.append("🔇 ", style="red")
        listening_text.append("PROCESSING...", style="bold red")
    
    listening_panel = Panel(
        Align.center(listening_text),
        border_style="bright_green" if state.is_listening else "bright_red",
        height=3
    )
    
    # Layout composition
    layout.split_column(
        Layout(header, size=3),
        Layout().split_row(
            Layout(status_panel),
            Layout(device_panel)
        ),
        Layout(commands_panel, size=6),
        Layout(listening_panel, size=3)
    )
    
    return layout

# Enhanced UI with device setup
def show_enhanced_ui():
    # Clear screen
    console.clear()
    
    # Setup dual headset configuration
    setup_dual_headset()
    
    # Startup animation
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Initializing Kevin AI Dual Headset System..."),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Loading...", total=100)
        for i in range(100):
            progress.update(task, advance=1)
            time.sleep(0.02)
    
    # Welcome message
    console.print(Rule("[bold cyan]🎧 KEVIN AI DUAL HEADSET ACTIVATED 🎧[/bold cyan]"))
    
    # Initial status update
    state.status = "Online & Ready"
    speak("Kevin Artificial Intelligence dual headset system activated. All systems online Boss. Ready for voice commands.")

# Enhanced command handler
def handle_command(command):
    command = command.lower().strip()
    state.last_command = command
    state.commands_processed += 1
    
    # Command keywords mapping
    command_keywords = {
        'pause': {
            'keywords': ['pause', 'stop', 'halt', 'freeze'],
            'action': lambda cmd: (pyautogui.press("space"), "Media paused.", "Media Paused")
        },
        'play': {
            'keywords': ['play', 'start', 'resume', 'continue', 'unpause'],
            'action': lambda cmd: (pyautogui.press("space"), "Media playing.", "Media Playing")
        },
        'forward': {
            'keywords': ['forward', 'next', 'skip', 'ahead', 'advance'],
            'action': lambda cmd: (pyautogui.press("right"), "Moved forward.", "Seeking Forward")
        },
        'backward': {
            'keywords': ['back', 'previous', 'rewind', 'return', 'behind'],
            'action': lambda cmd: (pyautogui.press("left"), "Moved back.", "Seeking Backward")
        },
        'scroll_up': {
            'keywords': ['scroll up', 'move up', 'go up', 'upward', 'up'],
            'action': lambda cmd: (pyautogui.scroll(300), "Scrolling up.", "Scrolling Up")
        },
        'scroll_down': {
            'keywords': ['scroll down', 'move down', 'go down', 'downward', 'down'],
            'action': lambda cmd: (pyautogui.scroll(-300), "Scrolling down.", "Scrolling Down")
        },
        'volume_up': {
            'keywords': ['volume up', 'louder', 'increase volume', 'turn up', 'raise volume'],
            'action': lambda cmd: (
                volume.SetMasterVolumeLevelScalar(min(volume.GetMasterVolumeLevelScalar() + 0.1, 1.0), None),
                f"Volume increased to {int(volume.GetMasterVolumeLevelScalar() * 100)} percent.",
                "Volume Increased"
            )
        },
        'volume_down': {
            'keywords': ['volume down', 'quieter', 'decrease volume', 'turn down', 'lower volume'],
            'action': lambda cmd: (
                volume.SetMasterVolumeLevelScalar(max(volume.GetMasterVolumeLevelScalar() - 0.1, 0.0), None),
                f"Volume decreased to {int(volume.GetMasterVolumeLevelScalar() * 100)} percent.",
                "Volume Decreased"
            )
        },
        'mute': {
            'keywords': ['mute', 'silence', 'quiet', 'no sound', 'shut up'],
            'action': lambda cmd: (volume.SetMute(1, None), "Audio muted.", "Audio Muted")
        },
        'unmute': {
            'keywords': ['unmute', 'unsilence', 'sound on', 'restore sound'],
            'action': lambda cmd: (volume.SetMute(0, None), "Audio unmuted.", "Audio Unmuted")
        }
    }

    # Social interaction keywords
    social_keywords = {
        'praise': {
            'keywords': ['good job', 'nice work', 'well done', 'great job', 'excellent'],
            'response': lambda cmd: ("Thank you, boss. I'm here to help.", "Acknowledged Praise")
        },
        'thanks': {
            'keywords': ['thank you', 'thanks', 'appreciate', 'grateful'],
            'response': lambda cmd: ("You're welcome, boss.", "Acknowledged Thanks")
        },
        'status': {
            'keywords': ['how are you', "how're you", 'how you doing', 'status'],
            'response': lambda cmd: ("I'm functioning optimally and ready to serve, boss.", "Status Check")
        },
        'greeting': {
            'keywords': ['hello', 'hi', 'hey', 'greetings'],
            'response': lambda cmd: ("Hello boss! How can I assist?", "Greeting Acknowledged")
        },
        'device_info': {
            'keywords': ['check devices', 'device status', 'audio setup', 'sound setup'],
            'response': lambda cmd: (f"Using {state.mic_name} for mic and {state.speaker_name} for audio.", "Device Status Check")
        }
    }

    # Remove wake word if present
    if "kevin" in command:
        command = command.replace("kevin", "").strip()

    # Check for command keywords
    for cmd_type, cmd_info in command_keywords.items():
        if any(keyword in command for keyword in cmd_info['keywords']):
            action_result = cmd_info['action'](command)
            pyautogui_action, speak_msg, status_msg = action_result
            speak(speak_msg)
            state.status = status_msg
            return

    # Check for social keywords
    for social_type, social_info in social_keywords.items():
        if any(keyword in command for keyword in social_info['keywords']):
            speak_msg, status_msg = social_info['response'](command)
            speak(speak_msg)
            state.status = status_msg
            return

    # Silently ignore unrecognized commands
    state.status = "Ready..."

# Enhanced listening function with better error handling
def listen_forever():
    recognizer = sr.Recognizer()
    calibration_retries = 0
    max_calibration_retries = 3
    
    while True:
        try:
            # Setup microphone with specific device
            mic = sr.Microphone(device_index=state.mic_device) if state.mic_device is not None else sr.Microphone()
            
            # Calibration with timeout and retry logic
            with mic as source:
                try:
                    console.print("[yellow]🎤 Calibrating microphone...[/yellow]")
                    state.status = "Calibrating..."
                    
                    # Set a shorter calibration duration
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    console.print("[green]✅ Microphone calibrated![/green]")
                    state.status = "Calibration successful"
                    calibration_retries = 0  # Reset retries on successful calibration
                except Exception as e:
                    calibration_retries += 1
                    console.print(f"[red]⚠️  Calibration attempt {calibration_retries} failed: {e}[/red]")
                    
                    if calibration_retries >= max_calibration_retries:
                        console.print("[red]❌ Maximum calibration retries reached. Resetting audio devices...[/red]")
                        # Reset audio devices
                        state.mic_device = None
                        state.speaker_device = None
                        state.mic_name = "Default"
                        state.speaker_name = "Default"
                        state.save_config()
                        
                        # Prompt for device reselection
                        setup_dual_headset()
                        calibration_retries = 0
                        continue
                    
                    time.sleep(2)  # Wait before retrying
                    continue
            
            def recognition_loop():
                while True:
                    try:
                        state.is_listening = True
                        state.status = "Listening..."
                        
                        with mic as source:
                            try:
                                audio = recognizer.listen(source, phrase_time_limit=4, timeout=2)
                                state.is_listening = False
                                
                                query = recognizer.recognize_google(audio).lower()
                                if query:
                                    console.print(f"\n[blue]🗣️  Command received:[/blue] [bold white]{query}[/bold white]")
                                    handle_command(query)
                                    
                                    # Reset status after command
                                    time.sleep(1)
                                    state.status = "Ready for commands..."
                                
                            except sr.WaitTimeoutError:
                                state.is_listening = False
                                state.status = "Ready (timeout reset)"
                                continue
                                
                    except sr.UnknownValueError:
                        state.is_listening = False
                        state.status = "Ready (no speech detected)"
                        continue
                        
                    except Exception as e:
                        state.is_listening = False
                        console.print(f"[red]⚠️  Recognition error: {e}[/red]")
                        state.status = "Recognition error, retrying..."
                        time.sleep(1)
            
            # Start recognition in a separate thread
            recognition_thread = threading.Thread(target=recognition_loop, daemon=True)
            recognition_thread.start()
            break
            
        except Exception as e:
            console.print(f"[red]❌ Microphone setup error: {e}[/red]")
            state.status = "Microphone setup failed"
            console.print("[yellow]⚠️  Retrying in 5 seconds...[/yellow]")
            time.sleep(5)

# Live status updater
def update_status_display():
    def update_loop():
        while True:
            try:
                # Update display every 0.5 seconds
                console.clear()
                layout = create_status_display()
                console.print(layout)
                time.sleep(0.5)
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Display error:[/red] {e}")
                time.sleep(1)
    
    threading.Thread(target=update_loop, daemon=True).start()

# Enhanced shutdown handler
def handle_shutdown():
    console.print("\n[yellow]👋 Shutting down Kevin AI...[/yellow]")
    
    # Save current configuration
    state.save_config()
    
    # Cleanup audio devices
    device_manager.cleanup()
    
    speak("Kevin AI shutting down. Goodbye boss.")
    console.print("[green]✅ Kevin AI has been shut down successfully.[/green]")
    sys.exit(0)

# Main execution with better error handling
if __name__ == "__main__":
    try:
        # Show enhanced UI with device setup
        show_enhanced_ui()
        
        # Start listening
        listen_forever()
        
        # Start status display updater
        update_status_display()
        
        # Keep the program running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        handle_shutdown()
    except Exception as e:
        console.print(f"[red]💥 Fatal error: {e}[/red]")
        sys.exit(1)