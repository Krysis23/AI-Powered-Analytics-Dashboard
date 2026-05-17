import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict

from utils.profiler import profile_dataframe


@dataclass
class CleaningReport:
    rows_before: int= 0
    rows_after: int=0
    cols_before: int=0
    cols_after: int=0
    steps: List[str]  = field(default_factory=list)
    cols_dropped: List[str]  = field(default_factory=list)
    nulls_filled: Dict[str, int]  = field(default_factory=dict)
    dtypes_changed: Dict[str, int]  = field(default_factory=dict)

    def to_dict(self)-> dict:
        return{
            "rows_before":  self.rows_before,
            "rows_after":  self.rows_after,
            "cols_before":  self.cols_before,
            "cols_after":  self.cols_after,
            "steps":  self.steps,
            "cols_dropped":  self.cols_dropped,
            "nulls_filled":  self.nulls_filled,
            "dtypes_changed":  self.dtypes_changed
        }
    
def clean(df:pd.DataFrame, config:dict) -> tuple[pd.DataFrame, CleaningReport]:
    report = CleaningReport(
        rows_before=len(df),
        rows_after=len(df.columns)
    )
    df = df.copy()
    if config.get("standardize_columns", False):
        new_names = {
            c: c.strip().lower().replace(" ", "_").replace("-","_")
            for c in df.columns
        }
        df.rename(columns=new_names, inplace=True)
        report.steps.append("Standardized column names to lowercase_underscore")

    if config.get("strip_whitespace",True):
        str_cols = df.select_dtypes(include=object).columns
        for col in str_cols:
            df[col] = df[col].str.strip()
        if len(str_cols):
            report.steps.append(f"Stripped whitespace from {len(str_cols)} text columns")
    
    null_threshold = config.get("null_threshold", 60)
    missing_rates = df.isna().mean()*100
    drop_cols = missing_rates[missing_rates > null_threshold].index.tolist()
    if drop_cols:
        df.drop(columns=drop_cols, inplace=True)
        report.cols_dropped.extend(drop_cols)
        report.steps.append(
            f"Dropped {len(drop_cols)} column(s) with > {null_threshold}% missing: "
            f"{drop_cols}"
        )

    if config.get("drop_duplicate_rows", True):
        before = len(df)
        df.drop_duplicates(inplace=True)
        removed = before  - len(df)
        if removed:
            report.steps.append(f"Removed {removed:,} duplicate rows")
        else:
            report.steps.append("No duplicate rows found")

    if config.get("parse_dates", True):
        profiles = profile_dataframe(df)
        for p in profiles:
            if p.inferred_type == "datetime" and p.name in df.columns:
                try:
                    df[p.name] = pd.to_datetime(
                        df[p.name], infer_datetime_format=True,errors="coerce"
                    )
                    report.dtypes_changed[p.name] = "datetime64"
                    report.steps.append(f"Parsed '{p.name}' as datetime")
                except Exception:
                    pass
    
    if config.get("drop_id_cols", True):
        if config.get("drop_id_cols", True):
            profiles = profile_dataframe(df)
            id_cols = [p.name for p in profiles if p.inferred_type == "id"]
            if id_cols:
                df.drop(columns=id_cols, inplace=True)
                report.cols_dropped.extend(id_cols)
                report.steps.append(f"Dropped ID-like columns: {id_cols}")

    
    strategy = config.get("null_strategy", "fill_median")
    numeric_cols = df.select_dtypes(include="number").columns


    for col in numeric_cols:
        n_null = int(df[col].isna().sum())
        if n_null == 0:
            continue


        if strategy == "fill_mean":
            fill_val = df[col].mean()
            df[col].fillna(round(fill_val, 4), inplace=True)
        elif strategy == "fill_median":
            fill_val = df[col].median()
            df[col].fillna(fill_val, inplace=True)
        elif strategy == "fill_zero":
            df[col].fillna(0,inplace=True)
        elif strategy == "drop_rows":
            df.dropna(subset=[col], inplace=True)

        report.nulls_filled[col] = n_null

    
    if report.nulls_filled:
        total_filled = sum(report.nulls_filled.values())
        report.steps.append(
            f"Filled {total_filled:,} misisng numeric value(s) using '{strategy}'"
        )


    
    cat_cols = df.select_dtypes(include="object").columns
    cat_filled = {}
    for col in cat_cols:
        n_null = int(df[col].isna().sum())
        if n_null == 0:
            continue
        mode = df[col].mode()
        fill_val = mode[0] if not mode.empty else "Unknown"
        df[col].fillna(fill_val, inplace=True)
        cat_filled[col] = n_null


    if cat_filled:
        report.steps.append(
            f"Filled {sum(cat_filled.values()):,} missing categorical value(s) with column mode"
        )
        report.nulls_filled.filled.update(cat_filled)

    
    if config.get("remove_otuliers", False):
        z_thresh = float(config.get("outlier_z_threshold", 3.0))
        before = len(df)
        num_cols = df.select_dtypes(include="number").columns
        for col in num_cols:
            std = df[col].std()
            if std == 0:
                continue
            z_scores = (df[col] - df[col].mean())/std
            df = df[np.abs(z_scores) < z_thresh]
        removed = before - len(df)

        if removed:
            report.steps.append(
                f"Removed {removed:,} outlier rows(z-score > {z_thresh})"
            )
        else:
            report.steps.append(f"No outliers found at z-threshold {z_thresh}")


    report.rows_after = len(df)
    report.cols_after = len(df.columns)

    if not report.steps:
        report.steps.append("Dataset looks clean - no issues found")
    
    return df,report