#!/bin/bash
# P2P Agent 安装脚本
# 将可执行文件安装到系统路径

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BINARY="$SCRIPT_DIR/dist/p2p-agent"

# 检查可执行文件是否存在
if [ ! -f "$BINARY" ]; then
    echo "❌ 未找到可执行文件，请先运行打包命令:"
    echo "   make build"
    echo "   或"
    echo "   python build.py"
    exit 1
fi

# 检测操作系统
OS="$(uname -s)"
case "$OS" in
    Linux*)     INSTALL_DIR="$HOME/.local/bin";;
    Darwin*)    INSTALL_DIR="$HOME/.local/bin";;
    MINGW*|MSYS*|CYGWIN*)  INSTALL_DIR="$HOME/bin";;
    *)          echo "❌ 不支持的操作系统: $OS"; exit 1;;
esac

# 创建安装目录
mkdir -p "$INSTALL_DIR"

# 复制可执行文件
echo "📦 安装 P2P Agent 到 $INSTALL_DIR..."
cp "$BINARY" "$INSTALL_DIR/p2p-agent"
chmod +x "$INSTALL_DIR/p2p-agent"

# 检查 PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "⚠️  请将以下目录添加到 PATH:"
    echo "   $INSTALL_DIR"
    echo ""
    echo "   添加方法 (bash/zsh):"
    echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    echo "   source ~/.bashrc"
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用方法:"
echo "  p2p-agent --name Alice"
echo "  p2p-agent --name Bob --connect 192.168.1.100:9000"
echo ""
echo "卸载方法:"
echo "  rm $INSTALL_DIR/p2p-agent"
