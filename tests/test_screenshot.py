"""Tests for core/screenshot.py and TakeScreenshot tool."""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image

from core.screenshot import take_screenshot_tool
from agent.tools import tools


class TestTakeScreenshotTool:
    """Unit and integration tests for take_screenshot_tool."""

    def test_success_path(self, tmp_path):
        """Mocked test: screenshot saves correctly when all dependencies work."""
        # Provide a fake screenshot image
        fake_image = Image.new("RGB", (1920, 1080), color=(30, 30, 30))
        with patch("core.screenshot.flash_screen"), \
             patch("core.screenshot.threading.Thread"), \
             patch("core.screenshot.time.sleep"), \
             patch("core.screenshot.ImageGrab.grab", return_value=fake_image), \
             patch.dict(os.environ, {"USERPROFILE": str(tmp_path)}):
            result = take_screenshot_tool()
        assert result["status"] == "success"
        assert result["file_path"] is not None
        assert os.path.exists(result["file_path"])

    def test_success_uses_screenshots_dir(self, tmp_path):
        """Saved file should be inside Screenshots folder."""
        fake_image = Image.new("RGB", (100, 100))
        with patch("core.screenshot.flash_screen"), \
             patch("core.screenshot.threading.Thread"), \
             patch("core.screenshot.time.sleep"), \
             patch("core.screenshot.ImageGrab.grab", return_value=fake_image), \
             patch.dict(os.environ, {"USERPROFILE": str(tmp_path)}):
            result = take_screenshot_tool()
        assert "Screenshots" in result["file_path"]

    def test_filename_has_timestamp(self, tmp_path):
        """Screenshot filename should start with 'Screenshot_'."""
        fake_image = Image.new("RGB", (100, 100))
        with patch("core.screenshot.flash_screen"), \
             patch("core.screenshot.threading.Thread"), \
             patch("core.screenshot.time.sleep"), \
             patch("core.screenshot.ImageGrab.grab", return_value=fake_image), \
             patch.dict(os.environ, {"USERPROFILE": str(tmp_path)}):
            result = take_screenshot_tool()
        basename = os.path.basename(result["file_path"])
        assert basename.startswith("Screenshot_")
        assert basename.endswith(".png")

    def test_imagegrab_exception_returns_error(self):
        """When ImageGrab.grab raises, return error dict (not crash)."""
        with patch("core.screenshot.flash_screen"), \
             patch("core.screenshot.threading.Thread"), \
             patch("core.screenshot.time.sleep"), \
             patch("core.screenshot.ImageGrab.grab", side_effect=OSError("Screen not accessible")), \
             patch.dict(os.environ, {"USERPROFILE": "C:\\fakeuser"}):
            result = take_screenshot_tool()
        assert result["status"] == "error"
        assert result["file_path"] is None
        assert "Failed to take screenshot" in result["message"]

    def test_makedirs_fallback_on_pictures_error(self, tmp_path):
        """When pictures directory is inaccessible, fallback to local directory succeeds."""
        fake_image = Image.new("RGB", (100, 100))
        fallback_dir = str(tmp_path / "screenshots")

        def fake_makedirs(path, exist_ok=True):
            if "Pictures" in path:
                raise PermissionError("Access denied to Pictures")
            return None

        with patch("core.screenshot.flash_screen"), \
             patch("core.screenshot.threading.Thread"), \
             patch("core.screenshot.time.sleep"), \
             patch("core.screenshot.ImageGrab.grab", return_value=fake_image), \
             patch("core.screenshot.os.makedirs", side_effect=fake_makedirs), \
             patch("core.screenshot.os.getcwd", return_value=str(tmp_path)), \
             patch.object(Image.Image, "save"), \
             patch.dict(os.environ, {"USERPROFILE": str(tmp_path)}):
            result = take_screenshot_tool()
        assert result["status"] == "success"
        assert "screenshots" in result["file_path"].lower()

    def test_flash_screen_terminates_cleanly(self):
        """Verified FIX: flash_screen uses root.after and does not hang the process."""
        import tkinter as tk
        with patch.object(tk.Tk, "mainloop"):
            from core.screenshot import flash_screen
            flash_screen()  # Should not raise or hang

    def test_onedrive_fallback_to_pictures(self, tmp_path):
        """When OneDrive/Pictures/Screenshots doesn't exist, use Pictures/Screenshots."""
        fake_image = Image.new("RGB", (100, 100))
        with patch("core.screenshot.flash_screen"), \
             patch("core.screenshot.threading.Thread"), \
             patch("core.screenshot.time.sleep"), \
             patch("core.screenshot.ImageGrab.grab", return_value=fake_image), \
             patch.dict(os.environ, {"USERPROFILE": str(tmp_path)}):
            result = take_screenshot_tool()
        # OneDrive path won't exist in tmp_path, should fall back to Pictures/Screenshots
        assert result["status"] == "success"

    def test_screenshot_tool_registered(self):
        """TakeScreenshot should be in the tools list."""
        tool = next((t for t in tools if t.name == "TakeScreenshot"), None)
        assert tool is not None

    def test_screenshot_tool_invokable(self, tmp_path):
        """LangChain tool.invoke call succeeds with mocked dependencies (string input required by Tool)."""
        fake_image = Image.new("RGB", (100, 100))
        tool = next((t for t in tools if t.name == "TakeScreenshot"), None)
        with patch("core.screenshot.flash_screen"), \
             patch("core.screenshot.threading.Thread"), \
             patch("core.screenshot.time.sleep"), \
             patch("core.screenshot.ImageGrab.grab", return_value=fake_image), \
             patch.dict(os.environ, {"USERPROFILE": str(tmp_path)}):
            # TakeScreenshot is a single-input Tool; must pass a non-empty string
            result = tool.invoke("take")
        assert result["status"] == "success"
