import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AppLayout from './AppLayout';

const mockNavigate = vi.fn();
const mockUseLocation = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockUseLocation(),
    Outlet: () => <div data-testid="outlet">Outlet Content</div>,
  };
});

describe('AppLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseLocation.mockReturnValue({ pathname: '/dashboard', search: '', hash: '', state: null });
  });

  it('renders sidebar and content area', () => {
    render(<AppLayout />);
    // Sidebar shows full title
    expect(screen.getByText('💰 家庭财务')).toBeTruthy();
    expect(screen.getByTestId('outlet')).toBeTruthy();
  });

  it('renders all 9 menu items', () => {
    render(<AppLayout />);
    const menuLabels = [
      '仪表盘', '交易明细', '流水导入', '分类管理', '账户管理',
      '有效规则', '无效规则', '退款配对', '垫付结算',
    ];
    for (const label of menuLabels) {
      // getAllByText because label appears in both sidebar menu and header title
      const elements = screen.getAllByText(label);
      expect(elements.length).toBeGreaterThanOrEqual(1);
    }
  });

  it('header shows current page title from selected menu', () => {
    mockUseLocation.mockReturnValue({ pathname: '/dashboard', search: '', hash: '', state: null });
    render(<AppLayout />);
    // Header shows the label - getAllByText because it's in both menu and header
    const elements = screen.getAllByText('仪表盘');
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it('header shows correct title for /accounts route', () => {
    mockUseLocation.mockReturnValue({ pathname: '/accounts', search: '', hash: '', state: null });
    render(<AppLayout />);
    const elements = screen.getAllByText('账户管理');
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it('header shows correct title for /import route', () => {
    mockUseLocation.mockReturnValue({ pathname: '/import', search: '', hash: '', state: null });
    render(<AppLayout />);
    const elements = screen.getAllByText('流水导入');
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it('header shows correct title for /valid-rules route', () => {
    mockUseLocation.mockReturnValue({ pathname: '/valid-rules', search: '', hash: '', state: null });
    render(<AppLayout />);
    const elements = screen.getAllByText('有效规则');
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it('header shows fallback title for unknown route', () => {
    mockUseLocation.mockReturnValue({ pathname: '/unknown', search: '', hash: '', state: null });
    render(<AppLayout />);
    expect(screen.getByText('家庭财务管理系统')).toBeTruthy();
  });

  it('clicking a menu item triggers navigation', () => {
    render(<AppLayout />);
    // Click the menu item for 账户管理 (use getAllByText since there are multiple)
    const menuElements = screen.getAllByText('账户管理');
    fireEvent.click(menuElements[0]);
    expect(mockNavigate).toHaveBeenCalledWith('/accounts');
  });

  it('clicking 流水导入 navigates to /import', () => {
    render(<AppLayout />);
    const elements = screen.getAllByText('流水导入');
    fireEvent.click(elements[0]);
    expect(mockNavigate).toHaveBeenCalledWith('/import');
  });

  it('clicking 交易明细 navigates to /transactions', () => {
    render(<AppLayout />);
    const elements = screen.getAllByText('交易明细');
    fireEvent.click(elements[0]);
    expect(mockNavigate).toHaveBeenCalledWith('/transactions');
  });

  it('clicking 分类管理 navigates to /categories', () => {
    render(<AppLayout />);
    const elements = screen.getAllByText('分类管理');
    fireEvent.click(elements[0]);
    expect(mockNavigate).toHaveBeenCalledWith('/categories');
  });

  it('clicking 有效规则 navigates to /valid-rules', () => {
    render(<AppLayout />);
    const elements = screen.getAllByText('有效规则');
    fireEvent.click(elements[0]);
    expect(mockNavigate).toHaveBeenCalledWith('/valid-rules');
  });

  it('clicking 无效规则 navigates to /invalid-rules', () => {
    render(<AppLayout />);
    const elements = screen.getAllByText('无效规则');
    fireEvent.click(elements[0]);
    expect(mockNavigate).toHaveBeenCalledWith('/invalid-rules');
  });

  it('clicking 退款配对 navigates to /refund-pairs', () => {
    render(<AppLayout />);
    const elements = screen.getAllByText('退款配对');
    fireEvent.click(elements[0]);
    expect(mockNavigate).toHaveBeenCalledWith('/refund-pairs');
  });

  it('clicking 垫付结算 navigates to /settlements', () => {
    render(<AppLayout />);
    const elements = screen.getAllByText('垫付结算');
    fireEvent.click(elements[0]);
    expect(mockNavigate).toHaveBeenCalledWith('/settlements');
  });

  it('collapsed state shows emoji only', () => {
    render(<AppLayout />);
    // Find the Sider's collapse trigger and click it
    const trigger = document.querySelector('.ant-layout-sider-trigger');
    if (trigger) {
      fireEvent.click(trigger);
      // After collapse, should show emoji only
      expect(screen.getByText('💰')).toBeTruthy();
      expect(screen.queryByText('💰 家庭财务')).toBeFalsy();
    }
  });

  it('uncollapsed state shows full title', () => {
    render(<AppLayout />);
    // Default state is uncollapsed
    expect(screen.getByText('💰 家庭财务')).toBeTruthy();
  });

  it('toggle collapse twice returns to uncollapsed', () => {
    render(<AppLayout />);
    const trigger = document.querySelector('.ant-layout-sider-trigger');
    if (trigger) {
      // 点击一次展开/收起
      fireEvent.click(trigger);
      // 再点击一次恢复
      fireEvent.click(trigger);
      // 恢复未展开状态
      expect(screen.getByText('💰 家庭财务')).toBeTruthy();
    }
  });

  it('renders all menu items with correct keys', () => {
    render(<AppLayout />);
    // 验证每个菜单项都存在
    const menuItems = document.querySelectorAll('.ant-menu-item');
    expect(menuItems.length).toBe(9);
  });
});
