import { WeatherParam } from "../Components/MapParamPanel";
import { getStations, getStationSensorData } from "./Api";
import type { CfSensorDataRow } from "./Objects/StationObj";

export async function getMapDataForParam(param: WeatherParam) {
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  startOfToday.setDate(startOfToday.getDate() - 1);
  const endOfDay = new Date(startOfToday);
  endOfDay.setHours(23, 59, 59, 999);

  const stations = await getStations();
  const sensorsData: Record<string, CfSensorDataRow[]> = {};

  for (const st of stations) {
    const sensor = await getStationSensorData(st.Id, param, "daily", startOfToday, endOfDay);
    if (!sensor) continue;

    sensorsData[st.Id] = sensor.data;
  }

  return sensorsData;
}
