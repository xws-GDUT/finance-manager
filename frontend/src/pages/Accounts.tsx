import { useState, useEffect } from 'react';
import { Card, Table, Tag } from 'antd';
import { fetchAccounts } from '../api';
import type { Account } from '../types';

export default function Accounts() {
  const [data, setData] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAccounts().then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const columns = [
    { title: '账户名称', dataIndex: 'name', key: 'name', width: 180 },
    {
      title: '类型', dataIndex: 'account_type', key: 'type', width: 100,
      render: (v: string) => {
        const m: Record<string, { color: string; text: string }> = {
          debit: { color: 'blue', text: '储蓄卡' },
          credit: { color: 'orange', text: '信用卡' },
          platform: { color: 'purple', text: '支付平台' },
        };
        const info = m[v] || { color: 'default', text: v };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    { title: '银行', dataIndex: 'bank_name', key: 'bank', width: 100, render: (v: string) => v || '-' },
    { title: '持有人', dataIndex: 'owner', key: 'owner', width: 100, render: (v: string) => v || '-' },
    {
      title: '交易笔数', key: 'count', width: 100,
      render: (_: unknown, r: Account) => r.stats?.tx_count || 0,
    },
    {
      title: '总支出', key: 'expense', width: 140,
      render: (_: unknown, r: Account) => (
        <span style={{ color: '#cf1322' }}>¥{(r.stats?.total_expense || 0).toLocaleString()}</span>
      ),
    },
    {
      title: '总收入', key: 'income', width: 140,
      render: (_: unknown, r: Account) => (
        <span style={{ color: '#389e0d' }}>¥{(r.stats?.total_income || 0).toLocaleString()}</span>
      ),
    },
  ];

  return (
    <Card title="账户管理">
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
        pagination={false} size="middle" />
    </Card>
  );
}
