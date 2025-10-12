#!/bin/bash
# GitHub Sentinel 守护进程管理脚本
# 用于管理DaemonProcess守护进程的启动、停止、重启和状态查看

# 设置脚本目录和项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
DAEMON_SCRIPT="$PROJECT_ROOT/src/daemon_process.py"
PID_FILE="$PROJECT_ROOT/run/github_sentinel.pid"
LOG_FILE="$PROJECT_ROOT/logs/daemon.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python环境
check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        if ! command -v python >/dev/null 2>&1; then
            print_error "Python未安装或不在PATH中"
            exit 1
        else
            PYTHON_CMD="python"
        fi
    else
        PYTHON_CMD="python3"
    fi
}

# 检查守护进程脚本是否存在
check_daemon_script() {
    if [ ! -f "$DAEMON_SCRIPT" ]; then
        print_error "守护进程脚本不存在: $DAEMON_SCRIPT"
        exit 1
    fi
}

# 启动守护进程
start_daemon() {
    print_info "启动 GitHub Sentinel 守护进程..."

    # 检查是否已在运行
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            print_warning "守护进程已在运行，PID: $PID"
            return 1
        fi
    fi

    # 创建必要的目录
    mkdir -p "$(dirname "$PID_FILE")"
    mkdir -p "$(dirname "$LOG_FILE")"

    # 启动守护进程
    cd "$PROJECT_ROOT"
    if [ "$1" = "--foreground" ] || [ "$1" = "-f" ]; then
        print_info "在前台模式启动守护进程..."
        $PYTHON_CMD "$DAEMON_SCRIPT" start --foreground
    else
        print_info "在后台模式启动守护进程..."
        $PYTHON_CMD "$DAEMON_SCRIPT" start

        # 检查启动是否成功
        sleep 2
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE" 2>/dev/null)
            if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
                print_success "守护进程启动成功，PID: $PID"
                print_info "PID文件: $PID_FILE"
                print_info "日志文件: $LOG_FILE"
            else
                print_error "守护进程启动失败"
                return 1
            fi
        else
            print_error "守护进程启动失败，未找到PID文件"
            return 1
        fi
    fi
}

# 停止守护进程
stop_daemon() {
    print_info "停止 GitHub Sentinel 守护进程..."

    cd "$PROJECT_ROOT"
    $PYTHON_CMD "$DAEMON_SCRIPT" stop

    if [ $? -eq 0 ]; then
        print_success "守护进程已停止"
    else
        print_error "停止守护进程失败"
        return 1
    fi
}

# 重启守护进程
restart_daemon() {
    print_info "重启 GitHub Sentinel 守护进程..."

    cd "$PROJECT_ROOT"
    $PYTHON_CMD "$DAEMON_SCRIPT" restart

    if [ $? -eq 0 ]; then
        print_success "守护进程重启成功"
        # 显示新的PID
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE" 2>/dev/null)
            if [ -n "$PID" ]; then
                print_info "新的PID: $PID"
            fi
        fi
    else
        print_error "重启守护进程失败"
        return 1
    fi
}

# 查看守护进程状态
status_daemon() {
    print_info "查看 GitHub Sentinel 守护进程状态..."
    echo "=================================================="

    cd "$PROJECT_ROOT"
    $PYTHON_CMD "$DAEMON_SCRIPT" status

    echo "=================================================="
    print_info "PID文件: $PID_FILE"
    print_info "日志文件: $LOG_FILE"

    # 显示最近的日志
    if [ -f "$LOG_FILE" ]; then
        echo ""
        print_info "最近10行日志:"
        echo "--------------------------------------------------"
        tail -n 10 "$LOG_FILE" 2>/dev/null || echo "无法读取日志文件"
    else
        print_warning "日志文件不存在"
    fi
}

# 查看日志
show_logs() {
    local lines=${1:-50}

    if [ -f "$LOG_FILE" ]; then
        print_info "显示最近 $lines 行日志:"
        echo "=================================================="
        tail -n "$lines" "$LOG_FILE"
    else
        print_error "日志文件不存在: $LOG_FILE"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "GitHub Sentinel 守护进程管理脚本"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs} [选项]"
    echo ""
    echo "命令:"
    echo "  start           启动守护进程"
    echo "  start -f        在前台模式启动守护进程"
    echo "  stop            停止守护进程"
    echo "  restart         重启守护进程"
    echo "  status          查看守护进程状态"
    echo "  logs [N]        显示最近N行日志（默认50行）"
    echo ""
    echo "示例:"
    echo "  $0 start                # 启��守护进程"
    echo "  $0 start --foreground   # 前台模式启动"
    echo "  $0 status               # 查看状态"
    echo "  $0 logs 100             # 查看最近100行日志"
    echo ""
}

# 主函数
main() {
    # 检查环境
    check_python
    check_daemon_script

    # 解析命令
    case "$1" in
        start)
            start_daemon "$2"
            ;;
        stop)
            stop_daemon
            ;;
        restart)
            restart_daemon
            ;;
        status)
            status_daemon
            ;;
        logs)
            show_logs "$2"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "无效的命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
