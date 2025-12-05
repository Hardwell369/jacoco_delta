"""
类型定义模块，包含项目中使用的各种数据结构类型定义
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Callable

from dataclasses import dataclass

# 行覆盖率数据类型
# 格式: {文件路径: {行号: 覆盖次数}}
LineCoverageData = dict[str, dict[int, int]]

# 分支覆盖率数据类型
# 格式: {文件路径: {行号: (已覆盖分支数, 总分支数)}}
BranchCoverageData = dict[str, dict[int, tuple[int, int]]]


@dataclass
class LineCoverageDiff:
    """行覆盖率差异数据结构"""
    # 仅在第一个数据集中存在的行 {行号: 覆盖次数}
    only_in_first: dict[int, int]
    # 仅在第二个数据集中存在的行 {行号: 覆盖次数}
    only_in_second: dict[int, int]


@dataclass
class BranchCoverageDiff:
    """分支覆盖率差异数据结构"""
    # 仅在第一个数据集中存在的分支 {行号: (已覆盖分支数, 总分支数)}
    only_in_first: dict[int, tuple[int, int]]
    # 仅在第二个数据集中存在的分支 {行号: (已覆盖分支数, 总分支数)}
    only_in_second: dict[int, tuple[int, int]]


@dataclass
class CoverageDiffResult:
    """覆盖率差异结果数据结构"""
    # 文件级别的差异 {文件路径: 差异详情}
    line_coverage_diff: dict[str, LineCoverageDiff]
    branch_coverage_diff: dict[str, BranchCoverageDiff]


class TestStatus(Enum):
    """测试状态枚举"""
    SUCCESS = "success"
    UNEXECUTED = "unexecuted"
    ERROR = "error"


@dataclass
class TestCase:
    """测试用例数据类"""
    name: str
    reproduce: Callable  # 具体的执行函数


@dataclass
class TestResult:
    """测试结果数据类"""
    status: TestStatus
    error_message: Optional[str]
    execution_time: float
    timestamp: str


@dataclass
class CoverageData:
    """覆盖率数据类"""
    xml_path: str
    timestamp: str


@dataclass
class TestData:
    """测试用例数据类"""
    test_case: TestCase
    result: TestResult
    coverage_data: List[CoverageData]


class PairTestCase:
    """成对测试用例数据类"""
    def __init__(self, case_name: str, bug_reproduce: Callable, correct_reproduce: Callable):
        """
        初始化成对测试用例
        
        Args:
            case_name: 测试用例名称
            bug_reproduce: bug复现函数
            correct_reproduce: 正确执行函数
        """
        bug_case_prefix = "bug_"
        correct_case_prefix = "correct_"
        bug_case = TestCase(bug_case_prefix + case_name, bug_reproduce)
        correct_case = TestCase(correct_case_prefix + case_name, correct_reproduce)
        self.case_name = case_name
        self.bug_case = bug_case
        self.correct_case = correct_case


@dataclass
class PairAnalysisResult:
    """成对测试用例分析结果数据类"""
    case_name: str
    diff_result: CoverageDiffResult
    bug_before_xml: str  # xml路径
    bug_after_xml: str 
    correct_before_xml: str 
    correct_after_xml: str
    bug_incremental_coverage: dict  # 包括行覆盖率和分支覆盖率["line_coverage_incremental", "branch_coverage_incremental"]
    correct_incremental_coverage: dict  # 包括行覆盖率和分支覆盖率["line_coverage_incremental", "branch_coverage_incremental"]


@dataclass
class FullAnalysisResult:
    """完整分析结果数据类"""
    pair_results: List[PairAnalysisResult]
    overall_diff_result: CoverageDiffResult