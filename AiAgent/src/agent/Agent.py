from agent.Graph import build_graph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
import os
import asyncio
from agent.McpTools import init_tool
from agent.Logging import get_logger

logger = get_logger(__name__)

class Agent():
    def __init__(self, isOpenAi = False):
        os.environ["USE_OPENAI"] = str(isOpenAi).lower()
        self.graph = build_graph()

        config: RunnableConfig = {"configurable": {"thread_id": 'TestId'}}
        self.config = config

    async def initializeChat(self):
        try:
            await init_tool()
            logger.info("cli mcp initialization succeeded")
        except Exception as e:
            raise ValueError("cli mcp initialization failed.")
        print(f"Bot:  Hi, Which station do you want to analyse?")
        single_prompt = (os.getenv("AGENT_PROMPT") or "").strip()
        if single_prompt:
            await self._handle_user_message(single_prompt)
            return

        while(True):
            try:
                userMessage = (await asyncio.to_thread(input, "User: ")).strip()
            except EOFError:
                print("Bot: No interactive stdin detected. Set AGENT_PROMPT to run one request or start the container with stdin attached.")
                return

            if not userMessage:
                continue
            if userMessage.lower() == "exit":
                break

            await self._handle_user_message(userMessage)

    async def _handle_user_message(self, userMessage: str):
        print(f"User: {userMessage}")

        print("\n--- Agent Steps ---")
        try:
            async for step in self.graph.astream(
                {"messages": [HumanMessage(content=userMessage)]},
                config=self.config,
                stream_mode="updates",
            ):
                self._print_step(step)
        except Exception:
            logger.exception("cli graph stream failed")
            print("Bot: I hit an internal error while processing your request. Please try again.")
            print("--- End Steps ---\n")
            return
        print("--- End Steps ---\n")

        try:
            snapshot = self.graph.get_state(self.config)
        except Exception:
            logger.exception("cli graph state retrieval failed")
            print("Bot: I hit an internal error while finalizing your response. Please try again.")
            print()
            return

        messages = snapshot.values.get("messages", []) if snapshot and snapshot.values else []
        if not messages:
            print("Bot: <no response>")
            print()
            return

        _, ai_message = Agent.last_ai_text(messages)
        print("Bot: ", ai_message, sep="")
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

    @staticmethod
    def last_ai_text(messages) -> tuple[AIMessage | None, str]:
        for m in reversed(messages):
            if isinstance(m, AIMessage) and (m.content or ""):
                if isinstance(m.content, str):
                    return m, m.content
            if isinstance(m.content, list):
                return m, " ".join(
                    c if isinstance(c, str) else c.get("text", "")
                    for c in m.content
                )
        return None, "<no assistant text>"

if __name__ == "__main__":
    use_openai = os.getenv("USE_OPENAI", "true").lower() == "true"
    agent = Agent(isOpenAi=use_openai)
    asyncio.run(agent.initializeChat())
