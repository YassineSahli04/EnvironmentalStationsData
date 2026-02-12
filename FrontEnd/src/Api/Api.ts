import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { StationObj, StationSensorObj } from "../Api/Objects/StationObj";

export const WeatherParam = {
  TEMPERATURE: "Temperature",
  PRECIPITATION: "Precipitation",
  RELATIVE_HUMIDITY: "Relative Humidity",
  SOLAR_RADIATION: "Solar Radiation",
  WIND_SPEED: "Wind Speed",
} as const;

export type WeatherParam = (typeof WeatherParam)[keyof typeof WeatherParam];

const TypeFilter = [
  "Pyranometer",
  "Pluviometer",
  "Meteorological",
  "Meteorological/Pluviometer",
  // "Drill and Drop",
  // "Aquachek",
];
const url = "http://localhost:8000/api/stations";

export async function getStations(): Promise<StationObj[]> {
  const allStationsUrl = `${url}/all`;
  try {
    const response = await axios.get<StationObj[]>(allStationsUrl, {
      params: { type: TypeFilter },
    });
    return response.data;
  } catch (err) {
    console.error("Issue While Loading Stations Data", err);
    throw new Error("Issue While Loading Stations Data");
  }
}

export function useAllStations() {
  return useQuery<StationObj[]>({
    queryKey: ["allStationsObj"],
    queryFn: getStations,
  });
}

export async function getStationsGeojson() {
  const geojsonUrl = `${url}/geojson`;
  const res = await axios.get(geojsonUrl, {
    params: { type: TypeFilter },
  });
  return res.data;
}

export async function getStationSensorsData(
  stationId: number | string,
  sensorsId: string[],
  dataGroup?: string,
  startDtUTC?: Date | string,
  endDtUTC?: Date | string
): Promise<StationSensorObj | null> {
  const sensorsUrl = `${url}/station/${stationId}/sensors`;

  try {
    const res = await axios.get<StationSensorObj>(sensorsUrl, {
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
