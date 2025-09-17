# コーディング原則

## プログラミング原則

- **KISS (Keep It Simple, Stupid)**: コードは可能な限りシンプルに。複雑さを避け、理解・保守・テストを容易にする。
- **DRY (Don't Repeat Yourself)**: 重複を避け、一箇所で管理して可読性と保守性を高める。
- **YAGNI (You Aren't Gonna Need It)**: 必要になるまで機能や抽象を追加しない。現在必要なものに集中する。
- **SLAP (Single Level of Abstraction Principle)**: 同じ抽象レベルのコードをまとめ、読みやすくする。
- **OCP (Open/Closed Principle)**: 拡張に開き、修正に閉じる設計を目指す。
- **名前重要 (Meaningful Names)**: 変数・関数・クラスに意図が伝わる名前を付ける。
- **PIE (Abstraction, Polymorphism, Inheritance, Encapsulation)**: OOPの基礎を適切に用いて柔軟性・再利用性を高める。

## プログラミングガイドライン

- **詳細なコメント (Educational Comments)**: 「何(How)」だけでなく「なぜ(Why)」も短く添える。
- **エラーハンドリング (Robust Error Handling)**: 予期せぬ例外でも落ちない方針とログ/再試行を備える。

## 常に効果的なコア原則

- **1関数=1責務**: 説明は一文で言える大きさに分割する。
- **ネストは浅く**: 原則2段以内。可能なら早期returnで段差を減らす。
- **DRYは「読みやすさより優先しない」**: 抽象で複雑化するなら小さな重複を許容。
- **名前は意図優先**: 目的語・条件・単位などを含める。略語はチーム合意のみ。
- **公開インターフェースは安定化を重視**: 内部実装は後から整理してよい（YAGNI）。

## トレードオフの判断基準

- **衝突時の優先順位**: KISS ＞ DRY、YAGNI ＞ OCP（将来拡張の確度が十分に高い場合のみOCPを優先）
- **可読性 ＞ 早すぎる最適化**: 性能要件が証拠で示されたときだけ複雑化を許容

## レビューチェックリスト

- **MUST**: この関数は一文で説明できるか？（できなければ分割）
- **MUST**: 早期returnやガード節でネストを一段減らせるか？
- **SHOULD**: 新しい抽象は「重複の削減」より「意図の明確化」に寄与しているか？

## 例外ポリシー

### 逸脱してよいケース
- 厳しい性能要件
- レガシー互換
- 期限制約で段階的改善が必要なとき

### 補償措置（必須）
- 逸脱理由を一行コメントで明記（例：`// PERF: ～`）
- ユニットテスト or スナップショットテストを追加する
- TODOに課題番号を付けて次リリースで是正計画を残す

## 実装例

### KISS原則（Good）
```typescript
function isAdult(u?: { age?: number }) {
  if (!u?.age) return false;  // ガード節
  return u.age >= 18;
}
```

### KISS原則（Bad）
```typescript
function chk(u: any) {
  if (u != null && typeof u.age === "number" && !(u.age < 18)) {
    return true;
  }
  return false;
}
```

### DRYの過剰抽象を避ける（Good）
```typescript
function renderTitle(t: string) { 
  return <h1>{t}</h1>; 
}

function renderSubtitle(s: string) { 
  return <h2>{s}</h2>; 
} 
// ここは重複許容で読みやすさ優先
```

### エラーハンドリング（Good）
```typescript
async function fetchUser(id: string) {
  try { 
    return await api.getUser(id); 
  } catch (e) { 
    log.warn("getUser failed", {id, e}); 
    return null; 
  }
}
```