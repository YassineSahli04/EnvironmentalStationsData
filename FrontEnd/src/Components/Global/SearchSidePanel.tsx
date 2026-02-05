import { useEffect, useMemo, useState } from "react";
import { Autocomplete, Box, Button, Divider, TextField, Typography, Slider } from "@mui/material";
import { useAllStations } from "../../Api/StationApi.ts";
import type { StationObj } from "../../Api/Objects/StationObj.ts";

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

type SearchSidePanelProps = {
  colors: any;
  onViewData: (stationId: string) => void;
  onLocationSelected?: (center: [number, number] | undefined, radiusKm: number | undefined) => void;
};

type Option = { label: string; id: string };
type GeoOption = { label: string; center: [number, number] };

const DEFAULT_RADIUS_KM = 7;

function distanceKm(a: [number, number], b: [number, number]) {
  const toRad = (x: number) => (x * Math.PI) / 180;
  const R = 6371; // km
  const [lng1, lat1] = a;
  const [lng2, lat2] = b;

  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);

  const s1 = Math.sin(dLat / 2);
  const s2 = Math.sin(dLng / 2);

  const aa = s1 * s1 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * s2 * s2;
  const c = 2 * Math.atan2(Math.sqrt(aa), Math.sqrt(1 - aa));
  return R * c;
}

const SearchSidePanel = ({ colors, onViewData, onLocationSelected }: SearchSidePanelProps) => {
  const { data: allLoadedStations, isLoading } = useAllStations();
  const [allStations, setAllStations] = useState<StationObj[]>([]);

  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedStation, setSelectedStation] = useState<Option>({ label: "", id: "" });

  const [stations, setStations] = useState<Option[]>([]);
  const [types, setTypes] = useState<string[]>([]);

  const [unselectedStationErrorIsVisible, setUnselectedStationErrorIsVisible] =
    useState<boolean>(false);

  const [radiusKm, setRadiusKm] = useState<number>(DEFAULT_RADIUS_KM);

  const [locationInput, setLocationInput] = useState<string>("");
  const [locationOptions, setLocationOptions] = useState<GeoOption[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<GeoOption | null>(null);
  const [locationError, setLocationError] = useState<string>("");

  async function geocode(q: string): Promise<GeoOption[]> {
    if (!q.trim()) return [];

    const url =
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(q)}.json` +
      `?autocomplete=true` +
      `&limit=5` +
      `&country=tn` +
      `&types=region,place,locality,district` +
      `&language=fr` +
      `&access_token=${MAPBOX_TOKEN}`;

    const res = await fetch(url);
    if (!res.ok) return [];
    const data = await res.json();

    return (data.features ?? []).map((f: any) => ({
      label: f.place_name,
      center: f.center as [number, number],
    }));
  }

  const commitLocationText = async (text: string) => {
    const q = text.trim();

    if (!q) {
      setSelectedLocation(null);
      setLocationError("");
      return;
    }

    try {
      const results = await geocode(q);
      if (results.length === 0) {
        setLocationError("No results found for that location.");
        return;
      }
      setLocationError("");
      setSelectedLocation(results[0]);
      setLocationInput(results[0].label);
    } catch {
      setLocationError("Location search failed.");
    }
  };

  // Load all stations
  useEffect(() => {
    if (allLoadedStations) setAllStations(allLoadedStations);
  }, [allLoadedStations]);

  // Debounced geocoding suggestions
  useEffect(() => {
    const t = setTimeout(async () => {
      const opts = await geocode(locationInput);
      setLocationOptions(opts);
    }, 250);

    return () => clearTimeout(t);
  }, [locationInput]);

  useEffect(() => {
    if (!selectedLocation) {
      onLocationSelected?.(undefined, undefined);
      return;
    }
    onLocationSelected?.(selectedLocation.center, radiusKm);
  }, [selectedLocation, radiusKm, onLocationSelected]);

  const stationsInRadius = useMemo(() => {
    if (!selectedLocation) return allStations;

    return allStations.filter((station: any) => {
      const lng = station.Longitude;

      const lat = station.Latitude;

      if (lng == null || lat == null) return false;

      const d = distanceKm(selectedLocation.center, [Number(lng), Number(lat)]);
      return d <= radiusKm;
    });
  }, [allStations, selectedLocation, radiusKm]);

  useEffect(() => {
    const stationOptions: Option[] = [];
    const typeOptions = new Set<string>([]);

    for (let station of stationsInRadius) {
      const name: string = station.Id + "-" + station.Name;
      const option: Option = { label: name, id: station.Id };

      if (station.Type) typeOptions.add(station.Type);

      if (selectedTypes.length == 0) {
        stationOptions.push(option);
        continue;
      }

      const matchesType =
        selectedTypes.length === 0 || (station.Type && selectedTypes.includes(station.Type));

      if (matchesType) stationOptions.push(option);
    }

    setTypes([...typeOptions]);
    setStations(stationOptions);
  }, [stationsInRadius, selectedTypes]);

  useEffect(() => {
    setSelectedStation({ label: "", id: "" });
    setUnselectedStationErrorIsVisible(false);
  }, [selectedLocation, radiusKm]);

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
        zIndex: 4,
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
        freeSolo
        options={locationOptions}
        value={selectedLocation}
        inputValue={locationInput}
        onInputChange={(_, value) => {
          setLocationInput(value);
          setLocationError("");
        }}
        onChange={(_, value) => {
          if (typeof value === "string") {
            setLocationInput(value);
            void commitLocationText(value);
            return;
          }
          setSelectedLocation(value);
          setLocationError("");
          if (value) setLocationInput(value.label);
        }}
        getOptionLabel={(o) => (typeof o === "string" ? o : o.label)}
        filterOptions={(x) => x}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Location"
            placeholder="City, street, address"
            size="small"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                void commitLocationText(locationInput);
              }
            }}
          />
        )}
      />

      {locationError && (
        <Typography variant="caption" color="error" sx={{ mt: -1 }}>
          {locationError}
        </Typography>
      )}

      {selectedLocation && (
        <>
          <Typography variant="caption" color={colors.grey[200]} sx={{ mt: -1 }}>
            Radius: {radiusKm} km • Found: {stationsInRadius.length} station(s)
          </Typography>

          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color={colors.grey[200]}>
              Adjust radius
            </Typography>
            <Slider
              value={radiusKm}
              onChange={(_, v) => setRadiusKm(v as number)}
              min={1}
              max={50}
              step={1}
              valueLabelDisplay="auto"
            />
          </Box>
        </>
      )}
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
          setSelectedStation(value ?? { label: "", id: "" });
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
