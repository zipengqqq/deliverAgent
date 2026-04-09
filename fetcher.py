import logging
from dataclasses import dataclass
from typing import Optional
from playwright.sync_api import Page, BrowserContext

from config import Config

# Boss直聘职位列表页的选择器（依据实际 DOM，如页面改版需同步更新）
JOB_LIST_SELECTOR = ".job-list-box .job-card-wrapper"
JOB_TITLE_SELECTOR = ".job-name"
SALARY_SELECTOR = ".salary"
COMPANY_SELECTOR = ".company-name"
LOCATION_SELECTOR = ".job-area"
TAGS_SELECTOR = ".tag-list li"
JD_BODY_SELECTOR = ".job-detail-body"
NEXT_PAGE_SELECTOR = ".pagination-next"
APPLY_BTN_SELECTOR = ".btn-startchat"


@dataclass
class JobItem:
    job_id: str
    title: str
    salary: str
    company: str
    location: str
    tags: list
    jd_text: str
    detail_url: str


class JobFetcher:
    def __init__(self, config: Config, context: BrowserContext):
        self._config = config
        self._context = context
        self._logger = logging.getLogger("deliverAgent")

    def fetch_all(self) -> list[JobItem]:
        page = self._context.new_page()
        jobs: list[JobItem] = []

        try:
            page.goto(self._config.boss_jobs_url, timeout=self._config.page_timeout)
            page.wait_for_load_state("networkidle", timeout=self._config.page_timeout)
            self._apply_filters(page)

            while True:
                page.wait_for_selector(JOB_LIST_SELECTOR, timeout=self._config.page_timeout)
                cards = page.query_selector_all(JOB_LIST_SELECTOR)
                self._logger.info(f"当前页找到 {len(cards)} 个职位卡片")

                for card in cards:
                    job = self._parse_card(card, page)
                    if job:
                        jobs.append(job)

                next_btn = page.query_selector(NEXT_PAGE_SELECTOR)
                if not next_btn or "disabled" in (next_btn.get_attribute("class") or ""):
                    break

                next_btn.click()
                page.wait_for_load_state("networkidle", timeout=self._config.page_timeout)
        finally:
            page.close()

        self._logger.info(f"共抓取职位 {len(jobs)} 个")
        return jobs

    def _apply_filters(self, page: Page):
        # Boss直聘通过 URL query params 实现筛选，直接在 URL 中构造即可
        # 此处通过点击页面筛选项实现薪资、经验等深度筛选（依赖页面 UI）
        # 如页面结构变化，可改为直接拼接 query params
        self._logger.debug("筛选条件已通过 URL 参数传入，跳过 UI 筛选步骤")

    def _parse_card(self, card, list_page: Page) -> Optional[JobItem]:
        try:
            title_el = card.query_selector(JOB_TITLE_SELECTOR)
            title = title_el.inner_text().strip() if title_el else ""

            salary_el = card.query_selector(SALARY_SELECTOR)
            salary = salary_el.inner_text().strip() if salary_el else ""

            company_el = card.query_selector(COMPANY_SELECTOR)
            company = company_el.inner_text().strip() if company_el else ""

            location_el = card.query_selector(LOCATION_SELECTOR)
            location = location_el.inner_text().strip() if location_el else ""

            tag_els = card.query_selector_all(TAGS_SELECTOR)
            tags = [t.inner_text().strip() for t in tag_els]

            # 获取详情链接
            link_el = card.query_selector("a")
            href = link_el.get_attribute("href") if link_el else ""
            detail_url = f"https://www.zhipin.com{href}" if href and href.startswith("/") else href
            job_id = href.split("/")[-1].split(".")[0] if href else ""

            # 打开详情页获取完整 JD
            jd_text = self._fetch_jd(detail_url, list_page)

            return JobItem(
                job_id=job_id,
                title=title,
                salary=salary,
                company=company,
                location=location,
                tags=tags,
                jd_text=jd_text,
                detail_url=detail_url,
            )
        except Exception as e:
            self._logger.warning(f"解析职位卡片失败：{e}")
            return None

    def _fetch_jd(self, url: str, list_page: Page) -> str:
        if not url:
            return ""
        detail_page = self._context.new_page()
        try:
            detail_page.goto(url, timeout=self._config.page_timeout)
            detail_page.wait_for_load_state("networkidle", timeout=self._config.page_timeout)
            body_el = detail_page.query_selector(JD_BODY_SELECTOR)
            return body_el.inner_text().strip() if body_el else ""
        except Exception as e:
            self._logger.warning(f"获取 JD 详情失败 [{url}]：{e}")
            return ""
        finally:
            detail_page.close()
