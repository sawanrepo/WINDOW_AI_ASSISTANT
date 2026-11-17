"""Tests for core/system_control.py – brightness, volume, mute, control_system."""
import sys
import pytest
from unittest.mock import MagicMock, patch, call

# system_control imports screen_brightness_control which requires WMI; mock it
sys.modules.setdefault("wmi", MagicMock())

from core.system_control import (
    control_system,
    set_brightness,
    set_volume,
    mute_audio,
    unmute_audio,
)
from agent.tools import control_system_wrapper, tools
from agent.schema import SystemActionInput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_volume_mocks():
    """Return patchers for pycaw and pythoncom so no real audio device is needed."""
    mock_vol = MagicMock()
    mock_vol.GetMasterVolumeLevelScalar.return_value = 0.5  # 50%
    p_speakers = patch("core.system_control.AudioUtilities.GetSpeakers")
    p_cast = patch("core.system_control.cast", return_value=mock_vol)
    p_com = patch("pythoncom.CoInitialize")
    return p_speakers, p_cast, p_com, mock_vol


# ---------------------------------------------------------------------------
# control_system
# ---------------------------------------------------------------------------
class TestControlSystem:
    def test_invalid_action_returns_error(self):
        result = control_system("sleep")
        assert result["status"] == "error"
        assert "Invalid action" in result["message"]

    def test_empty_string_action(self):
        result = control_system("")
        assert result["status"] == "error"

    def test_case_insensitive_invalid(self):
        result = control_system("SHUTDOWN_NOW")
        assert result["status"] == "error"

    def test_shutdown_calls_subprocess(self, monkeypatch):
        """Shutdown invokes subprocess.run. The conftest fixture intercepts it safely."""
        from unittest.mock import MagicMock
        import subprocess
        calls = []
        orig = subprocess.run
        def recording_run(cmd, *args, **kwargs):
            calls.append(cmd)
            return MagicMock(returncode=0)
        monkeypatch.setattr(subprocess, "run", recording_run)
        control_system("shutdown")
        assert any("shutdown" in str(c).lower() for c in calls)

    def test_restart_calls_subprocess(self, monkeypatch):
        import subprocess
        calls = []
        monkeypatch.setattr(subprocess, "run", lambda cmd, *a, **k: (calls.append(cmd), MagicMock())[1])
        control_system("restart")
        assert any("shutdown" in str(c).lower() for c in calls)

    def test_logoff_calls_subprocess(self, monkeypatch):
        import subprocess
        calls = []
        monkeypatch.setattr(subprocess, "run", lambda cmd, *a, **k: (calls.append(cmd), MagicMock())[1])
        control_system("logoff")
        assert any("shutdown" in str(c).lower() for c in calls)


class TestControlSystemWrapper:
    def test_wrapper_pydantic_model(self):
        result = control_system_wrapper(SystemActionInput(action="unknown"))
        assert result["status"] == "error"

    def test_wrapper_dict_input(self):
        result = control_system_wrapper({"action": "unknown_action"})
        assert result["status"] == "error"

    def test_wrapper_string_input(self):
        result = control_system_wrapper("invalid_action")
        assert result["status"] == "error"

    def test_wrapper_invalid_object_type(self):
        result = control_system_wrapper(12345)
        assert result["status"] == "error"
        assert "Invalid input" in result["message"]

    def test_control_system_tool_registered(self):
        tool = next((t for t in tools if t.name == "ControlSystem"), None)
        assert tool is not None
        assert tool.args_schema == SystemActionInput


# ---------------------------------------------------------------------------
# set_brightness
# ---------------------------------------------------------------------------
class TestSetBrightness:
    @pytest.fixture(autouse=True)
    def mock_sbc(self):
        with patch("screen_brightness_control.get_brightness", return_value=[50]), \
             patch("screen_brightness_control.set_brightness") as mock_set:
            self.mock_set = mock_set
            yield

    def test_set_mode(self):
        res = set_brightness(mode="set", value=80)
        assert res["status"] == "success"
        assert "80" in res["message"]

    def test_increase_mode(self):
        res = set_brightness(mode="increase", value=20)
        assert res["status"] == "success"
        assert "70" in res["message"]  # 50 + 20 = 70

    def test_decrease_mode(self):
        res = set_brightness(mode="decrease", value=30)
        assert res["status"] == "success"
        assert "20" in res["message"]  # 50 - 30 = 20

    def test_clamp_max(self):
        res = set_brightness(mode="set", value=150)
        assert res["status"] == "success"
        assert "100" in res["message"]

    def test_clamp_min(self):
        res = set_brightness(mode="set", value=-50)
        assert res["status"] == "success"
        assert "0" in res["message"]

    def test_increase_beyond_100_clamps(self):
        res = set_brightness(mode="increase", value=100)
        assert res["status"] == "success"
        assert "100" in res["message"]

    def test_decrease_below_0_clamps(self):
        res = set_brightness(mode="decrease", value=100)
        assert res["status"] == "success"
        assert "0" in res["message"]

    def test_invalid_mode(self):
        res = set_brightness(mode="random", value=50)
        assert res["status"] == "error"
        assert "Invalid mode" in res["message"]

    def test_sbc_exception_handled(self):
        with patch("screen_brightness_control.get_brightness", side_effect=Exception("No display")):
            res = set_brightness(mode="set", value=50)
        assert res["status"] == "error"
        assert "Failed to set brightness" in res["message"]

    def test_brightness_tool_registered(self):
        tool = next((t for t in tools if t.name == "SetBrightness"), None)
        assert tool is not None


# ---------------------------------------------------------------------------
# set_volume, mute_audio, unmute_audio
# ---------------------------------------------------------------------------
class TestSetVolume:
    @pytest.fixture(autouse=True)
    def mock_audio(self):
        p_speakers, p_cast, p_com, mock_vol = make_volume_mocks()
        with p_speakers, p_cast, p_com:
            self.mock_vol = mock_vol
            yield

    def test_set_volume_80(self):
        res = set_volume(mode="set", value=80)
        assert res["status"] == "success"
        assert "80" in res["message"]

    def test_increase_volume(self):
        res = set_volume(mode="increase", value=20)
        assert res["status"] == "success"
        assert "70" in res["message"]  # 50 + 20 = 70

    def test_decrease_volume(self):
        res = set_volume(mode="decrease", value=30)
        assert res["status"] == "success"
        assert "20" in res["message"]  # 50 - 30 = 20

    def test_clamp_volume_max(self):
        res = set_volume(mode="set", value=150)
        assert res["status"] == "success"
        assert "100" in res["message"]

    def test_clamp_volume_min(self):
        res = set_volume(mode="set", value=-20)
        assert res["status"] == "success"
        assert "0" in res["message"]

    def test_invalid_mode_volume(self):
        res = set_volume(mode="max", value=50)
        assert res["status"] == "error"
        assert "Invalid mode" in res["message"]

    def test_volume_exception_handled(self):
        with patch("core.system_control.AudioUtilities.GetSpeakers", side_effect=Exception("No audio device")):
            res = set_volume(mode="set", value=50)
        assert res["status"] == "error"
        assert "Failed to set volume" in res["message"]

    def test_volume_tool_registered(self):
        tool = next((t for t in tools if t.name == "SetVolume"), None)
        assert tool is not None


class TestMuteUnmute:
    @pytest.fixture(autouse=True)
    def mock_audio(self):
        p_speakers, p_cast, p_com, mock_vol = make_volume_mocks()
        with p_speakers, p_cast, p_com:
            self.mock_vol = mock_vol
            yield

    def test_mute_success(self):
        res = mute_audio()
        assert res["status"] == "success"
        assert "muted" in res["message"].lower()

    def test_unmute_success(self):
        res = unmute_audio()
        assert res["status"] == "success"
        assert "unmuted" in res["message"].lower()

    def test_mute_exception_handled(self):
        with patch("core.system_control.AudioUtilities.GetSpeakers", side_effect=Exception("No device")):
            res = mute_audio()
        assert res["status"] == "error"

    def test_unmute_exception_handled(self):
        with patch("core.system_control.AudioUtilities.GetSpeakers", side_effect=Exception("No device")):
            res = unmute_audio()
        assert res["status"] == "error"

    def test_mute_calls_set_mute_1(self):
        mute_audio()
        self.mock_vol.SetMute.assert_called_once_with(1, None)

    def test_unmute_calls_set_mute_0(self):
        unmute_audio()
        self.mock_vol.SetMute.assert_called_once_with(0, None)

    def test_mute_tool_registered(self):
        tool = next((t for t in tools if t.name == "MuteAudio"), None)
        assert tool is not None

    def test_unmute_tool_registered(self):
        tool = next((t for t in tools if t.name == "UnmuteAudio"), None)
        assert tool is not None
