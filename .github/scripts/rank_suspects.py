#!/usr/bin/env python3
"""
GitHub Actions診断シグナル04: 統合ランキング生成スクリプト

スタックトレース、ホットスポット、直近変更を統合して
問題箇所をスコアリングし、上位50件をランキング形式で出力する。
"""

import json
import os
import glob
from collections import defaultdict
from datetime import datetime
import sys


def load_json_safe(filepath):
    """JSONファイルを安全に読み込む"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return {}


def extract_stack_frames(log_files):
    """ログファイルからスタックフレーム情報を抽出"""
    frames = []
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 簡易的なスタックトレース抽出
                    lines = content.split('\n')
                    for line in lines:
                        if 'FAILED' in line or 'Error' in line or 'Exception' in line:
                            # ファイルパスを抽出（簡易版）
                            if '.ts' in line or '.js' in line or '.py' in line:
                                parts = line.split()
                                for part in parts:
                                    if '.ts' in part or '.js' in part or '.py' in part:
                                        frames.append({'file': part, 'line': None})
                                        break
            except Exception as e:
                print(f"Error processing {log_file}: {e}")
    return frames


def calculate_suspects():
    """問題箇所の統合ランキングを計算"""
    suspects = defaultdict(int)
    
    # スタックトレースから上位フレーム (+50点)
    log_files = [
        'analysis_data/logs/vitest-first.json',
        'analysis_data/logs/jest-first.json', 
        'analysis_data/logs/pytest-first.txt',
        'analysis_data/logs/next-smoke.txt',
        'analysis_data/logs/py-import-smoke.txt'
    ]
    
    frames = extract_stack_frames(log_files)
    for frame in frames[:3]:  # 上位3フレーム
        key = (frame['file'], frame['line'])
        suspects[key] += 50
    
    # 直近変更ファイル (+20点)
    change_map = load_json_safe('project-metadata/change-map.json')
    if 'changed_files' in change_map:
        for file_path in change_map['changed_files']:
            key = (file_path, None)
            suspects[key] += 20
    
    # ホットスポット (+15点)
    hotspots = load_json_safe('analysis_data/hotspots.json')
    if 'files' in hotspots:
        for hotspot in hotspots['files']:
            if 'file' in hotspot:
                key = (hotspot['file'], None)
                suspects[key] += 15
    
    # 降順ソートして上位50件
    sorted_suspects = sorted(suspects.items(), key=lambda x: x[1], reverse=True)[:50]
    
    return [
        {'file': file, 'line': line, 'score': score}
        for (file, line), score in sorted_suspects
    ]


def generate_github_summary(suspects):
    """GitHub Step Summary用のマークダウンテーブルを生成"""
    if not suspects:
        return "問題箇所が特定されませんでした。"
    
    lines = [
        "## 🎯 問題箇所ランキング（上位5件）",
        "| 順位 | ファイル | 行 | スコア |",
        "|------|----------|----|---------| "
    ]
    
    for i, suspect in enumerate(suspects[:5], 1):
        file_name = suspect['file'] if suspect['file'] else 'N/A'
        line_num = suspect['line'] if suspect['line'] else '-'
        score = suspect['score']
        lines.append(f"| {i} | {file_name} | {line_num} | {score} |")
    
    return '\n'.join(lines)


def main():
    """メイン処理"""
    print("🎯 統合ランキング生成を開始...")
    
    # ディレクトリ作成
    os.makedirs('analysis_data', exist_ok=True)
    
    # ランキング生成
    suspects = calculate_suspects()
    
    # 結果保存
    result = {
        'generated_at': datetime.utcnow().isoformat(),
        'total_suspects': len(suspects),
        'top_suspects': suspects,
        'scoring_breakdown': {
            'stack_traces': 50,
            'recent_changes': 20,
            'hotspots': 15
        }
    }
    
    with open('analysis_data/suspects.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {len(suspects)}件の問題箇所候補を生成しました")
    
    # GitHub Step Summary用の出力
    summary = generate_github_summary(suspects)
    print("\n" + summary)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())