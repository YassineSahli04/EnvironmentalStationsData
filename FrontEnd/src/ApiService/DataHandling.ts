import { WeatherParam } from "../Components/MapParamPanel";
import { getStations, getStationSensorData } from "./Api";
import type { CfSensorDataRow } from "./Objects/StationObj";

export async function getMapDataForParam(param: WeatherParam, date: Date) {
  const startOfDay = date;
  startOfDay.setUTCHours(0, 0, 0, 0);
  const endOfDay = new Date(startOfDay);
  endOfDay.setUTCHours(23, 59, 59);

  console.log(startOfDay, endOfDay);

  const stations = await getStations();
  const sensorsData: Record<string, CfSensorDataRow[]> = {};

  for (const st of stations) {
    const sensor = await getStationSensorData(st.Id, param, "daily", startOfDay, endOfDay);
    if (!sensor) continue;

    sensorsData[st.Id] = sensor.data;
  }

  return sensorsData;
}
