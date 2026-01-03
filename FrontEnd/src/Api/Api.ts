import axios from "axios";
import type { StationObj, StationSensorObj } from "../Api/Objects/StationObj";

export enum WeatherParam {
  TEMPERATURE = "Temperature",
  PRECIPITATION = "Precipitation",
  RELATIVE_HUMIDITY = "Relative Humidity",
  SOLAR_RADIATION = "Solar Radiation",
  WIND_SPEED = "Wind Speed",
}

const TypeFilter = [
  "Pyranometer",
  "Pluviometer",
  "Meteorological",
  "Meteorological/Pluviometer",
  // "Drill and Drop",
  // "Aquachek",
];
const url = "http://localhost:8000/api/stations";

export async function getStations(typeFilter: string[] = TypeFilter): Promise<StationObj[]> {
  const allStationsUrl = `${url}/all`;
  try {
    const response = await axios.get<StationObj[]>(allStationsUrl, {
      params: { type: typeFilter },
    });
    return response.data;
  } catch (err) {
    console.error("Issue While Loading Stations Data", err);
    throw new Error("Issue While Loading Stations Data");
  }
}

export async function getStationsGeojson(typeFilter: string[] = TypeFilter) {
  const geojsonUrl = `${url}/geojson`;
  const res = await axios.get(geojsonUrl, {
    params: { type: typeFilter },
  });
  return res.data;
}

export async function getStationSensorData(
  stationId: string,
  sensorId: string,
  dataGroup?: string,
  startDtUTC?: Date | string,
  endDtUTC?: Date | string
): Promise<StationSensorObj | null> {
  const sensorUrl = `${url}/station/${stationId}/${sensorId}`;

  try {
    const res = await axios.get<StationSensorObj>(sensorUrl, {
      params: {
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
