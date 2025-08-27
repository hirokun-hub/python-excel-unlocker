// shadcn/ui のユーティリティ。コンポーネントで使うクラス結合ヘルパー。
// - clsx: 複数のクラス名を結合する軽量ユーティリティ
// - tailwind-merge: Tailwind クラスの衝突を解決して最後に指定されたユーティリティを優先する
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * cn(...inputs)
 * - 複数の class 値を受け取り、clsx で結合したあと tailwind-merge で最終的な競合を解消して返す。
 * - コンポーネント内での className 組み立てに使います。
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}


