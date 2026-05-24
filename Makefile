.PHONY: build clean install run

# 默认目标
all: build

# 安装依赖
install:
	pip install -r requirements.txt
	pip install pyinstaller

# 打包（当前平台）
build:
	python build.py

# 打包所有平台（需要交叉编译环境）
build-all: build-linux build-macos build-windows

build-linux:
	@echo "📦 打包 Linux 版本..."
	pyinstaller --name=p2p-agent-linux --onefile --console p2p_agent.py

build-macos:
	@echo "📦 打包 macOS 版本..."
	pyinstaller --name=p2p-agent-macos --onefile --console p2p_agent.py

build-windows:
	@echo "📦 打包 Windows 版本..."
	pyinstaller --name=p2p-agent-windows.exe --onefile --console p2p_agent.py

# 清理
clean:
	rm -rf build/ dist/ *.spec __pycache__/

# 运行测试
test:
	python -m pytest test_p2p.py -v

# 运行示例
run:
	python p2p_agent.py --name TestAgent
