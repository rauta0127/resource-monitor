import pandas as pd
from abc import ABC, abstractmethod
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from PIL import Image
from slack import SlackNotificator
from clean_usage import clean_usage

class ResourceReport(ABC):
    def __init__(self, cpu_usage_filepath: str = "cpu_usage.csv", gpu_usage_filepath: str = "gpu_usage.csv"):
        self.cpu_usage_filepath = cpu_usage_filepath
        self.gpu_usage_filepath = gpu_usage_filepath
        self.cpu_usage_df = pd.read_csv(self.cpu_usage_filepath)
        self.gpu_usage_df = pd.read_csv(self.gpu_usage_filepath)
        self.cpu_usage_df['Timestamp'] = pd.to_datetime(self.cpu_usage_df['Timestamp'], errors='coerce')
        self.gpu_usage_df['Timestamp'] = pd.to_datetime(self.gpu_usage_df['Timestamp'], errors='coerce')

    def get_past_days_usage(self, usage_df: pd.DataFrame, past_days: int = 1):
        usage_df['Date'] = usage_df['Timestamp'].dt.floor('D')
        last_date = usage_df['Date'].max()
        start_date = last_date - pd.Timedelta(days=past_days)
        past_days_usage_df = usage_df[usage_df['Date'] >= start_date]
        past_days_usage_df = past_days_usage_df.drop(columns='Date')
        return past_days_usage_df
    
    def _custom_date_formatter(self, x, pos):
        timestamp = mdates.num2date(x)  # タイムスタンプをdatetimeに変換
        if timestamp.hour == 0:  # 0時の場合、日付、曜日を表示
            return timestamp.strftime('%m-%d (%a)')
        else:  # それ以外の時間は時間のみを表示
            return timestamp.strftime('%H')

    def plot_timeseries_trend(self, usage_df: pd.DataFrame, y_col: str, past_days: int = 8, color: str = "blue", save_path: str = "timeseries_trend.jpg"):
        past_days_usage_df = self.get_past_days_usage(usage_df, past_days=past_days)
        hostnames = sorted(past_days_usage_df['Hostname'].unique())

        ncols = 2
        nrows = (len(hostnames) + 1) // ncols
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(14, 3 * nrows), sharex=True)

        # Hostnameごとにプロットを作成
        for i in range(nrows*ncols):

            ax = axes[i // ncols, i % ncols]  # 2列に分割されたグリッドに配置
            if i < len(hostnames):
                hostname = hostnames[i]
                sns.lineplot(x='Timestamp', y=y_col, data=past_days_usage_df[past_days_usage_df['Hostname'] == hostname], ax=ax, marker=None, color=color)
                ax.set_title(f'{y_col} Trend for {hostname}')
                ax.set_xlabel('Time')
                ax.set_ylabel(f'{y_col}')

            # Y軸の範囲を固定
            ax.set_ylim(0, 100)
            
            # X軸のフォーマットを設定 (6時間ごとの主目盛り、必ず0時、6時、12時、18時が表示されるように設定)
            ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))  # 0時, 12時に主目盛り
            ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))  # 補助目盛りは6時間ごと

            # カスタムフォーマッタを設定
            ax.xaxis.set_major_formatter(FuncFormatter(self._custom_date_formatter))
            
            # X軸のラベル回転
            ax.tick_params(axis='x', rotation=90)

            # 補助線 (点線) の追加
            ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.5)  # 主目盛りの補助線は実線
            ax.grid(True, which='minor', axis='x', linestyle=':', linewidth=0.5)  # 補助目盛りの補助線は点線

        plt.tight_layout()
        plt.savefig(save_path, dpi=200)

    def plot_dayofweek_boxplot(self, usage_df: pd.DataFrame, y_col: str, past_days: int = 28, color: str = "blue", save_path: str = "dayofweek_boxplot.jpg"):
        past_days_usage_df = self.get_past_days_usage(usage_df, past_days=past_days)
        hostnames = sorted(past_days_usage_df['Hostname'].unique())

        past_days_usage_df['dayofweek'] = past_days_usage_df['Timestamp'].dt.dayofweek
        past_days_usage_df['dayofweek'] = past_days_usage_df['dayofweek'].map(lambda x: {
            0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
        }[x])
        ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        past_days_usage_df['dayofweek'] = pd.Categorical(past_days_usage_df['dayofweek'], categories=ordered_days, ordered=True)


        past_days_usage_df2 = self.get_past_days_usage(usage_df, past_days=7)

        past_days_usage_df2['dayofweek'] = past_days_usage_df2['Timestamp'].dt.dayofweek
        past_days_usage_df2['dayofweek'] = past_days_usage_df2['dayofweek'].map(lambda x: {
            0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
        }[x])
        ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        past_days_usage_df2['dayofweek'] = pd.Categorical(past_days_usage_df2['dayofweek'], categories=ordered_days, ordered=True)

        ncols = 2
        nrows = (len(hostnames) + 1) // ncols
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(14, 3 * nrows), sharex=True)

        # Hostnameごとにプロットを作成
        for i in range(nrows*ncols):

            ax = axes[i // ncols, i % ncols]  # 2列に分割されたグリッドに配置
            if i < len(hostnames):
                hostname = hostnames[i]
                sns.stripplot(x='dayofweek', y=y_col, data=past_days_usage_df[past_days_usage_df['Hostname'] == hostname], ax=ax, color=color)
                sns.stripplot(x='dayofweek', y=y_col, data=past_days_usage_df2[past_days_usage_df2['Hostname'] == hostname], ax=ax, color="orange")
                ax.set_title(f'{y_col} Trend for {hostname}')
                ax.set_xlabel('Time')
                ax.set_ylabel(f'{y_col}')

            # Y軸の範囲を固定
            ax.set_ylim(0, 100)
            
            # X軸のラベル回転
            ax.tick_params(axis='x', rotation=90)

            # 補助線 (点線) の追加
            ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.5)  # 主目盛りの補助線は実線

        plt.tight_layout()
        plt.savefig(save_path, dpi=200)

    def plot_hour_boxplot(self, usage_df: pd.DataFrame, y_col: str, past_days: int = 28, color: str = "blue", save_path: str = "hour_boxplot.jpg"):
        past_days_usage_df = self.get_past_days_usage(usage_df, past_days=past_days)
        past_days_usage_df['hour'] = past_days_usage_df['Timestamp'].dt.hour

        past_days_usage_df2 = self.get_past_days_usage(usage_df, past_days=7)
        past_days_usage_df2['hour'] = past_days_usage_df2['Timestamp'].dt.hour

        hostnames = sorted(past_days_usage_df['Hostname'].unique())

        ncols = 2
        nrows = (len(hostnames) + 1) // ncols
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(14, 3 * nrows), sharex=True)

        # Hostnameごとにプロットを作成
        for i in range(nrows*ncols):

            ax = axes[i // ncols, i % ncols]  # 2列に分割されたグリッドに配置
            if i < len(hostnames):
                hostname = hostnames[i]
                sns.stripplot(x='hour', y=y_col, data=past_days_usage_df[past_days_usage_df['Hostname'] == hostname], ax=ax, color=color)
                sns.stripplot(x='hour', y=y_col, data=past_days_usage_df2[past_days_usage_df2['Hostname'] == hostname], ax=ax, color="orange")
                ax.set_title(f'{y_col} Stripplot for {hostname}')
                ax.set_xlabel('Time')
                ax.set_ylabel(f'{y_col}')

            # Y軸の範囲を固定
            ax.set_ylim(0, 100)
            
            # X軸のラベル回転
            ax.tick_params(axis='x', rotation=90)

            # 補助線 (点線) の追加
            ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.5)  # 主目盛りの補助線は実線

        plt.tight_layout()
        plt.savefig(save_path, dpi=200)

    def merge_plot_vertical(self, image_files: list, save_path: str = 'combined_image_vertical.jpg'):
        images = [Image.open(img) for img in image_files]

        # 個々の画像サイズを取得して最大幅と合計高さを計算
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)

        # 合計サイズの空のキャンバスを作成
        new_image = Image.new('RGB', (max_width, total_height))

        # 画像をキャンバスに貼り付けて配置
        y_offset = 0
        for img in images:
            new_image.paste(img, (0, y_offset))
            y_offset += img.height

        new_image.save(save_path)

    def merge_plot_horizontal(self, image_files: list, save_path: str = 'combined_image_horizontal.jpg'):
        images = [Image.open(img) for img in image_files]

        # 個々の画像サイズを取得して合計幅と最大高さを計算
        total_width = sum(img.width for img in images)
        max_height = max(img.height for img in images)

        # 合計サイズの空のキャンバスを作成
        new_image = Image.new('RGB', (total_width, max_height))

        # 画像をキャンバスに貼り付けて配置
        x_offset = 0
        for img in images:
            new_image.paste(img, (x_offset, 0))
            x_offset += img.width

        new_image.save(save_path)

    def report(self, report_to: str = "slack"):
        report = ResourceReport()
        cpu_usage_df = report.cpu_usage_df
        report.plot_timeseries_trend(cpu_usage_df, y_col="CPU Usage(%)", save_path="img/timeseries_trend_cpu.jpg")
        report.plot_dayofweek_boxplot(cpu_usage_df, y_col="CPU Usage(%)", save_path="img/dayofweek_boxplot_cpu.jpg")
        report.plot_hour_boxplot(cpu_usage_df, y_col="CPU Usage(%)", save_path="img/hour_boxplot_cpu.jpg")
        report.merge_plot_vertical(["img/timeseries_trend_cpu.jpg", "img/dayofweek_boxplot_cpu.jpg", "img/hour_boxplot_cpu.jpg"], save_path='img/combined_image_cpu.jpg')
        gpu_usage_df = report.gpu_usage_df
        report.plot_timeseries_trend(gpu_usage_df, y_col="GPU Util(%)", save_path="img/timeseries_trend_gpu.jpg")
        report.plot_dayofweek_boxplot(gpu_usage_df, y_col="GPU Util(%)", save_path="img/dayofweek_boxplot_gpu.jpg")
        report.plot_hour_boxplot(gpu_usage_df, y_col="GPU Util(%)", save_path="img/hour_boxplot_gpu.jpg")
        report.merge_plot_vertical(["img/timeseries_trend_gpu.jpg", "img/dayofweek_boxplot_gpu.jpg", "img/hour_boxplot_gpu.jpg"], save_path='img/combined_image_gpu.jpg')
        report.merge_plot_horizontal(["img/combined_image_cpu.jpg", "img/combined_image_gpu.jpg"], save_path='img/combined_image.jpg')
        notificator = SlackNotificator()
        message = "Resource Report"
        filepath = 'img/combined_image.jpg'
        notificator.post_message_with_files(message, filepath)


if __name__ == "__main__":
    clean_usage()
    report = ResourceReport()
    report.report()
