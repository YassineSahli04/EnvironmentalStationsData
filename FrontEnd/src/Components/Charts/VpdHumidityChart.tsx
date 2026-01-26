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

type VpdHumidityChartProps = {
  data: SensorDataRow[];
  height?: number;
};

const VpdHumidityChart = forwardRef<ReactECharts, VpdHumidityChartProps>(
  function VpdHumidityChart({ data, height = 360 }, ref) {
    const option = useMemo(() => {
      const timestamps = extractTimeSeries(data);

      const seriesVpd = extractSensorValues(data, "VPD");
      const seriesHR = extractSensorValues(data, "Relative Humidity");

      const vpdColor = "#f472b6"; // Pink for VPD
      const humidityColor = "#22d3ee"; // Cyan for humidity

      const baseOptions = getBaseChartOptions();

      return {
        ...baseOptions,
        yAxis: [
          createYAxisOption(
            {
              name: "kPa",
              color: vpdColor,
              position: "left",
              formatter: (v: number) => v.toFixed(2),
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
        ],
        series: [
          {
            name: "VPD",
            type: "line",
            yAxisIndex: 0,
            data: buildSeriesData(timestamps, seriesVpd),
            showSymbol: false,
            smooth: true,
            lineStyle: { width: 2.5, color: vpdColor },
            itemStyle: { color: vpdColor },
            emphasis: { focus: "series" },
            areaStyle: {
              opacity: 0.15,
              color: {
                type: "linear",
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: vpdColor },
                  { offset: 1, color: "rgba(244, 114, 182, 0)" },
                ],
              },
            },
            z: 2,
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

export default VpdHumidityChart;

