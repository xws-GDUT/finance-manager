import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ValidRules from './ValidRules';
import {
  fetchValidRules,
  createValidRule,
  updateValidRule,
  deleteValidRule,
  testValidRule,
  applyValidRules,
  createDefaultValidRules,
} from '../api';

vi.mock('../api');
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), vi.fn()],
  Link: ({ children }: { children: React.ReactNode }) => children,
}));

const mockFetchValidRules = vi.mocked(fetchValidRules);
const mockCreateValidRule = vi.mocked(createValidRule);
const mockUpdateValidRule = vi.mocked(updateValidRule);
const mockDeleteValidRule = vi.mocked(deleteValidRule);
const mockTestValidRule = vi.mocked(testValidRule);
const mockApplyValidRules = vi.mocked(applyValidRules);
const mockCreateDefaultValidRules = vi.mocked(createDefaultValidRules);

const mockRule = (overrides = {}) => ({
  id: 1,
  name: '测试有效规则',
  priority: 50,
  is_active: true,
  sources: 'alipay,wechat',
  trans_types: '消费',
  directions: 'expense',
  categories: '1,2',
  payment_channels: '',
  keywords: '超市,购物',
  keyword_exclude: '',
  merchants: '',
  amount_min: null,
  amount_max: null,
  hit_count: 15,
  created_at: '2025-06-15T10:00:00Z',
  updated_at: '2025-06-15T10:00:00Z',
  ...overrides,
});

describe('ValidRules', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchValidRules.mockResolvedValue([mockRule()]);
    mockCreateValidRule.mockResolvedValue(mockRule({ id: 2 }));
    mockUpdateValidRule.mockResolvedValue(mockRule());
    mockDeleteValidRule.mockResolvedValue(undefined as any);
    mockTestValidRule.mockResolvedValue({ matched_count: 8 });
    mockApplyValidRules.mockResolvedValue({ matched: 15, total: 200 });
    mockCreateDefaultValidRules.mockResolvedValue({ created: 5, skipped: 2 });
  });

  // ── 渲染 RuleManager 组件 ──
  it('should render RuleManager component with valid type', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('有效规则（白名单）')).toBeInTheDocument();
    });
  });

  // ── 传入正确的 props (type="valid") ──
  it('should pass type="valid" to RuleManager', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('有效规则（白名单）')).toBeInTheDocument();
    });
  });

  // ── 传入正确的 API 函数 ──
  it('should call fetchValidRules on mount', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(mockFetchValidRules).toHaveBeenCalled();
    });
  });

  // ── 显示规则列表 ──
  it('should display rule list', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试有效规则')).toBeInTheDocument();
    });
  });

  // ── 空规则列表 ──
  it('should handle empty rule list', async () => {
    mockFetchValidRules.mockResolvedValue([]);

    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('有效规则（白名单）')).toBeInTheDocument();
    });

    const table = document.querySelector('.ant-table-tbody');
    expect(table).toBeInTheDocument();
  });

  // ── 新建规则按钮 ──
  it('should render create rule button', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('新建规则')).toBeInTheDocument();
    });
  });

  // ── 创建默认规则按钮 ──
  it('should render create defaults button', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('创建默认规则')).toBeInTheDocument();
    });
  });

  // ── 重新应用按钮 ──
  it('should render re-apply button', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('重新应用')).toBeInTheDocument();
    });
  });

  // ── 打开新建规则模态框 ──
  it('should open create modal when clicking create button', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('新建规则')).toBeInTheDocument();
    });

    const createBtns = screen.getAllByText('新建规则');
    const createBtn = createBtns.find(btn => btn.closest('.ant-card-extra'));
    if (createBtn) {
      await userEvent.click(createBtn);
    }

    await waitFor(() => {
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle).toBeInTheDocument();
    });
  });

  // ── 编辑规则 ──
  it('should open edit modal when clicking edit button', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试有效规则')).toBeInTheDocument();
    });

    const editBtn = screen.getByText('编辑');
    await userEvent.click(editBtn);

    await waitFor(() => {
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle?.textContent).toBe('编辑规则');
    });
  });

  // ── 删除规则 ──
  it('should delete rule after confirmation', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试有效规则')).toBeInTheDocument();
    });

    const deleteBtn = screen.getByText('删除');
    await userEvent.click(deleteBtn);

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
      expect(mockDeleteValidRule).toHaveBeenCalledWith(1);
    });
  });

  // ── 切换启用状态 ──
  it('should toggle rule active state', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试有效规则')).toBeInTheDocument();
    });

    const switches = document.querySelectorAll('.ant-switch');
    if (switches.length > 0) {
      await userEvent.click(switches[0]);

      await waitFor(() => {
        expect(mockUpdateValidRule).toHaveBeenCalledWith(1, { is_active: false });
      });
    }
  });

  // ── 创建默认规则 ──
  it('should create default rules', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('创建默认规则')).toBeInTheDocument();
    });

    const createDefaultsBtn = screen.getByText('创建默认规则');
    await userEvent.click(createDefaultsBtn);

    await waitFor(() => {
      expect(mockCreateDefaultValidRules).toHaveBeenCalled();
    });
  });

  // ── 重新应用规则 ──
  it('should apply rules', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('重新应用')).toBeInTheDocument();
    });

    const applyBtn = screen.getByText('重新应用');
    await userEvent.click(applyBtn);

    await waitFor(() => {
      expect(mockApplyValidRules).toHaveBeenCalled();
    });
  });

  // ── 测试规则 ──
  it('should test rule', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试有效规则')).toBeInTheDocument();
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
      expect(mockTestValidRule).toHaveBeenCalled();
    });
  });

  // ── 显示命中数 ──
  it('should display hit count', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('15')).toBeInTheDocument();
    });
  });

  // ── Valid 规则不显示对手方字段 ──
  it('should not show counterparties field for valid rules', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试有效规则')).toBeInTheDocument();
    });

    const editBtn = screen.getByText('编辑');
    await userEvent.click(editBtn);

    await waitFor(() => {
      expect(screen.queryByText('对手方（逗号分隔，精确匹配）')).not.toBeInTheDocument();
    });
  });

  // ── 显示优先级 ──
  it('should display rule priority', async () => {
    render(<ValidRules />);

    await waitFor(() => {
      expect(screen.getByText('测试有效规则')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
    });
  });
});
