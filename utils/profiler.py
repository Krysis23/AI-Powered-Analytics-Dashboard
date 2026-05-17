import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List


@dataclass
class ColumnProfile:
    name: str
    dtype:str
    inferred_type: str
    missing_count: int
    missing_pct: float
    n_unique: int
    min_val: object
    max_val: object
    mean_val: object
    sample_values: List

def infer_type(series: pd.Series)->str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    sample = series.dropna().astype(str).head(50)
    try:
        parsed = pd.to_datetime(sample, infer_datetime_format=True, errors="raise")
        if parsed.notna().mean() > 0.8:
            return "datetime"
    except Exception:
        pass
    n_unique = series.nunique()
    n_total = series.dropna().shape[0]

    if n_total == 0:
        return "categorical"
    
    uniqueness_ratio = n_unique / n_total

    if uniqueness_ratio > 0.9 and n_unique > 20:
        has_spaces = series.dropna().astype(str).str.contains(" ").mean()
        if has_spaces < 0.1:
            return "id"
        return "text"
    if n_unique <= 50:
        return "categorical"
    
    return "text"

def profile_dataframe(df: pd.DataFrame) -> List[ColumnProfile]:
    profiles = []
    for col in df.columns:
        s = df[col]
        itype = infer_type(s)

        if itype == "numeric":
            min_val = round(float(s.min()), 4) if s.notna.any() else None
            max_val = round(float(s.max()), 4) if s.notna.any() else None
            mean_val = round(float(s.mean()), 4) if s.notna.any() else None
        elif itype == "datatime":
            min_val = str(s.min()) if s.notna().any() else None
            max_val = str(s.max()) if s.notna().any() else None
            mean_val = None
        else:
            min_val = max_val = mean_val = None

        missing_count = int(s.isna().sum())
        profiles.append(ColumnProfile(
            name = col,
            dtype = str(s.dtype),
            inferred_type = itype,
            missing_count = missing_count,
            missing_pct = round(missing_count/max(len(s), 1)* 100, 1),
            n_unique = int(s.unique()),
            min_val = min_val,
            max_val = max_val,
            mean_val = mean_val,
            sample_values = [str(v) for v in s.dropna().unique()[:5].tolist()]
        ))
    return profiles

def profile_to_dict(profile: ColumnProfile)-> dict:
    return{
        "name": profile.name,
        "dtype": profile.dtype,
        "inferred_type": profile.inferred_type,
        "missing_count": profile.missing_count,
        "missing_pct": profile.missing_pct,
        "n_unique": profile.n_unique,
        "min_val": profile.min_val,
        "max_val": profile.max_val,
        "mean_val": profile.mean_val,
        "sample_values": profile.sample_values,
    }