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
        <Typography variant="body1">{message.text}</Typography>
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
