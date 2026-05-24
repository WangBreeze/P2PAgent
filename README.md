# P2P Agent - 去中心化通信系统

支持 **Windows、macOS、Linux** 的去中心化点对点通信系统。

## ✨ 特点

- 🌐 **跨平台** - 支持 Windows、macOS、Linux
- 🔗 **无中心服务器** - 每个节点都是平等的
- 🔍 **自动发现** - UDP 广播自动发现局域网内的其他 Agent
- 🔌 **手动连接** - 支持通过 IP 连接跨网络的 Agent
- 💬 **实时聊天** - WebSocket 双向通信
- 📁 **文件传输** - HTTP 点对点文件传输

## 🚀 快速开始

### 方法 1: 使用启动脚本（推荐）

**macOS/Linux:**
```bash
# 添加执行权限
chmod +x start_agent.sh

# 启动 Agent
./start_agent.sh Alice
./start_agent.sh Alice 9001
./start_agent.sh Bob 9002 192.168.1.100:9000
```

**Windows:**
```cmd
start_agent.bat Alice
start_agent.bat Alice 9001
start_agent.bat Bob 9002 192.168.1.100:9000
```

### 方法 2: 手动启动

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动 Agent
python p2p_agent.py --name Alice
```

### 交互命令

| 命令 | 说明 |
|------|------|
| 直接输入文字 | 广播聊天消息给所有 Peer |
| `/connect <ip:port>` | 手动连接其他 Peer |
| `/peers` | 查看已连接的 Peer 列表 |
| `/send <文件路径>` | 发送文件给所有 Peer |
| `/get <peer名称> <file_id>` | 从指定 Peer 下载文件 |
| `/help` | 显示帮助 |
| `/quit` | 退出 |

## 🎯 使用场景

### 场景 1: 局域网自动发现

在同一局域网内，多个 Agent 会自动发现并连接：

```bash
# 电脑 A (Windows)
python p2p_agent.py --name Alice --port 9000

# 电脑 B (macOS) - 自动发现 Alice
python p2p_agent.py --name Bob --port 9000

# 电脑 C (Linux) - 自动发现 Alice 和 Bob
python p2p_agent.py --name Charlie --port 9000
```

### 场景 2: 跨网络手动连接

不同网络的 Agent 需要手动连接：

```bash
# 电脑 A (公网 IP: 1.2.3.4)
python p2p_agent.py --name Alice --port 9000 --no-discover

# 电脑 B (连接到 A)
python p2p_agent.py --name Bob --port 9000 --no-discover --connect 1.2.3.4:9000
```

### 场景 3: 同一台电脑测试

在同一台电脑上测试多个 Agent：

```bash
# 终端 1
python p2p_agent.py --name Alice --port 9000

# 终端 2
python p2p_agent.py --name Bob --port 9002 --connect 127.0.0.1:9000

# 终端 3
python p2p_agent.py --name Charlie --port 9004 --connect 127.0.0.1:9000
```

## 📐 架构图

```
    ┌─────────────┐                    ┌─────────────┐
    │   Alice     │◄──── WebSocket ───►│     Bob     │
    │  (Windows)  │                    │   (macOS)   │
    │  :9000      │                    │    :9000    │
    └──────┬──────┘                    └──────┬──────┘
           │                                  │
           │         UDP Broadcast            │
           │◄────────────────────────────────►│
           │                                  │
    ┌──────┴──────┐                    ┌──────┴──────┐
    │   HTTP      │◄──── File ────────►│    HTTP     │
    │  :9001      │    Transfer        │   :9001     │
    └─────────────┘                    └─────────────┘
           ▲                                  ▲
           │                                  │
           └──────────── P2P ─────────────────┘
```

## 🔧 端口说明

每个 Agent 使用两个端口：

| 端口 | 用途 |
|------|------|
| `port` (默认 9000) | WebSocket - 聊天消息 |
| `port + 1` (默认 9001) | HTTP - 文件传输 |
| 37020 | UDP 广播 - 自动发现 |

## 🖥️ 平台特定说明

### Windows

```cmd
:: 激活虚拟环境
venv\Scripts\activate

:: 启动 Agent
python p2p_agent.py --name Alice
```

- 使用 `Ctrl+C` 退出
- 防火墙可能需要允许 Python 访问网络

### macOS

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动 Agent
python3 p2p_agent.py --name Alice
```

- 可能需要在系统偏好设置中允许网络访问

### Linux

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动 Agent
python3 p2p_agent.py --name Alice
```

- 确保 UDP 端口 37020 未被防火墙阻止

## 📝 注意事项

1. **防火墙** - 确保端口未被防火墙阻止
2. **同一局域网** - 自动发现仅在同一局域网内有效
3. **端口冲突** - 同一台电脑运行多个 Agent 时使用不同端口
4. **文件存储** - 上传的文件保存在 `uploads/` 目录，下载的文件保存在 `downloads/` 目录

## 🔍 故障排除

### 无法发现其他 Agent

1. 检查是否在同一局域网
2. 检查防火墙是否阻止 UDP 广播
3. 尝试手动连接：`/connect <ip:port>`

### 连接失败

1. 检查目标 Agent 是否正在运行
2. 检查端口是否正确
3. 检查防火墙设置

### 文件传输失败

1. 检查 HTTP 端口是否被占用
2. 检查磁盘空间是否充足
