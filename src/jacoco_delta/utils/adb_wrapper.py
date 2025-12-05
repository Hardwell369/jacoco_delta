"""
ADB封装模块，包含设备信息类和ADB命令封装类
"""

import subprocess
import os
from typing import List, Optional, Tuple


from .logger import get_logger


class DeviceInfo:
    """设备信息类"""
    def __init__(self, serial: str, state: str):
        self.serial = serial
        self.state = state


    def __str__(self):
        return f"Device(serial={self.serial}, state={self.state})"


class AdbError(Exception):
    """ADB相关异常类"""
    pass


class AdbWrapper:
    """ADB命令封装类"""
    
    def __init__(self, adb_path: str = "adb"):
        """
        初始化ADB包装器
        
        Args:
            adb_path: ADB可执行文件路径，默认为系统PATH中的adb
        """
        self.adb_path = adb_path
        self.logger = get_logger("adb_wrapper")


    def _run_adb_command(self, args: List[str], timeout: int = 30) -> Tuple[str, str, int]:
        """
        执行ADB命令
        
        Args:
            args: ADB命令参数列表
            timeout: 命令超时时间（秒）
            
        Returns:
            Tuple[stdout, stderr, return_code]
            
        Raises:
            AdbError: 当ADB命令执行失败时
        """
        cmd = [self.adb_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            raise AdbError(f"ADB command timed out: {' '.join(cmd)}")
        except Exception as e:
            raise AdbError(f"Failed to execute ADB command: {e}")


    def get_connected_devices(self) -> List[DeviceInfo]:
        """
        获取连接的设备列表
        
        Returns:
            设备信息列表
        """
        stdout, stderr, return_code = self._run_adb_command(["devices"])
        
        if return_code != 0:
            raise AdbError(f"Failed to get devices: {stderr}")
        
        devices = []
        lines = stdout.strip().split('\n')
        
        # 跳过第一行标题
        for line in lines[1:]:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    serial, state = parts[0], parts[1]
                    devices.append(DeviceInfo(serial, state))
        
        return devices


    def push_file(self, local_path: str, device_path: str, device_serial: Optional[str] = None):
        """
        向设备推送文件
        
        Args:
            local_path: 本地文件路径
            device_path: 设备上的目标路径
            device_serial: 设备序列号（当连接多个设备时指定）
        """
        if not os.path.exists(local_path):
            raise AdbError(f"Local file does not exist: {local_path}")
        
        args = []
        if device_serial:
            args.extend(["-s", device_serial])
        
        args.extend(["push", local_path, device_path])
        
        stdout, stderr, return_code = self._run_adb_command(args)
        
        if return_code != 0:
            self.logger.error(f"Failed to push file: {stderr}")
            raise AdbError(f"Failed to push file: {stderr}")

        self.logger.info(f"Successfully pushed file: {stdout}")


    def pull_file(self, device_path: str, local_path: str, device_serial: Optional[str] = None):
        """
        从设备拉取文件
        
        Args:
            device_path: 设备上的文件路径
            local_path: 本地目标路径
            device_serial: 设备序列号（当连接多个设备时指定）
        """
        # 确保本地目录存在
        local_dir = os.path.dirname(local_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)
        
        args = []
        if device_serial:
            args.extend(["-s", device_serial])
        
        args.extend(["pull", device_path, local_path])
        
        stdout, stderr, return_code = self._run_adb_command(args)
        
        if return_code != 0:
            self.logger.error(f"Failed to pull file: {stderr}")
            raise AdbError(f"Failed to pull file: {stderr}")

        self.logger.info(f"Successfully pulled file: {stdout}")


    def install_app(self, apk_path: str, device_serial: Optional[str] = None, reinstall: bool = True):
        """
        安装应用
        
        Args:
            apk_path: APK文件路径
            device_serial: 设备序列号（当连接多个设备时指定）
            reinstall: 是否重新安装
        """
        if not os.path.exists(apk_path):
            raise AdbError(f"APK file does not exist: {apk_path}")
        
        args = []
        if device_serial:
            args.extend(["-s", device_serial])
        
        args.append("install")
        if reinstall:
            args.append("-r")
        args.append(apk_path)
        
        stdout, stderr, return_code = self._run_adb_command(args)
        
        if return_code != 0:
            self.logger.error(f"Failed to install app: {stderr}")
            raise AdbError(f"Failed to install app: {stderr}")

        self.logger.info(f"Successfully installed app: {stdout}")


    def uninstall_app(self, package_name: str, device_serial: Optional[str] = None):
        """
        卸载应用
        
        Args:
            package_name: 应用包名
            device_serial: 设备序列号（当连接多个设备时指定）
        """
        args = []
        if device_serial:
            args.extend(["-s", device_serial])
        
        args.extend(["uninstall", package_name])
        
        stdout, stderr, return_code = self._run_adb_command(args)
        
        if return_code != 0:
            self.logger.error(f"Failed to uninstall app: {stderr}")
            raise AdbError(f"Failed to uninstall app: {stderr}")

        self.logger.info(f"Successfully uninstalled app: {stdout}")


    def launch_app(self, package_name: str, device_serial: Optional[str] = None):
        """
        启动应用
        
        Args:
            package_name: 应用包名
            device_serial: 设备序列号（当连接多个设备时指定）
        """
        args = []
        if device_serial:
            args.extend(["-s", device_serial])

        args.extend(["shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"])
        
        stdout, stderr, return_code = self._run_adb_command(args)
        
        if return_code != 0:
            self.logger.error(f"Failed to launch app: {stderr}")
            raise AdbError(f"Failed to launch app: {stderr}")

        self.logger.info(f"Successfully launched app: {stdout}")
    

    def shutdown_app(self, package_name: str, device_serial: Optional[str] = None):
        """
        关闭应用
        
        Args:
            package_name: 应用包名
            device_serial: 设备序列号（当连接多个设备时指定）
        """
        args = []
        if device_serial:
            args.extend(["-s", device_serial])
        
        args.extend(["shell", "am", "force-stop", package_name])
        
        stdout, stderr, return_code = self._run_adb_command(args)
        
        if return_code != 0:
            self.logger.error(f"Failed to shutdown app: {stderr}")
            raise AdbError(f"Failed to shutdown app: {stderr}")

        self.logger.info(f"Successfully shutdown app: {stdout}")


    def clear_app_data(self, package_name: str, device_serial: Optional[str] = None):
        """
        清除应用数据
        
        Args:
            package_name: 应用包名
            device_serial: 设备序列号（当连接多个设备时指定）
            清除数据是否成功
        """
        args = []
        if device_serial:
            args.extend(["-s", device_serial])
        
        args.extend(["shell", "pm", "clear", package_name])
        
        stdout, stderr, return_code = self._run_adb_command(args)
        
        if return_code != 0:
            self.logger.error(f"Failed to clear app data: {stderr}")
            raise AdbError(f"Failed to clear app data: {stderr}")

        self.logger.info(f"Successfully cleared app data: {stdout}")


    def execute_shell_command(self, command: str, device_serial: Optional[str] = None) -> str:
        """
        在设备上执行shell命令
        
        Args:
            command: 要执行的shell命令
            device_serial: 设备序列号（当连接多个设备时指定）
            
        Returns:
            命令执行结果
        """
        args = []
        if device_serial:
            args.extend(["-s", device_serial])
        
        args.extend(["shell", command])
        
        stdout, stderr, return_code = self._run_adb_command(args)
        
        if return_code != 0:
            self.logger.error(f"Failed to execute shell command: {stderr}")
            raise AdbError(f"Failed to execute shell command: {stderr}")
        
        self.logger.info(f"Successfully executed shell command: {stdout}")
        return stdout


    def take_screenshot(self, local_path: str, device_serial: Optional[str] = None):
        """
        截取设备屏幕并保存到本地
        
        Args:
            local_path: 本地保存路径
            device_serial: 设备序列号（当连接多个设备时指定）
        """
        # 确保本地目录存在
        local_dir = os.path.dirname(local_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)
        
        # 在设备上截屏并保存为临时文件
        temp_device_path = "/sdcard/screenshot_tmp.png"
        
        # 截屏命令
        screenshot_cmd = f"screencap -p {temp_device_path}"
        self.execute_shell_command(screenshot_cmd, device_serial)
        
        # 将截图拉取到本地
        success = self.pull_file(temp_device_path, local_path, device_serial)
        
        # 删除设备上的临时文件
        try:
            self.execute_shell_command(f"rm {temp_device_path}", device_serial)
            self.logger.info(f"Successfully deleted temp file: {temp_device_path}")
        except AdbError:
            self.logger.error(f"Failed to delete temp file: {temp_device_path}")
            pass  # 忽略删除临时文件的错误


    def get_logcat(self, lines: int = 100, device_serial: Optional[str] = None) -> str:
        """
        获取设备日志
        
        Args:
            lines: 获取日志的行数
            device_serial: 设备序列号（当连接多个设备时指定）
            
        Returns:
            日志内容
        """
        args = []
        if device_serial:
            args.extend(["-s", device_serial])
        
        args.extend(["logcat", "-d", "-t", str(lines)])
        
        stdout, stderr, return_code = self._run_adb_command(args)
        
        if return_code != 0:
            self.logger.error(f"Failed to get logcat: {stderr}")
            raise AdbError(f"Failed to get logcat: {stderr}")
        
        self.logger.info(f"Successfully got logcat: {stdout}")
        return stdout


    def check_device_connection(self, device_serial: Optional[str] = None) -> bool:
        """
        检查设备连接状态
        
        Args:
            device_serial: 设备序列号（当连接多个设备时指定）
            
        Returns:
            设备是否连接正常
        """
        try:
            devices = self.get_connected_devices()
            if device_serial:
                return any(device.serial == device_serial and device.state == "device" for device in devices)
            else:
                return len([d for d in devices if d.state == "device"]) > 0
        except AdbError:
            return False

