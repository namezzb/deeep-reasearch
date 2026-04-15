"""
BOSS直聘采集器
抓取 BOSS直聘平台职位信息

BOSS直聘网站结构分析：
- 搜索页面: https://www.zhipin.com/web/geip/search
- 职位详情: https://www.zhipin.com/job_detail/{job_id}.html
- 搜索API: https://www.zhipin.com/wapi/zpgeek/search/job.json
"""
import hashlib
import json
import re
from typing import Optional

from bs4 import BeautifulSoup

from collectors.base import CollectorBase, JobData


class BossCollector(CollectorBase):
    """BOSS直聘采集器"""

    BASE_URL = "https://www.zhipin.com"
    SEARCH_API = "https://www.zhipin.com/wapi/zpgeek/search/job.json"

    def __init__(self, config=None):
        super().__init__(config)
        self.cookies = {}  # BOSS需要登录，后续扩展

    @property
    def platform_name(self) -> str:
        return "boss"

    def search_jobs(self, keyword: str, city: str = "北京", page: int = 1,
                    salary_range: str = "", experience: str = "", **kwargs) -> list[JobData]:
        """
        搜索BOSS直聘职位

        Args:
            keyword: 搜索关键词
            city: 城市名称（需转换为城市码）
            page: 页码
            salary_range: 薪资范围，如 "20000,35000"
            experience: 经验要求，如 "1-3年"
            **kwargs: 其他参数

        Returns:
            职位数据列表
        """
        jobs = []

        # 城市码映射（简化版）
        city_code = self._get_city_code(city)

        # 构建请求参数
        params = {
            "query": keyword,
            "cityCode": city_code,
            "page": page,
            "pageSize": 15,
        }

        if salary_range:
            params["salaryRange"] = salary_range
        if experience:
            params["workExperience"] = experience

        try:
            # 尝试API请求
            response = self._get(self.SEARCH_API, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("zpData"):
                    job_list = data["zpData"].get("jobList", [])
                    for job in job_list:
                        job_data = self._parse_job_item(job)
                        jobs.append(job_data)
        except Exception as e:
            # API失败时返回空列表（避免实际请求）
            pass

        return jobs

    def get_job_detail(self, job_id: str) -> Optional[JobData]:
        """
        获取BOSS职位详情

        Args:
            job_id: 职位ID

        Returns:
            职位详情数据
        """
        url = f"{self.BASE_URL}/job_detail/{job_id}.html"

        try:
            response = self._get(url)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # 解析详情页面
            title = self._extract_text(soup, ".job-title")
            # 如果标题为空，说明页面无效
            if not title:
                return None

            job_data = JobData(
                platform=self.platform_name,
                job_id=job_id,
                title=title,
                company=self._extract_text(soup, ".company-name"),
                salary=self._extract_text(soup, ".salary"),
                location=self._extract_text(soup, ".location-name"),
                experience=self._extract_text(soup, ".experience"),
                education=self._extract_text(soup, ".education"),
                description=self._extract_description(soup),
                tags=self._extract_tags(soup),
                url=url,
            )
            return job_data
        except Exception:
            return None

    def _parse_job_item(self, job: dict) -> JobData:
        """
        解析职位列表项

        Args:
            job: 职位字典

        Returns:
            JobData对象
        """
        # 生成唯一ID
        job_id_str = f"{self.platform_name}_{job.get('jobId', '')}"
        job_id = hashlib.md5(job_id_str.encode()).hexdigest()[:12]

        # 解析薪资
        salary_text = job.get("salaryDesc", "")

        # 解析地点
        location_text = job.get("areaStr", "")

        # 解析经验学历
        job_labels = job.get("jobLabels", [])
        experience = ""
        education = ""
        for label in job_labels:
            if "年" in label:
                experience = label
            elif label in ["初中及以下", "高中", "大专", "本科", "硕士", "博士"]:
                education = label

        return JobData(
            platform=self.platform_name,
            job_id=job_id,
            job_id_original=job.get("jobId", ""),
            title=job.get("jobName", ""),
            company=job.get("brandName", ""),
            salary=salary_text,
            location=location_text,
            experience=experience,
            education=education,
            tags=job.get("skillTags", []),
            description=job.get("postDescription", ""),
            recruiter=job.get("recruiterName", ""),
            publish_time=job.get("lastLoginTime", ""),
            url=f"{self.BASE_URL}/job_detail/{job.get('jobId', '')}.html",
            raw_data=job,
        )

    def _extract_text(self, soup: BeautifulSoup, selector: str) -> str:
        """提取文本"""
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取职位描述"""
        desc_element = soup.select_one(".job-detail-box")
        if desc_element:
            return desc_element.get_text(strip=True)
        return ""

    def _extract_tags(self, soup: BeautifulSoup) -> list[str]:
        """提取福利标签"""
        tags = []
        tag_elements = soup.select(".tag-list .tag")
        for tag in tag_elements:
            text = tag.get_text(strip=True)
            if text:
                tags.append(text)
        return tags

    def _get_city_code(self, city: str) -> str:
        """城市名转城市码（简化版）"""
        city_map = {
            "北京": "101010100",
            "上海": "101020100",
            "深圳": "101280600",
            "广州": "101280100",
            "杭州": "101210100",
            "成都": "101270100",
            "武汉": "101200100",
            "西安": "101110100",
            "南京": "101190100",
            "重庆": "101040100",
            "苏州": "101190400",
            "天津": "101030000",
            "长沙": "101250100",
            "郑州": "101180100",
            "东莞": "101280500",
            "青岛": "101120200",
            "沈阳": "101070100",
            "宁波": "101210400",
            "昆明": "101290100",
            "大连": "101070200",
        }
        return city_map.get(city, "101010100")

    def collect_with_config(self, keywords: list[str], cities: list[str],
                            salary_range: str = "", max_per_source: int = 50) -> list[JobData]:
        """
        使用配置进行采集

        Args:
            keywords: 关键词列表
            cities: 城市列表
            salary_range: 薪资范围
            max_per_source: 每来源最大采集数

        Returns:
            采集到的职位列表
        """
        all_jobs = []

        for keyword in keywords:
            for city in cities:
                jobs = self.search_jobs(
                    keyword=keyword,
                    city=city,
                    salary_range=salary_range
                )
                all_jobs.extend(jobs)

                # 限制采集数量
                if len(all_jobs) >= max_per_source:
                    return all_jobs[:max_per_source]

        return all_jobs
