import os

from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI

openai_api_key = os.getenv("OPENAI_API_KEY")

model_name = "gpt-4-1106-preview"


def create_llm() -> RunnableSerializable:
    return ChatOpenAI(model_name=model_name, openai_api_key=f"{openai_api_key}")
