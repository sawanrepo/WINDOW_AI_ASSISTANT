from langchain.tools import Tool
from .schema import AppInput, BrightnessInput, VolumeInput, SystemActionInput, StatusInput, WebSearchInput
from core.app_launcher import launch_app
from core.screenshot import take_screenshot_tool
from core.system_control import control_system, set_brightness, set_volume, mute_audio, unmute_audio
from core.system_info import get_system_status
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

# Safe wrapper for web search
def web_search(query: str):
    tavily = TavilySearchAPIWrapper()
    result = tavily.invoke({"query": query})
    return result

# Defensive wrapper to support both list and schema input
def system_info_wrapper(args):
    if isinstance(args, list):
        return get_system_status(args)
    return get_system_status(args.requested)

def launch_app_wrapper(args):
    if isinstance(args, str):  # direct string passed (e.g., "word")
        name = args
    elif isinstance(args, dict):  # {"name": "word"}
        name = args.get("name")
    else:  # Pydantic model
        name = args.name

    return launch_app(name)

def set_volume_wrapper(args):
    if isinstance(args, dict):
        mode = args.get("mode")
        value = args.get("value")
    elif isinstance(args, (list, tuple)):  
        mode, value = args
    elif hasattr(args, "mode") and hasattr(args, "value"): 
        mode = args.mode
        value = args.value
    else:
        return {"status": "error", "message": "Invalid input format for SetVolume tool."}

    return set_volume(mode, value)

def set_brightness_wrapper(args):
    if isinstance(args, dict):
        mode = args.get("mode")
        value = args.get("value")
    elif isinstance(args, (list, tuple)):
        if len(args) == 2:
            mode, value = args
        else:
            return {"status": "error", "message": "Expected 2 arguments for brightness: mode and value."}
    elif hasattr(args, "mode") and hasattr(args, "value"):
        mode = args.mode
        value = args.value
    else:
        return {"status": "error", "message": "Invalid input format for SetBrightness tool."}

    return set_brightness(mode, value)

tools = [
    Tool(
        name="LaunchApp",
        description="Launch an application by name",
        args_schema=AppInput,
        func=launch_app_wrapper,
        return_direct=False
    ),

    Tool(
        name="TakeScreenshot",
        description="Take a screenshot and save it",
        func=lambda _: take_screenshot_tool(),  # ✅ fix: accepts dummy input
        return_direct=False
    ),

    Tool(
        name="ControlSystem",
        description="Control system (shutdown, restart, or logoff)",
        args_schema=SystemActionInput,
        func=lambda args: control_system(args.action) or "Action executed",
        return_direct=False
    ),

    Tool(
        name="SetBrightness",
        description="Adjust screen brightness",
        args_schema=BrightnessInput,
        func=set_brightness_wrapper,  # ✅ fix: handles both dict and Pydantic model
        return_direct=False
    ),

    Tool(
        name="SetVolume",
        description="Adjust system volume",
        args_schema=VolumeInput,
        func=set_volume_wrapper,  # ✅ fix: handles both dict and Pydantic model
        return_direct=False 
    ),

    Tool(
        name="MuteAudio",
        description="Mute system audio",
        func=lambda _: mute_audio(),  # ✅ fix: accepts dummy input
        return_direct=False
    ),

    Tool(
        name="UnmuteAudio",
        description="Unmute system audio",
        func=lambda _: unmute_audio(),  # ✅ fix: accepts dummy input
        return_direct=False
    ),

    Tool(
        name="SystemInfo",
        description="Get system status like CPU, RAM, and Battery",
        args_schema=StatusInput,
        func=system_info_wrapper,  # ✅ fix: handles both list and schema
        return_direct=False
    ),

    Tool(
        name="WebSearch",
        description="Perform a web search using Tavily",
        args_schema=WebSearchInput,
        func=lambda args: web_search(args.query),  # ✅ fix: args.query not args["query"]
        return_direct=False
    )
]