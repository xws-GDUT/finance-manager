import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Modal, Input, message, Popconfirm,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import {
  fetchSettlements, createSettlement, deleteSettlement,
  closeSettlement, reopenSettlement,
} from '../api';
import type { SettlementGroup } from '../types';

export default function Settlements() {
  const [data, setData] = useState<SettlementGroup[]>([]);
  const [loading, setLoading] = useState(false);

  // 创建 Modal
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');

  // 详情 Modal
  const [detailOpen, setDetailOpen] = useState(false);
  const [detail, setDetail] = useState<SettlementGroup | null>(null);

  const loadData = async () => {
    setLoading(true);
    try { setData(await fetchSettlements()); } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  const handleCreate = async () => {
    if (!newName.trim()) { message.warning('请输入名称'); return; }
    try {
      await createSettlement({ name: newName, description: newDesc });
      message.success('已创建');
      setCreateOpen(false);
      setNewName('');
      setNewDesc('');
      loadData();
    } catch { message.error('创建失败'); }
  };

  const handleClose = async (id: number) => {
    try { await closeSettlement(id); message.success('已结算'); loadData(); }
    catch { message.error('操作失败'); }
  };

  const handleReopen = async (id: number) => {
    try { await reopenSettlement(id); message.success('已重开'); loadData(); }
    catch { message.error('操作失败'); }
  };

  const handleDelete = async (id: number) => {
    try { await deleteSettlement(id); message.success('已删除'); loadData(); }
    catch { message.error('删除失败'); }
  };

  const viewDetail = (item: SettlementGroup) => {
    setDetail(item);
    setDetailOpen(true);
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', width: 180 },
    { title: '描述', dataIndex: 'description', key: 'desc', ellipsis: true, width: 200,
      render: (v: string) => v || '-' },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 80,
      render: (s: string) => <Tag color={s === 'open' ? 'blue' : 'green'}>{s === 'open' ? '进行中' : '已结算'}</Tag>,
    },
    {
      title: '垫付', key: 'advance', width: 130,
      render: (_: unknown, r: SettlementGroup) => (
        <span style={{ color: '#cf1322' }}>¥{r.total_advance.toLocaleString()}</span>
      ),
    },
    {
      title: '收款', key: 'reim', width: 130,
      render: (_: unknown, r: SettlementGroup) => (
        <span style={{ color: '#389e0d' }}>¥{r.total_reimbursement.toLocaleString()}</span>
      ),
    },
    {
      title: '净支出', key: 'net', width: 130,
      render: (_: unknown, r: SettlementGroup) => (
        <span style={{ fontWeight: 600, color: r.net_amount > 0 ? '#cf1322' : '#666' }}>
          ¥{r.net_amount.toLocaleString()}
        </span>
      ),
    },
    { title: 'AA', dataIndex: 'is_aa', key: 'aa', width: 60,
      render: (v: boolean) => v ? <Tag color="purple">AA</Tag> : null },
    {
      title: '操作', key: 'actions', width: 200,
      render: (_: unknown, r: SettlementGroup) => (
        <Space size="small">
          <Button type="link" size="small" onClick={() => viewDetail(r)}>详情</Button>
          {r.status === 'open' ? (
            <Popconfirm title="确定关闭结算？" onConfirm={() => handleClose(r.id)}>
              <Button type="link" size="small" style={{ color: '#cf1322' }}>关闭</Button>
            </Popconfirm>
          ) : (
            <Popconfirm title="确定重开结算？" onConfirm={() => handleReopen(r.id)}>
              <Button type="link" size="small" style={{ color: '#389e0d' }}>重开</Button>
            </Popconfirm>
          )}
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const itemColumns = [
    { title: '类型', dataIndex: 'item_type', key: 'type', width: 60,
      render: (v: string) => <Tag color={v === 'advance' ? 'red' : 'green'}>{v === 'advance' ? '垫付' : '收款'}</Tag> },
    { title: '日期', dataIndex: 'trans_date', key: 'date', width: 100 },
    { title: '描述', dataIndex: 'description', key: 'desc', ellipsis: true },
    { title: '商户', dataIndex: 'merchant', key: 'merchant', width: 120, ellipsis: true },
    {
      title: '金额', dataIndex: 'amount', key: 'amount', width: 120,
      render: (v: number, r: any) => (
        <span style={{ color: r.direction === 'expense' ? '#cf1322' : '#389e0d' }}>
          {r.direction === 'expense' ? '-' : '+'}¥{v.toLocaleString()}
        </span>
      ),
    },
  ];

  return (
    <div>
      <Card title="垫付结算" extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建结算组</Button>
      }>
        <Table columns={columns} dataSource={data} rowKey="id" loading={loading} size="middle"
          pagination={false} />
      </Card>

      <Modal title="新建结算组" open={createOpen} onOk={handleCreate}
        onCancel={() => setCreateOpen(false)} okText="创建" cancelText="取消">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>名称 *</div>
            <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="结算组名称" />
          </div>
          <div>
            <div style={{ marginBottom: 4, fontWeight: 500 }}>描述</div>
            <Input.TextArea value={newDesc} onChange={e => setNewDesc(e.target.value)} rows={2} placeholder="可选描述" />
          </div>
        </Space>
      </Modal>

      <Modal title={detail?.name || '结算详情'} open={detailOpen}
        onCancel={() => setDetailOpen(false)} footer={null} width={700}>
        {detail && (
          <div>
            <Space wrap style={{ marginBottom: 16 }}>
              <Tag color="blue">{detail.status === 'open' ? '进行中' : '已结算'}</Tag>
              <span>垫付：<span style={{ color: '#cf1322' }}>¥{detail.total_advance.toLocaleString()}</span></span>
              <span>收款：<span style={{ color: '#389e0d' }}>¥{detail.total_reimbursement.toLocaleString()}</span></span>
              <span>净支出：<strong>¥{detail.net_amount.toLocaleString()}</strong></span>
            </Space>
            <Table columns={itemColumns} dataSource={detail.items} rowKey="id"
              pagination={false} size="small" />
          </div>
        )}
      </Modal>
    </div>
  );
}
