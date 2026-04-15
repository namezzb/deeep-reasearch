"""
BOSS直聘采集器测试
"""
import pytest

from collectors.boss import BossCollector
from collectors.base import JobData


class TestBossCollector:
    """测试 BOSS直聘采集器"""

    def setup_method(self):
        """每个测试前初始化"""
        self.collector = BossCollector()

    def teardown_method(self):
        """每个测试后清理"""
        self.collector.close()

    def test_platform_name(self):
        """验证平台名称"""
        assert self.collector.platform_name == "boss"

    def test_search_jobs_returns_list(self):
        """验证搜索返回列表类型"""
        # 使用模拟数据测试结构，不实际请求
        jobs = self.collector.search_jobs("Python开发", "北京")
        assert isinstance(jobs, list)

    def test_job_data_structure(self):
        """验证 JobData 数据结构"""
        job = JobData(
            platform="boss",
            job_id="test123",
            title="Python开发工程师",
            company="测试公司",
            salary="20k-35k",
            location="北京·朝阳区",
            experience="1-3年",
            education="本科",
            tags=["五险一金", "弹性工作"],
            description="岗位职责：...",
            recruiter="张三",
            publish_time="3天前发布",
            url="https://www.zhipin.com/job_detail/test123.html",
        )

        assert job.platform == "boss"
        assert job.title == "Python开发工程师"
        assert job.company == "测试公司"
        assert "五险一金" in job.tags
        assert job.to_dict()["platform"] == "boss"

    def test_city_code_conversion(self):
        """验证城市码转换"""
        assert self.collector._get_city_code("北京") == "101010100"
        assert self.collector._get_city_code("上海") == "101020100"
        assert self.collector._get_city_code("未知城市") == "101010100"  # 默认值

    def test_get_job_detail(self):
        """验证获取职位详情"""
        # 使用无效ID测试返回None
        result = self.collector.get_job_detail("invalid_id_xxx")
        assert result is None

    def test_collect_with_config(self):
        """验证配置采集"""
        jobs = self.collector.collect_with_config(
            keywords=["Python"],
            cities=["北京"],
            max_per_source=10
        )
        assert isinstance(jobs, list)

    def test_random_delay(self):
        """验证随机延迟函数存在"""
        import time
        start = time.time()
        self.collector._random_delay(0.1, 0.2)
        elapsed = time.time() - start
        assert 0.05 <= elapsed <= 0.3

    def test_refresh_headers(self):
        """验证刷新请求头"""
        old_ua = self.collector.session.headers.get("User-Agent")
        self.collector._refresh_headers()
        new_ua = self.collector.session.headers.get("User-Agent")
        # 都是有效的 User-Agent
        assert "Mozilla" in new_ua
