import { getStations, getStationSensorsData } from "./StationApi.ts";
import { WeatherParam } from "./StationApi.ts";
import { queryClient } from "./AppQueryClient.ts";
import type { SensorDataRow } from "./Objects/StationObj";

export async function getMapDataForParam(param: WeatherParam, date: Date) {
  const startOfDay = new Date(
    Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), 0, 0, 0)
  );

  const endOfDay = new Date(
    Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), 23, 59, 59)
  );

  const stations = await queryClient.fetchQuery({
    queryKey: ["allStationsObj"],
    queryFn: getStations,
  });

  const pairs = await getDataInBatches(stations, 8, async (st) => {
    const sensor = await getStationSensorsData(st.Id, [param], "daily", startOfDay, endOfDay);
    return sensor ? ([st.Id, sensor.data] as const) : null;
  });

  const sensorsData: Record<string, SensorDataRow[]> = {};
  for (const p of pairs) {
    if (!p) continue;
    const [stationId, data] = p;
    sensorsData[stationId] = data;
  }

  return sensorsData;
}

export async function getDataInBatches<T, R>(
  items: T[],
  limit: number,
  fn: (item: T) => Promise<R>
): Promise<R[]> {
  const results: R[] = [];
  let i = 0;

  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (i < items.length) {
      const idx = i++;
      results[idx] = await fn(items[idx]);
    }
  });

  await Promise.all(workers);
  return results;
}
