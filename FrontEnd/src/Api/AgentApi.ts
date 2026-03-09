const API_URL = import.meta.env.VITE_API_URL;
const url = `${API_URL}/api/agent/chat`;

export async function agentChat() {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: "What are the available stations",
      user_id: "testUser",
      conversation_id: "conv1",
    }),
  });
  if (response && response.body) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      console.log(chunk);
    }
  }
}
