import pandas as pd
from datetime import datetime, timedelta
import pytz

def clean_usage():
    cpu_usage_path = "cpu_usage.csv"
    gpu_usage_path = "gpu_usage.csv"
    cpu_usage_df = pd.read_csv(cpu_usage_path, on_bad_lines='warn')
    gpu_usage_df = pd.read_csv(gpu_usage_path, on_bad_lines='warn')
    cpu_usage_df = cpu_usage_df[pd.notnull(cpu_usage_df["Third CPU Usage(%)"])].reset_index(drop=True)
    gpu_usage_df = gpu_usage_df[pd.notnull(gpu_usage_df["GPU Util(%)"])].reset_index(drop=True)
    cpu_usage_df = cpu_usage_df[pd.notnull(cpu_usage_df["Timestamp"])].reset_index(drop=True)
    gpu_usage_df = gpu_usage_df[pd.notnull(gpu_usage_df["Timestamp"])].reset_index(drop=True)


    # タイムスタンプをJSTとして認識（naive→aware）
    jst = pytz.timezone("Asia/Tokyo")
    cpu_usage_df["Timestamp"] = pd.to_datetime(cpu_usage_df["Timestamp"], errors="coerce")
    if cpu_usage_df["Timestamp"].dt.tz is None:
        cpu_usage_df["Timestamp"] = cpu_usage_df["Timestamp"].dt.tz_localize("Asia/Tokyo")
    else:
        cpu_usage_df["Timestamp"] = cpu_usage_df["Timestamp"].dt.tz_convert("Asia/Tokyo")
    gpu_usage_df["Timestamp"] = pd.to_datetime(gpu_usage_df["Timestamp"], errors="coerce")
    if gpu_usage_df["Timestamp"].dt.tz is None:
        gpu_usage_df["Timestamp"] = gpu_usage_df["Timestamp"].dt.tz_localize("Asia/Tokyo")
    else:
        gpu_usage_df["Timestamp"] = gpu_usage_df["Timestamp"].dt.tz_convert("Asia/Tokyo")

    # 現在時刻（JST）から3ヶ月前のデータを残す
    now = datetime.now(jst)
    three_months_ago = now - pd.DateOffset(months=3)
    cpu_usage_df = cpu_usage_df[cpu_usage_df["Timestamp"] >= three_months_ago]
    gpu_usage_df = gpu_usage_df[gpu_usage_df["Timestamp"] >= three_months_ago]

    cpu_usage_df.to_csv(cpu_usage_path, index=False)
    gpu_usage_df.to_csv(gpu_usage_path, index=False)

if __name__ == "__main__": 
    clean_usage()