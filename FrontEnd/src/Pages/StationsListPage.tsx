import { useMemo, useState } from "react";
import { Box, InputAdornment, TextField, Tooltip, Typography } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import SensorsIcon from "@mui/icons-material/Sensors";
import SensorsOffIcon from "@mui/icons-material/SensorsOff";
import { useNavigate } from "react-router-dom";
import { useAllStations } from "../Api/StationApi";
import { OverlayLoader } from "../Components/Global/OverlayLoader";
import type { StationObj, StationStatus } from "../Api/Objects/StationObj";
import "./StationsListPage.scss";

type StationsListPageProps = {
  isSideBarCollapsed: boolean;
};

export default function StationsListPage({ isSideBarCollapsed }: StationsListPageProps) {
  const { data: stations, isStationLoading } = useAllStations();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");

  const filteredStations = useMemo(() => {
    if (!stations) return [];
    if (!searchQuery.trim()) return stations;

    const query = searchQuery.toLowerCase();
    return stations.filter(
      (station) =>
        station.Name?.toLowerCase().includes(query) ||
        station.Location?.toLowerCase().includes(query) ||
        station.Manufacturer?.toLowerCase().includes(query) ||
        station.Type?.toLowerCase().includes(query)
    );
  }, [stations, searchQuery]);

  const stats = useMemo(() => {
    if (!stations) return { total: 0, online: 0, offline: 0 };
    const online = stations.filter((s) => s.State === "Online").length;
    return { total: stations.length, online, offline: stations.length - online };
  }, [stations]);

  const handleRowClick = (stationId: number) => {
    navigate(`/station/${stationId}`);
  };

  return (
    <Box className="stations-list-page">
      {/* Animated Background */}
      <div className="page-background">
        <div className="grid-overlay" />
        <div className="glow-orb orb-1" />
        <div className="glow-orb orb-2" />
      </div>

      {/* Header Section */}
      <Box className="page-header">
        <Box className="header-content">
          <Typography className="page-title">
            <span className="title-icon">◈</span>
            Environmental Stations
          </Typography>
          <Typography className="page-subtitle">
            Real-time monitoring dashboard for all connected stations
          </Typography>
        </Box>

        {/* Stats Cards */}
        <Box className="stats-container">
          <StatCard label="Total Stations" value={stats.total} variant="total" />
          <StatCard label="Online" value={stats.online} variant="online" />
          <StatCard label="Offline" value={stats.offline} variant="offline" />
        </Box>
      </Box>

      {/* Search Bar */}
      <Box className="search-container">
        <TextField
          fullWidth
          placeholder="Search stations by name, location, manufacturer, or type..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon className="search-icon" />
                </InputAdornment>
              ),
              className: "search-input",
            },
          }}
          className="search-field"
        />
      </Box>

      {/* Table Container */}
      <Box className="table-wrapper">
        <OverlayLoader show={isStationLoading} dim={0.3} blockInteraction={isStationLoading} />

        <Box className="table-container">
          <Box className="stations-table">
            {/* Table Header */}
            <Box className="table-header">
              <Box className="header-cell cell-name">Name</Box>
              <Box className="header-cell cell-location">Location</Box>
              <Box className="header-cell cell-manufacturer">Manufacturer</Box>
              <Box className="header-cell cell-type">Type</Box>
              <Box className="header-cell cell-coords">Latitude</Box>
              <Box className="header-cell cell-coords">Longitude</Box>
              <Box className="header-cell cell-altitude">Altitude</Box>
              <Box className="header-cell cell-state">State</Box>
            </Box>

            {/* Table Body */}
            <Box className="table-body">
              {filteredStations.map((station, index) => (
                <StationRow
                  key={station.Id}
                  station={station}
                  index={index}
                  onClick={() => handleRowClick(station.Id)}
                />
              ))}
            </Box>
          </Box>

          {!isStationLoading && filteredStations.length === 0 && (
            <Box className="empty-state">
              <Typography className="empty-text">No stations found</Typography>
              <Typography className="empty-subtext">
                Try adjusting your search criteria
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
}

// Stat Card Component
type StatCardProps = {
  label: string;
  value: number;
  variant: "total" | "online" | "offline";
};

function StatCard({ label, value, variant }: StatCardProps) {
  return (
    <Box className={`stat-card stat-${variant}`}>
      <Typography className="stat-value">{value}</Typography>
      <Typography className="stat-label">{label}</Typography>
      <div className="stat-glow" />
    </Box>
  );
}

// Station Row Component
type StationRowProps = {
  station: StationObj;
  index: number;
  onClick: () => void;
};

function StationRow({ station, index, onClick }: StationRowProps) {
  return (
    <Box
      className="table-row"
      onClick={onClick}
      style={{ animationDelay: `${index * 30}ms` }}
    >
      <Box className="row-cell cell-name">
        <span className="station-name">{station.Name || "—"}</span>
      </Box>
      <Box className="row-cell cell-location">{station.Location || "—"}</Box>
      <Box className="row-cell cell-manufacturer">
        <ManufacturerBadge manufacturer={station.Manufacturer} />
      </Box>
      <Box className="row-cell cell-type">{station.Type || "—"}</Box>
      <Box className="row-cell cell-coords">
        <CoordValue value={station.Latitude} />
      </Box>
      <Box className="row-cell cell-coords">
        <CoordValue value={station.Longitude} />
      </Box>
      <Box className="row-cell cell-altitude">
        <AltitudeValue value={station.Altitude} />
      </Box>
      <Box className="row-cell cell-state">
        <StatusBadge status={station.State} />
      </Box>
    </Box>
  );
}

// Manufacturer Badge
function ManufacturerBadge({ manufacturer }: { manufacturer: string | null }) {
  if (!manufacturer) return <span className="dim-text">—</span>;

  const colorMap: Record<string, string> = {
    DeltaOHM: "#4cceac",
    Pessl: "#6870fa",
  };

  return (
    <span
      className="manufacturer-badge"
      style={{ "--badge-color": colorMap[manufacturer] || "#a3a3a3" } as React.CSSProperties}
    >
      {manufacturer}
    </span>
  );
}

// Coordinate Value
function CoordValue({ value }: { value: number | null }) {
  if (value === null) return <span className="dim-text">—</span>;
  return <span className="coord-value">{value.toFixed(4)}°</span>;
}

// Altitude Value
function AltitudeValue({ value }: { value: number | null }) {
  if (value === null) return <span className="dim-text">—</span>;
  return <span className="altitude-value">{value.toFixed(0)}m</span>;
}

// Status Badge
function StatusBadge({ status }: { status: StationStatus }) {
  const isOnline = status === "Online";
  return (
    <Tooltip title={isOnline ? "Station is transmitting data" : "No recent data received"}>
      <span className={`status-badge status-${status.toLowerCase()}`}>
        {isOnline ? (
          <SensorsIcon className="status-icon" />
        ) : (
          <SensorsOffIcon className="status-icon" />
        )}
        {status}
      </span>
    </Tooltip>
  );
}


