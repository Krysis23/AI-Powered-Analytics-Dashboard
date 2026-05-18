import pytest
import pandas as pd
import numpy as np
from utils.cleaner import clean,CleaningReport


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Alice",None, "Eve"],
        "age": [25,30,25,28,None],
        "salary": [50000,60000,50000,55000,70000],
        "city": ["Mumbai", "Delhi", "Mumbai", "Pune","Chennai"],
        "user_id": ["u001","u002","u001","u004"],
        "junk_col": [None,None,None,None,None],
    })


def test_drops_high_missing_column(sample_df):
    config = {"null_threshold": 80}
    cleaned, report = clean(sample_df, config)
    assert "junk_col" not in cleaned.columns
    assert "junk_col" in report.cols_dropped

def test_removes_duplicates(sample_df):
    config = {"drop_duplicate_rows": True}
    cleaned, report = clean(sample_df, config)
    assert len(cleaned) < len(sample_df)
    assert any("duplicate" in s for s in report.steps)


def test_fills_numeric_nulls_median(sample_df):
    config = {"null_strategy": "fill_median", "drop_duplicate_rows": False}
    cleaned, report = clean(sample_df, config)
    assert cleaned["age"].isna().sum() == 0
    assert "age" in report.nulls_filled


def test_fills_numeric_nulls_mean(sample_df):
    config = {"null_strategy": "fill_mean", "drop_duplicate_rows": False}
    cleaned, report = clean(sample_df, config)
    assert cleaned["age"].isna().sum() == 0


def test_fills_numeric_nulls_zero(sample_df):
    config = {"null_strategy": "fill_zero", "drop_duplicate_rows": False}
    cleaned, report = clean(sample_df, config)
    assert cleaned["age"].isna().sum() == 0


def test_drops_id_columns(sample_df):
    config = {"drop_id_cols": True, "drop_duplicate_rows": False}
    cleaned, report = clean(sample_df, config)
    assert "user_id" not in cleaned.columns

def test_strips_whitespace():
    df = pd.DataFrame({"city": ["  Mumbai  ", " Delhi", "Pune  "]})
    config = {"strip_whitespace": True, "drop_duplicate_rows": False}
    cleaned, _ = clean(df, config)
    assert cleaned["city"].tolist() == ["Mumbai", "Delhi", "Pune"]

def test_remove_outliers():
    df = pd.DataFrame({"value": [10,11,10,12,10,1000]})
    config = {"remove_outliers": True, "outlier_z_threshold": 2.0, "drop_duplicate_rows": False}
    cleaned, report = clean(df,config)
    assert 1000 not in cleaned["value"].values
    assert any("outlier" in s for s in report.steps)


def test_report_row_counts(sample_df):
    config = {"drop_duplicate_rows": True}
    cleaned, report = clean(sample_df, config)
    assert report.rows_before == len(sample_df)
    assert report.rows_after == len(cleaned)

def test_empty_dataframe():
    df = pd.DataFrame({"a": [], "b": []})
    config = {}
    cleaned, report = clean(df, config)
    assert len(cleaned) == 0

