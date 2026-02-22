from langchain_ollama import ChatOllama
from langchain.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

checkpointer = InMemorySaver()

llm = ChatOllama(
    model="phi3.5",
    base_url="http://100.67.117.80:11434",
    temperature=0.2
    )

agent = create_agent(
    model=llm,
    checkpointer=checkpointer
    )

config: RunnableConfig = {"configurable": {"thread_id": "1"}}

agent.invoke(
    {"messages": [SystemMessage(content="You are a helpful assistant. All your answers will need to be short and concise.")]}
    , config=config
)

while(True):
    userMessage = input("User: ").strip()
    if userMessage.lower() == "exit":
        break

    print("Bot: ", end="", flush=True)
    response = agent.invoke(
            {"messages":[HumanMessage(content=userMessage)]},
            config=config
        )
    print(response["messages"][-1].content, end="", flush=True)  # type: ignore
    print()