import sys
from playwright.sync_api import sync_playwright

from config import load_config
from agent import DeliverAgent
from logger import setup_logger, print_stats


def main():
    config = load_config()
    logger = setup_logger(config.log_file)

    logger.info("deliverAgent 启动")
    logger.info(
        f"筛选条件 — 城市:{config.filter_city} "
        f"薪资:{config.filter_salary_min}-{config.filter_salary_max}K "
        f"关键词:{','.join(config.filter_keywords)}"
    )

    with sync_playwright() as pw:
        browser_launcher = getattr(pw, config.browser_type)
        browser = browser_launcher.launch(headless=config.headless)

        context = browser.new_context()
        # 注入 Cookie
        if config.boss_cookie:
            cookies = _parse_cookie_string(config.boss_cookie)
            context.add_cookies(cookies)

        try:
            agent = DeliverAgent(config, context)
            agent.run()
        finally:
            context.close()
            browser.close()

    logger.info("deliverAgent 运行结束")


def _parse_cookie_string(cookie_str: str) -> list[dict]:
    """将浏览器复制的 Cookie 字符串解析为 Playwright 所需的 cookie 列表。"""
    cookies = []
    for part in cookie_str.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            name, _, value = part.partition("=")
            cookies.append(
                {
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".zhipin.com",
                    "path": "/",
                }
            )
    return cookies


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        from config import load_config as _lc
        _cfg = _lc()
        print_stats(_cfg.log_file)
    else:
        main()
