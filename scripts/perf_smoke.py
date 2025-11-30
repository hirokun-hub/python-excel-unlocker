#!/usr/bin/env python3
"""
パフォーマンススモークテスト

目的: 20MB以下のファイルをN=4並列で処理し、10秒以内に完了することを確認
合否基準: 全リクエストがHTTP 200で成功し、10秒以内に完了すること
"""

import os
import sys
import time
import json
import glob
import argparse
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    import requests
except ImportError:
    print("Error: requests ライブラリが必要です。pip install requests を実行してください。")
    sys.exit(1)

# 設定
DEFAULT_BASE_URL = "http://localhost:3000"
DEFAULT_PARALLEL_COUNT = 4
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_PASSWORD = "test1234"
DEFAULT_DATA_DIR = "data"

# 色付き出力
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'

def log_info(msg: str):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {msg}")

def log_warn(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def log_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")
