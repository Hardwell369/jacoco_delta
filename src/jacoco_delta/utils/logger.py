import structlog
import logging
import sys
import os

def configure_logger(log_file_dir: str, log_file_name: str = "app.log"):
    """
    配置structlog记录器
    
    Args:
        log_file_dir: 日志文件目录
        log_file_name: 日志文件名, 默认为"app.log"
    """
    # 确保日志目录存在
    log_file_path = os.path.join(log_file_dir, log_file_name)
    os.makedirs(log_file_dir, exist_ok=True)
    
    # 配置标准logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # 配置structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    # 获取根记录器并添加文件处理器
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    return structlog.get_logger()

def get_logger(name: str):
    """
    获取带有特定名称的记录器
    
    Args:
        name: 记录器名称（通常是模块名）
        
    Returns:
        structlog记录器实例
    """
    return structlog.get_logger(name)