# K.E.V.I.N - Voice Controlled Media Assistant 🎧

K.E.V.I.N (Keyboard-Emulating Voice Interface Navigator) is a dual-headset voice control system that allows you to control media playback and system functions using natural voice commands.

## ⚠️ Important Note
**Python Version Requirement: 10.0.0**
```bash
python --version  # Should output: Python 10.0.0
```

## 🚀 Quick Start
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Run K.E.V.I.N:
   ```bash
   python kevin.py
   ```

## 📦 Required Libraries
```txt
speech_recognition
pyautogui
playsound
gTTS
rich
pycaw
sounddevice
soundfile
pyaudio
wave
comtypes
```

## 🎮 Available Commands

### Media Controls
- **Pause/Stop**: 
  - "pause", "stop", "halt", "freeze"
- **Play/Resume**: 
  - "play", "start", "resume", "continue", "unpause"
- **Forward/Next**: 
  - "forward", "next", "skip", "ahead", "advance"
- **Backward/Previous**: 
  - "back", "previous", "rewind", "return", "behind"

### Volume Controls
- **Volume Up**: 
  - "volume up", "louder", "increase volume", "turn up", "raise volume"
- **Volume Down**: 
  - "volume down", "quieter", "decrease volume", "turn down", "lower volume"
- **Mute**: 
  - "mute", "silence", "quiet", "no sound", "shut up"
- **Unmute**: 
  - "unmute", "unsilence", "sound on", "restore sound"

### Navigation
- **Scroll Up**: 
  - "scroll up", "move up", "go up", "upward", "up"
- **Scroll Down**: 
  - "scroll down", "move down", "go down", "downward", "down"

### System Commands
- **Device Info**: 
  - "check devices", "device status", "audio setup", "sound setup"
- **Status Check**: 
  - "how are you", "status"

### Social Interactions
- **Greetings**: 
  - "hello", "hi", "hey", "greetings"
- **Thanks**: 
  - "thank you", "thanks", "appreciate"
- **Praise**: 
  - "good job", "nice work", "well done"

## 🎧 Dual Headset Setup
K.E.V.I.N supports using different devices for input (microphone) and output (speakers). During first launch:
1. Select your preferred microphone from the list
2. Select your preferred audio output device
3. Configuration is saved automatically

## 🔍 Features
- Natural language command processing
- Dual headset support
- Real-time status display
- Automatic device testing
- Configuration persistence
- Rich command-line interface
- Automatic error recovery
- Wake word detection ("Kevin")

## 💡 Tips
- Prefix any command with "Kevin" to ensure it's recognized
- Speak clearly and in a normal tone
- Commands can be phrased naturally
- Configuration is saved between sessions
- Use "check devices" to verify audio setup

## ⚠️ Troubleshooting
If you encounter issues:
1. Ensure correct Python version (10.0.0)
2. Check microphone permissions
3. Verify audio devices are connected
4. Try resetting configuration
5. Check for background noise

## 🎯 Message from Creator
> "I know it's complicated, but it is what it is. K.E.V.I.N was built to make life easier through voice commands, even if its setup isn't the simplest. The complexity comes from making it robust and flexible enough to handle real-world usage. Stick with it - once you're past the initial setup, it's smooth sailing!"

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing
Feel free to submit issues and enhancement requests! 