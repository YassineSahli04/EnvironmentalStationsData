import { useEffect, useState, useMemo } from "react";
import AirOutlinedIcon from "@mui/icons-material/AirOutlined";
import KeyboardDoubleArrowLeftIcon from "@mui/icons-material/KeyboardDoubleArrowLeft";
import KeyboardDoubleArrowRightIcon from "@mui/icons-material/KeyboardDoubleArrowRight";
import OpacityOutlinedIcon from "@mui/icons-material/OpacityOutlined";
import ThermostatOutlinedIcon from "@mui/icons-material/ThermostatOutlined";
import WaterDropOutlinedIcon from "@mui/icons-material/WaterDropOutlined";
import WbSunnyOutlinedIcon from "@mui/icons-material/WbSunnyOutlined";
import {
  Box,
  IconButton,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  List,
  Paper,
  Typography,
  Divider,
  useTheme,
} from "@mui/material";
import { WeatherParam } from "../Api/StationApi.ts";
import { tokens } from "../theme";

const OPTIONS = {
  COMMON: ["Avg.", "Min.", "Max."],
  SUM: ["Sum"],
} as const;

type MapParamPanelProps = {
  onSelectedParamChange: (
    param: WeatherParam | undefined,
    dataOption: string | undefined,
    date: Date
  ) => void;
};

export default function MapParamPanel({ onSelectedParamChange }: MapParamPanelProps) {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  const [selectedParam, setSelectedParam] = useState<WeatherParam>();
  const [selectedOption, setSelectedOption] = useState<string>();

  const [date, setDate] = useState<Date>(new Date());

  const options = useMemo(() => {
    if (!selectedParam) return [];

    let base: string[] = [];
    switch (selectedParam) {
      case WeatherParam.TEMPERATURE:
      case WeatherParam.RELATIVE_HUMIDITY:
      case WeatherParam.WIND_SPEED:
        base = [...OPTIONS.COMMON];
        break;

      case WeatherParam.SOLAR_RADIATION:
      case WeatherParam.PRECIPITATION:
        base = [...OPTIONS.SUM];
        break;
    }

    const now = new Date();
    if (isDateEqual(now, date) && !base.includes("Last Measured")) {
      base.push("Last Measured");
    }

    return base;
  }, [selectedParam, date]);

  useEffect(() => {
    if (options.length) setSelectedOption(options[0]);
  }, [options]);

  useEffect(() => {
    if (!selectedParam || !selectedOption) return;

    const handler = setTimeout(() => {
      onSelectedParamChange(selectedParam, selectedOption.replace(/\.$/, "").toLowerCase(), date);
    }, 500);
    return () => clearTimeout(handler);
  }, [selectedParam, selectedOption, date]);

  const onSwitchDateButtonClicked = (buttonType: string) => {
    switch (buttonType) {
      case "nextDate":
        const nextDate = new Date(date);
        nextDate.setDate(date.getDate() + 1);
        setDate(nextDate);
        break;
      case "previousDate":
        const prevDate = new Date(date);
        prevDate.setDate(date.getDate() - 1);
        setDate(prevDate);
        break;
    }
  };
  const today = new Date();
  const isNextDateDisabled = isDateEqual(today, date);

  return (
    <Box
      sx={{
        position: "absolute",
        top: "10%",
        right: "3%",
        zIndex: 2,
        display: "flex",
        flexDirection: "column",
        gap: 1.5,
      }}
    >
      <Paper
        elevation={3}
        sx={{
          borderRadius: "12px",
          minWidth: 250,
          overflow: "hidden",
          backgroundColor: colors.primary[400],
          border: `1px solid ${colors.grey[700]}`,
        }}
      >
        {/* Date Navigation */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            px: 1,
            py: 1,
          }}
        >
          <IconButton
            disabled={!selectedParam}
            onClick={() => onSwitchDateButtonClicked("previousDate")}
            size="small"
            sx={{
              color: colors.grey[100],
              "&:hover": { backgroundColor: "rgba(66, 133, 244, 0.08)" },
              "&.Mui-disabled": {
                color: colors.grey[200],
                opacity: 0.4,
                cursor: "not-allowed",
                pointerEvents: "auto",
              },
            }}
          >
            <KeyboardDoubleArrowLeftIcon fontSize="small" style={{ marginLeft: "15px" }} />
          </IconButton>
          <Typography
            sx={{
              fontSize: 14,
              fontWeight: 500,
              color: colors.primary[100],
            }}
          >
            {date.toLocaleDateString("en-US")}
          </Typography>
          <IconButton
            disabled={isNextDateDisabled}
            onClick={() => onSwitchDateButtonClicked("nextDate")}
            size="small"
            sx={{
              color: colors.grey[100],
              "&:hover": { backgroundColor: "rgba(66, 133, 244, 0.08)" },
              "&.Mui-disabled": {
                color: colors.grey[200],
                opacity: 0.4,
                cursor: "not-allowed",
                pointerEvents: "auto",
              },
            }}
          >
            <KeyboardDoubleArrowRightIcon fontSize="small" style={{ marginRight: "15px" }} />
          </IconButton>
        </Box>
        <Divider />
        <Typography
          sx={{
            px: 2,
            py: 1.5,
            fontSize: 12,
            fontWeight: 500,
            color: colors.primary[100],
            textTransform: "uppercase",
            letterSpacing: 0.5,
          }}
        >
          Weather Data
        </Typography>
        <Divider />
        <List sx={{ py: 1, px: 1 }}>
          <ListItemButton
            selected={selectedParam === WeatherParam.TEMPERATURE}
            onClick={() => setSelectedParam(WeatherParam.TEMPERATURE)}
            sx={{
              borderRadius: "8px",
              py: 1,
              px: 2,
              "&.Mui-selected": {
                backgroundColor: "rgba(66, 133, 244, 0.12)",
                color: "#1a73e8",
                "& .MuiListItemIcon-root": { color: "#1a73e8" },
              },
              "&:hover": { backgroundColor: "rgba(66, 133, 244, 0.08)" },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36, color: colors.primary[100] }}>
              <ThermostatOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary={WeatherParam.TEMPERATURE}
              primaryTypographyProps={{ fontSize: 14 }}
            />
          </ListItemButton>
          <ListItemButton
            selected={selectedParam === WeatherParam.PRECIPITATION}
            onClick={() => setSelectedParam(WeatherParam.PRECIPITATION)}
            sx={{
              borderRadius: "8px",
              py: 1,
              px: 2,
              "&.Mui-selected": {
                backgroundColor: "rgba(66, 133, 244, 0.12)",
                color: "#1a73e8",
                "& .MuiListItemIcon-root": { color: "#1a73e8" },
              },
              "&:hover": { backgroundColor: "rgba(66, 133, 244, 0.08)" },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36, color: colors.primary[100] }}>
              <WaterDropOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary={WeatherParam.PRECIPITATION}
              primaryTypographyProps={{ fontSize: 14 }}
            />
          </ListItemButton>
          <ListItemButton
            selected={selectedParam === WeatherParam.RELATIVE_HUMIDITY}
            onClick={() => setSelectedParam(WeatherParam.RELATIVE_HUMIDITY)}
            sx={{
              borderRadius: "8px",
              py: 1,
              px: 2,
              "&.Mui-selected": {
                backgroundColor: "rgba(66, 133, 244, 0.12)",
                color: "#1a73e8",
                "& .MuiListItemIcon-root": { color: "#1a73e8" },
              },
              "&:hover": { backgroundColor: "rgba(66, 133, 244, 0.08)" },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36, color: colors.primary[100] }}>
              <OpacityOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary={WeatherParam.RELATIVE_HUMIDITY}
              primaryTypographyProps={{ fontSize: 14 }}
            />
          </ListItemButton>
          <ListItemButton
            selected={selectedParam === WeatherParam.SOLAR_RADIATION}
            onClick={() => setSelectedParam(WeatherParam.SOLAR_RADIATION)}
            sx={{
              borderRadius: "8px",
              py: 1,
              px: 2,
              "&.Mui-selected": {
                backgroundColor: "rgba(66, 133, 244, 0.12)",
                color: "#1a73e8",
                "& .MuiListItemIcon-root": { color: "#1a73e8" },
              },
              "&:hover": { backgroundColor: "rgba(66, 133, 244, 0.08)" },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36, color: colors.primary[100] }}>
              <WbSunnyOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary={WeatherParam.SOLAR_RADIATION}
              primaryTypographyProps={{ fontSize: 14 }}
            />
          </ListItemButton>
          <ListItemButton
            selected={selectedParam === WeatherParam.WIND_SPEED}
            onClick={() => setSelectedParam(WeatherParam.WIND_SPEED)}
            sx={{
              borderRadius: "8px",
              py: 1,
              px: 2,
              "&.Mui-selected": {
                backgroundColor: "rgba(66, 133, 244, 0.12)",
                color: "#1a73e8",
                "& .MuiListItemIcon-root": { color: "#1a73e8" },
              },
              "&:hover": { backgroundColor: "rgba(66, 133, 244, 0.08)" },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36, color: colors.primary[100] }}>
              <AirOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary={WeatherParam.WIND_SPEED}
              primaryTypographyProps={{ fontSize: 14 }}
            />
          </ListItemButton>
        </List>
      </Paper>

      {options.length === 0 || (
        <Paper
          elevation={3}
          sx={{
            borderRadius: "12px",
            minWidth: 250,
            overflow: "hidden",
            backgroundColor: colors.primary[400],
            border: `1px solid ${colors.grey[700]}`,
          }}
        >
          <List sx={{ py: 1, px: 1 }}>
            {options.map((option) => {
              return (
                <ListItemButton
                  key={`${selectedParam ?? "param"}-${option}`}
                  selected={selectedOption === option}
                  onClick={() => setSelectedOption(option)}
                  sx={{
                    borderRadius: "8px",
                    py: 0.25,
                    px: 2,
                    "&.Mui-selected": {
                      backgroundColor: "rgba(66, 133, 244, 0.12)",
                      color: "#1a73e8",
                      "& .MuiListItemIcon-root": { color: "#1a73e8" },
                    },
                    "&:hover": { backgroundColor: "rgba(66, 133, 244, 0.08)" },
                  }}
                >
                  <ListItemText primary={option} primaryTypographyProps={{ fontSize: 14 }} />
                </ListItemButton>
              );
            })}
          </List>
        </Paper>
      )}
    </Box>
  );
}

function isDateEqual(d1: Date, d2: Date) {
  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
  );
}

