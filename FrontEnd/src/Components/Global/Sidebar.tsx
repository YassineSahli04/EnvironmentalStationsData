import React, { useState } from "react";
import BarChartOutlinedIcon from "@mui/icons-material/BarChartOutlined";
import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import ContactsOutlinedIcon from "@mui/icons-material/ContactsOutlined";
import HelpOutlineOutlinedIcon from "@mui/icons-material/HelpOutlineOutlined";
import MapOutlinedIcon from "@mui/icons-material/MapOutlined";
import MenuOutlinedIcon from "@mui/icons-material/MenuOutlined";
import PeopleOutlinedIcon from "@mui/icons-material/PeopleOutlined";
import PersonOutlinedIcon from "@mui/icons-material/PersonOutlined";
import PieChartOutlineOutlinedIcon from "@mui/icons-material/PieChartOutlineOutlined";
import ReceiptOutlinedIcon from "@mui/icons-material/ReceiptOutlined";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";
import TimelineOutlinedIcon from "@mui/icons-material/TimelineOutlined";
import {
  Autocomplete,
  Box,
  Button,
  Divider,
  IconButton,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { ProSidebar, Menu, MenuItem } from "react-pro-sidebar";
import "react-pro-sidebar/dist/css/styles.css";
import { Link } from "react-router-dom";
import img from "../../assets/user.png";
import { tokens } from "../../theme";

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
};

type Option = { label: string; value: string };

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, setIsCollapsed }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const [selected, setSelected] = useState<string>("Dashboard");

  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);

  const [selectedFilters, setSelectedFilters] = useState<Option[]>([]);
  const [selectedSensors, setSelectedSensors] = useState<Option[]>([]);

  const filterOptions: Option[] = [
    { label: "Last 24 hours", value: "last_24h" },
    { label: "Last 7 days", value: "last_7d" },
    { label: "Last 30 days", value: "last_30d" },
  ];

  const sensorOptions: Option[] = [
    { label: "Temperature", value: "temperature" },
    { label: "Humidity", value: "humidity" },
    { label: "Wind speed", value: "wind_speed" },
  ];

  const handleViewData = () => {
    console.log("Filters:", selectedFilters);
    console.log("Sensors:", selectedSensors);
    // TODO: call backend / update map
  };

  return (
    <Box
      sx={{
        display: "flex",
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
      {/* LEFT: main sidebar */}
      <ProSidebar
        collapsed={isCollapsed}
        style={{
          height: "90vh",
          overflowY: "auto",
        }}
      >
        <Menu>
          {/* LOGO AND MENU ICON */}
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
                  Ali Sahli
                </Typography>
                <Typography variant="h5" color={colors.greenAccent[500]}>
                  Admin
                </Typography>
              </Box>
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
        <Box
          sx={{
            width: 300,
            backgroundColor: `${colors.primary[700]}`,
            borderRight: `1px solid ${colors.grey[700]}`,
            boxShadow: 4,
            p: 2,
            display: "flex",
            flexDirection: "column",
            gap: 2,
            zIndex: 1,
            height: "90vh",
          }}
        >
          <Typography variant="h6" fontWeight={600}>
            Search Stations
          </Typography>
          <Typography variant="body2" color={colors.grey[200]}>
            Select filters and sensors, then view the data on the map.
          </Typography>

          <Divider sx={{ borderColor: colors.grey[700] }} />

          <Autocomplete
            multiple
            options={filterOptions}
            value={selectedFilters}
            onChange={(_, value) => setSelectedFilters(value)}
            getOptionLabel={(option) => option.label}
            renderInput={(params) => (
              <TextField {...params} label="Filters" placeholder="Select filters" size="small" />
            )}
          />

          <Autocomplete
            multiple
            options={sensorOptions}
            value={selectedSensors}
            onChange={(_, value) => setSelectedSensors(value)}
            getOptionLabel={(option) => option.label}
            renderInput={(params) => (
              <TextField {...params} label="Sensors" placeholder="Select sensors" size="small" />
            )}
          />

          <Box flexGrow={1} />

          <Button variant="contained" fullWidth onClick={handleViewData}>
            View data
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default Sidebar;
