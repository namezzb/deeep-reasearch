#!/bin/bash
# DeepResearch 自动开发脚本 v2
# 基于标志位驱动，每次新会话自动校验状态
# 用法: ./auto_dev.sh <迭代次数>

set -e

# ========== 配置 ==========
MAX_ITERATIONS=${1:-10}
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$PROJECT_DIR/auto_dev.log"
STATE_DIR="$PROJECT_DIR/.auto_dev_state"

# 状态文件
CURRENT_FEATURE_FILE="$STATE_DIR/current_feature"
VERIFICATION_FILE="$STATE_DIR/verified_features"
PROGRESS_FILE="$PROJECT_DIR/claude-progress.txt"
FEATURE_FILE="$PROJECT_DIR/feature_list.json"

# Claude Code 会话名
SESSION_PREFIX="auto-dev"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ========== 日志函数 ==========
log() {
    local level=$1
    shift
    local msg="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${msg}" | tee -a "$LOG_FILE"
}
log_info() { log "${BLUE}INFO${NC}" "$@"; }
log_success() { log "${GREEN}OK${NC}" "$@"; }
log_warn() { log "${YELLOW}WARN${NC}" "$@"; }
log_error() { log "${RED}ERROR${NC}" "$@"; }

# ========== 初始化状态目录 ==========
init_state_dir() {
    mkdir -p "$STATE_DIR"
    log_info "状态目录: $STATE_DIR"
}

# ========== 读取当前正在处理的功能 ==========
get_current_feature() {
    if [ -f "$CURRENT_FEATURE_FILE" ]; then
        cat "$CURRENT_FEATURE_FILE"
    fi
}

# ========== 设置当前正在处理的功能 ==========
set_current_feature() {
    echo "$1" > "$CURRENT_FEATURE_FILE"
}

# ========== 清除当前功能 ==========
clear_current_feature() {
    rm -f "$CURRENT_FEATURE_FILE"
}

# ========== 标记功能已校验 ==========
mark_verified() {
    echo "$1:$(date +%s)" >> "$VERIFICATION_FILE"
}

# ========== 检查功能是否已校验 ==========
is_verified() {
    grep -q "^$1:" "$VERIFICATION_FILE" 2>/dev/null
}

# ========== 获取下一个待处理的功能 ==========
get_next_feature() {
    python3 -c "
import json
with open('$FEATURE_FILE', 'r') as f:
    data = json.load(f)
    pending = [f for f in data['features'] if not f.get('passes', False)]
    if pending:
        f = pending[0]
        print(f\"{f['id']}|{f['name']}|{f['description']}\")
" 2>/dev/null
}

# ========== 获取已完成的统计 ==========
get_stats() {
    python3 -c "
import json
with open('$FEATURE_FILE', 'r') as f:
    data = json.load(f)
    total = len(data['features'])
    completed = len([f for f in data['features'] if f.get('passes', False)])
    print(f\"$completed/$total\")
" 2>/dev/null
}

# ========== 验证功能是否真正完成 ==========
verify_feature_complete() {
    local feature_id=$1
    local passes=$(python3 -c "
import json
with open('$FEATURE_FILE', 'r') as f:
    data = json.load(f)
    for f_item in data['features']:
        if f_item['id'] == '$feature_id':
            print('true' if f_item.get('passes', False) else 'false')
            break
" 2>/dev/null)
    [ "$passes" = "true" ]
}

# ========== 运行 Claude Code 处理功能 ==========
run_claude_for_feature() {
    local feature_id=$1
    local feature_name=$2
    local feature_desc=$3
    local iteration=$4
    local session_name="${SESSION_PREFIX}-${feature_id}-${iteration}"

    log_info "=========================================="
    log_info "处理功能: [$feature_id] $feature_name"
    log_info "会话名: $session_name"
    log_info "=========================================="

    # 生成 prompt
    local prompt=$(cat << PROMPT
你是 DeepResearch 项目的自动化开发助手。

## 当前任务
功能ID: $feature_id
功能名称: $feature_name
功能描述: $feature_desc

## 工作流程

### 1. 加载环境
阅读以下文件了解项目结构：
- docs/long-running-agent-harness.md
- feature_list.json
- init.sh
- resume.sh

### 2. 执行测试步骤
从 feature_list.json 中找到 $feature_id 的 test_steps，逐个执行验证。

### 3. 完成开发
如果测试通过：
1. 更新 feature_list.json 中该功能的 passes 字段为 true
2. 追加进度到 claude-progress.txt
3. 提交代码（如果 git 可用）

### 4. 验证
完成所有操作后，运行以下命令验证状态：
- grep '"$feature_id"' feature_list.json | grep passes
- cat claude-progress.txt | tail -5

请开始执行。
PROMPT
)

    log_info "启动 Claude Code..."

    # 记录开始时间
    local start_time=$(date +%s)

    # 执行 Claude Code，使用 --dangerously-skip-permissions 跳过权限确认
    echo "$prompt" | claude --print \
        --dangerously-skip-permissions \
        --no-session-persistence \
        --output-format text \
        --name "$session_name" 2>&1 | tee -a "$LOG_FILE"

    local exit_code=${PIPESTATUS[0]}
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_info "Claude Code 执行完成 (exit: $exit_code, ${duration}s)"

    return $exit_code
}

# ========== 主流程 ==========
main() {
    log_info "=========================================="
    log_info "DeepResearch 自动开发脚本 v2 启动"
    log_info "最大迭代次数: $MAX_ITERATIONS"
    log_info "=========================================="

    # 初始化
    init_state_dir

    # 运行环境初始化
    log_info "运行环境初始化..."
    cd "$PROJECT_DIR"
    if [ -f "init.sh" ]; then
        bash init.sh 2>&1 | tee -a "$LOG_FILE" || true
    fi

    # 显示当前状态
    log_info "当前进度: $(get_stats)"
    if [ -f "resume.sh" ]; then
        bash resume.sh 2>&1 | tee -a "$LOG_FILE" || true
    fi

    local iteration=0
    local total_completed=0

    while [ $iteration -lt $MAX_ITERATIONS ]; do
        iteration=$((iteration + 1))
        log_info ""
        log_info "========== 迭代 #$iteration =========="

        # 步骤1: 检查是否有未完成的上一个任务
        local current_feature=$(get_current_feature)

        if [ -n "$current_feature" ]; then
            log_info "检测到未完成的任务: $current_feature"

            # 检查是否已校验
            if ! is_verified "$current_feature"; then
                log_info "功能 $current_feature 未校验，进行验证..."

                if verify_feature_complete "$current_feature"; then
                    log_success "功能 $current_feature 已验证完成"
                    mark_verified "$current_feature"
                    clear_current_feature
                    continue
                else
                    log_warn "功能 $current_feature 未真正完成，继续处理..."
                    # 从 feature_list 读取详情继续处理
                    local feature_info=$(python3 -c "
import json
with open('$FEATURE_FILE', 'r') as f:
    data = json.load(f)
    for f_item in data['features']:
        if f_item['id'] == '$current_feature':
            print(f\"{f_item['id']}|{f_item['name']}|{f_item['description']}\")
            break
" 2>/dev/null)
                    if [ -n "$feature_info" ]; then
                        run_claude_for_feature "$current_feature" "$(echo "$feature_info" | cut -d'|' -f2)" "$(echo "$feature_info" | cut -d'|' -f3)" "$iteration"
                    fi
                    continue
                fi
            else
                log_info "功能 $current_feature 已校验完成，跳过"
                clear_current_feature
            fi
        fi

        # 步骤2: 获取下一个待处理的功能
        local next_feature=$(get_next_feature)

        if [ -z "$next_feature" ]; then
            log_success "所有功能已完成！"
            break
        fi

        local feature_id=$(echo "$next_feature" | cut -d'|' -f1)
        local feature_name=$(echo "$next_feature" | cut -d'|' -f2)
        local feature_desc=$(echo "$next_feature" | cut -d'|' -f3)

        # 设置当前功能
        set_current_feature "$feature_id"

        # 清理该功能的校验记录（如果有的话，说明要重新验证）
        sed -i '' "/^$feature_id:/d" "$VERIFICATION_FILE" 2>/dev/null || true

        # 运行 Claude Code
        if run_claude_for_feature "$feature_id" "$feature_name" "$feature_desc" "$iteration"; then
            # 检查是否真正完成
            if verify_feature_complete "$feature_id"; then
                log_success "功能 $feature_id 开发完成"
                mark_verified "$feature_id"
                clear_current_feature
                total_completed=$((total_completed + 1))
            else
                log_warn "Claude Code 声称完成但验证失败，将重试"
            fi
        else
            log_warn "Claude Code 执行失败，将重试"
        fi

        # 短暂休息
        sleep 2
    done

    # 输出总结
    log_info ""
    log_info "=========================================="
    log_info "运行完成"
    log_info "总迭代次数: $iteration"
    log_info "成功完成功能数: $total_completed"
    log_info "最终进度: $(get_stats)"
    log_info "=========================================="
}

# ========== 信号处理 ==========
trap 'log_warn "收到中断信号"; exit 130' INT TERM

# 运行
main
