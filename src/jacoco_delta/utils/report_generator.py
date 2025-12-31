import os
from datetime import datetime
from typing import List, Set
import html 

from jacoco_delta.core.calculator import format_line_coverage_increment_data, format_branch_coverage_increment_data
from jacoco_delta.core.differ import format_line_diff_result, format_branch_diff_result
from jacoco_delta.utils.data_types import LineCoverageDiff, BranchCoverageDiff, PairAnalysisResult, FullAnalysisResult
from jacoco_delta.utils.logger import get_logger
from jacoco_delta.utils.css_styles import line_css_style, branch_css_style, index_css_style


class ReportGenerator:
    # 常量定义
    LINE_REPORT_SUFFIX = "_line_diff_report.html"
    BRANCH_REPORT_SUFFIX = "_branch_diff_report.html"
    CODE_CONTAINER_CLASS = "code-container"
    BRANCH_CODE_CONTAINER_CLASS = "branch-code-container"
    
    def __init__(self, source_code_base_path: str = "", context_lines: int = 5):
        """
        初始化报告生成器
        
        Args:
            source_code_base_path: 源代码基础路径, 用于读取源代码文件
            context_lines: 上下文行数, 用于显示差异前后的代码上下文
        """
        self.source_code_base_path = source_code_base_path
        self.context_lines = context_lines
        self.logger = get_logger("report_generator")


    def generate_incremental_data(self, result: PairAnalysisResult, output_dir: str):
        """
        生成增量覆盖率数据结果
        
        Args:
            output_dir: 报告输出目录
            result: 覆盖率对比结果
        """
        bug_line_incremental_data_path = os.path.join(output_dir, f"bug_{result.case_name}_line_incremental_data.md")
        bug_branch_incremental_data_path = os.path.join(output_dir, f"bug_{result.case_name}_branch_incremental_data.md")
        with open(bug_line_incremental_data_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_line_coverage_increment_data(result.bug_incremental_coverage["line_coverage_incremental"])))
        self.logger.info(f"生成bug line coverage increment data: {bug_line_incremental_data_path}")
        with open(bug_branch_incremental_data_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_branch_coverage_increment_data(result.bug_incremental_coverage["branch_coverage_incremental"])))
        self.logger.info(f"生成bug branch coverage increment data: {bug_branch_incremental_data_path}")

        correct_line_incremental_data_path = os.path.join(output_dir, f"correct_{result.case_name}_line_incremental_data.md")
        correct_branch_incremental_data_path = os.path.join(output_dir, f"correct_{result.case_name}_branch_incremental_data.md")
        with open(correct_line_incremental_data_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_line_coverage_increment_data(result.correct_incremental_coverage["line_coverage_incremental"])))
        self.logger.info(f"生成correct line coverage increment data: {correct_line_incremental_data_path}")
        with open(correct_branch_incremental_data_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_branch_coverage_increment_data(result.correct_incremental_coverage["branch_coverage_incremental"])))
        self.logger.info(f"生成correct branch coverage increment data: {correct_branch_incremental_data_path}")


    def generate_diff_data(self, result: PairAnalysisResult, output_dir: str):
        """
        生成差异数据结果
        
        Args:
            output_dir: 报告输出目录
            result: 覆盖率对比结果
        """
        line_diff_data_path = os.path.join(output_dir, f"line_diff_data.md")
        branch_diff_data_path = os.path.join(output_dir, f"branch_diff_data.md")
        with open(line_diff_data_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_line_diff_result(result.diff_result.line_coverage_diff)))
        self.logger.info(f"生成line diff data: {line_diff_data_path}")
        with open(branch_diff_data_path, "w", encoding='utf-8') as f:
            f.write("\n".join(format_branch_diff_result(result.diff_result.branch_coverage_diff)))
        self.logger.info(f"生成branch diff data: {branch_diff_data_path}")


    def generate_all_data(self, result: PairAnalysisResult, output_dir: str):
        """
        生成所有数据结果
        
        Args:
            output_dir: 报告输出目录
            result: 覆盖率对比结果
        """
        self.generate_incremental_data(result, output_dir)
        self.generate_diff_data(result, output_dir)


    def _get_current_time(self) -> str:
        """
        获取当前时间字符串
        
        Returns:
            格式化的时间字符串
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
                # 如果找不到文件, 返回空列表
                return [f"// 文件未找到: {full_path}"]
        
        # 如果所有编码都失败, 返回错误信息
        self.logger.error(f"无法读取源代码文件: {full_path} 所有编码尝试失败")
        return [f"// 无法读取文件: {full_path}"]


    def _get_extended_line_range(self, line_numbers: Set[int], max_lines: int, context_lines: int = 5) -> List[tuple]:
        """
        获取扩展的行号范围, 包括上下文行, 并标记分隔点
        
        Args:
            line_numbers: 需要高亮的行号集合
            max_lines: 文件总行数
            context_lines: 上下文行数, 默认为5
            
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
                # 如果范围重叠或相邻, 则合并
                if start <= current_end + 1:
                    current_end = max(current_end, end)
                else:
                    # 添加当前范围
                    merged_ranges.append((current_start, current_end))
                    current_start, current_end = start, end
            
            # 添加最后一个范围
            merged_ranges.append((current_start, current_end))
        
        # 生成实际的行号列表, 包含分隔符标记
        result_lines = []
        for i, (start, end) in enumerate(merged_ranges):
            # 添加范围内的所有行
            for line_num in range(start, end + 1):
                result_lines.append((line_num, False))  # (行号, 是否为分隔符)
            
            # 如果不是最后一个范围, 添加分隔符
            if i < len(merged_ranges) - 1:
                result_lines.append((-1, True))  # (-1表示分隔符, True表示是分隔符)
        
        return result_lines


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
            '<link rel="preconnect" href="https://fonts.googleapis.com">',
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">',
            '<script>',
            '// 全局侧边栏切换功能',
            'function toggleSidebar() {',
            '    const sidebar = document.querySelector(".sidebar");',
            '    sidebar.classList.toggle("collapsed");',
            '}',
            '',
            '// 目录展开/收起功能',
            'function toggleDir(dirHeader) {',
            '    const toggle = dirHeader.querySelector(".dir-toggle");',
            '    const content = dirHeader.nextElementSibling;',
            '    ',
            '    if (content.style.display === "none" || content.style.display === "") {',
            '        content.style.display = "block";',
            '        toggle.textContent = "−";',
            '    } else {',
            '        content.style.display = "none";',
            '        toggle.textContent = "+";',
            '    }',
            '}',
            '',
            '// 文件链接点击事件',
            'document.addEventListener(\'DOMContentLoaded\', () => {',
            '    const fileLinks = document.querySelectorAll(\'.file-link\');',
            '    ',
            '    fileLinks.forEach(link => {',
            '        link.addEventListener(\'click\', (e) => {',
            '            e.preventDefault();',
            '            ',
            '            fileLinks.forEach(l => l.classList.remove(\'active\'));',
            '            link.classList.add(\'active\');',
            '            ',
            '            const targetId = link.getAttribute(\'href\');',
            '            const targetElement = document.querySelector(targetId);',
            '            if (targetElement) {',
            '                targetElement.scrollIntoView({',
            '                    behavior: \'smooth\',',
            '                    block: \'start\'',
            '                });',
            '            }',
            '        });',
            '    });',
            '    ',
            '    if (fileLinks.length > 0) {',
            '        fileLinks[0].classList.add(\'active\');',
            '    }',
            '});',
            '</script>',
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
            '</body>',
            '</html>'
        ]


    def _generate_file_list_html(self, file_paths: List[str]) -> List[str]:
        """
        生成文件列表HTML(作为侧边栏, 支持层级展开/收起, 默认展开)
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件列表HTML内容列表
        """
        html_content = []
        if not file_paths:
            return html_content
        
        # 构建目录树结构
        dir_tree = {}
        for i, file_path in enumerate(file_paths):
            # 将文件路径按/分割成目录和文件名
            parts = file_path.split('/')
            current = dir_tree
            # 创建目录结构
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            # 添加文件名
            current[parts[-1]] = {'__file__': True, 'anchor_id': f"file-{i}"}
        
        # 递归合并连续的空文件夹
        def merge_empty_dirs(tree, path_parts=[]):
            merged_tree = {}
            for name, content in tree.items():
                if isinstance(content, dict) and '__file__' not in content:
                    # 是目录, 检查是否只有一个子目录且没有文件
                    if len(content) == 1 and '__file__' not in list(content.values())[0]:
                        # 合并目录
                        subname, subcontent = list(content.items())[0]
                        new_name = name + '/' + subname
                        new_content = merge_empty_dirs(subcontent, path_parts + [name, subname])
                        merged_tree[new_name] = new_content
                    else:
                        # 正常处理
                        merged_tree[name] = merge_empty_dirs(content, path_parts + [name])
                else:
                    # 是文件或有多个子项的目录
                    merged_tree[name] = content
            return merged_tree
        
        # 合并连续空文件夹
        merged_dir_tree = merge_empty_dirs(dir_tree)
        
        # 递归生成目录树HTML
        def generate_tree_html(tree, prefix=''):
            tree_html = []
            for name, content in sorted(tree.items()):
                if name == '__file__':
                    continue
                    
                if isinstance(content, dict) and '__file__' in content:
                    # 处理文件
                    tree_html.append(f'<li class="file-item">')
                    tree_html.append(f'  <a href="#{content["anchor_id"]}" class="file-link"><span>{name}</span></a>')
                    tree_html.append('</li>')
                else:
                    # 处理目录
                    tree_html.append(f'<li class="dir-item">')
                    tree_html.append(f'  <div class="dir-header" onclick="toggleDir(this)">')
                    tree_html.append(f'    <span class="dir-toggle">−</span>')
                    tree_html.append(f'    <span class="dir-name">{name}</span>')
                    tree_html.append(f'  </div>')
                    tree_html.append(f'  <ul class="dir-content" style="display: block;">')
                    tree_html.extend(generate_tree_html(content, prefix + name + '/'))
                    tree_html.append(f'  </ul>')
                    tree_html.append(f'</li>')
            return tree_html
        
        # 生成侧边栏
        html_content.append('<div class="sidebar" id="sidebar">')

        html_content.append('<h3 class="file-list-title">文件差异列表</h3>')
        html_content.append('<ul class="dir-tree">')
        html_content.extend(generate_tree_html(merged_dir_tree))
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
            anchor_id: 锚点ID, 用于页面内跳转
            
        Returns:
            HTML格式的差异内容
        """
        html_lines = []

        # 构造源代码文件的绝对路径
        source_file_path = os.path.join(self.source_code_base_path, file_path.replace('/', os.sep))
        
        # 添加文件标题, 包含锚点和跳转到源代码的链接
        html_lines.append(f'<div class="file-header" id="{anchor_id}">')
        html_lines.append(f'    文件: {file_path}')
        html_lines.append(f'    <a href="file:///{source_file_path}" target="_blank">')
        html_lines.append(f'        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">')
        html_lines.append(f'            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>')
        html_lines.append(f'            <polyline points="14 2 14 8 20 8"></polyline>')
        html_lines.append(f'            <line x1="16" y1="13" x2="8" y2="13"></line>')
        html_lines.append(f'            <line x1="16" y1="17" x2="8" y2="17"></line>')
        html_lines.append(f'            <polyline points="10 9 9 9 8 9"></polyline>')
        html_lines.append(f'        </svg>')
        html_lines.append(f'        打开源代码')
        html_lines.append(f'    </a>')
        html_lines.append(f'</div>')
        
        # 创建左右两列的容器
        html_lines.append('<div class="diff-container">')
        
        # 左侧面板 - 仅在第一个数据集中的行(Bug执行)
        html_lines.append('<div class="diff-panel">')
        html_lines.append('<div class="panel-header">仅在Bug执行中出现的行</div>')
        html_lines.append('<div class="code-container">')
        
        # 处理仅在第一个数据集中的行
        if diff_data.only_in_first:
            # 获取需要显示的行号(包括上下文和分隔符标记)
            only_first_lines = set(diff_data.only_in_first.keys())
            extended_lines = self._get_extended_line_range(only_first_lines, len(source_lines), self.context_lines)
            
            for line_num, is_separator in extended_lines:
                if is_separator:
                    # 添加分隔符行(适配新样式)
                    html_lines.append('<div class="code-line separator-line"><span class="line-number"></span><span class="code-content">⋮</span></div>')
                else:
                    # 确保行号在有效范围内
                    if 1 <= line_num <= len(source_lines):
                        # 对源代码进行HTML转义, 确保特殊字符被正确显示
                        line_content = html.escape(source_lines[line_num - 1].rstrip('\n\r'))
                        # 判断是否是覆盖行 - 使用bug-line类替代covered-line
                        if line_num in only_first_lines:
                            html_lines.append(f'<div class="code-line bug-line"><span class="line-number">{line_num}</span><span class="code-content">{line_content}</span></div>')
                        else:
                            html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span><span class="code-content">{line_content}</span></div>')
                    else:
                        html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span><span class="code-content">// 行号超出范围</span></div>')
        else:
            html_lines.append('<div class="code-line context-line"><span class="line-number"></span><span class="code-content">// 无差异行</span></div>')
            
        html_lines.append('</div>')  # 结束代码容器
        html_lines.append('</div>')  # 结束左侧面板
        
        # 右侧面板 - 仅在第二个数据集中的行(正确执行)
        html_lines.append('<div class="diff-panel">')
        html_lines.append('<div class="panel-header">仅在正确执行中出现的行</div>')
        html_lines.append('<div class="code-container">')
        
        # 处理仅在第二个数据集中的行
        if diff_data.only_in_second:
            # 获取需要显示的行号(包括上下文和分隔符标记)
            only_second_lines = set(diff_data.only_in_second.keys())
            extended_lines = self._get_extended_line_range(only_second_lines, len(source_lines), self.context_lines)
            
            for line_num, is_separator in extended_lines:
                if is_separator:
                    # 添加分隔符行(适配新样式)
                    html_lines.append('<div class="code-line separator-line"><span class="line-number"></span><span class="code-content">⋮</span></div>')
                else:
                    # 确保行号在有效范围内
                    if 1 <= line_num <= len(source_lines):
                        # 对源代码进行HTML转义, 确保特殊字符被正确显示
                        line_content = html.escape(source_lines[line_num - 1].rstrip('\n\r'))
                        # 判断是否是覆盖行 - 使用correct-line类替代covered-line
                        if line_num in only_second_lines:
                            html_lines.append(f'<div class="code-line correct-line"><span class="line-number">{line_num}</span><span class="code-content">{line_content}</span></div>')
                        else:
                            html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span><span class="code-content">{line_content}</span></div>')
                    else:
                        html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span><span class="code-content">// 行号超出范围</span></div>')
        else:
            html_lines.append('<div class="code-line context-line"><span class="line-number"></span><span class="code-content">// 无差异行</span></div>')
            
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
            anchor_id: 锚点ID, 用于页面内跳转
            
        Returns:
            HTML格式的差异内容
        """
        html_lines = []
        
        # 构造源代码文件的绝对路径
        source_file_path = os.path.join(self.source_code_base_path, file_path.replace('/', os.sep))
        
        # 添加文件标题, 包含锚点和跳转到源代码的链接
        html_lines.append(f'<div class="file-header" id="{anchor_id}">')
        html_lines.append(f'    文件: {file_path}')
        html_lines.append(f'    <a href="file:///{source_file_path}" target="_blank">')
        html_lines.append(f'        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">')
        html_lines.append(f'            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>')
        html_lines.append(f'            <polyline points="14 2 14 8 20 8"></polyline>')
        html_lines.append(f'            <line x1="16" y1="13" x2="8" y2="13"></line>')
        html_lines.append(f'            <line x1="16" y1="17" x2="8" y2="17"></line>')
        html_lines.append(f'            <polyline points="10 9 9 9 8 9"></polyline>')
        html_lines.append(f'        </svg>')
        html_lines.append(f'        打开源代码')
        html_lines.append(f'    </a>')
        html_lines.append(f'</div>')
        
        # 创建左右两列的容器(使用统一的diff-container类)
        html_lines.append('<div class="diff-container">')
        
        # 左侧面板 - 仅在第一个数据集中的分支(Bug执行)
        html_lines.append('<div class="diff-panel">')
        html_lines.append('<div class="panel-header">仅在Bug执行中出现的分支</div>')
        html_lines.append('<div class="code-container">')
        
        # 处理仅在第一个数据集中的分支
        if diff_data.only_in_first:
            # 获取需要显示的行号(包括上下文和分隔符标记)
            only_first_lines = set(diff_data.only_in_first.keys())
            extended_lines = self._get_extended_line_range(only_first_lines, len(source_lines), self.context_lines)
            
            for line_num, is_separator in extended_lines:
                if is_separator:
                    # 添加分隔符行(适配统一样式)
                    html_lines.append('<div class="code-line separator-line"><span class="line-number"></span><span class="code-content">⋮</span></div>')
                else:
                    # 确保行号在有效范围内
                    if 1 <= line_num <= len(source_lines):
                        # 对源代码进行HTML转义, 确保特殊字符被正确显示
                        line_content = html.escape(source_lines[line_num - 1].rstrip('\n\r'))
                        # 判断是否是覆盖行 - 使用bug-line类
                        if line_num in only_first_lines:
                            covered, total = diff_data.only_in_first[line_num]
                            full_content = f'{line_content} // 分支: 覆盖{covered}/{total}'
                            html_lines.append(f'<div class="code-line bug-line"><span class="line-number">{line_num}</span><span class="code-content">{full_content}</span></div>')
                        else:
                            html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span><span class="code-content">{line_content}</span></div>')
                    else:
                        html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span><span class="code-content">// 行号超出范围</span></div>')
        else:
            html_lines.append('<div class="code-line context-line"><span class="line-number"></span><span class="code-content">// 无差异分支</span></div>')
            
        html_lines.append('</div>')  # 结束代码容器
        html_lines.append('</div>')  # 结束左侧面板
        
        # 右侧面板 - 仅在第二个数据集中的分支(正确执行)
        html_lines.append('<div class="diff-panel">')
        html_lines.append('<div class="panel-header">仅在正确执行中出现的分支</div>')
        html_lines.append('<div class="code-container">')
        
        # 处理仅在第二个数据集中的分支
        if diff_data.only_in_second:
            # 获取需要显示的行号(包括上下文和分隔符标记)
            only_second_lines = set(diff_data.only_in_second.keys())
            extended_lines = self._get_extended_line_range(only_second_lines, len(source_lines), self.context_lines)
            
            for line_num, is_separator in extended_lines:
                if is_separator:
                    # 添加分隔符行(适配统一样式)
                    html_lines.append('<div class="code-line separator-line"><span class="line-number"></span><span class="code-content">⋮</span></div>')
                else:
                    # 确保行号在有效范围内
                    if 1 <= line_num <= len(source_lines):
                        # 对源代码进行HTML转义, 确保特殊字符被正确显示
                        line_content = html.escape(source_lines[line_num - 1].rstrip('\n\r'))
                        # 判断是否是覆盖行 - 使用correct-line类
                        if line_num in only_second_lines:
                            covered, total = diff_data.only_in_second[line_num]
                            full_content = f'{line_content} // 分支: 覆盖{covered}/{total}'
                            html_lines.append(f'<div class="code-line correct-line"><span class="line-number">{line_num}</span><span class="code-content">{full_content}</span></div>')
                        else:
                            html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span><span class="code-content">{line_content}</span></div>')
                    else:
                        html_lines.append(f'<div class="code-line context-line"><span class="line-number">{line_num}</span><span class="code-content">// 行号超出范围</span></div>')
        else:
            html_lines.append('<div class="code-line context-line"><span class="line-number"></span><span class="code-content">// 无差异分支</span></div>')
            
        html_lines.append('</div>')  # 结束代码容器
        html_lines.append('</div>')  # 结束右侧面板
        html_lines.append('</div>')  # 结束diff-container
        
        return '\n'.join(html_lines)


    def generate_line_diff_report(self, result: PairAnalysisResult, output_dir: str) -> str:
        """
        生成行覆盖率可视化HTML差异报告
        
        Args:
            result: 覆盖率对比结果
            output_dir: 报告输出目录
        
        Returns:
            str: 行覆盖率可视化HTML差异报告路径
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
            line_css_style()
        )
        
        html_content.append('<!-- 固定导航栏 -->')
        html_content.append('<div class="fixed-header">')
        html_content.append(f'    <h1>{result.case_name} 行覆盖率差异可视化报告</h1>')
        html_content.append('    <button class="sidebar-toggle-btn" onclick="toggleSidebar()">')
        html_content.append('        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">')
        html_content.append('            <line x1="3" y1="12" x2="21" y2="12"></line>')
        html_content.append('            <line x1="3" y1="6" x2="21" y2="6"></line>')
        html_content.append('            <line x1="3" y1="18" x2="21" y2="18"></line>')
        html_content.append('        </svg>')
        html_content.append('        文件列表')
        html_content.append('    </button>')
        html_content.append('</div>')
        
        # 添加文件列表(侧边栏)
        html_content.extend(self._generate_file_list_html(file_paths))
        
        # 添加主内容区域
        html_content.append('<div class="main-content">')
        html_content.append(f'<p>生成时间: {self._get_current_time()}</p>')
        
        # 处理行覆盖率差异
        if result.diff_result.line_coverage_diff:
            html_content.append('<h2>行覆盖率差异</h2>')
            
            for i, (file_path, diff_data) in enumerate(result.diff_result.line_coverage_diff.items()):
                # 读取源代码文件
                source_lines = self._read_source_file(file_path)
                
                # 生成该文件的HTML行覆盖率差异内容, 传入锚点ID
                anchor_id = f"file-{i}"
                file_diff_html = self._generate_html_line_diff_content(file_path, source_lines, diff_data, anchor_id)
                html_content.append(file_diff_html)
        
        html_content.append('</div>')  # 结束主内容区域
        
        # 添加HTML尾部
        html_content.extend(self._generate_html_footer())
        
        # 写入HTML文件
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
        
        self.logger.info(f"行覆盖率可视化差异报告已生成: {html_report_path}")
        return html_report_path


    def generate_branch_diff_report(self, result: PairAnalysisResult, output_dir: str) -> str:
        """
        生成分支覆盖率HTML差异报告
        
        Args:
            result: 覆盖率对比结果
            output_dir: 报告输出目录
        
        Returns:
            str: 分支覆盖率可视化HTML差异报告路径
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
            branch_css_style()
        )
        html_content.append('<!-- 固定导航栏 -->')
        html_content.append('<div class="fixed-header">')
        html_content.append(f'    <h1>{result.case_name} 分支覆盖率差异可视化报告</h1>')
        html_content.append('    <button class="sidebar-toggle-btn" onclick="toggleSidebar()">')
        html_content.append('        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">')
        html_content.append('            <line x1="3" y1="12" x2="21" y2="12"></line>')
        html_content.append('            <line x1="3" y1="6" x2="21" y2="6"></line>')
        html_content.append('            <line x1="3" y1="18" x2="21" y2="18"></line>')
        html_content.append('        </svg>')
        html_content.append('        文件列表')
        html_content.append('    </button>')
        html_content.append('</div>')
        
        # 添加文件列表(侧边栏)
        html_content.extend(self._generate_file_list_html(file_paths))
        
        # 添加主内容区域
        html_content.append('<div class="main-content">')
        html_content.append(f'<p>生成时间: {self._get_current_time()}</p>')
        
        # 处理分支覆盖率差异
        if result.diff_result.branch_coverage_diff:
            html_content.append('<h2>分支覆盖率差异</h2>')
            
            for i, (file_path, diff_data) in enumerate(result.diff_result.branch_coverage_diff.items()):
                # 读取源代码文件
                source_lines = self._read_source_file(file_path)
                
                # 生成该文件的HTML分支覆盖率差异内容, 传入锚点ID
                anchor_id = f"file-{i}"
                file_diff_html = self._generate_html_branch_diff_content(file_path, source_lines, diff_data, anchor_id)
                html_content.append(file_diff_html)
        
        html_content.append('</div>')  # 结束主内容区域
        
        # 添加HTML尾部
        html_content.extend(self._generate_html_footer())
        
        # 写入HTML文件
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
        
        self.logger.info(f"分支覆盖率可视化差异报告已生成: {html_report_path}")
        return html_report_path


    def generate_diff_report(self, result: PairAnalysisResult, output_dir: str) -> tuple[str, str]:
        """
        生成HTML差异报告, 分别生成行和分支覆盖率的独立报告
        
        Args:
            result: 覆盖率对比结果
            output_dir: 报告输出目录
        """
        # 生成行覆盖率可视化报告
        line_report_path = self.generate_line_diff_report(result, output_dir)
        # 生成分支覆盖率可视化报告
        branch_report_path = self.generate_branch_diff_report(result, output_dir)
        return line_report_path, branch_report_path


    def generate_comprehensive_report(self, full_result: FullAnalysisResult, reproducer_data: dict, output_dir: str) -> None:
        """
        生成综合报告, 整合总体分析报告和Bug复现测试报告
        
        Args:
            full_result: 成对测试用例的信息
            reproducer_data: Reproducer的数据, 包含测试结果和覆盖率数据
            output_dir: 输出目录
        """
        report_path = os.path.join(output_dir, "index.html")
        
        css_styles = index_css_style()
        html_content = self._generate_html_header("综合覆盖率差异分析报告", css_styles)
        
        # 添加报告标题和生成时间
        html_content.append('<div class="container">')
        html_content.append('<header class="report-header">')
        html_content.append('<h1>综合覆盖率差异分析报告</h1>')
        html_content.append(f'<p class="report-time">生成时间: {self._get_current_time()}</p>')
        html_content.append('</header>')
        
        # 添加分析概览
        html_content.append('<section class="overview-section">')
        html_content.append('<h2>分析概览</h2>')
        html_content.append(f'<div class="overview-card">')
        html_content.append(f'<p>总共分析了 <strong>{len(full_result.pair_results)}</strong> 对测试用例</p>')
        html_content.append('</div>')
        html_content.append('</section>')
        
        # 添加测试用例列表
        html_content.append('<section class="test-cases-section">')
        html_content.append('<h2>测试用例列表</h2>')
        
        for pair_result in full_result.pair_results:
            case_name = pair_result.case_name
            bug_result_data = reproducer_data[f"bug_{case_name}"]
            correct_result_data = reproducer_data[f"correct_{case_name}"]
            line_diff_report_path = pair_result.line_diff_report_path
            branch_diff_report_path = pair_result.branch_diff_report_path
            
            # 为每个测试用例创建一个卡片
            html_content.append(f'<div class="test-case-card">')
            html_content.append(f'<h3>{pair_result.case_name}</h3>')
            
            # Bug测试结果
            # 前置条件执行结果
            html_content.append('<div class="test-result-group">')
            html_content.append('<h4>Bug测试用例: 前置条件执行结果</h4>')
            html_content.append(f'<p>状态: <span class="status {bug_result_data.precondition_result.status.value.lower()}">{bug_result_data.precondition_result.status.value}</span></p>')
            html_content.append(f'<p>执行时间: {bug_result_data.precondition_result.execution_time:.2f}秒</p>')
            html_content.append(f'<p>开始时间戳: {bug_result_data.precondition_result.timestamp}</p>')
            if bug_result_data.precondition_result.error_message:
                html_content.append(f'<p class="error-message">错误信息: {bug_result_data.precondition_result.error_message}</p>')
            html_content.append('</div>')
            # 属性执行结果
            html_content.append('<div class="test-result-group">')
            html_content.append('<h4>Bug测试用例: 属性执行结果</h4>')
            html_content.append(f'<p>状态: <span class="status {bug_result_data.property_result.status.value.lower()}">{bug_result_data.property_result.status.value}</span></p>')
            html_content.append(f'<p>执行时间: {bug_result_data.property_result.execution_time:.2f}秒</p>')
            html_content.append(f'<p>开始时间戳: {bug_result_data.property_result.timestamp}</p>')
            if bug_result_data.property_result.error_message:
                html_content.append(f'<p class="error-message">错误信息: {bug_result_data.property_result.error_message}</p>')
            html_content.append('</div>')
            
            # Correct测试结果
            # 前置条件执行结果
            html_content.append('<div class="test-result-group">')
            html_content.append('<h4>Correct测试用例: 前置条件执行结果</h4>')
            html_content.append(f'<p>状态: <span class="status {correct_result_data.precondition_result.status.value.lower()}">{correct_result_data.precondition_result.status.value}</span></p>')
            html_content.append(f'<p>执行时间: {correct_result_data.precondition_result.execution_time:.2f}秒</p>')
            html_content.append(f'<p>开始时间戳: {correct_result_data.precondition_result.timestamp}</p>')
            if correct_result_data.precondition_result.error_message:
                html_content.append(f'<p class="error-message">错误信息: {correct_result_data.precondition_result.error_message}</p>')
            html_content.append('</div>')
            # 属性执行结果
            html_content.append('<div class="test-result-group">')
            html_content.append('<h4>Correct测试用例: 属性执行结果</h4>')
            html_content.append(f'<p>状态: <span class="status {correct_result_data.property_result.status.value.lower()}">{correct_result_data.property_result.status.value}</span></p>')
            html_content.append(f'<p>执行时间: {correct_result_data.property_result.execution_time:.2f}秒</p>')
            html_content.append(f'<p>开始时间戳: {correct_result_data.property_result.timestamp}</p>')
            if correct_result_data.property_result.error_message:
                html_content.append(f'<p class="error-message">错误信息: {correct_result_data.property_result.error_message}</p>')
            html_content.append('</div>')
            
            # 报告链接
            html_content.append('<div class="report-links">')
            html_content.append(f'<a href="{os.path.relpath(line_diff_report_path, output_dir)}" target="_blank" class="report-link">行覆盖率差异报告</a>')
            html_content.append(f'<a href="{os.path.relpath(branch_diff_report_path, output_dir)}" target="_blank" class="report-link">分支覆盖率差异报告</a>')
            html_content.append('</div>')
            
            html_content.append('</div>')  # 结束test-case-card
        
        html_content.append('</section>')  # 结束test-cases-section
        html_content.append('</div>')  # 结束container
        
        html_content.extend(self._generate_html_footer())
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
        
        self.logger.info(f"综合分析报告已生成: {report_path}")