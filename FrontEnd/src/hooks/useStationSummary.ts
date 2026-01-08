import { useState, useEffect } from "react";

export type StationStatus = "online" | "offline" | "delayed";

export interface StationSummary {
  id: string;
  name: string;
  location: string | null;
  status: StationStatus;
  lastDataTimestamp: string;
  sensorsCount: number;
  sensors: string[];
  coordinates: {
    latitude: number | null;
    longitude: number | null;
    altitude: number | null;
  };
  installationDate: string | null;
  owner: string | null;
  dataFrequency: string | null;
  notes: string | null;
}

// Mock data hook - replace with real API call when available
export function useStationSummary(stationId: string | undefined) {
  const [data, setData] = useState<StationSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!stationId) {
      setData(null);
      setIsLoading(false);
      return;
    }

    // Simulate API call with mock data
    setIsLoading(true);
    const timer = setTimeout(() => {
      setData({
        id: stationId,
        name: `Station ${stationId}`,
        location: "Bordeaux, France",
        status: "online",
        lastDataTimestamp: new Date().toISOString(),
        sensorsCount: 5,
        sensors: ["Temperature", "Humidity", "Solar Radiation", "Wind Speed", "Precipitation"],
        coordinates: {
          latitude: 44.8378,
          longitude: -0.5792,
          altitude: 35,
        },
        installationDate: "2023-06-15",
        owner: "Agricultural Research Institute",
        dataFrequency: "Hourly",
        notes: "Primary weather monitoring station for vineyard sector A.",
      });
      setIsLoading(false);
    }, 300);

    return () => clearTimeout(timer);
  }, [stationId]);

  return { data, isLoading, error };
}
