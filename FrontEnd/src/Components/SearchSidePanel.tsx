import { useState } from "react";
import { Autocomplete, Box, Button, Divider, TextField, Typography } from "@mui/material";

type SearchSidePanelProps = {
  colors: any;
};

type Option = { label: string; value: string };

const SearchSidePanel = ({ colors }: SearchSidePanelProps) => {
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
  );
};

export default SearchSidePanel;
