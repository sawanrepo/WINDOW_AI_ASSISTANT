"""Global test configuration and fixtures for Winora test suite."""
import os
import sys
from unittest.mock import MagicMock

# Safeguard for Windows sandbox environments where WMI moniker binding is restricted
try:
    import wmi  # noqa: F401
except Exception:
    sys.modules["wmi"] = MagicMock()

import pytest


@pytest.fixture(autouse=True)
def prevent_real_destructive_commands(monkeypatch):
    """Safety guard: ensure subprocess.run never actually executes system shutdown/restart/logoff."""
    import subprocess
    real_run = subprocess.run

    def safe_subprocess_run(cmd, *args, **kwargs):
        if isinstance(cmd, (list, tuple)) and len(cmd) > 0:
            executable = str(cmd[0]).lower()
            if executable == "shutdown" or executable.endswith("shutdown.exe"):
                # Safety mock: intercept destructive system calls
                mock_res = MagicMock()
                mock_res.returncode = 0
                mock_res.stdout = "Safety Intercept: Shutdown prevented during automated testing."
                mock_res.stderr = ""
                return mock_res
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", safe_subprocess_run)
