from langchain.tools import Tool
from langgraph.prebuilt import ToolExecutor
from schema import AppInput, BrightnessInput, VolumeInput, SystemActionInput, StatusInput, WebSearchInput
from core.app_launcher import launch_app
from core.screenshot import take_screenshot_tool
from core.system_control import control_system, set_brightness, set_volume, mute_audio, unmute_audio
from core.system_info import get_system_status
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

def web_search(query: str):
    tavily = TavilySearchAPIWrapper()
    result = tavily.invoke({"query": query})
    return result

tools = [

    Tool(
        name="LaunchApp",
        description="Launch an application by name",
        args_schema=AppInput,
        func=lambda args: launch_app(args.app_name)
    ),

    Tool(
        name="TakeScreenshot",
        description="Take a screenshot and save it",
        func=lambda: take_screenshot_tool()
    ),

    Tool(
        name="ControlSystem",
        description="Control system (shutdown, restart, or logoff)",
        args_schema=SystemActionInput,
        func=lambda args: control_system(args.action) or "Action executed"
    ),

    Tool(
        name="SetBrightness",
        description="Adjust screen brightness",
        args_schema=BrightnessInput,
        func=lambda args: set_brightness(args.mode, args.value)
    ),

    Tool(
        name="SetVolume",
        description="Adjust system volume",
        args_schema=VolumeInput,
        func=lambda args: set_volume(args.mode, args.value)
    ),

    Tool(
        name="MuteAudio",
        description="Mute system audio",
        func=lambda: mute_audio()
    ),

    Tool(
        name="UnmuteAudio",
        description="Unmute system audio",
        func=lambda: unmute_audio()
    ),

    Tool(
        name="SystemInfo",
        description="Get system status like CPU, RAM, and Battery",
        args_schema=StatusInput,
        func=lambda args: get_system_status(args.requested)
    ),

    Tool(
        name="WebSearch",
        description="Perform a web search using Tavily",
        args_schema=WebSearchInput,
        func=lambda args: web_search(args["query"])
    )
]
tool_executor = ToolExecutor(tools=tools, name="AgentToolExecutor")