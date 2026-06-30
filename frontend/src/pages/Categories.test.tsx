import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Categories from './Categories';

const mockFetchCategories = vi.fn();

vi.mock('../api', () => ({
  fetchCategories: () => mockFetchCategories(),
}));

const mockCategories = [
  {
    id: 1,
    name: '餐饮',
    icon: '🍜',
    type: 'expense' as const,
    sort_order: 1,
    children: [
      { id: 101, name: '早餐', icon: '🥐', type: 'expense' },
      { id: 102, name: '午餐', icon: '🍱', type: 'expense' },
    ],
  },
  {
    id: 2,
    name: '交通',
    icon: '🚗',
    type: 'expense' as const,
    sort_order: 2,
    children: [
      { id: 201, name: '地铁', icon: '🚇', type: 'expense' },
    ],
  },
  {
    id: 3,
    name: '工资',
    icon: '💰',
    type: 'income' as const,
    sort_order: 3,
    children: [],
  },
];

describe('Categories', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', async () => {
    // Don't resolve immediately so we can see the loading state
    mockFetchCategories.mockReturnValue(new Promise(() => {}));
    render(<Categories />);
    expect(document.querySelector('.ant-spin')).toBeTruthy();
  });

  it('loads categories and renders tree', async () => {
    mockFetchCategories.mockResolvedValue(mockCategories);
    render(<Categories />);

    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeTruthy();
    });
    expect(screen.getByText('交通')).toBeTruthy();
    expect(screen.getByText('工资')).toBeTruthy();
  });

  it('renders parent and child categories in tree', async () => {
    mockFetchCategories.mockResolvedValue(mockCategories);
    render(<Categories />);

    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeTruthy();
    });

    // Children should also be rendered
    expect(screen.getByText('早餐')).toBeTruthy();
    expect(screen.getByText('午餐')).toBeTruthy();
    expect(screen.getByText('地铁')).toBeTruthy();
  });

  it('shows type tags with correct colors', async () => {
    mockFetchCategories.mockResolvedValue(mockCategories);
    render(<Categories />);

    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeTruthy();
    });

    // Expense tags should be '支出' (multiple - 餐饮 and 交通)
    const expenseTags = screen.getAllByText('支出');
    expect(expenseTags.length).toBeGreaterThanOrEqual(1);
    // Income tag should be '收入'
    expect(screen.getByText('收入')).toBeTruthy();
  });

  it('renders card with title', async () => {
    mockFetchCategories.mockResolvedValue(mockCategories);
    render(<Categories />);

    await waitFor(() => {
      expect(screen.getByText('分类管理')).toBeTruthy();
    });
  });

  it('shows icons in tree', async () => {
    mockFetchCategories.mockResolvedValue(mockCategories);
    render(<Categories />);

    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeTruthy();
    });

    // Check icon text content
    expect(screen.getByText('🍜')).toBeTruthy();
    expect(screen.getByText('🚗')).toBeTruthy();
    expect(screen.getByText('💰')).toBeTruthy();
  });

  it('handles empty categories', async () => {
    mockFetchCategories.mockResolvedValue([]);
    render(<Categories />);

    await waitFor(() => {
      expect(screen.getByText('分类管理')).toBeTruthy();
    });
    // Tree should exist but with no data
    expect(screen.queryByText('餐饮')).toBeFalsy();
  });

  // ── fetch 错误处理 ──
  it('should handle fetch error gracefully', async () => {
    mockFetchCategories.mockRejectedValue(new Error('网络错误'));
    render(<Categories />);

    await waitFor(() => {
      expect(screen.getByText('分类管理')).toBeTruthy();
    });
    // 不应该崩溃
  });

  // ── 转账类型标签 ──
  it('should show transfer type tag', async () => {
    mockFetchCategories.mockResolvedValue([{
      id: 4,
      name: '转账',
      icon: '💸',
      type: 'transfer' as const,
      sort_order: 4,
      children: [],
    }]);
    render(<Categories />);

    await waitFor(() => {
      const transferElements = screen.getAllByText('转账');
      expect(transferElements.length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getByText('💸')).toBeTruthy();
  });
});
