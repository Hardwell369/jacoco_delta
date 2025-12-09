# JaCoCo Delta

JaCoCo Delta 是一个用于分析 JaCoCo 代码覆盖率报告差异的工具，旨在识别与 bug 相关的覆盖率变化。

## 功能特点

- 分析成对测试用例的覆盖率差异
- 计算执行前后的覆盖率增量
- 生成详细的差异分析报告
- 支持行覆盖率和分支覆盖率分析

## 安装

### 从源码安装

```bash
# 克隆项目
git clone <repository-url>
cd jacoco_delta

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装项目
pip install -e .
```

### 开发模式安装

```bash
pip install -e ".[dev]"
```

## 使用方法

### 命令行使用

```bash
jacoco-delta --help
```

### 作为库使用

```python
from jacoco_delta.workflow.runner import WorkflowRunner
from jacoco_delta.config import Config

# 创建配置
config = Config(
    app_package="com.example.app",
    app_source_dir="/path/to/source",
    app_classfiles_dir="/path/to/classes",
    report_output_dir="/path/to/output"
)

# 创建运行器
runner = WorkflowRunner(config)

# 运行分析
# result = runner.run_full_analysis(bug_test_cases, correct_test_cases)
```