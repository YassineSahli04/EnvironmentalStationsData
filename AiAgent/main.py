from langchain_ollama import ChatOllama

model = ChatOllama(
    model="phi3.5",
    base_url="http://localhost:11434",
    temperature=0.2
)

response = model.invoke("Summarize what a meteorological station measures in 1 sentence.")

print(response)