#!/usr/bin/env python3
"""
タスク管理とGit自動化スクリプト
タスクの完了マーク、自動コミット・プッシュを統合管理
"""

import os
import re
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class Colors:
    """コンソール出力用の色定義"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

class TaskManager:
    """タスク管理クラス"""
    
    def __init__(self, task_file_path: str = ".kiro/specs/secure-excel-unlock/tasks.md"):
        self.task_file_path = Path(task_file_path)
        self.project_root = Path(__file__).parent.parent
        os.chdir(self.project_root)
        
    def log(self, level: str, message: str):
        """色付きログ出力"""
        colors = {
            'INFO': Colors.BLUE,
            'SUCCESS': Colors.GREEN,
            'WARNING': Colors.YELLOW,
            'ERROR': Colors.RED,
            'DEBUG': Colors.PURPLE
        }
        color = colors.get(level, Colors.NC)
        print(f"{color}[{level}]{Colors.NC} {message}")
    
    def run_command(self, command: List[str], capture_output: bool = True) -> Tuple[bool, str]:
        """コマンド実行"""
        try:
            result = subprocess.run(
                command, 
                capture_output=capture_output, 
                text=True, 
                check=True
            )
            return True, result.stdout.strip() if capture_output else ""
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            return False, error_msg
    
    def get_git_status(self) -> Dict[str, any]:
        """Git状態の取得"""
        status = {}
        
        # 変更ファイルの確認
        success, output = self.run_command(['git', 'status', '--porcelain'])
        status['has_changes'] = bool(output.strip()) if success else False
        status['changed_files'] = output.strip().split('\n') if output.strip() else []
        
        # 現在のブランチ
        success, branch = self.run_command(['git', 'branch', '--show-current'])
        status['current_branch'] = branch if success else 'unknown'
        
        # 最新コミットハッシュ
        success, commit_hash = self.run_command(['git', 'rev-parse', '--short', 'HEAD'])
        status['latest_commit'] = commit_hash if success else 'unknown'
        
        return status
    
    def check_sensitive_content(self) -> List[str]:
        """機密情報チェック"""
        sensitive_patterns = [
            r'password\s*[=:]\s*["\']?[^"\'\s]+',
            r'secret\s*[=:]\s*["\']?[^"\'\s]+',
            r'key\s*[=:]\s*["\']?[^"\'\s]+',
            r'token\s*[=:]\s*["\']?[^"\'\s]+',
            r'aws_access_key_id\s*[=:]\s*["\']?[^"\'\s]+',
            r'aws_secret_access_key\s*[=:]\s*["\']?[^"\'\s]+',
        ]
        
        warnings = []
        
        # ステージングされたファイルをチェック
        success, staged_files = self.run_command(['git', 'diff', '--cached', '--name-only'])
        if not success or not staged_files:
            return warnings
        
        for file_path in staged_files.split('\n'):
            if not file_path.strip():
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in sensitive_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        warnings.append(f"機密情報の可能性: {file_path} (パターン: {pattern})")
            except (FileNotFoundError, PermissionError):
                continue
        
        return warnings
    
    def check_large_files(self, size_limit_mb: int = 10) -> List[str]:
        """大容量ファイルチェック"""
        warnings = []
        size_limit_bytes = size_limit_mb * 1024 * 1024
        
        success, staged_files = self.run_command(['git', 'diff', '--cached', '--name-only'])
        if not success or not staged_files:
            return warnings
        
        for file_path in staged_files.split('\n'):
            if not file_path.strip():
                continue
                
            try:
                file_size = os.path.getsize(file_path)
                if file_size > size_limit_bytes:
                    size_mb = file_size / (1024 * 1024)
                    warnings.append(f"大容量ファイル: {file_path} ({size_mb:.1f}MB)")
            except (FileNotFoundError, OSError):
                continue
        
        return warnings
    
    def parse_tasks(self) -> List[Dict[str, any]]:
        """タスクファイルの解析"""
        if not self.task_file_path.exists():
            self.log('ERROR', f"タスクファイルが見つかりません: {self.task_file_path}")
            return []
        
        tasks = []
        with open(self.task_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # タスクパターンの正規表現
        task_pattern = r'^- \[([ x])\] (\d+(?:\.\d+)?)\.\s*(.+)$'
        
        for line_num, line in enumerate(content.split('\n'), 1):
            match = re.match(task_pattern, line.strip())
            if match:
                completed = match.group(1) == 'x'
                task_number = match.group(2)
                title = match.group(3)
                
                tasks.append({
                    'line_number': line_num,
                    'task_number': task_number,
                    'title': title,
                    'completed': completed,
                    'raw_line': line
                })
        
        return tasks
    
    def mark_task_completed(self, task_number: str, dry_run: bool = False) -> bool:
        """タスクを完了済みにマーク"""
        if not self.task_file_path.exists():
            self.log('ERROR', f"タスクファイルが見つかりません: {self.task_file_path}")
            return False
        
        with open(self.task_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # タスクを完了済みにマーク
        pattern = f'^(- \\[)[ ](\\] {re.escape(task_number)}\\..*)$'
        replacement = r'\1x\2'
        
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        
        if count == 0:
            self.log('WARNING', f"タスク{task_number}が見つかりませんでした")
            return False
        
        if dry_run:
            self.log('INFO', f"[ドライラン] タスク{task_number}を完了済みにマークする予定です")
            return True
        
        # ファイルに書き戻し
        with open(self.task_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        self.log('SUCCESS', f"タスク{task_number}を完了済みにマークしました")
        return True
    
    def generate_commit_message(self, task_number: str, task_title: str) -> str:
        """コミットメッセージ生成"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""feat: タスク{task_number}完了 - {task_title}

- タスク{task_number}の実装を完了
- {task_title}に関する変更を適用
- 関連ファイルの更新とテスト実行

完了日時: {timestamp}
Co-authored-by: Kiro AI Assistant <kiro@example.com>"""
    
    def auto_commit_and_push(self, task_number: str, task_title: str, dry_run: bool = False) -> bool:
        """自動コミット・プッシュ"""
        self.log('INFO', f"タスク{task_number}の自動コミット・プッシュを開始します")
        
        # Git状態確認
        git_status = self.get_git_status()
        if not git_status['has_changes']:
            self.log('WARNING', "コミットする変更がありません")
            return False
        
        # 安全性チェック
        self.log('INFO', "安全性チェックを実行しています...")
        
        sensitive_warnings = self.check_sensitive_content()
        if sensitive_warnings:
            self.log('WARNING', "機密情報の可能性があるファイルが検出されました:")
            for warning in sensitive_warnings:
                print(f"  - {warning}")
        
        large_file_warnings = self.check_large_files()
        if large_file_warnings:
            self.log('WARNING', "大容量ファイルが検出されました:")
            for warning in large_file_warnings:
                print(f"  - {warning}")
        
        # コミットメッセージ生成
        commit_message = self.generate_commit_message(task_number, task_title)
        
        self.log('INFO', "生成されたコミットメッセージ:")
        print("=" * 50)
        print(commit_message)
        print("=" * 50)
        
        # 変更内容表示
        self.log('INFO', "コミット対象の変更内容:")
        success, status_output = self.run_command(['git', 'status', '--short'])
        if success:
            print(status_output)
        
        if dry_run:
            self.log('INFO', "[ドライラン] 以下の操作が実行される予定です:")
            self.log('INFO', "[ドライラン] 1. git add .")
            self.log('INFO', f"[ドライラン] 2. git commit -m \"{commit_message.split(chr(10))[0]}...\"")
            self.log('INFO', f"[ドライラン] 3. git push origin {git_status['current_branch']}")
            return True
        
        # 確認プロンプト
        if sensitive_warnings or large_file_warnings:
            response = input(f"\n{Colors.YELLOW}警告が検出されました。続行しますか？ (y/N): {Colors.NC}")
            if response.lower() != 'y':
                self.log('INFO', "操作をキャンセルしました")
                return False
        
        response = input(f"\n{Colors.CYAN}この内容でコミット・プッシュを実行しますか？ (y/N): {Colors.NC}")
        if response.lower() != 'y':
            self.log('INFO', "操作をキャンセルしました")
            return False
        
        # Git操作実行
        self.log('INFO', "変更をステージングしています...")
        success, _ = self.run_command(['git', 'add', '.'])
        if not success:
            self.log('ERROR', "git add に失敗しました")
            return False
        
        self.log('INFO', "コミットを実行しています...")
        success, _ = self.run_command(['git', 'commit', '-m', commit_message])
        if not success:
            self.log('ERROR', "git commit に失敗しました")
            return False
        
        self.log('INFO', "リモートリポジトリにプッシュしています...")
        success, _ = self.run_command(['git', 'push', 'origin', git_status['current_branch']])
        if not success:
            self.log('ERROR', "git push に失敗しました")
            return False
        
        # 最新のコミットハッシュを取得
        success, new_commit_hash = self.run_command(['git', 'rev-parse', '--short', 'HEAD'])
        
        self.log('SUCCESS', f"タスク{task_number}の変更を正常にコミット・プッシュしました")
        self.log('SUCCESS', f"ブランチ: {git_status['current_branch']}")
        self.log('SUCCESS', f"コミットハッシュ: {new_commit_hash if success else 'unknown'}")
        
        return True
    
    def list_tasks(self, show_completed: bool = False):
        """タスク一覧表示"""
        tasks = self.parse_tasks()
        if not tasks:
            self.log('WARNING', "タスクが見つかりませんでした")
            return
        
        self.log('INFO', f"タスク一覧 (合計: {len(tasks)}件)")
        print()
        
        for task in tasks:
            if not show_completed and task['completed']:
                continue
                
            status_icon = "✅" if task['completed'] else "⏳"
            status_text = "完了" if task['completed'] else "未完了"
            
            print(f"{status_icon} タスク{task['task_number']}: {task['title']}")
            print(f"   状態: {status_text}")
            print()
    
    def complete_task(self, task_number: str, dry_run: bool = False):
        """タスク完了処理（マーク + コミット・プッシュ）"""
        tasks = self.parse_tasks()
        target_task = None
        
        for task in tasks:
            if task['task_number'] == task_number:
                target_task = task
                break
        
        if not target_task:
            self.log('ERROR', f"タスク{task_number}が見つかりませんでした")
            return False
        
        if target_task['completed']:
            self.log('WARNING', f"タスク{task_number}は既に完了済みです")
            return False
        
        self.log('INFO', f"タスク{task_number}を完了処理します: {target_task['title']}")
        
        # タスクを完了済みにマーク
        if not self.mark_task_completed(task_number, dry_run):
            return False
        
        # 自動コミット・プッシュ
        return self.auto_commit_and_push(task_number, target_task['title'], dry_run)

def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print(f"""
{Colors.BLUE}タスク管理スクリプト{Colors.NC}

使用方法:
  {sys.argv[0]} list [--all]              # タスク一覧表示
  {sys.argv[0]} complete <task_number> [--dry-run]  # タスク完了処理
  {sys.argv[0]} mark <task_number> [--dry-run]      # タスクを完了済みにマーク
  {sys.argv[0]} commit <task_number> <title> [--dry-run]  # コミット・プッシュのみ

例:
  {sys.argv[0]} list
  {sys.argv[0]} complete 15 --dry-run
  {sys.argv[0]} mark 15
  {sys.argv[0]} commit 15 "JWT認証への移行"
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    task_manager = TaskManager()
    
    if command == 'list':
        show_all = '--all' in sys.argv
        task_manager.list_tasks(show_completed=show_all)
    
    elif command == 'complete':
        if len(sys.argv) < 3:
            print(f"{Colors.RED}エラー: タスク番号を指定してください{Colors.NC}")
            sys.exit(1)
        
        task_number = sys.argv[2]
        dry_run = '--dry-run' in sys.argv
        task_manager.complete_task(task_number, dry_run)
    
    elif command == 'mark':
        if len(sys.argv) < 3:
            print(f"{Colors.RED}エラー: タスク番号を指定してください{Colors.NC}")
            sys.exit(1)
        
        task_number = sys.argv[2]
        dry_run = '--dry-run' in sys.argv
        task_manager.mark_task_completed(task_number, dry_run)
    
    elif command == 'commit':
        if len(sys.argv) < 4:
            print(f"{Colors.RED}エラー: タスク番号とタイトルを指定してください{Colors.NC}")
            sys.exit(1)
        
        task_number = sys.argv[2]
        task_title = sys.argv[3]
        dry_run = '--dry-run' in sys.argv
        task_manager.auto_commit_and_push(task_number, task_title, dry_run)
    
    else:
        print(f"{Colors.RED}エラー: 不明なコマンド '{command}'{Colors.NC}")
        sys.exit(1)

if __name__ == '__main__':
    main()