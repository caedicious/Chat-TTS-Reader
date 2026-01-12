# Chat TTS Reader

**Read YouTube, Kick, and TikTok live chat messages aloud via text-to-speech.**

Perfect for streamers who want to hear chat messages without looking away from gameplay.

[![Release](https://img.shields.io/github/v/release/caedicious/Chat-TTS-Reader?include_prereleases)](https://github.com/caedicious/Chat-TTS-Reader/releases)
[![Downloads](https://img.shields.io/github/downloads/caedicious/Chat-TTS-Reader/total)](https://github.com/caedicious/Chat-TTS-Reader/releases)
[![License](https://img.shields.io/github/license/caedicious/Chat-TTS-Reader)](LICENSE.txt)
![Platform](https://img.shields.io/badge/platform-Windows-blue)

<p align="center">
  <img src="https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube"/>
  <img src="https://img.shields.io/badge/Kick-53FC18?style=for-the-badge&logo=kick&logoColor=black" alt="Kick"/>
  <img src="https://img.shields.io/badge/TikTok-000000?style=for-the-badge&logo=tiktok&logoColor=white" alt="TikTok"/>
  <img src="https://img.shields.io/badge/Twitch-9146FF?style=for-the-badge&logo=twitch&logoColor=white" alt="Twitch"/>
</p>

---

## Features

- 🎙️ **Multi-Platform Chat** - Connect to YouTube Live, Kick.com, and TikTok Live simultaneously
- 🔊 **High-Quality TTS** - Choose between Windows SAPI voices or Microsoft Edge neural voices
- 🎯 **Smart Filtering** - Filter by message length, ignore commands/links, block users/words
- ⏰ **Auto-Start** - Optionally wait for your Twitch stream to go live before starting
- 🚀 **One-Click Setup** - Complete setup wizard handles everything
- 🔒 **Secure** - Credentials stored safely in Windows Credential Manager
- 📦 **Portable** - No system-wide installation required

---

## Quick Start (One-Click Setup)

### Requirements
- Windows 10/11
- [Python 3.10+](https://www.python.org/downloads/) (check "Add to PATH" during install)

### Setup

1. **Download** the latest release from [Releases](../../releases)
2. **Extract** to any folder
3. **Run `Setup.bat`**

That's it! The setup wizard will guide you through:
- Installing all dependencies
- Configuring your platforms (YouTube, Kick, TikTok)
- Setting up Twitch live detection (optional)
- Adding to Windows startup (optional)

---

## After Setup

### Starting the App

- **Manual start:** Double-click `start-chat-tts.bat`
- **Auto-start:** If configured, it runs when Windows starts (or when you go live on Twitch)

### Reconfiguring

Run `Setup.bat` again to change any settings.

### Quick Config Edit

Edit `%USERPROFILE%\.chat-tts-reader\config.json` directly for advanced settings.

---

## Platform Setup Notes

### YouTube
Just need the video ID or URL of your live stream.

### Kick
Kick blocks automated requests. The setup wizard will:
1. Ask for your channel name
2. Guide you to find your Chatroom ID (required for reliable connection)
3. Optionally open a browser for authenticated login

### TikTok
Just need your TikTok username. Works when you're live.

### Twitch (Optional)
For auto-start when you go live:
1. Create an app at [dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps)
2. Enter the Client ID during setup
3. The app will poll Twitch and start automatically when your stream goes live

---

## Configuration

All settings are stored in `%USERPROFILE%\.chat-tts-reader\config.json`

### TTS Settings
| Setting | Description | Default |
|---------|-------------|---------|
| `engine` | `edge-tts` (neural) or `pyttsx3` (offline) | `edge-tts` |
| `rate` | Speech rate (50-400 wpm) | `150` |
| `volume` | Volume (0.0-1.0) | `1.0` |
| `edge_voice` | Voice for Edge TTS | `en-US-GuyNeural` |

### Popular Edge TTS Voices
- `en-US-GuyNeural` (male, US)
- `en-US-JennyNeural` (female, US)
- `en-US-AriaNeural` (female, US)
- `en-GB-RyanNeural` (male, UK)
- `en-AU-WilliamNeural` (male, Australian)

### Auto-Start with Twitch Live Detection

If you enabled this during installation, Chat TTS Reader will:
1. Start when Windows boots
2. Wait until you go live on Twitch
3. Automatically start reading chat

### Available Scripts

| Script | Description |
|--------|-------------|
| `start-chat-tts.bat` | Start the TTS reader manually |
| `configure.bat` | Change platform settings |
| `test-audio.bat` | Test audio output |
| `uninstall.bat` | Remove from system |

---

## Configuration

### Platform Setup

Run `configure.bat` to set up your streaming platforms:

#### YouTube Live
- **Video ID**: The part after `v=` in your stream URL
- Example: `https://youtube.com/watch?v=ABC123` → Video ID is `ABC123`
- No API key required

#### Kick.com
- **Channel Name**: Your Kick username
- Example: `https://kick.com/yourchannel` → Channel is `yourchannel`
- ⚠️ Kick may block requests due to anti-bot protection

#### TikTok Live
- **Username**: Your TikTok username (with or without @)
- Must be live for it to connect

### TTS Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Engine | `pyttsx3` (Windows voices) or `edge-tts` (neural voices) | `pyttsx3` |
| Rate | Words per minute | 175 |
| Volume | 0.0 to 1.0 | 1.0 |

#### Popular Edge TTS Voices
- `en-US-GuyNeural` (male, American)
- `en-US-JennyNeural` (female, American)
- `en-US-AriaNeural` (female, American)
- `en-GB-RyanNeural` (male, British)

### Message Filters

| Filter | Description | Default |
|--------|-------------|---------|
| Min Length | Minimum characters | 1 |
| Max Length | Maximum characters | 300 |
| Ignore Commands | Skip messages starting with `!` | Yes |
| Ignore Links | Skip messages with URLs | Yes |
| Blocked Users | Usernames to ignore | None |
| Blocked Words | Words to filter | None |

---

## Twitch Live Detection

To automatically start when you go live:

1. Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps)
2. Register a new application:
   - **Name**: Anything (e.g., "ChatTTSReader")
   - **OAuth Redirect**: `http://localhost`
   - **Category**: Chat Bot
   - **Client Type**: Public
3. Copy the **Client ID**
4. Run `configure.bat` and enter the Client ID when prompted

---

## Audio Setup

### Default Setup
TTS plays through your Windows default audio device.

### For Streaming (Separate TTS Audio)
To route TTS to a separate audio source in OBS:

1. Install [VoiceMeeter](https://vb-audio.com/Voicemeeter/) or [Virtual Audio Cable](https://vb-audio.com/Cable/)
2. Set Windows default playback to the virtual device
3. In OBS, add the virtual device as an audio source
4. Route the virtual device to your headphones in VoiceMeeter

### Troubleshooting Audio

Run `test-audio.bat` to diagnose audio issues.

**No sound?**
- Check Windows Volume Mixer (right-click speaker → Volume Mixer)
- Ensure Python isn't muted
- Try switching from `edge-tts` to `pyttsx3` in configuration

---

## Troubleshooting

### "Python not found"
- Install Python from [python.org](https://python.org/downloads)
- **Make sure to check "Add Python to PATH"**
- Restart the installer after installing Python

### YouTube: "Could not find ytInitialData"
- Your stream isn't live yet, or chat is disabled
- The video ID might be wrong

### Kick: "403" or "Failed to get channel info"
- Kick is blocking API requests (anti-bot protection)
- Try again later or disable Kick in configuration

### TikTok: "User is not live"
- You must be live on TikTok for it to connect
- The app will wait and retry automatically

### TTS: No sound
- Run `test-audio.bat` to diagnose
- Check Windows Volume Mixer
- Try switching TTS engines in configuration

---

## File Structure

```
Chat-TTS-Reader/
├── install.bat          # Run this first!
├── start-chat-tts.bat   # Start manually
├── configure.bat        # Change settings
├── test-audio.bat       # Test audio
├── uninstall.bat        # Remove from system
├── requirements.txt     # Python dependencies
├── main.py              # Main application
├── config.py            # Configuration management
├── configure.py         # Configuration wizard
├── tts_engine.py        # TTS engines
├── audio_test.py        # Audio testing utility
├── wait_for_live.py     # Twitch live detection
└── platforms/           # Chat platform handlers
    ├── base.py
    ├── youtube.py
    ├── kick.py
    └── tiktok.py
```

---

## Configuration File

Settings are stored at: `%USERPROFILE%\.chat-tts-reader\config.json`

You can edit this file directly if needed.

---

## Uninstalling

1. Double-click `uninstall.bat`
2. Delete the application folder

This removes:
- Startup shortcut
- Virtual environment
- Stored credentials
- Configuration files

---

## License

MIT License - Feel free to modify and distribute.

---

## Credits

- [pytchat](https://github.com/taizan-hokuto/pytchat) - YouTube Live chat
- [TikTokLive](https://github.com/isaackogan/TikTokLive) - TikTok Live
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) - Text-to-speech
- [edge-tts](https://github.com/rany2/edge-tts) - Microsoft Edge TTS
- [pygame](https://pygame.org) - Audio playback

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [BUILD.md](BUILD.md) for development setup instructions.

---

## Support

Having issues? Check the [Troubleshooting](#troubleshooting) section above.

- 🐛 **Bug reports**: [Open an issue](../../issues/new?template=bug_report.md)
- 💡 **Feature requests**: [Open an issue](../../issues/new?template=feature_request.md)
- 💬 **Questions**: [Start a discussion](../../discussions)
