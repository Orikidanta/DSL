# logger.py
import logging
import sys

def setup_logger(name="bot", level=logging.INFO):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # 避免重复添加 handler

    logger.setLevel(level)

    # 创建控制台处理器
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # 设置格式：时间 | 级别 | 消息
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger