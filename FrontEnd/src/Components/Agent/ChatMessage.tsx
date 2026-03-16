import React from "react";
import { Box, Typography, Avatar } from "@mui/material";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";

export type MessageType = {
  id: string;
  sender: "user" | "agent";
  text: string;
  timestamp: Date;
  files?: MessageFileAttachment[];
};

export type MessageFileAttachment = {
  name: string;
  href: string;
};

interface ChatMessageProps {
  message: MessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === "user";
  const parts = message.text.split(/(https?:\/\/[^\s]+)/g);

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        mb: 3,
      }}
    >
      {!isUser && (
        <Avatar
          sx={{
            mr: 1.5,
            width: 32,
            height: 32,
            bgcolor: "transparent",
            background: "linear-gradient(135deg, #3b82f6, #2563eb)",
            borderRadius: "8px",
            boxShadow: "0 2px 8px 0 rgba(59, 130, 246, 0.3)",
          }}
        >
          <SmartToyOutlinedIcon sx={{ color: "#fff", fontSize: 18 }} />
        </Avatar>
      )}

      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: isUser ? "flex-end" : "flex-start",
          maxWidth: "75%",
        }}
      >
        <Box
          sx={{
            p: 2,
            borderRadius: "16px",
            bgcolor: isUser ? "transparent" : "#1e2633",
            background: isUser ? "linear-gradient(135deg, #2563eb, #1d4ed8)" : undefined,
            color: isUser ? "#fff" : "#f3f4f6",
            border: isUser ? "none" : "1px solid rgba(59, 130, 246, 0.1)",
            boxShadow: isUser ? "0 4px 14px 0 rgba(59, 130, 246, 0.2)" : "none",
          }}
        >
          <Typography
            variant="body2"
            sx={{
              lineHeight: 1.6,
              overflowWrap: "anywhere",
              wordBreak: "break-word",
            }}
          >
            {parts.map((part, index) => {
              const isLink = /^https?:\/\/[^\s]+$/.test(part);
              if (!isLink) return <React.Fragment key={index}>{part}</React.Fragment>;

              return (
                <a
                  key={index}
                  href={part}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: isUser ? "#bfdbfe" : "#60a5fa",
                    textDecoration: "underline",
                  }}
                >
                  {part}
                </a>
              );
            })}
          </Typography>
          {message.files && message.files.length > 0 && (
            <Box sx={{ mt: 1, display: "flex", flexDirection: "column", gap: 0.5 }}>
              {message.files.map((file, index) => (
                <a
                  key={`${file.name}-${index}`}
                  href={file.href}
                  download={file.name}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: isUser ? "#bfdbfe" : "#60a5fa",
                    textDecoration: "underline",
                    fontSize: "0.875rem",
                  }}
                >
                  Download {file.name}
                </a>
              ))}
            </Box>
          )}
        </Box>
        <Typography
          variant="caption"
          sx={{
            mt: 0.5,
            px: 1,
            color: "#6b7280",
            fontSize: "0.7rem",
          }}
        >
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </Typography>
      </Box>
    </Box>
  );
};

export default ChatMessage;
