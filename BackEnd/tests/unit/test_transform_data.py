import pandas as pd
import pytest

from BackEnd.Utils.TransformData import TransformData


def _make_multi_col_df(time_values, data_col_name, data_values):
    """Build a DataFrame with MultiIndex columns like (\"date_time\",\"\") and (col, \"\")."""
    cols = pd.MultiIndex.from_tuples([("date_time", ""), (data_col_name, "")])
    df = pd.DataFrame({"dt": time_values, "val": data_values})
    df.columns = cols
    return df


class TestCombineDfsWithSameTimestamp:
    def test_happy_path(self):
        times = pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00", "2025-01-01 02:00"])
        df1 = _make_multi_col_df(times, "temp", [10, 20, 30])
        df2 = _make_multi_col_df(times, "humidity", [50, 60, 70])

        result = TransformData.combine_dfs_with_same_timestamp([df1, df2])
        assert ("temp", "") in result.columns
        assert ("humidity", "") in result.columns
        assert len(result) == 3

    def test_mismatched_start_raises(self):
        t1 = pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00"])
        t2 = pd.to_datetime(["2025-01-01 00:30", "2025-01-01 01:30"])
        df1 = _make_multi_col_df(t1, "a", [1, 2])
        df2 = _make_multi_col_df(t2, "b", [3, 4])

        with pytest.raises(ValueError, match="starts at"):
            TransformData.combine_dfs_with_same_timestamp([df1, df2])

    def test_mismatched_step_raises(self):
        t1 = pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00"])
        t2 = pd.to_datetime(["2025-01-01 00:00", "2025-01-01 02:00"])
        df1 = _make_multi_col_df(t1, "a", [1, 2])
        df2 = _make_multi_col_df(t2, "b", [3, 4])

        with pytest.raises(ValueError, match="step"):
            TransformData.combine_dfs_with_same_timestamp([df1, df2])


class TestCombineDfsWithDiffTimestamp:
    def test_happy_path(self):
        ts1 = [1_700_000_000_000, 1_700_000_060_000]  # ms epoch, ~1 min apart
        ts2 = [1_700_000_030_000, 1_700_000_090_000]
        df1 = pd.DataFrame({"DATE_TIME": ts1, "temp": [10.0, 20.0]})
        df2 = pd.DataFrame({"DATE_TIME": ts2, "humidity": [50.0, 60.0]})

        result = TransformData.combine_dfs_with_diff_timestamp([df1, df2])
        assert "DATE_TIME" in result.columns
        assert "temp" in result.columns
        assert "humidity" in result.columns

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="empty"):
            TransformData.combine_dfs_with_diff_timestamp([])

    def test_bad_timestamp_raises(self):
        df = pd.DataFrame({"DATE_TIME": [100, 200], "val": [1.0, 2.0]})
        with pytest.raises(ValueError, match="Timestamp conversion failed"):
            TransformData.combine_dfs_with_diff_timestamp([df])


class TestCombineDfBatchesWithSameColumns:
    def test_happy_path(self):
        df1 = pd.DataFrame({
            "date_time": pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00"]),
            "temp": [10.0, 20.0],
        })
        df2 = pd.DataFrame({
            "date_time": pd.to_datetime(["2025-01-01 01:00", "2025-01-01 02:00"]),
            "temp": [22.0, 30.0],
        })

        result = TransformData.combine_df_batches_with_same_columns([df1, df2])
        assert len(result) == 3
        overlap_row = result[result["date_time"] == pd.Timestamp("2025-01-01 01:00", tz="UTC")]
        assert overlap_row["temp"].iloc[0] == pytest.approx(21.0)

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="empty"):
            TransformData.combine_df_batches_with_same_columns([])
