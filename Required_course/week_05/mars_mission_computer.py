import json
import os
import platform
import shutil
import subprocess
import time


class MissionComputer:
    def __init__(self, settings_path='setting.txt'):
        self.settings_path = settings_path
        self.enabled_keys = self._load_settings()

    def _load_settings(self):
        """Load enabled output keys from setting.txt.

        File format examples:
        - OS_Name=true
        - CPU_Usage=false
        - # comments are ignored
        """
        if not os.path.exists(self.settings_path):
            return None

        enabled = set()

        try:
            with open(self.settings_path, 'r', encoding='utf-8') as file:
                for raw_line in file:
                    line = raw_line.strip()

                    if not line or line.startswith('#'):
                        continue

                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().lower()
                    else:
                        key = line.strip()
                        value = 'true'

                    if value in {'1', 'true', 'yes', 'on'}:
                        enabled.add(key)
        except Exception:
            return None

        return enabled

    def _filter_output(self, payload):
        if self.enabled_keys is None:
            return payload

        return {k: v for k, v in payload.items() if k in self.enabled_keys}

    @staticmethod
    def _bytes_to_gib(size_in_bytes):
        return round(size_in_bytes / (1024 ** 3), 2)

    @staticmethod
    def _run_powershell(command):
        executable = shutil.which('powershell') or shutil.which('pwsh')
        if not executable:
            raise RuntimeError('PowerShell is not available on this system.')

        result = subprocess.run(
            [executable, '-NoProfile', '-Command', command],
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
        return result.stdout.strip()

    def _get_total_memory_bytes(self):
        """Retrieve total physical memory using standard-library approaches."""
        if hasattr(os, 'sysconf'):
            page_size = os.sysconf('SC_PAGE_SIZE')
            page_count = os.sysconf('SC_PHYS_PAGES')
            if isinstance(page_size, int) and isinstance(page_count, int):
                return page_size * page_count

        system_name = platform.system().lower()

        if 'windows' in system_name:
            output = self._run_powershell(
                '(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory'
            )
            if output:
                return int(float(output))

        raise RuntimeError('Unable to detect total memory size.')

    def _get_cpu_usage_percent(self):
        """Estimate CPU usage from load average when available.

        On Unix-like systems this uses 1-minute load normalized by core count.
        """
        if hasattr(os, 'getloadavg'):
            load1, _, _ = os.getloadavg()
            cpu_cores = os.cpu_count() or 1
            usage = (load1 / cpu_cores) * 100
            return round(max(0.0, min(usage, 100.0)), 2)

        # Windows fallback with PowerShell CIM query.
        output = self._run_powershell(
            '(Get-CimInstance Win32_Processor | Measure-Object -Property '
            'LoadPercentage -Average).Average'
        )
        if output:
            return round(float(output), 2)

        raise RuntimeError('Unable to detect CPU usage.')

    def _read_proc_meminfo_total(self):
        with open('/proc/meminfo', 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('MemTotal:'):
                    parts = line.split()
                    return int(parts[1]) * 1024
        raise RuntimeError('MemTotal not found in /proc/meminfo.')

    def _read_proc_meminfo_available(self):
        with open('/proc/meminfo', 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('MemAvailable:'):
                    parts = line.split()
                    return int(parts[1]) * 1024
        raise RuntimeError('MemAvailable not found in /proc/meminfo.')

    def _get_memory_usage_percent(self):
        if os.path.exists('/proc/meminfo'):
            total = self._read_proc_meminfo_total()
            available = self._read_proc_meminfo_available()
            used = total - available
            if total <= 0:
                raise RuntimeError('Invalid total memory from /proc/meminfo.')
            return round((used / total) * 100, 2)

        if platform.system().lower().startswith('windows'):
            total_output = self._run_powershell(
                '(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize'
            )
            free_output = self._run_powershell(
                '(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'
            )

            total_kb = int(float(total_output))
            free_kb = int(float(free_output))

            if total_kb <= 0:
                raise RuntimeError('Invalid total memory from Win32_OperatingSystem.')

            used_kb = total_kb - free_kb
            return round((used_kb / total_kb) * 100, 2)

        raise RuntimeError('Unable to detect memory usage.')

    def get_mission_computer_info(self):
        payload = {
            'OS_Name': None,
            'OS_Version': None,
            'CPU_Type': None,
            'CPU_Cores': None,
            'Total_Memory_Size_GB': None,
            'Errors': {},
        }

        try:
            payload['OS_Name'] = platform.system()
        except Exception as exc:
            payload['Errors']['OS_Name'] = str(exc)

        try:
            payload['OS_Version'] = platform.version()
        except Exception as exc:
            payload['Errors']['OS_Version'] = str(exc)

        try:
            payload['CPU_Type'] = platform.processor() or platform.machine()
        except Exception as exc:
            payload['Errors']['CPU_Type'] = str(exc)

        try:
            payload['CPU_Cores'] = os.cpu_count()
        except Exception as exc:
            payload['Errors']['CPU_Cores'] = str(exc)

        try:
            total_memory_bytes = self._get_total_memory_bytes()
            payload['Total_Memory_Size_GB'] = self._bytes_to_gib(total_memory_bytes)
        except Exception as exc:
            payload['Errors']['Total_Memory_Size_GB'] = str(exc)

        if not payload['Errors']:
            payload.pop('Errors')

        filtered = self._filter_output(payload)
        return json.dumps(filtered, indent=4)

    def get_mission_computer_load(self):
        payload = {
            'CPU_Usage': None,
            'Memory_Usage': None,
            'Timestamp': None,
            'Errors': {},
        }

        try:
            payload['CPU_Usage'] = self._get_cpu_usage_percent()
        except Exception as exc:
            payload['Errors']['CPU_Usage'] = str(exc)

        try:
            payload['Memory_Usage'] = self._get_memory_usage_percent()
        except Exception as exc:
            payload['Errors']['Memory_Usage'] = str(exc)

        try:
            payload['Timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as exc:
            payload['Errors']['Timestamp'] = str(exc)

        if not payload['Errors']:
            payload.pop('Errors')

        filtered = self._filter_output(payload)
        return json.dumps(filtered, indent=4)


if __name__ == '__main__':
    runComputer = MissionComputer(
        settings_path=os.path.join(os.path.dirname(__file__), 'setting.txt')
    )

    print(runComputer.get_mission_computer_info())
    print(runComputer.get_mission_computer_load())
