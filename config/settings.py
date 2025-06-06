from dotenv import load_dotenv
import os

load_dotenv()

HF_MODEL_ID = os.getenv("HF_MODEL_ID")
HF_TOKEN = os.getenv("HF_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")