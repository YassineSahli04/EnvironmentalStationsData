import React, { useState, useRef, useEffect } from "react";
import CloseIcon from "@mui/icons-material/Close";
import SendIcon from "@mui/icons-material/Send";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import { Box, IconButton, TextField, Typography, Drawer, Avatar, Badge, styled } from "@mui/material";
import ChatMessage, { type MessageFileAttachment, type MessageType } from "./ChatMessage";
import { agentChat, type AgentFilePayload } from "../../Api/AgentApi";

interface AgentChatBoxProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  convId: string;
}

const StyledBadge = styled(Badge)(() => ({
  "& .MuiBadge-badge": {
    backgroundColor: "#4ade80",
    color: "#4ade80",
    boxShadow: `0 0 0 2px #0f1419`,
    "&::after": {
      position: "absolute",
      top: 0,
      left: 0,
      width: "100%",
      height: "100%",
      borderRadius: "50%",
      animation: "ripple 1.2s infinite ease-in-out",
      border: "1px solid currentColor",
      content: '""',
    },
  },
  "@keyframes ripple": {
    "0%": { transform: "scale(.8)", opacity: 1 },
    "100%": { transform: "scale(2.4)", opacity: 0 },
  },
}));

const AgentChatBox: React.FC<AgentChatBoxProps> = ({ isOpen, onClose, userId, convId }) => {
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
    <Drawer
      anchor="right"
      open={isOpen}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: "100%", sm: 480 },
          background: "linear-gradient(to bottom, #0f1419, #1a1f2e)",
          borderLeft: "1px solid rgba(59, 130, 246, 0.2)",
          display: "flex",
          flexDirection: "column",
          boxShadow: 24,
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          position: "relative",
          px: 3,
          py: 2.5,
          borderBottom: "1px solid rgba(59, 130, 246, 0.2)",
          background: "linear-gradient(to right, rgba(37, 99, 235, 0.1), rgba(59, 130, 246, 0.05))",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <StyledBadge
            overlap="circular"
            anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
            variant="dot"
          >
            <Avatar
              sx={{
                bgcolor: "transparent",
                background: "linear-gradient(135deg, #3b82f6, #2563eb)",
                boxShadow: "0 4px 14px 0 rgba(59, 130, 246, 0.39)",
                width: 44,
                height: 44,
                borderRadius: "12px",
              }}
            >
              <SmartToyOutlinedIcon sx={{ color: "#fff" }} />
            </Avatar>
          </StyledBadge>
          <Box>
            <Typography variant="h6" fontWeight="600" color="#fff">
              Data Assistant
            </Typography>
            <Typography
              variant="caption"
              sx={{ color: "rgba(147, 197, 253, 0.7)", display: "flex", alignItems: "center", gap: 0.5 }}
            >
              <Box component="span" sx={{ width: 6, height: 6, borderRadius: "50%", bgcolor: "#4ade80" }} />
              Online
            </Typography>
          </Box>
        </Box>
        <IconButton
          onClick={onClose}
          sx={{
            color: "#9ca3af",
            transition: "all 0.2s",
            "&:hover": { color: "#fff", bgcolor: "rgba(255,255,255,0.1)" },
          }}
        >
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          px: 3,
          py: 3,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
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
          p: 3,
          borderTop: "1px solid rgba(59, 130, 246, 0.2)",
          background: "linear-gradient(to top, #0f1419, transparent)",
          display: "flex",
          gap: 1.5,
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          sx={{
            "& .MuiOutlinedInput-root": {
              borderRadius: "16px",
              bgcolor: "#1e2633",
              color: "#fff",
              border: "1px solid rgba(59, 130, 246, 0.1)",
              "& fieldset": { border: "none" },
              "&:hover fieldset": { border: "none" },
              "&.Mui-focused fieldset": {
                border: "2px solid rgba(59, 130, 246, 0.5)",
              },
            },
            "& .MuiOutlinedInput-input::placeholder": {
              color: "#6b7280",
              opacity: 1,
            },
          }}
        />
        <IconButton
          onClick={handleSend}
          disabled={!inputValue.trim()}
          sx={{
            width: 56,
            height: 56,
            mx: "0 !important",
            borderRadius: "16px",
            background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
            color: "#fff",
            boxShadow: "0 4px 14px 0 rgba(59, 130, 246, 0.2)",
            transition: "all 0.2s",
            "&:hover": {
              background: "linear-gradient(135deg, #3b82f6, #2563eb)",
              boxShadow: "0 6px 20px 0 rgba(59, 130, 246, 0.3)",
            },
            "&.Mui-disabled": {
              background: "linear-gradient(135deg, #374151, #1f2937)",
              color: "#9ca3af",
              boxShadow: "none",
            },
          }}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Drawer>
  );
};

export default AgentChatBox;
