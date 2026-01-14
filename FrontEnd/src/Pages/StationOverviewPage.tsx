import { useState, useMemo, useEffect, useRef } from "react";
import { Box } from "@mui/material";
import { useParams, useNavigate } from "react-router-dom";
import { useAllStations, getStationSensorsData } from "../Api/Api";
import AmbianceDualAxisChart from "../Components/Charts/AmbianceDualAxisChart";
import { OverlayLoader } from "../Components/Global/OverlayLoader";
import ChartCard from "../Components/StationPageComponents/ChartCard";
import StationDetailsAccordion from "../Components/StationPageComponents/StationDetailsAccordion";
import StationSummaryBar from "../Components/StationPageComponents/StationSummaryBar";

type StationOverviewPageProps = {
  isSideBarCollapsed: boolean;
};

export default function StationOverviewPage({ isSideBarCollapsed }: StationOverviewPageProps) {
  const { stationId } = useParams<{ stationId: string }>();
  const navigate = useNavigate();
  const chartRef = useRef<any>(null);

  const { data: stations, isStationLoading } = useAllStations();

  const station = useMemo(() => stations.find((st) => st.Id === stationId), [stations, stationId]);

  const [ambianceData, setAmbianceData] = useState<any[]>([]);
  const [isChartLoading, setIsChartLoading] = useState(true);

  const startOfDay = "2025-12-01T00:00:00Z";
  const endOfDay = "2026-01-08T00:00:00Z";

  useEffect(() => {
    if (!stationId) return;

    setIsChartLoading(true);
    (async () => {
      const res = await getStationSensorsData(
        stationId,
        ["Relative Humidity", "Solar Radiation", "Temperature"],
        "hour",
        startOfDay,
        endOfDay
      );
      setAmbianceData(res || []);
      setIsChartLoading(false);
    })();
  }, [stationId]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      chartRef.current?.getEchartsInstance?.()?.resize();
    }, 250);
    return () => clearTimeout(timeoutId);
  }, [isSideBarCollapsed]);

  const handleStationChange = (newStationId: string) => {
    navigate(`/stations/${newStationId}`);
  };

  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        overflow: "auto",
        p: 2,
        bgcolor: "#141b2d",
      }}
    >
      {/* Sticky Station Summary Bar */}
      <StationSummaryBar
        station={station}
        isLoading={isStationLoading}
        onStationChange={handleStationChange}
        availableStations={[]} // Can be populated from API
      />

      {/* Collapsible Station Details */}
      <StationDetailsAccordion station={station} isLoading={isStationLoading} />

      {/* Charts Area */}
      <ChartCard title="Ambiance" subtitle="Temperature, Humidity & Solar Radiation">
        <OverlayLoader show={isChartLoading} dim={0.2} blockInteraction={isChartLoading} />
        {isChartLoading ? null : ambianceData.length === 0 ? (
          <h1 style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
            No Data Available
          </h1>
        ) : (
          <AmbianceDualAxisChart ref={chartRef} data={ambianceData} height={400} title="" />
        )}
      </ChartCard>
    </Box>
  );
}
