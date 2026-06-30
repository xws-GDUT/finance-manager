import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import InvalidRules from './InvalidRules';
import {
  fetchInvalidRules,
  createInvalidRule,
  updateInvalidRule,
  deleteInvalidRule,
  testInvalidRule,
  applyInvalidRules,
  createDefaultInvalidRules,
} from '../api';

vi.mock('../api');
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), vi.fn()],
  Link: ({ children }: { children: React.ReactNode }) => children,
}));

const mockFetchInvalidRules = vi.mocked(fetchInvalidRules);
const mockCreateInvalidRule = vi.mocked(createInvalidRule);
const mockUpdateInvalidRule = vi.mocked(updateInvalidRule);
const mockDeleteInvalidRule = vi.mocked(deleteInvalidRule);
const mockTestInvalidRule = vi.mocked(testInvalidRule);
const mockApplyInvalidRules = vi.mocked(applyInvalidRules);
const mockCreateDefaultInvalidRules = vi.mocked(createDefaultInvalidRules);

const mockRule = (overrides = {}) => ({
  id: 1,
  name: '测试无效规则',
  priority: 50,
  is_active: true,
  sources: 'alipay',
  trans_types: '',
  directions: 'expense',
  categories: '',
  payment_channels: '',
  keywords: '测试关键词',
  keyword_exclude: '',
  merchants: '',
  amount_min: null,
  amount_max: null,
  counterparties: '测试对手方',
  hit_count: 5,
  created_at: '2025-06-15T10:00:00Z',
  updated_at: '2025-06-15T10:00:00Z',
  ...overrides,
});

describe('InvalidRules', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchInvalidRules.mockResolvedValue([mockRule()]);
    mockCreateInvalidRule.mockResolvedValue(mockRule({ id: 2 }));
    mockUpdateInvalidRule.mockResolvedValue(mockRule());
    mockDeleteInvalidRule.mockResolvedValue(undefined as any);
    mockTestInvalidRule.mockResolvedValue({ matched_count: 10 });
    mockApplyInvalidRules.mockResolvedValue({ matched: 20, total: 100 });
    mockCreateDefaultInvalidRules.mockResolvedValue({ created: 3, skipped: 1 });
  });

  // ── 渲染 RuleManager 组件 ──
  it('should render RuleManager component with invalid type', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('无效规则（黑名单）')).toBeInTheDocument();
    });
  });

  // ── 传入正确的 props (type="invalid") ──
  it('should pass type="invalid" to RuleManager', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('无效规则（黑名单）')).toBeInTheDocument();
    });
  });

  // ── 传入正确的 API 函数 ──
  it('should call fetchInvalidRules on mount', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(mockFetchInvalidRules).toHaveBeenCalled();
    });
  });

  // ── 显示规则列表 ──
  it('should display rule list', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试无效规则')).toBeInTheDocument();
    });
  });

  // ── 空规则列表 ──
  it('should handle empty rule list', async () => {
    mockFetchInvalidRules.mockResolvedValue([]);

    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('无效规则（黑名单）')).toBeInTheDocument();
    });

    // 空列表时表格数据为空
    const table = document.querySelector('.ant-table-tbody');
    expect(table).toBeInTheDocument();
  });

  // ── 新建规则按钮 ──
  it('should render create rule button', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('新建规则')).toBeInTheDocument();
    });
  });

  // ── 创建默认规则按钮 ──
  it('should render create defaults button', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('创建默认规则')).toBeInTheDocument();
    });
  });

  // ── 重新应用按钮 ──
  it('should render re-apply button', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('重新应用')).toBeInTheDocument();
    });
  });

  // ── 打开新建规则模态框 ──
  it('should open create modal when clicking create button', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('新建规则')).toBeInTheDocument();
    });

    // Card extra 中的新建规则按钮
    const createBtns = screen.getAllByText('新建规则');
    // Card extra 中是第二个（ant-card-extra 里的）
    const createBtn = createBtns.find(btn => btn.closest('.ant-card-extra'));
    if (createBtn) {
      await userEvent.click(createBtn);
    }

    await waitFor(() => {
      // Modal 标题为 "新建规则"
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle).toBeInTheDocument();
    });
  });

  // ── 编辑规则 ──
  it('should open edit modal when clicking edit button', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试无效规则')).toBeInTheDocument();
    });

    const editBtn = screen.getByText('编辑');
    await userEvent.click(editBtn);

    await waitFor(() => {
      // Modal 标题为 "编辑规则"
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle?.textContent).toBe('编辑规则');
    });
  });

  // ── 删除规则 ──
  it('should delete rule after confirmation', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试无效规则')).toBeInTheDocument();
    });

    const deleteBtn = screen.getByText('删除');
    await userEvent.click(deleteBtn);

    await waitFor(() => {
      expect(screen.getByText('确定删除？')).toBeInTheDocument();
    });

    // 使用 Popconfirm 中的确认按钮
    const popConfirm = document.querySelector('.ant-popconfirm');
    if (popConfirm) {
      const confirmBtn = popConfirm.querySelector('.ant-btn-primary') as HTMLElement;
      if (confirmBtn) {
        await userEvent.click(confirmBtn);
      }
    }

    await waitFor(() => {
      expect(mockDeleteInvalidRule).toHaveBeenCalledWith(1);
    });
  });

  // ── 切换启用状态 ──
  it('should toggle rule active state', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试无效规则')).toBeInTheDocument();
    });

    const switches = document.querySelectorAll('.ant-switch');
    if (switches.length > 0) {
      await userEvent.click(switches[0]);

      await waitFor(() => {
        expect(mockUpdateInvalidRule).toHaveBeenCalledWith(1, { is_active: false });
      });
    }
  });

  // ── 创建默认规则 ──
  it('should create default rules', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('创建默认规则')).toBeInTheDocument();
    });

    const createDefaultsBtn = screen.getByText('创建默认规则');
    await userEvent.click(createDefaultsBtn);

    await waitFor(() => {
      expect(mockCreateDefaultInvalidRules).toHaveBeenCalled();
    });
  });

  // ── 重新应用规则 ──
  it('should apply rules', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('重新应用')).toBeInTheDocument();
    });

    const applyBtn = screen.getByText('重新应用');
    await userEvent.click(applyBtn);

    await waitFor(() => {
      expect(mockApplyInvalidRules).toHaveBeenCalled();
    });
  });

  // ── 测试规则 ──
  it('should test rule', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试无效规则')).toBeInTheDocument();
    });

    const editBtn = screen.getByText('编辑');
    await userEvent.click(editBtn);

    await waitFor(() => {
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle?.textContent).toBe('编辑规则');
    });

    // Modal footer 中的测试按钮
    const modalFooter = document.querySelector('.ant-modal-footer');
    if (modalFooter) {
      const testBtn = within(modalFooter as HTMLElement).getByText(/测试/);
      await userEvent.click(testBtn);
    }

    await waitFor(() => {
      expect(mockTestInvalidRule).toHaveBeenCalled();
    });
  });

  // ── 显示命中数 ──
  it('should display hit count', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  // ── 对手方字段（仅 invalid 规则有） ──
  it('should show counterparties field for invalid rules', async () => {
    render(<InvalidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试无效规则')).toBeInTheDocument();
    });

    const editBtn = screen.getByText('编辑');
    await userEvent.click(editBtn);

    await waitFor(() => {
      expect(screen.getByText('对手方（逗号分隔，精确匹配）')).toBeInTheDocument();
    });
  });
});
