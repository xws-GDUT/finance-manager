import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Switch, Modal, Input, InputNumber,
  Select, message, Popconfirm,
} from 'antd';
import { PlusOutlined, PlayCircleOutlined, ExperimentOutlined, ThunderboltOutlined } from '@ant-design/icons';
import type { ValidRule, InvalidRule } from '../types';

interface Props {
  type: 'valid' | 'invalid';
  title: string;
  fetchFn: () => Promise<(ValidRule | InvalidRule)[]>;
  createFn: (data: any) => Promise<any>;
  updateFn: (id: number, data: any) => Promise<any>;
  deleteFn: (id: number) => Promise<any>;
  testFn: (data: any) => Promise<{ matched_count: number }>;
  applyFn: () => Promise<any>;
  createDefaultsFn: () => Promise<{ created: number; skipped: number }>;
}

const SOURCE_OPTIONS = [
  { value: 'alipay', label: '支付宝' }, { value: 'wechat', label: '微信支付' },
  { value: 'jd', label: '京东' }, { value: 'meituan', label: '美团' },
  { value: 'douyin', label: '抖音月付' }, { value: 'bocom_debit', label: '交通银行储蓄卡' },
  { value: 'cmb_debit', label: '招商银行储蓄卡' }, { value: 'cib_credit', label: '中信信用卡' },
  { value: 'cmb_credit', label: '招商银行信用卡' },
];

export default function RuleManager({ type, title, fetchFn, createFn, updateFn, deleteFn, testFn, applyFn, createDefaultsFn }: Props) {
  const [data, setData] = useState<(ValidRule | InvalidRule)[]>([]);
  const [loading, setLoading] = useState(false);

  // 编辑 Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Partial<ValidRule | InvalidRule>>({});
  const [isNew, setIsNew] = useState(true);

  // 测试
  const [testResult, setTestResult] = useState<number | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const rules = await fetchFn();
      setData(rules as any);
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  const openCreate = () => {
    setEditing({ name: '', priority: 50, is_active: true, sources: '', directions: '', keywords: '', keyword_exclude: '', counterparties: '' });
    setIsNew(true);
    setTestResult(null);
    setModalOpen(true);
  };

  const openEdit = (rule: ValidRule | InvalidRule) => {
    setEditing({ ...rule });
    setIsNew(false);
    setTestResult(null);
    setModalOpen(true);
  };

  const save = async () => {
    try {
      if (isNew) {
        await createFn(editing);
        message.success('已创建');
      } else if (editing.id) {
        await updateFn(editing.id, editing);
        message.success('已更新');
      }
      setModalOpen(false);
      loadData();
    } catch { message.error('保存失败'); }
  };

  const handleDelete = async (id: number) => {
    try { await deleteFn(id); message.success('已删除'); loadData(); }
    catch { message.error('删除失败'); }
  };

  const toggleActive = async (rule: ValidRule | InvalidRule) => {
    try {
      await updateFn(rule.id, { is_active: !rule.is_active });
      loadData();
    } catch { message.error('操作失败'); }
  };

  const handleTest = async () => {
    try {
      const res = await testFn(editing);
      setTestResult(res.matched_count);
    } catch { message.error('测试失败'); }
  };

  const handleApply = async () => {
    try {
      const res = await applyFn();
      message.success(`已重新应用：${res.matched || 0} / ${res.total || 0} 条`);
      loadData();
    } catch { message.error('应用失败'); }
  };

  const handleCreateDefaults = async () => {
    try {
      const res = await createDefaultsFn();
      message.success(`默认规则创建完成：新增 ${res.created} 条，跳过 ${res.skipped} 条`);
      loadData();
    } catch { message.error('创建默认规则失败'); }
  };

  const updateField = (field: string, value: any) => {
    setEditing(prev => ({ ...prev, [field]: value }));
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', width: 200 },
    { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80, sorter: (a: any, b: any) => a.priority - b.priority },
    {
      title: '启用', dataIndex: 'is_active', key: 'active', width: 70,
      render: (_: unknown, r: any) => <Switch checked={r.is_active} size="small" onChange={() => toggleActive(r)} />,
    },
    { title: '来源', dataIndex: 'sources', key: 'sources', width: 180, ellipsis: true,
      render: (v: string) => v ? v.split(',').map((s: string) => <Tag key={s} style={{ marginBottom: 2 }}>{s}</Tag>) : <Tag>全部</Tag>,
    },
    { title: '方向', dataIndex: 'directions', key: 'directions', width: 80,
      render: (v: string) => v || '全部',
    },
    { title: '关键词', dataIndex: 'keywords', key: 'keywords', width: 200, ellipsis: true,
      render: (v: string) => v || '-',
    },
    { title: '命中', dataIndex: 'hit_count', key: 'hit_count', width: 70 },
    {
      title: '操作', key: 'actions', width: 140,
      render: (_: unknown, r: any) => (
        <Space size="small">
          <Button type="link" size="small" onClick={() => openEdit(r)}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title={title}
      extra={
        <Space>
          <Button icon={<ThunderboltOutlined />} onClick={handleCreateDefaults}>创建默认规则</Button>
          <Button icon={<ExperimentOutlined />} onClick={handleApply}>重新应用</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建规则</Button>
        </Space>
      }
    >
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} size="middle"
        pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条` }} />

      <Modal
        title={isNew ? '新建规则' : '编辑规则'}
        open={modalOpen}
        onOk={save}
        onCancel={() => setModalOpen(false)}
        width={640}
        okText="保存"
        cancelText="取消"
        footer={[
          <Button key="test" icon={<PlayCircleOutlined />} onClick={handleTest}>
            测试 {testResult !== null && `(${testResult} 条)`}
          </Button>,
          <Button key="cancel" onClick={() => setModalOpen(false)}>取消</Button>,
          <Button key="save" type="primary" onClick={save}>保存</Button>,
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          <div>
            <div style={{ marginBottom: 2, fontWeight: 500 }}>名称 *</div>
            <Input value={editing.name} onChange={e => updateField('name', e.target.value)} placeholder="规则名称" />
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div style={{ marginBottom: 2, fontWeight: 500 }}>优先级</div>
              <InputNumber value={editing.priority} onChange={v => updateField('priority', v)} min={0} max={1000} style={{ width: '100%' }} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ marginBottom: 2, fontWeight: 500 }}>启用</div>
              <Switch checked={editing.is_active} onChange={v => updateField('is_active', v)} />
            </div>
          </div>
          <div>
            <div style={{ marginBottom: 2, fontWeight: 500 }}>来源（逗号分隔，留空匹配全部）</div>
            <Select mode="multiple" value={editing.sources ? editing.sources.split(',').filter(Boolean) : []}
              onChange={(v) => updateField('sources', v.join(','))} options={SOURCE_OPTIONS}
              style={{ width: '100%' }} placeholder="选择来源" allowClear />
          </div>
          <div>
            <div style={{ marginBottom: 2, fontWeight: 500 }}>收支方向（逗号分隔）</div>
            <Select mode="multiple" value={editing.directions ? editing.directions.split(',').filter(Boolean) : []}
              onChange={(v) => updateField('directions', v.join(','))}
              options={[{ value: 'expense', label: '支出' }, { value: 'income', label: '收入' }]}
              style={{ width: '100%' }} placeholder="留空匹配全部" allowClear />
          </div>
          <div>
            <div style={{ marginBottom: 2, fontWeight: 500 }}>关键词（逗号分隔）</div>
            <Input.TextArea value={editing.keywords || ''} onChange={e => updateField('keywords', e.target.value)}
              rows={2} placeholder="关键词，逗号分隔。搜索范围：描述+商户+对手方+交易类型+支付渠道" />
          </div>
          <div>
            <div style={{ marginBottom: 2, fontWeight: 500 }}>排除关键词（逗号分隔）</div>
            <Input.TextArea value={editing.keyword_exclude || ''} onChange={e => updateField('keyword_exclude', e.target.value)}
              rows={2} placeholder="排除关键词，逗号分隔" />
          </div>
          {type === 'invalid' && (
            <div>
              <div style={{ marginBottom: 2, fontWeight: 500 }}>对手方（逗号分隔，精确匹配）</div>
              <Input value={(editing as any).counterparties || ''}
                onChange={e => updateField('counterparties', e.target.value)}
                placeholder="对手方名称，逗号分隔" />
            </div>
          )}
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div style={{ marginBottom: 2, fontWeight: 500 }}>最小金额</div>
              <InputNumber value={editing.amount_min} onChange={v => updateField('amount_min', v)} style={{ width: '100%' }} placeholder="留空不限" />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ marginBottom: 2, fontWeight: 500 }}>最大金额</div>
              <InputNumber value={editing.amount_max} onChange={v => updateField('amount_max', v)} style={{ width: '100%' }} placeholder="留空不限" />
            </div>
          </div>
        </Space>
      </Modal>
    </Card>
  );
}
