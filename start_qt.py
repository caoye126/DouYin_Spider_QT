#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qt界面启动脚本
作者: 五更琉璃
日期: 2025年
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from qt_interface import main
    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装PyQt5: pip install PyQt5")
    sys.exit(1)
except Exception as e:
    print(f"启动错误: {e}")
    sys.exit(1)
