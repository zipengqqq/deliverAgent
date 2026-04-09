import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(log_file: str) -> logging.Logger:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("deliverAgent")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(fmt)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def log_delivery(logger: logging.Logger, company: str, position: str, llm_result: str, status: str):
    logger.info(f"{company} | {position} | LLM:{llm_result} | {status}")


def print_stats(log_file: str):
    if not os.path.exists(log_file):
        print("暂无投递记录")
        return

    total = applied = skipped = failed = 0
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            if "| INFO |" not in line:
                continue
            total += 1
            if "投递成功" in line:
                applied += 1
            elif "跳过" in line or "不匹配" in line:
                skipped += 1
            elif "失败" in line or "ERROR" in line:
                failed += 1

    print(f"===== 投递统计 =====")
    print(f"日志文件 : {log_file}")
    print(f"记录总数 : {total}")
    print(f"投递成功 : {applied}")
    print(f"跳过     : {skipped}")
    print(f"失败     : {failed}")
