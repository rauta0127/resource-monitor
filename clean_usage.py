import pandas as pd

def clean_usage():
    cpu_usage_path = "cpu_usage.csv"
    gpu_usage_path = "gpu_usage.csv"
    cpu_usage_df = pd.read_csv(cpu_usage_path, on_bad_lines='warn')
    gpu_usage_df = pd.read_csv(gpu_usage_path, on_bad_lines='warn')
    cpu_usage_df = cpu_usage_df[pd.notnull(cpu_usage_df["Third CPU Usage(%)"])].reset_index(drop=True)
    gpu_usage_df = gpu_usage_df[pd.notnull(gpu_usage_df["GPU Util(%)"])].reset_index(drop=True)
    cpu_usage_df = cpu_usage_df[pd.notnull(cpu_usage_df["Timestamp"])].reset_index(drop=True)
    gpu_usage_df = gpu_usage_df[pd.notnull(gpu_usage_df["Timestamp"])].reset_index(drop=True)
    cpu_usage_df.to_csv(cpu_usage_path, index=False)
    gpu_usage_df.to_csv(gpu_usage_path, index=False)

if __name__ == "__main__": 
    clean_usage()