#!/usr/bin/env python3
"""
GitHub Step Summary更新スクリプト

suspects.jsonから上位5件を読み込んで
GitHub Step Summaryに表形式で追加する。
"""

import json
import os
import sys


def main():
    """メイン処理"""
    if not os.path.exists('analysis_data/suspects.json'):
        print("| - | ランキングデータなし | - | - |")
        return 0
    
    try:
        with open('analysis_data/suspects.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        suspects = data.get('top_suspects', [])
        for i, suspect in enumerate(suspects[:5], 1):
            file_name = suspect.get('file', 'N/A')
            line_num = suspect.get('line', '-') if suspect.get('line') else '-'
            score = suspect.get('score', 0)
            print(f"| {i} | {file_name} | {line_num} | {score} |")
    
    except Exception as e:
        print(f"Error reading suspects.json: {e}")
        print("| - | エラー | - | - |")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())