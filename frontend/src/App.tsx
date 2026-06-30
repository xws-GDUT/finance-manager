import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AppLayout from './components/AppLayout';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Import from './pages/Import';
import Categories from './pages/Categories';
import Accounts from './pages/Accounts';
import ValidRules from './pages/ValidRules';
import InvalidRules from './pages/InvalidRules';
import RefundPairs from './pages/RefundPairs';
import Settlements from './pages/Settlements';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <HashRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/import" element={<Import />} />
            <Route path="/categories" element={<Categories />} />
            <Route path="/accounts" element={<Accounts />} />
            <Route path="/valid-rules" element={<ValidRules />} />
            <Route path="/invalid-rules" element={<InvalidRules />} />
            <Route path="/refund-pairs" element={<RefundPairs />} />
            <Route path="/settlements" element={<Settlements />} />
          </Route>
        </Routes>
      </HashRouter>
    </ConfigProvider>
  );
}

export default App;
