import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
  Skeleton,
} from "@mui/material";
import type { StationSummary } from "../../hooks/useStationSummary";

type StationDetailsAccordionProps = {
  station: StationSummary | null;
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
              value={formatCoordinates(
                station.coordinates.latitude,
                station.coordinates.longitude,
                station.coordinates.altitude
              )}
            />
            <DetailRow label="Installation Date" value={formatDate(station.installationDate)} />
            <DetailRow label="Owner / Organization" value={station.owner} />
          </Box>

          {/* Right Column */}
          <Box>
            <DetailRow label="Data Frequency" value={station.dataFrequency} />
            <DetailRow label="Available Sensors" value={station.sensors.join(", ")} />
            <DetailRow label="Notes" value={station.notes} />
          </Box>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}
