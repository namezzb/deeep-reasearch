"""
招聘信息采集器模块
支持多平台职位信息采集
"""
from collectors.base import CollectorBase, JobData
from collectors.boss import BossCollector

__all__ = [
    "CollectorBase",
    "JobData",
    "BossCollector",
]
