import os
from datetime import datetime
from typing import List, Set
import html 

from jacoco_delta.workflow.runner import PairAnalysisResult
from jacoco_delta.core.calculator import format_line_coverage_increment_data, format_branch_coverage_increment_data
from jacoco_delta.core.differ import format_line_diff_result, format_branch_diff_result
from jacoco_delta.utils.data_types import LineCoverageDiff, BranchCoverageDiff
from jacoco_delta.utils.logger import get_logger

# 依据diff数据生成差异报告, 以html的形式展示, 参考jacoco的报告格式
class ReportGenerator:
    # 常量定义
    LINE_REPORT_SUFFIX = "_line_visual_diff_report.html"
    BRANCH_REPORT_SUFFIX = "_branch_visual_diff_report.html"
    CODE_CONTAINER_CLASS = "code-container"
    BRANCH_CODE_CONTAINER_CLASS = "branch-code-container"
    
    def __init__(self, source_code_base_path: str = "", context_lines: int = 5):
        """
        初始化报告生成器
        
        Args:
            source_code_base_path: 源代码基础路径，用于读取源代码文件
            context_lines: 上下文行数，用于显示差异前后的代码上下文
        """
        self.source_code_base_path = source_code_base_path
        self.context_lines = context_lines
        self.logger = get_logger("report_generator")

    def generate_incremental_report(self, result: PairAnalysisResult, output_dir: str):
        """
        生成增量覆盖率数据结果
        
        Args:
            output_dir: 报告输出目录
            result: 覆盖率对比结果
        """
        bug_line_report_path = os.path.join(output_dir, f"bug_{result.case_name}_line_incremental_report.md")
        bug_branch_report_path = os.path.join(output_dir, f"bug_{result.case_name}_branch_incremental_report.md")
        with open(bug_line_report_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_line_coverage_increment_data(result.bug_incremental_coverage["line_coverage_incremental"])))
        self.logger.info(f"生成bug line coverage increment data: {bug_line_report_path}")
        with open(bug_branch_report_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_branch_coverage_increment_data(result.bug_incremental_coverage["branch_coverage_incremental"])))
        self.logger.info(f"生成bug branch coverage increment data: {bug_branch_report_path}")

        correct_line_report_path = os.path.join(output_dir, f"correct_{result.case_name}_line_incremental_report.md")
        correct_branch_report_path = os.path.join(output_dir, f"correct_{result.case_name}_branch_incremental_report.md")
        with open(correct_line_report_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_line_coverage_increment_data(result.correct_incremental_coverage["line_coverage_incremental"])))
        self.logger.info(f"生成correct line coverage increment data: {correct_line_report_path}")
        with open(correct_branch_report_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_branch_coverage_increment_data(result.correct_incremental_coverage["branch_coverage_incremental"])))
        self.logger.info(f"生成correct branch coverage increment data: {correct_branch_report_path}")


    def generate_diff_report(self, result: PairAnalysisResult, output_dir: str):
        """
        生成差异数据结果
        
        Args:
            output_dir: 报告输出目录
            result: 覆盖率对比结果
        """
        line_diff_report_path = os.path.join(output_dir, f"line_diff_report.md")
        branch_diff_report_path = os.path.join(output_dir, f"branch_diff_report.md")
        with open(line_diff_report_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_line_diff_result(result.diff_result.line_coverage_diff)))
        self.logger.info(f"生成line diff data: {line_diff_report_path}")
        with open(branch_diff_report_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_branch_diff_result(result.diff_result.branch_coverage_diff)))
        self.logger.info(f"生成branch diff data: {branch_diff_report_path}")


    def generate_all_data_report(self, result: PairAnalysisResult, output_dir: str):
        """
        生成所有数据结果
        
        Args:
            output_dir: 报告输出目录
            result: 覆盖率对比结果
        """
        self.generate_incremental_report(result, output_dir)
        self.generate_diff_report(result, output_dir)


    def _read_source_file(self, file_path: str) -> List[str]:
        """
        读取源代码文件内容
        
        Args:
            file_path: 源代码文件路径
            
        Returns:
            文件内容行列表
        """
        # 尝试不同的编码格式读取文件
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        
        # 构建完整的文件路径
        full_path = os.path.join(self.source_code_base_path, file_path.replace('/', os.sep))
        
        for encoding in encodings:
            try:
                with open(full_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                self.logger.info(f"成功读取源代码文件: {full_path} 编码: {encoding}")
                return lines
            except UnicodeDecodeError:
                continue
            except FileNotFoundError:
                self.logger.error(f"源代码文件未找到: {full_path}")
                # 如果找不到文件，返回空列表
                return [f"// 文件未找到: {full_path}"]
        
        # 如果所有编码都失败，返回错误信息
        self.logger.error(f"无法读取源代码文件: {full_path} 所有编码尝试失败")
        return [f"// 无法读取文件: {full_path}"]


    def _get_extended_line_range(self, line_numbers: Set[int], max_lines: int, context_lines: int = 5) -> List[tuple]:
        """
        获取扩展的行号范围，包括上下文行，并标记分隔点
        
        Args:
            line_numbers: 需要高亮的行号集合
            max_lines: 文件总行数
            context_lines: 上下文行数，默认为5
            
        Returns:
            包含(行号, 是否为分隔符)元组的列表
        """
        if not line_numbers:
            return []
            
        # 先获取所有需要显示的行号
        extended_ranges = []
        sorted_lines = sorted(list(line_numbers))
        
        for line_num in sorted_lines:
            # 添加上下文行
            start = max(1, line_num - context_lines)
            end = min(max_lines, line_num + context_lines)
            extended_ranges.append((start, end))
        
        # 合并重叠的范围
        merged_ranges = []
        if extended_ranges:
            current_start, current_end = extended_ranges[0]
            
            for start, end in extended_ranges[1:]:
                # 如果范围重叠或相邻，则合并
                if start <= current_end + 1:
                    current_end = max(current_end, end)
                else:
                    # 添加当前范围
                    merged_ranges.append((current_start, current_end))
                    current_start, current_end = start, end
            
            # 添加最后一个范围
            merged_ranges.append((current_start, current_end))
        
        # 生成实际的行号列表，包含分隔符标记
        result_lines = []
        for i, (start, end) in enumerate(merged_ranges):
            # 添加范围内的所有行
            for line_num in range(start, end + 1):
                result_lines.append((line_num, False))  # (行号, 是否为分隔符)
            
            # 如果不是最后一个范围，添加分隔符
            if i < len(merged_ranges) - 1:
                result_lines.append((-1, True))  # (-1表示分隔符, True表示是分隔符)
        
        return result_lines


    def _get_line_css_styles(self) -> str:
        """
        获取行覆盖率CSS样式
        
        Returns:
            CSS样式字符串
        """
        return """
        <style>
            .code-container {
                font-family: 'Courier New', Courier, monospace;
                font-size: 14px;
                line-height: 1.4;
                border: 1px solid #ddd;
                border-radius: 4px;
                overflow: auto;
                max-height: 600px;
                margin-bottom: 20px;
            }
            .code-line {
                padding: 2px 10px;
                white-space: pre;
            }
            .line-number {
                display: inline-block;
                width: 50px;
                color: #999;
                text-align: right;
                margin-right: 10px;
                user-select: none;
            }
            .covered-line {
                background-color: #e6ffec; /* 浅绿色 */
            }
            .context-line {
                background-color: #ffffff; /* 白色 */
            }
            .separator-line {
                background-color: #f0f0f0;
                text-align: center;
                font-style: italic;
                color: #999;
            }
            .separator-content {
                display: inline-block;
                width: 100%;
                text-align: center;
            }
            .file-header {
                background-color: #f6f8fa;
                padding: 10px;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
            .diff-container {
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }
            .diff-panel {
                flex: 1;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .panel-header {
                background-color: #f6f8fa;
                padding: 8px 12px;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
            /* 文件列表样式 */
            .file-list {
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
            .file-list h3 {
                margin-top: 0;
            }
            .file-item {
                margin: 5px 0;
            }
            .file-link {
                margin-right: 15px;
            }
            /* 返回顶部按钮样式 */
            .back-to-top {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                z-index: 1000;
            }
            .back-to-top:hover {
                background-color: #0056b3;
            }
        </style>
        """

    def _get_branch_css_styles(self) -> str:
        """
        获取分支覆盖率CSS样式
        
        Returns:
            CSS样式字符串
        """
        return """
        <style>
            .branch-code-container {
                font-family: 'Courier New', Courier, monospace;
                font-size: 14px;
                line-height: 1.4;
                border: 1px solid #ddd;
                border-radius: 4px;
                overflow: auto;
                max-height: 600px;
                margin-bottom: 20px;
            }
            .branch-code-line {
                padding: 2px 10px;
                white-space: pre;
            }
            .branch-line-number {
                display: inline-block;
                width: 50px;
                color: #999;
                text-align: right;
                margin-right: 10px;
                user-select: none;
            }
            .branch-covered-line {
                background-color: #e6ffec; /* 浅绿色 */
            }
            .branch-context-line {
                background-color: #ffffff; /* 白色 */
            }
            .separator-line {
                background-color: #f0f0f0;
                text-align: center;
                font-style: italic;
                color: #999;
            }
            .separator-content {
                display: inline-block;
                width: 100%;
                text-align: center;
            }
            .branch-file-header {
                background-color: #f6f8fa;
                padding: 10px;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
            .branch-diff-container {
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }
            .branch-diff-panel {
                flex: 1;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .branch-panel-header {
                background-color: #f6f8fa;
                padding: 8px 12px;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
            /* 文件列表样式 */
            .file-list {
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
            .file-list h3 {
                margin-top: 0;
            }
            .file-item {
                margin: 5px 0;
            }
            .file-link {
                margin-right: 15px;
            }
            /* 返回顶部按钮样式 */
            .back-to-top {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                z-index: 1000;
            }
            .back-to-top:hover {
                background-color: #0056b3;
            }
        </style>
        """


    def _generate_html_header(self, title: str, css_styles: str) -> List[str]:
        """
        生成HTML头部内容
        
        Args:
            title: 页面标题
            css_styles: CSS样式
            
        Returns:
            HTML头部内容列表
        """
        return [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta charset="UTF-8">',
            f'<title>{title}</title>',
            css_styles,
            '</head>',
            '<body>'
        ]


    def _generate_html_footer(self) -> List[str]:
        """
        生成HTML尾部内容
        
        Returns:
            HTML尾部内容列表
        """
        return [
            '<button class="back-to-top" onclick="window.scrollTo({top: 0, behavior: \'smooth\'});">返回顶部</button>',
            '</body>',
            '</html>'
        ]


    def _generate_file_list_html(self, file_paths: List[str]) -> List[str]:
        """
        生成文件列表HTML
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件列表HTML内容列表
        """
        html_content = []
        if file_paths:
            html_content.append('<div class="file-list">')
            html_content.append('<h3>文件列表:</h3>')
            html_content.append('<ul>')
            for i, file_path in enumerate(file_paths):
                anchor_id = f"file-{i}"
                # 构造源代码文件的绝对路径
                source_file_path = os.path.join(self.source_code_base_path, file_path.replace('/', os.sep))
                html_content.append(f'<li class="file-item">')
                html_content.append(f'  <a href="#{anchor_id}" class="file-link">跳转到文件</a>')
                html_content.append(f'  <a href="file:///{source_file_path}" class="file-link" target="_blank">打开源代码</a>')
                html_content.append(f'  {file_path}')
                html_content.append('</li>')
            html_content.append('</ul>')
            html_content.append('</div>')
        return html_content


    def _generate_html_line_diff_content(self, 
                                    file_path: str,
                                    source_lines: List[str],
                                    diff_data: LineCoverageDiff,
                                    anchor_id: str) -> str:
        """
        生成HTML格式的行覆盖率差异内容
        
        Args:
            file_path: 文件路径
            source_lines: 源代码行列表
            diff_data: 行覆盖率差异数据
            anchor_id: 锚点ID，用于页面内跳转
            
        Returns:
            HTML格式的差异内容
        """
        html_lines = []

        # 构造源代码文件的绝对路径
        source_file_path = os.path.join(self.source_code_base_path, file_path.replace('/', os.sep))
        
        # 添加文件标题，包含锚点和跳转到源代码的链接
        html_lines.append(f'<div class="file-header" id="{anchor_id}">文件: {file_path} <a href="file:///{source_file_path}" class="file-link" target="_blank">[打开源代码]</a></div>')
        
        # 创建左右两列的容器
        html_lines.append('<div class="diff-container">')
        
        # 左侧面板 - 仅在第一个数据集中的行
        html_lines.append('<div class="diff-panel">')
        html_lines.append('<div class="panel-header">仅在Bug执行中出现的行</div>')
        html_lines.append('<div class="code-container">')
        
        # 处理仅在第一个数据集中的行
        if diff_data.only_in_first:
            # 获取需要显示的行号（包括上下文和分隔符标记）
            only_first_lines = set(diff_data.only_in_first.keys())
            extended_lines = self._get_extended_line_range(only_first_lines, len(source_lines), self.context_lines)
            
            for line_num, is_separator in extended_lines:
                if is_separator:
                    # 添加分隔符行
                    html_lines.append('<div class="code-line separator-line"><span class="line-number"></span><div class="separator-content">⋮</div></div>')
                else:
                    # 确保行号在有效范围内
                    if 1 <= line_num <= len(source_lines):
                        # 对源代码进行HTML转义，确保特殊字符被正确显示
                        line_content = html.escape(source_lines[line_num - 1].rstrip('\n\r'))
                        # 判断是否是覆盖行
                        if line_num in only_first_lines:
                            html_lines.append(f'<div class="code-line covered-line"><span class="line-number">{line_num}</span>{line_content}</div>')
                        else:
                            html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span>{line_content}</div>')
                    else:
                        html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span>// 行号超出范围</div>')
        else:
            html_lines.append('<div class="code-line context-line"><span class="line-number"></span>// 无差异行</div>')
            
        html_lines.append('</div>')  # 结束代码容器
        html_lines.append('</div>')  # 结束左侧面板
        
        # 右侧面板 - 仅在第二个数据集中的行
        html_lines.append('<div class="diff-panel">')
        html_lines.append('<div class="panel-header">仅在正确执行中出现的行</div>')
        html_lines.append('<div class="code-container">')
        
        # 处理仅在第二个数据集中的行
        if diff_data.only_in_second:
            # 获取需要显示的行号（包括上下文和分隔符标记）
            only_second_lines = set(diff_data.only_in_second.keys())
            extended_lines = self._get_extended_line_range(only_second_lines, len(source_lines), self.context_lines)
            
            for line_num, is_separator in extended_lines:
                if is_separator:
                    # 添加分隔符行
                    html_lines.append('<div class="code-line separator-line"><span class="line-number"></span><div class="separator-content">⋮</div></div>')
                else:
                    # 确保行号在有效范围内
                    if 1 <= line_num <= len(source_lines):
                        # 对源代码进行HTML转义，确保特殊字符被正确显示
                        line_content = html.escape(source_lines[line_num - 1].rstrip('\n\r'))
                        # 判断是否是覆盖行
                        if line_num in only_second_lines:
                            html_lines.append(f'<div class="code-line covered-line"><span class="line-number">{line_num}</span>{line_content}</div>')
                        else:
                            html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span>{line_content}</div>')
                    else:
                        html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span>// 行号超出范围</div>')
        else:
            html_lines.append('<div class="code-line context-line"><span class="line-number"></span>// 无差异行</div>')
            
        html_lines.append('</div>')  # 结束代码容器
        html_lines.append('</div>')  # 结束右侧面板        
        html_lines.append('</div>')  # 结束diff-container
        
        return '\n'.join(html_lines)


    def _generate_html_branch_diff_content(self, 
                                    file_path: str,
                                    source_lines: List[str],
                                    diff_data: BranchCoverageDiff,
                                    anchor_id: str) -> str:
        """
        生成HTML格式的分支覆盖率差异内容
        
        Args:
            file_path: 文件路径
            source_lines: 源代码行列表
            diff_data: 分支覆盖率差异数据
            anchor_id: 锚点ID，用于页面内跳转
            
        Returns:
            HTML格式的差异内容
        """
        html_lines = []
        
        # 构造源代码文件的绝对路径
        source_file_path = os.path.join(self.source_code_base_path, file_path.replace('/', os.sep))
        
        # 添加文件标题，包含锚点和跳转到源代码的链接
        html_lines.append(f'<div class="branch-file-header" id="{anchor_id}">文件: {file_path} <a href="file:///{source_file_path}" class="file-link" target="_blank">[打开源代码]</a></div>')
        
        # 创建左右两列的容器
        html_lines.append('<div class="branch-diff-container">')
        
        # 左侧面板 - 仅在第一个数据集中的分支
        html_lines.append('<div class="branch-diff-panel">')
        html_lines.append('<div class="branch-panel-header">仅在Bug执行中出现的分支</div>')
        html_lines.append('<div class="branch-code-container">')
        
        # 处理仅在第一个数据集中的分支
        if diff_data.only_in_first:
            # 获取需要显示的行号（包括上下文和分隔符标记）
            only_first_lines = set(diff_data.only_in_first.keys())
            extended_lines = self._get_extended_line_range(only_first_lines, len(source_lines), self.context_lines)
            
            for line_num, is_separator in extended_lines:
                if is_separator:
                    # 添加分隔符行
                    html_lines.append('<div class="branch-code-line separator-line"><span class="branch-line-number"></span><div class="separator-content">⋮</div></div>')
                else:
                    # 确保行号在有效范围内
                    if 1 <= line_num <= len(source_lines):
                        # 对源代码进行HTML转义，确保特殊字符被正确显示
                        line_content = html.escape(source_lines[line_num - 1].rstrip('\n\r'))
                        # 判断是否是覆盖行
                        if line_num in only_first_lines:
                            covered, total = diff_data.only_in_first[line_num]
                            html_lines.append(f'<div class="branch-code-line branch-covered-line"><span class="branch-line-number">{line_num}</span>{line_content} // 分支: 覆盖{covered}/{total}</div>')
                        else:
                            html_lines.append(f'<div class="branch-code-line branch-context-line"><span class="branch-line-number">{line_num}</span>{line_content}</div>')
                    else:
                        html_lines.append(f'<div class="branch-code-line branch-context-line"><span class="branch-line-number">{line_num}</span>// 行号超出范围</div>')
        else:
            html_lines.append('<div class="branch-code-line branch-context-line"><span class="branch-line-number"></span>// 无差异分支</div>')
            
        html_lines.append('</div>')  # 结束代码容器
        html_lines.append('</div>')  # 结束左侧面板
        
        # 右侧面板 - 仅在第二个数据集中的分支
        html_lines.append('<div class="branch-diff-panel">')
        html_lines.append('<div class="branch-panel-header">仅在正确执行中出现的分支</div>')
        html_lines.append('<div class="branch-code-container">')
        
        # 处理仅在第二个数据集中的分支
        if diff_data.only_in_second:
            # 获取需要显示的行号（包括上下文和分隔符标记）
            only_second_lines = set(diff_data.only_in_second.keys())
            extended_lines = self._get_extended_line_range(only_second_lines, len(source_lines), self.context_lines)
            
            for line_num, is_separator in extended_lines:
                if is_separator:
                    # 添加分隔符行
                    html_lines.append('<div class="branch-code-line separator-line"><span class="branch-line-number"></span><div class="separator-content">⋮</div></div>')
                else:
                    # 确保行号在有效范围内
                    if 1 <= line_num <= len(source_lines):
                        # 对源代码进行HTML转义，确保特殊字符被正确显示
                        line_content = html.escape(source_lines[line_num - 1].rstrip('\n\r'))
                        # 判断是否是覆盖行
                        if line_num in only_second_lines:
                            covered, total = diff_data.only_in_second[line_num]
                            html_lines.append(f'<div class="branch-code-line branch-covered-line"><span class="branch-line-number">{line_num}</span>{line_content} // 分支: 覆盖{covered}/{total}</div>')
                        else:
                            html_lines.append(f'<div class="branch-code-line branch-context-line"><span class="branch-line-number">{line_num}</span>{line_content}</div>')
                    else:
                        html_lines.append(f'<div class="branch-code-line branch-context-line"><span class="branch-line-number">{line_num}</span>// 行号超出范围</div>')
        else:
            html_lines.append('<div class="branch-code-line branch-context-line"><span class="branch-line-number"></span>// 无差异分支</div>')
            
        html_lines.append('</div>')  # 结束代码容器
        html_lines.append('</div>')  # 结束右侧面板
        html_lines.append('</div>')  # 结束diff-container
        
        return '\n'.join(html_lines)


    def generate_visual_line_diff_report(self, result: PairAnalysisResult, output_dir: str):
        """
        生成行覆盖率可视化HTML差异报告
        
        Args:
            result: 覆盖率对比结果
            output_dir: 报告输出目录
        """
        # 创建行覆盖率HTML报告文件
        html_report_path = os.path.join(output_dir, f"{result.case_name}{self.LINE_REPORT_SUFFIX}")
        
        # 收集所有文件路径
        file_paths = []
        if result.diff_result.line_coverage_diff:
            file_paths = list(result.diff_result.line_coverage_diff.keys())
        
        # 开始构建HTML内容
        html_content = self._generate_html_header(
            f"{result.case_name} 行覆盖率差异可视化报告",
            self._get_line_css_styles()
        )
        
        html_content.append(f'<h1>{result.case_name} 行覆盖率差异可视化报告</h1>')
        html_content.append(f'<p>生成时间: {self._get_current_time()}</p>')
        
        # 添加文件列表
        html_content.extend(self._generate_file_list_html(file_paths))
        
        # 处理行覆盖率差异
        if result.diff_result.line_coverage_diff:
            html_content.append('<h2>行覆盖率差异</h2>')
            
            for i, (file_path, diff_data) in enumerate(result.diff_result.line_coverage_diff.items()):
                # 读取源代码文件
                source_lines = self._read_source_file(file_path)
                
                # 生成该文件的HTML行覆盖率差异内容，传入锚点ID
                anchor_id = f"file-{i}"
                file_diff_html = self._generate_html_line_diff_content(file_path, source_lines, diff_data, anchor_id)
                html_content.append(file_diff_html)
        
        # 添加返回顶部按钮
        html_content.extend(self._generate_html_footer())
        
        # 写入HTML文件
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
        
        self.logger.info(f"行覆盖率可视化差异报告已生成: {html_report_path}")


    def generate_visual_branch_diff_report(self, result: PairAnalysisResult, output_dir: str):
        """
        生成分支覆盖率可视化HTML差异报告
        
        Args:
            result: 覆盖率对比结果
            output_dir: 报告输出目录
        """
        # 创建分支覆盖率HTML报告文件
        html_report_path = os.path.join(output_dir, f"{result.case_name}{self.BRANCH_REPORT_SUFFIX}")
        
        # 收集所有文件路径
        file_paths = []
        if result.diff_result.branch_coverage_diff:
            file_paths = list(result.diff_result.branch_coverage_diff.keys())
        
        # 开始构建HTML内容
        html_content = self._generate_html_header(
            f"{result.case_name} 分支覆盖率差异可视化报告",
            self._get_branch_css_styles()
        )
        
        html_content.append(f'<h1>{result.case_name} 分支覆盖率差异可视化报告</h1>')
        html_content.append(f'<p>生成时间: {self._get_current_time()}</p>')
        
        # 添加文件列表
        html_content.extend(self._generate_file_list_html(file_paths))
        
        # 处理分支覆盖率差异
        if result.diff_result.branch_coverage_diff:
            html_content.append('<h2>分支覆盖率差异</h2>')
            
            for i, (file_path, diff_data) in enumerate(result.diff_result.branch_coverage_diff.items()):
                # 读取源代码文件
                source_lines = self._read_source_file(file_path)
                
                # 生成该文件的HTML分支覆盖率差异内容，传入锚点ID
                anchor_id = f"file-{i}"
                file_diff_html = self._generate_html_branch_diff_content(file_path, source_lines, diff_data, anchor_id)
                html_content.append(file_diff_html)
        
        # 添加返回顶部按钮
        html_content.extend(self._generate_html_footer())
        
        # 写入HTML文件
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
        
        self.logger.info(f"分支覆盖率可视化差异报告已生成: {html_report_path}")


    def generate_visual_diff_report(self, result: PairAnalysisResult, output_dir: str):
        """
        生成可视化HTML差异报告，分别生成行和分支覆盖率的独立报告
        
        Args:
            result: 覆盖率对比结果
            output_dir: 报告输出目录
        """
        # 生成行覆盖率可视化报告
        self.generate_visual_line_diff_report(result, output_dir)
        
        # 生成分支覆盖率可视化报告
        self.generate_visual_branch_diff_report(result, output_dir)

    def _get_current_time(self) -> str:
        """
        获取当前时间字符串
        
        Returns:
            格式化的时间字符串
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")