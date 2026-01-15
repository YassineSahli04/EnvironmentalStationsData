import { useEffect, useState } from "react";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import DateRangeIcon from "@mui/icons-material/DateRange";
import QueryStatsIcon from "@mui/icons-material/QueryStats";
import TuneIcon from "@mui/icons-material/Tune";
import {
  Box,
  Typography,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  InputAdornment,
  Chip,
  Tooltip,
} from "@mui/material";

type DataQueryCardProps = {
  stationId: string | undefined;
  onDataQueryChange: (startDate: string, endDate: string, aggregationType: string) => void;
};

const aggregationOptions: { label: string; shortLabel: string }[] = [
  { label: "Hourly", shortLabel: "1H" },
  { label: "Daily", shortLabel: "1D" },
  { label: "Weekly", shortLabel: "1W" },
  { label: "Monthly", shortLabel: "1M" },
];

function formatDateLabel(dateStr: string): string {
  if (!dateStr) return "Not set";
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function calculateDaysDifference(start: Date, end: Date): number | null {
  const diffTime = end.getTime() - start.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

export default function DataQueryCard({ stationId, onDataQueryChange }: DataQueryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const sevenDaysAgo = new Date();
  sevenDaysAgo.setHours(0, 0, 0, 0);
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  const [startDate, setStartDate] = useState<Date>(sevenDaysAgo);
  const [endDate, setEndDate] = useState<Date>(new Date());

  const [aggrType, setAggrType] = useState<string>("Hourly");

  const daysDiff = calculateDaysDifference(startDate, endDate);
  const isValidRange = daysDiff !== null && daysDiff > 0;

  const handleAggregationChange = (
    _event: React.MouseEvent<HTMLElement>,
    newValue: string | null
  ) => {
    if (newValue !== null) {
      setAggrType(newValue);
    }
  };
  useEffect(() => {
    if (stationId === undefined) return;
    const start = new Date(
      Date.UTC(startDate.getUTCFullYear(), startDate.getUTCMonth(), startDate.getUTCDate(), 0, 0, 0)
    );
    const end = new Date(
      Date.UTC(endDate.getUTCFullYear(), endDate.getUTCMonth(), endDate.getUTCDate(), 23, 59, 59)
    );
    onDataQueryChange(start.toISOString().split("T")[0], end.toISOString().split("T")[0], aggrType);
  }, [startDate, endDate, aggrType, stationId]);

  return (
    <Box
      sx={{
        bgcolor: "#1F2A40",
        borderRadius: 2,
        p: 2.5,
        mt: 2,
        boxShadow: "0 4px 20px rgba(0,0,0,0.25)",
        border: "1px solid rgba(255,255,255,0.05)",
        transition: "all 0.2s ease",
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: isExpanded ? 2.5 : 0,
          cursor: "pointer",
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 36,
              height: 36,
              borderRadius: 1.5,
              bgcolor: "rgba(104, 112, 250, 0.15)",
            }}
          >
            <QueryStatsIcon sx={{ color: "#868dfb", fontSize: 20 }} />
          </Box>
          <Box>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                color: "#f1f5f9",
                fontSize: "1rem",
              }}
            >
              Data Query Settings
            </Typography>
            <Typography variant="caption" sx={{ color: "#64748b" }}>
              Configure time range and data resolution
            </Typography>
          </Box>
        </Box>

        {/* Summary chips when collapsed */}
        {!isExpanded && (
          <Box sx={{ display: "flex", gap: 1 }}>
            <Chip
              size="small"
              label={`${formatDateLabel(startDate.toISOString().split("T")[0])} - ${formatDateLabel(endDate.toISOString().split("T")[0])}`}
              sx={{
                bgcolor: "rgba(148, 163, 184, 0.1)",
                color: "#94a3b8",
                fontSize: "0.75rem",
              }}
            />
            <Chip
              size="small"
              label={aggregationOptions.find((a) => a.label === aggrType)?.label}
              sx={{
                bgcolor: "rgba(104, 112, 250, 0.15)",
                color: "#868dfb",
                fontSize: "0.75rem",
                fontWeight: 600,
              }}
            />
          </Box>
        )}

        <TuneIcon
          sx={{
            color: "#64748b",
            transform: isExpanded ? "rotate(0deg)" : "rotate(90deg)",
            transition: "transform 0.2s ease",
          }}
        />
      </Box>

      {/* Expandable Content */}
      {isExpanded && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "1fr 1fr auto" },
            gap: 3,
            alignItems: "flex-start",
          }}
        >
          {/* Date Range Section */}
          <Box>
            <Typography
              variant="caption"
              sx={{
                color: "#94a3b8",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                display: "flex",
                alignItems: "center",
                gap: 0.75,
                mb: 1.5,
              }}
            >
              <DateRangeIcon sx={{ fontSize: 14 }} />
              Date Range
            </Typography>

            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <TextField
                type="date"
                label="Start Date"
                value={startDate.toISOString().split("T")[0]}
                onChange={(e) => {
                  const newStart = new Date(e.target.value);
                  setStartDate(newStart);
                }}
                size="small"
                fullWidth
                slotProps={{
                  inputLabel: { shrink: true },
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <CalendarMonthIcon sx={{ color: "#64748b", fontSize: 18 }} />
                      </InputAdornment>
                    ),
                  },
                }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    bgcolor: "#141b2d",
                    borderRadius: 1.5,
                    "& fieldset": {
                      borderColor: "rgba(255,255,255,0.08)",
                    },
                    "&:hover fieldset": {
                      borderColor: "rgba(255,255,255,0.15)",
                    },
                    "&.Mui-focused fieldset": {
                      borderColor: "#868dfb",
                    },
                  },
                  "& .MuiInputLabel-root": {
                    color: "#94a3b8",
                  },
                  "& .MuiInputLabel-root.Mui-focused": {
                    color: "#868dfb",
                  },
                  "& input": {
                    color: "#f1f5f9",
                  },
                  "& input::-webkit-calendar-picker-indicator": {
                    filter: "invert(0.7)",
                    cursor: "pointer",
                  },
                }}
              />

              <TextField
                type="date"
                label="End Date"
                value={endDate.toISOString().split("T")[0]}
                onChange={(e) => {
                  const newEnd = new Date(e.target.value);
                  setEndDate(newEnd);
                }}
                size="small"
                fullWidth
                slotProps={{
                  inputLabel: { shrink: true },
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <CalendarMonthIcon sx={{ color: "#64748b", fontSize: 18 }} />
                      </InputAdornment>
                    ),
                  },
                }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    bgcolor: "#141b2d",
                    borderRadius: 1.5,
                    "& fieldset": {
                      borderColor: "rgba(255,255,255,0.08)",
                    },
                    "&:hover fieldset": {
                      borderColor: "rgba(255,255,255,0.15)",
                    },
                    "&.Mui-focused fieldset": {
                      borderColor: "#868dfb",
                    },
                  },
                  "& .MuiInputLabel-root": {
                    color: "#94a3b8",
                  },
                  "& .MuiInputLabel-root.Mui-focused": {
                    color: "#868dfb",
                  },
                  "& input": {
                    color: "#f1f5f9",
                  },
                  "& input::-webkit-calendar-picker-indicator": {
                    filter: "invert(0.7)",
                    cursor: "pointer",
                  },
                }}
              />
            </Box>

            {/* Date range indicator */}
            {daysDiff === null ? null : isValidRange ? (
              <Box
                sx={{
                  mt: 1.5,
                  p: 1,
                  borderRadius: 1,
                  bgcolor: "rgba(76, 206, 172, 0.08)",
                  border: "1px solid rgba(76, 206, 172, 0.2)",
                }}
              >
                <Typography variant="caption" sx={{ color: "#4cceac", fontWeight: 500 }}>
                  {daysDiff} day{daysDiff !== 1 ? "s" : ""} selected
                </Typography>
              </Box>
            ) : (
              <Box
                sx={{
                  mt: 1.5,
                  p: 1,
                  borderRadius: 1,
                  bgcolor: "rgba(219, 79, 74, 0.08)",
                  border: "1px solid rgba(219, 79, 74, 0.2)",
                }}
              >
                <Typography variant="caption" sx={{ color: "#db4f4a", fontWeight: 500 }}>
                  End date must be after start date
                </Typography>
              </Box>
            )}
          </Box>

          {/* Aggregation Type Section */}
          <Box>
            <Typography
              variant="caption"
              sx={{
                color: "#94a3b8",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                display: "flex",
                alignItems: "center",
                gap: 0.75,
                mb: 1.5,
              }}
            >
              <TuneIcon sx={{ fontSize: 14 }} />
              Aggregation
            </Typography>

            <ToggleButtonGroup
              value={aggrType}
              exclusive
              onChange={handleAggregationChange}
              aria-label="data aggregation type"
              sx={{
                display: "flex",
                flexWrap: "wrap",
                gap: 1,
                "& .MuiToggleButtonGroup-grouped": {
                  border: "1px solid rgba(255,255,255,0.08) !important",
                  borderRadius: "8px !important",
                  m: 0,
                },
              }}
            >
              {aggregationOptions.map((option) => (
                <Tooltip key={option.label} title={option.label} arrow placement="top">
                  <ToggleButton
                    value={option.label}
                    sx={{
                      px: 2.5,
                      py: 1.5,
                      bgcolor: "#141b2d",
                      color: "#94a3b8",
                      textTransform: "none",
                      fontWeight: 500,
                      minWidth: 70,
                      transition: "all 0.15s ease",
                      "&:hover": {
                        bgcolor: "rgba(134, 141, 251, 0.08)",
                        borderColor: "rgba(134, 141, 251, 0.3) !important",
                      },
                      "&.Mui-selected": {
                        bgcolor: "rgba(134, 141, 251, 0.15)",
                        color: "#868dfb",
                        borderColor: "#868dfb !important",
                        fontWeight: 600,
                        "&:hover": {
                          bgcolor: "rgba(134, 141, 251, 0.2)",
                        },
                      },
                    }}
                  >
                    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                      <Typography variant="body2" sx={{ fontWeight: "inherit" }}>
                        {option.shortLabel}
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          fontSize: "0.65rem",
                          opacity: 0.7,
                          mt: 0.25,
                        }}
                      >
                        {option.label}
                      </Typography>
                    </Box>
                  </ToggleButton>
                </Tooltip>
              ))}
            </ToggleButtonGroup>

            {/* Aggregation description */}
            <Box
              sx={{
                mt: 2,
                p: 1.5,
                borderRadius: 1,
                bgcolor: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.05)",
              }}
            >
              <Typography variant="caption" sx={{ color: "#64748b", lineHeight: 1.5 }}>
                {aggrType === "Hourly" && "Data points averaged per hour for detailed analysis."}
                {aggrType === "Daily" && "Data points averaged per day for daily trends."}
                {aggrType === "Weekly" && "Data points averaged per week for weekly patterns."}
                {aggrType === "Monthly" && "Data points averaged per month for long-term analysis."}
              </Typography>
            </Box>
          </Box>

          {/* Quick Presets */}
          <Box sx={{ display: { xs: "none", lg: "block" } }}>
            <Typography
              variant="caption"
              sx={{
                color: "#94a3b8",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                mb: 1.5,
                display: "block",
              }}
            >
              Quick Presets
            </Typography>

            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              {[
                { label: "Last 7 days", days: 7 },
                { label: "Last 30 days", days: 30 },
                { label: "Last 90 days", days: 90 },
                { label: "Last year", days: 365 },
              ].map((preset) => (
                <Chip
                  key={preset.label}
                  label={preset.label}
                  size="small"
                  onClick={() => {
                    const end = new Date();
                    const start = new Date();
                    start.setDate(end.getDate() - preset.days);
                    setStartDate(start);
                    setEndDate(end);
                  }}
                  sx={{
                    bgcolor: "rgba(255,255,255,0.03)",
                    color: "#94a3b8",
                    border: "1px solid rgba(255,255,255,0.08)",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                    "&:hover": {
                      bgcolor: "rgba(134, 141, 251, 0.1)",
                      borderColor: "rgba(134, 141, 251, 0.3)",
                      color: "#a4a9fc",
                    },
                  }}
                />
              ))}
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
}
