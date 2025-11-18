import { useContext } from "react";
import DarkModeOutlinedIcon from "@mui/icons-material/DarkModeOutlined";
import LightModeOutlinedIcon from "@mui/icons-material/LightModeOutlined";
import NotificationsOutlinedIcon from "@mui/icons-material/NotificationsOutlined";
import PersonOutlinedIcon from "@mui/icons-material/PersonOutlined";
import SearchIcon from "@mui/icons-material/Search";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import { Box, IconButton, useTheme, Typography } from "@mui/material";
import InputBase from "@mui/material/InputBase";
import { ColorModeContext, tokens } from "../../theme";

const Topbar = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const colorMode = useContext(ColorModeContext);

  return (
    <Box
      sx={{
        position: "relative",
        zIndex: 2,
        backgroundColor: colors.primary[400],
        height: "10vh",
      }}
      display="flex"
      justifyContent="space-between"
      alignItems="center"
      p={2}
    >
      {/* LEFT: title + search */}
      <Box display="flex" alignItems="center" gap={2} ml="15px">
        <Typography variant="h3" paddingRight="30px" color={colors.grey[100]}>
          AGRODATA
        </Typography>

        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            backgroundColor: colors.primary[400],
            borderRadius: "3px",
            border: `1px solid ${colors.grey[600]}`,
          }}
        >
          <InputBase sx={{ ml: 2, mr: 1, minWidth: 200 }} placeholder="Search" />
          <IconButton type="button" sx={{ p: 1 }}>
            <SearchIcon />
          </IconButton>
        </Box>
      </Box>

      {/* RIGHT: icons */}
      <Box sx={{ position: "relative", zIndex: 2 }} display="flex">
        <IconButton onClick={colorMode.toggleColorMode}>
          {theme.palette.mode === "dark" ? <DarkModeOutlinedIcon /> : <LightModeOutlinedIcon />}
        </IconButton>
        <IconButton>
          <NotificationsOutlinedIcon />
        </IconButton>
        <IconButton>
          <SettingsOutlinedIcon />
        </IconButton>
        <IconButton>
          <PersonOutlinedIcon />
        </IconButton>
      </Box>
    </Box>
  );
};

export default Topbar;
