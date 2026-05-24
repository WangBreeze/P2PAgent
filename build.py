"""
PyInstaller 打包脚本
支持 Windows、macOS、Linux
"""

import PyInstaller.__main__
import platform
import os
import shutil

SYSTEM = platform.system()

# 打包配置
args = [
    'p2p_agent.py',
    '--name=p2p-agent',
    '--onefile',  # 打包成单个文件
    '--console',  # 控制台程序
    '--clean',
    '--noconfirm',
]

# 添加数据文件
if SYSTEM == 'Windows':
    args.append('--icon=NONE')

# 执行打包
print(f"🚀 开始打包 ({SYSTEM})...")
PyInstaller.__main__.run(args)

print(f"✅ 打包完成！")
print(f"   输出目录: dist/")
