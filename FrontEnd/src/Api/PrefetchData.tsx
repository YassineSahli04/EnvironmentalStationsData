import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getStations, getStationsGeojson } from "./StationApi.ts";
import { TypeFilter } from "./StationApi.ts";

export function PrefetchData() {
  const qc = useQueryClient();

  useEffect(() => {
    qc.prefetchQuery({ queryKey: ["allStationsGeojson"], queryFn: getStationsGeojson });
    qc.prefetchQuery({
      queryKey: ["allStationsObj", [...TypeFilter]],
      queryFn: () => getStations([...TypeFilter]),
    });
  }, [qc]);

  return null;
}
