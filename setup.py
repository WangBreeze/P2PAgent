"""
P2P Agent 打包配置
用于 PyInstaller 打包成独立可执行文件
"""

from setuptools import setup, find_packages

setup(
    name="p2p-agent",
    version="1.0.0",
    description="去中心化 P2P 通信系统 - 支持聊天和文件传输",
    author="P2P Agent",
    packages=find_packages(),
    install_requires=[
        "websockets>=12.0",
        "aiohttp>=3.9.0",
    ],
    entry_points={
        "console_scripts": [
            "p2p-agent=p2p_agent:main",
        ],
    },
    python_requires=">=3.8",
)
