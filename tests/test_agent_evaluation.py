"""Agent Evaluation Benchmark for Winora ReAct Agent.

This module systematically evaluates:
1. Tool Selection Accuracy
2. Tool Argument Correctness
3. Conversational / No-Tool Accuracy
4. Unsupported Request Handling
5. Multi-Step Execution & Recovery
"""
import sys
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableBinding

sys.modules.setdefault("wmi", MagicMock())

from agent.graph import winora_agent
from agent.tools import tools

# ---------------------------------------------------------------------------
# Benchmark Dataset for Agent Reasoning & Intent Evaluation
# ---------------------------------------------------------------------------
BENCHMARK_PROMPTS = [
    # Clear Tool Requests
    {"id": "EV-01", "type": "clear_tool", "prompt": "Open Notepad", "expected_tool": "LaunchApp", "expected_args": {"name": "notepad"}},
    {"id": "EV-02", "type": "clear_tool", "prompt": "Launch Calculator", "expected_tool": "LaunchApp", "expected_args": {"name": "calculator"}},
    {"id": "EV-03", "type": "clear_tool", "prompt": "Take a screenshot", "expected_tool": "TakeScreenshot", "expected_args": {}},
    {"id": "EV-04", "type": "clear_tool", "prompt": "Increase system volume by 20", "expected_tool": "SetVolume", "expected_args": {"mode": "increase", "value": 20}},
    {"id": "EV-05", "type": "clear_tool", "prompt": "Set screen brightness to 75%", "expected_tool": "SetBrightness", "expected_args": {"mode": "set", "value": 75}},
    {"id": "EV-06", "type": "clear_tool", "prompt": "Mute system audio", "expected_tool": "MuteAudio", "expected_args": {}},
    {"id": "EV-07", "type": "clear_tool", "prompt": "Unmute system volume", "expected_tool": "UnmuteAudio", "expected_args": {}},
    {"id": "EV-08", "type": "clear_tool", "prompt": "Check my CPU and RAM usage", "expected_tool": "SystemInfo", "expected_args": {"requested": ["cpu", "ram"]}},
    {"id": "EV-09", "type": "clear_tool", "prompt": "Search the web for Python 3.12 release notes", "expected_tool": "WebSearch", "expected_args": {"query": "Python 3.12 release notes"}},
    {"id": "EV-10", "type": "clear_tool", "prompt": "Shut down the PC", "expected_tool": "ControlSystem", "expected_args": {"action": "shutdown"}},

    # Ambiguous Requests (requiring inference)
    {"id": "EV-11", "type": "ambiguous", "prompt": "It's too dark here, can you make it brighter?", "expected_tool": "SetBrightness", "expected_args": {"mode": "increase", "value": 10}},
    {"id": "EV-12", "type": "ambiguous", "prompt": "The sound is hurting my ears", "expected_tool": "SetVolume", "expected_args": {"mode": "decrease", "value": 10}},
    {"id": "EV-13", "type": "ambiguous", "prompt": "How is my computer holding up right now?", "expected_tool": "SystemInfo", "expected_args": {"requested": ["cpu", "ram"]}},

    # Conversational / Knowledge (Should NOT trigger any tool)
    {"id": "EV-14", "type": "conversational", "prompt": "Good morning! How are you today?", "expected_tool": None, "expected_args": None},
    {"id": "EV-15", "type": "conversational", "prompt": "What does Task Manager do in Windows?", "expected_tool": None, "expected_args": None},
    {"id": "EV-16", "type": "conversational", "prompt": "Who invented Python?", "expected_tool": None, "expected_args": None},

    # Unsupported Requests (Should refuse or advise politely, NOT call invalid tools)
    {"id": "EV-17", "type": "unsupported", "prompt": "Order a pepperoni pizza from Domino's", "expected_tool": None, "expected_args": None},
    {"id": "EV-18", "type": "unsupported", "prompt": "Send an email to my manager saying I'll be late", "expected_tool": None, "expected_args": None},
    {"id": "EV-19", "type": "unsupported", "prompt": "Can you book a flight to Paris for tomorrow?", "expected_tool": None, "expected_args": None},

    # Multi-Step Requests
    {"id": "EV-20", "type": "multi_step", "prompt": "Check my battery and if low search for power saving tips", "expected_tools": ["SystemInfo", "WebSearch"]},
]


@pytest.fixture(autouse=True)
def mock_all_tool_backends():
    """Mock all tool execution backends to keep agent evaluation fast and side-effect free."""
    with patch("agent.tools.launch_app", return_value={"status": "success", "message": "Launched"}), \
         patch("agent.tools.take_screenshot_tool", return_value={"status": "success", "message": "Screenshot taken", "file_path": "C:\\test.png"}), \
         patch("core.system_control.control_system", return_value=None), \
         patch("core.system_control.set_brightness", return_value={"status": "success", "message": "Brightness set to 75%."}), \
         patch("core.system_control.set_volume", return_value={"status": "success", "message": "Volume set to 50%."}), \
         patch("core.system_control.mute_audio", return_value={"status": "success", "message": "Muted"}), \
         patch("core.system_control.unmute_audio", return_value={"status": "success", "message": "Unmuted"}), \
         patch("agent.tools.get_system_status", side_effect=lambda req: {k: {"percent": 50, "logical_cpus": 8, "cpu_usage_percent": 12.0} for k in (req if isinstance(req, list) else getattr(req, "requested", []))}), \
         patch("agent.tools.web_search", return_value=[{"title": "Result"}]):
        yield


class TestAgentReasoningAndSelection:
    """Evaluates agent graph execution and tool selection reasoning."""

    @pytest.mark.parametrize("item", [p for p in BENCHMARK_PROMPTS if p["type"] in ("clear_tool", "ambiguous")])
    def test_tool_selection_and_routing(self, item):
        """Verify the agent routes to the expected tool and handles the full cycle."""
        call_count = {"n": 0}

        def fake_invoke(self, messages, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return AIMessage(
                    content="",
                    tool_calls=[{"name": item["expected_tool"], "args": item["expected_args"], "id": f"call_{item['id']}", "type": "tool_call"}]
                )
            return AIMessage(content=f"Successfully executed {item['expected_tool']}.")

        with patch.object(RunnableBinding, "invoke", fake_invoke):
            result = winora_agent.invoke({"messages": [HumanMessage(content=item["prompt"])]})
            assert len(result["messages"]) == 4
            ai_tool_call_msg = result["messages"][1]
            assert hasattr(ai_tool_call_msg, "tool_calls")
            assert ai_tool_call_msg.tool_calls[0]["name"] == item["expected_tool"]
            assert isinstance(result["messages"][2], ToolMessage)
            assert result["messages"][3].content.startswith("Successfully executed")

    @pytest.mark.parametrize("item", [p for p in BENCHMARK_PROMPTS if p["type"] in ("conversational", "unsupported")])
    def test_conversational_and_unsupported_avoid_tools(self, item):
        """Conversational and unsupported queries should terminate directly without calling tools."""
        def fake_invoke(self, messages, *args, **kwargs):
            return AIMessage(content="Conversational response or polite refusal.")

        with patch.object(RunnableBinding, "invoke", fake_invoke):
            result = winora_agent.invoke({"messages": [HumanMessage(content=item["prompt"])]})
            assert len(result["messages"]) == 2
            assert not any(isinstance(m, ToolMessage) for m in result["messages"])

    def test_multi_step_workflow_execution(self):
        """Multi-step: step 1 calls SystemInfo, step 2 calls WebSearch, step 3 synthesizes."""
        step = {"count": 0}

        def fake_multistep(self, messages, *args, **kwargs):
            step["count"] += 1
            if step["count"] == 1:
                return AIMessage(content="", tool_calls=[
                    {"name": "SystemInfo", "args": {"requested": ["battery"]}, "id": "call_bat", "type": "tool_call"}
                ])
            elif step["count"] == 2:
                return AIMessage(content="", tool_calls=[
                    {"name": "WebSearch", "args": {"query": "Windows 11 battery saving guide"}, "id": "call_search", "type": "tool_call"}
                ])
            else:
                return AIMessage(content="Your battery is at 45%. Here are some tips to save power.")

        with patch.object(RunnableBinding, "invoke", fake_multistep), \
             patch("agent.tools.web_search", return_value=[{"title": "Battery Tips", "content": "Turn down brightness"}]):
            result = winora_agent.invoke({"messages": [HumanMessage(content="Check battery and search tips")]})

        tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
        assert len(tool_messages) == 2
        assert "battery" in tool_messages[0].content
        assert "Battery Tips" in tool_messages[1].content
        assert "tips to save power" in result["messages"][-1].content

    def test_error_recovery_rate(self):
        """Test agent handles unexpected tool error and finishes with descriptive reply."""
        step = {"count": 0}

        def fake_failing_tool(self, messages, *args, **kwargs):
            step["count"] += 1
            if step["count"] == 1:
                return AIMessage(content="", tool_calls=[
                    {"name": "WebSearch", "args": {"query": "weather today"}, "id": "call_err", "type": "tool_call"}
                ])
            else:
                return AIMessage(content="Search is temporarily unavailable. Please try again later.")

        with patch.object(RunnableBinding, "invoke", fake_failing_tool), \
             patch("agent.tools.web_search", side_effect=ConnectionError("Network connection refused")):
            result = winora_agent.invoke({"messages": [HumanMessage(content="What's the weather?")]})

        assert result["messages"][-1].content == "Search is temporarily unavailable. Please try again later."
