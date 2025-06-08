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
        return {"status": "error",
                "message": f"Invalid action '{action}'. Use 'shutdown', 'restart', or 'logoff'."}

def set_brightness(mode: str, value: int) -> dict:
    try:
        mode = mode.lower()
        current = sbc.get_brightness(display=0)[0]

        if mode == "set":
            new_level = min(max(value, 0), 100)
        elif mode == "increase":
            new_level = min(current + value, 100)
        elif mode == "decrease":
            new_level = max(current - value, 0)
        else:
            return {"status": "error",
                    "message": f"Invalid mode '{mode}'. Use 'set', 'increase', or 'decrease'."}

        sbc.set_brightness(new_level, display=0)
        return {"status": "success",
                "message": f"Brightness successfully set to {new_level}%."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to set brightness: {e}"}

def set_volume(mode: str, value: int) -> dict:
    try:
        pythoncom.CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        current = volume.GetMasterVolumeLevelScalar() * 100

        if mode == "set":
            new_level = min(max(value, 0), 100)
        elif mode == "increase":
            new_level = min(current + value, 100)
        elif mode == "decrease":
            new_level = max(current - value, 0)
        else:
            return {"status": "error",
                    "message": f"Invalid mode '{mode}'. Use 'set', 'increase', or 'decrease'."}

        volume.SetMasterVolumeLevelScalar(new_level / 100, None)
        return {"status": "success",
                "message": f"Volume successfully set to {round(new_level)}%."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to set volume: {e}"}


def mute_audio() -> dict:
    try:
        pythoncom.CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1, None)
        return {"status": "success", "message": "System volume has been muted."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to mute volume: {e}"}


def unmute_audio() -> dict:
    try:
        pythoncom.CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(0, None)
        return {"status": "success", "message": "System volume has been unmuted."}  
    except Exception as e:
        return {"status": "error", "message": f"Failed to unmute volume: {e}"}