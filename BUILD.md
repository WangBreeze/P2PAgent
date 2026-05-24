# 📦 P2P Agent 打包指南

## 快速打包（当前平台）

### 方法 1: 使用 Makefile

```bash
# 安装依赖
make install

# 打包
make build

# 输出文件在 dist/ 目录
```

### 方法 2: 直接运行脚本

```bash
# 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 打包
python build.py
```

### 方法 3: 手动打包

```bash
pip install pyinstaller
pyinstaller --name=p2p-agent --onefile --console p2p_agent.py
```

## 输出文件

打包完成后，在 `dist/` 目录下会生成可执行文件：

| 平台 | 文件名 | 大小 |
|------|--------|------|
| Linux | `p2p-agent` | ~15MB |
| macOS | `p2p-agent` | ~15MB |
| Windows | `p2p-agent.exe` | ~15MB |

## 安装到系统

### Linux/macOS

```bash
# 方法 1: 使用安装脚本
chmod +x install.sh
./install.sh

# 方法 2: 手动安装
cp dist/p2p-agent ~/.local/bin/
chmod +x ~/.local/bin/p2p-agent
```

### Windows

```cmd
REM 方法 1: 使用安装脚本
install.bat

REM 方法 2: 手动复制
copy dist\p2p-agent.exe C:\Users\%USERNAME%\p2p-agent\
```

## 跨平台打包

### 使用 GitHub Actions（推荐）

1. Fork 本项目
2. 创建 Release Tag: `git tag v1.0.0 && git push --tags`
3. GitHub Actions 会自动构建三个平台的版本
4. 在 Release 页面下载

### 本地交叉编译

```bash
# Linux
make build-linux

# macOS (需要 macOS 系统)
make build-macos

# Windows (需要 Windows 或 Wine)
make build-windows
```

## 使用打包后的程序

### 直接运行

```bash
# Linux/macOS
./dist/p2p-agent --name Alice

# Windows
dist\p2p-agent.exe --name Alice
```

### 分发给其他人

直接将 `dist/p2p-agent`（或 `p2p-agent.exe`）发送给其他人，无需安装 Python！

```bash
# 电脑 A
./p2p-agent --name Alice --port 9000

# 电脑 B
./p2p-agent --name Bob --port 9000 --connect 192.168.1.100:9000
```

## 常见问题

### Q: 打包后文件太大？

A: 使用 `--exclude-module` 排除不需要的模块：
```bash
pyinstaller --name=p2p-agent --onefile --console \
    --exclude-module=tkinter \
    --exclude-module=matplotlib \
    p2p_agent.py
```

### Q: Windows 杀毒软件误报？

A: 这是 PyInstaller 打包的常见问题。解决方案：
1. 使用代码签名证书签名
2. 在杀毒软件中添加白名单
3. 使用 Nuitka 替代 PyInstaller

### Q: macOS 提示"无法验证开发者"？

A: 右键点击程序 -> 打开 -> 仍然打开

或者移除隔离属性：
```bash
xattr -d com.apple.quarantine p2p-agent
```
