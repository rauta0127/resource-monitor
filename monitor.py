from abc import ABC, abstractmethod
from datetime import datetime
import psutil
import pandas as pd
import os
import subprocess
import csv
import platform
import argparse

class ResourceMonitor(ABC):
    def __init__(self, csv_path):
        self.CSV_PATH = csv_path
        self.COLUMNS = []

    def get_os_type(self):
        """
        Darwin: macOS
        Linux: Linux
        Windows: Windows
        """
        os_type = platform.system()
        return os_type

    def get_currenttime(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return current_time
    
    def get_hostname(self):
        hostname = os.uname()[1]
        return hostname
    
    def get_cpu_usage(self):
        cpu_usage = psutil.cpu_percent(interval=1, percpu=False)
        return cpu_usage
    
    def get_loadavg(self):
        load1m, load5m, load15m = os.getloadavg()
        return load1m, load5m, load15m
    
    def get_memory_usage(self):
        mem_info = psutil.virtual_memory()
        total_memory = mem_info.total // (1024 **2)
        used_memory = mem_info.used // (1024 **2)
        free_memory = mem_info.free // (1024 **2)
        return total_memory, used_memory, free_memory
    
    def get_top_cpu_users(self):
        command = "ps -eo user,%cpu | awk 'NR>1 {a[$1]+=$2} END {for (u in a) print u\",\"a[u]}' | sort -t',' -k2 -nr | head -n 3"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        top_cpu_users = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                user, cpu = line.split(',')
                try:
                    cpu = float(cpu)
                    top_cpu_users.append([user, cpu])
                except:
                    top_cpu_users.append([user, None])
        else:
            for _ in range(3):
                top_cpu_users.append([None, None])
        return top_cpu_users

    @abstractmethod
    def monitor(self): 
        pass

    def check_existing_csv(self):
        """Check if the CSV file exists, and add column names if missing."""
        if os.path.exists(self.CSV_PATH):
            with open(self.CSV_PATH, mode='r+', newline='') as file:
                reader = csv.reader(file)
                first_row = next(reader, None)
                if first_row is None or first_row != self.COLUMNS:
                    # If column names are missing or incorrect, add them
                    writer = csv.writer(file)
                    file.seek(0)  # Move to the beginning of the file to add column names
                    writer.writerow(self.COLUMNS)
                    file.truncate()  # Truncate the file content after adding the column names
        else:
            return False  # If the file does not exist

        return True  # If the file exists and is correct


    def create_csv(self):
        with open(self.CSV_PATH, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.COLUMNS)

    def save(self, data: list):
        if not self.check_existing_csv():
            self.create_csv()
        
        with open(self.CSV_PATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

class CPUMonitor(ResourceMonitor):
    def __init__(self, csv_path: str = "cpu_usage.csv"):
        super().__init__(csv_path)
        self.COLUMNS = [
            "Timestamp", "Hostname", "CPU Usage(%)", 
            "Load Average(1m)", "Load Average(5m)", "Load Average(15m)",
            "Total Memory(MB)", "Used Memory(MB)", "Free Memory(MB)",
            "Top User", "Top CPU Usage(%)", 
            "Second User", "Second CPU Usage(%)", 
            "Third User", "Third CPU Usage(%)"
        ]

    def monitor(self):
        current_time = self.get_currenttime()
        hostname = self.get_hostname()
        cpu_usage = self.get_cpu_usage()
        load1m, load5m, load15m = self.get_loadavg()
        total_memory, used_memory, free_memory = self.get_memory_usage()
        top_cpu_users = self.get_top_cpu_users()
        data = [
            current_time, hostname, cpu_usage, 
            load1m, load5m, load15m, 
            total_memory, used_memory, free_memory, 
            top_cpu_users[0][0], top_cpu_users[0][1], 
            top_cpu_users[1][0], top_cpu_users[1][1], 
            top_cpu_users[2][0], top_cpu_users[2][1]
        ]
        self.save(data)
        return data

class GPUMonitor(ResourceMonitor):
    def __init__(self, csv_path: str = "gpu_usage.csv"):
        super().__init__(csv_path)
        self.COLUMNS = [
            "Timestamp","Hostname","GPU Index","Name","Temp(C)","Power Usage(W)","Power Cap(W)","Mem Usage(MB)","Mem Total(MB)","GPU Util(%)"
        ]

    def get_gpu_usage(self):
        command = ["nvidia-smi", "--query-gpu=index,name,temperature.gpu,power.draw,power.limit,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"]
        gpu_usage = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return gpu_usage

    def monitor(self):
        current_time = self.get_currenttime()
        hostname = self.get_hostname()
        gpu_usage = self.get_gpu_usage()
        gpu_info = gpu_usage.stdout.strip().split('\n')
        for line in gpu_info:
            data = [current_time, hostname] + line.split(', ')
            self.save(data)

if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="Monitor CPU or GPU usage.")
    parser.add_argument(
        "monitor_type", choices=["cpu", "gpu"], 
        help="Specify whether to monitor CPU or GPU usage."
    )
    parser.add_argument(
        "--csv_path", type=str, 
        help="Specify the path to the CSV file for logging."
    )
    
    args = parser.parse_args()
    # Ensure the csv_path has the correct extension
    if not args.csv_path.endswith(".csv"):
        raise ValueError("The CSV path must end with '.csv'.")
    
    csv_path = args.csv_path if args.csv_path else "cpu_usage.csv" if args.monitor_type == "cpu" else "gpu_usage.csv"
    
    if args.monitor_type == "cpu":
        CPUMonitor(csv_path).monitor()
    elif args.monitor_type == "gpu":
        GPUMonitor(csv_path).monitor()