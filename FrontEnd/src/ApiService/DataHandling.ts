import { WeatherParam } from "../Components/MapParamPanel";
import { getStations, getStationSensorData } from "./Api";

export async function getMapDataForParam(param: WeatherParam, dataOption: string) {
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  startOfToday.setDate(startOfToday.getDate() - 1);
  const endOfDay = new Date(startOfToday);
  endOfDay.setHours(23, 59, 59, 999);

  const stations = await getStations();
  const sensorsData: Record<string, { time: string; value: number | null }[]> = {};

  for (const st of stations) {
    const sensor = await getStationSensorData(st.Id, param, "daily", startOfToday, endOfDay);
    if (!sensor) continue;
    console.log(sensor);

    const cleanedData = sensor.data.map((p) => ({
      time: p.time,
      value: p.values[dataOption],
    }));

    sensorsData[st.Id] = cleanedData;
  }

  return sensorsData;
}
