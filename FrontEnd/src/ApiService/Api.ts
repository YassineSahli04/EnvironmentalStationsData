import axios from "axios";
import type { StationObj, StationSensorObj } from "../ApiService/Objects/StationObj";

const typeFilter = ["Pyranometer", "Pluviometer", "Meteorological", "Meteorological/Pluviometer"];
const url = "http://localhost:8000/api/stations";

export async function getStations(): Promise<StationObj[]> {
  try {
    const response = await axios.get<StationObj[]>(url, {
      params: { type: typeFilter },
    });
    return response.data;
  } catch (err) {
    console.error("Issue While Loading Stations Data", err);
    throw new Error("Issue While Loading Stations Data");
  }
}

export async function getStationsGeojson() {
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
