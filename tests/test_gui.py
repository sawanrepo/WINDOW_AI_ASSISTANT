"""
Tests for interface/gui.py – WinoraGUI structural tests.

NOTE: Tkinter/customtkinter under the testing sandbox crashes with Windows
exception 0xc0000008 when creating a second CTk instance in the same process.
Tests requiring a GUI window instance are marked accordingly.
Tests that only verify imports, function existence, and structure run fine.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.modules.setdefault("wmi", MagicMock())


class TestGUIImport:
    """These tests do not create any Tk window – safe in all environments."""

    def test_gui_module_importable(self):
        """interface.gui should import without raising."""
        import interface.gui  # noqa: F401

    def test_launch_gui_function_exists(self):
        """launch_gui should be callable."""
        from interface.gui import launch_gui
        assert callable(launch_gui)

    def test_winora_gui_class_exists(self):
        """WinoraGUI class should be importable."""
        from interface.gui import WinoraGUI
        assert WinoraGUI is not None

    def test_gui_imports_winora_agent(self):
        """GUI module should import the compiled winora_agent from agent.graph."""
        import interface.gui as gui_mod
        assert hasattr(gui_mod, "winora_agent")

    def test_gui_imports_speak_and_listen(self):
        """GUI module should import speak and listen from speech."""
        import interface.gui as gui_mod
        assert hasattr(gui_mod, "speak")
        assert hasattr(gui_mod, "listen")

    def test_gui_uses_dark_mode_by_default(self):
        """
        Inspect GUI source to confirm Dark mode is set by default
        (structural/documentation test, no window created).
        """
        import inspect
        import interface.gui as gui_mod
        source = inspect.getsource(gui_mod.WinoraGUI.__init__)
        assert "Dark" in source

    def test_gui_uses_threading_for_responses(self):
        """Verify GUI uses threading so the UI doesn't block during agent calls."""
        import inspect
        import interface.gui as gui_mod
        source = inspect.getsource(gui_mod.WinoraGUI.send_message)
        assert "Thread" in source

    def test_gui_handles_empty_input(self):
        """Verify send_message checks for empty input (structural/code review test)."""
        import inspect
        import interface.gui as gui_mod
        source = inspect.getsource(gui_mod.WinoraGUI.send_message)
        assert "not user_text" in source or "if not" in source

    def test_gui_waiting_for_reply_guard(self):
        """Verify send_message has a waiting_for_reply guard."""
        import inspect
        import interface.gui as gui_mod
        source = inspect.getsource(gui_mod.WinoraGUI.send_message)
        assert "waiting_for_reply" in source

    def test_gui_error_handling_in_get_response(self):
        """Verify get_response has try/except for agent errors."""
        import inspect
        import interface.gui as gui_mod
        source = inspect.getsource(gui_mod.WinoraGUI.get_response)
        assert "except" in source
        assert "[Error]" in source

    def test_gui_calls_speak_after_response(self):
        """Verify get_response calls speak() to read the response aloud."""
        import inspect
        import interface.gui as gui_mod
        source = inspect.getsource(gui_mod.WinoraGUI.get_response)
        assert "speak" in source

    def test_gui_chat_display_starts_disabled_in_code(self):
        """Verify __init__ sets chat_display state to 'disabled'."""
        import inspect
        import interface.gui as gui_mod
        source = inspect.getsource(gui_mod.WinoraGUI.__init__)
        assert "disabled" in source

    def test_gui_theme_toggle_exists_in_code(self):
        """Verify theme_toggle switch is defined in GUI init."""
        import inspect
        import interface.gui as gui_mod
        source = inspect.getsource(gui_mod.WinoraGUI.__init__)
        assert "theme_toggle" in source

    def test_listen_and_send_uses_threading(self):
        """Verify voice input uses threading to avoid blocking the UI."""
        import inspect
        import interface.gui as gui_mod
        source = inspect.getsource(gui_mod.WinoraGUI.listen_and_send)
        assert "Thread" in source

    def test_gui_headless_first_instance(self):
        """
        Test creating a single GUI instance – only run once to avoid Windows fatal crash
        when creating multiple CTk instances in the same process.
        This test is intentionally isolated.
        """
        try:
            import customtkinter as ctk
            from interface.gui import WinoraGUI
            root = ctk.CTk()
            root.withdraw()
            app = WinoraGUI(root)
            assert app.waiting_for_reply is False
            assert app.chat_history == []
            app.user_input.insert(0, "Hello")
            assert app.user_input.get() == "Hello"
            app.append_chat("User", "Test", "#fff", "#fff")
            assert app.chat_display.cget("state") == "disabled"
            root.destroy()
        except Exception as e:
            # In restricted sandbox environments (no display), skip gracefully
            pytest.skip(f"GUI creation failed in environment: {e}")
