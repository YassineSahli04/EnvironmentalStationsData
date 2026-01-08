import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { getStationSensorsData } from "../Api/Api";
import AmbianceDualAxisChart from "../Components/Charts/AmbianceDualAxisChart";

export default function StationDataPage() {
  const { stationId } = useParams<{ stationId: string }>();

  const startOfDay = "2026-01-01T00:00:00Z";
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

  return (
    <>
      <div style={{ backgroundColor: "#ee1111ff" }}>
        <h1>Hello, this is station {stationId}</h1>
      </div>
      <AmbianceDualAxisChart data={ambianceData} />
    </>
  );
}
