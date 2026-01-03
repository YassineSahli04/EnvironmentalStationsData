import { getStations, getStationSensorData } from "./Api";
import { WeatherParam } from "./Api.ts";
import type { CfSensorDataRow } from "./Objects/StationObj";

export async function getMapDataForParam(param: WeatherParam, date: Date) {
  const startOfDay = new Date(
    Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), 0, 0, 0)
  );

  const endOfDay = new Date(
    Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), 23, 59, 59)
  );

  const stations = await getStations();
  const sensorsData: Record<string, CfSensorDataRow[]> = {};

  for (const st of stations) {
    const sensor = await getStationSensorData(st.Id, param, "day", startOfDay, endOfDay);
    if (!sensor) continue;

    sensorsData[st.Id] = sensor.data;
  }

  return sensorsData;
}
