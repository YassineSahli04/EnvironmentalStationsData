import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SensorsIcon from "@mui/icons-material/Sensors";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
  Skeleton,
  Chip,
  Tooltip,
} from "@mui/material";
import type { StationObj, StationSensorObj } from "../../Api/Objects/StationObj";

type StationDetailsAccordionProps = {
  station: StationObj | null;
  isLoading: boolean;
};

type DetailRowProps = {
  label: string;
  value: string | number | null | undefined;
};

function DetailRow({ label, value }: DetailRowProps) {
  return (
    <Box
      sx={{
        display: "flex",
        py: 1.5,
        borderBottom: "1px solid rgba(255,255,255,0.05)",
        "&:last-child": {
          borderBottom: "none",
        },
      }}
    >
      <Typography
        variant="body2"
        sx={{
          color: "#94a3b8",
          minWidth: 160,
          fontWeight: 500,
        }}
      >
        {label}
      </Typography>
      <Typography
        variant="body2"
        sx={{
          color: "#f1f5f9",
          flex: 1,
        }}
      >
        {value ?? "—"}
      </Typography>
    </Box>
  );
}

function formatCoordinates(lat: number | null, lon: number | null, alt: number | null): string {
  if (lat === null || lon === null) return "—";
  const latStr = `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? "N" : "S"}`;
  const lonStr = `${Math.abs(lon).toFixed(4)}° ${lon >= 0 ? "E" : "W"}`;
  const altStr = alt !== null ? ` (${alt}m)` : "";
  return `${latStr}, ${lonStr}${altStr}`;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

const SENSOR_COLORS = [
  { color: "#f87171", bgColor: "rgba(248, 113, 113, 0.12)" }, // Red
  { color: "#fb923c", bgColor: "rgba(251, 146, 60, 0.12)" }, // Orange
  { color: "#fbbf24", bgColor: "rgba(251, 191, 36, 0.12)" }, // Amber
  { color: "#a3e635", bgColor: "rgba(163, 230, 53, 0.12)" }, // Lime
  { color: "#34d399", bgColor: "rgba(52, 211, 153, 0.12)" }, // Emerald
  { color: "#22d3ee", bgColor: "rgba(34, 211, 238, 0.12)" }, // Cyan
  { color: "#60a5fa", bgColor: "rgba(96, 165, 250, 0.12)" }, // Blue
  { color: "#a78bfa", bgColor: "rgba(167, 139, 250, 0.12)" }, // Violet
  { color: "#f472b6", bgColor: "rgba(244, 114, 182, 0.12)" }, // Pink
  { color: "#e879f9", bgColor: "rgba(232, 121, 249, 0.12)" }, // Fuchsia
  { color: "#38bdf8", bgColor: "rgba(56, 189, 248, 0.12)" }, // Sky
  { color: "#4ade80", bgColor: "rgba(74, 222, 128, 0.12)" }, // Green
];

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

function getSensorColor(sensorName: string): { color: string; bgColor: string } {
  const index = hashString(sensorName.toLowerCase()) % SENSOR_COLORS.length;
  return SENSOR_COLORS[index];
}

function SensorChip({ sensor }: { sensor: StationSensorObj }) {
  const { color, bgColor } = getSensorColor(sensor.sensor);
  const displayName = sensor.sensor
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");

  return (
    <Tooltip
      title={
        <Box sx={{ p: 0.5 }}>
          <Typography variant="caption" sx={{ fontWeight: 600, display: "block" }}>
            {displayName}
          </Typography>
          {sensor.unit && (
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              Unit: {sensor.unit}
            </Typography>
          )}
        </Box>
      }
      arrow
      placement="top"
    >
      <Chip
        label={
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <Box
              sx={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                bgcolor: color,
                flexShrink: 0,
              }}
            />
            <span>{displayName}</span>
            {sensor.unit && (
              <Typography
                component="span"
                sx={{
                  fontSize: "0.65rem",
                  opacity: 0.7,
                  ml: 0.25,
                }}
              >
                ({sensor.unit})
              </Typography>
            )}
          </Box>
        }
        size="small"
        sx={{
          bgcolor: bgColor,
          color: color,
          border: `1px solid ${color}25`,
          fontWeight: 500,
          fontSize: "0.75rem",
          height: "auto",
          py: 0.5,
          "& .MuiChip-label": {
            px: 1.25,
          },
          transition: "all 0.15s ease",
          "&:hover": {
            bgcolor: `${color}20`,
            transform: "translateY(-1px)",
          },
        }}
      />
    </Tooltip>
  );
}

export default function StationDetailsAccordion({
  station,
  isLoading,
}: StationDetailsAccordionProps) {
  if (isLoading) {
    return (
      <Box
        sx={{
          bgcolor: "#1F2A40",
          borderRadius: 2,
          p: 2,
          border: "1px solid rgba(255,255,255,0.05)",
        }}
      >
        <Skeleton variant="text" width={200} height={28} />
      </Box>
    );
  }

  if (!station) {
    return null;
  }

  return (
    <Accordion
      defaultExpanded={false}
      sx={{
        bgcolor: "#1F2A40",
        borderRadius: "8px !important",
        boxShadow: "0 4px 20px rgba(0,0,0,0.25)",
        border: "1px solid rgba(255,255,255,0.05)",
        "&:before": {
          display: "none",
        },
        "&.Mui-expanded": {
          margin: 0,
        },
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon sx={{ color: "#94a3b8" }} />}
        sx={{
          borderRadius: 2,
          "&:hover": {
            bgcolor: "rgba(255,255,255,0.02)",
          },
          "& .MuiAccordionSummary-content": {
            my: 1.5,
          },
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontWeight: 600,
            color: "#f1f5f9",
            fontSize: "1rem",
          }}
        >
          Station Details
        </Typography>
      </AccordionSummary>
      <AccordionDetails
        sx={{
          pt: 0,
          px: 3,
          pb: 2,
        }}
      >
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
            gap: { xs: 0, md: 4 },
          }}
        >
          {/* Left Column */}
          <Box>
            <DetailRow
              label="Coordinates"
              value={formatCoordinates(station.Latitude, station.Longitude, station.Altitude)}
            />
            <DetailRow label="Manufacturer" value={station.Manufacturer} />
          </Box>

          {/* Right Column */}
          <Box>
            <DetailRow label="Station Type" value={station.Type} />
            <DetailRow
              label="Last Mesured Data Point"
              value={formatDate(station.LastDataPointTime)}
            />
          </Box>
        </Box>

        {/* Sensors Section - Full Width */}
        {station.SensorsList && station.SensorsList.length > 0 && (
          <Box sx={{ mt: 2, pt: 2, borderTop: "1px solid rgba(255,255,255,0.05)" }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
              <SensorsIcon sx={{ color: "#64748b", fontSize: 16 }} />
              <Typography
                variant="body2"
                sx={{
                  color: "#94a3b8",
                  fontWeight: 500,
                }}
              >
                Available Sensors
              </Typography>
              <Chip
                label={station.SensorsList.length}
                size="small"
                sx={{
                  height: 20,
                  fontSize: "0.7rem",
                  bgcolor: "rgba(134, 141, 251, 0.15)",
                  color: "#868dfb",
                  fontWeight: 600,
                }}
              />
            </Box>
            <Box
              sx={{
                display: "flex",
                flexWrap: "wrap",
                gap: 1,
              }}
            >
              {station.SensorsList.map((sensor) => (
                <SensorChip key={sensor.sensor} sensor={sensor} />
              ))}
            </Box>
          </Box>
        )}
      </AccordionDetails>
    </Accordion>
  );
}
