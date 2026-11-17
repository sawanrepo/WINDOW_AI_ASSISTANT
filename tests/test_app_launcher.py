"""Tests for core/app_launcher.py and agent LaunchApp tool."""
import os
import pytest
from unittest.mock import MagicMock, patch, call

from core.app_launcher import name_matches, get_uwp_apps, launch_uwp_app, launch_app
from agent.tools import launch_app_wrapper, tools
from agent.schema import AppInput


class TestNameMatches:
    """Unit tests for the name_matches helper function."""

    def test_exact_match_without_extension(self):
        assert name_matches("notepad.exe", "notepad") is True

    def test_starts_with_match(self):
        assert name_matches("notepad lite.exe", "notepad") is True

    def test_no_false_positive_underscore(self):
        """'notepad_old.exe' should NOT match 'notepad' (strict matching)."""
        assert name_matches("notepad_old.exe", "notepad") is False

    def test_no_false_positive_no_space_prefix(self):
        """'mynotepad.exe' should NOT match 'notepad' – word boundary enforced."""
        assert name_matches("mynotepad.exe", "notepad") is False

    def test_plus_in_name(self):
        assert name_matches("notepad++.exe", "notepad++") is True

    def test_empty_filename(self):
        assert name_matches("", "notepad") is False

    def test_empty_app_name_matches_all(self):
        """Empty app_name matches any filename because word-boundary regex matches empty string."""
        assert name_matches("notepad.exe", "") is True

    def test_case_insensitive(self):
        assert name_matches("Notepad.EXE", "notepad") is True

    def test_calc_match(self):
        assert name_matches("calc.exe", "calc") is True

    def test_no_extension_still_works(self):
        assert name_matches("notepad", "notepad") is True


class TestGetUwpApps:
    """Tests for get_uwp_apps PowerShell integration."""

    def test_returns_list(self):
        """Live test: get_uwp_apps returns a list (may be empty in restricted envs)."""
        result = get_uwp_apps()
        assert isinstance(result, list)

    def test_returns_tuples_of_two(self):
        """Each entry should be a 2-tuple (name, appid)."""
        result = get_uwp_apps()
        for item in result:
            assert isinstance(item, tuple) and len(item) == 2

    def test_mocked_powershell_failure(self):
        """When PowerShell call raises, get_uwp_apps returns empty list."""
        with patch("subprocess.run", side_effect=Exception("PowerShell blocked")):
            result = get_uwp_apps()
        assert result == []


class TestLaunchUwpApp:
    """Tests for launch_uwp_app UWP resolution logic."""

    def test_matching_app_found(self):
        """When a matching UWP app is found, it should return success."""
        fake_apps = [("Notepad", "Windows.notepad_8wekyb3d8bbwe!App")]
        with patch("core.app_launcher.get_uwp_apps", return_value=fake_apps), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = launch_uwp_app("notepad")
        assert result["status"] == "success"
        assert "Notepad" in result["message"]

    def test_no_matching_app(self):
        """When no UWP app matches, return not_found."""
        with patch("core.app_launcher.get_uwp_apps", return_value=[]):
            result = launch_uwp_app("nonexistentapp12345")
        assert result["status"] == "not_found"

    def test_launch_raises_exception(self):
        """When subprocess.run raises, return error dict."""
        fake_apps = [("Notepad", "Windows.notepad")]
        with patch("core.app_launcher.get_uwp_apps", return_value=fake_apps), \
             patch("subprocess.run", side_effect=Exception("Launch failed")):
            result = launch_uwp_app("notepad")
        assert result["status"] == "error"
        assert "Failed to launch" in result["message"]

    def test_launch_permission_error(self):
        """When exception message contains 'permission', return permission_denied."""
        fake_apps = [("SomeAdminApp", "Microsoft.AdminApp")]
        with patch("core.app_launcher.get_uwp_apps", return_value=fake_apps), \
             patch("subprocess.run", side_effect=Exception("Access permission denied")):
            result = launch_uwp_app("adminapp")
        assert result["status"] == "permission_denied"


class TestLaunchApp:
    """Integration tests for the main launch_app function."""

    def test_launch_known_app_in_path(self):
        """Mocked test: 'notepad' via PATH lookup – os.startfile mocked to avoid real launch."""
        with patch("core.app_launcher.get_uwp_apps", return_value=[]), \
             patch("os.startfile") as mock_start, \
             patch("os.path.isfile", return_value=True):
            result = launch_app("notepad")
        # Should find it via PATH or start-menu
        assert result["status"] in ("success", "not_found", "permission_denied")

    def test_launch_nonexistent_app(self):
        """Launch a clearly nonexistent app returns not_found."""
        with patch("core.app_launcher.get_uwp_apps", return_value=[]), \
             patch("os.path.isfile", return_value=False), \
             patch("os.walk", return_value=iter([])):
            result = launch_app("thisappdoesnotexist_xyz_12345")
        assert result["status"] == "not_found"

    def test_launch_empty_string(self):
        """Launch with empty string – documents behavior: should not crash."""
        with patch("core.app_launcher.get_uwp_apps", return_value=[]), \
             patch("os.path.isfile", return_value=False), \
             patch("os.walk", return_value=iter([])):
            result = launch_app("")
        # Behavior is unspecified: should not crash
        assert isinstance(result, dict)
        assert "status" in result


class TestLaunchAppWrapper:
    """Tests for the launch_app_wrapper adapter in agent/tools.py."""

    def test_wrapper_string_input(self):
        with patch("agent.tools.launch_app", return_value={"status": "success", "message": "ok"}) as mock:
            result = launch_app_wrapper("notepad")
        mock.assert_called_once_with("notepad")
        assert result["status"] == "success"

    def test_wrapper_dict_input(self):
        with patch("agent.tools.launch_app", return_value={"status": "success", "message": "ok"}) as mock:
            result = launch_app_wrapper({"name": "calc"})
        mock.assert_called_once_with("calc")

    def test_wrapper_pydantic_input(self):
        with patch("agent.tools.launch_app", return_value={"status": "success", "message": "ok"}) as mock:
            result = launch_app_wrapper(AppInput(name="spotify"))
        mock.assert_called_once_with("spotify")

    def test_launch_app_tool_registered(self):
        """LaunchApp tool should be registered in tools list."""
        tool = next((t for t in tools if t.name == "LaunchApp"), None)
        assert tool is not None
        assert tool.args_schema == AppInput

    def test_launch_tool_invoke_with_dict(self):
        """LaunchApp tool.invoke accepts dict args via schema conversion."""
        with patch("agent.tools.launch_app", return_value={"status": "success", "message": "Launched"}):
            tool = next((t for t in tools if t.name == "LaunchApp"), None)
            result = tool.invoke({"name": "notepad"})
        assert result["status"] == "success"

    def test_launch_tool_invoke_wrong_key_fails(self):
        """
        BUG DOCUMENTATION: prompt few-shot examples use 'app_name' but schema requires 'name'.
        When invoked via LangGraph ToolNode with {'app_name': 'notepad'}, Pydantic
        raises ValidationError – it propagates out of tool.invoke() (not silently caught).
        This confirms the prompt/schema mismatch is a real bug.
        """
        from pydantic import ValidationError
        tool = next((t for t in tools if t.name == "LaunchApp"), None)
        with pytest.raises(ValidationError):
            tool.invoke({"app_name": "notepad"})
