import { useEffect, useState } from "react";
import { Autocomplete, Box, Button, Divider, TextField, Typography } from "@mui/material";
import { useAllStations } from "../../Api/Api.ts";
import type { StationObj } from "../../Api/Objects/StationObj.ts";

type SearchSidePanelProps = {
  colors: any;
  onViewData: (stationId: string) => void;
};

type Option = { label: string; id: string };

const SearchSidePanel = ({ colors, onViewData }: SearchSidePanelProps) => {
  const { data: allLoadedStations, isLoading } = useAllStations();
  const [allStations, setAllStations] = useState<StationObj[]>([]);

  const [selectedManufacturer, setSelectedManufacturer] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedStation, setSelectedStation] = useState<Option>({ label: "", id: "" });

  const [stations, setStations] = useState<Option[]>([]);
  const [manufacturers, setManufacturers] = useState<string[]>([]);
  const [types, setTypes] = useState<string[]>([]);

  const [unselectedStationErrorIsVisible, setUnselectedStationErrorIsVisible] =
    useState<boolean>(false);

  useEffect(() => {
    if (allLoadedStations) setAllStations(allLoadedStations);
  }, [allLoadedStations]);

  useEffect(() => {
    const stationOptions: Option[] = [];
    const manufacturerOptions = new Set<string>([]);
    const typeOptions = new Set<string>([]);
    for (let station of allStations) {
      const name: string = station.Id + "-" + station.Name;
      const option: Option = { label: name, id: station.Id };
      if (station.Manufacturer) manufacturerOptions.add(station.Manufacturer);
      if (station.Type) typeOptions.add(station.Type);
      if (selectedManufacturer.length === 0 && selectedTypes.length == 0) {
        stationOptions.push(option);
        continue;
      }
      const matchesManufacturer =
        selectedManufacturer.length === 0 ||
        (station.Manufacturer && selectedManufacturer.includes(station.Manufacturer));

      const matchesType =
        selectedTypes.length === 0 || (station.Type && selectedTypes.includes(station.Type));

      if (matchesManufacturer && matchesType) {
        stationOptions.push(option);
      }
    }
    setManufacturers([...manufacturerOptions]);
    setTypes([...typeOptions]);
    setStations(stationOptions);
  }, [allStations, selectedManufacturer, selectedTypes]);

  const handleViewData = () => {
    if (!selectedStation || selectedStation.id == "") {
      setUnselectedStationErrorIsVisible(true);
      return;
    }
    onViewData(selectedStation.id);
  };

  return (
    <Box
      sx={{
        position: "absolute",
        left: "100%",
        width: 300,
        backgroundColor: `${colors.primary[700]}`,
        borderRight: `1px solid ${colors.grey[700]}`,
        boxShadow: 4,
        p: 2,
        display: "flex",
        flexDirection: "column",
        gap: 2,
        height: "90vh",
        zIndex: 2,
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
        options={manufacturers}
        value={selectedManufacturer}
        onChange={(_, value) => setSelectedManufacturer(value)}
        getOptionLabel={(option) => option}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Station Manufacturer"
            placeholder="Select station manufacturer"
            size="small"
          />
        )}
      />

      <Autocomplete
        multiple
        options={types}
        value={selectedTypes}
        onChange={(_, value) => setSelectedTypes(value)}
        getOptionLabel={(option) => option}
        renderInput={(params) => (
          <TextField {...params} label="Types" placeholder="Select types" size="small" />
        )}
      />

      <Autocomplete
        options={stations}
        value={selectedStation}
        onChange={(_, value) => {
          setSelectedStation(value);
          if (value) setUnselectedStationErrorIsVisible(false);
        }}
        getOptionLabel={(option) => option.label}
        renderInput={(params) => (
          <TextField {...params} label="Stations" placeholder="Select station" size="small" />
        )}
      />

      {unselectedStationErrorIsVisible && (
        <Typography variant="body2" color="error" sx={{ mt: -1 }}>
          Please select a station before viewing data.
        </Typography>
      )}

      <Box flexGrow={1} />

      <Button variant="contained" fullWidth onClick={handleViewData}>
        View data
      </Button>
    </Box>
  );
};

export default SearchSidePanel;
