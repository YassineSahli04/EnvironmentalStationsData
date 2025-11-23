import { useEffect, useState } from "react";
import { Autocomplete, Box, Button, Divider, TextField, Typography } from "@mui/material";

type SearchSidePanelProps = {
  colors: any;
};

type Option = { label: string; id: string };

const SearchSidePanel = ({ colors }: SearchSidePanelProps) => {
  const [selectedStations, setSelectedStations] = useState<Option[]>([]);
  const [selectedSensors, setSelectedSensors] = useState<Option[]>([]);

  const [stations, setStations] = useState<Option[]>([]);
  useEffect(() => {
    async function load() {
      try {
        const stations = await (await fetch("http://localhost:8000/api/stations/a")).json();
        const stationOptions: Option[] = [];
        for (let station of stations) {
          const name: string = station.Id + "-" + station.Name;
          const option: Option = { label: name, id: station.Id };
          stationOptions.push(option);
        }
        setStations(stationOptions);
      } catch {
        console.log("====================================");
        console.log("Issue While Loading Stations Data");
        console.log("====================================");
      }
    }
    load();
  }, []);

  const handleViewData = () => {
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
        Select Stations and sensors to visualize the data.
      </Typography>

      <Divider sx={{ borderColor: colors.grey[700] }} />

      <Autocomplete
        multiple
        options={stations}
        value={selectedStations}
        onChange={(_, value) => setSelectedStations(value)}
        getOptionLabel={(option) => option.label}
        renderInput={(params) => (
          <TextField {...params} label="Filters" placeholder="Select filters" size="small" />
        )}
      />

      <Autocomplete
        multiple
        options={stations}
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
