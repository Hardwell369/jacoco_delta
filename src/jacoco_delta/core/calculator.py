"""
计算模块，包含覆盖率增量计算函数
"""

from typing import List
from ..utils.data_types import LineCoverageData, BranchCoverageData


def calculate_line_coverage_increment(
    baseline_coverage: LineCoverageData, 
    current_coverage: LineCoverageData, 
) -> LineCoverageData:
    """
    对比两个行覆盖率数据，输出差异到文件
    仅输出在current_coverage中新增的行（即增量）
    
    Args:
        baseline_coverage: 基准版本覆盖率数据 {文件路径: {行号: 覆盖次数}}
        current_coverage: 当前版本覆盖率数据 {文件路径: {行号: 覆盖次数}}
    
    Returns:
        增量行覆盖率数据 {文件路径: {行号: 覆盖次数}}
    """
    # 获取所有文件的并集
    all_file_paths = set(baseline_coverage.keys()).union(set(current_coverage.keys()))
    incremental_coverage_data: LineCoverageData = {}
    
    # 遍历每个文件
    for file_path in sorted(all_file_paths):
        baseline_lines = baseline_coverage.get(file_path, {})
        current_lines = current_coverage.get(file_path, {})
        
        # 找出在current_coverage中新增的行（即增量）
        added_or_improved_lines = {}
        for line_number, coverage_count in current_lines.items():
            if line_number not in baseline_lines:
                # 在current_coverage中新增的行
                added_or_improved_lines[line_number] = coverage_count
            elif baseline_lines[line_number] == 0 and coverage_count > 0:
                # 在baseline_coverage中未覆盖但在current_coverage中覆盖的行
                added_or_improved_lines[line_number] = coverage_count
        
        # 如果有新增或改进的行，则添加到结果中
        if added_or_improved_lines:
            incremental_coverage_data[file_path] = added_or_improved_lines
    
    return incremental_coverage_data


def format_line_coverage_increment_data(
    increment_data: LineCoverageData
) -> List[str]:
    """
    将行覆盖率增量数据格式化为字符串列表
    
    Args:
        increment_data: 增量覆盖率数据 {文件路径: {行号: 覆盖次数}}
        
    Returns:
        格式化的字符串列表，可用于写入文件
    """
    lines = []
    
    for file in sorted(increment_data.keys()):
        lines.append(f"===== 文件: {file} =====\n")
        file_data = increment_data[file]
        # 按行号排序输出
        for line_num in sorted(file_data.keys()):
            lines.append(f"行 {line_num}: 覆盖{file_data[line_num]}次")
        lines.append("\n")
    
    return lines


def calculate_branch_coverage_increment(
    baseline_coverage: BranchCoverageData, 
    current_coverage: BranchCoverageData, 
) -> BranchCoverageData:
    """
    对比两个分支覆盖率数据，输出差异
    仅输出在current_coverage中新增或改进的分支覆盖情况
    
    Args:
        baseline_coverage: 基准版本分支覆盖率数据 {文件路径: {行号: (已覆盖分支数, 总分支数)}}
        current_coverage: 当前版本分支覆盖率数据 {文件路径: {行号: (已覆盖分支数, 总分支数)}}
    
    Returns:
        增量分支覆盖率数据 {文件路径: {行号: (已覆盖分支数, 总分支数)}}
    """
    # 获取所有文件的并集
    all_file_paths = set(baseline_coverage.keys()).union(current_coverage.keys())
    incremental_branch_data: BranchCoverageData = {}

    # 遍历每个文件
    for file_path in sorted(all_file_paths):
        baseline_branches = baseline_coverage.get(file_path, {})  # 行号: (已覆盖分支数, 总分支数)
        current_branches = current_coverage.get(file_path, {})
        
        # 找出在current_coverage中新增或改进的分支覆盖情况
        added_or_improved_branches = {}
        for line_number, (current_covered_count, current_total_count) in current_branches.items():
            if line_number not in baseline_branches:
                # 在current_coverage中新增的分支行
                added_or_improved_branches[line_number] = (current_covered_count, current_total_count)
            else:
                baseline_covered_count, baseline_total_count = baseline_branches[line_number]
                # 分支总数相同，但覆盖数增加
                if baseline_total_count == current_total_count and current_covered_count > baseline_covered_count:
                    added_or_improved_branches[line_number] = (current_covered_count, current_total_count)
                # 分支总数增加（新增分支），且有覆盖
                elif current_total_count > baseline_total_count and current_covered_count > 0:
                    added_or_improved_branches[line_number] = (current_covered_count, current_total_count)
        
        # 如果有新增或改进的分支，则添加到结果中
        if added_or_improved_branches:
            incremental_branch_data[file_path] = added_or_improved_branches
    
    return incremental_branch_data


def format_branch_coverage_increment_data(
    increment_data: BranchCoverageData
) -> List[str]:
    """
    将分支覆盖率增量数据格式化为字符串列表
    
    Args:
        increment_data: 增量分支覆盖率数据 {文件路径: {行号: (已覆盖分支数, 总分支数)}}
        
    Returns:
        格式化的字符串列表，可用于写入文件
    """
    lines = []
    
    for file in sorted(increment_data.keys()):
        lines.append(f"===== 文件: {file} =====\n")
        file_data = increment_data[file]
        for line_num in sorted(file_data.keys()):
            covered, total = file_data[line_num]
            lines.append(f"行 {line_num}: 覆盖{covered}个（总分支{total}个")
        lines.append("\n")
    
    return lines