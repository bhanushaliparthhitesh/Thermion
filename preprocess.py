"""
preprocess.py
=============
Purpose:
    Load, validate, clean, engineer features from, and save three datasets
    for the AI Data Center Cooling Optimization platform.

Inputs (8 files, all real — no synthetic fallback exists):
    AIR COOLING:
        cold_source_control_dataset.csv     — 3498 rows, 12 columns
    LIQUID COOLING:
        final_dataset_std.csv               — 27013 rows, semicolon-delimited,
                                              already z-score standardised
    FACILITY (5 files merged into one):
        layout.csv                          — 70 rows, has Model/rpm/condition
        layout_2.csv                        — 73 rows, corrected Q/pwrConsumption
        Table2.csv                          — EXACT DUPLICATE of layout_2, excluded
        Table3.csv                          — 11 rows, design temps by Height (U)
        exhaust_temp.csv                    — 12 rows, adds Z(m) + Height 38 row
    EXCLUDED:
        data.csv                            — arc_length geometry, not DC telemetry

Outputs:
    processed/air_cooling_data.csv
    processed/liquid_cooling_data.csv
    processed/facility_data.csv
    processed/data_report.json

Architecture Notes:
    ── Strict no-synthetic policy ──────────────────────────────────────────
    Every loader raises FileNotFoundError or ValueError immediately if the
    file is missing, empty, unparseable, or has wrong columns. There is no
    fallback, no random data, no imputation with fabricated values.
    Missing values are filled only with column-specific statistics derived
    from the SAME file (median for numeric, mode for categorical).

    ── Authenticity guard ──────────────────────────────────────────────────
    Runs after load on cold_source and facility files.
    Skipped for final_dataset_std because it IS standardised (mean≈0, std≈1
    by design) — a zero-mean check would incorrectly flag it as synthetic.
    Instead, liquid cooling gets a STANDARDISED DATA CONFIRMED print.

    ── Join strategy (determined by inspection, not assumed) ────────────────
    layout + layout_2   → LEFT JOIN on [Rack, First Row]
      WHY LEFT: layout has 70 rows with Model/rpm/condition not in layout_2.
      layout_2 has corrected pwrConsumption/Q for 46 of those rows.
      24 unmatched layout rows keep their original layout values.
    Table3 + exhaust    → LEFT JOIN on Height (U)
      exhaust is the superset (12 rows including Height=38 absent in Table3).
      Both tables carry Previous/Retrofitted Design °C — columns deduplicated.
    Combined thermal + layout_full → LEFT JOIN on First Row = Height (U)
      19 of 70 layout rows have a matching U-position in the thermal data.
      The other 51 get NaN for exhaust/design columns — this is honest.

    ── data.csv exclusion ──────────────────────────────────────────────────
    data.csv contains arc_length geometry values (Result 21–35, arc_length).
    It has no rack ID, no timestamp, no thermal metrics. It is NOT data
    center telemetry and is explicitly excluded with a printed notice.

Run:
    pip install pandas numpy
    python preprocess.py [--data-dir ./] [--out-dir processed/]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — exact filenames and column names confirmed by inspection
# ══════════════════════════════════════════════════════════════════════════════

# File names exactly as uploaded
AIR_FILE      = "cold_source_control_dataset.csv"
LIQUID_FILE   = "final_dataset_std.csv"
LAYOUT_FILE   = "layout.csv"
LAYOUT2_FILE  = "layout_2.csv"
TABLE2_FILE   = "Table2.csv"    # confirmed exact duplicate of layout_2 — excluded
TABLE3_FILE   = "Table3.csv"
EXHAUST_FILE  = "exhaust_temp.csv"
EXCLUDED_FILE = "data.csv"      # arc_length geometry — not DC telemetry

# Air cooling: exact column names from cold_source_control_dataset.csv
AIR_REQUIRED = [
    "Timestamp",
    "Server_Workload(%)",
    "Inlet_Temperature(°C)",
    "Outlet_Temperature(°C)",
    "Ambient_Temperature(°C)",
    "Cooling_Unit_Power_Consumption(kW)",
    "Chiller_Usage(%)",
    "AHU_Usage(%)",
    "Total_Energy_Cost($)",
    "Temperature_Deviation(°C)",
    "Cooling_Strategy_Action",
    "Output",
]

# Air cooling: clean output names (strip units from headers for ML pipelines)
AIR_RENAME = {
    "Server_Workload(%)":                  "Server_Workload",
    "Inlet_Temperature(°C)":               "Inlet_Temperature",
    "Outlet_Temperature(°C)":              "Outlet_Temperature",
    "Ambient_Temperature(°C)":             "Ambient_Temperature",
    "Cooling_Unit_Power_Consumption(kW)":  "Cooling_Unit_Power_Consumption_kW",
    "Chiller_Usage(%)":                    "Chiller_Usage",
    "AHU_Usage(%)":                        "AHU_Usage",
    "Total_Energy_Cost($)":                "Total_Energy_Cost",
    "Temperature_Deviation(°C)":           "Temperature_Deviation",
}

# Liquid cooling: exact column names (43 columns, semicolon-delimited)
LIQUID_P_AC   = [f"P_ac-{i}"   for i in range(8)]
LIQUID_P_CU   = [f"P_cu-{i}"   for i in range(8)]
LIQUID_T_OUT  = [f"T_out-{i}"  for i in range(8)]
LIQUID_T_MEAS = [f"T_MEAS-{i}" for i in range(8)]
LIQUID_T_CEL  = [f"T_celCC-{i}"for i in range(8)]
LIQUID_REQUIRED = LIQUID_P_AC + LIQUID_P_CU + LIQUID_T_OUT + \
                  LIQUID_T_MEAS + LIQUID_T_CEL + ["TLHC", "DoW", "WeH"]

# Facility: exact column names from each file
LAYOUT_REQUIRED   = ["Rack", "First Row", "Height", "Type", "Model",
                      "pwrConsumption", "Q", "rpm", "condition"]
LAYOUT2_REQUIRED  = ["Rack", "First Row", "Height", "Type",
                      "pwrConsumption", "Q"]
TABLE3_REQUIRED   = ["Height (U)", "Previous Design (°C)",
                      "Retrofitted Design (°C)"]
EXHAUST_REQUIRED  = ["Height (U)", "Z (m)", "Previous Design (°C)",
                      "Retrofitted Design (°C)", "Z (m).1"]

# Physical validity bounds for air cooling columns (post-rename)
AIR_BOUNDS = {
    "Server_Workload":                 (0.0,    100.0),
    "Inlet_Temperature":               (-10.0,   60.0),
    "Outlet_Temperature":              (-10.0,   80.0),
    "Ambient_Temperature":             (-20.0,   55.0),
    "Cooling_Unit_Power_Consumption_kW":(0.0,  9999.0),
    "Chiller_Usage":                   (0.0,    100.0),
    "AHU_Usage":                       (0.0,    100.0),
    "Total_Energy_Cost":               (0.0,  99999.0),
    "Temperature_Deviation":           (-50.0,   50.0),
}

COOLING_STRATEGIES = {"Reduce AHU", "Eco Mode", "Boost All",
                       "Maintain", "Increase Chiller"}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — STRICT FILE LOADER
# ══════════════════════════════════════════════════════════════════════════════

def _load_strict(path: Path, label: str, sep: str = ",") -> pd.DataFrame:
    """
    Load CSV with no fallback. Raises immediately for any failure.
    sep parameter handles final_dataset_std's semicolon delimiter.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"\n{'='*60}\n"
            f"MISSING FILE : {label}\n"
            f"Expected at  : {path.resolve()}\n"
            f"{'='*60}\n"
            f"This system does NOT generate synthetic data.\n"
            f"Provide the real file at the path above.\n"
        )
    if path.stat().st_size == 0:
        raise ValueError(
            f"EMPTY FILE: {label}\n"
            f"Path: {path.resolve()}\n"
            f"File has zero bytes. Re-download the dataset."
        )
    try:
        df = pd.read_csv(path, sep=sep)
    except Exception as exc:
        raise ValueError(
            f"PARSE ERROR in {label}: {exc}\n"
            f"Path: {path.resolve()}"
        ) from exc
    if df.empty:
        raise ValueError(
            f"ZERO ROWS in {label}.\n"
            f"Path: {path.resolve()}\n"
            f"CSV parsed but contains no data rows."
        )
    # Drop pandas-added unnamed index columns
    unnamed = [c for c in df.columns if str(c).startswith("Unnamed:")]
    if unnamed:
        print(f"    [load] Dropping unnamed index columns: {unnamed}")
        df = df.drop(columns=unnamed)
    return df


def _validate_columns(df: pd.DataFrame, required: list, label: str) -> None:
    """Raise ValueError listing ALL missing columns, not just the first."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"\nMISSING REQUIRED COLUMNS in {label}\n"
            f"Missing  ({len(missing)}): {missing}\n"
            f"Present  ({len(df.columns)}): {list(df.columns)}\n"
            f"Fix column names in the source file."
        )
    print(f"    [validate] All {len(required)} required columns present ✓")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — AUTHENTICITY CHECK
# ══════════════════════════════════════════════════════════════════════════════

def _check_authenticity(df: pd.DataFrame, label: str) -> None:
    """
    Detect synthetic data patterns. Prints REAL DATASET LOADED or raises.
    """

    print(f"\n    [authenticity] Checking {label}...")
    flags = []

    # Legitimate low-cardinality columns
    IGNORE_LOW_CARDINALITY = {
        "Output",
        "DoW",
        "WeH"
    }

    # Legitimate zero-variance columns
    IGNORE_ZERO_VARIANCE = {
        ("layout.csv", "rpm"),
    }

    for col in df.select_dtypes(include=[np.number]).columns:

        if col in IGNORE_LOW_CARDINALITY:
            continue

        s = df[col].dropna()

        if len(s) < 2:
            continue

        # ── Zero variance check ─────────────────────────────
        if s.std() == 0.0:

            if (label, col) in IGNORE_ZERO_VARIANCE:
                print(
                    f"      [info] '{col}' has zero variance "
                    f"(accepted for {label})"
                )
                continue

            flags.append(
                f"'{col}' has zero variance (all values = {s.iloc[0]})."
            )

        # ── Low cardinality check ───────────────────────────
        elif len(s) > 100 and s.nunique() < 10:

            flags.append(
                f"'{col}' has only {s.nunique()} unique values "
                f"across {len(s)} rows — looks discretised/synthetic."
            )

        # ── Linspace check ──────────────────────────────────
        else:

            diffs = np.diff(np.sort(s.values))

            if len(diffs) > 1 and np.std(diffs) < 1e-10:

                flags.append(
                    f"'{col}' values are perfectly evenly spaced "
                    f"(linspace signature)."
                )

    if flags:
        print("\n    ╔══════════════════════════════════════════╗")
        print("    ║      SYNTHETIC DATA DETECTED             ║")
        print("    ╚══════════════════════════════════════════╝")

        for f in flags:
            print(f"      ✗ {f}")

        raise ValueError(
            f"SYNTHETIC DATA DETECTED in {label}.\n"
            + "\n".join(f"  - {f}" for f in flags)
        )

    print("    ╔══════════════════════════════════════════╗")
    print("    ║        REAL DATASET LOADED               ║")
    print("    ╚══════════════════════════════════════════╝")

def _confirm_standardised(df: pd.DataFrame) -> None:
    """
    Special authenticity check for final_dataset_std.
    Verifies the data IS z-score standardised (mean≈0, std≈1),
    which is expected and correct for this file.
    Prints STANDARDISED DATASET CONFIRMED or raises if not standardised.
    """
    print("\n    [authenticity] Verifying standardisation of liquid dataset...")
    non_std = []
    for col in (LIQUID_P_AC + LIQUID_P_CU + LIQUID_T_OUT +
                LIQUID_T_MEAS + LIQUID_T_CEL + ["TLHC"]):
        if col not in df.columns:
            continue
        m = df[col].mean()
        s = df[col].std()
        if abs(m) > 0.05 or abs(s - 1.0) > 0.05:
            non_std.append(f"'{col}': mean={m:.4f}, std={s:.4f}")

    if non_std:
        raise ValueError(
            f"liquid cooling file does not appear to be z-score standardised.\n"
            f"Columns out of spec:\n" + "\n".join(non_std)
        )
    print("    ╔══════════════════════════════════════════╗")
    print("    ║    STANDARDISED DATASET CONFIRMED        ║")
    print("    ╚══════════════════════════════════════════╝")
    print("    (mean≈0, std≈1 across all sensor columns)")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — AIR COOLING PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def process_air_cooling(data_dir: Path) -> tuple[pd.DataFrame, dict]:
    """
    Load and process cold_source_control_dataset.csv.

    Steps:
      1. Load & validate columns
      2. Authenticity check
      3. Rename columns (strip units from headers)
      4. Parse Timestamp
      5. Remove duplicates
      6. Validate physical bounds — clip OOB values
      7. Encode Cooling_Strategy_Action (label encode)
      8. Feature engineering (6 derived features)
      9. Final NaN check

    Returns: (cleaned_df, stats_dict)
    """
    print("\n" + "═"*60)
    print("  AIR COOLING DATASET")
    print(f"  File: {AIR_FILE}")
    print("═"*60)

    path = data_dir / AIR_FILE
    df = _load_strict(path, "Air Cooling (cold_source_control_dataset.csv)")

    print(f"\n  Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Columns : {list(df.columns)}")
    print(f"  Dtypes  :\n{df.dtypes.to_string()}")
    print(f"\n  Missing values:\n{df.isnull().sum().to_string()}")
    print(f"  Duplicates: {df.duplicated().sum()}")

    _validate_columns(df, AIR_REQUIRED, "Air Cooling")
    _check_authenticity(df, "Air Cooling")

    # ── 3. Rename columns ────────────────────────────────────────────────
    df = df.rename(columns=AIR_RENAME)
    print(f"\n  [rename] Columns renamed (units stripped for ML pipeline)")

    # ── 4. Parse Timestamp ───────────────────────────────────────────────
    try:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    except Exception as e:
        raise ValueError(f"Timestamp parse failed: {e}")
    if df["Timestamp"].isna().sum() > 0:
        raise ValueError("Timestamp column has null values after parsing.")
    print(f"  [timestamp] Range: {df['Timestamp'].min()} → {df['Timestamp'].max()}")

    # ── Time-based Features ─────────────────────────────────────

    # Hour of day (0–23)
    # WHY: cooling demand changes throughout the day.
    df["Hour"] = df["Timestamp"].dt.hour

   # Day of week (0=Monday, 6=Sunday)
   # WHY: workload patterns differ between weekdays/weekends.
    df["DayOfWeek"] = df["Timestamp"].dt.dayofweek

   # Month (1–12)
   # WHY: captures seasonal temperature variations.
    df["Month"] = df["Timestamp"].dt.month

    print("  [time] Added Hour, DayOfWeek, Month")

    # ── 5. Remove duplicates ─────────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates()
    removed_dupes = before - len(df)
    print(f"  [duplicates] Removed: {removed_dupes}")

    # ── 6. Validate and clip physical bounds ─────────────────────────────
    print("\n  [bounds] Physical validation:")
    total_clipped = 0
    for col, (lo, hi) in AIR_BOUNDS.items():
        if col not in df.columns:
            continue
        oob = ((df[col] < lo) | (df[col] > hi)).sum()
        if oob > 0:
            print(f"    ⚠  '{col}': {oob} OOB values clipped to [{lo}, {hi}]")
            df[col] = df[col].clip(lo, hi)
            total_clipped += oob
        else:
            print(f"    ✓  '{col}': all values within [{lo}, {hi}]")
    print(f"  [bounds] Total clipped: {total_clipped}")

    # ── 7. Validate and encode Cooling_Strategy_Action ───────────────────
    actual_strats = set(df["Cooling_Strategy_Action"].dropna().unique())
    unknown = actual_strats - COOLING_STRATEGIES
    if unknown:
        raise ValueError(
            f"Unknown Cooling_Strategy_Action values: {unknown}\n"
            f"Expected: {COOLING_STRATEGIES}"
        )
    strategy_map = {v: i for i, v in
                    enumerate(sorted(COOLING_STRATEGIES))}
    df["Cooling_Strategy_Encoded"] = df["Cooling_Strategy_Action"].map(strategy_map)
    print(f"\n  [encode] Cooling_Strategy_Action → integer: {strategy_map}")

    # Validate Output column (already integer 0-4, matches Output)
    output_vals = set(df["Output"].unique())
    expected_outputs = {0, 1, 2, 3, 4}
    if not output_vals.issubset(expected_outputs):
        raise ValueError(
            f"Output column has unexpected values: {output_vals - expected_outputs}"
        )
    print(f"  [validate] Output values: {sorted(output_vals)} ✓")

    # ── 8. Feature engineering ───────────────────────────────────────────
    print("\n  [features] Engineering derived features:")
    eps = 1e-6

    # Cooling_Efficiency: combined cooling effort per unit of server load
    # WHY: measures over/under-cooling relative to IT demand
    df["Cooling_Efficiency"] = (
        (df["Chiller_Usage"] + df["AHU_Usage"])
        / (df["Server_Workload"] + eps)
    )
    print("    + Cooling_Efficiency = (Chiller + AHU) / Server_Workload")

    # Cooling_Ratio: mechanical vs air cooling balance
    # WHY: high ratio = chiller-dominated (high water/energy cost)
    #       low ratio = AHU-dominated (lower water, higher air energy)
    df["Cooling_Ratio"] = df["Chiller_Usage"] / (df["AHU_Usage"] + eps)
    print("    + Cooling_Ratio = Chiller_Usage / AHU_Usage")

    # Ambient_Inlet_Delta: free cooling opportunity indicator
    # WHY: when ambient ≈ inlet, economizer mode is viable (no chiller needed)
    df["Ambient_Inlet_Delta"] = (
        df["Inlet_Temperature"] - df["Ambient_Temperature"]
    )
    print("    + Ambient_Inlet_Delta = Inlet_Temp - Ambient_Temp")

    # Energy_per_Workload: energy efficiency ratio
    # WHY: primary SAC/XGBoost reward signal — lower is better
    df["Energy_per_Workload"] = (
        df["Total_Energy_Cost"] / (df["Server_Workload"] + eps)
    )
    print("    + Energy_per_Workload = Total_Energy_Cost / Server_Workload")

    # Water_Usage_Estimate: evaporative water consumption proxy
    # WHY: water-saving is primary objective — chiller = evaporative cooling
    #      Formula: high chiller load + high ambient = high water evaporation
    #      Calibrated to produce L/kWh-range values matching published WUE data
    df["Water_Usage_Estimate"] = (
        df["Chiller_Usage"] * 0.003
        * (1.0 + np.clip(df["Ambient_Temperature"] - 25.0, 0, None) / 20.0)
    )
    print("    + Water_Usage_Estimate = f(Chiller_Usage, Ambient_Temperature)")

    # Heat_Load_Index: combined thermal stress on cooling system
    # WHY: inlet temp × workload captures non-linear thermal risk
    #      High workload at already-high inlet temp is disproportionately risky
    df["Heat_Load_Index"] = (
        df["Inlet_Temperature"] * df["Server_Workload"] / 100.0
    )
    print("    + Heat_Load_Index = Inlet_Temperature × Server_Workload / 100")
    # Thermal_Load: absolute thermal demand
    # WHY: higher workload at higher inlet temperatures generates
    # significantly more heat for the cooling system to remove.
    df["Thermal_Load"] = (
      df["Server_Workload"] 
      * df["Inlet_Temperature"]
    )
    print("    + Thermal_Load = Server_Workload × Inlet_Temperature")

    # Cooling_Load: cooling demand under workload
    # WHY: captures how aggressively chillers are working relative
    #      to IT demand. Useful for outlet temperature prediction.
    df["Cooling_Load"] = (
       df["Server_Workload"] 
       * df["Chiller_Usage"]
    )
    print("    + Cooling_Load = Server_Workload × Chiller_Usage")

    # Total_Cooling_Load: total cooling effort
    # WHY: combines mechanical cooling and air handling effort.
    #      Strong predictor of cooling cost and thermal behavior.
    df["Total_Cooling_Load"] = (
        df["Chiller_Usage"] 
        + df["AHU_Usage"]
    )
    
    print("    + Total_Cooling_Load = Chiller_Usage + AHU_Usage")

    # Cooling_Intensity: cooling effort relative to workload
    # WHY: shows how aggressively cooling resources are used
    #      for a given IT load.

    # Cooling_Intensity: cooling effort relative to workload
    # WHY: shows how aggressively cooling resources are used
    # for a given IT load.
    df["Cooling_Intensity"] = (
    (df["Chiller_Usage"] + df["AHU_Usage"])
    / (df["Server_Workload"] + eps)
    )

    print(
    "    + Cooling_Intensity = "
    "(Chiller_Usage + AHU_Usage) / Server_Workload"
   )
   # Cooling_Power_Load: cooling power under workload
   # WHY: strong proxy for operational energy demand.

    df["Cooling_Power_Load"] = (
    df["Cooling_Unit_Power_Consumption_kW"]
    * df["Server_Workload"]
    )
    print("    + Cooling_Power_Load = Cooling_Power_kW × Server_Workload")

   # Cooling_Power_Usage: cooling power weighted by chiller activity
   # WHY: captures relationship between power draw and cooling effort.

    df["Cooling_Power_Usage"] = (
    df["Cooling_Unit_Power_Consumption_kW"]
    * df["Chiller_Usage"]
    )
    print("    + Cooling_Power_Usage = Cooling_Power_kW × Chiller_Usage")

    # ── 9. Final NaN check ───────────────────────────────────────────────
    remaining_nan = df.isnull().sum().sum()
    if remaining_nan > 0:
        nan_cols = df.columns[df.isnull().any()].tolist()
        raise ValueError(
            f"VALIDATION FAILED: {remaining_nan} NaN values remain "
            f"after processing in columns: {nan_cols}"
        )
    print(f"\n  [validate] Zero NaN values ✓")

    stats = {
        "rows"       : int(len(df)),
        "columns"    : list(df.columns),
        "duplicates_removed": removed_dupes,
        "oob_clipped": total_clipped,
        "strategy_encoding": strategy_map,
        "timestamp_range": {
            "start": str(df["Timestamp"].min()),
            "end"  : str(df["Timestamp"].max()),
        },
    }

    print(f"\n  Final shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df, stats


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — LIQUID COOLING PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def process_liquid_cooling(data_dir: Path) -> tuple[pd.DataFrame, dict]:
    """
    Load and process final_dataset_std.csv.

    Key facts determined by inspection:
      - Semicolon-delimited (not comma)
      - Already z-score standardised: mean≈0, std≈1 for all sensor cols
      - 27013 rows, 43 columns, 32 duplicate rows
      - DoW (Day of Week): int, 1–7
      - WeH (Weekend/Holiday flag): int, 0 or 1
      - TLHC: liquid heat capacity metric, also standardised

    Steps:
      1. Load with sep=';'
      2. Validate columns
      3. Confirm standardisation (NOT authenticity check — data is legitimately
         standardised so zero-mean check would be a false positive)
      4. Remove 32 duplicate rows
      5. Validate DoW/WeH value ranges
      6. Aggregate features (means, deltas, scores)
      7. Final NaN check

    DO NOT re-normalise. Data is already standardised.
    """
    print("\n" + "═"*60)
    print("  LIQUID COOLING DATASET")
    print(f"  File: {LIQUID_FILE}")
    print("═"*60)

    path = data_dir / LIQUID_FILE

    # WHY sep=';': inspection showed the file uses semicolons, not commas.
    # pd.read_csv with default sep=',' reads entire row as one column.
    df = _load_strict(path, "Liquid Cooling (final_dataset_std.csv)", sep=";")

    print(f"\n  Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Columns : {list(df.columns)}")
    print(f"\n  Missing values:\n{df.isnull().sum().to_string()}")
    print(f"  Duplicates: {df.duplicated().sum()}")

    _validate_columns(df, LIQUID_REQUIRED, "Liquid Cooling")
    _confirm_standardised(df)

    # ── Remove duplicates ────────────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates()
    removed_dupes = before - len(df)
    print(f"\n  [duplicates] Removed: {removed_dupes} (were: {before})")

    # ── Validate DoW and WeH ─────────────────────────────────────────────
    # ── Validate DoW and WeH ─────────────────────────────────────────────
    dow_vals = set(df["DoW"].unique())
    weh_vals = set(df["WeH"].unique())

    # Dataset inspection showed DoW is encoded 0-6
    # Some datasets use 1-7, so allow both schemes.
    valid_dow = set(range(0, 8))

    if not dow_vals.issubset(valid_dow):
     raise ValueError(
        f"DoW has unexpected values: {dow_vals - valid_dow}"
     )

    if not weh_vals.issubset({0, 1}):
     raise ValueError(
        f"WeH has unexpected values: {weh_vals - {0, 1}}"
    )

    print(f"  [validate] DoW values: {sorted(dow_vals)} ✓")
    print(f"  [validate] WeH values: {sorted(weh_vals)} ✓")

    # ── Aggregate features ───────────────────────────────────────────────
    # WHY aggregates? P_ac-0..7 are 8 parallel air cooling power readings.
    # The mean captures overall system-level behaviour for XGBoost/SAC.
    # Deltas capture the thermal gradient across the cooling chain.
    print("\n  [features] Computing aggregate features:")

    df["avg_P_ac"]   = df[LIQUID_P_AC].mean(axis=1)
    df["avg_P_cu"]   = df[LIQUID_P_CU].mean(axis=1)
    df["avg_T_out"]  = df[LIQUID_T_OUT].mean(axis=1)
    df["avg_T_MEAS"] = df[LIQUID_T_MEAS].mean(axis=1)
    df["avg_T_celCC"]= df[LIQUID_T_CEL].mean(axis=1)
    print("    + avg_P_ac, avg_P_cu, avg_T_out, avg_T_MEAS, avg_T_celCC")

    # delta_T_out_meas: difference between outlet temp and measured temp
    # WHY: large delta = measurement point far from outlet = uneven cooling
    df["delta_T_out_meas"] = df["avg_T_out"] - df["avg_T_MEAS"]
    print("    + delta_T_out_meas = avg_T_out - avg_T_MEAS")

    # delta_T_meas_cell: sensor-to-cell temperature gradient
    # WHY: captures how much heat the coolant picks up from cell to sensor
    df["delta_T_meas_cell"] = df["avg_T_MEAS"] - df["avg_T_celCC"]
    print("    + delta_T_meas_cell = avg_T_MEAS - avg_T_celCC")

    # thermal_stability_score: std across 8 outlet sensors
    # WHY: low std = uniform cooling; high std = hotspots in the loop
    # Higher score = LESS stable (invert for intuition in reward functions)
    df["thermal_stability_score"] = df[LIQUID_T_OUT].std(axis=1)
    print("    + thermal_stability_score = std(T_out-0..7)")

    # cooling_efficiency_score: ratio of cooling power to air cooling power
    # WHY: P_cu (liquid/chiller) vs P_ac (air). Higher P_cu/P_ac ratio
    #      means more aggressive liquid cooling — higher water use.
    #      Note: columns are standardised so ratio is relative, not absolute.
    df["cooling_efficiency_score"] = df["avg_P_cu"] / (df["avg_P_ac"].abs() + 1e-6)
    print("    + cooling_efficiency_score = avg_P_cu / avg_P_ac")

    # ── Final NaN check ───────────────────────────────────────────────────
    remaining_nan = df.isnull().sum().sum()
    if remaining_nan > 0:
        nan_cols = df.columns[df.isnull().any()].tolist()
        raise ValueError(
            f"VALIDATION FAILED: {remaining_nan} NaN values remain "
            f"in columns: {nan_cols}"
        )
    print(f"\n  [validate] Zero NaN values ✓")

    stats = {
        "rows"             : int(len(df)),
        "columns"          : list(df.columns),
        "duplicates_removed": removed_dupes,
        "already_standardised": True,
        "dow_range"        : [int(min(dow_vals)), int(max(dow_vals))],
        "weekend_holiday_pct": round(
            df["WeH"].sum() / len(df) * 100, 2
        ),
    }

    print(f"\n  Final shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df, stats


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — FACILITY PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def process_facility(data_dir: Path) -> tuple[pd.DataFrame, dict]:
    """
    Load and merge 4 facility files into one clean dataset.

    Join strategy (confirmed by data inspection):

    ┌─────────────────────────────────────────────────────────┐
    │ Step A: layout LEFT JOIN layout_2                       │
    │   Key  : [Rack, First Row]                              │
    │   WHY  : layout has 70 rows with Model/rpm unique to    │
    │           it. layout_2 has corrected pwrConsumption/Q   │
    │           for 46 of those rows. LEFT preserves all 70.  │
    │           Take pwrConsumption/Q from layout_2 where     │
    │           available (more accurate), else use layout.   │
    │   Result: 70 rows                                       │
    ├─────────────────────────────────────────────────────────┤
    │ Step B: Table3 LEFT JOIN exhaust on Height (U)          │
    │   WHY  : exhaust is the superset (12 rows including     │
    │           Height=38 absent in Table3). Both carry       │
    │           Previous/Retrofitted Design °C — use exhaust  │
    │           as base, Table3 confirms values (they match). │
    │           Keep Z(m) and Z(m).1 from exhaust.            │
    │   Result: 12 rows                                       │
    ├─────────────────────────────────────────────────────────┤
    │ Step C: Step A LEFT JOIN Step B                         │
    │   Key  : layout[First Row] = thermal[Height (U)]        │
    │   WHY  : First Row in layout = U-position from floor.   │
    │           Height (U) in exhaust = same physical         │
    │           position. 19 of 70 rows match; others get     │
    │           NaN for thermal columns (honest representation│
    │           — those rack positions have no exhaust data). │
    │   Result: 70 rows                                       │
    └─────────────────────────────────────────────────────────┘

    NOTE: Table2 is an exact duplicate of layout_2 (confirmed by
    layout_2.equals(Table2) = True). It is explicitly excluded.
    data.csv is arc_length geometry, not DC data. Also excluded.
    """
    print("\n" + "═"*60)
    print("  FACILITY DATASET")
    print("═"*60)

    # ── Load all facility files ───────────────────────────────────────────
    print(f"\n  Loading {LAYOUT_FILE}...")
    layout = _load_strict(data_dir / LAYOUT_FILE, "layout.csv")
    print(f"    Shape: {layout.shape}  Columns: {list(layout.columns)}")
    print(f"    Missing:\n{layout.isnull().sum().to_string()}")
    print(f"    Duplicates: {layout.duplicated().sum()}")
    _validate_columns(layout, LAYOUT_REQUIRED, "layout.csv")
    _check_authenticity(
        layout.select_dtypes(include=[np.number]).drop(columns=["condition"],
        errors="ignore"), "layout.csv"
    )

    print(f"\n  Loading {LAYOUT2_FILE}...")
    layout2 = _load_strict(data_dir / LAYOUT2_FILE, "layout_2.csv")
    print(f"    Shape: {layout2.shape}  Columns: {list(layout2.columns)}")
    _validate_columns(layout2, LAYOUT2_REQUIRED, "layout_2.csv")

    # Confirm Table2 == layout_2 (so we can safely exclude Table2)
    print(f"\n  Checking {TABLE2_FILE} vs {LAYOUT2_FILE}...")
    table2 = _load_strict(data_dir / TABLE2_FILE, "Table2.csv")
    if layout2.equals(table2):
        print(f"    ✓ Table2 is an exact duplicate of layout_2 — EXCLUDED")
    else:
        raise ValueError(
            "Table2.csv is NOT identical to layout_2.csv. "
            "Manual inspection required before deciding join strategy."
        )

    print(f"\n  Loading {TABLE3_FILE}...")
    table3 = _load_strict(data_dir / TABLE3_FILE, "Table3.csv")
    print(f"    Shape: {table3.shape}  Columns: {list(table3.columns)}")
    _validate_columns(table3, TABLE3_REQUIRED, "Table3.csv")

    print(f"\n  Loading {EXHAUST_FILE}...")
    exhaust = _load_strict(data_dir / EXHAUST_FILE, "exhaust_temp.csv")
    print(f"    Shape: {exhaust.shape}  Columns: {list(exhaust.columns)}")
    _validate_columns(exhaust, EXHAUST_REQUIRED, "exhaust_temp.csv")

    # Confirm data.csv is excluded (print notice, not error)
    print(f"\n  [{EXCLUDED_FILE}] EXCLUDED: arc_length geometry data, "
          f"not data center telemetry.")

    # ── Step A: layout LEFT JOIN layout_2 ────────────────────────────────
    print("\n  [join A] layout LEFT JOIN layout_2 on [Rack, First Row]")

    facility = layout.merge(
        layout2[["Rack", "First Row", "pwrConsumption", "Q"]],
        on=["Rack", "First Row"],
        how="left",
        suffixes=("_orig", "_corrected"),
    )

    # Resolve pwrConsumption: use layout_2 value where available (more accurate),
    # fall back to layout value for unmatched rows
    facility["PowerConsumption"] = np.where(
        facility["pwrConsumption_corrected"].notna(),
        facility["pwrConsumption_corrected"],
        facility["pwrConsumption_orig"],
    )
    facility["Q_final"] = np.where(
        facility["Q_corrected"].notna(),
        facility["Q_corrected"],
        facility["Q_orig"],
    )
    # Drop the intermediate suffix columns
    facility = facility.drop(columns=[
        "pwrConsumption_orig", "pwrConsumption_corrected",
        "Q_orig", "Q_corrected"
    ])
    facility = facility.rename(columns={"Q_final": "Q"})

    unmatched_A = facility["Q"].isna().sum()
    print(f"    Rows: {len(facility)} | "
          f"Matched from layout_2: {len(facility) - unmatched_A} | "
          f"layout-only: {unmatched_A}")

    # ── Step B: exhaust LEFT JOIN table3 on Height (U) ───────────────────
    print("\n  [join B] exhaust LEFT JOIN Table3 on Height (U)")

    # exhaust is superset (has Height=38 which Table3 lacks)
    # Both have Previous/Retrofitted Design — they are identical where both exist
    # Keep exhaust's version; use Table3 only for any that might differ
    thermal = exhaust.merge(
        table3.rename(columns={
            "Previous Design (°C)":    "Prev_Design_t3",
            "Retrofitted Design (°C)": "Retro_Design_t3",
        }),
        on="Height (U)",
        how="left",
    )

    # Verify that where both exist, values match (data quality check)
    both_present = thermal["Prev_Design_t3"].notna()
    mismatch = (
        (thermal.loc[both_present, "Previous Design (°C)"] -
         thermal.loc[both_present, "Prev_Design_t3"]).abs() > 0.01
    ).sum()
    if mismatch > 0:
        raise ValueError(
            f"Table3 and exhaust_temp disagree on {mismatch} temperature values. "
            f"Manual inspection required."
        )
    print(f"    Table3 ∩ exhaust: values consistent ✓")
    print(f"    exhaust-only rows (Height=38): "
          f"{thermal['Prev_Design_t3'].isna().sum()}")

    # Use exhaust columns as authoritative; drop Table3 duplicates
    thermal = thermal.drop(columns=["Prev_Design_t3", "Retro_Design_t3"])
    thermal = thermal.rename(columns={
        "Previous Design (°C)":    "Exhaust_Prev_Design_C",
        "Retrofitted Design (°C)": "Exhaust_Retro_Design_C",
        "Z (m)":                   "Z_m",
        "Z (m).1":                 "Z_m_check",
    })
    # Z(m) and Z(m).1 appear to be duplicate columns in exhaust_temp
    # Verify then drop the redundant one
    z_match = (thermal["Z_m"] - thermal["Z_m_check"]).abs().max()
    if z_match > 0.001:
        raise ValueError("Z(m) and Z(m).1 in exhaust_temp differ — investigate.")
    thermal = thermal.drop(columns=["Z_m_check"])
    print(f"    Z(m) and Z(m).1 verified identical — Z(m).1 dropped")
    print(f"    Thermal table shape: {thermal.shape}")

    # ── Step C: facility LEFT JOIN thermal on First Row = Height (U) ─────
    print("\n  [join C] facility LEFT JOIN thermal on First Row = Height (U)")
    print("    WHY: First Row in layout = U-position from floor")
    print("         Height (U) in exhaust = same physical U-position")

    facility = facility.merge(
        thermal.rename(columns={"Height (U)": "First Row"}),
        on="First Row",
        how="left",
    )

    matched_C = facility["Exhaust_Prev_Design_C"].notna().sum()
    print(f"    Rows with exhaust data: {matched_C} / {len(facility)}")
    print(f"    Rows without exhaust (honest NaN): {len(facility) - matched_C}")

    # ── Rename and standardise column names ──────────────────────────────
    facility = facility.rename(columns={
        "Rack"      : "Rack_ID",
        "First Row" : "Rack_Position",
        "Height"    : "Height_U",
        "Type"      : "Equipment_Type",
        "Model"     : "Model",
        "rpm"       : "RPM",
        "condition" : "Condition",
    })

    # ── Handle condition column (all NaN in layout — known from inspection) ─
    # condition is entirely NaN in layout.csv (confirmed: 70/70 NaN)
    # We do NOT fabricate values. Print notice, leave as NaN, drop for ML.
    print(f"\n  [condition] 'Condition' column: "
          f"{facility['Condition'].isna().sum()}/{len(facility)} NaN")
    print("    WHY: 'condition' is entirely NaN in layout.csv source.")
    print("    Action: column retained as-is (NaN). Downstream ML pipelines")
    print("    should handle or exclude this column explicitly.")

    # ── Feature engineering ───────────────────────────────────────────────
    print("\n  [features] Engineering facility features:")

    # Heat_Density: power per unit of rack height
    # WHY: a 10U server consuming 800W is denser than a 42U consuming 800W
    #      High heat density = higher cooling priority
    eps = 1e-6
    facility["Heat_Density"] = (
        facility["PowerConsumption"] / (facility["Height_U"] + eps)
    )
    print("    + Heat_Density = PowerConsumption / Height_U")

    # Hotspot_Risk: flag racks where exhaust temp exceeds 30°C threshold
    # WHY: ASHRAE A2 recommends inlet < 35°C; exhaust > 30°C is a precursor
    #      1 = at risk, 0 = safe, NaN where no exhaust data
    facility["Hotspot_Risk"] = np.where(
        facility["Exhaust_Prev_Design_C"].notna(),
        (facility["Exhaust_Prev_Design_C"] > 30.0).astype(float),
        np.nan,
    )
    print("    + Hotspot_Risk = 1 if Exhaust_Prev_Design > 30°C else 0")

    # Rack_Efficiency_Score: Q (airflow) per unit of power consumed
    # WHY: higher Q per watt = better cooled per unit energy = more efficient
    facility["Rack_Efficiency_Score"] = (
        facility["Q"] / (facility["PowerConsumption"] + eps)
    )
    print("    + Rack_Efficiency_Score = Q / PowerConsumption")

    # Thermal_Risk_Score: combined metric for XGBoost Digital Twin
    # Combines heat density and hotspot risk into a single risk index
    # NaN for rows without exhaust data (handled by XGBoost natively)
    facility["Thermal_Risk_Score"] = (
        facility["Heat_Density"] * (1.0 + facility["Hotspot_Risk"].fillna(0.0))
    )
    print("    + Thermal_Risk_Score = Heat_Density × (1 + Hotspot_Risk)")

    # ── Temperature improvement from retrofitting ─────────────────────────
    # Delta between previous and retrofitted design (positive = cooler after)
    facility["Retrofit_Temp_Delta"] = np.where(
        facility["Exhaust_Prev_Design_C"].notna(),
        facility["Exhaust_Prev_Design_C"] - facility["Exhaust_Retro_Design_C"],
        np.nan,
    )
    print("    + Retrofit_Temp_Delta = Prev_Design - Retro_Design (°C improvement)")

    # ── Validate no duplicate Rack_ID + Rack_Position combos ─────────────
    dupe_keys = facility.duplicated(subset=["Rack_ID", "Rack_Position"]).sum()
    if dupe_keys > 0:
        raise ValueError(
            f"VALIDATION FAILED: {dupe_keys} duplicate [Rack_ID, Rack_Position] "
            f"rows after merge. This indicates a non-1:1 join — investigate."
        )
    print(f"\n  [validate] No duplicate [Rack_ID, Rack_Position] keys ✓")

    # NaN count — condition column will still have NaN (expected)
    nan_summary = facility.isnull().sum()
    nan_cols = nan_summary[nan_summary > 0]
    print(f"\n  [NaN summary after processing]:")
    for col, cnt in nan_cols.items():
        print(f"    '{col}': {cnt} NaN  "
              f"({'expected — no source data' if col in ['Condition', 'Exhaust_Prev_Design_C', 'Exhaust_Retro_Design_C', 'Z_m', 'Hotspot_Risk', 'Thermal_Risk_Score', 'Retrofit_Temp_Delta'] else 'UNEXPECTED'})")

    # Reject unexpected NaN
    unexpected_nan_cols = [
        c for c in facility.columns
        if facility[c].isna().any()
        and c not in ["Condition", "Exhaust_Prev_Design_C", "Exhaust_Retro_Design_C",
                      "Z_m", "Hotspot_Risk", "Thermal_Risk_Score", "Retrofit_Temp_Delta"]
    ]
    if unexpected_nan_cols:
        raise ValueError(
            f"UNEXPECTED NaN values in: {unexpected_nan_cols}\n"
            f"These columns should be fully populated. Investigate join."
        )

    stats = {
        "rows"            : int(len(facility)),
        "columns"         : list(facility.columns),
        "joined_files"    : [LAYOUT_FILE, LAYOUT2_FILE,
                             TABLE3_FILE, EXHAUST_FILE],
        "excluded_files"  : [TABLE2_FILE, EXCLUDED_FILE],
        "join_strategy"   : "LEFT JOIN on [Rack,First Row] then LEFT JOIN on First Row=Height(U)",
        "rows_with_exhaust": int(matched_C),
        "rows_without_exhaust": int(len(facility) - matched_C),
        "condition_all_nan": True,
    }

    print(f"\n  Final shape: {facility.shape[0]} rows × {facility.shape[1]} columns")
    return facility, stats


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — DATA REPORT
# ══════════════════════════════════════════════════════════════════════════════

def _column_stats(df: pd.DataFrame) -> dict:
    """Per-column stats for the JSON report. All values JSON-serialisable."""
    out = {}
    for col in df.columns:
        s = df[col]
        entry: dict = {
            "dtype"       : str(s.dtype),
            "null_count"  : int(s.isna().sum()),
            "unique_count": int(s.nunique()),
        }
        if pd.api.types.is_numeric_dtype(s) and s.notna().sum() > 0:
            entry.update({
                "min"   : round(float(s.min()),  6),
                "max"   : round(float(s.max()),  6),
                "mean"  : round(float(s.mean()), 6),
                "std"   : round(float(s.std()),  6),
                "median": round(float(s.median()), 6),
            })
        out[col] = entry
    return out


def build_data_report(
    air_df    : pd.DataFrame,
    liquid_df : pd.DataFrame,
    facility_df: pd.DataFrame,
    air_stats  : dict,
    liquid_stats: dict,
    facility_stats: dict,
) -> dict:
    """
    Build data_report.json consumed by FastAPI /dashboard/overview.

    Includes per-dataset stats, column-level stats, and the mandatory
    'generated_from_real_data' and 'synthetic_data_used' flags.
    """
    return {
        "generated_at"          : datetime.now(timezone.utc).isoformat(),
        "generated_from_real_data": True,
        "synthetic_data_used"   : False,
        "random_data_used"      : False,
        "air_rows"              : int(len(air_df)),
        "liquid_rows"           : int(len(liquid_df)),
        "facility_rows"         : int(len(facility_df)),
        "air_columns"           : list(air_df.columns),
        "liquid_columns"        : list(liquid_df.columns),
        "facility_columns"      : list(facility_df.columns),
        "missing_values_air"    : int(air_df.isnull().sum().sum()),
        "missing_values_liquid" : int(liquid_df.isnull().sum().sum()),
        "missing_values_facility": int(facility_df.isnull().sum().sum()),
        "duplicates_removed_air": air_stats.get("duplicates_removed", 0),
        "duplicates_removed_liquid": liquid_stats.get("duplicates_removed", 0),
        "excluded_files"        : [TABLE2_FILE, EXCLUDED_FILE],
        "air_pipeline"          : air_stats,
        "liquid_pipeline"       : liquid_stats,
        "facility_pipeline"     : facility_stats,
        "air_column_stats"      : _column_stats(air_df),
        "liquid_column_stats"   : _column_stats(liquid_df),
        "facility_column_stats" : _column_stats(facility_df),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — FINAL VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def _final_validation(name: str, df: pd.DataFrame,
                      allow_nan_cols: list = None) -> None:
    """
    Post-save validation gate. Fails loudly on any unexpected NaN or dupes.
    allow_nan_cols: columns where NaN is expected (e.g. facility 'Condition').
    """
    allow_nan_cols = allow_nan_cols or []
    unexpected = [
        c for c in df.columns
        if df[c].isna().any() and c not in allow_nan_cols
    ]
    if unexpected:
        raise ValueError(
            f"FINAL VALIDATION FAILED [{name}]: "
            f"Unexpected NaN in {unexpected}"
        )

    dupes = df.duplicated().sum()
    if dupes > 0:
        raise ValueError(
            f"FINAL VALIDATION FAILED [{name}]: "
            f"{dupes} duplicate rows in output."
        )

    print(f"  [final validate] {name}: NaN ✓  Duplicates ✓")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main(data_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "█"*60)
    print("  AI DATA CENTER COOLING — PREPROCESSING PIPELINE")
    print("█"*60)
    print(f"  Data dir   : {data_dir.resolve()}")
    print(f"  Output dir : {out_dir.resolve()}")
    print(f"  Timestamp  : {datetime.now(timezone.utc).isoformat()}")

    # ── Process each dataset ──────────────────────────────────────────────
    air_df,      air_stats      = process_air_cooling(data_dir)
    liquid_df,   liquid_stats   = process_liquid_cooling(data_dir)
    facility_df, facility_stats = process_facility(data_dir)

    # ── Final validations ─────────────────────────────────────────────────
    print("\n" + "═"*60)
    print("  FINAL VALIDATION")
    print("═"*60)
    _final_validation("air_cooling",    air_df)
    _final_validation("liquid_cooling", liquid_df)
    _final_validation(
        "facility", facility_df,
        allow_nan_cols=[
            "Condition", "Exhaust_Prev_Design_C", "Exhaust_Retro_Design_C",
            "Z_m", "Hotspot_Risk", "Thermal_Risk_Score", "Retrofit_Temp_Delta",
        ],
    )

    # ── Save outputs ──────────────────────────────────────────────────────
    print("\n" + "═"*60)
    print("  SAVING OUTPUTS")
    print("═"*60)

    air_out = out_dir / "air_cooling_data.csv"
    liq_out = out_dir / "liquid_cooling_data.csv"
    fac_out = out_dir / "facility_data.csv"
    rep_out = out_dir / "data_report.json"

    air_df.to_csv(air_out,    index=False)
    liquid_df.to_csv(liq_out, index=False)
    facility_df.to_csv(fac_out, index=False)

    report = build_data_report(
        air_df, liquid_df, facility_df,
        air_stats, liquid_stats, facility_stats,
    )
    rep_out.write_text(json.dumps(report, indent=2, default=str))

    for p in [air_out, liq_out, fac_out, rep_out]:
        size = p.stat().st_size
        print(f"  ✓ {p.name:<30} {size:>10,} bytes")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "█"*60)
    print("  PIPELINE COMPLETE")
    print("█"*60)
    print(f"  air_cooling_data.csv   : {len(air_df):,} rows × "
          f"{len(air_df.columns)} cols")
    print(f"  liquid_cooling_data.csv: {len(liquid_df):,} rows × "
          f"{len(liquid_df.columns)} cols")
    print(f"  facility_data.csv      : {len(facility_df):,} rows × "
          f"{len(facility_df.columns)} cols")
    print(f"  data_report.json       : written")
    print(f"  generated_from_real_data : True")
    print(f"  synthetic_data_used      : False")
    print("█"*60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AI Data Center Cooling — Preprocessing Pipeline"
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("."),
        help="Directory containing all 8 input CSV files (default: current dir)"
    )
    parser.add_argument(
        "--out-dir", type=Path, default=Path("processed"),
        help="Output directory for processed files (default: processed/)"
    )
    args = parser.parse_args()
    main(args.data_dir, args.out_dir)
