import React, { useState } from "react";
import { Box, Fab, Zoom, useTheme } from "@mui/material";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import { tokens } from "../../theme";
import AgentChatBox from "./AgentChatBox";

const AgentWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  return (
    <Box
      sx={{
        position: "fixed",
        bottom: 24,
        right: 24,
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
        gap: 2,
      }}
    >
      {/* Chat Box Popup */}
      <Zoom in={isOpen}>
        <Box sx={{ display: isOpen ? "block" : "none" }}>
          <AgentChatBox onClose={() => setIsOpen(false)} />
        </Box>
      </Zoom>

      {/* Floating Action Button */}
      <Zoom in={!isOpen}>
        <Fab
          color="primary"
          aria-label="agent"
          onClick={() => setIsOpen(true)}
          sx={{
            bgcolor: colors.blueAccent[600],
            color: colors.grey[100],
            "&:hover": {
              bgcolor: colors.blueAccent[500],
            },
            width: 60,
            height: 60,
            boxShadow: 3,
            display: isOpen ? "none" : "flex", // Hide FAB completely when open, but use Zoom for transition
          }}
        >
          <SmartToyOutlinedIcon fontSize="large" />
        </Fab>
      </Zoom>
    </Box>
  );
};

export default AgentWidget;
