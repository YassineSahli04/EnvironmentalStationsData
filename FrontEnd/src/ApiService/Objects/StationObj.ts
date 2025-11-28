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
}
