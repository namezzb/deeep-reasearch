#!/bin/bash
# DeepResearch Agent 进入状态脚本
# 每次会话开始时执行，恢复工作状态

set -e

echo "=== 进入工作状态 ==="

# 1. 确认工作目录
echo "[1/6] 工作目录: $(pwd)"

# 2. 读取进度文件
if [ -f "claude-progress.txt" ]; then
    echo "[2/6] === 近期进度 ==="
    tail -20 claude-progress.txt
else
    echo "[2/6] 无进度文件"
fi

# 3. 读取 git 历史
echo "[3/6] === 最近提交 ==="
git log --oneline -10 2>/dev/null || echo "（暂无提交历史）"

# 4. 检查功能列表
if [ -f "feature_list.json" ]; then
    echo "[4/6] === 功能状态 ==="
    TOTAL=$(grep -c '"passes":' feature_list.json || echo 0)
    PASSED=$(grep -c '"passes": true' feature_list.json || echo 0)
    echo "已完成: $PASSED / $TOTAL"
else
    echo "[4/6] 无功能列表"
fi

# 5. 检查未提交更改
if [ -d ".git" ]; then
    echo "[5/6] === 更改统计 ==="
    git status --porcelain | head -20
fi

# 6. 初始化环境
echo "[6/6] 初始化环境..."
bash init.sh

echo "=== 准备就绪 ==="
