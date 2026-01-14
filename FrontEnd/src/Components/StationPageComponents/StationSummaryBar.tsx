import AccessTimeIcon from "@mui/icons-material/AccessTime";
import LocationOnIcon from "@mui/icons-material/LocationOn";
import SensorsIcon from "@mui/icons-material/Sensors";
import { Box, Typography, Chip, Select, MenuItem, Skeleton } from "@mui/material";
import type { SelectChangeEvent } from "@mui/material";
import type { StationObj, StationStatus } from "../../Api/Objects/StationObj";

type StationSummaryBarProps = {
  station: StationObj | null;
  isLoading: boolean;
  onStationChange?: (stationId: string) => void;
  availableStations?: { id: string; name: string }[];
};

const statusColors: Record<StationStatus, "success" | "error"> = {
  online: "success",
  offline: "error",
};

const statusLabels: Record<StationStatus, string> = {
  online: "Online",
  offline: "Offline",
};

function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function StationSummaryBar({
  station,
  isLoading,
  onStationChange,
  availableStations = [],
}: StationSummaryBarProps) {
  const handleStationChange = (event: SelectChangeEvent<string>) => {
    onStationChange?.(event.target.value);
  };

  if (isLoading) {
    return (
      <Box
        sx={{
          position: "sticky",
          top: 0,
          zIndex: 2,
          bgcolor: "#1F2A40",
          borderRadius: 2,
          p: 2,
          mb: 2,
          boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
        }}
      >
        <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
          <Skeleton variant="text" width={200} height={32} />
          <Skeleton variant="rounded" width={80} height={24} />
          <Skeleton variant="text" width={150} height={24} />
        </Box>
      </Box>
    );
  }

  if (!station) {
    return null;
  }

  return (
    <Box
      sx={{
        position: "sticky",
        top: 0,
        zIndex: 2,
        bgcolor: "#1F2A40",
        borderRadius: 2,
        p: 2.5,
        mb: 2,
        boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
        border: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            sm: "1fr 1fr",
            md: "2fr 1fr 1fr 1fr auto",
          },
          gap: 2,
          alignItems: "center",
        }}
      >
        {/* Station Name & ID */}
        <Box>
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              color: "#f1f5f9",
              mb: 0.5,
            }}
          >
            {station.Name}
          </Typography>
          <Typography variant="caption" sx={{ color: "#94a3b8", fontFamily: "monospace" }}>
            ID: {station.Id}
          </Typography>
        </Box>

        {/* Status */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Chip
            label={statusLabels[station.Status]}
            color={statusColors[station.Status]}
            size="small"
            sx={{
              fontWeight: 600,
              "& .MuiChip-label": { px: 1.5 },
            }}
          />
        </Box>

        {/* Location */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <LocationOnIcon sx={{ color: "#64748b", fontSize: 18 }} />
          <Typography variant="body2" sx={{ color: "#cbd5e1" }}>
            {station.Location || "—"}
          </Typography>
        </Box>

        {/* Last Data & Sensors */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <AccessTimeIcon sx={{ color: "#64748b", fontSize: 16 }} />
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              {formatTimestamp(station.LastDataPointTime)}
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <SensorsIcon sx={{ color: "#64748b", fontSize: 16 }} />
            <Typography variant="caption" sx={{ color: "#94a3b8" }}>
              {station.SensorList?.length ?? 0} sensors
            </Typography>
          </Box>
        </Box>

        {/* Change Station Dropdown */}
        {availableStations.length > 0 && (
          <Select
            value={station.Id}
            onChange={handleStationChange}
            size="small"
            sx={{
              minWidth: 140,
              bgcolor: "#141b2d",
              color: "#f1f5f9",
              borderRadius: 1,
              "& .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(255,255,255,0.1)",
              },
              "&:hover .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(255,255,255,0.2)",
              },
              "& .MuiSvgIcon-root": {
                color: "#94a3b8",
              },
            }}
          >
            {availableStations.map((s) => (
              <MenuItem key={s.id} value={s.id}>
                {s.name}
              </MenuItem>
            ))}
          </Select>
        )}
      </Box>
    </Box>
  );
}
