"""
采集器基类
定义所有采集器的通用接口和公共功能
"""
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import requests

from config.config_manager import ConfigManager


@dataclass
class JobData:
    """职位数据统一格式"""
    platform: str
    job_id: str
    title: str
    company: str
    salary: str
    location: str
    experience: str = ""
    education: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""
    recruiter: str = ""
    publish_time: str = ""
    url: str = ""
    raw_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "platform": self.platform,
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "salary": self.salary,
            "location": self.location,
            "experience": self.experience,
            "education": self.education,
            "tags": self.tags,
            "description": self.description,
            "recruiter": self.recruiter,
            "publish_time": self.publish_time,
            "url": self.url,
        }


class CollectorBase(ABC):
    """采集器抽象基类"""

    # 常用 User-Agent 列表
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]

    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self) -> None:
        """配置 Session"""
        self.session.headers.update({
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0) -> None:
        """随机延迟"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _refresh_headers(self) -> None:
        """刷新请求头（模拟不同浏览器）"""
        self.session.headers["User-Agent"] = random.choice(self.USER_AGENTS)

    def _get(self, url: str, **kwargs) -> requests.Response:
        """GET 请求（带随机延迟）"""
        self._random_delay()
        self._refresh_headers()
        return self.session.get(url, **kwargs)

    def _post(self, url: str, **kwargs) -> requests.Response:
        """POST 请求（带随机延迟）"""
        self._random_delay()
        self._refresh_headers()
        return self.session.post(url, **kwargs)

    @abstractmethod
    def search_jobs(self, keyword: str, city: str = "北京", **kwargs) -> list[JobData]:
        """
        搜索职位

        Args:
            keyword: 搜索关键词
            city: 城市名称
            **kwargs: 其他参数

        Returns:
            职位数据列表
        """
        pass

    @abstractmethod
    def get_job_detail(self, job_id: str) -> Optional[JobData]:
        """
        获取职位详情

        Args:
            job_id: 职位ID

        Returns:
            职位数据
        """
        pass

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台名称"""
        pass

    def close(self) -> None:
        """关闭会话"""
        self.session.close()
