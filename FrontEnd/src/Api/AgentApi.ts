const API_URL = import.meta.env.VITE_API_URL;
const url = `${API_URL}/api/agent/chat`;

export type AgentFilePayload = {
  filename?: string;
  mime_type?: string;
  content_base64?: string;
  content_text?: string;
  download_url?: string;
};

export type AgentChatResponse = {
  response: string;
  files: AgentFilePayload[];
};

export async function agentChat(message: string, userId: string, convId: string) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      user_id: userId,
      conv_id: convId,
    }),
  });
  if (!response.ok) {
    throw new Error(`Agent request failed with status ${response.status}`);
  }

  const data = (await response.json()) as {
    response?: unknown;
    file?: unknown;
  };

  const normalizedFiles: AgentFilePayload[] = [];

  if (data.file && typeof data.file === "object") {
    normalizedFiles.push(data.file as AgentFilePayload);
  }

  return {
    response: typeof data.response === "string" ? data.response : "",
    files: normalizedFiles,
  } satisfies AgentChatResponse;
}
