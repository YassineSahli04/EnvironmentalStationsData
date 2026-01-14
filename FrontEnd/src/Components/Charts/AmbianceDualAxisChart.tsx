import { useMemo, forwardRef } from "react";
import ReactECharts from "echarts-for-react";
import type { SensorDataRow } from "../../Api/Objects/StationObj";

type AmbianceDualAxisChartProps = {
  data: SensorDataRow[];
  height?: number;
};

function toNumberOrNull(v: unknown): number | null {
  if (v === null || v === undefined) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

const AmbianceDualAxisChart = forwardRef<ReactECharts, AmbianceDualAxisChartProps>(
  function AmbianceDualAxisChart({ data, height = 360 }, ref) {
    const option = useMemo(() => {
      const x = data.map((d) => d.time);

      const seriesT = data.map((d) => toNumberOrNull(d.values["Temperature"]));
      const seriesHR = data.map((d) => toNumberOrNull(d.values["Relative Humidity"]));
      const seriesRg = data.map((d) => toNumberOrNull(d.values["Solar Radiation"]));

      const tempColor = "#f97316";
      const humidityColor = "#22d3ee";
      const radiationColor = "#a3e635";

      return {
        grid: { left: 80, right: 120, top: 50, bottom: 100 },
        legend: {
          bottom: 5,
          textStyle: { fontSize: 12, color: "#cbd5e1" },
        },
        tooltip: {
          trigger: "axis",
          axisPointer: {
            type: "cross",
            crossStyle: { color: "#94a3b8" },
          },
          backgroundColor: "rgba(15, 23, 42, 0.92)",
          borderColor: "rgba(148, 163, 184, 0.2)",
          borderRadius: 8,
          textStyle: { color: "#f1f5f9" },
          valueFormatter: (value: unknown) => {
            if (value === null || value === undefined) return "—";
            const n = Number(value);
            return Number.isFinite(n) ? String(n) : "—";
          },
        },
        toolbox: {
          left: 0,
          top: -10,
          iconStyle: { borderColor: "#94a3b8" },
          emphasis: { iconStyle: { borderColor: "#f1f5f9" } },
          feature: {
            dataZoom: { yAxisIndex: "none" },
            restore: {},
            saveAsImage: {},
          },
        },
        dataZoom: [
          { type: "inside", xAxisIndex: 0, filterMode: "none" },
          {
            type: "slider",
            xAxisIndex: 0,
            height: 24,
            bottom: 45,
            backgroundColor: "rgba(30, 41, 59, 0.6)",
            borderColor: "rgba(148, 163, 184, 0.2)",
            fillerColor: "rgba(59, 130, 246, 0.3)",
            handleStyle: { color: "#3b82f6", borderColor: "#60a5fa" },
            moveHandleStyle: { color: "#3b82f6" },
            textStyle: { color: "#94a3b8" },
            dataBackground: {
              lineStyle: { color: "rgba(148, 163, 184, 0.3)" },
              areaStyle: { color: "rgba(148, 163, 184, 0.1)" },
            },
          },
        ],
        xAxis: {
          type: "time",
          boundaryGap: false,
          axisLabel: {
            hideOverlap: true,
            color: "#94a3b8",
            // Smart formatting based on time granularity
            formatter: {
              year: "{yyyy}",
              month: "{MMM} {yyyy}",
              day: "{MMM} {d}",
              hour: "{MMM} {d} {HH}h",
              minute: "{HH}:{mm}",
              second: "{HH}:{mm}:{ss}",
            },
          },
          axisLine: { lineStyle: { color: "#475569" } },
          splitLine: { show: true, lineStyle: { color: "rgba(71, 85, 105, 0.4)", type: "dashed" } },
        },
        yAxis: [
          {
            type: "value",
            name: "°C",
            nameLocation: "middle",
            nameGap: 50,
            nameTextStyle: { color: tempColor, fontWeight: 600, fontSize: 13 },
            position: "left",
            axisLabel: {
              formatter: (v: number) => `${v}`,
              color: tempColor,
            },
            axisLine: { show: true, lineStyle: { color: tempColor, width: 2 } },
            splitLine: {
              show: true,
              lineStyle: { color: "rgba(71, 85, 105, 0.3)", type: "dashed" },
            },
          },
          {
            type: "value",
            name: "% HR",
            nameLocation: "middle",
            nameGap: 50,
            nameTextStyle: { color: humidityColor, fontWeight: 600, fontSize: 13 },
            position: "right",
            min: 0,
            max: 100,
            axisLabel: {
              formatter: (v: number) => `${v}%`,
              color: humidityColor,
            },
            axisLine: { show: true, lineStyle: { color: humidityColor, width: 2 } },
            splitLine: { show: false },
          },
          {
            type: "value",
            name: "W·m⁻²",
            nameLocation: "middle",
            nameGap: 55,
            nameTextStyle: { color: radiationColor, fontWeight: 600, fontSize: 13 },
            position: "right",
            offset: 80,
            axisLabel: {
              formatter: (v: number) => `${v}`,
              color: radiationColor,
            },
            axisLine: { show: true, lineStyle: { color: radiationColor, width: 2 } },
            splitLine: { show: false },
          },
        ],
        animationDuration: 250,
        series: [
          {
            name: "Température (T)",
            type: "line",
            yAxisIndex: 0,
            data: x.map((ts, i) => [ts, seriesT[i]]),
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
            data: x.map((ts, i) => [ts, seriesHR[i]]),
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
            data: x.map((ts, i) => [ts, seriesRg[i]]),
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
