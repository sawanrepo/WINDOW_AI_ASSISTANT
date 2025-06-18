from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import add_messages, StateGraph, END
from config.settings import GOOGLE_API_KEY
from .tools import tools
from .prompt import get_system_prompt
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3,
    max_output_tokens=512,
    google_api_key=GOOGLE_API_KEY,
).bind_tools(tools)

# System prompt
system_prompt = get_system_prompt(tools)
system_message = SystemMessage(content=system_prompt)

# Agent node logic
def agent_node(state: AgentState):
    inputs = [system_message] + state["messages"]
    response = llm.invoke(inputs)
    return {"messages": [response]}

# Tool router
def tool_router(state: AgentState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return END

# Define graph
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
tool_node = ToolNode(tools=tools)
graph.add_node("tool_node", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", tool_router)
graph.add_edge("tool_node", "agent")

# Compile graph
winora_agent = graph.compile()