import logging
import random
import time
from playwright.sync_api import BrowserContext

from config import Config
from fetcher import JobFetcher, JobItem, APPLY_BTN_SELECTOR
from matcher import JDMatcher
from logger import log_delivery

CHAT_INPUT_SELECTOR = ".chat-input textarea, .input-area textarea"
CHAT_SEND_SELECTOR = ".chat-input .btn-send, .input-area .btn-send"


class DeliverAgent:
    def __init__(self, config: Config, context: BrowserContext):
        self._config = config
        self._context = context
        self._logger = logging.getLogger("deliverAgent")
        self._fetcher = JobFetcher(config, context)
        self._matcher = JDMatcher(config)
        self._daily_count = 0

    def run(self):
        self._logger.info("开始抓取职位列表...")
        jobs = self._fetcher.fetch_all()

        self._logger.info(f"共获取 {len(jobs)} 个职位，开始逐一匹配并投递")
        for job in jobs:
            if self._daily_count >= self._config.max_daily_apply:
                self._logger.info(f"已达每日投递上限 {self._config.max_daily_apply}，停止投递")
                break

            self._process_job(job)

        self._logger.info(f"本次运行共投递 {self._daily_count} 个职位")

    def _process_job(self, job: JobItem):
        self._logger.info(f"正在处理：{job.company} - {job.title}（{job.salary}）")

        matched = self._matcher.is_match(job.title, job.jd_text)
        if not matched:
            self._logger.info(f"  → 跳过（LLM 判断：不匹配）")
            log_delivery(self._logger, job.company, job.title, "不匹配", "跳过")
            return

        self._logger.info(f"  → LLM 判断匹配，准备投递")
        success = self._apply(job)

        status = "投递成功" if success else "投递失败"
        log_delivery(self._logger, job.company, job.title, "匹配", status)

        if success:
            self._daily_count += 1
            delay = random.uniform(self._config.apply_delay_min, self._config.apply_delay_max)
            self._logger.debug(f"  → 等待 {delay:.1f}s 后继续")
            time.sleep(delay)

    def _apply(self, job: JobItem) -> bool:
        page = self._context.new_page()
        try:
            page.goto(job.detail_url, timeout=self._config.page_timeout)
            page.wait_for_load_state("networkidle", timeout=self._config.page_timeout)

            apply_btn = page.query_selector(APPLY_BTN_SELECTOR)
            if not apply_btn:
                self._logger.warning(f"  → 未找到「立即沟通」按钮，跳过")
                return False

            apply_btn.click()
            page.wait_for_timeout(2000)

            if self._config.auto_greet:
                self._send_greet(page, job)

            return True
        except Exception as e:
            self._logger.error(f"  → 投递异常 [{job.title}]：{e}")
            return False
        finally:
            page.close()

    def _send_greet(self, page, job: JobItem):
        message = self._config.greet_message.format(
            position=job.title, company=job.company
        )
        try:
            input_el = page.query_selector(CHAT_INPUT_SELECTOR)
            send_btn = page.query_selector(CHAT_SEND_SELECTOR)
            if input_el and send_btn:
                input_el.fill(message)
                page.wait_for_timeout(500)
                send_btn.click()
                self._logger.debug(f"  → 打招呼消息已发送")
            else:
                self._logger.warning("  → 未找到对话输入框，打招呼跳过")
        except Exception as e:
            self._logger.warning(f"  → 发送打招呼失败：{e}")
