import React, { useState } from "react";
import { SignedIn, SignedOut, useUser } from "@clerk/clerk-react";
import ListAltOutlinedIcon from "@mui/icons-material/ListAltOutlined";
import MapOutlinedIcon from "@mui/icons-material/MapOutlined";
import MenuOutlinedIcon from "@mui/icons-material/MenuOutlined";
import PeopleAltOutlinedIcon from "@mui/icons-material/PeopleAltOutlined";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";
import { Box, IconButton, Skeleton, Typography, useTheme } from "@mui/material";
import { ProSidebar, Menu, MenuItem } from "react-pro-sidebar";
import "react-pro-sidebar/dist/css/styles.css";
import { Link } from "react-router-dom";
import { useAppUser } from "../../Context/AppUserContext";
import img from "../../assets/user.png";
import { tokens } from "../../theme";
import SearchSidePanel from "./SearchSidePanel";

type ItemProps = {
  title: string;
  to?: string;
  icon: React.ReactNode;
  selected: string;
  setSelected: React.Dispatch<React.SetStateAction<string>>;
  onClickExtra?: () => void;
};

const Item: React.FC<ItemProps> = ({ title, to, icon, selected, setSelected, onClickExtra }) => {

  const handleClick = () => {
    setSelected(title);
    if (onClickExtra) {
      onClickExtra();
    }
  };

  return (
    <MenuItem
      active={selected === title}
      onClick={handleClick}
      icon={icon}
    >
      <Typography sx={{ fontWeight: selected === title ? "600" : "500", fontSize: "15px" }}>{title}</Typography>
      {to && <Link to={to} />}
    </MenuItem>
  );
};

type SidebarProps = {
  isCollapsed: boolean;
  setIsCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
  onStationViewData: (stationId: string) => void;
  onLocationSelected: (center: [number, number] | undefined, radiusKm: number | undefined) => void;
};

const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  setIsCollapsed,
  onStationViewData,
  onLocationSelected,
}) => {
  const { isLoaded, user } = useUser();
  const { appUser } = useAppUser();

  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const [selected, setSelected] = useState<string>("Dashboard");

  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);

  const onViewData = (stationId: string) => {
    setIsFilterPanelOpen(false);
    onStationViewData(stationId);
  };

  return (
    <Box
      sx={{
        position: "relative",
        display: "flex",
        flexShrink: 0,
        width: "fit-content",
        "& .pro-sidebar": {
          borderRight: "none",
        },
        "& .pro-sidebar-inner": {
          background: `#1A222C !important`,
        },
        "& .pro-icon-wrapper": {
          backgroundColor: "transparent !important",
        },
        "& .pro-inner-item": {
          padding: "10px 15px !important",
          margin: "0 15px 5px 15px !important",
          borderRadius: "8px",
          color: "#8A99AF !important",
          transition: "all 0.3s ease",
          display: "flex",
          alignItems: "center",
        },
        "& .pro-sidebar.collapsed .pro-inner-item": {
          margin: "0 10px 5px 10px !important",
          padding: "10px !important",
          justifyContent: "center !important",
        },
        "& .pro-sidebar.collapsed .pro-item-content": {
          flex: "0 !important",
          minWidth: "0 !important",
          width: "0 !important",
        },
        "& .pro-sidebar.collapsed .pro-item-content .MuiTypography-root": {
          display: "none !important",
        },
        "& .pro-sidebar.collapsed .pro-icon-wrapper": {
          marginRight: "0 !important",
        },
        "& .pro-inner-item:hover": {
          backgroundColor: "#333A48 !important",
          color: "#fff !important",
        },
        "& .pro-menu-item.active .pro-inner-item": {
          backgroundColor: "#333A48 !important",
          color: "#fff !important",
        },
        "& .pro-item-content .MuiTypography-root": {
          fontFamily: "'Inter', sans-serif !important",
        }
      }}
    >
      <ProSidebar
        collapsed={isCollapsed}
        style={{
          height: "90vh",
          overflowY: "auto",
        }}
      >
        <Menu>
          <MenuItem
            onClick={() => setIsCollapsed(!isCollapsed)}
            icon={isCollapsed ? <MenuOutlinedIcon sx={{ color: "#8A99AF" }} /> : undefined}
            style={{
              margin: "10px 0 20px 0",
              color: "#8A99AF",
            }}
          >
            {!isCollapsed && (
              <Box display="flex" justifyContent="flex-end" alignItems="center" ml="15px">
                <IconButton onClick={() => setIsCollapsed(!isCollapsed)} sx={{ color: "#8A99AF" }}>
                  <MenuOutlinedIcon />
                </IconButton>
              </Box>
            )}
          </MenuItem>

          <Box sx={{ borderBottom: "1px solid #2E3A47", pb: 2, mb: 2 }}>
            {!isLoaded ? (
              // Skeleton loading state
              <Box px={isCollapsed ? 1 : 3} display="flex" justifyContent={isCollapsed ? "center" : "flex-start"}>
                <Box display="flex" alignItems="center" gap={2}>
                  <Skeleton variant="circular" width={48} height={48} sx={{ bgcolor: "#333A48" }} />
                  {!isCollapsed && (
                    <Box>
                      <Skeleton variant="text" width={100} height={24} sx={{ bgcolor: "#333A48" }} />
                      <Skeleton variant="text" width={60} height={16} sx={{ bgcolor: "#333A48" }} />
                    </Box>
                  )}
                </Box>
              </Box>
            ) : (
              <Box>
                <SignedOut>
                  <Box display="flex" alignItems="center" gap={2} px={isCollapsed ? 1 : 3} justifyContent={isCollapsed ? "center" : "flex-start"}>
                    <img
                      style={{
                        width: 48,
                        height: 48,
                        borderRadius: "50%",
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                        color: "#fff",
                        fontWeight: "bold",
                        fontSize: "20px",
                        flexShrink: 0,
                      }}
                    src={img}
                    />
                    {!isCollapsed && (
                      <Box>
                        <Typography variant="h6" color="#fff" fontWeight="600">
                          Guest
                        </Typography>
                        <Typography variant="body2" sx={{ color: "#10B981" }}>
                          Visitor
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </SignedOut>
                <SignedIn>
                  <Box display="flex" alignItems="center" gap={2} px={isCollapsed ? 1 : 3} justifyContent={isCollapsed ? "center" : "flex-start"}>
                    <Box
                      component="img"
                      alt="profile-user"
                      src={user?.hasImage ? user.imageUrl : img}
                      onError={({ currentTarget }) => {
                        currentTarget.onerror = null; // prevents looping
                        currentTarget.style.display = 'none';
                        (currentTarget.nextElementSibling as HTMLElement).style.display = 'flex';
                      }}
                      sx={{ width: 48, height: 48, borderRadius: "50%", cursor: "pointer", objectFit: "cover", flexShrink: 0, display: user?.hasImage ? 'block' : 'none' }}
                    />
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        bgcolor: "#F25F22",
                        borderRadius: "50%",
                        display: user?.hasImage ? 'none' : 'flex',
                        justifyContent: "center",
                        alignItems: "center",
                        color: "#fff",
                        fontWeight: "bold",
                        fontSize: "22px",
                        flexShrink: 0,
                        cursor: "pointer",
                      }}
                    >
                      {user ? (user.fullName ? user.fullName.charAt(0).toUpperCase() : "U") : "S"}
                    </Box>
                    {!isCollapsed && (
                      <Box>
                        <Typography variant="h6" color="#fff" fontWeight="600">
                          {user ? user.fullName || "User" : "Serveur INAT"}
                        </Typography>
                        <Typography variant="body2" sx={{ color: "#10B981" }}>
                          {appUser ? appUser.role[0].toUpperCase() + appUser.role.slice(1) : "Admin"}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </SignedIn>
              </Box>
            )}
          </Box>

          <Box>
            <Item
              title="Stations Map"
              to="/"
              icon={<MapOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />

            {!isCollapsed && (
              <Typography
                variant="caption"
                sx={{
                  color: "#8A99AF",
                  ml: "30px",
                  fontWeight: "600",
                  display: "block",
                  mt: "15px",
                  mb: "5px",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px"
                }}
              >
                Data
              </Typography>
            )}

            <Item
              title="Search Stations"
              icon={<SearchOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(!isFilterPanelOpen)}
            />
            <Item
              title="Stations List"
              to="/stations"
              icon={<ListAltOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />

            {appUser?.role === "admin" && (
              <Item
                title="Users Dashboard"
                to="/users"
                icon={<PeopleAltOutlinedIcon />}
                selected={selected}
                setSelected={setSelected}
                onClickExtra={() => setIsFilterPanelOpen(false)}
              />
            )}
          </Box>
        </Menu>
      </ProSidebar>

      {isFilterPanelOpen && (
        <SearchSidePanel
          colors={colors}
          onViewData={onViewData}
          onLocationSelected={onLocationSelected}
        />
      )}
    </Box>
  );
};

export default Sidebar;
