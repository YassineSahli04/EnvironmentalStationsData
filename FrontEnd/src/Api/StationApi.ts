import { useAuth } from "@clerk/clerk-react";
import { QueryClient, useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { SensorDataRow, StationObj, StationSensorObj } from "./Objects/StationObj";

export const WeatherParam = {
  TEMPERATURE: "Temperature",
  PRECIPITATION: "Precipitation",
  RELATIVE_HUMIDITY: "Relative Humidity",
  SOLAR_RADIATION: "Solar Radiation",
  WIND_SPEED: "Wind Speed",
} as const;

export type WeatherParam = (typeof WeatherParam)[keyof typeof WeatherParam];

export const MapStationsTypeFilter = [
  "Pyranometer",
  "Pluviometer",
  "Meteorological",
  "Meteorological/Pluviometer",
  "Virtual",
] as const;

const API_URL = import.meta.env.VITE_API_URL;
const url = `${API_URL}/api/stations`;

export async function getStations(
  typeFilter: string[],
  token: string | null
): Promise<StationObj[]> {
  const allStationsUrl = `${url}/all`;
  try {
    const response = await axios.get<StationObj[]>(allStationsUrl, {
      headers: { Authorization: `Bearer ${token}` },
      params: { type: typeFilter },
    });
    return response.data;
  } catch (err) {
    console.error("Issue While Loading Stations Data", err);
    throw new Error("Issue While Loading Stations Data");
  }
}

export function useAllStations(types: string[] | undefined, enabled = true) {
  const { getToken } = useAuth();

  return useQuery<StationObj[]>({
    queryKey: ["allStationsObj", types],
    enabled: enabled && types !== undefined,
    queryFn: async () => {
      const token = await getToken();
      return getStations(types ?? [], token);
    },
  });
}

export async function getStationsGeojson() {
  const geojsonUrl = `${url}/geojson`;
  const res = await axios.get(geojsonUrl, {
    params: { type: MapStationsTypeFilter },
  });
  return res.data;
}

export async function getStationSensorsData(
  stationId: number | string,
  sensorsId: string[],
  dataGroup?: string,
  startDtUTC?: Date | string,
  endDtUTC?: Date | string
): Promise<SensorDataRow[] | null> {
  const sensorsUrl = `${url}/station/${stationId}/sensors`;

  try {
    const res = await axios.get<SensorDataRow[]>(sensorsUrl, {
      params: {
        sensorsId,
        dataGroup,
        startDtUTC: startDtUTC instanceof Date ? startDtUTC.toISOString() : startDtUTC,
        endDtUTC: endDtUTC instanceof Date ? endDtUTC.toISOString() : endDtUTC,
      },
    });

    return res.data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      console.error("Failed to fetch station sensor data:", {
        stationId,
        sensorsId,
        status: err.response?.status,
        detail: err.response?.data?.detail ?? err.message,
      });
      return null;
    }

    console.error("Unexpected error while fetching station sensor data:", err);
    return null;
  }
}

export async function getStationSensor(
  stationId: string,
  sensorId: string,
  dataGroup?: string,
  startDtUTC?: Date | string,
  endDtUTC?: Date | string
): Promise<StationSensorObj | null> {
  const sensorsUrl = `${url}/station/${stationId}/sensor`;

  try {
    const res = await axios.get<StationSensorObj>(sensorsUrl, {
      params: {
        sensorId,
        dataGroup,
        startDtUTC: startDtUTC instanceof Date ? startDtUTC.toISOString() : startDtUTC,
        endDtUTC: endDtUTC instanceof Date ? endDtUTC.toISOString() : endDtUTC,
      },
    });

    return res.data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      console.error("Failed to fetch station sensor data:", {
        stationId,
        sensorId,
        status: err.response?.status,
        detail: err.response?.data?.detail ?? err.message,
      });
      return null;
    }

    console.error("Unexpected error while fetching station sensor data:", err);
    return null;
  }
}

export async function updateStationInfo(
  token: string,
  station: StationObj,
  queryClient: QueryClient
) {
  try {
    const response = await axios.put(`${url}/update/${station.Id}`, station, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    queryClient.setQueryData(["allStationsObj"], (oldData: StationObj[] | undefined) => {
      if (!oldData) return [response.data];
      return oldData.map((s) => (s.Id === station.Id ? response.data : s));
    });
    return response.data;
  } catch (err) {
    console.error("Issue While Updating Station Data", err);
    throw new Error("Issue While Updating Station Data");
  }
}
