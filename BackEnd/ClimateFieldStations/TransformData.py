import pandas as pd

class TransformData:

    @staticmethod
    def transform_data_to_df_or_csv(dataJsonObject,isCsv = False):
        cols = [('Date/Time', "")]
        sensorsData = dataJsonObject["data"]
        
        for sensorData in sensorsData:
            if sensorData['type'] != 'Sensor':
                break
            colP1 = sensorData['name']
            cols += [(colP1, v) for v in sensorData['values']]

        columns = pd.MultiIndex.from_tuples(cols, names=["sensor", "metric"])

        dataVals = []
        for i in range(len(dataJsonObject["dates"])):
            row = []
            dt = dataJsonObject["dates"][i]
            row.append(dt)
            for sensorData in sensorsData:
                if sensorData['type'] != 'Sensor':
                    break
                for valType in sensorData['values']:
                    row.append(sensorData['values'][valType][i])
            dataVals.append(row)
        df = pd.DataFrame(dataVals, columns=columns)
        df[("Date/Time", "")] = pd.to_datetime(df[("Date/Time", "")], utc=True)
        
        if isCsv: df.to_csv("test.csv", index=False); return;
        return df 

    @staticmethod
    def combine_dfs_with_same_timestamp(dfs):
        ref_time = dfs[0][("Date/Time", "")]
        ref_start = ref_time.iloc[0]
        ref_step = ref_time.diff().dropna().iloc[0]

        for idx, df in enumerate(dfs[1:], start=2):
            ts = df[("Date/Time", "")]
            start = ts.iloc[0]
            step = ts.diff().dropna().iloc[0]

            if start != ref_start:
                raise ValueError(f"DataFrame #{idx} starts at {start}, expected {ref_start}")

            if step != ref_step:
                raise ValueError(f"DataFrame #{idx} step {step}, expected {ref_step}")
        dfs_idxed = [df.set_index(("Date/Time", "")) for df in dfs]
        merged = pd.concat(dfs_idxed, axis=1).reset_index()
        merged.columns.names = dfs[0].columns.names
        return merged
    
    @staticmethod
    def combine_dfs_with_diff_timestamp(dfs, time_col="DATE_TIME"):
        """
        - Rounds timestamps to the nearest minute
        - For rows that land on the same rounded timestamp in a df,
        keeps a single row with the average of numeric columns
        - Aligns all dfs on the union of all timestamps (outer join)
        - If a df has no data at a given timestamp -> NaN
        """
        if not dfs:
            raise ValueError("dfs list is empty")

        aligned = []

        for df in dfs:
            tmp = df.copy()

            tmp[time_col] = pd.to_datetime(tmp[time_col], unit="ms", origin="unix", utc=True)

            tmp[time_col] = tmp[time_col].dt.round("min")
            
            # guard rail to check timestamp conversion
            if tmp[time_col].dt.year.min() < 2000:
                raise ValueError("Timestamp conversion failed: likely wrong unit")

            tmp = (
                tmp.groupby(time_col, as_index=True)
                .mean(numeric_only=True)
            )

            aligned.append(tmp)

        merged = pd.concat(aligned, axis=1, join="outer").sort_index().reset_index()
        merged.rename(columns={merged.columns[0]: time_col}, inplace=True)

        return merged