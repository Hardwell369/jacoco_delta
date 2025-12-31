"""
reproducer 模块, 用于自动化重现测试用例, 并收集必要的信息
"""

import os
import time
from typing import Optional, Callable


from .adb_wrapper import AdbWrapper, AdbError
from .logger import get_logger
from .data_types import TestCase, TestResult, TestStatus, TestData, CoverageData


class Reproducer:
    """复现和覆盖率收集类"""
    
    def __init__(self, adb: AdbWrapper, app_package: str, apk_path: str, device_serial: Optional[str] = None):
        """
        初始化复现器
        
        Args:
            adb: AdbWrapper
            app_package: 应用包名
            device_serial: 设备序列号
        """
        self.adb = adb
        self.app_package = app_package
        self.apk_path = apk_path
        self.device_serial = device_serial
        self.data = dict[str, TestData]()  # 存储所有测试数据, 键为测试用例名称
        self.logger = get_logger("reproducer")


    def add_test_case(self, test_case: TestCase) -> None:
        """
        添加测试用例
        
        Args:
            test_case: 测试用例对象
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.data[test_case.name] = TestData(test_case,
                                            TestResult(TestStatus.UNEXECUTED, None, 0.0, timestamp),
                                            TestResult(TestStatus.UNEXECUTED, None, 0.0, timestamp),
                                            CoverageData("", ""),
                                            CoverageData("", ""))


    def setup_test_environment(self, init_operation: Callable):
        """
        设置测试环境
        """
        try:
            # 安装应用
            self.adb.install_app(self.apk_path, self.device_serial)
            
            # # 清除应用数据
            # self.adb.clear_app_data(self.app_package, self.device_serial)
            
            # 启动应用
            self.adb.launch_app(self.app_package, self.device_serial)
            
            # 执行打开app后的初始化操作
            self.logger.info("执行打开app后的初始化操作")
            init_operation()
            self.logger.info("初始化操作执行完成")

            # 等待应用启动
            time.sleep(3)
            self.logger.info("测试环境设置完成")

            return True
        except AdbError as e:
            self.logger.error(f"环境设置失败: {e}")
            raise AdbError(f"环境设置失败: {e}")


    def reset_environment(self):
        """
        重置测试环境到初始状态
        """
        try:
            # 强制停止应用
            self.adb.shutdown_app(self.app_package, self.device_serial)
            
            # # 清除应用数据
            # self.adb.clear_app_data(self.app_package, self.device_serial)

            # 卸载应用
            self.adb.uninstall_app(self.app_package, self.device_serial)

            self.logger.info("测试环境已重置")
        except AdbError as e:
            self.logger.error(f"环境重置失败: {e}")
            raise AdbError(f"环境重置失败: {e}")


    # def execute_test_case(self,
    #                     test_case: TestCase, 
    #                     output_dir: str,
    #                     ec_file_generator: Callable,
    #                     ec_file_path: str,
    #                     jacococli_jar_path: str, 
    #                     app_classfiles_path: str, 
    #                     app_source_path: str,
    # ) -> TestResult:
    #     """
    #     执行单个测试用例
        
    #     Args:
    #         test_case: 要执行的测试用例
            
    #     Returns:
    #         测试结果对象
    #     """
    #     start_time = time.time()
    #     timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
    #     try:
    #         # 执行前置条件
    #         self.logger.info(f"开始执行测试用例: {test_case.name} 的前置条件")
    #         test_case.preconditions()
    #         self.logger.info(f"测试用例执行完成: {test_case.name} 的前置条件")
    #         # 收集覆盖率数据
    #         # self.logger.info(f"开始收集测试用例: {test_case.name} 的前置条件的覆盖率数据")
    #         # precondition_output_dir = os.path.join(output_dir, f"{test_case.name}_precondition")
    #         # os.makedirs(precondition_output_dir, exist_ok=True)
    #         # precondition_coverage_data =  self.collect_coverage_data(ec_file_generator,
    #         #                                                         ec_file_path,
    #         #                                                         precondition_output_dir,
    #         #                                                         jacococli_jar_path, 
    #         #                                                         app_classfiles_path, 
    #         #                                                         app_source_path,
    #         #                                                         test_case.name)
    #         # self.data[test_case.name].precondition_coverage_data = precondition_coverage_data
            
    #         # self.logger.info(f"测试用例: {test_case.name} 的前置条件的覆盖率数据收集完成, 保存至: {precondition_coverage_data.xml_path}")

    #         # 执行属性
    #         self.logger.info(f"开始执行测试用例: {test_case.name} 的属性")
    #         test_case.property()
    #         self.logger.info(f"测试用例执行完成: {test_case.name} 的属性")
    #         # 收集覆盖率数据
    #         # self.logger.info(f"开始收集测试用例: {test_case.name} 的属性的覆盖率数据")
    #         # property_output_dir = os.path.join(output_dir, f"{test_case.name}_property")
    #         # os.makedirs(property_output_dir, exist_ok=True)
    #         # property_coverage_data =  self.collect_coverage_data(ec_file_generator,
    #         #                                                     ec_file_path,
    #         #                                                     property_output_dir,
    #         #                                                     jacococli_jar_path, 
    #         #                                                     app_classfiles_path, 
    #         #                                                     app_source_path,
    #         #                                                     test_case.name)
    #         # self.data[test_case.name].property_coverage_data = property_coverage_data
            
    #         # self.logger.info(f"测试用例: {test_case.name} 的属性的覆盖率数据收集完成, 保存至: {property_coverage_data.xml_path}")

    #         status = TestStatus.SUCCESS
    #         error_message = None

    #     except Exception as e:
    #         status = TestStatus.ERROR
    #         error_message = str(e)
    #     finally:
    #         # 收集覆盖率数据
    #         self.logger.info(f"开始收集测试用例: {test_case.name} 的前置条件的覆盖率数据")
    #         precondition_output_dir = os.path.join(output_dir, f"{test_case.name}_precondition")
    #         os.makedirs(precondition_output_dir, exist_ok=True)
    #         precondition_coverage_data =  self.collect_coverage_data(ec_file_generator,
    #                                                                 ec_file_path,
    #                                                                 precondition_output_dir,
    #                                                                 jacococli_jar_path, 
    #                                                                 app_classfiles_path, 
    #                                                                 app_source_path,
    #                                                                 test_case.name)
    #         self.data[test_case.name].precondition_coverage_data = precondition_coverage_data

    #         # 收集覆盖率数据
    #         self.logger.info(f"开始收集测试用例: {test_case.name} 的属性的覆盖率数据")
    #         property_output_dir = os.path.join(output_dir, f"{test_case.name}_property")
    #         os.makedirs(property_output_dir, exist_ok=True)
    #         property_coverage_data =  self.collect_coverage_data(ec_file_generator,
    #                                                             ec_file_path,
    #                                                             property_output_dir,
    #                                                             jacococli_jar_path, 
    #                                                             app_classfiles_path, 
    #                                                             app_source_path,
    #                                                             test_case.name)
    #         self.data[test_case.name].property_coverage_data = property_coverage_data
        
    #     execution_time = time.time() - start_time
        
    #     result = TestResult(
    #         status=status,
    #         error_message=error_message if status == TestStatus.ERROR else None,
    #         execution_time=execution_time,
    #         timestamp=timestamp
    #     )
        
    #     self.data[test_case.name].result = result
    #     return result

    def execute_test_case(self,
                        test_case: TestCase, 
                        output_dir: str,
                        ec_file_generator: Callable,
                        ec_file_path: str,
                        jacococli_jar_path: str, 
                        app_classfiles_path: str, 
                        app_source_path: str,
    ) -> None:
        """
        执行单个测试用例
        
        Args:
            test_case: 要执行的测试用例
            output_dir: 测试用例输出目录
            ec_file_generator: 覆盖率数据生成器
            ec_file_path: 覆盖率数据文件路径
            jacococli_jar_path: JaCoCo CLI JAR路径
            app_classfiles_path: app编译后的类文件路径
            app_source_path: app源代码路径

        Returns:
            测试结果对象
        """
        start_time = time.time()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        precondition_status = TestStatus.SUCCESS
        precondition_error_message = None

        property_status = TestStatus.SUCCESS
        property_error_message = None

        try:
            # 执行前置条件
            self.logger.info(f"开始执行测试用例: {test_case.name} 的前置条件")
            test_case.preconditions()
            self.logger.info(f"测试用例执行完成: {test_case.name} 的前置条件")

        except Exception as e:
            precondition_status = TestStatus.ERROR
            precondition_error_message = str(e)
        finally:
            # 收集覆盖率数据
            self.logger.info(f"开始收集测试用例: {test_case.name} 的前置条件的覆盖率数据")
            precondition_output_dir = os.path.join(output_dir, f"{test_case.name}_precondition")
            os.makedirs(precondition_output_dir, exist_ok=True)
            precondition_coverage_data =  self.collect_coverage_data(ec_file_generator,
                                                                    ec_file_path,
                                                                    precondition_output_dir,
                                                                    jacococli_jar_path, 
                                                                    app_classfiles_path, 
                                                                    app_source_path,
                                                                    test_case.name)
            self.data[test_case.name].precondition_coverage_data = precondition_coverage_data
            # 记录前置条件执行结果
            precondition_result = TestResult(
                status=precondition_status,
                error_message=precondition_error_message if precondition_status == TestStatus.ERROR else None,
                execution_time=time.time() - start_time,
                timestamp=timestamp
            )
            self.data[test_case.name].precondition_result = precondition_result

        try:
            # 执行属性
            self.logger.info(f"开始执行测试用例: {test_case.name} 的属性")
            test_case.property()
            self.logger.info(f"测试用例执行完成: {test_case.name} 的属性")
        except Exception as e:
            property_status = TestStatus.ERROR
            property_error_message = str(e)
        finally:
            # 收集覆盖率数据
            self.logger.info(f"开始收集测试用例: {test_case.name} 的属性的覆盖率数据")
            property_output_dir = os.path.join(output_dir, f"{test_case.name}_property")
            os.makedirs(property_output_dir, exist_ok=True)
            property_coverage_data =  self.collect_coverage_data(ec_file_generator,
                                                                ec_file_path,
                                                                property_output_dir,
                                                                jacococli_jar_path, 
                                                                app_classfiles_path, 
                                                                app_source_path,
                                                                test_case.name)
            self.data[test_case.name].property_coverage_data = property_coverage_data
            # 记录属性执行结果
            property_result = TestResult(
                status=property_status,
                error_message=property_error_message if property_status == TestStatus.ERROR else None,
                execution_time=time.time() - start_time,
                timestamp=timestamp
            )
            self.data[test_case.name].property_result = property_result


    def collect_coverage_data(self,
                            ec_file_generator: Callable,
                            ec_file_path: str,
                            output_dir: str,
                            jacococli_jar_path: str, 
                            app_classfiles_path: str, 
                            app_source_path: str,
                            test_case_name: str,
    ) -> CoverageData:
        """
        收集JaCoCo覆盖率数据
        
        Args:
            ec_file_generator: 覆盖率数据生成器
            ec_file_path: 覆盖率文件在设备上的路径
            output_dir: 覆盖率文件的保存目录路径
            jacococli_jar_path: JaCoCo CLI JAR路径
            app_classfiles_path: app编译后的类文件路径
            app_source_path: app源代码路径
            test_case_name: 关联的测试用例名称
            
        Returns:
            覆盖率数据对象
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        ec_file_type = ec_file_path.split(".")[-1]
        output_file_path = f"{output_dir}/{test_case_name}.{ec_file_type}"
        
        try:
            # 生成覆盖率文件
            self.logger.info(f"开始生成覆盖率文件操作")
            ec_file_generator()
            self.logger.info(f"完成生成覆盖率文件操作")

            # 从设备拉取覆盖率文件
            self.adb.pull_file(ec_file_path, output_file_path, self.device_serial)

            # 将.ec文件转换为XML格式（需要JaCoCo CLI工具）
            self.convert_ec_to_xml(output_file_path, output_file_path.replace(f".{ec_file_type}", ".xml"),
                                jacococli_jar_path, app_classfiles_path, app_source_path)
            
            coverage_data = CoverageData(
                xml_path=output_file_path.replace(f".{ec_file_type}", ".xml"),
                timestamp=timestamp
            )
            
            # self.data[test_case_name].coverage_data.append(coverage_data)
            self.logger.info(f"覆盖率数据已收集: {coverage_data.xml_path}")
            return coverage_data
            
        except AdbError as e:
            self.logger.error(f"收集覆盖率数据失败: {e}")
            raise


    def convert_ec_to_xml(self, ec_file_path: str, 
                        xml_path: str, 
                        jacococli_jar_path: str, 
                        app_classfiles_path: str, 
                        app_source_path: str
    ) -> None:
        """
        将.ec覆盖率文件转换为XML格式
        
        Args:
            ec_file_path: .ec文件路径
            xml_path: 输出的XML文件路径
            jacococli_jar_path: JaCoCo CLI JAR路径
            app_classfiles_path: app编译后的类文件路径
            app_source_path: app源代码路径
        """
        import shutil
        import subprocess

        # 检查输入文件是否存在
        if not os.path.exists(ec_file_path):
            raise FileNotFoundError(f"输入的.ec文件不存在: {ec_file_path}")

        # 检查Java环境
        if not shutil.which("java"):
            raise EnvironmentError("未找到Java环境, 请确保已安装Java并配置了PATH")
        
        output_dir = os.path.dirname(xml_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 构建命令
        cmd = [
            "java", "-jar", jacococli_jar_path, "report", ec_file_path,
            "--classfiles", app_classfiles_path,
            "--sourcefiles", app_source_path,
            "--xml", xml_path
        ]
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )
            
            # 检查执行结果
            if result.returncode != 0:
                error_msg = f"JaCoCo转换失败: {result.stderr}"
                # 创建一个简单的占位XML文件, 避免后续处理出错
                self._create_placeholder_xml(xml_path, error_msg)
                raise RuntimeError(error_msg)
                
            self.logger.info(f"成功转换覆盖率文件: {ec_file_path} -> {xml_path}")
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("JaCoCo转换超时（超过5分钟）")
        except Exception as e:
            # 创建一个简单的占位XML文件, 避免后续处理出错
            self._create_placeholder_xml(xml_path, str(e))
            raise RuntimeError(f"JaCoCo转换过程中发生错误: {str(e)}")


    def _create_placeholder_xml(self, xml_path: str, error_message: str) -> None:
        """
        创建占位XML文件, 当转换失败时使用
        
        Args:
            xml_path: XML文件路径
            error_message: 错误信息
        """
        try:
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
                f.write('<!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">\n')
                f.write('<report name="Coverage Report">\n')
                f.write(f'  <sessioninfo id="placeholder-error" start="0" dump="0">\n')
                f.write(f'    <error>{error_message}</error>\n')
                f.write(f'  </sessioninfo>\n')
                f.write('</report>\n')
        except Exception:
            # 即使创建占位文件失败, 也不应该影响主流程
            pass


    def reproduce_test_case(self, 
                        test_case: TestCase, 
                        output_dir: str,
                        ec_file_generator: Callable,
                        ec_file_path: str,
                        jacococli_jar_path: str, 
                        app_classfiles_path: str, 
                        app_source_path: str,
                        init_operation: Callable,
    ) -> TestData:
        """
        复现特定测试用例并收集覆盖率数据
        
        Args:
            test_case: 测试用例
            
        Returns:
            测试结果
        """
        self.logger.info(f"开始复现测试用例: {test_case.name}")
        
        # 设置测试环境
        if not self.setup_test_environment(init_operation):
            raise Exception("无法设置测试环境")
        
        try:
            # 添加测试用例
            self.add_test_case(test_case)
            # 执行测试用例
            self.execute_test_case(test_case,
                                    output_dir,
                                    ec_file_generator,
                                    ec_file_path,
                                    jacococli_jar_path, 
                                    app_classfiles_path, 
                                    app_source_path)

            return self.data[test_case.name]
            
        finally:
            # 重置环境
            self.reset_environment()

