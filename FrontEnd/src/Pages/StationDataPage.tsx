import { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import { getStationSensorsData } from "../Api/Api";
import AmbianceDualAxisChart from "../Components/Charts/AmbianceDualAxisChart";

type StationDataPageProps = {
  isSideBarCollapsed: boolean;
};

export default function StationDataPage({ isSideBarCollapsed }: StationDataPageProps) {
  const { stationId } = useParams<{ stationId: string }>();
  const chartRef = useRef<any>(null);

  const startOfDay = "2025-12-01T00:00:00Z";
  const endOfDay = "2026-01-08T00:00:00Z";

  const [ambianceData, setAmbianceData] = useState<any[]>([]);

  useEffect(() => {
    if (!stationId) return;

    (async () => {
      const res = await getStationSensorsData(
        stationId,
        ["Relative Humidity", "Solar Radiation", "Temperature"],
        "hour",
        startOfDay,
        endOfDay
      );
      setAmbianceData(res);
    })();
  }, [stationId]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (chartRef.current) {
        chartRef.current.getEchartsInstance()?.resize();
      }
    }, 25);
    return () => clearTimeout(timeoutId);
  }, [isSideBarCollapsed]);

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <AmbianceDualAxisChart ref={chartRef} data={ambianceData} />
    </div>
  );
}
