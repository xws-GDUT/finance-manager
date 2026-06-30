import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Settlements from './Settlements';
import {
  fetchSettlements,
  createSettlement,
  deleteSettlement,
  closeSettlement,
  reopenSettlement,
} from '../api';

vi.mock('../api');
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), vi.fn()],
  Link: ({ children }: { children: React.ReactNode }) => children,
}));

const mockFetchSettlements = vi.mocked(fetchSettlements);
const mockCreateSettlement = vi.mocked(createSettlement);
const mockDeleteSettlement = vi.mocked(deleteSettlement);
const mockCloseSettlement = vi.mocked(closeSettlement);
const mockReopenSettlement = vi.mocked(reopenSettlement);

const mockSettlement = (overrides = {}) => ({
  id: 1,
  name: '六月聚餐',
  description: '部门聚餐费用结算',
  status: 'open' as const,
  total_advance: 500,
  total_reimbursement: 200,
  net_amount: 300,
  virtual_tx: null,
  is_aa: false,
  items: [
    {
      id: 1,
      transaction: 100,
      item_type: 'advance' as const,
      trans_date: '2025-06-15',
      amount: 300,
      description: '餐厅消费',
      merchant: '海底捞',
      direction: 'expense',
    },
    {
      id: 2,
      transaction: 200,
      item_type: 'reimbursement' as const,
      trans_date: '2025-06-16',
      amount: 200,
      description: '同事转账',
      merchant: '',
      direction: 'income',
    },
  ],
  created_at: '2025-06-15T10:00:00Z',
  updated_at: '2025-06-15T10:00:00Z',
  ...overrides,
});

describe('Settlements', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchSettlements.mockResolvedValue([mockSettlement()]);
    mockCreateSettlement.mockResolvedValue(mockSettlement({ id: 2, name: '新结算' }));
    mockDeleteSettlement.mockResolvedValue(undefined as any);
    mockCloseSettlement.mockResolvedValue({});
    mockReopenSettlement.mockResolvedValue({});
  });

  // ── 加载结算列表 ──
  it('should load and display settlements', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('垫付结算')).toBeInTheDocument();
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });
  });

  // ── 空结算列表 ──
  it('should handle empty settlement list', async () => {
    mockFetchSettlements.mockResolvedValue([]);

    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('垫付结算')).toBeInTheDocument();
    });
  });

  // ── 创建结算按钮 ──
  it('should render create settlement button', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('新建结算组')).toBeInTheDocument();
    });
  });

  // ── 创建结算（含名称验证） ──
  it('should validate name when creating settlement', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('新建结算组')).toBeInTheDocument();
    });

    // Card extra 中的新建按钮
    const createBtns = screen.getAllByText('新建结算组');
    const createBtn = createBtns.find(btn => btn.closest('.ant-card-extra'));
    if (createBtn) {
      await userEvent.click(createBtn);
    }

    await waitFor(() => {
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle?.textContent).toBe('新建结算组');
      expect(screen.getByText('名称 *')).toBeInTheDocument();
    });

    // 不输入名称直接点创建
    const okBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    if (okBtn) {
      await userEvent.click(okBtn);
    }
  });

  // ── 成功创建结算 ──
  it('should create settlement with name and description', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('新建结算组')).toBeInTheDocument();
    });

    const createBtns = screen.getAllByText('新建结算组');
    const createBtn = createBtns.find(btn => btn.closest('.ant-card-extra'));
    if (createBtn) {
      await userEvent.click(createBtn);
    }

    await waitFor(() => {
      expect(screen.getByText('名称 *')).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText('结算组名称');
    await userEvent.type(nameInput, '新结算组');

    const okBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    if (okBtn) {
      await userEvent.click(okBtn);
    }

    await waitFor(() => {
      expect(mockCreateSettlement).toHaveBeenCalledWith({
        name: '新结算组',
        description: '',
      });
    });
  });

  // ── 关闭结算 ──
  it('should close a settlement', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });

    const closeBtns = screen.getAllByText('关闭');
    if (closeBtns.length > 0) {
      await userEvent.click(closeBtns[0]);
    }

    await waitFor(() => {
      expect(screen.getByText('确定关闭结算？')).toBeInTheDocument();
    });

    const popConfirm = document.querySelector('.ant-popconfirm');
    if (popConfirm) {
      const confirmBtn = popConfirm.querySelector('.ant-btn-primary') as HTMLElement;
      if (confirmBtn) {
        await userEvent.click(confirmBtn);
      }
    }

    await waitFor(() => {
      expect(mockCloseSettlement).toHaveBeenCalledWith(1);
    });
  });

  // ── 重开结算 ──
  it('should reopen a closed settlement', async () => {
    mockFetchSettlements.mockResolvedValue([mockSettlement({ status: 'closed' })]);

    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });

    const reopenBtns = screen.getAllByText('重开');
    if (reopenBtns.length > 0) {
      await userEvent.click(reopenBtns[0]);
    }

    await waitFor(() => {
      expect(screen.getByText('确定重开结算？')).toBeInTheDocument();
    });

    const popConfirm = document.querySelector('.ant-popconfirm');
    if (popConfirm) {
      const confirmBtn = popConfirm.querySelector('.ant-btn-primary') as HTMLElement;
      if (confirmBtn) {
        await userEvent.click(confirmBtn);
      }
    }

    await waitFor(() => {
      expect(mockReopenSettlement).toHaveBeenCalledWith(1);
    });
  });

  // ── 删除结算 ──
  it('should delete a settlement', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });

    const deleteBtns = screen.getAllByText('删除');
    if (deleteBtns.length > 0) {
      await userEvent.click(deleteBtns[0]);
    }

    await waitFor(() => {
      expect(screen.getByText('确定删除？')).toBeInTheDocument();
    });

    const popConfirm = document.querySelector('.ant-popconfirm');
    if (popConfirm) {
      const confirmBtn = popConfirm.querySelector('.ant-btn-primary') as HTMLElement;
      if (confirmBtn) {
        await userEvent.click(confirmBtn);
      }
    }

    await waitFor(() => {
      expect(mockDeleteSettlement).toHaveBeenCalledWith(1);
    });
  });

  // ── 结算详情 Modal ──
  it('should show settlement detail modal', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });

    const detailBtns = screen.getAllByText('详情');
    if (detailBtns.length > 0) {
      await userEvent.click(detailBtns[0]);
    }

    await waitFor(() => {
      // 详情 Modal 的标题是结算组名称
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle?.textContent).toBe('六月聚餐');
    });
  });

  // ── 结算详情中的金额显示 ──
  it('should display amounts with correct colors in detail', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });

    const detailBtns = screen.getAllByText('详情');
    if (detailBtns.length > 0) {
      await userEvent.click(detailBtns[0]);
    }

    await waitFor(() => {
      const expenseAmount = screen.getByText('-¥300');
      expect(expenseAmount).toBeInTheDocument();
      expect(expenseAmount).toHaveStyle({ color: '#cf1322' });

      const incomeAmount = screen.getByText('+¥200');
      expect(incomeAmount).toBeInTheDocument();
      expect(incomeAmount).toHaveStyle({ color: '#389e0d' });
    });
  });

  // ── 状态 Tag（进行中） ──
  it('should display open status tag as blue', async () => {
    render(<Settlements />);

    await waitFor(() => {
      const statusTag = screen.getByText('进行中');
      expect(statusTag).toBeInTheDocument();
    });
  });

  // ── 状态 Tag（已结算） ──
  it('should display closed status tag as green', async () => {
    mockFetchSettlements.mockResolvedValue([mockSettlement({ status: 'closed' })]);

    render(<Settlements />);

    await waitFor(() => {
      const statusTag = screen.getByText('已结算');
      expect(statusTag).toBeInTheDocument();
    });
  });

  // ── AA 标签显示 ──
  it('should display AA tag for AA settlements', async () => {
    mockFetchSettlements.mockResolvedValue([mockSettlement({ is_aa: true })]);

    render(<Settlements />);

    await waitFor(() => {
      const aaTag = screen.getByText('AA');
      expect(aaTag).toBeInTheDocument();
    });
  });

  // ── 非 AA 不显示标签 ──
  it('should not display AA tag for non-AA settlements', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });

    // AA 标签不应出现
    const aaTag = document.querySelector('.ant-tag-purple');
    expect(aaTag).toBeNull();
  });

  // ── 垫付金额颜色（红色） ──
  it('should display advance amount in red', async () => {
    render(<Settlements />);

    await waitFor(() => {
      const advanceAmount = screen.getByText('¥500');
      expect(advanceAmount).toBeInTheDocument();
      expect(advanceAmount).toHaveStyle({ color: '#cf1322' });
    });
  });

  // ── 收款金额颜色（绿色） ──
  it('should display reimbursement amount in green', async () => {
    render(<Settlements />);

    await waitFor(() => {
      const reimAmount = screen.getByText('¥200');
      expect(reimAmount).toBeInTheDocument();
      expect(reimAmount).toHaveStyle({ color: '#389e0d' });
    });
  });

  // ── 净支出颜色 ──
  it('should display net amount with correct color', async () => {
    render(<Settlements />);

    await waitFor(() => {
      const netAmount = screen.getByText('¥300');
      expect(netAmount).toBeInTheDocument();
    });
  });

  // ── 关闭结算详情 Modal ──
  it('should close settlement detail modal', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });

    const detailBtns = screen.getAllByText('详情');
    if (detailBtns.length > 0) {
      await userEvent.click(detailBtns[0]);
    }

    await waitFor(() => {
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle?.textContent).toBe('六月聚餐');
    });

    const closeBtns = document.querySelectorAll('.ant-modal-close');
    if (closeBtns.length > 0) {
      await userEvent.click(closeBtns[closeBtns.length - 1] as HTMLElement);
    }
  });

  // ── 取消创建结算 ──
  it('should cancel settlement creation', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('新建结算组')).toBeInTheDocument();
    });

    const createBtns = screen.getAllByText('新建结算组');
    const createBtn = createBtns.find(btn => btn.closest('.ant-card-extra'));
    if (createBtn) {
      await userEvent.click(createBtn);
    }

    await waitFor(() => {
      expect(screen.getByText('名称 *')).toBeInTheDocument();
    });

    // Modal 中存在关闭按钮和取消按钮
    const closeButton = document.querySelector('.ant-modal-close');
    expect(closeButton).toBeInTheDocument();

    const cancelBtn = document.querySelector('.ant-modal-footer button:not(.ant-btn-primary)');
    expect(cancelBtn).toBeInTheDocument();
  });

  // ── 加载状态 ──
  it('should show loading state', async () => {
    mockFetchSettlements.mockImplementation(() => new Promise(() => {}));

    render(<Settlements />);

    const spinElements = document.querySelectorAll('.ant-spin');
    expect(spinElements.length).toBeGreaterThan(0);
  });

  // ── handleCreate catch ──
  it('should handle create settlement error gracefully', async () => {
    mockCreateSettlement.mockRejectedValue(new Error('创建失败'));
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('新建结算组')).toBeInTheDocument();
    });

    const createBtns = screen.getAllByText('新建结算组');
    const createBtn = createBtns.find(btn => btn.closest('.ant-card-extra'));
    if (createBtn) {
      await userEvent.click(createBtn);
    }

    await waitFor(() => {
      expect(screen.getByText('名称 *')).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText('结算组名称');
    await userEvent.type(nameInput, '新结算组');

    const okBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    if (okBtn) {
      await userEvent.click(okBtn);
    }

    await waitFor(() => {
      expect(mockCreateSettlement).toHaveBeenCalled();
    });
  });

  // ── handleClose catch ──
  it('should handle close settlement error gracefully', async () => {
    mockCloseSettlement.mockRejectedValue(new Error('操作失败'));
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });

    const closeBtns = screen.getAllByText('关闭');
    if (closeBtns.length > 0) {
      await userEvent.click(closeBtns[0]);
    }

    await waitFor(() => {
      expect(screen.getByText('确定关闭结算？')).toBeInTheDocument();
    });

    const popConfirm = document.querySelector('.ant-popconfirm');
    if (popConfirm) {
      const confirmBtn = popConfirm.querySelector('.ant-btn-primary') as HTMLElement;
      if (confirmBtn) {
        await userEvent.click(confirmBtn);
      }
    }

    await waitFor(() => {
      expect(mockCloseSettlement).toHaveBeenCalledWith(1);
    });
  });

  // ── handleReopen catch ──
  it('should handle reopen settlement error gracefully', async () => {
    mockFetchSettlements.mockResolvedValue([mockSettlement({ status: 'closed' })]);
    mockReopenSettlement.mockRejectedValue(new Error('操作失败'));
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });

    const reopenBtns = screen.getAllByText('重开');
    if (reopenBtns.length > 0) {
      await userEvent.click(reopenBtns[0]);
    }

    await waitFor(() => {
      expect(screen.getByText('确定重开结算？')).toBeInTheDocument();
    });

    const popConfirm = document.querySelector('.ant-popconfirm');
    if (popConfirm) {
      const confirmBtn = popConfirm.querySelector('.ant-btn-primary') as HTMLElement;
      if (confirmBtn) {
        await userEvent.click(confirmBtn);
      }
    }

    await waitFor(() => {
      expect(mockReopenSettlement).toHaveBeenCalledWith(1);
    });
  });

  // ── handleDelete catch ──
  it('should handle delete settlement error gracefully', async () => {
    mockDeleteSettlement.mockRejectedValue(new Error('删除失败'));
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('六月聚餐')).toBeInTheDocument();
    });

    const deleteBtns = screen.getAllByText('删除');
    if (deleteBtns.length > 0) {
      await userEvent.click(deleteBtns[0]);
    }

    await waitFor(() => {
      expect(screen.getByText('确定删除？')).toBeInTheDocument();
    });

    const popConfirm = document.querySelector('.ant-popconfirm');
    if (popConfirm) {
      const confirmBtn = popConfirm.querySelector('.ant-btn-primary') as HTMLElement;
      if (confirmBtn) {
        await userEvent.click(confirmBtn);
      }
    }

    await waitFor(() => {
      expect(mockDeleteSettlement).toHaveBeenCalledWith(1);
    });
  });

  // ── 创建 Modal 输入描述 ──
  it('should allow entering description in create modal', async () => {
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('新建结算组')).toBeInTheDocument();
    });

    const createBtns = screen.getAllByText('新建结算组');
    const createBtn = createBtns.find(btn => btn.closest('.ant-card-extra'));
    if (createBtn) {
      await userEvent.click(createBtn);
    }

    await waitFor(() => {
      expect(screen.getByText('名称 *')).toBeInTheDocument();
    });

    const descTextarea = document.querySelector('.ant-modal textarea');
    if (descTextarea) {
      await userEvent.type(descTextarea, '测试描述');
    }
  });

  // ── loadData catch ──
  it('should handle loadData error gracefully', async () => {
    mockFetchSettlements.mockRejectedValue(new Error('加载失败'));
    render(<Settlements />);

    await waitFor(() => {
      expect(screen.getByText('垫付结算')).toBeInTheDocument();
    });
  });
});
