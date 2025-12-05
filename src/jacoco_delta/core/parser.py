"""
解析模块，包含XML文件解析函数
"""

import xml.etree.ElementTree as ET
from typing import Dict, Tuple, List

from ..utils.data_types import LineCoverageData, BranchCoverageData
from ..utils.logger import get_logger

logger = get_logger("parser")

def parse_jacoco_line_coverage(xml_path: str) -> LineCoverageData:
    """
    解析Jacoco XML文件，返回行覆盖率数据
    返回格式: {文件路径: {行号: 覆盖次数}}
    """
    line_coverage: LineCoverageData = {}
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        for package_elem in root.iter('package'):
            package_name = package_elem.get('name', '')
            
            for source_elem in package_elem.findall('sourcefile'):
                source_file = source_elem.get('name')
                if not source_file:
                    continue
                
                # 构建完整路径
                full_path = f"{package_name}/{source_file}" if package_name else source_file
                
                # 提取行号和覆盖次数
                lines: Dict[int, int] = {}
                for line in source_elem.findall('line'):
                    line_nr = int(line.get('nr', 0))
                    covered_times = int(line.get('ci', 0))
                    if covered_times > 0:  # 只记录被覆盖的行
                        lines[line_nr] = covered_times
                
                if lines:
                    line_coverage[full_path] = lines
    
    except Exception as e:
        logger.error(f"解析XML出错 ({xml_path}): {str(e)}")
        raise
    
    return line_coverage


def format_line_coverage_data(coverage_data: LineCoverageData) -> List[str]:
    """
    将行覆盖率数据格式化为字符串列表
    
    Args:
        coverage_data: 行覆盖率数据 {文件路径: {行号: 覆盖次数}}
        
    Returns:
        格式化的字符串列表，可用于打印或写入文件
    """
    formatted_lines = []
    
    for file_path in sorted(coverage_data.keys()):
        formatted_lines.append(f"===== 文件: {file_path} =====\n")
        file_coverage = coverage_data[file_path]
        # 按行号排序输出
        for line_number in sorted(file_coverage.keys()):
            formatted_lines.append(f"行 {line_number}: 覆盖{file_coverage[line_number]}次")
        formatted_lines.append("\n")
    
    return formatted_lines


def parse_jacoco_branch_coverage(xml_path: str) -> BranchCoverageData:
    """
    解析Jacoco XML文件，返回分支覆盖率数据
    返回格式: {文件路径: {行号: (已覆盖分支数, 总分支数)}}
    """
    branch_coverage: BranchCoverageData = {}
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for package_elem in root.iter('package'):
            package_name = package_elem.get('name', '')
            
            for source_elem in package_elem.findall('sourcefile'):
                source_file = source_elem.get('name')
                if not source_file:
                    continue
                    
                full_file_path = f"{package_name}/{source_file}" if package_name else source_file
                
                lines: Dict[int, Tuple[int, int]] = {}
                for line in source_elem.findall('line'):
                    line_num = int(line.get('nr', 0))  # 行号
                    mb = int(line.get('mb', 0))       # 未覆盖分支数
                    cb = int(line.get('cb', 0))       # 已覆盖分支数
                    total_branches = mb + cb
                    
                    if total_branches > 0:  # 只记录有分支的行
                        lines[line_num] = (cb, total_branches)
                
                if lines:
                    branch_coverage[full_file_path] = lines
                    
    except Exception as e:
        logger.error(f"解析XML出错 ({xml_path}): {str(e)}")
        raise
    
    return branch_coverage


def format_branch_coverage_data(branch_coverage_data: BranchCoverageData) -> List[str]:
    """
    将分支覆盖率数据格式化为字符串列表
    
    Args:
        branch_coverage_data: 分支覆盖率数据 {文件路径: {行号: (已覆盖分支数, 总分支数)}}
        
    Returns:
        格式化的字符串列表，可用于打印或写入文件
    """
    formatted_lines = []
    
    for file_path in sorted(branch_coverage_data.keys()):
        formatted_lines.append(f"===== 文件: {file_path} =====\n")
        file_branch_coverage = branch_coverage_data[file_path]
        # 按行号排序输出
        for line_number in sorted(file_branch_coverage.keys()):
            covered_count, total_count = file_branch_coverage[line_number]
            formatted_lines.append(f"行 {line_number}: 覆盖{covered_count}个（总分支{total_count}个）")
        formatted_lines.append("\n")
    
    return formatted_lines