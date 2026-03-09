import React, { useState, useRef, useEffect } from "react";
import CloseIcon from "@mui/icons-material/Close";
import SendIcon from "@mui/icons-material/Send";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import { Box, IconButton, TextField, Typography, useTheme, Paper } from "@mui/material";
import { tokens } from "../../theme";
import ChatMessage, { type MessageType } from "./ChatMessage";
import { agentChat } from "../../Api/AgentApi";

interface AgentChatBoxProps {
  onClose: () => void;
  userId: string;
  convId: string;
}

const AgentChatBox: React.FC<AgentChatBoxProps> = ({ onClose, userId, convId }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
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
      const agentResponseText = await agentChat(messageText, userId, convId);
      const newAgentMessage: MessageType = {
        id: (Date.now() + 1).toString(),
        sender: "agent",
        text: agentResponseText,
        timestamp: new Date(),
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
