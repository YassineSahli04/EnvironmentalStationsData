from user import  get_all_stations
from station import get_all_station_sensors, get_station_data_in_timestamp
from datetime import datetime, timezone
from data_handeling import transform_data_to_df_or_csv, combine_dfs_with_same_timestamp

stations = get_all_stations()


start = int(datetime(2025, 9, 15, 23, 0, 0,tzinfo=timezone.utc).timestamp())
end = int(datetime(2025, 9, 20, 23, 0, 0, tzinfo=timezone.utc).timestamp())

dfs = []
for st in stations:
    id = st["name"]["original"]
    st_dataJsonObject = get_station_data_in_timestamp(id, "hourly", start, end)

    st_df = transform_data_to_df_or_csv(st_dataJsonObject)
    dfs.append(st_df)

final_df = combine_dfs_with_same_timestamp(dfs)

final_df.to_csv("test.csv", index=False)