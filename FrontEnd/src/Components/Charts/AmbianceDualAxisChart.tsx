import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import type { SensorDataRow } from "../../Api/Objects/StationObj";

type Props = {
  data: SensorDataRow[];
  height?: number;
  title?: string;
};

function toNumberOrNull(v: unknown): number | null {
  if (v === null || v === undefined) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export default function AmbianceDualAxisChart({ data, height = 360, title = "Ambiance" }: Props) {
  const option = useMemo(() => {
    const x = data.map((d) => d.time);

    const seriesT = data.map((d) => toNumberOrNull(d.values["Temperature"]));
    const seriesHR = data.map((d) => toNumberOrNull(d.values["Relative Humidity"]));
    const seriesRg = data.map((d) => toNumberOrNull(d.values["Solar Radiation"]));

    return {
      backgroundColor: "transparent",
      title: {
        text: title,
        left: "left",
        top: 4,
        textStyle: { fontSize: 14, fontWeight: 600 },
      },
      grid: { left: 52, right: 52, top: 46, bottom: 44 },
      legend: {
        top: 20,
        left: "left",
        itemGap: 14,
        textStyle: { fontSize: 12 },
      },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross" },
        // Nice compact tooltip with units
        valueFormatter: (value: unknown) => {
          if (value === null || value === undefined) return "—";
          const n = Number(value);
          return Number.isFinite(n) ? String(n) : "—";
        },
      },
      toolbox: {
        right: 8,
        top: 6,
        feature: {
          dataZoom: { yAxisIndex: "none" },
          restore: {},
          saveAsImage: {},
        },
      },
      dataZoom: [
        { type: "inside", xAxisIndex: 0, filterMode: "none" },
        { type: "slider", xAxisIndex: 0, height: 18, bottom: 6 },
      ],
      xAxis: {
        type: "time",
        boundaryGap: false,
        axisLabel: { hideOverlap: true },
      },
      yAxis: [
        {
          type: "value",
          name: "°C / W·m⁻²",
          nameGap: 34,
          axisLabel: {
            formatter: (v: number) => `${v}`,
          },
          splitLine: { show: true },
        },
        {
          type: "value",
          name: "% HR",
          nameGap: 34,
          min: 0,
          max: 100,
          axisLabel: {
            formatter: (v: number) => `${v}%`,
          },
          splitLine: { show: false },
        },
      ],
      // Keep animations smooth but not heavy
      animationDuration: 250,
      series: [
        {
          name: "Rayonnement (Rg)",
          type: "line",
          yAxisIndex: 0,
          data: x.map((ts, i) => [ts, seriesRg[i]]),
          showSymbol: false,
          smooth: true,
          lineStyle: { width: 2, opacity: 0.55 },
          areaStyle: { opacity: 0.12 },
          emphasis: { focus: "series" },
          // keep it visually “background”
          z: 1,
        },
        {
          name: "Température (T)",
          type: "line",
          yAxisIndex: 0,
          data: x.map((ts, i) => [ts, seriesT[i]]),
          showSymbol: false,
          smooth: true,
          lineStyle: { width: 2.5 },
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
          lineStyle: { width: 2.5 },
          emphasis: { focus: "series" },
          z: 2,
        },
      ],
    };
  }, [data, title]);

  return (
    <ReactECharts
      option={option}
      style={{ height, width: "100%" }}
      notMerge={true}
      lazyUpdate={true}
    />
  );
}
