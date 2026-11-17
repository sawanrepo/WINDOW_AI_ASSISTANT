"""
Tests for agent/graph.py – LangGraph ReAct loop, routing, and tool integration.
All LLM calls are mocked; no live Gemini API is used.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableBinding

sys.modules.setdefault("wmi", MagicMock())

import agent.graph as graph_module
from agent.graph import winora_agent, tool_router, agent_node, AgentState


# ---------------------------------------------------------------------------
# tool_router
# ---------------------------------------------------------------------------
class TestToolRouter:
    def _state(self, messages):
        return {"messages": messages}

    def test_routes_to_tool_node_on_tool_calls(self):
        msg = AIMessage(content="", tool_calls=[
            {"name": "SystemInfo", "args": {"requested": ["cpu"]}, "id": "tc1", "type": "tool_call"}
        ])
        result = tool_router(self._state([msg]))
        assert result == "tool_node"

    def test_routes_to_end_on_no_tool_calls(self):
        from langgraph.graph import END
        msg = AIMessage(content="Hello!")
        result = tool_router(self._state([msg]))
        assert result == END

    def test_routes_to_end_on_empty_tool_calls(self):
        from langgraph.graph import END
        msg = AIMessage(content="Done.", tool_calls=[])
        result = tool_router(self._state([msg]))
        assert result == END

    def test_routes_to_end_on_human_message(self):
        from langgraph.graph import END
        msg = HumanMessage(content="Hello")
        result = tool_router(self._state([msg]))
        assert result == END


# ---------------------------------------------------------------------------
# Full graph execution – mocked LLM
# ---------------------------------------------------------------------------
class TestWinoraAgentGraph:

    def _run_with_fake_llm(self, fake_invoke_fn, user_input):
        with patch.object(RunnableBinding, "invoke", fake_invoke_fn):
            return winora_agent.invoke({"messages": [HumanMessage(content=user_input)]})

    def test_simple_conversational_response(self):
        """Agent returns a final AIMessage with no tool calls for a greeting."""
        def fake(self, messages, *a, **kw):
            return AIMessage(content="Hello! How can I help?")

        result = self._run_with_fake_llm(fake, "Hello")
        assert result["messages"][-1].content == "Hello! How can I help?"

    def test_single_tool_call_then_final_response(self):
        """Agent: tool call -> tool executes -> LLM synthesises final answer."""
        step = {"n": 0}

        def fake(self, messages, *a, **kw):
            step["n"] += 1
            if step["n"] == 1:
                return AIMessage(content="", tool_calls=[
                    {"name": "SystemInfo", "args": {"requested": ["cpu"]}, "id": "c1", "type": "tool_call"}
                ])
            return AIMessage(content="CPU looks fine.")

        result = self._run_with_fake_llm(fake, "What is my CPU usage?")
        messages = result["messages"]
        # HumanMessage, AIMessage(tool_call), ToolMessage, AIMessage(final)
        assert len(messages) == 4
        assert isinstance(messages[2], ToolMessage)
        assert "cpu" in messages[2].content.lower()
        assert messages[3].content == "CPU looks fine."

    def test_unknown_tool_name_returns_tool_error(self):
        """When agent calls a tool that doesn't exist, ToolNode returns an error message."""
        step = {"n": 0}

        def fake(self, messages, *a, **kw):
            step["n"] += 1
            if step["n"] == 1:
                return AIMessage(content="", tool_calls=[
                    {"name": "GhostTool", "args": {}, "id": "cx", "type": "tool_call"}
                ])
            return AIMessage(content="I couldn't do that.")

        result = self._run_with_fake_llm(fake, "Do ghost task")
        tool_msg = result["messages"][2]
        assert isinstance(tool_msg, ToolMessage)
        assert "not a valid tool" in tool_msg.content.lower()

    def test_tool_exception_recovered_gracefully(self):
        """When a tool raises, LangGraph catches and returns error ToolMessage; agent recovers."""
        step = {"n": 0}

        def fake(self, messages, *a, **kw):
            step["n"] += 1
            if step["n"] == 1:
                return AIMessage(content="", tool_calls=[
                    {"name": "WebSearch", "args": {"query": "Windows 11"}, "id": "cw", "type": "tool_call"}
                ])
            return AIMessage(content="Search unavailable, please try later.")

        with patch("agent.tools.TavilySearchResults.invoke", side_effect=Exception("Quota exceeded")):
            result = self._run_with_fake_llm(fake, "Search Windows 11")
        final = result["messages"][-1]
        assert final.content == "Search unavailable, please try later."

    def test_launch_app_schema_mismatch_raises_pydantic_error(self):
        """
        Regression test: When ToolNode receives {'app_name': 'notepad'}, Pydantic
        rejects it because AppInput schema requires 'name'.
        """
        step = {"n": 0}

        def fake(self, messages, *a, **kw):
            step["n"] += 1
            if step["n"] == 1:
                return AIMessage(content="", tool_calls=[
                    {"name": "LaunchApp", "args": {"app_name": "notepad"}, "id": "cla", "type": "tool_call"}
                ])
            return AIMessage(content="Handled.")

        result = self._run_with_fake_llm(fake, "Open Notepad")
        tool_msg = result["messages"][2]
        assert isinstance(tool_msg, ToolMessage)
        assert "validation error" in tool_msg.content.lower() or "field required" in tool_msg.content.lower()

    def test_launch_app_with_correct_schema_succeeds(self):
        """Verified FIX: Prompt few-shot uses {'name': 'notepad'} which succeeds without error."""
        step = {"n": 0}

        def fake(self, messages, *a, **kw):
            step["n"] += 1
            if step["n"] == 1:
                return AIMessage(content="", tool_calls=[
                    {"name": "LaunchApp", "args": {"name": "notepad"}, "id": "cla2", "type": "tool_call"}
                ])
            return AIMessage(content="Notepad launched.")

        with patch("agent.tools.launch_app", return_value={"status": "success", "message": "Launched"}):
            result = self._run_with_fake_llm(fake, "Open Notepad")
        tool_msg = result["messages"][2]
        assert isinstance(tool_msg, ToolMessage)
        assert "success" in tool_msg.content.lower()
        assert result["messages"][3].content == "Notepad launched."

    def test_multi_step_system_info_then_explain(self):
        """Multi-step: retrieve system info then explain; both steps should produce sensible output."""
        step = {"n": 0}

        def fake(self, messages, *a, **kw):
            step["n"] += 1
            if step["n"] == 1:
                return AIMessage(content="", tool_calls=[
                    {"name": "SystemInfo", "args": {"requested": ["cpu", "ram"]}, "id": "cms", "type": "tool_call"}
                ])
            # Second call: LLM should have tool output in context
            assert any(isinstance(m, ToolMessage) for m in messages)
            return AIMessage(content="Your system is running at moderate load.")

        result = self._run_with_fake_llm(fake, "Tell me about my system")
        assert result["messages"][-1].content == "Your system is running at moderate load."

    def test_empty_user_input_does_not_crash(self):
        """Agent should handle empty string input without crashing."""
        def fake(self, messages, *a, **kw):
            return AIMessage(content="I didn't get any input.")

        result = self._run_with_fake_llm(fake, "")
        assert isinstance(result["messages"][-1].content, str)

    def test_very_long_user_input(self):
        """Agent should handle very long input without crashing."""
        long_input = "Tell me about " + ("Windows system " * 500)

        def fake(self, messages, *a, **kw):
            return AIMessage(content="That's a lot of text.")

        result = self._run_with_fake_llm(fake, long_input)
        assert isinstance(result["messages"][-1].content, str)

    def test_agent_stops_after_final_message_no_tools(self):
        """Agent should stop (not loop) when LLM returns no tool calls."""
        call_count = {"n": 0}

        def fake(self, messages, *a, **kw):
            call_count["n"] += 1
            return AIMessage(content="Done.")

        result = self._run_with_fake_llm(fake, "Tell me a joke")
        assert call_count["n"] == 1  # LLM called only once

    def test_unsupported_request_no_tool_called(self):
        """Agent should handle requests that don't map to any tool without calling tools."""
        def fake(self, messages, *a, **kw):
            return AIMessage(content="I can't help with that.")

        result = self._run_with_fake_llm(fake, "Make me a cup of coffee")
        # Ensure no ToolMessage in result
        assert not any(isinstance(m, ToolMessage) for m in result["messages"])


# ---------------------------------------------------------------------------
# Prompt and tool registration integrity
# ---------------------------------------------------------------------------
class TestToolRegistration:
    def test_all_expected_tools_present(self):
        from agent.tools import tools
        expected = {
            "LaunchApp", "TakeScreenshot", "ControlSystem",
            "SetBrightness", "SetVolume", "MuteAudio", "UnmuteAudio",
            "SystemInfo", "WebSearch"
        }
        actual = {t.name for t in tools}
        assert expected == actual

    def test_tool_count(self):
        from agent.tools import tools
        assert len(tools) == 9

    def test_system_prompt_contains_tool_names(self):
        from agent.prompt import get_system_prompt
        from agent.tools import tools
        prompt = get_system_prompt(tools)
        for tool in tools:
            assert tool.name in prompt

    def test_system_prompt_contains_security_rules(self):
        from agent.prompt import get_system_prompt
        from agent.tools import tools
        prompt = get_system_prompt(tools)
        assert "SECURITY" in prompt or "NEVER" in prompt

    def test_few_shot_examples_in_prompt(self):
        from agent.prompt import get_system_prompt, FEW_SHOT_EXAMPLES
        from agent.tools import tools
        prompt = get_system_prompt(tools)
        # At least one few-shot input should appear
        for ex in FEW_SHOT_EXAMPLES:
            assert ex["input"] in prompt
