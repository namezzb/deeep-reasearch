"""
进度追踪模块
实现 Claude 会话间状态持久化
"""
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ProgressEntry:
    """进度条目"""
    timestamp: str
    feature_id: str
    description: str
    feature_id_display: str  # 格式化显示 [FEATURE-ID]


class ProgressTracker:
    """
    进度追踪器
    支持会话间状态持久化
    """

    DEFAULT_PROGRESS_FILE = "claude-progress.txt"

    def __init__(self, progress_file: Optional[str] = None) -> None:
        self.progress_file = progress_file or self.DEFAULT_PROGRESS_FILE

    def initialize(self) -> None:
        """初始化进度文件"""
        if not os.path.exists(self.progress_file):
            Path(self.progress_file).touch()

    def _format_timestamp(self) -> str:
        """生成时间戳 [YYYY-MM-DD HH:MM]"""
        return datetime.now().strftime("[%Y-%m-%d %H:%M]")

    def _format_feature_id(self, feature_id: str) -> str:
        """格式化功能ID [FEATURE-ID]"""
        return f"[{feature_id}]"

    def write_progress(self, feature_id: str, description: str) -> None:
        """
        写入进度条目

        Args:
            feature_id: 功能ID (如 core-001)
            description: 进度描述
        """
        self.initialize()

        timestamp = self._format_timestamp()
        feature_display = self._format_feature_id(feature_id)
        line = f"{timestamp} {feature_display} {description}\n"

        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(line)

    def read_progress(self) -> list[ProgressEntry]:
        """
        读取所有进度条目

        Returns:
            进度条目列表
        """
        if not os.path.exists(self.progress_file):
            return []

        entries: list[ProgressEntry] = []
        # 时间戳格式: [YYYY-MM-DD HH:MM] [FEATURE-ID] description
        pattern = re.compile(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] \[([^\]]+)\] (.+)")

        with open(self.progress_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                match = pattern.match(line)
                if match:
                    entries.append(ProgressEntry(
                        timestamp=match.group(1),
                        feature_id=match.group(2),
                        description=match.group(3),
                        feature_id_display=match.group(2)
                    ))

        return entries

    def get_last_entry(self) -> Optional[ProgressEntry]:
        """获取最后一条进度记录"""
        entries = self.read_progress()
        return entries[-1] if entries else None

    def get_entries_by_feature(self, feature_id: str) -> list[ProgressEntry]:
        """获取指定功能的进度记录"""
        return [e for e in self.read_progress() if e.feature_id == feature_id]


def create_default_tracker() -> ProgressTracker:
    """创建默认进度追踪器"""
    return ProgressTracker(progress_file="claude-progress.txt")
