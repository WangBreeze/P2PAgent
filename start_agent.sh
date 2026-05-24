#!/bin/bash
# P2P Agent 启动脚本 (macOS/Linux)

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 检查参数
if [ -z "$1" ]; then
    echo "用法: ./start_agent.sh <Agent名称> [端口] [连接地址]"
    echo ""
    echo "示例:"
    echo "  ./start_agent.sh Alice"
    echo "  ./start_agent.sh Alice 9001"
    echo "  ./start_agent.sh Bob 9002 192.168.1.100:9000"
    exit 1
fi

NAME=$1
PORT=${2:-9000}
CONNECT=$3

# 构建命令
CMD="python p2p_agent.py --name $NAME --port $PORT"

if [ -n "$CONNECT" ]; then
    CMD="$CMD --connect $CONNECT --no-discover"
fi

echo "🚀 启动 P2P Agent: $NAME"
echo "   端口: $PORT"
if [ -n "$CONNECT" ]; then
    echo "   连接到: $CONNECT"
fi
echo ""

# 启动
exec $CMD
