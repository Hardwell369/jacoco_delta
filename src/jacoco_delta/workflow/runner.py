"""
工作流运行器模块，负责协调整个覆盖率差异分析流程
"""

import os
import time
from typing import List, Tuple, Callable

from .config import Config
from ..utils.adb_wrapper import AdbWrapper
from ..utils.data_types import TestCase, PairTestCase, FullAnalysisResult, PairAnalysisResult, LineCoverageData, BranchCoverageData, CoverageDiffResult
from ..utils.reproducer import Reproducer
from ..utils.logger import configure_logger, get_logger
from ..core.parser import parse_jacoco_line_coverage, parse_jacoco_branch_coverage
from ..core.differ import compare_line_diff, compare_branch_diff
from ..core.calculator import calculate_line_coverage_increment, calculate_branch_coverage_increment
from ..utils.report_generator import ReportGenerator

class WorkflowRunner:
    """工作流运行器，协调整个覆盖率差异分析流程"""

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
        self.report_generator = ReportGenerator(self.config.app_source_path)
        configure_logger(config.report_output_path, "workflow.log")
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
                self.config.report_output_path, 
                pair_case.case_name
            )
            os.makedirs(case_output_dir, exist_ok=True)
            
            # 执行成对测试用例分析
            pair_result = self._run_pair_analysis(
                pair_case, self.init_operation, self.ec_file_generator, case_output_dir
            )
            pair_results.append(pair_result)
        
        # 计算总体差异
        overall_diff_result = self._calculate_overall_diff(pair_results)
        
        full_result = FullAnalysisResult(
            pair_results=pair_results,
            overall_diff_result=overall_diff_result
        )
        
        # 生成总体报告
        self.reproducer.generate_reproduction_report(self.config.report_output_path) # 待整合
        self._generate_overall_report(full_result, self.config.report_output_path) # 待整合
        self.logger.info(f"完整分析完成, 共处理 {len(pair_test_cases)} 对测试用例, 结果保存在: {self.config.report_output_path}")
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
        
        self._generate_pair_report(result, output_dir)
        
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
                self.config.app_classfiles_path, 
                self.config.app_source_path, 
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
                self.config.app_classfiles_path, 
                self.config.app_source_path, 
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
                                      after_branch_cov: BranchCoverageData) -> dict:
        """
        计算覆盖率增量（after - before）
        
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
                              first_line_cov_inc, first_branch_cov_inc,
                              second_line_cov_inc, second_branch_cov_inc) -> CoverageDiffResult:
        """
        执行增量覆盖率差异分析
        
        Returns:
            覆盖率差异结果
        """
        line_diff = compare_line_diff(first_line_cov_inc, second_line_cov_inc)
        branch_diff = compare_branch_diff(first_branch_cov_inc, second_branch_cov_inc)
        
        return CoverageDiffResult(line_diff, branch_diff)

    # 暂时不用
    def _calculate_overall_diff(self, pair_results: List[PairAnalysisResult]) -> CoverageDiffResult:
        """
        计算总体差异
        
        Returns:
            总体覆盖率差异结果
        """
        # 这里简化处理，实际可以根据需要进行更复杂的聚合
        # 例如合并所有pair的差异结果
        if pair_results:
            return pair_results[0].diff_result
        else:
            return CoverageDiffResult({}, {})

    def _generate_pair_report(self, pair_result: PairAnalysisResult, report_dir: str) -> None:
        """
        生成单对测试用例分析报告
        
        Args:
            pair_result: 成对分析结果
            report_dir: 报告保存目录
        """
        # 生成测试用例的中间结果与可视化差异报告
        self.logger.info(f"生成中间结果: {pair_result.case_name}")
        data_path = os.path.join(report_dir, "data")
        os.makedirs(data_path, exist_ok=True)
        self.report_generator.generate_all_data_report(pair_result, data_path)
        self.logger.info(f"生成可视化差异报告: {pair_result.case_name}")
        self.report_generator.generate_visual_diff_report(pair_result, report_dir)

        report_path = os.path.join(report_dir, f"{pair_result.case_name}_analysis_report.md")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# {pair_result.case_name} 覆盖率差异分析报告\n\n")
            f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 写入基础信息
            f.write("## 基础信息\n")
            f.write(f"- Bug执行前XML路径: {pair_result.bug_before_xml}\n")
            f.write(f"- Bug执行后XML路径: {pair_result.bug_after_xml}\n")
            f.write(f"- 正确执行前XML路径: {pair_result.correct_before_xml}\n")
            f.write(f"- 正确执行后XML路径: {pair_result.correct_after_xml}\n\n")

            # 写入差异分析结果
            f.write("## 覆盖率增量差异分析结果\n")
            if pair_result.diff_result.line_coverage_diff:
                f.write("### 行覆盖率增量差异\n")
                for file_path, diff in pair_result.diff_result.line_coverage_diff.items():
                    f.write(f"#### 文件: {file_path}\n")
                    if diff.only_in_first:
                        f.write("- 仅在Bug增量中出现的行:\n")
                        for line_num, count in diff.only_in_first.items():
                            f.write(f"  - 行 {line_num}: 覆盖{count}次\n")
                    if diff.only_in_second:
                        f.write("- 仅在正确执行增量中出现的行:\n")
                        for line_num, count in diff.only_in_second.items():
                            f.write(f"  - 行 {line_num}: 覆盖{count}次\n")
                    f.write("\n")
            
            if pair_result.diff_result.branch_coverage_diff:
                f.write("### 分支覆盖率增量差异\n")
                for file_path, diff in pair_result.diff_result.branch_coverage_diff.items():
                    f.write(f"#### 文件: {file_path}\n")
                    if diff.only_in_first:
                        f.write("- 仅在Bug增量中出现的分支:\n")
                        for line_num, (covered, total) in diff.only_in_first.items():
                            f.write(f"  - 行 {line_num}: 覆盖{covered}个（总分支{total}个）\n")
                    if diff.only_in_second:
                        f.write("- 仅在正确执行增量中出现的分支:\n")
                        for line_num, (covered, total) in diff.only_in_second.items():
                            f.write(f"  - 行 {line_num}: 覆盖{covered}个（总分支{total}个）\n")
                    f.write("\n")
        
        self.logger.info(f"单对测试用例分析报告已生成: {report_path}")

    def _generate_overall_report(self, full_result: FullAnalysisResult, base_output_path: str) -> None:
        """
        生成总体分析报告
        
        Args:
            full_result: 完整分析结果
            base_output_path: 基础输出路径
        """
        report_path = os.path.join(base_output_path, "overall_analysis_report.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 总体覆盖率差异分析报告\n\n")
            f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 分析概览\n")
            f.write(f"- 总共分析了 {len(full_result.pair_results)} 对测试用例\n")
            f.write("- 各对测试用例的详细分析结果请参见对应的子目录\n\n")
            
            f.write("## 测试用例列表\n")
            for pair_result in full_result.pair_results:
                f.write(f"- {pair_result.case_name}\n")
            f.write("\n")
            
            # 可以在这里添加总体统计信息

        self.logger.info(f"总体分析报告已生成: {report_path}")
