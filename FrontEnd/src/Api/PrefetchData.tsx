// PrefetchBootstrap.tsx
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getStations, getStationsGeojson } from "./StationApi.ts";

// adjust imports

export function PrefetchData() {
  const qc = useQueryClient();

  useEffect(() => {
    qc.prefetchQuery({ queryKey: ["allStationsGeojson"], queryFn: getStationsGeojson });
    qc.prefetchQuery({ queryKey: ["allStationsObj"], queryFn: getStations });
  }, [qc]);

  return null;
}
