import React, { useState } from "react";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import { Box, Fab, Zoom, useTheme } from "@mui/material";
import { useAppUser } from "../../Context/AppUserContext";
import { tokens } from "../../theme";
import AgentChatBox from "./AgentChatBox";

const AgentWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { appUser } = useAppUser();
  const [convId, setConvId] = useState("GuestConvId");
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  const handleOpenChat = () => {
    setConvId(new Date().toISOString());
    setIsOpen(true);
  };

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
      {/* Drawer-based Chat Box */}
      <AgentChatBox
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        userId={appUser ? appUser.id : "GuestUserId"}
        convId={convId}
      />

      {/* Floating Action Button */}
      <Zoom in={!isOpen}>
        <Fab
          color="primary"
          aria-label="agent"
          onClick={handleOpenChat}
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
