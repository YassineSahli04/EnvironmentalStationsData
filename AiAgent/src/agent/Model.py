from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from dataclasses import dataclass
from pydantic import SecretStr
import os

@dataclass
class Model:

    @classmethod
    def build_default_model(cls) -> BaseChatModel:
        use_openai = os.getenv("USE_OPENAI", "true").lower() == "true"

        if use_openai:
            key_path = os.getenv("OPENAI_KEY_PATH")
            if not key_path:
                raise RuntimeError("OPENAI_KEY_PATH not set")

            with open(key_path, "r") as f:
                openai_key = f.read().strip()

            return ChatOpenAI(
                model="gpt-4.1-mini",
                api_key=SecretStr(openai_key),
                temperature=0.2,
            )

        return ChatOllama(
            model="qwen2.5:7b",
            base_url="http://host.docker.internal:11434",
            temperature=0.2,
        )


