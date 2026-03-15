import { useContext } from "react";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/clerk-react";
import DarkModeOutlinedIcon from "@mui/icons-material/DarkModeOutlined";
import LightModeOutlinedIcon from "@mui/icons-material/LightModeOutlined";
import { Box, IconButton, useTheme, Typography, Button } from "@mui/material";
import { ColorModeContext } from "../../theme";

const Topbar = () => {
  const theme = useTheme();
  const colorMode = useContext(ColorModeContext);

  return (
    <Box
      sx={{
        position: "relative",
        background: "#1A222C",
        height: "10vh",
        boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
      }}
      display="flex"
      justifyContent="space-between"
      alignItems="center"
      zIndex={2}
      p={2}
    >
      {/* LEFT: title */}
      <Box display="flex" alignItems="center" ml="30px">
        <Typography variant="h4" fontWeight="bold" sx={{ color: "#E2E8F0", letterSpacing: "1px" }}>
          AGRODATA
        </Typography>
      </Box>

      {/* RIGHT: icons */}
      <Box sx={{ position: "relative" }} display="flex" alignItems="center" gap={1} paddingRight={2}>
        <SignedOut>
          <SignInButton mode="modal">
            <Button
              variant="outlined"
              size="small"
              sx={{
                ml: 1,
                color: "#E2E8F0",
                borderColor: "#333A48",
                textTransform: "none",
                borderRadius: "6px",
                "&:hover": {
                  borderColor: "#E2E8F0",
                  bgcolor: "rgba(255,255,255,0.05)"
                },
              }}
            >
              Sign In
            </Button>
          </SignInButton>
        </SignedOut>
        <SignedIn>
          <Box sx={{ ml: 1, display: "flex", alignItems: "center" }}>
            <UserButton afterSignOutUrl="/" />
          </Box>
        </SignedIn>
      </Box>
    </Box>
  );
};

export default Topbar;
