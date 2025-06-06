import subprocess
import platform
import pythoncom
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc


def control_system(action: str):
    action = action.lower()
    if action == "shutdown":
        subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
    elif action == "restart":
        subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
    elif action == "logoff":
        subprocess.run(["shutdown", "/l"], check=True)
    else:
        raise ValueError(f"Unsupported action: {action}")


def set_brightness(level: int) -> str:
    try:
        if level == 0:
            current = sbc.get_brightness(display=0)[0]
            new_level = min(current + 10, 100)
        else:
            new_level = min(max(level, 0), 100)
        sbc.set_brightness(new_level, display=0)
        return f"Brightness successfully set to {new_level}%."
    except Exception as e:
        raise RuntimeError(f"Failed to set brightness: {e}")


def set_volume(level: int) -> str:
    try:
        pythoncom.CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        current = volume.GetMasterVolumeLevelScalar() * 100
        if level == 0:
            new_level = min(current + 10, 100)
        else:
            new_level = min(max(level, 0), 100)

        volume.SetMasterVolumeLevelScalar(new_level / 100, None)
        return f"Volume successfully set to {round(new_level)}%."
    except Exception as e:
        raise RuntimeError(f"Failed to set volume: {e}")


def mute_audio() -> str:
    try:
        pythoncom.CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1, None)
        return "System volume has been muted."
    except Exception as e:
        raise RuntimeError(f"Failed to mute volume: {e}")


def unmute_audio() -> str:
    try:
        pythoncom.CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(0, None)
        return "System volume has been unmuted."
    except Exception as e:
        raise RuntimeError(f"Failed to unmute volume: {e}")