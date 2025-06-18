from langchain.tools import Tool, StructuredTool
from .schema import AppInput, StatusInput, SystemActionInput, WebSearchInput
from core.app_launcher import launch_app
from core.screenshot import take_screenshot_tool
from core.system_control import (
    control_system,
    set_brightness,
    set_volume,
    mute_audio,
    unmute_audio
)
from core.system_info import get_system_status
from langchain_community.tools.tavily_search import TavilySearchResults

def web_search(query: str):
    return TavilySearchResults().invoke({"query": query})

# System info wrapper to support list and schema
def system_info_wrapper(args):
    if isinstance(args, list):
        return get_system_status(args)
    return get_system_status(args.requested)

# App launcher wrapper
def launch_app_wrapper(args):
    if isinstance(args, str):
        name = args
    elif isinstance(args, dict):
        name = args.get("name")
    else:
        name = args.name
    return launch_app(name)

def safe_web_search_wrapper(args):
    if hasattr(args, "query"):
        return web_search(args.query)
    elif isinstance(args, dict):
        return web_search(args.get("query"))
    return web_search(args)

def control_system_wrapper(args):
    try:
        # Handles Pydantic model
        if hasattr(args, "action"):
            return control_system(args.action)

        # Handles dict format
        if isinstance(args, dict) and "action" in args:
            return control_system(args["action"])

        # Handles direct string fallback
        if isinstance(args, str):
            return control_system(args)

        return {"status": "error", "message": "Invalid input for control system."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to execute system command: {e}"}

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
        func=lambda _: take_screenshot_tool(),
        return_direct=False
    ),

    Tool(
        name="ControlSystem",
        description="Control system (shutdown, restart, or logoff), if u dont get anything return from this tool then it has been excuted successfully",
        args_schema=SystemActionInput,
        func=control_system_wrapper,
        return_direct=False
    ),

    StructuredTool.from_function(
        set_brightness,
        name="SetBrightness",
        description="Set, increase, or decrease screen brightness",
        return_direct=False
    ),

    StructuredTool.from_function(
        set_volume,
        name="SetVolume",
        description="Set, increase, or decrease system volume",
        return_direct=False
    ),

    Tool(
        name="MuteAudio",
        description="Mute system audio",
        func=lambda _: mute_audio(),
        return_direct=False
    ),

    Tool(
        name="UnmuteAudio",
        description="Unmute system audio",
        func=lambda _: unmute_audio(),
        return_direct=False
    ),

    Tool(
        name="SystemInfo",
        description="Get system status like CPU, RAM, and Battery",
        args_schema=StatusInput,
        func=system_info_wrapper,
        return_direct=False
    ),

    Tool(
        name="WebSearch",
        description="Perform a web search using Tavily",
        args_schema=WebSearchInput,
        func=safe_web_search_wrapper,
        return_direct=False
    )
] 