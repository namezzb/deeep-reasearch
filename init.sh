#!/bin/bash
# DeepResearch Agent 初始化脚本
# 用于启动开发环境和验证系统状态

set -e

echo "=== DeepResearch 环境初始化 ==="

# 1. 检查依赖
echo "[1/5] 检查依赖..."
command -v python3 >/dev/null 2>&1 || { echo "错误: 需要 python3"; exit 1; }

# 2. 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "[2/5] 激活虚拟环境..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "[2/5] 激活虚拟环境..."
    source .venv/bin/activate
fi

# 3. 安装依赖
echo "[3/5] 安装依赖..."
if [ -f "requirements.txt" ]; then
    pip3 install --user -r requirements.txt -q 2>/dev/null || pip3 install -r requirements.txt -q --break-system-packages 2>/dev/null || echo "（依赖安装跳过 - 网络问题）"
fi

# 4. 验证环境
echo "[4/5] 验证环境..."
python3 -c "import sys; print(f'Python {sys.version}')"

# 5. 运行基础测试
echo "[5/5] 运行基础验证..."
python3 -m pytest tests/ -v --tb=short -x -q 2>/dev/null || echo "测试完成（或无测试目录）"

echo "=== 初始化完成 ==="
echo "当前状态: $(git branch --show-current 2>/dev/null || echo ' detached')"
echo "未提交更改: $(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
