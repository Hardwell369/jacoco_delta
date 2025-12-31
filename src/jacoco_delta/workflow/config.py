"""
配置文件
"""
import os
import time
from typing import Optional

from jacoco_delta.utils.logger import get_logger


class Config:
    """配置类"""

    def __init__(self, app_package: str, 
            apk_path: str,
            app_source_dir: str, 
            app_classfiles_dir: str, 
            ec_file_path: str,
            report_output_dir: str,
            device_serial: Optional[str] = None, 
            adb_path: str = "adb",
            jacococli_jar_path: str = ""
    ):
        """
        初始化配置类
        
        Args:
            app_package: app包名
            apk_path: apk文件路径
            app_source_dir: app源代码路径
            app_classfiles_dir: app编译后的类文件路径
            ec_file_path: 覆盖率数据文件路径(在设备上的路径)
            report_output_dir: 报告输出路径(必须为文件夹路径)
            device_serial: 设备序列号, 默认为None, 则使用默认设备
            adb_path: ADB路径, 默认为None, 则使用系统环境变量中的adb
            jacococli_jar_path: JaCoCo CLI JAR路径, 默认为None, 则使用项目根目录下的jacococli.jar
        """
        self.app_package = app_package
        self.apk_path = apk_path
        self.app_source_dir = app_source_dir
        self.app_classfiles_dir = app_classfiles_dir
        self.ec_file_path = ec_file_path
        self.report_output_dir = report_output_dir
        self.device_serial = device_serial
        self.adb_path = adb_path
        self.jacococli_jar_path = jacococli_jar_path
        self.logger = get_logger("config")

        os.makedirs(self.report_output_dir, exist_ok=True)

        if not self.adb_path:
            self.adb_path = "adb"

        if not self.jacococli_jar_path:
            self._default_jacococli_jar_path()

        self._check_config_validity()

        self.logger.info(f"配置初始化完成, 应用包名: {self.app_package}, \
                        APK路径: {self.apk_path}, \
                        源代码目录: {self.app_source_dir}, \
                        类文件目录: {self.app_classfiles_dir}, \
                        覆盖率数据路径: {self.ec_file_path}, \
                        报告输出目录: {self.report_output_dir}, \
                        设备序列号: {self.device_serial}, \
                        ADB路径: {self.adb_path}, \
                        JaCoCo CLI JAR路径: {self.jacococli_jar_path}".replace(" ", "").replace(",", "\n"))


    def _default_jacococli_jar_path(self):
        """
        获取JaCoCo CLI JAR路径
        默认使用本项目下的jacococli.jar
        """
        current_file_abs_path = os.path.abspath(__file__)
        src_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_abs_path)))
        project_root = os.path.dirname(src_root)
        jar_path = os.path.join(project_root, "jacococli.jar")
        if not os.path.exists(jar_path):
            raise FileNotFoundError(f"Jacoco CLI JAR路径不存在: {jar_path}, 请检查项目根目录是否包含jacococli.jar")
        self.jacococli_jar_path = jar_path


    def _check_config_validity(self):
        """检查配置是否完整, 且路径是否存在"""
        # 检查是否有任何属性为空
        if not all([self.app_package, self.apk_path, self.app_source_dir, self.app_classfiles_dir]):
            raise ValueError("配置中存在空值，请检查app_package, apk_path, app_source_dir, app_classfiles_dir")

        # 检查路径是否存在
        for path in [self.app_source_dir, self.app_classfiles_dir]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"路径不存在: {path}")

    