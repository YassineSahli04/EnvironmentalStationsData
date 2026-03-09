import React from "react";
import { Box, Typography, useTheme } from "@mui/material";
import { tokens } from "../../theme";

export type MessageType = {
  id: string;
  sender: "user" | "agent";
  text: string;
  timestamp: Date;
};

interface ChatMessageProps {
  message: MessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const isUser = message.sender === "user";
  const parts = message.text.split(/(https?:\/\/[^\s]+)/g);

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        mb: 2,
      }}
    >
      <Box
        sx={{
          maxWidth: "80%",
          p: 1.5,
          borderRadius: 2,
          bgcolor: isUser ? colors.blueAccent[700] : colors.primary[400],
          color: colors.grey[100],
          boxShadow: 1,
        }}
      >
        <Typography
          variant="body1"
          sx={{
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
                  color: colors.blueAccent[200],
                  textDecoration: "underline",
                }}
              >
                {part}
              </a>
            );
          })}
        </Typography>
        <Typography
          variant="caption"
          sx={{
            display: "block",
            mt: 0.5,
            opacity: 0.7,
            textAlign: isUser ? "right" : "left",
          }}
        >
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </Typography>
      </Box>
    </Box>
  );
};

export default ChatMessage;
