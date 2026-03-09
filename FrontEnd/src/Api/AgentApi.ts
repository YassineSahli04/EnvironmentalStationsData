const API_URL = import.meta.env.VITE_API_URL;
const url = `${API_URL}/api/agent/chat`;

export async function agentChat() {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: "What are the available stations",
      user_id: "testUser",
      conv_id: "conv1",
    }),
  });
  if (!response.ok) {
    throw new Error(`Agent request failed with status ${response.status}`);
  }

  const data = (await response.json()) as { response?: string };
  return data.response ?? "";
}
