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
        
        # 计算总体差异
        # overall_diff_result = self._calculate_overall_diff(pair_results)
        
        full_result = FullAnalysisResult(
            pair_results=pair_results,
            # overall_diff_result=overall_diff_result
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
                          output_dir: str) -> PairAnalysisResult:
        """
        执行成对测试用例分析
        
        Args:
            pair_case: 成对测试用例
            output_dir: 输出目录
            
        Returns:
            成对分析结果
        """
        self.logger.info(f"执行成对测试用例分析: {pair_case.bug_case.name} <-> {pair_case.correct_case.name}")
        
        # 1. 执行bug复现流程并收集覆盖率数据
        self.logger.info("1. 执行bug复现流程...")
        bug_before_xml, bug_after_xml = self._run_single_flow(
            pair_case.bug_case, init_operation, ec_file_generator, output_dir
        )
        
        # 2. 执行正确流程并收集覆盖率数据
        self.logger.info("2. 执行正确流程...")
        correct_before_xml, correct_after_xml = self._run_single_flow(
            pair_case.correct_case, init_operation, ec_file_generator, output_dir
        )
        
        # 3. 解析XML覆盖率文件
        self.logger.info("3. 解析覆盖率数据...")
        bug_before_line_cov = parse_jacoco_line_coverage(bug_before_xml)
        bug_before_branch_cov = parse_jacoco_branch_coverage(bug_before_xml)
        bug_after_line_cov = parse_jacoco_line_coverage(bug_after_xml)
        bug_after_branch_cov = parse_jacoco_branch_coverage(bug_after_xml)
        
        correct_before_line_cov = parse_jacoco_line_coverage(correct_before_xml)
        correct_before_branch_cov = parse_jacoco_branch_coverage(correct_before_xml)
        correct_after_line_cov = parse_jacoco_line_coverage(correct_after_xml)
        correct_after_branch_cov = parse_jacoco_branch_coverage(correct_after_xml)
        
        # 4. 计算覆盖率增量
        self.logger.info("4. 计算覆盖率增量...")
        bug_incremental = self._calculate_incremental_coverage(
            bug_before_line_cov, bug_before_branch_cov,
            bug_after_line_cov, bug_after_branch_cov
        )
        correct_incremental = self._calculate_incremental_coverage(
            correct_before_line_cov, correct_before_branch_cov,
            correct_after_line_cov, correct_after_branch_cov
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
            bug_before_xml=bug_before_xml,
            bug_after_xml=bug_after_xml,
            correct_before_xml=correct_before_xml,
            correct_after_xml=correct_after_xml,
            bug_incremental_coverage=bug_incremental,
            correct_incremental_coverage=correct_incremental
        )
        
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
            (before_xml_path, after_xml_path) 前后XML文件路径元组
        """
        # 添加测试用例
        self.reproducer.add_test_case(test_case)
        
        # 设置测试环境
        self.reproducer.setup_test_environment(init_operation)
        
        try:
            # 收集执行前的覆盖率数据
            self.logger.info(f"收集{test_case.name}执行前的覆盖率数据...")
            before_ec_path = self.config.coverage_ec_path
            before_output_dir = os.path.join(output_dir, f"{test_case.name}_before")
            os.makedirs(before_output_dir, exist_ok=True)
            before_coverage_data = self.reproducer.collect_coverage_data(
                ec_file_generator,
                before_ec_path, 
                before_output_dir, 
                self.config.jacococli_jar_path, 
                self.config.app_classfiles_dir, 
                self.config.app_source_dir, 
                test_case.name
            )
            before_xml_path = before_coverage_data.xml_path
            
            # 执行测试用例
            self.logger.info(f"执行测试用例: {test_case.name}")
            self.reproducer.execute_test_case(test_case)
            
            # 收集执行后的覆盖率数据
            self.logger.info(f"收集{test_case.name}执行后的覆盖率数据...")
            after_ec_path = self.config.coverage_ec_path
            after_output_dir = os.path.join(output_dir, f"{test_case.name}_after")
            os.makedirs(after_output_dir, exist_ok=True)
            after_coverage_data = self.reproducer.collect_coverage_data(
                ec_file_generator,
                after_ec_path, 
                after_output_dir, 
                self.config.jacococli_jar_path, 
                self.config.app_classfiles_dir, 
                self.config.app_source_dir, 
                test_case.name
            )
            after_xml_path = after_coverage_data.xml_path

            return before_xml_path, after_xml_path
            
        finally:
            # 重置环境
            self.reproducer.reset_environment()


    def _calculate_incremental_coverage(self, 
                                    before_line_cov: LineCoverageData,
                                    before_branch_cov: BranchCoverageData,
                                    after_line_cov: LineCoverageData,
                                    after_branch_cov: BranchCoverageData
    ) -> dict:
        """
        计算覆盖率增量 after - before
        
        Returns:
            包含行覆盖率和分支覆盖率增量的字典
        """
        line_incremental = calculate_line_coverage_increment(before_line_cov, after_line_cov)
        branch_incremental = calculate_branch_coverage_increment(before_branch_cov, after_branch_cov)
        
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
