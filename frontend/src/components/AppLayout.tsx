import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import type { MenuProps } from 'antd';
import {
  DashboardOutlined,
  UnorderedListOutlined,
  UploadOutlined,
  TagsOutlined,
  WalletOutlined,
  CheckCircleOutlined,
  StopOutlined,
  SwapOutlined,
  TeamOutlined,
} from '@ant-design/icons';

const { Sider, Content, Header } = Layout;

const menuItems: MenuProps['items'] = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/transactions', icon: <UnorderedListOutlined />, label: '交易明细' },
  { key: '/import', icon: <UploadOutlined />, label: '流水导入' },
  { key: '/categories', icon: <TagsOutlined />, label: '分类管理' },
  { key: '/accounts', icon: <WalletOutlined />, label: '账户管理' },
  { key: '/valid-rules', icon: <CheckCircleOutlined />, label: '有效规则' },
  { key: '/invalid-rules', icon: <StopOutlined />, label: '无效规则' },
  { key: '/refund-pairs', icon: <SwapOutlined />, label: '退款配对' },
  { key: '/settlements', icon: <TeamOutlined />, label: '垫付结算' },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  // HashRouter: useLocation() 的 pathname 直接是 hash 中的路径
  // 例如 URL #/import → pathname = /import
  const selectedKey = '/' + (location.pathname.split('/')[1] || 'dashboard');

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        width={200}
      >
        <div style={{
          height: 48,
          margin: 16,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: collapsed ? 16 : 18,
          fontWeight: 'bold',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
        }}>
          {collapsed ? '💰' : '💰 家庭财务'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          fontSize: 16,
          fontWeight: 500,
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
        }}>
          {(() => {
            const item = (menuItems as Array<{key?: string; label?: string}>).find(m => m && m.key === selectedKey);
            return item?.label || '家庭财务管理系统';
          })()}
        </Header>
        <Content style={{ margin: 16, padding: 24, background: '#fff', borderRadius: 8, overflow: 'auto' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
