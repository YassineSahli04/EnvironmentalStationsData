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

type AmbianceDualAxisChartProps = {
  data: SensorDataRow[];
  height?: number;
};

const AmbianceDualAxisChart = forwardRef<ReactECharts, AmbianceDualAxisChartProps>(
  function AmbianceDualAxisChart({ data, height = 360 }, ref) {
    const option = useMemo(() => {
      const timestamps = extractTimeSeries(data);

      const seriesT = extractSensorValues(data, "Temperature");
      const seriesHR = extractSensorValues(data, "Relative Humidity");
      const seriesRg = extractSensorValues(data, "Solar Radiation");

      const tempColor = "#f97316";
      const humidityColor = "#22d3ee";
      const radiationColor = "#a3e635";

      const baseOptions = getBaseChartOptions();

      return {
        ...baseOptions,
        yAxis: [
          createYAxisOption(
            {
              name: "°C",
              color: tempColor,
              position: "left",
            },
            true // show split lines on primary axis
          ),
          createYAxisOption(
            {
              name: "% HR",
              color: humidityColor,
              position: "right",
              min: 0,
              max: 100,
              formatter: (v: number) => `${v}%`,
            },
            false
          ),
          createYAxisOption(
            {
              name: "W·m⁻²",
              color: radiationColor,
              position: "right",
              offset: 80,
            },
            false
          ),
        ],
        series: [
          {
            name: "Température (T)",
            type: "line",
            yAxisIndex: 0,
            data: buildSeriesData(timestamps, seriesT),
            showSymbol: false,
            smooth: true,
            lineStyle: { width: 2.5, color: tempColor },
            itemStyle: { color: tempColor },
            emphasis: { focus: "series" },
            z: 3,
          },
          {
            name: "Humidité (HR)",
            type: "line",
            yAxisIndex: 1,
            data: buildSeriesData(timestamps, seriesHR),
            showSymbol: false,
            smooth: true,
            lineStyle: { width: 2.5, color: humidityColor },
            itemStyle: { color: humidityColor },
            emphasis: { focus: "series" },
            z: 2,
          },
          {
            name: "Rayonnement (Rg)",
            type: "line",
            yAxisIndex: 2,
            data: buildSeriesData(timestamps, seriesRg),
            showSymbol: false,
            smooth: true,
            lineStyle: { width: 2, color: radiationColor },
            itemStyle: { color: radiationColor },
            areaStyle: {
              opacity: 0.2,
              color: {
                type: "linear",
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: radiationColor },
                  { offset: 1, color: "rgba(163, 230, 53, 0)" },
                ],
              },
            },
            emphasis: { focus: "series" },
            z: 1,
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
  }
);

export default AmbianceDualAxisChart;
