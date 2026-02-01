import { useState, useMemo, useEffect, useRef } from "react";
import { Box } from "@mui/material";
import { useParams, useNavigate } from "react-router-dom";
import { useAllStations, getStationSensorsData } from "../Api/Api";
import AmbianceChart from "../Components/Charts/AmbianceChart";
import EventsChart from "../Components/Charts/EventsChart";
import StressChart from "../Components/Charts/StressChart";
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
  const id = Number(stationId);
  const navigate = useNavigate();
  const chartRef = useRef<any>(null);

  const { data: stations, isStationLoading } = useAllStations();

  const station = useMemo(() => stations?.find((st) => st.Id === id), [stations, id]);

  const [ambianceData, setAmbianceData] = useState<any[]>([]);
  const [stressData, setStressData] = useState<any[]>([]);
  const [eventsData, setEventsData] = useState<any[]>([]);
  const [isChartLoading, setIsChartLoading] = useState(true);
  const [expandedChart, setExpandedChart] = useState<"ambiance" | "stress" | "events" | null>(
    "ambiance"
  );

  const onDataQueryChange = (startDate: string, endDate: string, aggregationType: string) => {
    if (!id) return;

    setIsChartLoading(true);
    (async () => {
      const resAmbianceData = await getStationSensorsData(
        id,
        ["Relative Humidity", "Solar Radiation", "Temperature"],
        aggregationType,
        startDate,
        endDate
      );
      const resStressData = await getStationSensorsData(
        id,
        ["Relative Humidity", "vpd"],
        aggregationType,
        startDate,
        endDate
      );
      const resEventsData = await getStationSensorsData(
        id,
        ["Precipitation", "wind speed"],
        aggregationType,
        startDate,
        endDate
      );
      setAmbianceData(resAmbianceData || []);
      setStressData(resStressData || []);
      setEventsData(resEventsData || []);
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
        station={station}
        isLoading={isStationLoading}
        onStationChange={handleStationChange}
        availableStations={[]} // Can be populated from API
      />

      {/* Collapsible Station Details */}
      <StationDetailsAccordion station={station} isLoading={isStationLoading} />

      {/* Data Query Settings */}
      <DataQueryCard stationId={stationId} onDataQueryChange={onDataQueryChange} />

      {/* Charts Area */}
      <ChartCard
        title="Ambiance"
        subtitle="Temperature, Relative Humidity & Solar Radiation"
        expanded={expandedChart === "ambiance"}
        onToggle={() => setExpandedChart(expandedChart === "ambiance" ? null : "ambiance")}
        accentColor="#f97316"
      >
        <OverlayLoader show={isChartLoading} dim={0.2} blockInteraction={isChartLoading} />
        {isChartLoading ? null : ambianceData.length === 0 ? (
          <h1 style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
            No Data Available
          </h1>
        ) : (
          <AmbianceChart ref={chartRef} data={ambianceData} height={400} />
        )}
      </ChartCard>
      <ChartCard
        title="Stress"
        subtitle="VPD & Relative Humidity"
        expanded={expandedChart === "stress"}
        onToggle={() => setExpandedChart(expandedChart === "stress" ? null : "stress")}
        accentColor="#f472b6"
      >
        <OverlayLoader show={isChartLoading} dim={0.2} blockInteraction={isChartLoading} />
        {isChartLoading ? null : stressData.length === 0 ? (
          <h1 style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
            No Data Available
          </h1>
        ) : (
          <StressChart ref={chartRef} data={stressData} height={400} />
        )}
      </ChartCard>
      <ChartCard
        title="Events"
        subtitle="Precipitation & Wind Speed"
        expanded={expandedChart === "events"}
        onToggle={() => setExpandedChart(expandedChart === "events" ? null : "events")}
        accentColor="#38bdf8"
      >
        <OverlayLoader show={isChartLoading} dim={0.2} blockInteraction={isChartLoading} />
        {isChartLoading ? null : eventsData.length === 0 ? (
          <h1 style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
            No Data Available
          </h1>
        ) : (
          <EventsChart ref={chartRef} data={eventsData} height={400} />
        )}
      </ChartCard>
    </Box>
  );
}
