import { WeatherParam } from "../Components/MapParamPanel";

export function getMapDataForParam(param: WeatherParam, dataOption: string) {
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  const now = new Date();
}
