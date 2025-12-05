"""
对比模块，包含覆盖率差异对比函数
"""

from typing import Dict, Tuple, List
from ..utils.data_types import LineCoverageData, BranchCoverageData, LineCoverageDiff, BranchCoverageDiff



def _compare_line_diff_for_file(
    lines_in_first: Dict[int, int], 
    lines_in_second: Dict[int, int]
) -> LineCoverageDiff:
    """
    比较单个文件的行覆盖率数据
    
    Args:
        lines_in_first: 第一个数据集的行覆盖率 {行号: 覆盖次数}
        lines_in_second: 第二个数据集的行覆盖率 {行号: 覆盖次数}
        
    Returns:
        行覆盖率差异
    """
    # 找出仅在第一个数据集中的行
    only_in_first = {line: lines_in_first[line] for line in lines_in_first if line not in lines_in_second}
    
    # 找出仅在第二个数据集中的行
    only_in_second = {line: lines_in_second[line] for line in lines_in_second if line not in lines_in_first}
    
    return LineCoverageDiff(only_in_first, only_in_second)


def _compare_branch_diff_for_file(
    branches_in_first: Dict[int, Tuple[int, int]], 
    branches_in_second: Dict[int, Tuple[int, int]]
) -> BranchCoverageDiff:
    """
    比较单个文件的分支覆盖率数据
    
    Args:
        branches_in_first: 第一个数据集的分支覆盖率 {行号: (已覆盖分支数, 总分支数)}
        branches_in_second: 第二个数据集的分支覆盖率 {行号: (已覆盖分支数, 总分支数)}
        
    Returns:
        分支覆盖率差异
    """
    # 找出仅在第一个数据集中的分支
    only_in_first = {line: branches_in_first[line] for line in branches_in_first if line not in branches_in_second}
    
    # 找出仅在第二个数据集中的分支
    only_in_second = {line: branches_in_second[line] for line in branches_in_second if line not in branches_in_first}
    
    return BranchCoverageDiff(only_in_first, only_in_second)


def compare_line_diff(
    first: LineCoverageData, 
    second: LineCoverageData
) -> Dict[str, LineCoverageDiff]:
    """
    比较两个行覆盖率数据集，找出它们之间的差异
    
    Args:
        first: 第一个行覆盖率数据集 {文件路径: {行号: 覆盖次数}}
        second: 第二个行覆盖率数据集 {文件路径: {行号: 覆盖次数}}
        
    Returns:
        文件级别的行覆盖率差异 {文件路径: LineCoverageDiff}
    """
    all_files = set(first.keys()).union(set(second.keys()))
    
    # 存储差异结果
    diff_result = {}
    
    for file in sorted(all_files):
        lines_in_first = first.get(file, {})
        lines_in_second = second.get(file, {})
        
        # 比较当前文件的行覆盖率数据
        file_diff = _compare_line_diff_for_file(lines_in_first, lines_in_second)
        
        # 只有当存在差异时才添加到结果中
        if file_diff.only_in_first or file_diff.only_in_second:
            diff_result[file] = file_diff
    
    return diff_result


def compare_branch_diff(
    first: BranchCoverageData, 
    second: BranchCoverageData
) -> Dict[str, BranchCoverageDiff]:
    """
    比较两个分支覆盖率数据集，找出它们之间的差异
    
    Args:
        first: 第一个分支覆盖率数据集 {文件路径: {行号: (已覆盖分支数, 总分支数)}}
        second: 第二个分支覆盖率数据集 {文件路径: {行号: (已覆盖分支数, 总分支数)}}
        
    Returns:
        文件级别的分支覆盖率差异 {文件路径: BranchCoverageDiff}
    """
    all_files = set(first.keys()).union(set(second.keys()))

    # 存储差异结果
    diff_result = {}

    for file in sorted(all_files):
        branches_in_first = first.get(file, {})
        branches_in_second = second.get(file, {})
        
        # 比较当前文件的分支覆盖率数据
        file_diff = _compare_branch_diff_for_file(branches_in_first, branches_in_second)
        
        # 只有当存在差异时才添加到结果中
        if file_diff.only_in_first or file_diff.only_in_second:
            diff_result[file] = file_diff

    return diff_result


def format_line_diff_result(line_diff_result: Dict[str, LineCoverageDiff]) -> List[str]:
    """
    将行覆盖率的差异结果格式化为字符串列表
    
    Args:
        line_diff_result: 行覆盖率差异结果 {文件路径: LineCoverageDiff}
        
    Returns:
        格式化的字符串列表，可用于打印或写入文件
    """
    formatted_lines = []
    
    # 格式化行覆盖率差异
    if line_diff_result:
        formatted_lines.append("========== 行覆盖率差异 ==========\n")
        for file_path in sorted(line_diff_result.keys()):
            line_diff = line_diff_result[file_path]
            formatted_lines.append(f"文件: {file_path}\n")
            
            # 仅在第一个数据集中的行
            if line_diff.only_in_first:
                formatted_lines.append("  仅在第一个数据集中:")
                for line_number in sorted(line_diff.only_in_first.keys()):
                    formatted_lines.append(f"    行 {line_number}: 覆盖{line_diff.only_in_first[line_number]}次")
            
            # 仅在第二个数据集中的行
            if line_diff.only_in_second:
                formatted_lines.append("  仅在第二个数据集中:")
                for line_number in sorted(line_diff.only_in_second.keys()):
                    formatted_lines.append(f"    行 {line_number}: 覆盖{line_diff.only_in_second[line_number]}次")
            formatted_lines.append("\n")
    
    return formatted_lines


def format_branch_diff_result(branch_diff_result: Dict[str, BranchCoverageDiff]) -> List[str]:
    """
    将分支覆盖率的差异结果格式化为字符串列表
    
    Args:
        branch_diff_result: 分支覆盖率差异结果 {文件路径: BranchCoverageDiff}
        
    Returns:
        格式化的字符串列表，可用于打印或写入文件
    """
    formatted_lines = []
    
    # 格式化分支覆盖率差异
    if branch_diff_result:
        formatted_lines.append("========== 分支覆盖率差异 ==========\n")
        for file_path in sorted(branch_diff_result.keys()):
            branch_diff = branch_diff_result[file_path]
            formatted_lines.append(f"文件: {file_path}\n")
            
            # 仅在第一个数据集中的分支
            if branch_diff.only_in_first:
                formatted_lines.append("  仅在第一个数据集中:")
                for line_number in sorted(branch_diff.only_in_first.keys()):
                    covered_count, total_count = branch_diff.only_in_first[line_number]
                    formatted_lines.append(f"    行 {line_number}: 覆盖{covered_count}个（总分支{total_count}个")
            
            # 仅在第二个数据集中的分支
            if branch_diff.only_in_second:
                formatted_lines.append("  仅在第二个数据集中:")
                for line_number in sorted(branch_diff.only_in_second.keys()):
                    covered_count, total_count = branch_diff.only_in_second[line_number]
                    formatted_lines.append(f"    行 {line_number}: 覆盖{covered_count}个（总分支{total_count}个")
            formatted_lines.append("\n")
    
    return formatted_lines