export interface SensorDataRow {
  time: string;
  values: Record<string, number | null>;
}
export interface StationSensorObj {
  sensorName: string;
  sensorId: string;
  type: string;
  decimals: number;
  unit: string;
  aggregationsType: string[];
  data: SensorDataRow[];
}

export type StationStatus = "online" | "offline";

export interface StationObj {
  Id: string;
  Name: string | null;
  Location: string | null;
  Manufacturer: string | null;
  Type: string | null;
  Latitude: number | null;
  Longitude: number | null;
  Altitude: number | null;
  DataSourceId: number | null;
  DataTableName: string | null;

  LastDataTimestamp: string;
  SensorList: StationSensorObj[];
  DataFrequency: string;

  // UI Only
  Status: StationStatus;
}
