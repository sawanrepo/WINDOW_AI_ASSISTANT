from pydantic import BaseModel, Field
from typing import List

class AppInput(BaseModel):
    name: str = Field(..., description="The name of the application to launch.")

class SystemActionInput(BaseModel):
    action: str = Field(..., description="System action: 'shutdown', 'restart', or 'logoff'")

class StatusInput(BaseModel):
    requested: List[str] = Field(..., description="List of items whose info to be fetched like ['cpu', 'ram', 'battery']")

class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query to perform a web search using Tavily")