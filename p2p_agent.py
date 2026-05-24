"""
P2P Agent - 去中心化的点对点通信系统
支持：自动发现、聊天、文件传输
平台：Windows、macOS、Linux

启动: python p2p_agent.py --name MyAgent [--port 9000] [--discover]
"""

import asyncio
import json
import uuid
import os
import sys
import argparse
import socket
import platform
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

import websockets
from aiohttp import web


# ============ 配置 ============

BROADCAST_PORT = 37020  # UDP 广播端口
BROADCAST_INTERVAL = 5  # 广播间隔(秒)
BROADCAST_MAGIC = "P2P_AGENT_DISCOVERY"  # 广播魔数
SYSTEM = platform.system()  # Windows, Darwin, Linux


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def get_local_ip() -> str:
    """获取本机局域网 IP（跨平台）"""
    try:
        # 方法1：通过 UDP 连接获取
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip
    except:
        return "127.0.0.1"


def get_broadcast_address() -> str:
    """获取广播地址（跨平台）"""
    try:
        local_ip = get_local_ip()
        if local_ip == "127.0.0.1":
            return "255.255.255.255"
        
        # 计算广播地址
        parts = local_ip.split(".")
        parts[-1] = "255"
        return ".".join(parts)
    except:
        return "255.255.255.255"


# ============ Peer 信息 ============

class PeerInfo:
    def __init__(self, name: str, ip: str, ws_port: int, http_port: int):
        self.name = name
        self.ip = ip
        self.ws_port = ws_port
        self.http_port = http_port
        self.ws = None  # WebSocket 连接
    
    @property
    def id(self) -> str:
        return f"{self.name}@{self.ip}:{self.ws_port}"
    
    @property
    def http_url(self) -> str:
        return f"http://{self.ip}:{self.http_port}"
    
    def __str__(self):
        return f"{self.name} ({self.ip}:{self.ws_port})"


# ============ P2P 节点 ============

class P2PNode:
    def __init__(self, name: str, port: int, enable_discovery: bool = True):
        self.name = name
        self.ip = get_local_ip()
        self.ws_port = port
        self.http_port = port + 1
        self.enable_discovery = enable_discovery
        
        # 已连接的 Peers {peer_id: PeerInfo}
        self.peers: Dict[str, PeerInfo] = {}
        
        # 文件存储
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)
        
        # 文件元数据 {file_id: metadata}
        self.file_metadata: Dict[str, dict] = {}
        
        self.running = True
        self._ws_server = None
        self._http_runner = None
    
    # ============ 启动 ============
    
    async def start(self):
        """启动所有服务"""
        log(f"🚀 启动 P2P Agent: {self.name}")
        log(f"   平台: {SYSTEM}")
        log(f"   本机 IP: {self.ip}")
        log(f"   WebSocket 端口: {self.ws_port}")
        log(f"   HTTP 端口: {self.http_port}")
        
        tasks = []
        
        # 启动 WebSocket 服务器
        tasks.append(asyncio.create_task(self.start_ws_server()))
        
        # 启动 HTTP 服务器
        tasks.append(asyncio.create_task(self.start_http_server()))
        
        # 启动 UDP 发现
        if self.enable_discovery:
            tasks.append(asyncio.create_task(self.broadcast_presence()))
            tasks.append(asyncio.create_task(self.listen_broadcast()))
        
        log("=" * 50)
        log("✅ P2P Agent 已就绪！")
        log("=" * 50)
        
        # 保持运行直到 self.running = False
        try:
            while self.running:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """优雅关闭"""
        log("🛑 正在关闭...")
        self.running = False
        
        # 关闭所有 Peer 连接
        for peer in list(self.peers.values()):
            if peer.ws:
                try:
                    await peer.ws.close()
                except:
                    pass
        
        # 关闭 WebSocket 服务器
        if self._ws_server:
            self._ws_server.close()
            await self._ws_server.wait_closed()
        
        # 关闭 HTTP 服务器
        if self._http_runner:
            await self._http_runner.cleanup()
    
    # ============ WebSocket 服务端 ============
    
    async def start_ws_server(self):
        """启动 WebSocket 服务器"""
        try:
            self._ws_server = await websockets.serve(
                self.handle_peer_connection, 
                "0.0.0.0", 
                self.ws_port
            )
            log(f"🔗 WebSocket 服务已启动: ws://{self.ip}:{self.ws_port}")
            await self._ws_server.wait_closed()
        except OSError as e:
            log(f"❌ WebSocket 端口 {self.ws_port} 被占用: {e}")
            self.running = False
    
    async def handle_peer_connection(self, websocket):
        """处理来自其他 Peer 的连接"""
        peer = None
        try:
            # 第一条消息是注册信息
            raw = await websocket.recv()
            data = json.loads(raw)
            
            if data.get("type") != "register":
                await websocket.send(json.dumps({"type": "error", "content": "请先注册"}))
                return
            
            # 创建 Peer 信息
            peer = PeerInfo(
                name=data["name"],
                ip=data.get("ip", websocket.remote_address[0]),
                ws_port=data.get("ws_port", 0),
                http_port=data.get("http_port", 0)
            )
            peer.ws = websocket
            
            # 保存 Peer
            self.peers[peer.id] = peer
            log(f"✅ 新 Peer 连接: {peer}")
            
            # 回复注册成功
            await websocket.send(json.dumps({
                "type": "register_ack",
                "name": self.name,
                "ip": self.ip,
                "ws_port": self.ws_port,
                "http_port": self.http_port
            }))
            
            # 通知其他 Peer
            await self.broadcast({
                "type": "system",
                "content": f"{peer.name} 已加入"
            }, exclude=peer.id)
            
            # 消息循环
            async for raw in websocket:
                data = json.loads(raw)
                await self.handle_message(data, peer)
        
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            log(f"❌ 连接错误: {e}")
        finally:
            if peer and peer.id in self.peers:
                del self.peers[peer.id]
                log(f"👋 Peer 断开: {peer.name}")
                await self.broadcast({
                    "type": "system",
                    "content": f"{peer.name} 已离开"
                })
    
    # ============ 主动连接其他 Peer ============
    
    async def connect_to_peer(self, address: str):
        """主动连接到其他 Peer"""
        try:
            # 解析地址
            if ":" in address:
                ip, port = address.rsplit(":", 1)
                port = int(port)
            else:
                ip = address
                port = 9000  # 默认端口
            
            ws_url = f"ws://{ip}:{port}"
            log(f"🔗 正在连接: {ws_url}")
            
            ws = await websockets.connect(ws_url)
            
            # 发送注册信息
            await ws.send(json.dumps({
                "type": "register",
                "name": self.name,
                "ip": self.ip,
                "ws_port": self.ws_port,
                "http_port": self.http_port
            }))
            
            # 等待确认
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(raw)
            
            if data.get("type") == "register_ack":
                peer = PeerInfo(
                    name=data["name"],
                    ip=data.get("ip", ip),
                    ws_port=data.get("ws_port", port),
                    http_port=data.get("http_port", port + 1)
                )
                peer.ws = ws
                self.peers[peer.id] = peer
                
                log(f"✅ 已连接到: {peer}")
                
                # 启动消息接收
                asyncio.create_task(self.receive_from_peer(peer))
                
                return True
            else:
                log(f"❌ 注册失败: {data}")
                await ws.close()
                return False
        
        except Exception as e:
            log(f"❌ 连接失败: {e}")
            return False
    
    async def receive_from_peer(self, peer: PeerInfo):
        """接收来自已连接 Peer 的消息"""
        try:
            async for raw in peer.ws:
                data = json.loads(raw)
                await self.handle_message(data, peer)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            log(f"❌ 接收错误: {e}")
        finally:
            if peer.id in self.peers:
                del self.peers[peer.id]
                log(f"👋 与 {peer.name} 的连接已断开")
    
    # ============ 消息处理 ============
    
    async def handle_message(self, data: dict, peer: PeerInfo):
        """处理收到的消息"""
        msg_type = data.get("type", "chat")
        
        if msg_type == "chat":
            content = data.get("content", "")
            print(f"\r💬 [{peer.name}]: {content}")
            self.show_prompt()
        
        elif msg_type == "file_notify":
            filename = data.get("filename", "")
            file_id = data.get("file_id", "")
            print(f"\r📁 [{peer.name}] 分享了文件: {filename} (ID: {file_id})")
            self.show_prompt()
        
        elif msg_type == "system":
            content = data.get("content", "")
            print(f"\r🔔 {content}")
            self.show_prompt()
        
        # 转发给其他 Peer（避免重复转发）
        if data.get("origin") != self.name:
            data["origin"] = data.get("from", peer.name)
            await self.broadcast(data, exclude=peer.id)
    
    async def broadcast(self, message: dict, exclude: str = None):
        """广播消息给所有已连接的 Peer"""
        if not self.peers:
            return
        
        message["from"] = self.name
        payload = json.dumps(message, ensure_ascii=False)
        
        disconnected = []
        for peer_id, peer in list(self.peers.items()):
            if peer_id != exclude and peer.ws:
                try:
                    await peer.ws.send(payload)
                except:
                    disconnected.append(peer_id)
        
        # 清理断开的连接
        for pid in disconnected:
            if pid in self.peers:
                del self.peers[pid]
    
    # ============ UDP 广播发现 ============
    
    async def broadcast_presence(self):
        """UDP 广播自己的存在"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        message = json.dumps({
            "magic": BROADCAST_MAGIC,
            "name": self.name,
            "ip": self.ip,
            "ws_port": self.ws_port,
            "http_port": self.http_port
        }).encode()
        
        broadcast_addr = get_broadcast_address()
        
        while self.running:
            try:
                sock.sendto(message, (broadcast_addr, BROADCAST_PORT))
            except Exception as e:
                # Windows 可能会报错，忽略
                pass
            await asyncio.sleep(BROADCAST_INTERVAL)
    
    async def listen_broadcast(self):
        """监听 UDP 广播，发现其他 Peer"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Windows 需要绑定到具体端口
        try:
            sock.bind(("", BROADCAST_PORT))
        except OSError:
            # 如果端口被占用，尝试绑定到 0.0.0.0
            sock.bind(("0.0.0.0", BROADCAST_PORT))
        
        sock.setblocking(False)
        
        loop = asyncio.get_event_loop()
        
        while self.running:
            try:
                data, addr = await loop.run_in_executor(None, lambda: sock.recvfrom(1024))
                info = json.loads(data.decode())
                
                # 验证魔数
                if info.get("magic") != BROADCAST_MAGIC:
                    continue
                
                # 忽略自己
                if info.get("name") == self.name and info.get("ip") == self.ip:
                    continue
                
                # 检查是否已连接
                peer_id = f"{info['name']}@{info['ip']}:{info['ws_port']}"
                if peer_id in self.peers:
                    continue
                
                # 自动连接新发现的 Peer
                log(f"🔍 发现新 Peer: {info['name']} ({info['ip']}:{info['ws_port']})")
                address = f"{info['ip']}:{info['ws_port']}"
                asyncio.create_task(self.connect_to_peer(address))
            
            except BlockingIOError:
                await asyncio.sleep(0.1)
            except Exception as e:
                await asyncio.sleep(0.1)
    
    # ============ HTTP 文件服务 ============
    
    async def start_http_server(self):
        """启动 HTTP 文件服务器"""
        try:
            app = web.Application()
            app.router.add_post('/upload', self.handle_upload)
            app.router.add_get('/download/{file_id}', self.handle_download)
            
            self._http_runner = web.AppRunner(app)
            await self._http_runner.setup()
            site = web.TCPSite(self._http_runner, "0.0.0.0", self.http_port)
            await site.start()
            log(f"📁 HTTP 文件服务已启动: http://{self.ip}:{self.http_port}")
            
            # 保持运行
            await asyncio.Future()
        except OSError as e:
            log(f"❌ HTTP 端口 {self.http_port} 被占用: {e}")
            self.running = False
    
    async def handle_upload(self, request: web.Request):
        """处理文件上传"""
        try:
            reader = await request.multipart()
            file_field = await reader.next()
            
            if not file_field or file_field.name != 'file':
                return web.json_response({"error": "缺少 file 字段"}, status=400)
            
            file_id = str(uuid.uuid4())[:8]
            filename = file_field.filename or f"file_{file_id}"
            filepath = self.upload_dir / f"{file_id}_{filename}"
            
            size = 0
            with open(filepath, 'wb') as f:
                while True:
                    chunk = await file_field.read_chunk()
                    if not chunk:
                        break
                    size += len(chunk)
                    f.write(chunk)
            
            self.file_metadata[file_id] = {
                "filename": filename,
                "path": str(filepath),
                "size": size,
                "time": datetime.now().isoformat()
            }
            
            log(f"📥 收到文件: {filename} ({size} bytes)")
            
            return web.json_response({
                "file_id": file_id,
                "filename": filename,
                "size": size
            })
        
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_download(self, request: web.Request):
        """处理文件下载"""
        file_id = request.match_info.get("file_id")
        
        if file_id not in self.file_metadata:
            return web.json_response({"error": "文件不存在"}, status=404)
        
        meta = self.file_metadata[file_id]
        filepath = Path(meta["path"])
        
        if not filepath.exists():
            return web.json_response({"error": "文件已删除"}, status=404)
        
        return web.FileResponse(
            filepath,
            headers={"Content-Disposition": f'attachment; filename="{meta["filename"]}"'}
        )
    
    # ============ 文件操作 ============
    
    async def upload_and_share(self, filepath: str, target_peer_id: str = None):
        """上传文件并分享"""
        import aiohttp
        
        path = Path(filepath)
        if not path.exists():
            log(f"❌ 文件不存在: {filepath}")
            return
        
        # 保存到本地
        file_id = str(uuid.uuid4())[:8]
        import shutil
        dest = self.upload_dir / f"{file_id}_{path.name}"
        shutil.copy(path, dest)
        self.file_metadata[file_id] = {
            "filename": path.name,
            "path": str(dest),
            "size": path.stat().st_size,
            "time": datetime.now().isoformat()
        }
        
        # 上传到所有 Peer
        upload_success = 0
        for peer_id, peer in self.peers.items():
            try:
                async with aiohttp.ClientSession() as session:
                    data = aiohttp.FormData()
                    data.add_field('file', open(path, 'rb'), filename=path.name)
                    
                    async with session.post(f"{peer.http_url}/upload", data=data) as resp:
                        if resp.status == 200:
                            upload_success += 1
                            log(f"📤 已上传到 {peer.name}")
            except Exception as e:
                log(f"⚠️ 上传到 {peer.name} 失败: {e}")
        
        # 通知所有人
        await self.broadcast({
            "type": "file_notify",
            "filename": path.name,
            "file_id": file_id
        })
        
        log(f"✅ 文件已分享: {path.name} (成功上传到 {upload_success} 个 Peer)")
    
    async def download_file(self, file_id: str, peer_name: str, save_path: str = None):
        """从指定 Peer 下载文件"""
        import aiohttp
        
        # 查找 Peer
        target_peer = None
        for peer in self.peers.values():
            if peer.name == peer_name:
                target_peer = peer
                break
        
        if not target_peer:
            log(f"❌ 未找到 Peer: {peer_name}")
            return
        
        url = f"{target_peer.http_url}/download/{file_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        log(f"❌ 下载失败: {resp.status}")
                        return
                    
                    cd = resp.headers.get('Content-Disposition', '')
                    if 'filename=' in cd:
                        filename = cd.split('filename=')[-1].strip('"')
                    else:
                        filename = f"file_{file_id}"
                    
                    save_to = Path(save_path) if save_path else self.download_dir / filename
                    
                    with open(save_to, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                    
                    log(f"✅ 文件已下载: {save_to}")
        
        except Exception as e:
            log(f"❌ 下载错误: {e}")
    
    def show_prompt(self):
        """显示输入提示"""
        sys.stdout.write(f"[{self.name}] > ")
        sys.stdout.flush()


# ============ 主程序 ============

def print_help():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                      📖 P2P Agent 命令帮助                      ║
╠══════════════════════════════════════════════════════════════════╣
║  聊天:      直接输入文字广播给所有 Peer                           ║
║  连接:      /connect <ip:port>    手动连接其他 Peer               ║
║  列表:      /peers                查看已连接的 Peer               ║
║  发送文件:  /send <文件路径>       发送给所有 Peer                 ║
║  下载文件:  /get <peer名称> <file_id>  从指定 Peer 下载           ║
║  帮助:      /help                                                 ║
║  退出:      /quit 或 Ctrl+C                                      ║
╚══════════════════════════════════════════════════════════════════╝
""")


async def main():
    parser = argparse.ArgumentParser(
        description="P2P Agent - 去中心化通信系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动 Agent（自动发现局域网内的其他 Agent）
  python p2p_agent.py --name Alice

  # 指定端口启动
  python p2p_agent.py --name Alice --port 9001

  # 启动时连接到指定 Peer
  python p2p_agent.py --name Bob --connect 192.168.1.100:9000

  # 禁用自动发现（适合跨网络）
  python p2p_agent.py --name Alice --no-discover
"""
    )
    parser.add_argument("--name", required=True, help="Agent 名称")
    parser.add_argument("--port", type=int, default=9000, help="WebSocket 端口 (HTTP 端口=port+1)")
    parser.add_argument("--no-discover", action="store_true", help="禁用自动发现")
    parser.add_argument("--connect", help="启动时自动连接的地址 (ip:port)")
    args = parser.parse_args()
    
    node = P2PNode(args.name, args.port, not args.no_discover)
    
    # 处理 Ctrl+C（跨平台）
    def signal_handler():
        log("👋 收到退出信号")
        node.running = False
    
    loop = asyncio.get_event_loop()
    
    # 注册信号处理
    if SYSTEM != "Windows":
        # Unix 系统使用 signal
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
    
    # 启动节点（后台运行）
    start_task = asyncio.create_task(node.start())
    
    # 等待服务启动
    await asyncio.sleep(1)
    
    # 自动连接
    if args.connect:
        await node.connect_to_peer(args.connect)
    
    print_help()
    
    # 输入循环
    has_terminal = sys.stdin.isatty()
    
    if not has_terminal:
        log("⚠️ 无终端模式，仅提供服务功能")
        log("   使用 'python p2p_agent.py --name XXX --connect IP:PORT' 连接")
    
    try:
        while node.running:
            if not has_terminal:
                # 无终端模式，只保持服务运行
                await asyncio.sleep(1)
                continue
            
            try:
                node.show_prompt()
                
                line = await asyncio.get_event_loop().run_in_executor(None, input)
                line = line.strip()
                
                if not line:
                    continue
                
                if line.startswith('/'):
                    parts = line.split(maxsplit=2)
                    cmd = parts[0].lower()
                    
                    if cmd == '/quit' or cmd == '/exit':
                        log("👋 再见!")
                        node.running = False
                        break
                    
                    elif cmd == '/help':
                        print_help()
                    
                    elif cmd == '/peers':
                        if not node.peers:
                            print("📭 暂无已连接的 Peer")
                        else:
                            print("\n👥 已连接的 Peer:")
                            print("-" * 50)
                            for peer_id, peer in node.peers.items():
                                print(f"  • {peer.name} ({peer.ip}:{peer.ws_port})")
                            print("-" * 50)
                    
                    elif cmd == '/connect':
                        if len(parts) < 2:
                            print("❌ 用法: /connect <ip:port>")
                            continue
                        await node.connect_to_peer(parts[1])
                    
                    elif cmd == '/send':
                        if len(parts) < 2:
                            print("❌ 用法: /send <文件路径>")
                            continue
                        await node.upload_and_share(parts[1])
                    
                    elif cmd == '/get':
                        if len(parts) < 3:
                            print("❌ 用法: /get <peer名称> <file_id>")
                            continue
                        await node.download_file(parts[2], parts[1])
                    
                    else:
                        print(f"❌ 未知命令: {cmd}，输入 /help 查看帮助")
                
                else:
                    # 广播聊天消息
                    await node.broadcast({
                        "type": "chat",
                        "content": line
                    })
                    print(f"💬 [我]: {line}")
            
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                if node.running:
                    log(f"❌ 错误: {e}")
    
    except KeyboardInterrupt:
        pass
    finally:
        node.running = False
        start_task.cancel()
        try:
            await start_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见!")
