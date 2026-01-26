import { useState, useMemo, useEffect, useRef } from "react";
import { Box } from "@mui/material";
import { useParams, useNavigate } from "react-router-dom";
import { useAllStations, getStationSensorsData } from "../Api/Api";
import AmbianceDualAxisChart from "../Components/Charts/AmbianceDualAxisChart";
import VpdHumidityChart from "../Components/Charts/VpdHumidityChart";
import { OverlayLoader } from "../Components/Global/OverlayLoader";
import ChartCard from "../Components/StationPageComponents/ChartCard";
import DataQueryCard from "../Components/StationPageComponents/DataQueryCard";
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

  const station = useMemo(() => stations?.find((st) => st.Id === stationId), [stations, stationId]);

  const [ambianceData, setAmbianceData] = useState<any[]>([]);
  const [stressData, setStressData] = useState<any[]>([]);
  const [isChartLoading, setIsChartLoading] = useState(true);

  const onDataQueryChange = (startDate: string, endDate: string, aggregationType: string) => {
    if (!stationId) return;

    setIsChartLoading(true);
    (async () => {
      const resAmbianceData = await getStationSensorsData(
        stationId,
        ["Relative Humidity", "Solar Radiation", "Temperature"],
        aggregationType,
        startDate,
        endDate
      );
      const resStressData = await getStationSensorsData(
        stationId,
        ["Relative Humidity", "vpd"],
        aggregationType,
        startDate,
        endDate
      );
      setAmbianceData(resAmbianceData || []);
      setStressData(resStressData || []);
      setIsChartLoading(false);
    })();
  };

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
        station={{ ...station, Status: "online" }}
        isLoading={isStationLoading}
        onStationChange={handleStationChange}
        availableStations={[]} // Can be populated from API
      />

      {/* Collapsible Station Details */}
      <StationDetailsAccordion station={station} isLoading={isStationLoading} />

      {/* Data Query Settings */}
      <DataQueryCard stationId={stationId} onDataQueryChange={onDataQueryChange} />

      {/* Charts Area */}
      <ChartCard title="Ambiance" subtitle="Temperature, Humidity & Solar Radiation">
        <OverlayLoader show={isChartLoading} dim={0.2} blockInteraction={isChartLoading} />
        {isChartLoading ? null : ambianceData.length === 0 ? (
          <h1 style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
            No Data Available
          </h1>
        ) : (
          <AmbianceDualAxisChart ref={chartRef} data={ambianceData} height={400} />
        )}
      </ChartCard>
      <ChartCard title="Stress" subtitle="VPD & Relative Humidity">
        <OverlayLoader show={isChartLoading} dim={0.2} blockInteraction={isChartLoading} />
        {isChartLoading ? null : stressData.length === 0 ? (
          <h1 style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
            No Data Available
          </h1>
        ) : (
          <VpdHumidityChart ref={chartRef} data={stressData} height={400} />
        )}
      </ChartCard>
    </Box>
  );
}
