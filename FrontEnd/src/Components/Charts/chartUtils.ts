import type { SensorDataRow } from "../../Api/Objects/StationObj";

/**
 * Convert unknown value to number or null
 */
export function toNumberOrNull(v: unknown): number | null {
  if (v === null || v === undefined) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

/**
 * Extract time series data from SensorDataRow array
 */
export function extractTimeSeries(data: SensorDataRow[]): string[] {
  return data.map((d) => d.time);
}

/**
 * Extract sensor values from SensorDataRow array
 */
export function extractSensorValues(
  data: SensorDataRow[],
  sensorKey: string
): (number | null)[] {
  return data.map((d) => toNumberOrNull(d.values[sensorKey]));
}

/**
 * Build series data as [timestamp, value] pairs for ECharts
 */
export function buildSeriesData(
  timestamps: string[],
  values: (number | null)[]
): [string, number | null][] {
  return timestamps.map((ts, i) => [ts, values[i]]);
}

export type SeriesConfig = {
  name: string;
  sensorKey: string;
  color: string;
  yAxisIndex: number;
  lineWidth?: number;
  zIndex?: number;
  areaStyle?: boolean;
};

export type YAxisConfig = {
  name: string;
  color: string;
  position: "left" | "right";
  offset?: number;
  min?: number;
  max?: number;
  formatter?: (v: number) => string;
};

/**
 * Create a y-axis configuration for ECharts
 */
export function createYAxisOption(config: YAxisConfig, showSplitLine = false) {
  return {
    type: "value" as const,
    name: config.name,
    nameLocation: "middle" as const,
    nameGap: config.offset ? 55 : 50,
    nameTextStyle: { color: config.color, fontWeight: 600, fontSize: 13 },
    position: config.position,
    offset: config.offset,
    min: config.min,
    max: config.max,
    axisLabel: {
      formatter: config.formatter ?? ((v: number) => `${v}`),
      color: config.color,
    },
    axisLine: { show: true, lineStyle: { color: config.color, width: 2 } },
    splitLine: showSplitLine
      ? { show: true, lineStyle: { color: "rgba(71, 85, 105, 0.3)", type: "dashed" as const } }
      : { show: false },
  };
}

/**
 * Create a line series configuration for ECharts
 */
export function createLineSeries(
  config: SeriesConfig,
  timestamps: string[],
  data: SensorDataRow[]
) {
  const values = extractSensorValues(data, config.sensorKey);
  const seriesData = buildSeriesData(timestamps, values);

  const series: Record<string, unknown> = {
    name: config.name,
    type: "line",
    yAxisIndex: config.yAxisIndex,
    data: seriesData,
    showSymbol: false,
    smooth: true,
    lineStyle: { width: config.lineWidth ?? 2.5, color: config.color },
    itemStyle: { color: config.color },
    emphasis: { focus: "series" },
    z: config.zIndex ?? 1,
  };

  if (config.areaStyle) {
    series.areaStyle = {
      opacity: 0.2,
      color: {
        type: "linear",
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [
          { offset: 0, color: config.color },
          { offset: 1, color: config.color.replace(/[^,]+\)$/, "0)").replace("#", "rgba(") },
        ],
      },
    };
  }

  return series;
}

/**
 * Base chart options shared across all time series charts
 */
export function getBaseChartOptions() {
  return {
    grid: { left: 80, right: 120, top: 50, bottom: 100 },
    legend: {
      bottom: 5,
      textStyle: { fontSize: 12, color: "#cbd5e1" },
    },
    tooltip: {
      trigger: "axis" as const,
      axisPointer: {
        type: "cross" as const,
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
      { type: "inside" as const, xAxisIndex: 0, filterMode: "none" as const },
      {
        type: "slider" as const,
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
      type: "time" as const,
      boundaryGap: false,
      axisLabel: {
        hideOverlap: true,
        color: "#94a3b8",
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
      splitLine: {
        show: true,
        lineStyle: { color: "rgba(71, 85, 105, 0.4)", type: "dashed" as const },
      },
    },
    animationDuration: 250,
  };
}

