"""
Utility script to list audio devices and test TTS output.
Run: python audio_test.py
"""

import asyncio
import sys


def list_devices_pygame():
    """List audio devices using pygame/SDL."""
    print("\n=== Audio Output (pygame) ===")
    try:
        import pygame
        pygame.mixer.init()
        print(f"Pygame initialized - using system default audio device")
        print("To change output device, set it as default in Windows Sound Settings")
        pygame.mixer.quit()
    except Exception as e:
        print(f"pygame not available: {e}")


def list_devices_powershell():
    """List audio devices using PowerShell."""
    print("\n=== Audio Devices (Windows) ===")
    try:
        import subprocess
        
        # Try AudioDeviceCmdlets module first
        result = subprocess.run(
            ['powershell', '-c', '''
            try {
                Get-AudioDevice -List | ForEach-Object {
                    Write-Output "$($_.Index): $($_.Name) [$($_.Type)]"
                }
            } catch {
                # Fallback to WMI
                Get-WmiObject Win32_SoundDevice | ForEach-Object {
                    Write-Output "$($_.DeviceID): $($_.Name)"
                }
            }
            '''],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(result.stdout)
        else:
            print("No audio devices found or AudioDeviceCmdlets not installed.")
            print("\nTo install AudioDeviceCmdlets (optional):")
            print("  Install-Module -Name AudioDeviceCmdlets -Force")
            
    except Exception as e:
        print(f"Error: {e}")


async def test_edge_tts(voice: str = "en-US-GuyNeural"):
    """Test edge-tts playback."""
    print(f"\n=== Testing Edge TTS (voice: {voice}) ===")
    
    try:
        from tts_engine import EdgeTTSEngine, TTSMessage
        
        engine = EdgeTTSEngine(voice=voice, rate=175, volume=1.0)
        message = TTSMessage(text="Hello! This is a test of the text to speech system.")
        
        print("Playing test message...")
        await engine.speak(message)
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_pyttsx3():
    """Test pyttsx3 playback."""
    print("\n=== Testing pyttsx3 ===")
    
    try:
        import pyttsx3
        engine = pyttsx3.init()
        
        print("Available voices:")
        for i, voice in enumerate(engine.getProperty('voices')):
            print(f"  {i}: {voice.name}")
        
        print("\nPlaying test message...")
        engine.say("Hello! This is a test of the text to speech system.")
        engine.runAndWait()
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    print("=" * 50)
    print("  Chat TTS Reader - Audio Test Utility")
    print("=" * 50)
    
    list_devices_powershell()
    list_devices_pygame()
    
    print("\n" + "=" * 50)
    print("  Which TTS engine do you want to test?")
    print("=" * 50)
    print("  1. edge-tts (neural voices, better quality)")
    print("  2. pyttsx3 (Windows SAPI voices)")
    print("  3. Skip test")
    
    choice = input("\nChoice [1]: ").strip() or "1"
    
    if choice == "1":
        asyncio.run(test_edge_tts())
    elif choice == "2":
        test_pyttsx3()
    else:
        print("Skipped.")
    
    print("\n" + "=" * 50)
    print("  Troubleshooting Tips")
    print("=" * 50)
    print("""
If you don't hear audio:

1. Check Windows Volume Mixer
   - Right-click speaker icon → Open Volume Mixer
   - Make sure Python isn't muted

2. Check default playback device
   - Right-click speaker icon → Sound Settings
   - Set correct output device as default

3. For streaming with TTS to separate audio:
   - Use VoiceMeeter or Virtual Audio Cable
   - Set TTS to output to a virtual device
   - Route that to OBS

4. Try pyttsx3 instead of edge-tts
   - Run: python configure.py
   - Change TTS engine to pyttsx3
""")


if __name__ == "__main__":
    main()
