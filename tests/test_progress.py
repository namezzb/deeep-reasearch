"""
进度追踪系统测试
测试会话间状态持久化功能
"""
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest


# 测试进度追踪模块
def test_progress_file_creation():
    """测试创建 claude-progress.txt"""
    from progress_tracker import ProgressTracker

    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = ProgressTracker(progress_file=os.path.join(tmpdir, "test-progress.txt"))
        assert not os.path.exists(tracker.progress_file)
        tracker.initialize()
        assert os.path.exists(tracker.progress_file)


def test_progress_write():
    """测试进度写入"""
    from progress_tracker import ProgressTracker

    with tempfile.TemporaryDirectory() as tmpdir:
        progress_file = os.path.join(tmpdir, "test-progress.txt")
        tracker = ProgressTracker(progress_file=progress_file)
        tracker.initialize()

        tracker.write_progress("core-001", "完成项目初始化")
        tracker.write_progress("core-002", "实现进度追踪系统")

        with open(progress_file, "r") as f:
            content = f.read()
            assert "core-001" in content
            assert "core-002" in content
            assert "完成项目初始化" in content


def test_progress_read():
    """测试进度读取"""
    from progress_tracker import ProgressTracker

    with tempfile.TemporaryDirectory() as tmpdir:
        progress_file = os.path.join(tmpdir, "test-progress.txt")
        tracker = ProgressTracker(progress_file=progress_file)
        tracker.initialize()

        tracker.write_progress("core-001", "完成项目初始化")

        entries = tracker.read_progress()
        assert len(entries) == 1
        assert entries[0].feature_id == "core-001"
        assert entries[0].description == "完成项目初始化"


def test_multi_session_recovery():
    """测试多会话恢复"""
    from progress_tracker import ProgressTracker

    with tempfile.TemporaryDirectory() as tmpdir:
        progress_file = os.path.join(tmpdir, "test-progress.txt")

        # 会话1: 写入进度
        tracker1 = ProgressTracker(progress_file=progress_file)
        tracker1.initialize()
        tracker1.write_progress("core-001", "完成项目初始化")
        tracker1.write_progress("core-002", "开始实现进度追踪")

        # 会话2: 读取进度（模拟新会话恢复）
        tracker2 = ProgressTracker(progress_file=progress_file)
        entries = tracker2.read_progress()

        assert len(entries) == 2
        assert any(e.feature_id == "core-001" for e in entries)
        assert any(e.feature_id == "core-002" for e in entries)


def test_progress_timestamp_format():
    """测试时间戳格式"""
    from progress_tracker import ProgressTracker

    with tempfile.TemporaryDirectory() as tmpdir:
        progress_file = os.path.join(tmpdir, "test-progress.txt")
        tracker = ProgressTracker(progress_file=progress_file)
        tracker.initialize()

        tracker.write_progress("core-001", "测试时间戳")

        entries = tracker.read_progress()
        assert len(entries) == 1
        # 验证时间戳格式 YYYY-MM-DD HH:MM (存储时不带方括号)
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", entries[0].timestamp)


def test_progress_feature_id_format():
    """测试功能ID格式"""
    from progress_tracker import ProgressTracker

    with tempfile.TemporaryDirectory() as tmpdir:
        progress_file = os.path.join(tmpdir, "test-progress.txt")
        tracker = ProgressTracker(progress_file=progress_file)
        tracker.initialize()

        tracker.write_progress("core-002", "测试功能ID")

        entries = tracker.read_progress()
        assert len(entries) == 1
        # 验证功能ID格式 FEATURE-ID (存储时不带方括号)
        import re
        assert re.match(r"[^:]+", entries[0].feature_id_display)
