"""
工作流运行器模块, 负责协调整个覆盖率差异分析流程
"""

import os
import time
from typing import List, Tuple, Callable

from .config import Config
from ..utils.adb_wrapper import AdbWrapper
from ..utils.data_types import *
from ..utils.reproducer import Reproducer
from ..utils.logger import configure_logger, get_logger
from ..core.parser import parse_jacoco_line_coverage, parse_jacoco_branch_coverage
from ..core.differ import compare_line_diff, compare_branch_diff
from ..core.calculator import calculate_line_coverage_increment, calculate_branch_coverage_increment
from ..utils.report_generator import ReportGenerator

class WorkflowRunner:
    """工作流运行器, 协调整个覆盖率差异分析流程"""

    def __init__(self, config: Config, init_operation: Callable = lambda: None, ec_file_generator: Callable = lambda: None):
        """
        初始化工作流运行器
        
        Args:
            config: 配置对象
            init_operation: 初始化操作函数
            ec_file_generator: 覆盖率文件生成函数
        """
        self.config = config
        self.init_operation = init_operation
        self.ec_file_generator = ec_file_generator
        self.reproducer = Reproducer(AdbWrapper(config.adb_path), config.app_package, config.apk_path, config.device_serial)
        self.report_generator = ReportGenerator(self.config.app_source_dir)
        configure_logger(self.config.report_output_dir, "workflow.log")
        self.logger = get_logger("runner")


    def run_full_analysis(self, pair_test_cases: List[PairTestCase]) -> FullAnalysisResult:
        """
        执行完整的覆盖率差异分析流程
        
        Args:
            pair_test_cases: 成对测试用例列表
            
        Returns:
            完整分析结果对象
        """
        if len(pair_test_cases) == 0:
            raise ValueError("成对测试用例列表不能为空")
        
        self.logger.info("开始执行完整的覆盖率差异分析...")
        
        pair_results = []
        
        # 按顺序处理每一对测试用例
        for i, pair_case in enumerate(pair_test_cases):
            self.logger.info(f"处理第 {i+1} 对测试用例: {pair_case.bug_case.name} <-> {pair_case.correct_case.name}")
            
            # 为每对测试用例创建独立的输出目录
            case_output_dir = os.path.join(
                self.config.report_output_dir, 
                pair_case.case_name
            )
            os.makedirs(case_output_dir, exist_ok=True)
            
            # 执行成对测试用例分析
            pair_result = self._run_pair_analysis(
                pair_case, self.init_operation, self.ec_file_generator, case_output_dir
            )
            pair_results.append(pair_result)
        
        full_result = FullAnalysisResult(
            pair_results=pair_results,
        )
        
        # 生成总体报告
        reproducer_data = self.reproducer.data
        output_dir = self.config.report_output_dir
        self.report_generator.generate_comprehensive_report(full_result, reproducer_data, output_dir)
        self.logger.info(f"完整分析完成, 共处理 {len(pair_test_cases)} 对测试用例, 结果保存在: {output_dir}")
        return full_result


    def _run_pair_analysis(self, 
                        pair_case: PairTestCase,
                        init_operation: Callable, 
                        ec_file_generator: Callable,
                        output_dir: str
    ) -> PairAnalysisResult:
        """
        执行成对测试用例分析
        
        Args:
            pair_case: 成对测试用例
            output_dir: 输出目录
            
        Returns:
            成对分析结果, 行覆盖率差异报告路径, 分支覆盖率差异报告路径
        """
        self.logger.info(f"执行成对测试用例分析: {pair_case.bug_case.name} <-> {pair_case.correct_case.name}")
        
        # 1. 执行bug复现流程并收集覆盖率数据
        self.logger.info("1. 执行bug复现流程...")
        bug_precondition_xml, bug_property_xml = self._run_single_flow(
            pair_case.bug_case, init_operation, ec_file_generator, output_dir
        )
        
        # 2. 执行正确流程并收集覆盖率数据
        self.logger.info("2. 执行正确流程...")
        correct_precondition_xml, correct_property_xml = self._run_single_flow(
            pair_case.correct_case, init_operation, ec_file_generator, output_dir
        )
        
        # 3. 解析XML覆盖率文件
        self.logger.info("3. 解析覆盖率数据...")
        bug_precondition_line_cov = parse_jacoco_line_coverage(bug_precondition_xml)
        bug_precondition_branch_cov = parse_jacoco_branch_coverage(bug_precondition_xml)
        bug_property_line_cov = parse_jacoco_line_coverage(bug_property_xml)
        bug_property_branch_cov = parse_jacoco_branch_coverage(bug_property_xml)
        
        correct_precondition_line_cov = parse_jacoco_line_coverage(correct_precondition_xml)
        correct_precondition_branch_cov = parse_jacoco_branch_coverage(correct_precondition_xml)
        correct_property_line_cov = parse_jacoco_line_coverage(correct_property_xml)
        correct_property_branch_cov = parse_jacoco_branch_coverage(correct_property_xml)
        
        # 4. 计算覆盖率增量
        self.logger.info("4. 计算覆盖率增量...")
        bug_incremental = self._calculate_incremental_coverage(
            bug_precondition_line_cov, bug_precondition_branch_cov,
            bug_property_line_cov, bug_property_branch_cov
        )
        correct_incremental = self._calculate_incremental_coverage(
            correct_precondition_line_cov, correct_precondition_branch_cov,
            correct_property_line_cov, correct_property_branch_cov
        )
        
        # 5. 执行增量差异分析
        self.logger.info("5. 执行增量差异分析...")
        diff_result = self._perform_diff_analysis(
            bug_incremental["line_coverage_incremental"],
            bug_incremental["branch_coverage_incremental"],
            correct_incremental["line_coverage_incremental"],
            correct_incremental["branch_coverage_incremental"]
        )
        
        # 6. 生成单对测试用例报告
        self.logger.info("6. 生成单对测试用例报告...")
        result = PairAnalysisResult(
            case_name=pair_case.case_name,
            diff_result=diff_result,
            bug_precondition_xml=bug_precondition_xml,
            bug_property_xml=bug_property_xml,
            correct_precondition_xml=correct_precondition_xml,
            correct_property_xml=correct_property_xml,
            bug_incremental_coverage=bug_incremental,
            correct_incremental_coverage=correct_incremental,
            line_diff_report_path="",
            branch_diff_report_path=""
        )

        # 7. 保存中间数据
        self.logger.info("7. 保存中间数据...")
        data_dir = os.path.join(output_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.report_generator.generate_all_data(result, data_dir)

        # 8. 生成差异报告
        self.logger.info("8. 生成差异报告...")
        line_diff_report_path, branch_diff_report_path = self.report_generator.generate_diff_report(result, output_dir)
        result.line_diff_report_path = line_diff_report_path
        result.branch_diff_report_path = branch_diff_report_path
        
        return result


    def _run_single_flow(self, test_case: TestCase, init_operation: Callable, ec_file_generator: Callable, output_dir: str) -> Tuple[str, str]:
        """
        执行单个测试流程并收集前后覆盖率数据
        
        Args:
            test_case: 测试用例
            init_operation: 初始化操作函数
            ec_file_generator: 覆盖率文件生成函数
            output_dir: 输出目录
            
        Returns:
            (precondition_xml_path, property_xml_path) 前置条件和属性XML文件路径元组
        """
        # 执行测试用例
        data = self.reproducer.reproduce_test_case(test_case,
                                                    output_dir,
                                                    ec_file_generator,
                                                    self.config.ec_file_path,
                                                    self.config.jacococli_jar_path, 
                                                    self.config.app_classfiles_dir, 
                                                    self.config.app_source_dir,
                                                    init_operation)

        precondition_xml_path = data.precondition_coverage_data.xml_path
        property_xml_path = data.property_coverage_data.xml_path

        return precondition_xml_path, property_xml_path


    def _calculate_incremental_coverage(self, 
                                    precondition_line_cov: LineCoverageData,
                                    precondition_branch_cov: BranchCoverageData,
                                    property_line_cov: LineCoverageData,
                                    property_branch_cov: BranchCoverageData
    ) -> dict:
        """
        计算覆盖率增量 after - before
        
        Returns:
            包含行覆盖率和分支覆盖率增量的字典
        """
        line_incremental = calculate_line_coverage_increment(precondition_line_cov, property_line_cov)
        branch_incremental = calculate_branch_coverage_increment(precondition_branch_cov, property_branch_cov)
        
        return {
            "line_coverage_incremental": line_incremental,
            "branch_coverage_incremental": branch_incremental
        }


    def _perform_diff_analysis(self, 
                            first_line_cov_inc: LineCoverageData,
                            first_branch_cov_inc: BranchCoverageData,
                            second_line_cov_inc: LineCoverageData, 
                            second_branch_cov_inc: BranchCoverageData
    ) -> CoverageDiffResult:
        """
        执行增量覆盖率差异分析
        
        Returns:
            覆盖率差异结果
        """
        line_diff = compare_line_diff(first_line_cov_inc, second_line_cov_inc)
        branch_diff = compare_branch_diff(first_branch_cov_inc, second_branch_cov_inc)
        
        return CoverageDiffResult(line_diff, branch_diff)
