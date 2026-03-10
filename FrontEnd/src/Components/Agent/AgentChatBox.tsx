import React, { useState, useRef, useEffect } from "react";
import CloseIcon from "@mui/icons-material/Close";
import SendIcon from "@mui/icons-material/Send";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import { Box, IconButton, TextField, Typography, useTheme, Paper } from "@mui/material";
import { tokens } from "../../theme";
import ChatMessage, { type MessageFileAttachment, type MessageType } from "./ChatMessage";
import { agentChat, type AgentFilePayload } from "../../Api/AgentApi";

interface AgentChatBoxProps {
  onClose: () => void;
  userId: string;
  convId: string;
}

const AgentChatBox: React.FC<AgentChatBoxProps> = ({ onClose, userId, convId }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const objectUrlsRef = useRef<string[]>([]);
  const [messages, setMessages] = useState<MessageType[]>([
    {
      id: "1",
      sender: "agent",
      text: "Hello! I am your AI assistant. How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    return () => {
      objectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
      objectUrlsRef.current = [];
    };
  }, []);

  const createAttachmentFromPayload = (payload: AgentFilePayload): MessageFileAttachment | null => {
    const name = payload.filename?.trim() || "generated-file.txt";

    if (payload.download_url && payload.download_url.trim()) {
      return { name, href: payload.download_url };
    }

    if (payload.content_base64 && payload.content_base64.trim()) {
      const base64 = payload.content_base64.trim();
      const binary = window.atob(base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i += 1) {
        bytes[i] = binary.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: payload.mime_type || "application/octet-stream" });
      const href = URL.createObjectURL(blob);
      objectUrlsRef.current.push(href);
      return { name, href };
    }

    if (payload.content_text !== undefined) {
      const blob = new Blob([payload.content_text], { type: payload.mime_type || "text/plain" });
      const href = URL.createObjectURL(blob);
      objectUrlsRef.current.push(href);
      return { name, href };
    }

    return null;
  };

  const handleSend = async () => {
    const messageText = inputValue.trim();
    if (messageText === "") return;

    const newUserMessage: MessageType = {
      id: Date.now().toString(),
      sender: "user",
      text: messageText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setInputValue("");

    try {
      const agentResponse = await agentChat(messageText, userId, convId);
      const attachments = agentResponse.files
        .map(createAttachmentFromPayload)
        .filter((file): file is MessageFileAttachment => file !== null);
      const newAgentMessage: MessageType = {
        id: (Date.now() + 1).toString(),
        sender: "agent",
        text: agentResponse.response || (attachments.length > 0 ? " " : ""),
        timestamp: new Date(),
        files: attachments.length > 0 ? attachments : undefined,
      };
      setMessages((prev) => [...prev, newAgentMessage]);
    } catch (error) {
      const fallbackMessage: MessageType = {
        id: (Date.now() + 1).toString(),
        sender: "agent",
        text: "Sorry, I could not reach the assistant right now.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, fallbackMessage]);
      console.error("Agent chat request failed:", error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  return (
    <Paper
      elevation={4}
      sx={{
        width: 350,
        height: 500,
        display: "flex",
        flexDirection: "column",
        borderRadius: "12px",
        overflow: "hidden",
        bgcolor: colors.primary[500],
        border: `1px solid ${colors.primary[400]}`,
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          bgcolor: colors.blueAccent[700],
          color: colors.grey[100],
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <SmartToyOutlinedIcon />
          <Typography variant="h5" fontWeight="bold">
            Data Assistant
          </Typography>
        </Box>
        <IconButton size="small" onClick={onClose} sx={{ color: colors.grey[100] }}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          p: 2,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          bgcolor: theme.palette.mode === "dark" ? colors.primary[600] : "#fcfcfc",
        }}
      >
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box
        sx={{
          p: 2,
          bgcolor: colors.primary[500],
          borderTop: `1px solid ${colors.primary[400]}`,
          display: "flex",
          gap: 1,
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type a message..."
          size="small"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          sx={{
            "& .MuiOutlinedInput-root": {
              borderRadius: "20px",
              bgcolor: colors.primary[400],
            },
          }}
        />
        <IconButton
          color="primary"
          onClick={handleSend}
          sx={{
            bgcolor: colors.blueAccent[700],
            color: colors.grey[100],
            "&:hover": {
              bgcolor: colors.blueAccent[600],
            },
          }}
        >
          <SendIcon fontSize="small" />
        </IconButton>
      </Box>
    </Paper>
  );
};

export default AgentChatBox;
