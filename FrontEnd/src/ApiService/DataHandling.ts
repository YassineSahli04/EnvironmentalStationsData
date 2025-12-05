import { WeatherParam } from "../Components/MapParamPanel";
import { getStations, getStationSensorData } from "./Api";
import type { StationSensorObj, CfSensorDataRow } from "./Objects/StationObj";

export async function getMapDataForParam(param: WeatherParam, dataOption: string) {
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  const now = new Date();

  const stations = (await getStations()).filter((st) => st.Manufacturer === "Pessl");
  const sensorsData: Record<string, { time: string; value: number | null }[]> = {};

  for (const st of stations) {
    const sensor = await getStationSensorData(st.Id, param, "hourly", startOfToday, now);
    if (!sensor) continue;

    const cleanedData = sensor.data.map((p) => ({
      time: p.time,
      value: p.values[dataOption],
    }));

    sensorsData[st.Id] = cleanedData;
  }
  return sensorsData;
}
