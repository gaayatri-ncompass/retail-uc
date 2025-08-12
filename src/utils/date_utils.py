import pandas as pd

def generate_date_dimension(csv_configs, output_csv_path):
    min_dates = []
    max_dates = []

    for config in csv_configs:
        df = pd.read_csv(config["path"])
        date_col = config["date_column"]

        if date_col not in df.columns:
            print(f"Warning: Column '{date_col}' not found in {config['path']}")
            continue

        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])

        if not df.empty:
            min_dates.append(df[date_col].min())
            max_dates.append(df[date_col].max())

    if not min_dates or not max_dates:
        raise ValueError("No valid dates found in provided CSVs.")

    overall_min = min(min_dates)
    overall_max = max(max_dates)

  
    dates = pd.date_range(start=overall_min, end=overall_max, freq='D')
    dim_df = pd.DataFrame({"date": dates})

  
    dim_df["day"] = dim_df["date"].dt.day
    dim_df["month"] = dim_df["date"].dt.month
    dim_df["quarter"] = dim_df["date"].dt.quarter
    dim_df["year"] = dim_df["date"].dt.year
    dim_df["day_of_week"] = dim_df["date"].dt.dayofweek

    dim_df.to_csv(output_csv_path, index=False)
    print(f"Date dimension saved to {output_csv_path} covering {overall_min.date()} to {overall_max.date()}")
