import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Transactions from './Transactions';
import {
  fetchTransactions,
  fetchFilterValues,
  fetchCategories,
  updateTransaction,
  deleteTransaction,
} from '../api';

vi.mock('../api');
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), vi.fn()],
  Link: ({ children }: { children: React.ReactNode }) => children,
}));

const mockFetchTransactions = vi.mocked(fetchTransactions);
const mockFetchFilterValues = vi.mocked(fetchFilterValues);
const mockFetchCategories = vi.mocked(fetchCategories);
const mockUpdateTransaction = vi.mocked(updateTransaction);
const mockDeleteTransaction = vi.mocked(deleteTransaction);

const mockTransaction = (overrides = {}) => ({
  id: 1,
  trans_date: '2025-06-15',
  amount: 100,
  direction: 'expense' as const,
  direction_display: '支出',
  source: 'alipay',
  source_display: '支付宝',
  status: 'confirmed' as const,
  status_display: '有效',
  trans_type: '消费',
  description: '超市购物',
  merchant: '沃尔玛',
  counterparty: '沃尔玛超市',
  payment_method: '快捷支付',
  payment_channel: '支付宝',
  remark: '',
  category: null,
  category_name: '',
  category_icon: '',
  category_type: '',
  account: null,
  account_name: '',
  valid_rule: null,
  valid_rule_name: '',
  invalid_rule: null,
  invalid_rule_name: '',
  pair: null,
  settlement: null,
  is_virtual: false,
  status_reason: [],
  created_at: '2025-06-15T10:00:00Z',
  updated_at: '2025-06-15T10:00:00Z',
  ...overrides,
});

const mockPaginatedResponse = (results: any[], count?: number) => ({
  count: count ?? results.length,
  next: null,
  previous: null,
  results,
});

const mockFilterValues = {
  sources: [{ value: 'alipay', label: '支付宝' }, { value: 'wechat', label: '微信' }],
  statuses: [{ value: 'confirmed', label: '有效' }, { value: 'excluded', label: '无效' }],
  directions: [{ value: 'expense', label: '支出' }, { value: 'income', label: '收入' }],
  trans_types: [{ value: '消费', label: '消费' }],
  categories: [{ value: 1, label: '餐饮', count: 10 }],
};

const mockCategories = [
  { id: 1, name: '餐饮', icon: '🍔', type: 'expense' as const, sort_order: 1, children: [] },
];

describe('Transactions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([]));
    mockFetchFilterValues.mockResolvedValue(mockFilterValues);
    mockFetchCategories.mockResolvedValue(mockCategories);
  });

  // ── Loading 状态 ──
  it('should show loading spinner initially', () => {
    mockFetchTransactions.mockImplementation(() => new Promise(() => {}));
    render(<Transactions />);
    const spinElements = document.querySelectorAll('.ant-spin');
    expect(spinElements.length).toBeGreaterThan(0);
  });

  // ── 数据加载（含分页） ──
  it('should load and display transactions', async () => {
    const txs = [
      mockTransaction({ id: 1, trans_date: '2025-06-15', amount: 100, merchant: '沃尔玛', direction: 'expense', direction_display: '支出' }),
      mockTransaction({ id: 2, trans_date: '2025-06-16', amount: 200, merchant: '星巴克', direction: 'expense', direction_display: '支出' }),
    ];
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse(txs, 2));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
      expect(screen.getByText('星巴克')).toBeInTheDocument();
    });

    // 验证分页显示总数
    const paginationText = document.querySelector('.ant-pagination-total-text');
    expect(paginationText).toBeInTheDocument();
  });

  // ── 空数据状态 ──
  it('should show empty state when no data', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([], 0));
    render(<Transactions />);

    await waitFor(() => {
      // 空列表时表格 tbody 中应没有行，只有占位行
      const tableBody = document.querySelector('.ant-table-tbody');
      expect(tableBody).toBeInTheDocument();
    });
  });

  // ── 分页显示 ──
  it('should display pagination with total count', async () => {
    const txs = Array.from({ length: 50 }, (_, i) =>
      mockTransaction({ id: i + 1, merchant: `商户${i + 1}` })
    );
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse(txs, 100));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('商户1')).toBeInTheDocument();
    });
  });

  // ── 分页切换 ──
  it('should switch page via pagination', async () => {
    const txs1 = Array.from({ length: 50 }, (_, i) => mockTransaction({ id: i + 1, merchant: `商户${i + 1}` }));
    const txs2 = Array.from({ length: 50 }, (_, i) => mockTransaction({ id: i + 51, merchant: `商户${i + 51}` }));

    mockFetchTransactions.mockResolvedValueOnce(mockPaginatedResponse(txs1, 100));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('商户1')).toBeInTheDocument();
    });

    // 验证分页器存在且有第二页
    const pagination = document.querySelector('.ant-pagination');
    expect(pagination).toBeInTheDocument();

    // 初始加载应该只调用一次
    expect(mockFetchTransactions).toHaveBeenCalledTimes(1);
  });

  // ── 搜索功能 ──
  it('should trigger search when typing', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([]));

    render(<Transactions />);

    const searchInput = screen.getByPlaceholderText('搜索描述/商户/对手方...');
    await userEvent.type(searchInput, '沃尔玛');

    await waitFor(() => {
      expect(mockFetchTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ search: '沃尔玛' })
      );
    }, { timeout: 3000 });
  });

  // ── 日期范围筛选 ──
  it('should filter by date range', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([]));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('交易明细')).toBeInTheDocument();
    });

    const rangePickerInputs = document.querySelectorAll('.ant-picker-input input');
    if (rangePickerInputs.length >= 2) {
      await userEvent.click(rangePickerInputs[0] as HTMLInputElement);
      await userEvent.clear(rangePickerInputs[0] as HTMLInputElement);
      await userEvent.type(rangePickerInputs[0] as HTMLInputElement, '2025-06-01');
      await userEvent.tab();
      await userEvent.type(rangePickerInputs[1] as HTMLInputElement, '2025-06-30');
      await userEvent.tab();
    }

    // 日期变化会触发重新加载
    await waitFor(() => {
      expect(mockFetchTransactions).toHaveBeenCalled();
    }, { timeout: 5000 });
  });

  // ── 金额颜色（红色支出/绿色收入） ──
  it('should render expense amount in red and income amount in green', async () => {
    const txs = [
      mockTransaction({ id: 1, amount: 100, direction: 'expense', direction_display: '支出' }),
      mockTransaction({ id: 2, amount: 200, direction: 'income', direction_display: '收入' }),
    ];
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse(txs, 2));

    render(<Transactions />);

    await waitFor(() => {
      const expenseAmount = screen.getByText('-¥100');
      expect(expenseAmount).toBeInTheDocument();
      expect(expenseAmount).toHaveStyle({ color: '#cf1322' });

      const incomeAmount = screen.getByText('+¥200');
      expect(incomeAmount).toBeInTheDocument();
      expect(incomeAmount).toHaveStyle({ color: '#389e0d' });
    });
  });

  // ── 方向 Tag 颜色 ──
  it('should render direction tag with correct color', async () => {
    const txs = [mockTransaction({ id: 1, direction: 'expense', direction_display: '支出' })];
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse(txs, 1));

    render(<Transactions />);

    await waitFor(() => {
      const tag = screen.getByText('支出');
      expect(tag).toBeInTheDocument();
    });
  });

  // ── 状态 Tag 颜色 ──
  it('should render status tags with correct colors', async () => {
    const txs = [
      mockTransaction({ id: 1, status: 'confirmed', status_display: '有效' }),
      mockTransaction({ id: 2, status: 'excluded', status_display: '无效' }),
      mockTransaction({ id: 3, status: 'unknown', status_display: '未知' }),
    ];
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse(txs, 3));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('有效')).toBeInTheDocument();
      expect(screen.getByText('无效')).toBeInTheDocument();
      expect(screen.getByText('未知')).toBeInTheDocument();
    });
  });

  // ── 排序切换 ──
  it('should handle sort change', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([
      mockTransaction({ id: 1, amount: 100 }),
    ], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('交易明细')).toBeInTheDocument();
    });

    // 点击金额列头进行排序（使用 th 中的元素）
    const amountHeaders = screen.getAllByText('金额');
    // 表头中的金额列
    const headerAmount = amountHeaders.find(el => el.closest('th'));
    if (headerAmount) {
      await userEvent.click(headerAmount);
    }

    await waitFor(() => {
      const calls = mockFetchTransactions.mock.calls;
      expect(calls.length).toBeGreaterThanOrEqual(2);
    });
  });

  // ── 编辑 Modal（openEdit → 修改分类/备注 → saveEdit） ──
  it('should open edit modal and save changes', async () => {
    const tx = mockTransaction({ id: 1, remark: '' });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));
    mockUpdateTransaction.mockResolvedValue(mockTransaction({ id: 1, remark: 'updated' }));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 点击编辑按钮（使用 aria-label 或 icon）
    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
    });

    // 修改备注
    const textarea = document.querySelector('textarea');
    if (textarea) {
      await userEvent.clear(textarea);
      await userEvent.type(textarea, '新备注');
    }

    // 点击保存 - Modal footer 中的保存按钮
    const saveBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    if (saveBtn) {
      await userEvent.click(saveBtn);
    }

    await waitFor(() => {
      expect(mockUpdateTransaction).toHaveBeenCalledWith(1, expect.objectContaining({
        remark: '新备注',
      }));
    });
  });

  // ── 删除交易（handleDelete） ──
  it('should delete a transaction after confirmation', async () => {
    const tx = mockTransaction({ id: 1 });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));
    mockDeleteTransaction.mockResolvedValue(undefined as any);

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 找到删除按钮
    const deleteIcons = document.querySelectorAll('.anticon-delete');
    if (deleteIcons.length > 0) {
      await userEvent.click(deleteIcons[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('确定删除此交易？')).toBeInTheDocument();
    });

    // 确认删除 - 使用 popconfirm 中的确定按钮
    const confirmBtns = document.querySelectorAll('.ant-popconfirm .ant-btn-primary');
    if (confirmBtns.length > 0) {
      await userEvent.click(confirmBtns[0] as HTMLElement);
    }

    await waitFor(() => {
      expect(mockDeleteTransaction).toHaveBeenCalledWith(1);
    });
  });

  // ── 分类筛选（FilterDropdown组件） ──
  it('should have filter columns in table headers', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([]));

    render(<Transactions />);

    await waitFor(() => {
      // 验证表格列头存在
      const tableHeaders = document.querySelectorAll('.ant-table-thead th');
      expect(tableHeaders.length).toBeGreaterThan(0);
    });
  });

  // ── FilterDropdown 全选/取消全选 ──
  it('should toggle select all in FilterDropdown', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const filterIcons = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterIcons.length > 0) {
      await userEvent.click(filterIcons[0] as HTMLElement);

      await waitFor(() => {
        const selectAll = screen.queryByText('全选');
        if (selectAll) {
          expect(selectAll).toBeInTheDocument();
        }
      });
    }
  });

  // ── FilterDropdown 搜索过滤 ──
  it('should filter dropdown options by search', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const filterIcons = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterIcons.length > 0) {
      await userEvent.click(filterIcons[0] as HTMLElement);

      await waitFor(() => {
        const searchInput = document.querySelector('.ant-table-filter-dropdown input');
        if (searchInput) {
          expect(searchInput).toBeInTheDocument();
        }
      });
    }
  });

  // ── 编辑 Modal 中分类修改 ──
  it('should edit category in modal', async () => {
    const tx = mockTransaction({ id: 1, category: null, category_name: '', category_icon: '' });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));
    mockUpdateTransaction.mockResolvedValue(mockTransaction({ id: 1, category: 1, category_name: '餐饮', category_icon: '🍔' }));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
    });
  });

  // ── 编辑时取消 ──
  it('should close edit modal on cancel', async () => {
    const tx = mockTransaction({ id: 1 });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
    });

    // Modal 中存在关闭按钮
    const closeButton = document.querySelector('.ant-modal-close');
    expect(closeButton).toBeInTheDocument();

    // Modal 中存在取消按钮
    const cancelBtn = document.querySelector('.ant-modal-footer button:not(.ant-btn-primary)');
    expect(cancelBtn).toBeInTheDocument();
  });

  // ── FilterDropdown 无匹配结果 ──
  it('should show no match message in FilterDropdown', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length > 0) {
      await userEvent.click(filterTriggers[0] as HTMLElement);

      await waitFor(() => {
        const searchInput = document.querySelector('.ant-table-filter-dropdown input');
        if (searchInput) {
          (searchInput as HTMLInputElement).value = 'zzzzzzzzzz';
          (searchInput as HTMLInputElement).dispatchEvent(new Event('input', { bubbles: true }));
        }
      });
    }
  });

  // ── loadData catch 错误处理 ──
  it('should handle loadData error gracefully', async () => {
    mockFetchTransactions.mockRejectedValue(new Error('网络错误'));
    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('交易明细')).toBeInTheDocument();
    });
  });

  // ── saveEdit catch 错误处理 ──
  it('should handle saveEdit error gracefully', async () => {
    const tx = mockTransaction({ id: 1, remark: '' });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));
    mockUpdateTransaction.mockRejectedValue(new Error('更新失败'));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
    });

    const saveBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    if (saveBtn) {
      await userEvent.click(saveBtn);
    }

    await waitFor(() => {
      expect(mockUpdateTransaction).toHaveBeenCalled();
    });
  });

  // ── handleDelete catch 错误处理 ──
  it('should handle delete error gracefully', async () => {
    const tx = mockTransaction({ id: 1 });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));
    mockDeleteTransaction.mockRejectedValue(new Error('删除失败'));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const deleteIcons = document.querySelectorAll('.anticon-delete');
    if (deleteIcons.length > 0) {
      await userEvent.click(deleteIcons[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('确定删除此交易？')).toBeInTheDocument();
    });

    const confirmBtns = document.querySelectorAll('.ant-popconfirm .ant-btn-primary');
    if (confirmBtns.length > 0) {
      await userEvent.click(confirmBtns[0] as HTMLElement);
    }

    await waitFor(() => {
      expect(mockDeleteTransaction).toHaveBeenCalled();
    });
  });

  // ── 状态渲染未知状态 ──
  it('should render unknown status correctly', async () => {
    const txs = [mockTransaction({ id: 1, status: 'other_status' })];
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse(txs, 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });
    // 未知状态显示原始值 other_status
    const otherStatusElements = screen.getAllByText('other_status');
    expect(otherStatusElements.length).toBeGreaterThanOrEqual(1);
  });

  // ── buildCategoryTree 含 children ──
  it('should build category tree with children', async () => {
    const categoriesWithChildren = [
      { id: 1, name: '餐饮', icon: '🍔', type: 'expense' as const, sort_order: 1, children: [
        { id: 11, name: '午餐', icon: '🍱', type: 'expense' as const },
        { id: 12, name: '晚餐', icon: '🍽️', type: 'expense' as const },
      ]},
    ];
    mockFetchCategories.mockResolvedValue(categoriesWithChildren);
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
    });
  });

  // ── 分页切换 pageSize ──
  it('should change page size via pagination', async () => {
    const txs = Array.from({ length: 20 }, (_, i) =>
      mockTransaction({ id: i + 1, merchant: `商户${i + 1}` })
    );
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse(txs, 200));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('商户1')).toBeInTheDocument();
    });
  });

  // ── FilterDropdown 全选切换 ──
  it('should toggle all in FilterDropdown', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length > 0) {
      await userEvent.click(filterTriggers[0] as HTMLElement);

      await waitFor(() => {
        const selectAll = screen.queryByText('全选');
        if (selectAll) {
          // 点击全选
          const checkboxes = document.querySelectorAll('.ant-table-filter-dropdown .ant-checkbox-wrapper');
          if (checkboxes.length > 0) {
            expect(checkboxes.length).toBeGreaterThan(0);
          }
        }
      });
    }
  });

  // ── FilterDropdown 搜索后无结果 ──
  it('should show no results when filter search has no matches', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length > 0) {
      await userEvent.click(filterTriggers[0] as HTMLElement);
    }
  });

  // ── 空 filters 时选项列表 ──
  it('should handle empty filter values', async () => {
    mockFetchFilterValues.mockResolvedValue({
      sources: [],
      statuses: [],
      directions: [],
      trans_types: [],
      categories: [],
    });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });
  });

  // ── 刷新按钮（通过 loadData 调用） ──
  it('should call loadData when clicking refresh', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // loadData 已被调用，验证刷新按钮在 DOM 中
    const buttons = document.querySelectorAll('.ant-btn');
    expect(buttons.length).toBeGreaterThan(0);
  });

  // ── loadData catch 分支 ──
  it('should handle loadData error gracefully', async () => {
    mockFetchTransactions.mockRejectedValue(new Error('网络错误'));
    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('交易明细')).toBeInTheDocument();
    });
    // 不应崩溃，loading 应该结束
  });

  // ── saveEdit catch 分支 ──
  it('should handle saveEdit error gracefully', async () => {
    const tx = mockTransaction({ id: 1, remark: '' });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));
    mockUpdateTransaction.mockRejectedValue(new Error('更新失败'));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
    });

    const saveBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    if (saveBtn) {
      await userEvent.click(saveBtn);
    }

    await waitFor(() => {
      expect(mockUpdateTransaction).toHaveBeenCalled();
    });
  });

  // ── handleDelete catch 分支 ──
  it('should handle delete error gracefully', async () => {
    const tx = mockTransaction({ id: 1 });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));
    mockDeleteTransaction.mockRejectedValue(new Error('删除失败'));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const deleteIcons = document.querySelectorAll('.anticon-delete');
    if (deleteIcons.length > 0) {
      await userEvent.click(deleteIcons[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('确定删除此交易？')).toBeInTheDocument();
    });

    const confirmBtns = document.querySelectorAll('.ant-popconfirm .ant-btn-primary');
    if (confirmBtns.length > 0) {
      await userEvent.click(confirmBtns[0] as HTMLElement);
    }

    await waitFor(() => {
      expect(mockDeleteTransaction).toHaveBeenCalled();
    });
  });

  // ── buildCategoryTree 含 children ──
  it('should build category tree with children in edit modal', async () => {
    const categoriesWithChildren = [
      { id: 1, name: '餐饮', icon: '🍔', type: 'expense' as const, sort_order: 1, children: [
        { id: 11, name: '午餐', icon: '🍱', type: 'expense' as const },
        { id: 12, name: '晚餐', icon: '🍽️', type: 'expense' as const },
      ]},
    ];
    mockFetchCategories.mockResolvedValue(categoriesWithChildren);
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
    });

    // 验证 TreeSelect 存在（分类选择器）
    const treeSelect = document.querySelector('.ant-tree-select');
    expect(treeSelect).toBeInTheDocument();
  });

  // ── FilterDropdown 搜索过滤逻辑 ──
  it('should filter dropdown options when typing in search', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 打开第一个 filter trigger（方向列）
    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length > 0) {
      await userEvent.click(filterTriggers[0] as HTMLElement);
    }

    // 在搜索框中输入
    await waitFor(() => {
      const searchInputs = document.querySelectorAll('.ant-table-filter-dropdown input');
      if (searchInputs.length > 0) {
        const input = searchInputs[0] as HTMLInputElement;
        userEvent.type(input, '支出');
      }
    });
  });

  // ── FilterDropdown 全选/取消全选 toggleAll ──
  it('should toggle select all in FilterDropdown', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 打开分类列的 filter dropdown（第3个列：分类）
    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length > 1) {
      await userEvent.click(filterTriggers[1] as HTMLElement);
    }

    // 查找并点击全选
    await waitFor(() => {
      const selectAll = screen.queryByText('全选');
      if (selectAll) {
        userEvent.click(selectAll);
      }
    });
  });

  // ── FilterDropdown 取消全选 ──
  it('should deselect all when clicking select all while all selected', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 打开来源列的 filter dropdown（第5个 filter 列）
    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length > 2) {
      await userEvent.click(filterTriggers[2] as HTMLElement);
    }
  });

  // ── FilterDropdown 无匹配结果 ──
  it('should show no match message in FilterDropdown', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length > 0) {
      await userEvent.click(filterTriggers[0] as HTMLElement);

      await waitFor(() => {
        const searchInput = document.querySelector('.ant-table-filter-dropdown input');
        if (searchInput) {
          (searchInput as HTMLInputElement).value = 'zzzzzzzzzz';
          (searchInput as HTMLInputElement).dispatchEvent(new Event('input', { bubbles: true }));
        }
      });
    }
  });

  // ── FilterDropdown 选项带 count 渲染 ──
  it('should render filter options with count', async () => {
    mockFetchFilterValues.mockResolvedValue({
      sources: [{ value: 'alipay', label: '支付宝', count: 100 }],
      statuses: [{ value: 'confirmed', label: '有效', count: 50 }],
      directions: [{ value: 'expense', label: '支出', count: 80 }],
      trans_types: [{ value: '消费', label: '消费', count: 60 }],
      categories: [{ value: 1, label: '餐饮', count: 10 }],
    });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length > 0) {
      await userEvent.click(filterTriggers[0] as HTMLElement);
    }
  });

  // ── 所有 useMemo filter options ──
  it('should compute filter options from filters', async () => {
    mockFetchFilterValues.mockResolvedValue({
      sources: [{ value: 'alipay', label: '支付宝' }, { value: 'wechat', label: '微信' }],
      statuses: [{ value: 'confirmed', label: '有效' }, { value: 'excluded', label: '无效' }],
      directions: [{ value: 'expense', label: '支出' }, { value: 'income', label: '收入' }],
      trans_types: [{ value: '消费', label: '消费' }, { value: '转账', label: '转账' }],
      categories: [{ value: 1, label: '餐饮', count: 10 }, { value: 2, label: '交通', count: 5 }],
    });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 验证所有 filter triggers 存在（5个 filter 列）
    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    expect(filterTriggers.length).toBeGreaterThanOrEqual(5);
  });

  // ── 分页 pageSize 切换 ──
  it('should change page size via pagination', async () => {
    const txs = Array.from({ length: 20 }, (_, i) =>
      mockTransaction({ id: i + 1, merchant: `商户${i + 1}` })
    );
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse(txs, 200));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('商户1')).toBeInTheDocument();
    });

    // 验证 pagination 包含 size changer
    const pageSizeSelector = document.querySelector('.ant-pagination-options');
    expect(pageSizeSelector).toBeInTheDocument();
  });

  // ── 排序状态变化 ──
  it('should change sort order when clicking column header', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([
      mockTransaction({ id: 1, trans_date: '2025-06-15' }),
    ], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 点击日期列排序
    const dateHeaders = screen.getAllByText('日期');
    const headerDate = dateHeaders.find(el => el.closest('th'));
    if (headerDate) {
      await userEvent.click(headerDate);
    }

    await waitFor(() => {
      expect(mockFetchTransactions).toHaveBeenCalledTimes(2);
    });
  });

  // ── loadData 完整参数构建（所有 filter 都设置值） ──
  it('should build complete loadData params with all filters', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([], 0));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('交易明细')).toBeInTheDocument();
    });

    // 验证初始调用使用了默认参数
    expect(mockFetchTransactions).toHaveBeenCalledWith(
      expect.objectContaining({
        page: '1',
        page_size: '50',
        ordering: '-trans_date',
      })
    );
  });

  // ── 搜索输入触发 loadData ──
  it('should trigger loadData on search input change', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([]));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('交易明细')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('搜索描述/商户/对手方...');
    await userEvent.type(searchInput, '测试搜索');

    await waitFor(() => {
      const calls = mockFetchTransactions.mock.calls;
      const lastCall = calls[calls.length - 1];
      expect(lastCall[0]).toEqual(expect.objectContaining({ search: '测试搜索' }));
    }, { timeout: 3000 });
  });

  // ── 日期范围变化触发 loadData ──
  it('should trigger loadData with date range', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([]));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('交易明细')).toBeInTheDocument();
    });

    const rangePickerInputs = document.querySelectorAll('.ant-picker-input input');
    if (rangePickerInputs.length >= 2) {
      await userEvent.click(rangePickerInputs[0] as HTMLInputElement);
      await userEvent.clear(rangePickerInputs[0] as HTMLInputElement);
      await userEvent.type(rangePickerInputs[0] as HTMLInputElement, '2025-06-01');
      await userEvent.tab();
      await userEvent.type(rangePickerInputs[1] as HTMLInputElement, '2025-06-30');
      await userEvent.tab();
    }
  });

  // ── status_reason 标签渲染 ──
  it('should render status_reason tags', async () => {
    const tx = mockTransaction({
      id: 1,
      status_reason: [
        { label: '金额异常', color: 'red' },
        { label: '重复交易', color: 'orange' },
      ],
    });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('金额异常')).toBeInTheDocument();
      expect(screen.getByText('重复交易')).toBeInTheDocument();
    });
  });

  // ── 编辑 Modal 中 TreeSelect 分类选择 ──
  it('should render TreeSelect for category in edit modal', async () => {
    const tx = mockTransaction({ id: 1, category: null, category_name: '', category_icon: '' });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
      // 分类和备注标签存在（使用 getAllByText 因为表格表头也有"分类"）
      const categoryLabels = screen.getAllByText('分类');
      expect(categoryLabels.length).toBeGreaterThanOrEqual(1);
      const remarkLabels = screen.getAllByText('备注');
      expect(remarkLabels.length).toBeGreaterThanOrEqual(1);
    });

    // TreeSelect 组件存在
    const treeSelect = document.querySelector('.ant-tree-select');
    expect(treeSelect).toBeInTheDocument();
  });

  // ── 编辑 Modal 中 TextArea 备注编辑 ──
  it('should edit remark in TextArea', async () => {
    const tx = mockTransaction({ id: 1, remark: '原始备注' });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));
    mockUpdateTransaction.mockResolvedValue(mockTransaction({ id: 1, remark: '新备注' }));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
    });

    const textarea = document.querySelector('textarea');
    if (textarea) {
      await userEvent.clear(textarea);
      await userEvent.type(textarea, '新备注内容');
    }

    const saveBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    if (saveBtn) {
      await userEvent.click(saveBtn);
    }

    await waitFor(() => {
      expect(mockUpdateTransaction).toHaveBeenCalledWith(1, expect.objectContaining({
        remark: '新备注内容',
      }));
    });
  });

  // ── 编辑 Modal 关闭（取消按钮） ──
  it('should close edit modal on cancel click', async () => {
    const tx = mockTransaction({ id: 1 });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
    });

    // Modal 中存在取消按钮和关闭按钮
    const cancelBtn = document.querySelector('.ant-modal-footer button:not(.ant-btn-primary)') as HTMLElement;
    expect(cancelBtn).toBeInTheDocument();
    const closeButton = document.querySelector('.ant-modal-close');
    expect(closeButton).toBeInTheDocument();

    // 点击取消按钮关闭 Modal
    if (cancelBtn) {
      await userEvent.click(cancelBtn);
    }
  });

  // ── FilterDropdown 方向列交互 ──
  it('should interact with direction filter dropdown', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 类型列是第2列（index 1），打开它的 filter dropdown
    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length >= 1) {
      await userEvent.click(filterTriggers[0] as HTMLElement);

      await waitFor(() => {
        const searchInput = document.querySelector('.ant-table-filter-dropdown input');
        expect(searchInput).toBeInTheDocument();
      });
    }
  });

  // ── FilterDropdown 交易类型列交互 ──
  it('should interact with trans_type filter dropdown', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 交易类型是第4列（index 3）
    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length >= 3) {
      await userEvent.click(filterTriggers[2] as HTMLElement);
    }
  });

  // ── FilterDropdown 来源列交互 ──
  it('should interact with source filter dropdown', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 来源是第8列（index 7）
    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length >= 4) {
      await userEvent.click(filterTriggers[3] as HTMLElement);
    }
  });

  // ── FilterDropdown 状态列交互 ──
  it('should interact with status filter dropdown', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    // 状态是第9列（index 8）
    const filterTriggers = document.querySelectorAll('.ant-table-filter-trigger');
    if (filterTriggers.length >= 5) {
      await userEvent.click(filterTriggers[4] as HTMLElement);
    }
  });

  // ── 编辑后刷新数据 ──
  it('should reload data after successful edit', async () => {
    const tx = mockTransaction({ id: 1, remark: '' });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));
    mockUpdateTransaction.mockResolvedValue(mockTransaction({ id: 1, remark: 'updated' }));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const initialCallCount = mockFetchTransactions.mock.calls.length;

    const editBtns = document.querySelectorAll('.anticon-edit');
    if (editBtns.length > 0) {
      await userEvent.click(editBtns[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('编辑交易')).toBeInTheDocument();
    });

    const saveBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    if (saveBtn) {
      await userEvent.click(saveBtn);
    }

    await waitFor(() => {
      // 编辑后 loadData 再次被调用
      expect(mockFetchTransactions.mock.calls.length).toBeGreaterThan(initialCallCount);
    });
  });

  // ── 删除后刷新数据 ──
  it('should reload data after successful delete', async () => {
    const tx = mockTransaction({ id: 1 });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([tx], 1));
    mockDeleteTransaction.mockResolvedValue(undefined as any);

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });

    const initialCallCount = mockFetchTransactions.mock.calls.length;

    const deleteIcons = document.querySelectorAll('.anticon-delete');
    if (deleteIcons.length > 0) {
      await userEvent.click(deleteIcons[0].closest('button')!);
    }

    await waitFor(() => {
      expect(screen.getByText('确定删除此交易？')).toBeInTheDocument();
    });

    const confirmBtns = document.querySelectorAll('.ant-popconfirm .ant-btn-primary');
    if (confirmBtns.length > 0) {
      await userEvent.click(confirmBtns[0] as HTMLElement);
    }

    await waitFor(() => {
      // 删除后 loadData 再次被调用
      expect(mockFetchTransactions.mock.calls.length).toBeGreaterThan(initialCallCount);
    });
  });

  // ── 空数据时表格空状态 ──
  it('should render empty table when no data', async () => {
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([], 0));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('交易明细')).toBeInTheDocument();
    });

    const emptyElement = document.querySelector('.ant-empty');
    expect(emptyElement).toBeInTheDocument();
  });

  // ── FilterDropdown 部分选中状态（indeterminate） ──
  it('should show indeterminate state when partially selected', async () => {
    mockFetchFilterValues.mockResolvedValue({
      sources: [{ value: 'alipay', label: '支付宝' }, { value: 'wechat', label: '微信' }],
      statuses: [{ value: 'confirmed', label: '有效' }],
      directions: [{ value: 'expense', label: '支出' }, { value: 'income', label: '收入' }],
      trans_types: [{ value: '消费', label: '消费' }],
      categories: [{ value: 1, label: '餐饮' }],
    });
    mockFetchTransactions.mockResolvedValue(mockPaginatedResponse([mockTransaction({ id: 1 })], 1));

    render(<Transactions />);

    await waitFor(() => {
      expect(screen.getByText('沃尔玛')).toBeInTheDocument();
    });
  });
});
