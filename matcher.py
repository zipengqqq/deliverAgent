import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from config import Config

SYSTEM_PROMPT = (
    "你是一位专业的求职助手。请根据候选人背景和职位描述，判断该职位是否值得投递。\n"
    '必须严格返回如下 JSON，不得包含任何其他内容：\n'
    '{{"result": "匹配"}} 或 {{"result": "不匹配"}}'
)

HUMAN_PROMPT = (
    "候选人背景：{candidate_profile}\n\n"
    "职位名称：{job_title}\n"
    "职位描述：{jd_text}\n\n"
    "请判断是否匹配。"
)


class JDMatcher:
    def __init__(self, config: Config):
        self._config = config
        self._logger = logging.getLogger("deliverAgent")

        llm = ChatOpenAI(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            model=config.llm_model,
            model_kwargs={"response_format": {"type": "json_object"}},
            temperature=0,
        )

        prompt = ChatPromptTemplate.from_messages(
            [("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT)]
        )

        self._chain = prompt | llm | JsonOutputParser()

    def is_match(self, job_title: str, jd_text: str) -> bool:
        try:
            output = self._chain.invoke(
                {
                    "candidate_profile": self._config.candidate_profile,
                    "job_title": job_title,
                    "jd_text": jd_text,
                }
            )
            result = output.get("result", "不匹配")
            matched = result == "匹配"
            self._logger.debug(f"LLM 判断 [{job_title}]：{result}")
            return matched
        except Exception as e:
            self._logger.warning(f"LLM 调用失败 [{job_title}]：{e}，默认跳过")
            return False
