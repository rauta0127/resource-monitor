import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from PIL import Image
import numpy as np
from datetime import datetime
import pytz
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import pytz

from slack import SlackNotificator
from clean_usage import clean_usage


class ResourceReport(ABC):
    def __init__(self, cpu_usage_filepath: str = "cpu_usage.csv", gpu_usage_filepath: str = "gpu_usage.csv"):
        self.cpu_usage_df = self._read_usage_data(cpu_usage_filepath)
        self.gpu_usage_df = self._read_usage_data(gpu_usage_filepath)
        self.now = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d_%H:%M:%S")

    def _read_usage_data(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        # df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce').dt.tz_localize("Asia/Tokyo", ambiguous='NaT', nonexistent='shift_forward')
        jst = pytz.timezone("Asia/Tokyo")
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        if df["Timestamp"].dt.tz is None:
            df["Timestamp"] = df["Timestamp"].dt.tz_localize("Asia/Tokyo")
        else:
            df["Timestamp"] = df["Timestamp"].dt.tz_convert("Asia/Tokyo")
        return df.dropna(subset=['Timestamp'])

    def get_past_days_usage(self, usage_df: pd.DataFrame, past_days: int = 1) -> pd.DataFrame:
        usage_df = usage_df.copy()
        usage_df['Date'] = usage_df['Timestamp'].dt.floor('D')
        last_date = usage_df['Date'].max()
        start_date = last_date - pd.Timedelta(days=past_days)
        return usage_df[usage_df['Date'] >= start_date].drop(columns='Date')

    def _custom_date_formatter(self, x, pos):
        timestamp = mdates.num2date(x)
        return timestamp.strftime('%m-%d (%a)') if timestamp.hour == 0 else timestamp.strftime('%H')

    def _prepare_axes(self, n: int, ncols=2):
        nrows = (n + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(14, 3 * nrows), sharex=True)
        axes = axes.flatten() if isinstance(axes, np.ndarray) else [axes]
        return fig, axes

    def plot_timeseries_trend(self, usage_df: pd.DataFrame, y_col: str, past_days=8, color="blue", save_path="timeseries_trend.jpg"):
        df = self.get_past_days_usage(usage_df, past_days)
        hostnames = sorted(df['Hostname'].unique())
        fig, axes = self._prepare_axes(len(hostnames))

        for i, hostname in enumerate(hostnames):
            ax = axes[i]
            sns.lineplot(data=df[df['Hostname'] == hostname], x='Timestamp', y=y_col, ax=ax, color=color)
            ax.set_title(f'{y_col} Trend for {hostname} @ {self.now}')
            ax.set_ylim(0, 100)
            ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))
            ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
            ax.xaxis.set_major_formatter(FuncFormatter(self._custom_date_formatter))
            ax.tick_params(axis='x', rotation=90)
            ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.5)
            ax.grid(True, which='minor', axis='x', linestyle=':', linewidth=0.5)

        plt.tight_layout()
        plt.savefig(save_path, dpi=200)

    def _plot_categorical_strip(self, usage_df, y_col, category, past_days, recent_days, color, recent_color, save_path, title_suffix):
        df_all = self.get_past_days_usage(usage_df, past_days)
        df_recent = self.get_past_days_usage(usage_df, recent_days)
        df_all[category] = getattr(df_all['Timestamp'].dt, category)
        df_recent[category] = getattr(df_recent['Timestamp'].dt, category)

        if category == "dayofweek":
            mapper = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        else:  # hour
            mapper = list(range(24))

        df_all[category] = pd.Categorical(df_all[category], categories=mapper, ordered=True)
        df_recent[category] = pd.Categorical(df_recent[category], categories=mapper, ordered=True)

        hostnames = sorted(df_all['Hostname'].unique())
        fig, axes = self._prepare_axes(len(hostnames))

        for i, hostname in enumerate(hostnames):
            ax = axes[i]
            sns.stripplot(data=df_all[df_all['Hostname'] == hostname], x=category, y=y_col, ax=ax, color=color)
            sns.stripplot(data=df_recent[df_recent['Hostname'] == hostname], x=category, y=y_col, ax=ax, color=recent_color)
            ax.set_title(f'{y_col} {title_suffix} for {hostname}')
            ax.set_ylim(0, 100)
            ax.tick_params(axis='x', rotation=90)
            ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.5)

        plt.tight_layout()
        plt.savefig(save_path, dpi=200)

    def plot_dayofweek_boxplot(self, usage_df, y_col, past_days=28, color="blue", save_path="dayofweek_boxplot.jpg"):
        self._plot_categorical_strip(usage_df, y_col, "dayofweek", past_days, 7, color, "orange", save_path, "by Day")

    def plot_hour_boxplot(self, usage_df, y_col, past_days=28, color="blue", save_path="hour_boxplot.jpg"):
        self._plot_categorical_strip(usage_df, y_col, "hour", past_days, 7, color, "orange", save_path, "by Hour")

    def merge_images(self, image_files, direction="vertical", save_path="combined.jpg"):
        images = [Image.open(p) for p in image_files]
        widths, heights = zip(*(i.size for i in images))
        if direction == "vertical":
            new_img = Image.new("RGB", (max(widths), sum(heights)))
            offset = 0
            for img in images:
                new_img.paste(img, (0, offset))
                offset += img.height
        else:
            new_img = Image.new("RGB", (sum(widths), max(heights)))
            offset = 0
            for img in images:
                new_img.paste(img, (offset, 0))
                offset += img.width
        new_img.save(save_path)

    def report(self, report_to: str = "slack"):
        self.plot_timeseries_trend(self.cpu_usage_df, y_col="CPU Usage(%)", save_path="img/timeseries_trend_cpu.jpg")
        self.plot_dayofweek_boxplot(self.cpu_usage_df, y_col="CPU Usage(%)", save_path="img/dayofweek_boxplot_cpu.jpg")
        self.plot_hour_boxplot(self.cpu_usage_df, y_col="CPU Usage(%)", save_path="img/hour_boxplot_cpu.jpg")
        self.merge_images(
            ["img/timeseries_trend_cpu.jpg", "img/dayofweek_boxplot_cpu.jpg", "img/hour_boxplot_cpu.jpg"],
            direction="vertical",
            save_path="img/combined_image_cpu.jpg"
        )

        self.plot_timeseries_trend(self.gpu_usage_df, y_col="GPU Util(%)", save_path="img/timeseries_trend_gpu.jpg")
        self.plot_dayofweek_boxplot(self.gpu_usage_df, y_col="GPU Util(%)", save_path="img/dayofweek_boxplot_gpu.jpg")
        self.plot_hour_boxplot(self.gpu_usage_df, y_col="GPU Util(%)", save_path="img/hour_boxplot_gpu.jpg")
        self.merge_images(
            ["img/timeseries_trend_gpu.jpg", "img/dayofweek_boxplot_gpu.jpg", "img/hour_boxplot_gpu.jpg"],
            direction="vertical",
            save_path="img/combined_image_gpu.jpg"
        )

        self.merge_images(
            ["img/combined_image_cpu.jpg", "img/combined_image_gpu.jpg"],
            direction="horizontal",
            save_path="img/combined_image.jpg"
        )

        if report_to == "slack":
            notificator = SlackNotificator()
            notificator.post_message_with_files("Resource Report", 'img/combined_image.jpg')


if __name__ == "__main__":
    clean_usage()
    report = ResourceReport()
    report.report()
