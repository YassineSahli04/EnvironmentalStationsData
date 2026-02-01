export interface SensorDataRow {
  time: string;
  values: Record<string, number | null>;
}
export interface StationSensorObj {
  sensor: string;
  unit: string;
  aggregationsType: string[];
  data: SensorDataRow[];
}

export type StationStatus = "Online" | "Offline";

export interface StationObj {
  Id: number;
  Name: string | null;
  Location: string | null;
  Manufacturer: string | null;
  Type: string | null;
  Latitude: number | null;
  Longitude: number | null;
  Altitude: number | null;
  DataSourceId: number | null;
  DataTableName: string | null;

  LastDataPointTime: string;
  SensorsList: StationSensorObj[];
  DataFrequency: string;

  // UI Only
  State: StationStatus;
}
