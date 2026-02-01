import { useMemo, forwardRef } from "react";
import ReactECharts from "echarts-for-react";
import type { SensorDataRow } from "../../Api/Objects/StationObj";
import {
  extractTimeSeries,
  extractSensorValues,
  buildSeriesData,
  createYAxisOption,
  getBaseChartOptions,
} from "./chartUtils";

type EventsChartProps = {
  data: SensorDataRow[];
  height?: number;
};

const EventsChart = forwardRef<ReactECharts, EventsChartProps>(function EventsChart(
  { data, height = 360 },
  ref
) {
  const option = useMemo(() => {
    const timestamps = extractTimeSeries(data);

    const seriesPrecip = extractSensorValues(data, "Precipitation");
    const seriesWind = extractSensorValues(data, "wind speed");

    const precipColor = "#38bdf8"; // Sky blue for precipitation
    const windColor = "#a78bfa"; // Purple for wind

    const baseOptions = getBaseChartOptions();

    return {
      ...baseOptions,
      yAxis: [
        createYAxisOption(
          {
            name: "mm",
            color: precipColor,
            position: "left",
            formatter: (v: number) => `${v}`,
          },
          true // show split lines on primary axis
        ),
        createYAxisOption(
          {
            name: "m/s",
            color: windColor,
            position: "right",
            formatter: (v: number) => v.toFixed(1),
          },
          false
        ),
      ],
      series: [
        {
          name: "Precipitation",
          type: "bar",
          yAxisIndex: 0,
          data: buildSeriesData(timestamps, seriesPrecip),
          itemStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: precipColor },
                { offset: 1, color: "#0284c7" },
              ],
            },
            borderRadius: [4, 4, 0, 0],
          },
          emphasis: { focus: "series" },
          barMaxWidth: 20,
          z: 1,
        },
        {
          name: "Wind Speed",
          type: "line",
          yAxisIndex: 1,
          data: buildSeriesData(timestamps, seriesWind),
          showSymbol: false,
          smooth: true,
          lineStyle: { width: 2.5, color: windColor },
          itemStyle: { color: windColor },
          areaStyle: {
            opacity: 0.15,
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: windColor },
                { offset: 1, color: "rgba(167, 139, 250, 0)" },
              ],
            },
          },
          emphasis: { focus: "series" },
          z: 2,
        },
      ],
    };
  }, [data]);

  return (
    <ReactECharts
      ref={ref}
      option={option}
      style={{ height, width: "100%" }}
      notMerge={true}
      lazyUpdate={true}
    />
  );
});

export default EventsChart;
