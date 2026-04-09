import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise ValueError(f"必填配置项 {key} 未设置，请检查 .env 文件")
    return value


def _int_env(key: str, default: int) -> int:
    raw = os.getenv(key, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"配置项 {key} 必须为整数，当前值：{raw!r}")


def _bool_env(key: str, default: bool) -> bool:
    raw = os.getenv(key, str(default)).strip().lower()
    return raw in ("true", "1", "yes")


@dataclass
class Config:
    # Boss直聘
    boss_cookie: str
    boss_jobs_url: str

    # 筛选条件
    filter_city: str
    filter_job_type: str
    filter_salary_min: int
    filter_salary_max: int
    filter_experience: str
    filter_education: str
    filter_industry: list
    filter_company_scale: str
    filter_keywords: list

    # LLM
    candidate_profile: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str

    # 投递行为
    max_daily_apply: int
    apply_delay_min: int
    apply_delay_max: int
    auto_greet: bool
    greet_message: str

    # Playwright
    headless: bool
    browser_type: str
    page_timeout: int

    # 日志
    log_file: str


def load_config() -> Config:
    boss_cookie = _require("BOSS_COOKIE")
    llm_api_key = _require("LLM_API_KEY")
    candidate_profile = _require("CANDIDATE_PROFILE")

    salary_min = _int_env("FILTER_SALARY_MIN", 0)
    salary_max = _int_env("FILTER_SALARY_MAX", 999)
    if salary_min > salary_max:
        raise ValueError(
            f"FILTER_SALARY_MIN ({salary_min}) 不能大于 FILTER_SALARY_MAX ({salary_max})"
        )

    delay_min = _int_env("APPLY_DELAY_MIN", 3)
    delay_max = _int_env("APPLY_DELAY_MAX", 8)
    if delay_min > delay_max:
        raise ValueError(
            f"APPLY_DELAY_MIN ({delay_min}) 不能大于 APPLY_DELAY_MAX ({delay_max})"
        )

    raw_industry = os.getenv("FILTER_INDUSTRY", "").strip()
    industry = [i.strip() for i in raw_industry.split(",") if i.strip()]

    raw_keywords = os.getenv("FILTER_KEYWORDS", "").strip()
    keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]

    return Config(
        boss_cookie=boss_cookie,
        boss_jobs_url=os.getenv(
            "BOSS_JOBS_URL", "https://www.zhipin.com/web/geek/jobs?ka=header-jobs"
        ),
        filter_city=os.getenv("FILTER_CITY", "").strip(),
        filter_job_type=os.getenv("FILTER_JOB_TYPE", "全职").strip(),
        filter_salary_min=salary_min,
        filter_salary_max=salary_max,
        filter_experience=os.getenv("FILTER_EXPERIENCE", "不限").strip(),
        filter_education=os.getenv("FILTER_EDUCATION", "不限").strip(),
        filter_industry=industry,
        filter_company_scale=os.getenv("FILTER_COMPANY_SCALE", "").strip(),
        filter_keywords=keywords,
        candidate_profile=candidate_profile,
        llm_api_key=llm_api_key,
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1").strip(),
        llm_model=os.getenv("LLM_MODEL", "deepseek-chat").strip(),
        max_daily_apply=_int_env("MAX_DAILY_APPLY", 50),
        apply_delay_min=delay_min,
        apply_delay_max=delay_max,
        auto_greet=_bool_env("AUTO_GREET", True),
        greet_message=os.getenv(
            "GREET_MESSAGE",
            "您好，我对贵公司的{position}职位很感兴趣，期待进一步沟通！",
        ),
        headless=_bool_env("HEADLESS", True),
        browser_type=os.getenv("BROWSER_TYPE", "chromium").strip(),
        page_timeout=_int_env("PAGE_TIMEOUT", 30000),
        log_file=os.getenv("LOG_FILE", "./logs/deliver.log").strip(),
    )
