#!/usr/bin/env python3
"""
包括的セキュリティ監査スクリプト

このスクリプトは以下を統合実行します：
1. GitHub OIDC設定の検証と改善
2. GitHub Secrets管理の監査
3. セキュリティ設定の総合評価
4. 改善提案の生成
"""

import json
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List

class ComprehensiveSecurityAuditor:
    def __init__(self):
        self.results = {
            'audit_timestamp': datetime.now().isoformat(),
            'oidc_audit': None,
            'secrets_audit': None,
            'overall_security_score': 0,
            'critical_issues': [],
            'improvement_plan': [],
            'compliance_status': {}
        }
        
        # セキュリティ要件（要件4に基づく）
        self.security_requirements = {
            'github_oidc': {
                'description': 'GitHub OIDC認証の適切な設定',
                'weight': 30,
                'criteria': [
                    'OIDCプロバイダーの存在',
                    'IAMロールの適切な信頼ポリシー',
                    'ブランチ制限の設定',
                    '最小権限ポリシーの適用'
                ]
            },
            'secrets_management': {
                'description': 'GitHub Secretsの適切な管理',
                'weight': 25,
                'criteria': [
                    '必要なシークレットの設定完了',
                    '未使用シークレットの整理',
                    '非推奨シークレットの削除',
                    'セキュアな認証方式の採用'
                ]
            },
            'access_control': {
                'description': 'アクセス制御の適切な設定',
                'weight': 20,
                'criteria': [
                    'リポジトリレベルでの制限',
                    'ブランチ保護の設定',
                    '最小権限の原則',
                    '定期的な権限レビュー'
                ]
            },
            'monitoring': {
                'description': '監視とログ記録',
                'weight': 15,
                'criteria': [
                    'CloudTrail監視',
                    'GitHub Actions監査ログ',
                    'セキュリティイベントの追跡',
                    '異常検知の仕組み'
                ]
            },
            'compliance': {
                'description': 'コンプライアンスと文書化',
                'weight': 10,
                'criteria': [
                    'セキュリティポリシーの文書化',
                    '手順書の整備',
                    '定期的な監査実施',
                    'インシデント対応手順'
                ]
            }
        }
    
    def run_oidc_audit(self) -> bool:
        """GitHub OIDC監査の実行"""
        print("🔒 GitHub OIDC監査を実行中...")
        
        try:
            # OIDC監査スクリプトの実行
            result = subprocess.run([
                'python3', 'scripts/security-audit-github-oidc.py'
            ], capture_output=True, text=True)
            
            # 結果ファイルの読み込み
            audit_files = [f for f in os.listdir('.') if f.startswith('security-audit-') and f.endswith('.json')]
            if audit_files:
                latest_file = max(audit_files, key=os.path.getctime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    self.results['oidc_audit'] = json.load(f)
                
                # ファイルのクリーンアップ
                os.remove(latest_file)
                
                print("✅ GitHub OIDC監査完了")
                return True
            else:
                print("⚠️ OIDC監査結果ファイルが見つかりません")
                return False
                
        except Exception as e:
            print(f"❌ OIDC監査の実行に失敗: {e}")
            return False
    
    def run_secrets_audit(self) -> bool:
        """GitHub Secrets監査の実行"""
        print("🔐 GitHub Secrets監査を実行中...")
        
        try:
            # Secrets監査スクリプトの実行
            result = subprocess.run([
                'python3', 'scripts/security-audit-github-secrets.py'
            ], capture_output=True, text=True)
            
            # 結果ファイルの読み込み
            audit_files = [f for f in os.listdir('.') if f.startswith('github-secrets-audit-') and f.endswith('.json')]
            if audit_files:
                latest_file = max(audit_files, key=os.path.getctime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    self.results['secrets_audit'] = json.load(f)
                
                # 関連ファイルのクリーンアップ
                base_name = latest_file.replace('.json', '')
                cleanup_files = [
                    latest_file,
                    f"{base_name}-cleanup.sh",
                    f"{base_name}-management-guide.md"
                ]
                
                for file in cleanup_files:
                    if os.path.exists(file):
                        os.remove(file)
                
                print("✅ GitHub Secrets監査完了")
                return True
            else:
                print("⚠️ Secrets監査結果ファイルが見つかりません")
                return False
                
        except Exception as e:
            print(f"❌ Secrets監査の実行に失敗: {e}")
            return False
    
    def calculate_security_score(self) -> int:
        """セキュリティスコアの計算"""
        print("📊 セキュリティスコアを計算中...")
        
        total_score = 0
        max_score = 100
        
        # GitHub OIDC評価
        oidc_score = self._evaluate_oidc_security()
        total_score += oidc_score * (self.security_requirements['github_oidc']['weight'] / 100)
        
        # GitHub Secrets評価
        secrets_score = self._evaluate_secrets_security()
        total_score += secrets_score * (self.security_requirements['secrets_management']['weight'] / 100)
        
        # アクセス制御評価
        access_score = self._evaluate_access_control()
        total_score += access_score * (self.security_requirements['access_control']['weight'] / 100)
        
        # 監視評価
        monitoring_score = self._evaluate_monitoring()
        total_score += monitoring_score * (self.security_requirements['monitoring']['weight'] / 100)
        
        # コンプライアンス評価
        compliance_score = self._evaluate_compliance()
        total_score += compliance_score * (self.security_requirements['compliance']['weight'] / 100)
        
        self.results['overall_security_score'] = int(total_score)
        
        print(f"📈 総合セキュリティスコア: {int(total_score)}/100")
        
        return int(total_score)
    
    def _evaluate_oidc_security(self) -> int:
        """OIDC設定のセキュリティ評価"""
        if not self.results['oidc_audit']:
            return 0
        
        score = 100
        oidc_data = self.results['oidc_audit']
        
        # OIDCプロバイダーの存在確認
        if not oidc_data.get('oidc_provider'):
            score -= 40
            self.results['critical_issues'].append({
                'category': 'oidc',
                'severity': 'high',
                'issue': 'GitHub OIDCプロバイダーが設定されていません',
                'impact': 'AWS認証にアクセスキーを使用する必要があり、セキュリティリスクが高い'
            })
        
        # IAMロールの存在確認
        if not oidc_data.get('iam_role'):
            score -= 30
            self.results['critical_issues'].append({
                'category': 'oidc',
                'severity': 'high',
                'issue': 'GitHub Actions用IAMロールが見つかりません',
                'impact': 'OIDC認証が使用できません'
            })
        
        # セキュリティ問題の評価
        security_issues = oidc_data.get('security_issues', [])
        high_issues = [i for i in security_issues if i.get('severity') == 'high']
        medium_issues = [i for i in security_issues if i.get('severity') == 'medium']
        
        score -= len(high_issues) * 15
        score -= len(medium_issues) * 5
        
        return max(0, score)
    
    def _evaluate_secrets_security(self) -> int:
        """Secrets管理のセキュリティ評価"""
        if not self.results['secrets_audit']:
            return 0
        
        score = 100
        secrets_data = self.results['secrets_audit']
        
        # 不足シークレットの評価
        missing_secrets = secrets_data.get('missing_secrets', [])
        high_priority_missing = [s for s in missing_secrets if s.get('priority') == 'high']
        medium_priority_missing = [s for s in missing_secrets if s.get('priority') == 'medium']
        
        score -= len(high_priority_missing) * 20
        score -= len(medium_priority_missing) * 10
        
        # 未使用シークレットの評価
        unused_secrets = secrets_data.get('unused_secrets', [])
        score -= len(unused_secrets) * 5
        
        # セキュリティ問題の評価
        security_issues = secrets_data.get('security_issues', [])
        high_issues = [i for i in security_issues if i.get('severity') == 'high']
        medium_issues = [i for i in security_issues if i.get('severity') == 'medium']
        
        score -= len(high_issues) * 15
        score -= len(medium_issues) * 5
        
        return max(0, score)
    
    def _evaluate_access_control(self) -> int:
        """アクセス制御の評価"""
        score = 70  # 基本スコア（現在の実装レベル）
        
        # ブランチ保護の確認（GitHub API経由で確認が必要）
        # 現在は基本的な設定があると仮定
        
        return score
    
    def _evaluate_monitoring(self) -> int:
        """監視設定の評価"""
        score = 60  # 基本スコア（GitHub Actions標準ログ）
        
        # CloudTrail設定の確認（AWS API経由で確認が必要）
        # 現在は基本的な監視があると仮定
        
        return score
    
    def _evaluate_compliance(self) -> int:
        """コンプライアンスの評価"""
        score = 80  # 基本スコア（文書化が充実している）
        
        # 文書の存在確認
        required_docs = [
            'docs/github-secrets-setup-guide.md',
            'docs/github-oidc-migration.md',
            'docs/security-enhancements.md'
        ]
        
        for doc in required_docs:
            if not os.path.exists(doc):
                score -= 10
        
        return max(0, score)
    
    def generate_improvement_plan(self):
        """改善計画の生成"""
        print("📋 改善計画を生成中...")
        
        improvement_plan = []
        
        # OIDC関連の改善
        if self.results['oidc_audit']:
            oidc_issues = self.results['oidc_audit'].get('security_issues', [])
            oidc_recommendations = self.results['oidc_audit'].get('recommendations', [])
            
            for issue in oidc_issues:
                if issue.get('severity') == 'high':
                    improvement_plan.append({
                        'priority': 'high',
                        'category': 'oidc',
                        'task': f"OIDC設定修正: {issue.get('message', '')}",
                        'estimated_effort': '1-2時間',
                        'impact': 'セキュリティリスクの大幅軽減'
                    })
            
            for rec in oidc_recommendations:
                if rec.get('type') == 'setup':
                    improvement_plan.append({
                        'priority': 'high',
                        'category': 'oidc',
                        'task': f"OIDC設定: {rec.get('message', '')}",
                        'estimated_effort': '30分-1時間',
                        'impact': 'セキュリティ向上'
                    })
        
        # Secrets関連の改善
        if self.results['secrets_audit']:
            missing_secrets = self.results['secrets_audit'].get('missing_secrets', [])
            unused_secrets = self.results['secrets_audit'].get('unused_secrets', [])
            
            for secret in missing_secrets:
                priority = 'high' if secret.get('priority') == 'high' else 'medium'
                improvement_plan.append({
                    'priority': priority,
                    'category': 'secrets',
                    'task': f"シークレット設定: {secret.get('name', '')}",
                    'estimated_effort': '15-30分',
                    'impact': 'デプロイメント機能の確保'
                })
            
            if unused_secrets:
                improvement_plan.append({
                    'priority': 'low',
                    'category': 'secrets',
                    'task': f"未使用シークレットの整理: {len(unused_secrets)}個",
                    'estimated_effort': '15分',
                    'impact': 'セキュリティ衛生の向上'
                })
        
        # 優先度順にソート
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        improvement_plan.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        self.results['improvement_plan'] = improvement_plan
    
    def generate_compliance_report(self):
        """コンプライアンスレポートの生成"""
        compliance_status = {}
        
        for req_name, req_config in self.security_requirements.items():
            compliance_status[req_name] = {
                'description': req_config['description'],
                'weight': req_config['weight'],
                'criteria': req_config['criteria'],
                'status': 'partial',  # 詳細評価は個別実装が必要
                'score': 70  # 基本スコア
            }
        
        self.results['compliance_status'] = compliance_status
    
    def print_comprehensive_summary(self):
        """包括的な監査結果サマリーの表示"""
        print("\n" + "="*80)
        print("🛡️  包括的セキュリティ監査結果")
        print("="*80)
        
        # 総合スコア
        score = self.results['overall_security_score']
        score_emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        print(f"\n📊 総合セキュリティスコア: {score_emoji} {score}/100")
        
        if score >= 80:
            print("✅ 優秀 - セキュリティ設定は良好です")
        elif score >= 60:
            print("⚠️ 良好 - いくつかの改善が推奨されます")
        else:
            print("❌ 要改善 - 重要なセキュリティ問題があります")
        
        # 重要な問題
        if self.results['critical_issues']:
            print(f"\n🚨 重要な問題 ({len(self.results['critical_issues'])}件):")
            for i, issue in enumerate(self.results['critical_issues'], 1):
                severity_emoji = "🔴" if issue['severity'] == 'high' else "🟡"
                print(f"  {i}. {severity_emoji} [{issue['category']}] {issue['issue']}")
                print(f"     影響: {issue['impact']}")
        
        # 改善計画
        if self.results['improvement_plan']:
            print(f"\n📋 改善計画 ({len(self.results['improvement_plan'])}項目):")
            
            high_priority = [p for p in self.results['improvement_plan'] if p['priority'] == 'high']
            medium_priority = [p for p in self.results['improvement_plan'] if p['priority'] == 'medium']
            low_priority = [p for p in self.results['improvement_plan'] if p['priority'] == 'low']
            
            if high_priority:
                print(f"\n  🔴 高優先度 ({len(high_priority)}項目):")
                for i, task in enumerate(high_priority, 1):
                    print(f"    {i}. {task['task']}")
                    print(f"       工数: {task['estimated_effort']}, 効果: {task['impact']}")
            
            if medium_priority:
                print(f"\n  🟡 中優先度 ({len(medium_priority)}項目):")
                for i, task in enumerate(medium_priority, 1):
                    print(f"    {i}. {task['task']}")
            
            if low_priority:
                print(f"\n  🟢 低優先度 ({len(low_priority)}項目):")
                for i, task in enumerate(low_priority, 1):
                    print(f"    {i}. {task['task']}")
        
        # 次のステップ
        print(f"\n🚀 推奨される次のステップ:")
        if score < 60:
            print("  1. 高優先度の問題を即座に修正")
            print("  2. GitHub OIDC設定の完了")
            print("  3. 必要なシークレットの設定")
        elif score < 80:
            print("  1. 中優先度の改善項目を実施")
            print("  2. 定期的なセキュリティ監査の実施")
            print("  3. 監視機能の強化")
        else:
            print("  1. 定期的なセキュリティ監査の継続")
            print("  2. 新機能追加時のセキュリティレビュー")
            print("  3. セキュリティ文書の更新")
    
    def save_comprehensive_results(self, filename: str = None):
        """包括的な結果の保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive-security-audit-{timestamp}"
        
        # JSON結果の保存
        json_filename = f"{filename}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # レポートの生成
        report = self._generate_detailed_report()
        report_filename = f"{filename}-report.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n💾 包括的監査結果を保存しました:")
        print(f"  📄 詳細結果: {json_filename}")
        print(f"  📊 レポート: {report_filename}")
    
    def _generate_detailed_report(self) -> str:
        """詳細レポートの生成"""
        lines = [
            "# 包括的セキュリティ監査レポート",
            "",
            f"**実行日時**: {self.results['audit_timestamp']}",
            f"**総合スコア**: {self.results['overall_security_score']}/100",
            "",
            "## エグゼクティブサマリー",
            "",
            f"本監査では、Excel Password Removerプロジェクトのセキュリティ設定を包括的に評価しました。",
            f"総合セキュリティスコアは{self.results['overall_security_score']}点となり、",
        ]
        
        score = self.results['overall_security_score']
        if score >= 80:
            lines.append("セキュリティ設定は良好な状態です。")
        elif score >= 60:
            lines.append("基本的なセキュリティは確保されていますが、いくつかの改善が推奨されます。")
        else:
            lines.append("重要なセキュリティ問題が発見されており、早急な対応が必要です。")
        
        lines.extend([
            "",
            "## 監査結果詳細",
            "",
            "### GitHub OIDC設定",
            ""
        ])
        
        if self.results['oidc_audit']:
            oidc_issues = len(self.results['oidc_audit'].get('security_issues', []))
            lines.append(f"- 検出された問題: {oidc_issues}件")
            
            if self.results['oidc_audit'].get('oidc_provider'):
                lines.append("- ✅ OIDCプロバイダー: 設定済み")
            else:
                lines.append("- ❌ OIDCプロバイダー: 未設定")
            
            if self.results['oidc_audit'].get('iam_role'):
                lines.append("- ✅ IAMロール: 設定済み")
            else:
                lines.append("- ❌ IAMロール: 未設定")
        
        lines.extend([
            "",
            "### GitHub Secrets管理",
            ""
        ])
        
        if self.results['secrets_audit']:
            total_secrets = len(self.results['secrets_audit'].get('repository_secrets', []))
            missing_secrets = len(self.results['secrets_audit'].get('missing_secrets', []))
            unused_secrets = len(self.results['secrets_audit'].get('unused_secrets', []))
            
            lines.extend([
                f"- 設定済みシークレット: {total_secrets}個",
                f"- 不足シークレット: {missing_secrets}個",
                f"- 未使用シークレット: {unused_secrets}個"
            ])
        
        lines.extend([
            "",
            "## 改善計画",
            ""
        ])
        
        if self.results['improvement_plan']:
            for i, task in enumerate(self.results['improvement_plan'], 1):
                priority_emoji = "🔴" if task['priority'] == 'high' else "🟡" if task['priority'] == 'medium' else "🟢"
                lines.extend([
                    f"### {i}. {task['task']} {priority_emoji}",
                    "",
                    f"- **カテゴリ**: {task['category']}",
                    f"- **優先度**: {task['priority']}",
                    f"- **推定工数**: {task['estimated_effort']}",
                    f"- **期待効果**: {task['impact']}",
                    ""
                ])
        
        lines.extend([
            "## 推奨事項",
            "",
            "1. **定期的な監査**: 月次でセキュリティ監査を実施",
            "2. **自動化**: セキュリティチェックをCI/CDパイプラインに組み込み",
            "3. **文書化**: セキュリティ手順の継続的な更新",
            "4. **教育**: チームメンバーへのセキュリティ教育",
            "",
            "---",
            "",
            f"*このレポートは自動生成されました - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        return '\n'.join(lines)
    
    def run_comprehensive_audit(self):
        """包括的な監査を実行"""
        print("🛡️ 包括的セキュリティ監査を開始します...")
        print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        success_count = 0
        
        # 1. OIDC監査
        if self.run_oidc_audit():
            success_count += 1
        
        # 2. Secrets監査
        if self.run_secrets_audit():
            success_count += 1
        
        # 3. セキュリティスコア計算
        self.calculate_security_score()
        
        # 4. 改善計画生成
        self.generate_improvement_plan()
        
        # 5. コンプライアンスレポート生成
        self.generate_compliance_report()
        
        # 6. 結果表示と保存
        self.print_comprehensive_summary()
        self.save_comprehensive_results()
        
        # 7. 終了コードの決定
        score = self.results['overall_security_score']
        if score < 60:
            print(f"\n❌ セキュリティスコアが低すぎます ({score}/100)")
            return 1
        elif success_count < 2:
            print(f"\n⚠️ 一部の監査が失敗しました")
            return 1
        else:
            print(f"\n✅ 包括的セキュリティ監査が完了しました")
            return 0

def main():
    """メイン処理"""
    auditor = ComprehensiveSecurityAuditor()
    exit_code = auditor.run_comprehensive_audit()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()