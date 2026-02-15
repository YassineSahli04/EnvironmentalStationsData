import { useEffect } from "react";
import { useAuth } from "@clerk/clerk-react";
import { useQueryClient } from "@tanstack/react-query";
import { getStations, getStationsGeojson } from "./StationApi.ts";
import { MapStationsTypeFilter } from "./StationApi.ts";

export function PrefetchData() {
  const qc = useQueryClient();
  const { getToken } = useAuth();

  useEffect(() => {
    qc.prefetchQuery({ queryKey: ["allStationsGeojson"], queryFn: getStationsGeojson });
    qc.prefetchQuery({
      queryKey: ["allStationsObj", [...MapStationsTypeFilter]],
      queryFn: async () => {
        const token = await getToken();
        return getStations([...MapStationsTypeFilter], token);
      },
    });
  }, [qc, getToken]);

  return null;
}
