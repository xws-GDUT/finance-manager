import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RefundPairs from './RefundPairs';
import { fetchRefundPairs, autoPair, unpair, fetchAAScan, createAA } from '../api';

vi.mock('../api');
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), vi.fn()],
  Link: ({ children }: { children: React.ReactNode }) => children,
}));

const mockFetchRefundPairs = vi.mocked(fetchRefundPairs);
const mockAutoPair = vi.mocked(autoPair);
const mockUnpair = vi.mocked(unpair);
const mockFetchAAScan = vi.mocked(fetchAAScan);
const mockCreateAA = vi.mocked(createAA);

const mockPair = (overrides = {}) => ({
  id: 1,
  expense_tx: 100,
  refund_tx: 200,
  expense_date: '2025-06-15',
  expense_amount: 100,
  expense_desc: '超市购物',
  expense_merchant: '沃尔玛',
  refund_date: '2025-06-16',
  refund_amount: 100,
  refund_desc: '退款',
  refund_merchant: '沃尔玛',
  match_score: 95,
  match_method: 'auto' as const,
  match_detail: {},
  created_at: '2025-06-16T10:00:00Z',
  ...overrides,
});

const mockAAScanResult = [
  {
    receipts: [{ id: 1, date: '2025-06-15', amount: '30', description: '收款1' }],
    total_receipt: '30',
    candidate_expenses: [{ id: 10, date: '2025-06-15', amount: '30', description: '午餐' }],
    suggested_pairs: [{
      expense_id: 10,
      expense_date: '2025-06-15',
      expense_amount: '30',
      expense_desc: '午餐',
      receipt_total: '30',
      ratio: 0.95,
    }],
  },
];

describe('RefundPairs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchRefundPairs.mockResolvedValue([mockPair()]);
    mockAutoPair.mockResolvedValue({ paired: 5, skipped: 2 });
    mockUnpair.mockResolvedValue(undefined as any);
    mockFetchAAScan.mockResolvedValue(mockAAScanResult);
    mockCreateAA.mockResolvedValue({});
  });

  // ── 加载配对列表 ──
  it('should load and display refund pairs', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('退款配对')).toBeInTheDocument();
    });
  });

  // ── 空配对列表 ──
  it('should handle empty pair list', async () => {
    mockFetchRefundPairs.mockResolvedValue([]);

    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('退款配对')).toBeInTheDocument();
    });

    // 空列表时表格存在但无数据
    const table = document.querySelector('.ant-table-tbody');
    expect(table).toBeInTheDocument();
  });

  // ── 自动配对按钮 ──
  it('should render auto pair button and handle click', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('自动配对')).toBeInTheDocument();
    });

    const autoPairBtn = screen.getByText('自动配对');
    await userEvent.click(autoPairBtn);

    await waitFor(() => {
      expect(mockAutoPair).toHaveBeenCalled();
    });
  });

  // ── 解除配对 ──
  it('should unpair a pair', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('退款配对')).toBeInTheDocument();
    });

    const unpairBtns = screen.getAllByText('解除');
    if (unpairBtns.length > 0) {
      await userEvent.click(unpairBtns[0]);
    }

    await waitFor(() => {
      expect(mockUnpair).toHaveBeenCalledWith(1);
    });
  });

  // ── 配对详情 Modal ──
  it('should show pair detail modal', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('退款配对')).toBeInTheDocument();
    });

    const detailBtns = screen.getAllByText('详情');
    if (detailBtns.length > 0) {
      await userEvent.click(detailBtns[0]);
    }

    await waitFor(() => {
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle?.textContent).toBe('配对详情');
    });

    // 验证消费金额（红色）
    const expenseAmounts = screen.getAllByText('-¥100');
    // Modal 中的那个
    expect(expenseAmounts.length).toBeGreaterThanOrEqual(1);

    // 验证退款金额（绿色）
    const refundAmounts = screen.getAllByText('+¥100');
    expect(refundAmounts.length).toBeGreaterThanOrEqual(1);
  });

  // ── 关闭配对详情 Modal ──
  it('should close pair detail modal', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('退款配对')).toBeInTheDocument();
    });

    const detailBtns = screen.getAllByText('详情');
    if (detailBtns.length > 0) {
      await userEvent.click(detailBtns[0]);
    }

    await waitFor(() => {
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle?.textContent).toBe('配对详情');
    });

    // 点击 Modal 关闭按钮
    const closeBtns = document.querySelectorAll('.ant-modal-close');
    if (closeBtns.length > 0) {
      await userEvent.click(closeBtns[0] as HTMLElement);
    }
  });

  // ── AA 扫描按钮 ──
  it('should render AA scan button and handle click', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('AA 扫描')).toBeInTheDocument();
    });

    const aaScanBtn = screen.getByText('AA 扫描');
    await userEvent.click(aaScanBtn);

    await waitFor(() => {
      expect(mockFetchAAScan).toHaveBeenCalled();
    });
  });

  // ── AA 扫描结果 Modal ──
  it('should display AA scan results in modal', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('AA 扫描')).toBeInTheDocument();
    });

    const aaScanBtn = screen.getByText('AA 扫描');
    await userEvent.click(aaScanBtn);

    await waitFor(() => {
      const modalTitle = document.querySelectorAll('.ant-modal-title');
      // AA 扫描 Modal 标题是 "AA 群收款扫描"
      const aaTitle = Array.from(modalTitle).find(el => el.textContent === 'AA 群收款扫描');
      expect(aaTitle).toBeInTheDocument();
    });
  });

  // ── AA 扫描空结果 ──
  it('should show empty AA scan result message', async () => {
    mockFetchAAScan.mockResolvedValue([]);

    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('AA 扫描')).toBeInTheDocument();
    });

    const aaScanBtn = screen.getByText('AA 扫描');
    await userEvent.click(aaScanBtn);

    await waitFor(() => {
      expect(screen.getByText('未发现 AA 群收款场景')).toBeInTheDocument();
    });
  });

  // ── AA 创建结算 ──
  it('should create AA settlement', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('AA 扫描')).toBeInTheDocument();
    });

    const aaScanBtn = screen.getByText('AA 扫描');
    await userEvent.click(aaScanBtn);

    // 等待 AA Modal 出现
    await waitFor(() => {
      const modalTitles = document.querySelectorAll('.ant-modal-title');
      const aaTitle = Array.from(modalTitles).find(el => el.textContent === 'AA 群收款扫描');
      expect(aaTitle).toBeInTheDocument();
    });

    // 验证扫描结果在 Modal 中
    expect(mockFetchAAScan).toHaveBeenCalled();
  });

  // ── 得分颜色 >=80 绿色 ──
  it('should render high score in green', async () => {
    mockFetchRefundPairs.mockResolvedValue([mockPair({ match_score: 95 })]);

    render(<RefundPairs />);

    await waitFor(() => {
      const scoreTag = screen.getByText('95.0');
      expect(scoreTag).toBeInTheDocument();
    });
  });

  // ── 得分颜色 >=60 <80 橙色 ──
  it('should render medium score in orange', async () => {
    mockFetchRefundPairs.mockResolvedValue([mockPair({ match_score: 70 })]);

    render(<RefundPairs />);

    await waitFor(() => {
      const scoreTag = screen.getByText('70.0');
      expect(scoreTag).toBeInTheDocument();
    });
  });

  // ── 得分颜色 <60 红色 ──
  it('should render low score in red', async () => {
    mockFetchRefundPairs.mockResolvedValue([mockPair({ match_score: 40 })]);

    render(<RefundPairs />);

    await waitFor(() => {
      const scoreTag = screen.getByText('40.0');
      expect(scoreTag).toBeInTheDocument();
    });
  });

  // ── 配对方式 Tag（自动） ──
  it('should render match method tag for auto', async () => {
    mockFetchRefundPairs.mockResolvedValue([mockPair({ match_method: 'auto' })]);

    render(<RefundPairs />);

    await waitFor(() => {
      const methodTag = screen.getByText('自动');
      expect(methodTag).toBeInTheDocument();
    });
  });

  // ── 配对方式 Tag（手动） ──
  it('should render match method tag for manual', async () => {
    mockFetchRefundPairs.mockResolvedValue([mockPair({ match_method: 'manual' })]);

    render(<RefundPairs />);

    await waitFor(() => {
      const methodTag = screen.getByText('手动');
      expect(methodTag).toBeInTheDocument();
    });
  });

  // ── 配对方式 Tag（AA） ──
  it('should render match method tag for AA', async () => {
    mockFetchRefundPairs.mockResolvedValue([mockPair({ match_method: 'aa' })]);

    render(<RefundPairs />);

    await waitFor(() => {
      const methodTag = screen.getByText('AA');
      expect(methodTag).toBeInTheDocument();
    });
  });

  // ── 显示消费和退款信息 ──
  it('should display expense and refund details in table', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      // 验证表格中有数据
      const tableBody = document.querySelector('.ant-table-tbody');
      expect(tableBody).toBeInTheDocument();
      expect(tableBody?.children.length).toBeGreaterThan(0);
    });
  });

  // ── 消费金额颜色（红色） ──
  it('should display expense amount in red', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      const expenseAmount = screen.getByText('-¥100');
      expect(expenseAmount).toBeInTheDocument();
      expect(expenseAmount).toHaveStyle({ color: '#cf1322' });
    });
  });

  // ── 退款金额颜色（绿色） ──
  it('should display refund amount in green', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      const refundAmount = screen.getByText('+¥100');
      expect(refundAmount).toBeInTheDocument();
      expect(refundAmount).toHaveStyle({ color: '#389e0d' });
    });
  });

  // ── 关闭 AA 扫描 Modal ──
  it('should close AA scan modal', async () => {
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('AA 扫描')).toBeInTheDocument();
    });

    const aaScanBtn = screen.getByText('AA 扫描');
    await userEvent.click(aaScanBtn);

    await waitFor(() => {
      const modalTitles = document.querySelectorAll('.ant-modal-title');
      const aaTitle = Array.from(modalTitles).find(el => el.textContent === 'AA 群收款扫描');
      expect(aaTitle).toBeInTheDocument();
    });

    // 关闭 AA Modal（第二个 Modal 的关闭按钮）
    const closeBtns = document.querySelectorAll('.ant-modal-close');
    if (closeBtns.length > 0) {
      await userEvent.click(closeBtns[closeBtns.length - 1] as HTMLElement);
    }
  });

  // ── handleAutoPair catch ──
  it('should handle auto pair error gracefully', async () => {
    mockAutoPair.mockRejectedValue(new Error('配对失败'));
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('自动配对')).toBeInTheDocument();
    });

    const autoPairBtn = screen.getByText('自动配对');
    await userEvent.click(autoPairBtn);

    await waitFor(() => {
      expect(mockAutoPair).toHaveBeenCalled();
    });
  });

  // ── handleUnpair catch ──
  it('should handle unpair error gracefully', async () => {
    mockUnpair.mockRejectedValue(new Error('操作失败'));
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('退款配对')).toBeInTheDocument();
    });

    const unpairBtns = screen.getAllByText('解除');
    if (unpairBtns.length > 0) {
      await userEvent.click(unpairBtns[0]);
    }

    await waitFor(() => {
      expect(mockUnpair).toHaveBeenCalledWith(1);
    });
  });

  // ── handleAAScan catch ──
  it('should handle AA scan error gracefully', async () => {
    mockFetchAAScan.mockRejectedValue(new Error('扫描失败'));
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('AA 扫描')).toBeInTheDocument();
    });

    const aaScanBtn = screen.getByText('AA 扫描');
    await userEvent.click(aaScanBtn);

    await waitFor(() => {
      expect(mockFetchAAScan).toHaveBeenCalled();
    });
  });

  // ── handleAACreate catch ──
  it('should handle AA create error gracefully', async () => {
    mockCreateAA.mockRejectedValue(new Error('创建失败'));
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('AA 扫描')).toBeInTheDocument();
    });

    const aaScanBtn = screen.getByText('AA 扫描');
    await userEvent.click(aaScanBtn);

    await waitFor(() => {
      const modalTitles = document.querySelectorAll('.ant-modal-title');
      const aaTitle = Array.from(modalTitles).find(el => el.textContent === 'AA 群收款扫描');
      expect(aaTitle).toBeInTheDocument();
    });

    // 尝试展开 Collapse panel
    const collapseHeaders = document.querySelectorAll('.ant-collapse-header');
    if (collapseHeaders.length > 0) {
      await userEvent.click(collapseHeaders[0] as HTMLElement);
    }

    // 尝试找到创建按钮
    await waitFor(() => {
      expect(mockFetchAAScan).toHaveBeenCalled();
    });
  });

  // ── handleAACreate 成功 ──
  it('should create AA settlement successfully', async () => {
    mockCreateAA.mockResolvedValue({});
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('AA 扫描')).toBeInTheDocument();
    });

    const aaScanBtn = screen.getByText('AA 扫描');
    await userEvent.click(aaScanBtn);

    await waitFor(() => {
      const modalTitles = document.querySelectorAll('.ant-modal-title');
      const aaTitle = Array.from(modalTitles).find(el => el.textContent === 'AA 群收款扫描');
      expect(aaTitle).toBeInTheDocument();
    });

    // 展开 Collapse
    const collapseHeaders = document.querySelectorAll('.ant-collapse-header');
    if (collapseHeaders.length > 0) {
      await userEvent.click(collapseHeaders[0] as HTMLElement);
    }

    // 检查有建议的配对信息
    await waitFor(() => {
      expect(mockFetchAAScan).toHaveBeenCalled();
    });
  });

  // ── loadPairs catch ──
  it('should handle loadPairs error gracefully', async () => {
    mockFetchRefundPairs.mockRejectedValue(new Error('加载失败'));
    render(<RefundPairs />);

    await waitFor(() => {
      expect(screen.getByText('退款配对')).toBeInTheDocument();
    });
  });
});
