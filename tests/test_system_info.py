"""Tests for core/system_info.py and agent SystemInfo tool."""
import pytest
from unittest.mock import MagicMock, patch
import psutil

from core.system_info import get_system_status
from agent.schema import StatusInput
from agent.tools import system_info_wrapper, tools


class TestSystemInfoCore:
    """Unit tests for get_system_status with live and mocked psutil."""

    def test_get_system_status_cpu_live(self):
        """Live environment test: retrieve real CPU statistics."""
        res = get_system_status(["cpu"])
        assert "cpu" in res
        cpu = res["cpu"]
        assert isinstance(cpu["logical_cpus"], int)
        assert cpu["logical_cpus"] > 0
        assert isinstance(cpu["physical_cpus"], (int, type(None)))
        assert isinstance(cpu["cpu_usage_percent"], (int, float))
        assert 0.0 <= cpu["cpu_usage_percent"] <= 100.0

    def test_get_system_status_ram_live(self):
        """Live environment test: retrieve real RAM statistics."""
        res = get_system_status(["ram"])
        assert "ram" in res
        ram = res["ram"]
        assert ram["total_gb"] > 0.0
        assert ram["used_gb"] >= 0.0
        assert ram["available_gb"] >= 0.0
        assert 0.0 <= ram["ram_usage_percent"] <= 100.0

    def test_get_system_status_battery_live(self):
        """Live environment test: retrieve real Battery statistics or None."""
        res = get_system_status(["battery"])
        assert "battery" in res
        # Battery may be None on a desktop PC without UPS
        if res["battery"] is not None:
            bat = res["battery"]
            assert 0 <= bat["battery_percent"] <= 100
            assert isinstance(bat["charging"], (bool, type(None)))

    def test_get_system_status_all_live(self):
        """Live environment test: query CPU, RAM, and Battery in one call."""
        res = get_system_status(["cpu", "ram", "battery"])
        assert "cpu" in res
        assert "ram" in res
        assert "battery" in res

    def test_get_system_status_empty_list(self):
        """Query with empty requested list should return empty dict."""
        res = get_system_status([])
        assert res == {}

    def test_get_system_status_unsupported_metrics(self):
        """Query with unrecognized items should return empty dict."""
        res = get_system_status(["gpu", "disk", "network"])
        assert res == {}

    def test_get_system_status_mocked_battery_none(self):
        """Mocked test: desktop PC where psutil.sensors_battery() returns None."""
        with patch("psutil.sensors_battery", return_value=None):
            res = get_system_status(["battery"])
            assert res == {"battery": None}

    def test_get_system_status_mocked_battery_unlimited_secs(self):
        """Mocked test: battery secsleft == POWER_TIME_UNLIMITED -> secs_left should be None."""
        mock_bat = MagicMock(percent=85, power_plugged=True, secsleft=psutil.POWER_TIME_UNLIMITED)
        with patch("psutil.sensors_battery", return_value=mock_bat):
            res = get_system_status(["battery"])
            assert res["battery"]["secs_left"] is None
            assert res["battery"]["battery_percent"] == 85
            assert res["battery"]["charging"] is True

    def test_get_system_status_mocked_battery_calculating(self):
        """Mocked test: battery secsleft is 3600 seconds."""
        mock_bat = MagicMock(percent=50, power_plugged=False, secsleft=3600)
        with patch("psutil.sensors_battery", return_value=mock_bat):
            res = get_system_status(["battery"])
            assert res["battery"]["secs_left"] == 3600
            assert res["battery"]["battery_percent"] == 50


class TestSystemInfoWrapper:
    """Tests for system_info_wrapper and SystemInfo Tool registration."""

    def test_wrapper_with_pydantic_status_input(self):
        """Wrapper accepts StatusInput schema."""
        inp = StatusInput(requested=["cpu"])
        res = system_info_wrapper(inp)
        assert "cpu" in res

    def test_wrapper_with_raw_list(self):
        """Wrapper accepts raw list of strings."""
        res = system_info_wrapper(["ram"])
        assert "ram" in res

    def test_wrapper_with_dict_success(self):
        """Verified FIX: system_info_wrapper now accepts dict without AttributeError."""
        res = system_info_wrapper({"requested": ["cpu"]})
        assert "cpu" in res

    def test_tool_registration_and_invoke(self):
        """Test the registered SystemInfo LangChain tool invokes correctly."""
        tool = next((t for t in tools if t.name == "SystemInfo"), None)
        assert tool is not None
        assert tool.name == "SystemInfo"
        assert tool.args_schema == StatusInput
        # Invoking via tool handles dict-to-schema parsing
        res = tool.invoke({"requested": ["cpu"]})
        assert "cpu" in res
