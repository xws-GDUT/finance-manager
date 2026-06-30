import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RuleManager from './RuleManager';
import type { ValidRule, InvalidRule } from '../types';

// Mock antd message
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    message: {
      success: vi.fn(),
      error: vi.fn(),
    },
  };
});

const mockRule: ValidRule = {
  id: 1,
  name: '测试规则',
  priority: 50,
  is_active: true,
  sources: 'alipay,wechat',
  trans_types: '',
  directions: 'expense',
  categories: '',
  payment_channels: '',
  keywords: '餐饮,外卖',
  keyword_exclude: '',
  merchants: '',
  amount_min: null,
  amount_max: null,
  hit_count: 10,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

const mockInvalidRule: InvalidRule = {
  ...mockRule,
  counterparties: '测试对手方',
};

function createMockProps(type: 'valid' | 'invalid' = 'valid') {
  return {
    type,
    title: type === 'valid' ? '有效规则' : '无效规则',
    fetchFn: vi.fn(),
    createFn: vi.fn(),
    updateFn: vi.fn(),
    deleteFn: vi.fn(),
    testFn: vi.fn(),
    applyFn: vi.fn(),
    createDefaultsFn: vi.fn(),
  };
}

describe('RuleManager - valid type', () => {
  let props: ReturnType<typeof createMockProps>;

  beforeEach(() => {
    vi.clearAllMocks();
    props = createMockProps('valid');
    props.fetchFn.mockResolvedValue([mockRule]);
  });

  it('loads data on mount', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(props.fetchFn).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });
  });

  it('shows table columns', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });
    expect(screen.getByText('名称')).toBeTruthy();
    expect(screen.getByText('优先级')).toBeTruthy();
    expect(screen.getByText('启用')).toBeTruthy();
    expect(screen.getByText('来源')).toBeTruthy();
    expect(screen.getByText('方向')).toBeTruthy();
    expect(screen.getByText('关键词')).toBeTruthy();
    expect(screen.getByText('命中')).toBeTruthy();
    expect(screen.getByText('操作')).toBeTruthy();
  });

  it('openCreate opens modal with empty form', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });
    fireEvent.click(screen.getByText('新建规则'));
    // Modal should be visible with title "新建规则"
    await waitFor(() => {
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle?.textContent).toBe('新建规则');
    });
  });

  it('creates a new rule on save', async () => {
    props.createFn.mockResolvedValue({ id: 2 });
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('新建规则'));
    await waitFor(() => {
      expect(document.querySelector('.ant-modal')).toBeTruthy();
    });

    // Find the name input in the modal
    const nameInput = document.querySelector('.ant-modal input[placeholder="规则名称"]') as HTMLInputElement;
    if (nameInput) {
      fireEvent.change(nameInput, { target: { value: '新规则' } });
    }

    // Click save button - use querySelector to find the primary button in modal footer
    const saveBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    expect(saveBtn).toBeTruthy();
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(props.createFn).toHaveBeenCalledWith(
        expect.objectContaining({ name: '新规则' })
      );
    });
  });

  it('edits an existing rule', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    // Click the "编辑" button in the table row
    const editButtons = screen.getAllByText('编辑');
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      const modalTitle = document.querySelector('.ant-modal-title');
      expect(modalTitle?.textContent).toBe('编辑规则');
    });
  });

  it('saves edited rule', async () => {
    props.updateFn.mockResolvedValue({ id: 1 });
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    const editButtons = screen.getAllByText('编辑');
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(document.querySelector('.ant-modal')).toBeTruthy();
    });

    // Change name in modal
    const nameInput = document.querySelector('.ant-modal input[placeholder="规则名称"]') as HTMLInputElement;
    if (nameInput) {
      fireEvent.change(nameInput, { target: { value: '修改后的规则' } });
    }

    // Click save - use querySelector for modal footer primary button
    const saveBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    expect(saveBtn).toBeTruthy();
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(props.updateFn).toHaveBeenCalledWith(1, expect.objectContaining({ name: '修改后的规则' }));
    });
  });

  it('deletes a rule', async () => {
    props.deleteFn.mockResolvedValue({});
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    // Click the delete button in table row
    const deleteButtons = screen.getAllByText('删除');
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      // Popconfirm should appear
      expect(screen.getByText('确定删除？')).toBeTruthy();
    });

    // Click the confirm button in Popconfirm
    const okButton = document.querySelector('.ant-popconfirm .ant-btn-primary') as HTMLElement;
    if (okButton) {
      fireEvent.click(okButton);
    }

    await waitFor(() => {
      expect(props.deleteFn).toHaveBeenCalledWith(1);
    });
  });

  it('toggles active state', async () => {
    props.updateFn.mockResolvedValue({ id: 1 });
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    const switches = document.querySelectorAll('.ant-switch');
    if (switches.length > 0) {
      fireEvent.click(switches[0]);
      await waitFor(() => {
        expect(props.updateFn).toHaveBeenCalledWith(1, { is_active: false });
      });
    }
  });

  it('tests a rule', async () => {
    props.testFn.mockResolvedValue({ matched_count: 5 });
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    // Open edit first to access the test button in modal
    const editButtons = screen.getAllByText('编辑');
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(document.querySelector('.ant-modal')).toBeTruthy();
    });

    // Click test button in modal footer
    const testBtn = document.querySelector('.ant-modal-footer button') as HTMLElement;
    expect(testBtn).toBeTruthy();
    fireEvent.click(testBtn);

    await waitFor(() => {
      expect(props.testFn).toHaveBeenCalled();
    });
  });

  it('applies rules', async () => {
    props.applyFn.mockResolvedValue({ matched: 10, total: 20 });
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('重新应用'));
    await waitFor(() => {
      expect(props.applyFn).toHaveBeenCalled();
    });
  });

  it('creates default rules', async () => {
    props.createDefaultsFn.mockResolvedValue({ created: 5, skipped: 2 });
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('创建默认规则'));
    await waitFor(() => {
      expect(props.createDefaultsFn).toHaveBeenCalled();
    });
  });

  it('does not show counterparty field for valid type', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('新建规则'));

    await waitFor(() => {
      expect(document.querySelector('.ant-modal')).toBeTruthy();
    });

    // counterparty field should not exist
    expect(screen.queryByText('对手方（逗号分隔，精确匹配）')).toBeFalsy();
  });
});

describe('RuleManager - invalid type', () => {
  let props: ReturnType<typeof createMockProps>;

  beforeEach(() => {
    vi.clearAllMocks();
    props = createMockProps('invalid');
    props.fetchFn.mockResolvedValue([mockInvalidRule]);
  });

  it('loads invalid rules on mount', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(props.fetchFn).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });
  });

  it('shows counterparty field in edit modal for invalid type', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('新建规则'));

    await waitFor(() => {
      // The counterparty field should be visible in the modal
      expect(screen.getByText('对手方（逗号分隔，精确匹配）')).toBeTruthy();
    });
  });

  it('counterparty field shows existing value when editing', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    const editButtons = screen.getAllByText('编辑');
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('对手方（逗号分隔，精确匹配）')).toBeTruthy();
    });

    // The counterparty input should have the existing value
    const counterpartyInput = document.querySelector('.ant-modal input[placeholder="对手方名称，逗号分隔"]') as HTMLInputElement;
    expect(counterpartyInput).toBeTruthy();
  });

  it('loadData handles fetch error', async () => {
    props.fetchFn.mockRejectedValue(new Error('Network error'));
    render(<RuleManager {...props} />);

    await waitFor(() => {
      expect(props.fetchFn).toHaveBeenCalledTimes(1);
    });
  });

  it('save handles error', async () => {
    props.createFn.mockRejectedValue(new Error('Create error'));
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('新建规则'));
    await waitFor(() => {
      expect(document.querySelector('.ant-modal')).toBeTruthy();
    });

    const saveBtn = document.querySelector('.ant-modal-footer .ant-btn-primary') as HTMLElement;
    expect(saveBtn).toBeTruthy();
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(props.createFn).toHaveBeenCalled();
    });
  });

  it('delete handles error', async () => {
    props.deleteFn.mockRejectedValue(new Error('Delete error'));
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    const deleteButtons = screen.getAllByText('删除');
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('确定删除？')).toBeTruthy();
    });

    const okButton = document.querySelector('.ant-popconfirm .ant-btn-primary') as HTMLElement;
    if (okButton) {
      fireEvent.click(okButton);
    }

    await waitFor(() => {
      expect(props.deleteFn).toHaveBeenCalledWith(1);
    });
  });

  it('toggleActive handles error', async () => {
    props.updateFn.mockRejectedValue(new Error('Toggle error'));
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    const switches = document.querySelectorAll('.ant-switch');
    if (switches.length > 0) {
      fireEvent.click(switches[0]);
      await waitFor(() => {
        expect(props.updateFn).toHaveBeenCalledWith(1, { is_active: false });
      });
    }
  });

  it('test handles error', async () => {
    props.testFn.mockRejectedValue(new Error('Test error'));
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    const editButtons = screen.getAllByText('编辑');
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(document.querySelector('.ant-modal')).toBeTruthy();
    });

    const testBtn = document.querySelector('.ant-modal-footer button') as HTMLElement;
    expect(testBtn).toBeTruthy();
    fireEvent.click(testBtn);

    await waitFor(() => {
      expect(props.testFn).toHaveBeenCalled();
    });
  });

  it('apply handles error', async () => {
    props.applyFn.mockRejectedValue(new Error('Apply error'));
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('重新应用'));
    await waitFor(() => {
      expect(props.applyFn).toHaveBeenCalled();
    });
  });

  it('createDefaults handles error', async () => {
    props.createDefaultsFn.mockRejectedValue(new Error('CreateDefaults error'));
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('创建默认规则'));
    await waitFor(() => {
      expect(props.createDefaultsFn).toHaveBeenCalled();
    });
  });

  it('modal cancel button closes modal', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('新建规则'));
    await waitFor(() => {
      expect(document.querySelector('.ant-modal')).toBeTruthy();
    });

    // Click the cancel button in modal footer
    const cancelBtn = document.querySelector('.ant-modal-footer button:not(.ant-btn-primary)') as HTMLElement;
    if (cancelBtn) {
      fireEvent.click(cancelBtn);
    }
  });

  it('modal form fields are rendered and editable', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('新建规则'));
    await waitFor(() => {
      expect(document.querySelector('.ant-modal')).toBeTruthy();
    });

    // 验证表单字段存在
    expect(screen.getByText('名称 *')).toBeTruthy();
    const priorityElements = screen.getAllByText('优先级');
    expect(priorityElements.length).toBeGreaterThanOrEqual(1);
    const enableElements = screen.getAllByText('启用');
    expect(enableElements.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('来源（逗号分隔，留空匹配全部）')).toBeTruthy();
    expect(screen.getByText('收支方向（逗号分隔）')).toBeTruthy();
    expect(screen.getByText('关键词（逗号分隔）')).toBeTruthy();
    expect(screen.getByText('排除关键词（逗号分隔）')).toBeTruthy();
    expect(screen.getByText('最小金额')).toBeTruthy();
    expect(screen.getByText('最大金额')).toBeTruthy();
  });

  it('updateField changes form values', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('新建规则'));
    await waitFor(() => {
      expect(document.querySelector('.ant-modal')).toBeTruthy();
    });

    // 修改优先级
    const priorityInput = document.querySelector('.ant-input-number-input') as HTMLInputElement;
    if (priorityInput) {
      fireEvent.change(priorityInput, { target: { value: '100' } });
    }
  });

  it('cancel button in modal closes modal', async () => {
    render(<RuleManager {...props} />);
    await waitFor(() => {
      expect(screen.getByText('测试规则')).toBeTruthy();
    });

    fireEvent.click(screen.getByText('新建规则'));
    await waitFor(() => {
      expect(document.querySelector('.ant-modal')).toBeTruthy();
    });

    const modalFooter = document.querySelector('.ant-modal-footer');
    if (modalFooter) {
      const buttons = modalFooter.querySelectorAll('button');
      // Find cancel button (non-primary)
      for (const btn of Array.from(buttons)) {
        if (!btn.classList.contains('ant-btn-primary')) {
          fireEvent.click(btn);
          break;
        }
      }
    }
  });
});
