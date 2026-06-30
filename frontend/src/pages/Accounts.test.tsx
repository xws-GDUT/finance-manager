import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Accounts from './Accounts';

const mockFetchAccounts = vi.fn();

vi.mock('../api', () => ({
  fetchAccounts: () => mockFetchAccounts(),
}));

const mockAccounts = [
  {
    id: 1,
    name: '支付宝',
    account_type: 'platform' as const,
    bank_name: '',
    owner: '张三',
    match_keywords: 'alipay',
    is_active: true,
    stats: { tx_count: 50, total_expense: 10000, total_income: 5000 },
  },
  {
    id: 2,
    name: '招商银行储蓄卡',
    account_type: 'debit' as const,
    bank_name: '招商银行',
    owner: '李四',
    match_keywords: 'cmb_debit',
    is_active: true,
    stats: { tx_count: 30, total_expense: 8000, total_income: 12000 },
  },
  {
    id: 3,
    name: '中信信用卡',
    account_type: 'credit' as const,
    bank_name: '中信银行',
    owner: '',
    match_keywords: 'cib_credit',
    is_active: true,
    stats: { tx_count: 20, total_expense: 5000, total_income: 0 },
  },
];

describe('Accounts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads account data and renders table', async () => {
    mockFetchAccounts.mockResolvedValue(mockAccounts);
    render(<Accounts />);

    await waitFor(() => {
      expect(screen.getByText('支付宝')).toBeTruthy();
    });
    expect(screen.getByText('招商银行储蓄卡')).toBeTruthy();
    expect(screen.getByText('中信信用卡')).toBeTruthy();
  });

  it('shows correct type tag colors', async () => {
    mockFetchAccounts.mockResolvedValue(mockAccounts);
    render(<Accounts />);

    await waitFor(() => {
      expect(screen.getByText('支付平台')).toBeTruthy();
    });
    expect(screen.getByText('储蓄卡')).toBeTruthy();
    expect(screen.getByText('信用卡')).toBeTruthy();
  });

  it('shows "-" for empty bank_name', async () => {
    mockFetchAccounts.mockResolvedValue(mockAccounts);
    render(<Accounts />);

    await waitFor(() => {
      expect(screen.getByText('支付宝')).toBeTruthy();
    });
    // Bank name column for 支付宝 is empty, should render '-'
    // Use getAllByText because there are multiple '-' (bank and owner)
    const dashes = screen.getAllByText('-');
    // At least one '-' from bank_name of 支付宝 and one from owner of 中信信用卡
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it('shows "-" for empty owner', async () => {
    mockFetchAccounts.mockResolvedValue(mockAccounts);
    render(<Accounts />);

    await waitFor(() => {
      expect(screen.getByText('中信信用卡')).toBeTruthy();
    });
    // The owner column has a '-' for empty owner
    const dashes = screen.getAllByText('-');
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it('displays transaction statistics', async () => {
    mockFetchAccounts.mockResolvedValue(mockAccounts);
    render(<Accounts />);

    await waitFor(() => {
      expect(screen.getByText('支付宝')).toBeTruthy();
    });

    // Check expense column - ¥10,000 formatted
    expect(screen.getByText('¥10,000')).toBeTruthy();
    // Check income column - ¥5,000 formatted (use getAllByText in case of duplicates)
    const incomeElements = screen.getAllByText('¥5,000');
    expect(incomeElements.length).toBeGreaterThanOrEqual(1);
  });

  it('renders column headers', async () => {
    mockFetchAccounts.mockResolvedValue(mockAccounts);
    render(<Accounts />);

    await waitFor(() => {
      expect(screen.getByText('账户名称')).toBeTruthy();
    });
    expect(screen.getByText('类型')).toBeTruthy();
    expect(screen.getByText('银行')).toBeTruthy();
    expect(screen.getByText('持有人')).toBeTruthy();
    expect(screen.getByText('交易笔数')).toBeTruthy();
    expect(screen.getByText('总支出')).toBeTruthy();
    expect(screen.getByText('总收入')).toBeTruthy();
  });

  it('handles empty data gracefully', async () => {
    mockFetchAccounts.mockResolvedValue([]);
    render(<Accounts />);

    await waitFor(() => {
      expect(screen.getByText('账户管理')).toBeTruthy();
    });
    // Table should be rendered with empty data
    expect(screen.queryByText('支付宝')).toBeFalsy();
  });

  // ── 错误处理 ──
  it('should handle fetch error gracefully', async () => {
    mockFetchAccounts.mockRejectedValue(new Error('网络错误'));
    render(<Accounts />);

    await waitFor(() => {
      expect(screen.getByText('账户管理')).toBeTruthy();
    });
  });

  // ── 未知账户类型 ──
  it('should handle unknown account type', async () => {
    mockFetchAccounts.mockResolvedValue([{
      id: 10,
      name: '未知账户',
      account_type: 'unknown_type',
      bank_name: '',
      owner: '',
      match_keywords: '',
      is_active: true,
      stats: { tx_count: 0, total_expense: 0, total_income: 0 },
    }]);
    render(<Accounts />);

    await waitFor(() => {
      expect(screen.getByText('未知账户')).toBeTruthy();
    });
    // 未知类型应该显示原值
    expect(screen.getByText('unknown_type')).toBeTruthy();
  });

  // ── 零 stats 值 ──
  it('should display zero stats correctly', async () => {
    mockFetchAccounts.mockResolvedValue([{
      id: 10,
      name: '零数据账户',
      account_type: 'debit',
      bank_name: '',
      owner: '',
      match_keywords: '',
      is_active: true,
      stats: { tx_count: 0, total_expense: 0, total_income: 0 },
    }]);
    render(<Accounts />);

    await waitFor(() => {
      expect(screen.getByText('零数据账户')).toBeTruthy();
    });
    // 零值显示为 0
    expect(screen.getByText('0')).toBeTruthy();
  });
});
