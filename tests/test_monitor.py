import unittest
from unittest.mock import patch, MagicMock
import os
import csv
import tempfile
from monitor import CPUMonitor, GPUMonitor

class TestResourceMonitor(unittest.TestCase):
    @patch('os.uname')
    @patch('platform.system')
    def test_get_hostname(self, mock_platform, mock_uname):
        mock_uname.return_value = ['dummy', 'host', 'dummy', 'dummy', 'dummy']
        monitor = CPUMonitor("dummy.csv")
        self.assertEqual(monitor.get_hostname(), 'host')

    @patch('psutil.cpu_percent')
    def test_get_cpu_usage(self, mock_cpu_percent):
        mock_cpu_percent.return_value = 50.0
        monitor = CPUMonitor("dummy.csv")
        self.assertEqual(monitor.get_cpu_usage(), 50.0)

    @patch('os.getloadavg')
    def test_get_loadavg(self, mock_getloadavg):
        mock_getloadavg.return_value = (1.0, 0.5, 0.3)
        monitor = CPUMonitor("dummy.csv")
        self.assertEqual(monitor.get_loadavg(), (1.0, 0.5, 0.3))

    @patch('psutil.virtual_memory')
    def test_get_memory_usage(self, mock_virtual_memory):
        mock_virtual_memory.return_value = MagicMock(total=2048 * (1024 ** 2), used=1024 * (1024 ** 2), free=1024 * (1024 ** 2))
        monitor = CPUMonitor("dummy.csv")
        total_memory, used_memory, free_memory = monitor.get_memory_usage()
        self.assertEqual(total_memory, 2048)
        self.assertEqual(used_memory, 1024)
        self.assertEqual(free_memory, 1024)

    @patch('subprocess.run')
    def test_get_top_cpu_users(self, mock_subprocess):
        mock_subprocess.return_value.stdout = "user1,20.0\nuser2,15.0\nuser3,10.0"
        monitor = CPUMonitor("dummy.csv")
        top_users = monitor.get_top_cpu_users()
        self.assertEqual(top_users, [['user1', 20.0], ['user2', 15.0], ['user3', 10.0]])

    @patch('os.path.exists')
    @patch('builtins.open')
    def test_check_existing_csv(self, mock_open, mock_exists):
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value = MagicMock()
        monitor = CPUMonitor("dummy.csv")
        monitor.COLUMNS = ['Column1', 'Column2']
        self.assertTrue(monitor.check_existing_csv())

    @patch('os.path.exists')
    @patch('builtins.open')
    def test_create_csv(self, mock_open, mock_exists):
        mock_exists.return_value = False
        monitor = CPUMonitor("dummy.csv")
        monitor.COLUMNS = ['Column1', 'Column2']
        monitor.create_csv()
        mock_open.assert_called_once_with("dummy.csv", mode='w', newline='')

    @patch('os.path.exists')
    @patch('builtins.open')
    def test_save(self, mock_open, mock_exists):
        mock_exists.return_value = True
        monitor = CPUMonitor("dummy.csv")
        monitor.save(["data1", "data2"])
        mock_open.assert_called_once_with("dummy.csv", mode='a', newline='')

    @patch('subprocess.run')
    def test_gpu_monitor(self, mock_subprocess):
        mock_subprocess.return_value.stdout = "0, GeForce GTX 1080, 50, 150, 250, 2000, 8192, 80"
        gpu_monitor = GPUMonitor("gpu_usage.csv")
        gpu_monitor.monitor()
        # Check if the CSV is created or appended correctly
        with open("gpu_usage.csv", mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)
            self.assertEqual(len(rows), 1)  # Only 1 entry should exist for this test

if __name__ == "__main__":
    unittest.main()
