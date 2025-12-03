import { useEffect, useState } from "react";
import AirOutlinedIcon from "@mui/icons-material/AirOutlined";
import OpacityOutlinedIcon from "@mui/icons-material/OpacityOutlined";
import ThermostatOutlinedIcon from "@mui/icons-material/ThermostatOutlined";
import WaterDropOutlinedIcon from "@mui/icons-material/WaterDropOutlined";
import WbSunnyOutlinedIcon from "@mui/icons-material/WbSunnyOutlined";
import {
  Box,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  List,
  Paper,
  Typography,
  Divider,
  useTheme,
} from "@mui/material";
import { tokens } from "../theme";

export enum WeatherParam {
  TEMPERATURE = "Temperature",
  PRECIPITATION = "Precipitation",
  RELATIVE_HUMIDITY = "Relative Humidity",
  SOLAR_RADIATION = "Solar Radiation",
  WIND_SPEED = "Wind Speed",
}
const OPTIONS = {
  COMMON: ["Avg.", "Min.", "Max.", "Last Measured"],
  SOLAR: ["Sum", "Last Measured"],
  PRECIP: ["Sum Last 24h", "Sum Last 48h", "Sum Last Week", "Last Measured"],
} as const;

type MapParamPanelProps = {
  onSelectedParamChange: (param: WeatherParam | undefined, dataOption: string | undefined) => void;
};

export default function MapParamPanel({ onSelectedParamChange }: MapParamPanelProps) {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  const [selectedParam, setSelectedParam] = useState<WeatherParam>();
  const [options, setOptions] = useState<string[]>([...OPTIONS.COMMON]);
  const [selectedOption, setSelectedOption] = useState<string>();

  const onSelectParam = (param: WeatherParam) => {
    setSelectedParam(param);
    const optionsList: string[] = [];
    switch (param) {
      case WeatherParam.TEMPERATURE:
      case WeatherParam.RELATIVE_HUMIDITY:
      case WeatherParam.WIND_SPEED:
        optionsList.push(...OPTIONS.COMMON);
        break;
      case WeatherParam.SOLAR_RADIATION:
        optionsList.push(...OPTIONS.SOLAR);
        break;
      case WeatherParam.PRECIPITATION:
        optionsList.push(...OPTIONS.PRECIP);
        break;
    }
    setOptions(optionsList);
    setSelectedOption(optionsList[0]);
  };

  useEffect(() => {
    if (selectedParam || selectedOption) return;
    onSelectedParamChange(selectedParam, selectedOption);
  }, [selectedParam, selectedOption]);

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
            onClick={() => onSelectParam(WeatherParam.TEMPERATURE)}
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
            onClick={() => onSelectParam(WeatherParam.PRECIPITATION)}
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
            onClick={() => onSelectParam(WeatherParam.RELATIVE_HUMIDITY)}
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
            onClick={() => onSelectParam(WeatherParam.SOLAR_RADIATION)}
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
            onClick={() => onSelectParam(WeatherParam.WIND_SPEED)}
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
    </Box>
  );
}
