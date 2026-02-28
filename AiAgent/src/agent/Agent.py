from langchain_ollama import ChatOllama
from AiAgent.src.agent.Graph import build_graph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
import os

class Agent():
    def __init__(self, isOpenAi = False):
        if isOpenAi :
            key_path = os.getenv("OPENAI_KEY_PATH")
            if not key_path:
                raise RuntimeError("OPENAI_KEY_PATH not set")

            with open(key_path, "r") as f:
                self.openAiKey = f.read().strip()

        if isOpenAi:
            llm = ChatOpenAI(
                model="gpt-4.1-mini",
                api_key=SecretStr(self.openAiKey),
                temperature=0.2
            )
        else:
            llm = ChatOllama(
                model="qwen2.5:7b",
                base_url="http://host.docker.internal:11434",
                temperature=0.2
            )

        self.graph = build_graph(llm)

        config: RunnableConfig = {"configurable": {"thread_id": 'TestId'}}
        self.config = config

    def initializeChat(self):
        print(f"Bot:  Hi, Which station do you want to analyse?")
        while(True):
            userMessage = input("User: ").strip()
            if userMessage.lower() == "exit":
                break

            print("\n--- Agent Steps ---")
            for step in self.graph.stream(
                {"messages": [HumanMessage(content=userMessage)]},
                config=self.config,
                stream_mode="updates",
            ):
                self._print_step(step)
            print("--- End Steps ---\n")

            snapshot = self.graph.get_state(self.config)
            messages = snapshot.values.get("messages", []) if snapshot and snapshot.values else []
            if not messages:
                print("Bot: <no response>")
                continue

            print("Bot: ", self.last_ai_text(messages), sep="")
            print()

    def _print_step(self, step):
        if not isinstance(step, dict):
            return

        for node_name, update in step.items():
            print(f"[step] {node_name}")
            if not isinstance(update, dict):
                continue

            messages = update.get("messages", [])
            if not messages:
                continue

            last = messages[-1]
            content = getattr(last, "content", None)
            if content:
                print(f"  [message] {content}")
            tool_calls = getattr(last, "tool_calls", None) or []
            for call in tool_calls:
                tool_name = call.get("name")
                tool_args = call.get("args")
                print(f"  [tool_call] {tool_name} args={tool_args}")

            if getattr(last, "type", None) == "tool":
                print(f"  [tool_result] {getattr(last, 'name', 'unknown')} -> {last.content}")

    def last_ai_text(self, messages):
        for m in reversed(messages):
            if isinstance(m, AIMessage) and (m.content or ""):
                return m.content
        return "<no assistant text>"




