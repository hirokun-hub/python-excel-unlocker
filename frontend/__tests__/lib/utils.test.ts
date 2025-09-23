import { cn } from '@/lib/utils';

describe('cn ユーティリティ', () => {
  it('複数のクラスを結合しTailwind競合を解決する', () => {
    const result = cn('px-2', 'text-sm', ['px-2', { hidden: false, block: true }]);
    expect(result).toBe('text-sm px-2 block');
  });
});
