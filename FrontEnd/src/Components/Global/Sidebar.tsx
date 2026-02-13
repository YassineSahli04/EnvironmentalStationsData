import React, { useState } from "react";
import { SignedIn, SignedOut, useUser } from "@clerk/clerk-react";
import BarChartOutlinedIcon from "@mui/icons-material/BarChartOutlined";
import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import ContactsOutlinedIcon from "@mui/icons-material/ContactsOutlined";
import HelpOutlineOutlinedIcon from "@mui/icons-material/HelpOutlineOutlined";
import ListAltOutlinedIcon from "@mui/icons-material/ListAltOutlined";
import MapOutlinedIcon from "@mui/icons-material/MapOutlined";
import MenuOutlinedIcon from "@mui/icons-material/MenuOutlined";
import PeopleAltOutlinedIcon from "@mui/icons-material/PeopleAltOutlined";
import PersonOutlinedIcon from "@mui/icons-material/PersonOutlined";
import PieChartOutlineOutlinedIcon from "@mui/icons-material/PieChartOutlineOutlined";
import ReceiptOutlinedIcon from "@mui/icons-material/ReceiptOutlined";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";
import TimelineOutlinedIcon from "@mui/icons-material/TimelineOutlined";
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
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  const handleClick = () => {
    setSelected(title);
    if (onClickExtra) {
      onClickExtra();
    }
  };

  return (
    <MenuItem
      active={selected === title}
      style={{
        color: colors.grey[100],
      }}
      onClick={handleClick}
      icon={icon}
    >
      <Typography>{title}</Typography>
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
        "& .pro-sidebar-inner": {
          background: `${colors.primary[400]} !important`,
        },
        "& .pro-icon-wrapper": {
          backgroundColor: "transparent !important",
        },
        "& .pro-inner-item": {
          padding: "5px 35px 5px 20px !important",
        },
        "& .pro-inner-item:hover": {
          color: "#868dfb !important",
        },
        "& .pro-menu-item.active": {
          color: "#6870fa !important",
        },
      }}
    >
      <ProSidebar
        collapsed={isCollapsed}
        style={{
          color: colors.grey[100],
          height: "90vh",
          overflowY: "auto",
        }}
      >
        <Menu>
          <MenuItem
            onClick={() => setIsCollapsed(!isCollapsed)}
            icon={isCollapsed ? <MenuOutlinedIcon /> : undefined}
            style={{
              margin: "10px 0 20px 0",
              color: colors.grey[100],
            }}
          >
            {!isCollapsed && (
              <Box display="flex" justifyContent="right" alignItems="center" ml="15px">
                <IconButton onClick={() => setIsCollapsed(!isCollapsed)}>
                  <MenuOutlinedIcon />
                </IconButton>
              </Box>
            )}
          </MenuItem>

          {!isCollapsed && (
            <Box>
              {!isLoaded ? (
                // Skeleton loading state
                <Box mb="25px">
                  <Box display="flex" justifyContent="center" alignItems="center">
                    <Skeleton
                      variant="circular"
                      width={100}
                      height={100}
                      animation="wave"
                      sx={{ bgcolor: colors.primary[300] }}
                    />
                  </Box>
                  <Box textAlign="center" sx={{ mt: "10px" }}>
                    <Skeleton
                      variant="text"
                      width={120}
                      height={32}
                      animation="wave"
                      sx={{ bgcolor: colors.primary[300], mx: "auto" }}
                    />
                    <Skeleton
                      variant="text"
                      width={60}
                      height={20}
                      animation="wave"
                      sx={{ bgcolor: colors.primary[300], mx: "auto", mt: "4px" }}
                    />
                  </Box>
                </Box>
              ) : (
                <Box>
                  <SignedOut>
                    <Box mb="25px">
                      <Box display="flex" justifyContent="center" alignItems="center">
                        <img
                          alt="profile-user"
                          width="100px"
                          height="100px"
                          src={img}
                          style={{ cursor: "pointer", borderRadius: "50%" }}
                        />
                      </Box>
                      <Box textAlign="center">
                        <Typography
                          variant="h2"
                          color={colors.grey[100]}
                          fontWeight="bold"
                          sx={{ m: "10px 0 0 0" }}
                        >
                          Guest
                        </Typography>
                      </Box>
                    </Box>
                  </SignedOut>
                  <SignedIn>
                    <Box mb="25px">
                      <Box display="flex" justifyContent="center" alignItems="center">
                        <img
                          alt="profile-user"
                          width="100px"
                          height="100px"
                          src={user?.hasImage ? user.imageUrl : img}
                          style={{ cursor: "pointer", borderRadius: "50%" }}
                        />
                      </Box>
                      <Box textAlign="center">
                        <Typography
                          variant="h2"
                          color={colors.grey[100]}
                          fontWeight="bold"
                          sx={{ m: "10px 0 0 0" }}
                        >
                          {user ? user.fullName : "Signed User"}
                        </Typography>
                        <Typography variant="h5" color={colors.greenAccent[500]}>
                          {appUser ? appUser.role[0].toUpperCase() + appUser.role.slice(1) : "User"}
                        </Typography>
                      </Box>
                    </Box>
                  </SignedIn>
                </Box>
              )}
            </Box>
          )}

          <Box paddingLeft={isCollapsed ? undefined : "10%"}>
            <Item
              title="Stations Map"
              to="/"
              icon={<MapOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />

            <Typography variant="h6" color={colors.grey[300]} sx={{ m: "15px 0 5px 20px" }}>
              Data
            </Typography>

            <Item
              title="Search Stations"
              icon={<SearchOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(!isFilterPanelOpen)}
            />
            {appUser?.role === "admin" && <Item
              title="Stations List"
              to="/stations"
              icon={<ListAltOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />}

            {appUser?.role === "admin" && <Item
              title="Users Dashboard"
              to="/users"
              icon={<PeopleAltOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />}

            <Item
              title="Contacts Information"
              to="/contacts"
              icon={<ContactsOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />
            <Item
              title="Invoices Balances"
              to="/invoices"
              icon={<ReceiptOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />

            <Typography variant="h6" color={colors.grey[300]} sx={{ m: "15px 0 5px 20px" }}>
              Pages
            </Typography>
            <Item
              title="Profile Form"
              to="/form"
              icon={<PersonOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />
            <Item
              title="Calendar"
              to="/calendar"
              icon={<CalendarTodayOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />
            <Item
              title="FAQ Page"
              to="/faq"
              icon={<HelpOutlineOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />

            <Typography variant="h6" color={colors.grey[300]} sx={{ m: "15px 0 5px 20px" }}>
              Charts
            </Typography>
            <Item
              title="Bar Chart"
              to="/bar"
              icon={<BarChartOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />
            <Item
              title="Pie Chart"
              to="/pie"
              icon={<PieChartOutlineOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />
            <Item
              title="Line Chart"
              to="/line"
              icon={<TimelineOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />
            <Item
              title="Geography Chart"
              to="/geography"
              icon={<MapOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
              onClickExtra={() => setIsFilterPanelOpen(false)}
            />
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

