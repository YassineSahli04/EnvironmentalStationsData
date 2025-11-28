import axios from "axios";
import type { StationObj } from "../ApiService/Objects/StationObj";

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
